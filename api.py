import aiohttp
import asyncio
import ssl
from typing import Optional

OPENDOTA = "https://api.opendota.com/api"
_ssl = ssl.create_default_context()
_ssl.check_hostname = False
_ssl.verify_mode = ssl.CERT_NONE


async def _get(url: str, params: dict = None) -> any:
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10), ssl=_ssl) as resp:
            if resp.status == 200:
                return await resp.json()
            return None


async def fetch_heroes() -> list[dict]:
    return await _get(f"{OPENDOTA}/heroes") or []


_teams_cache: list[dict] = []


async def _load_teams() -> list[dict]:
    global _teams_cache
    if _teams_cache:
        return _teams_cache
    result = await _get(f"{OPENDOTA}/teams")
    _teams_cache = result or []
    return _teams_cache


async def search_team(name: str) -> Optional[dict]:
    teams = await _load_teams()
    q = name.lower().strip()
    # Точное совпадение
    for t in teams:
        if t["name"].lower() == q:
            return t
    # Частичное совпадение
    matches = [t for t in teams if q in t["name"].lower() or t.get("tag", "").lower() == q]
    if not matches:
        # Ищем по отдельным словам
        words = q.split()
        matches = [t for t in teams if any(w in t["name"].lower() for w in words if len(w) > 2)]
    if not matches:
        return None
    # Берём с наибольшим рейтингом
    matches.sort(key=lambda t: t.get("rating", 0), reverse=True)
    return matches[0]


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
