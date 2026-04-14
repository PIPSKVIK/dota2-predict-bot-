"""
Логика предсказания результата матча.
"""
import asyncio
import math
from api import (
    fetch_head_to_head, fetch_team_heroes, fetch_hero_stats,
    fetch_team, fetch_hero_matchups,
)
from session import Session
import insights as insight_db


async def predict(session: Session) -> dict:
    team1_id = session.team1["id"]
    team2_id = session.team2["id"]

    picks1 = session.picks["team1"]
    picks2 = session.picks["team2"]

    # Запрашиваем всё параллельно
    (
        h2h,
        t1, t2,
        t1_heroes, t2_heroes,
        hero_stats,
        matchups_data,
    ) = await asyncio.gather(
        fetch_head_to_head(team1_id, team2_id),
        fetch_team(team1_id),
        fetch_team(team2_id),
        fetch_team_heroes(team1_id),
        fetch_team_heroes(team2_id),
        fetch_hero_stats(),
        _fetch_all_matchups(picks1 + picks2),
    )

    # Считаем каждый фактор (все возвращают delta team1 - team2 от -1 до 1)
    h2h_score      = _h2h_score(h2h, team1_id)
    rating_score   = _rating_score(t1, t2)
    pick_fit_score = _pick_fit_score(picks1, t1_heroes) - _pick_fit_score(picks2, t2_heroes)
    hero_wr_score  = _hero_winrate_score(picks1, picks2, hero_stats)
    counter_score  = _counter_score(picks1, picks2, matchups_data)
    synergy_score  = _synergy_score(picks1, picks2)
    meta_score     = insight_db.insights_score(picks1, picks2)

    # Веса: h2h=28%, рейтинг=19%, каунтеры=19%, синергии=14%, winrate=10%, пики=5%, мета=5%
    delta = (
        h2h_score      * 0.28 +
        rating_score   * 0.19 +
        counter_score  * 0.19 +
        synergy_score  * 0.14 +
        hero_wr_score  * 0.10 +
        pick_fit_score * 0.05 +
        meta_score     * 0.05
    )

    # Live-данные (если матч уже идёт)
    live = getattr(session, "live_data", None) or {}
    live_score = 0.0
    live_weight = 0.0
    if live:
        kills1 = live.get("kills_team1", 0) or 0
        kills2 = live.get("kills_team2", 0) or 0
        gold_adv = live.get("gold_advantage", 0) or 0  # >0 = team1 впереди

        total_kills = kills1 + kills2
        kill_score = (kills1 - kills2) / max(total_kills, 1)          # -1..1
        gold_score = max(-1.0, min(1.0, gold_adv / 10000))            # -1..1
        live_score = kill_score * 0.4 + gold_score * 0.6

        # Чем больше килов — тем больше вес live-данных (до 50%)
        live_weight = min(0.5, total_kills / 40)
        delta = delta * (1 - live_weight) + live_score * live_weight

    team1_pct = round(50 + 50 * (2 / (1 + math.exp(-delta * 3)) - 1), 1)
    team2_pct = round(100 - team1_pct, 1)

    return {
        "team1": session.team1["name"],
        "team2": session.team2["name"],
        "team1_pct": team1_pct,
        "team2_pct": team2_pct,
        "h2h_total": len(h2h),
        "team1_h2h_wins": sum(1 for m in h2h if _team_won(m, team1_id)),
        "live_weight": round(live_weight, 2),
        "details": {
            "h2h":      round(h2h_score, 3),
            "rating":   round(rating_score, 3),
            "counters": round(counter_score, 3),
            "synergy":  round(synergy_score, 3),
            "meta":     round(meta_score, 3),
            "hero_wr":  round(hero_wr_score, 3),
            "pick_fit": round(pick_fit_score, 3),
        }
    }


# ──────────────────────────────────────────────
# Вспомогательные функции
# ──────────────────────────────────────────────

async def _fetch_all_matchups(picks: list[dict]) -> dict[int, dict]:
    """Загружаем matchup данные для всех героев параллельно"""
    ids = [p["id"] for p in picks]
    results = await asyncio.gather(*[fetch_hero_matchups(hid) for hid in ids])
    return dict(zip(ids, results))


