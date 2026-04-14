import aiohttp
import asyncio
import ssl
import os
import urllib.parse
from typing import Optional

import httpx

OPENDOTA = "https://api.opendota.com/api"
LIQUIPEDIA_API = "https://api.liquipedia.net/api/v3"
LIQUIPEDIA_KEY = os.getenv("LIQUIPEDIA_API_KEY", "")

_ssl = ssl.create_default_context()
_ssl.check_hostname = False
_ssl.verify_mode = ssl.CERT_NONE

_lp_headers = {
    "Authorization": f"Apikey {LIQUIPEDIA_KEY}",
    "Accept": "application/json",
}


async def _get(url: str, params: dict = None) -> any:
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10), ssl=_ssl) as resp:
            if resp.status == 200:
                return await resp.json()
            return None


async def fetch_heroes() -> list[dict]:
    return await _get(f"{OPENDOTA}/heroes") or []


def _pagename_variants(q: str) -> list[str]:
    """Генерирует варианты pagename из введённого названия."""
    base = q.replace(" ", "_")
    variants = [base]
    # "BetBoom" -> "BetBoom_Team"
    if not base.lower().startswith("team_"):
        variants.append(base + "_Team")
    # "Spirit" -> "Team_Spirit"
    if not base.lower().startswith("team_"):
        variants.append("Team_" + base)
    return variants


async def _lp_team_by_pagename(pagename: str) -> Optional[dict]:
    try:
        async with httpx.AsyncClient(headers=_lp_headers, timeout=8) as client:
            resp = await client.get(f"{LIQUIPEDIA_API}/team", params={
                "wiki": "dota2",
                "limit": "1",
                "conditions": f"[[pagename::{pagename}]]",
            })
            data = resp.json().get("result", [])
            if data:
                t = data[0]
                return {
                    "team_id":  t.get("pageid", 0),
                    "name":     t.get("name") or pagename.replace("_", " "),
                    "tag":      t.get("shortname", ""),
                    "logo_url": t.get("logodarkurl") or t.get("logourl") or "",
                    "rating":   0,
                }
    except Exception:
        pass
    return None


# Кэш команд из расписания для fuzzy-поиска
_teams_from_schedule: list[dict] = []


def update_teams_cache(teams: list[dict]) -> None:
    """Вызывается из schedule.py при загрузке матчей."""
    global _teams_from_schedule
    existing = {t["name"].lower() for t in _teams_from_schedule}
    for t in teams:
        if t["name"].lower() not in existing:
            _teams_from_schedule.append(t)
            existing.add(t["name"].lower())


def _fuzzy_match(q: str, teams: list[dict]) -> Optional[dict]:
    q_lower = q.lower()
    # Точное совпадение
    for t in teams:
        if t["name"].lower() == q_lower:
            return t
    # Частичное — q содержится в названии или наоборот
    candidates = [t for t in teams
                  if q_lower in t["name"].lower() or t["name"].lower() in q_lower]
    if not candidates:
        # По словам
        words = [w for w in q_lower.split() if len(w) > 2]
        candidates = [t for t in teams
                      if any(w in t["name"].lower() for w in words)]
    if not candidates:
        return None
    return candidates[0]


async def search_team(name: str) -> Optional[dict]:
    """Поиск команды: сначала в кэше расписания, потом через Liquipedia API."""
    q = name.strip()
    if not q:
        return None

    # 1. Поиск в кэше команд из расписания
    found = _fuzzy_match(q, _teams_from_schedule)
    if found:
        return found

    # 2. Перебор вариантов pagename через API
    for variant in _pagename_variants(q):
        result = await _lp_team_by_pagename(variant)
        if result:
            _teams_from_schedule.append(result)
            return result

    return None


async def fetch_team(team_id: int) -> Optional[dict]:
    return await _get(f"{OPENDOTA}/teams/{team_id}")


async def fetch_team_matches(team_id: int, limit: int = 50) -> list[dict]:
    matches = await _get(f"{OPENDOTA}/teams/{team_id}/matches")
    if not matches:
        return []
    return matches[:limit]


async def fetch_head_to_head(team1_id: int, team2_id: int) -> list[dict]:
    """Матчи между двумя командами"""
    matches = await _get(f"{OPENDOTA}/teams/{team1_id}/matches")
    if not matches:
        return []
    h2h = [m for m in matches if m.get("opposing_team_id") == team2_id]
    return h2h


async def fetch_hero_stats() -> list[dict]:
    """Winrate героев на текущем патче"""
    return await _get(f"{OPENDOTA}/heroStats") or []


async def fetch_match_details(match_id: int) -> Optional[dict]:
    return await _get(f"{OPENDOTA}/matches/{match_id}")


async def fetch_team_heroes(team_id: int) -> list[dict]:
    """Любимые герои команды"""
    return await _get(f"{OPENDOTA}/teams/{team_id}/heroes") or []


_matchup_cache: dict[int, dict[int, dict]] = {}  # hero_id -> {enemy_id -> {games, wins}}


async def fetch_hero_matchups(hero_id: int) -> dict[int, dict]:
    """Matchup данные героя против каждого врага. Кэшируется."""
    if hero_id in _matchup_cache:
        return _matchup_cache[hero_id]
    data = await _get(f"{OPENDOTA}/heroes/{hero_id}/matchups") or []
    result = {m["hero_id"]: m for m in data}
    _matchup_cache[hero_id] = result
    return result
