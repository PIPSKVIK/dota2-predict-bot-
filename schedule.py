"""
Скрапинг расписания матчей с Liquipedia.
"""
import httpx
from bs4 import BeautifulSoup
from datetime import datetime, timezone

URL = "https://liquipedia.net/dota2/Liquipedia:Upcoming_and_ongoing_matches"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}

_cache: dict = {"data": [], "fetched_at": None}
CACHE_TTL = 300  # 5 минут


async def get_matches() -> list[dict]:
    now = datetime.now(timezone.utc).timestamp()
    if _cache["fetched_at"] and now - _cache["fetched_at"] < CACHE_TTL:
        return _cache["data"]

    try:
        async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=15) as client:
            resp = await client.get(URL)
            resp.raise_for_status()
    except Exception:
        return _cache["data"]

    matches = _parse(resp.text)
    _cache["data"] = matches
    _cache["fetched_at"] = now
    return matches


def _clean(name: str) -> str:
    return name.replace(" (page does not exist)", "").strip()


def _parse(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    matches = []

    for div in soup.select(".new-match-style"):
        try:
            m = _parse_match(div)
            if m:
                matches.append(m)
        except Exception:
            continue

    return matches


def _parse_match(tag) -> dict | None:
    # Команды
    left_link  = tag.select_one(".match-info-header-opponent-left .name a")
    right_links = tag.select(".match-info-header-opponent:not(.match-info-header-opponent-left) .name a")
    right_link = right_links[0] if right_links else None

    t1 = left_link.get_text(strip=True)  if left_link  else "TBD"
    t2 = right_link.get_text(strip=True) if right_link else "TBD"

    if t1 == "TBD" and t2 == "TBD":
        return None

    t1_full = _clean(left_link.get("title", t1)  if left_link  else t1)
    t2_full = _clean(right_link.get("title", t2) if right_link else t2)

    # Формат (Bo3, Bo5...)
    fmt_el = tag.select_one(".match-info-header-scoreholder-lower")
    fmt = fmt_el.get_text(strip=True).strip("()") if fmt_el else ""

    # Счёт если матч идёт
    scores = tag.select(".match-info-header-scoreholder-score")
    score = None
    if len(scores) >= 2:
        s1 = scores[0].get_text(strip=True)
        s2 = scores[1].get_text(strip=True)
        if s1.isdigit() and s2.isdigit():
            score = f"{s1}:{s2}"

    # Время матча
    time_el = tag.select_one(".timer-object")
    timestamp = None
    time_str = ""
    if time_el:
        ts = time_el.get("data-timestamp")
        if ts:
            try:
                timestamp = int(ts)
                dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                time_str = dt.strftime("%d %b %H:%M UTC")
            except ValueError:
                pass
        if not time_str:
            time_str = time_el.get_text(strip=True)

    # Турнир
    tour_el = tag.select_one(".match-info-tournament-name")
    tournament = tour_el.get_text(strip=True) if tour_el else ""

    # Ссылки на страницы команд
    t1_url = ""
    t2_url = ""
    if left_link:
        href = left_link.get("href", "")
        if href.startswith("/dota2/") and "index.php" not in href:
            t1_url = "https://liquipedia.net" + href
    if right_link:
        href = right_link.get("href", "")
        if href.startswith("/dota2/") and "index.php" not in href:
            t2_url = "https://liquipedia.net" + href

    # Статус матча
    live = bool(score)

    return {
        "team1":      t1_full,
        "team2":      t2_full,
        "team1_short": t1,
        "team2_short": t2,
        "format":     fmt,
        "score":      score,
        "timestamp":  timestamp,
        "time_str":   time_str,
        "tournament": tournament,
        "team1_url":  t1_url,
        "team2_url":  t2_url,
        "live":       live,
    }