def _team_won(match: dict, team_id: int) -> bool:
    radiant_win = match.get("radiant_win")
    is_radiant = match.get("radiant_team_id") == team_id
    return (radiant_win and is_radiant) or (not radiant_win and not is_radiant)


def _h2h_score(matches: list, team1_id: int) -> float:
    if not matches:
        return 0.0
    wins = sum(1 for m in matches if _team_won(m, team1_id))
    return (wins / len(matches) - 0.5) * 2  # от -1 до 1


def _rating_score(t1: dict, t2: dict) -> float:
    if not t1 or not t2:
        return 0.0
    diff = t1.get("rating", 1500) - t2.get("rating", 1500)
    return max(-1.0, min(1.0, diff / 500))


def _pick_fit_score(picks: list[dict], team_heroes: list[dict]) -> float:
    if not team_heroes or not picks:
        return 0.0
    team_hero_ids = {h["hero_id"]: h.get("games", 0) for h in team_heroes}
    total_games = sum(team_hero_ids.values()) or 1
    return sum(team_hero_ids.get(p["id"], 0) / total_games for p in picks)


def _hero_winrate_score(picks1: list, picks2: list, hero_stats: list) -> float:
    stats = {h["id"]: h for h in hero_stats}

    def avg_wr(picks):
        wrs = []
        for p in picks:
            h = stats.get(p["id"])
            if h:
                total = h.get("pro_pick") or h.get("pub_pick", 1) or 1
                wins  = h.get("pro_win")  or h.get("pub_win",  0)
                wrs.append(wins / total)
        return sum(wrs) / len(wrs) if wrs else 0.5

    return (avg_wr(picks1) - avg_wr(picks2)) * 2


def _counter_score(picks1: list, picks2: list, matchups: dict[int, dict]) -> float:
    """
    Считаем насколько пики team1 контрят пики team2 и наоборот.
    matchups[hero_id][enemy_id] = {games_played, wins} — wins hero_id против enemy_id.
    Возвращает delta от -1 до 1 (положительное = team1 контрит team2).
    """
    def team_counter_score(attackers: list, defenders: list) -> float:
        wrs = []
        for a in attackers:
            a_matchups = matchups.get(a["id"], {})
            for d in defenders:
                m = a_matchups.get(d["id"])
                if m and m["games_played"] > 0:
                    wrs.append(m["wins"] / m["games_played"])
        return sum(wrs) / len(wrs) if wrs else 0.5

    score1 = team_counter_score(picks1, picks2)  # team1 против team2
    score2 = team_counter_score(picks2, picks1)  # team2 против team1
    return (score1 - score2) * 2  # нормализуем к -1..1


# Роли которые хорошо комбинируются
_GOOD_COMBOS = [
    ({"Initiator"}, {"AoE", "Nuker"}),          # инициатор + АоЕ урон
    ({"Disabler"}, {"Carry", "Nuker"}),           # дизейбл + урон
    ({"Support", "Healer"}, {"Carry"}),           # саппорт + керри
    ({"Pusher"}, {"Pusher"}),                     # два пушера
    ({"Escape"}, {"Nuker", "Carry"}),             # мобильный керри
]

_BAD_COMBOS = [
    ({"Carry"}, {"Carry"}),   # два хардкерри — плохо (нет саппорта)
]


def _synergy_score(picks1: list, picks2: list) -> float:
    """
    Простая эвристика синергий на основе ролей героев.
    Возвращает delta от -1 до 1.
    """
    def team_synergy(picks: list) -> float:
        score = 0.0
        roles_list = [set(h.get("roles", [])) for h in picks]
        for i, r1 in enumerate(roles_list):
            for j, r2 in enumerate(roles_list):
                if i >= j:
                    continue
                for good1, good2 in _GOOD_COMBOS:
                    if (r1 & good1 and r2 & good2) or (r2 & good1 and r1 & good2):
                        score += 1.0
                for bad1, bad2 in _BAD_COMBOS:
                    if r1 & bad1 and r2 & bad2:
                        score -= 0.5
        # Нормализуем: максимум ~10 хороших пар из C(5,2)=10
        return score / 10.0

    s1 = team_synergy(picks1)
    s2 = team_synergy(picks2)
    return max(-1.0, min(1.0, s1 - s2))
