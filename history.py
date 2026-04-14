"""
История предиктов с результатами матчей.
"""
import sqlite3
import json
import os
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(__file__), "insights.db")


def _db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                team1            TEXT NOT NULL,
                team2            TEXT NOT NULL,
                team1_pct        REAL NOT NULL,
                team2_pct        REAL NOT NULL,
                predicted_winner TEXT NOT NULL,
                picks_team1      TEXT,
                picks_team2      TEXT,
                actual_winner    TEXT,
                correct          INTEGER,
                created_at       TEXT NOT NULL
            )
        """)


def save_prediction(result: dict, picks: dict) -> int:
    winner = result["team1"] if result["team1_pct"] > result["team2_pct"] else result["team2"]
    with _db() as conn:
        cur = conn.execute(
            """INSERT INTO predictions
               (team1, team2, team1_pct, team2_pct, predicted_winner, picks_team1, picks_team2, created_at)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                result["team1"],
                result["team2"],
                result["team1_pct"],
                result["team2_pct"],
                winner,
                json.dumps([h.get("localized_name") for h in picks.get("team1", [])]),
                json.dumps([h.get("localized_name") for h in picks.get("team2", [])]),
                datetime.utcnow().isoformat(),
            ),
        )
        return cur.lastrowid


def set_result(prediction_id: int, actual_winner: str):
    with _db() as conn:
        row = conn.execute(
            "SELECT predicted_winner FROM predictions WHERE id=?", (prediction_id,)
        ).fetchone()
        if not row:
            return None
        correct = 1 if row["predicted_winner"] == actual_winner else 0
        conn.execute(
            "UPDATE predictions SET actual_winner=?, correct=? WHERE id=?",
            (actual_winner, correct, prediction_id),
        )
    return get_prediction(prediction_id)


def get_all() -> list[dict]:
    with _db() as conn:
        rows = conn.execute(
            "SELECT * FROM predictions ORDER BY created_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def get_prediction(prediction_id: int) -> dict | None:
    with _db() as conn:
        row = conn.execute(
            "SELECT * FROM predictions WHERE id=?", (prediction_id,)
        ).fetchone()
    return dict(row) if row else None


def get_stats() -> dict:
    rows = get_all()
    total = len(rows)
    with_result = [r for r in rows if r["correct"] is not None]
    correct = sum(1 for r in with_result if r["correct"] == 1)
    accuracy = round(correct / len(with_result) * 100, 1) if with_result else None
    return {
        "total":        total,
        "with_result":  len(with_result),
        "correct":      correct,
        "accuracy_pct": accuracy,
    }
