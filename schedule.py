"""
Расписание матчей через Liquipedia DB API.
Docs: https://api.liquipedia.net
"""
import os
import urllib.parse
from datetime import datetime, timezone, timedelta

import httpx
from dotenv import load_dotenv
import api as api_mod

load_dotenv()

API_KEY = os.getenv("LIQUIPEDIA_API_KEY", "")
API_URL = "https://api.liquipedia.net/api/v3/match"

HEADERS = {
    "Authorization": f"Apikey {API_KEY}",
    "Accept": "application/json",
}

_cache: dict = {"data": [], "fetched_at": None}
CACHE_TTL = 300  # 5 минут


async def get_matches() -> list[dict]:
    now = datetime.now(timezone.utc).timestamp()
    if _cache["fetched_at"] and now - _cache["fetched_at"] < CACHE_TTL:
        return _cache["data"]

    matches = await _fetch()
    if matches or not _cache["data"]:
        _cache["data"] = matches
        _cache["fetched_at"] = now
        # Обновляем кэш команд для поиска
        teams = []
        for m in matches:
            for key in ("team1", "team2"):
                logo_key = key + "_logo"
                teams.append({"name": m[key], "team_id": 0, "tag": "", "logo_url": m.get(logo_key, ""), "rating": 0})
        api_mod.update_teams_cache(teams)
    return _cache["data"]


async def _fetch() -> list[dict]:
    # Берём матчи от текущего момента на 7 дней вперёд, только tier 1-3
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    week_str = (datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S")

    cond = f"[[date::>{now_str}]] AND [[date::<{week_str}]]"
    params = {
        "wiki":       "dota2",
        "limit":      "50",
        "order":      "date asc",
        "conditions": cond,
    }

    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=15, follow_redirects=True) as client:
            resp = await client.get(API_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        print(f"[schedule] API error: {e}")
        return _cache["data"]

    results = []
    for m in data.get("result", []):
        parsed = _parse_match(m)
        if parsed:
            results.append(parsed)

    return results


def _parse_match(m: dict) -> dict | None:
    ops = m.get("match2opponents", [])
    if len(ops) < 2:
        return None

    t1 = ops[0].get("name", "").strip()
    t2 = ops[1].get("name", "").strip()

    # Пропускаем TBD / пустые команды
    if not t1 or not t2 or t1.startswith("#") or t2.startswith("#"):
        return None

    # Пропускаем низкие тиры (4+)
    tier = m.get("liquipediatier", "5")
    try:
        if int(tier) >= 4:
            return None
    except ValueError:
        pass

    # Счёт
    s1 = ops[0].get("score", -1)
    s2 = ops[1].get("score", -1)
    score = None
    if isinstance(s1, int) and isinstance(s2, int) and s1 >= 0 and s2 >= 0:
        score = f"{s1}:{s2}"

    # Логотипы команд
    def _logo(op: dict) -> str:
        tt = op.get("teamtemplate") or {}
        return tt.get("imagedarkurl") or tt.get("imageurl") or ""

    t1_logo = _logo(ops[0])
    t2_logo = _logo(ops[1])

    # Время (UTC → МСК UTC+3)
    MSK = timezone(timedelta(hours=3))
    date_str = m.get("date", "")
    timestamp = None
    time_str = ""
    if date_str:
        try:
            dt = datetime.fromisoformat(date_str.replace(" ", "T")).replace(tzinfo=timezone.utc)
            timestamp = int(dt.timestamp())
            time_str = dt.astimezone(MSK).strftime("%d %b %H:%M МСК")
        except ValueError:
            time_str = date_str

    # Формат
    bestof = m.get("bestof", 0)
    fmt = f"Bo{bestof}" if bestof and int(bestof) > 0 else ""

    # Live: матч начался, ещё не завершён
    now_ts = datetime.now(timezone.utc).timestamp()
    is_live = bool(
        m.get("finished") == 0
        and timestamp
        and timestamp <= now_ts
    )

    return {
        "team1":      t1,
        "team2":      t2,
        "team1_logo": t1_logo,
        "team2_logo": t2_logo,
        "format":     fmt,
        "score":      score,
        "timestamp":  timestamp,
        "time_str":   time_str,
        "tournament": m.get("tournament", ""),
        "tier":       tier,
        "live":       is_live,
    }
