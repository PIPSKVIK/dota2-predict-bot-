"""
Хранение и парсинг мета-инсайдов через Groq LLM.
"""
import sqlite3
import json
import os
from datetime import datetime
from groq import AsyncGroq

DB_FILE = os.path.join(os.path.dirname(__file__), "insights.db")
client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_INSIGHT = """Ты парсишь инсайды про Dota 2 мету. Из сообщения пользователя извлеки:
- hero: имя героя на английском (как в игре, например "Lina", "Anti-Mage") или null
- effect: одно из "strong" (имба/ташит/сломан/picks), "weak" (слабый/не работает/контрится), "combo" (связка двух героев)
- combo_hero: второй герой если это связка, иначе null
- weight: уверенность/сила инсайда от 0.5 до 1.5 (1.0 по умолчанию, 1.5 если сказал "очень" или "сломан")

Примеры:
"Лина сейчас ташит" -> {"hero": "Lina", "effect": "strong", "combo_hero": null, "weight": 1.0}
"Морф слабый на этом патче" -> {"hero": "Morphling", "effect": "weak", "combo_hero": null, "weight": 1.0}
"связка Кунка Магнус сломана" -> {"hero": "Kunkka", "effect": "combo", "combo_hero": "Magnus", "weight": 1.5}
"Антимаг очень имба" -> {"hero": "Anti-Mage", "effect": "strong", "combo_hero": null, "weight": 1.5}

Отвечай ТОЛЬКО JSON."""


def _db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS insights (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                raw_text   TEXT NOT NULL,
                hero       TEXT,
                effect     TEXT,
                combo_hero TEXT,
                weight     REAL DEFAULT 1.0,
                created_at TEXT NOT NULL
            )
        """)


async def parse_and_save(raw_text: str) -> dict:
    """Парсим текст через LLM и сохраняем в БД."""
    resp = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_INSIGHT},
            {"role": "user",   "content": raw_text},
        ],
        temperature=0,
        max_tokens=120,
    )
    try:
        parsed = json.loads(resp.choices[0].message.content)
    except Exception:
        parsed = {"hero": None, "effect": "strong", "combo_hero": None, "weight": 1.0}

    with _db() as conn:
        cur = conn.execute(
            "INSERT INTO insights (raw_text, hero, effect, combo_hero, weight, created_at) VALUES (?,?,?,?,?,?)",
            (
                raw_text,
                parsed.get("hero"),
                parsed.get("effect", "strong"),
                parsed.get("combo_hero"),
                parsed.get("weight", 1.0),
                datetime.utcnow().isoformat(),
            ),
        )
        insight_id = cur.lastrowid

    return get_insight(insight_id)


def get_all() -> list[dict]:
    with _db() as conn:
        rows = conn.execute("SELECT * FROM insights ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]


def get_insight(insight_id: int) -> dict | None:
    with _db() as conn:
        row = conn.execute("SELECT * FROM insights WHERE id=?", (insight_id,)).fetchone()
    return dict(row) if row else None


def delete_insight(insight_id: int):
    with _db() as conn:
        conn.execute("DELETE FROM insights WHERE id=?", (insight_id,))


def insights_score(picks1: list, picks2: list) -> float:
    """
    Считаем влияние инсайдов на предикт.
    Возвращает delta от -1 до 1 (положительное = team1 выигрывает от инсайдов).
    """
    rows = get_all()
    if not rows:
        return 0.0

    def hero_names(picks):
        return {h.get("localized_name", "").lower() for h in picks}

    n1 = hero_names(picks1)
    n2 = hero_names(picks2)

    score = 0.0
    for ins in rows:
        hero = (ins.get("hero") or "").lower()
        combo = (ins.get("combo_hero") or "").lower()
        effect = ins.get("effect", "strong")
        w = float(ins.get("weight", 1.0)) * 0.1  # максимум ~0.15 за инсайд

        if effect == "strong":
            if hero in n1:
                score += w
            elif hero in n2:
                score -= w

        elif effect == "weak":
            if hero in n1:
                score -= w
            elif hero in n2:
                score += w

        elif effect == "combo" and combo:
            # Связка в одной команде
            if hero in n1 and combo in n1:
                score += w * 1.5
            elif hero in n2 and combo in n2:
                score -= w * 1.5

    return max(-1.0, min(1.0, score))
