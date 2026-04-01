"""
Хранение состояния сессии пользователя в памяти (dict по user_id).
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Stage(str, Enum):
    TEAMS = "teams"        # ждём названия команд
    BANS = "bans"          # ждём банны (опционально)
    PICKS = "picks"        # ждём пики
    ODDS = "odds"          # ждём коэффициенты
    DONE = "done"          # предикт готов


@dataclass
class Session:
    stage: Stage = Stage.TEAMS
    tournament: Optional[str] = None

    team1: Optional[dict] = None   # {"id": ..., "name": ...}
    team2: Optional[dict] = None

    bans: dict = field(default_factory=lambda: {"team1": [], "team2": []})
    picks: dict = field(default_factory=lambda: {"team1": [], "team2": []})

    pending_team: Optional[str] = None   # "team1" или "team2" — выбрана кнопкой
    odds: Optional[dict] = None          # {"team1": 1.8, "team2": 2.1}
    pending_odd: Optional[str] = None    # "team1" или "team2" — ждём кэф для этой команды

    def picks_count(self) -> tuple[int, int]:
        return len(self.picks["team1"]), len(self.picks["team2"])

    def bans_count(self) -> tuple[int, int]:
        return len(self.bans["team1"]), len(self.bans["team2"])

    def picks_complete(self) -> bool:
        return len(self.picks["team1"]) == 5 and len(self.picks["team2"]) == 5

    def teams_set(self) -> bool:
        return self.team1 is not None and self.team2 is not None


# Глобальное хранилище сессий
_sessions: dict[int, Session] = {}


def get_session(user_id: int) -> Session:
    if user_id not in _sessions:
        _sessions[user_id] = Session()
    return _sessions[user_id]


def reset_session(user_id: int) -> Session:
    _sessions[user_id] = Session()
    return _sessions[user_id]
