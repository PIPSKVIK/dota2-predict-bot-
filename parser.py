"""
Парсинг голосовых/текстовых команд через LLM.
"""
import json
import os
from groq import AsyncGroq

client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_TEAMS = """Ты парсишь сообщения про Dota 2 матч. Извлеки:
- team1: название первой команды (строка или null)
- team2: название второй команды (строка или null)
- tournament: название турнира если упомянуто (строка или null)

Отвечай ТОЛЬКО JSON. Пример: {"team1": "Team Spirit", "team2": "Team Liquid", "tournament": "ESL One"}"""


def _pick_ban_system(team1: str, team2: str) -> str:
    return f"""Ты парсишь сообщения про Dota 2 драфт. В матче участвуют команды: "{team1}" и "{team2}".

Извлеки из сообщения:
- team: одна из команд ("{team1}" или "{team2}", строка или null)
- action: "pick" или "ban" (если не ясно — "pick")
- hero: ПОЛНОЕ имя героя Dota 2 как назвал пользователь (строка или null)

ВАЖНО: "{team1}" и "{team2}" — это названия команд, а НЕ герои.
Если в названии команды и героя есть общее слово — определи правильно что команда, а что герой.
Например: "Team Spirit берут Vengeful Spirit" — команда "Team Spirit", герой "Vengeful Spirit".

Пользователь говорит по-русски или по-английски. Примеры:
"Спирит пикнули Джарико" -> {{"team": "{team1}", "action": "pick", "hero": "Джарико"}}
"Ликвид забанили Морфа" -> {{"team": "{team2}", "action": "ban", "hero": "Морф"}}
"за Спирит — Пак" -> {{"team": "{team1}", "action": "pick", "hero": "Пак"}}
"Team Spirit берут Vengeful Spirit" -> {{"team": "{team1}", "action": "pick", "hero": "Vengeful Spirit"}}

Отвечай ТОЛЬКО JSON."""


async def parse_teams(text: str) -> dict:
    resp = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_TEAMS},
            {"role": "user", "content": text},
        ],
        temperature=0,
        max_tokens=100,
    )
    try:
        return json.loads(resp.choices[0].message.content)
    except Exception:
        return {"team1": None, "team2": None, "tournament": None}


async def parse_pick_ban(text: str, team1: str = "", team2: str = "") -> dict:
    resp = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": _pick_ban_system(team1, team2)},
            {"role": "user", "content": text},
        ],
        temperature=0,
        max_tokens=100,
    )
    try:
        return json.loads(resp.choices[0].message.content)
    except Exception:
        return {"team": None, "action": "pick", "hero": None}


async def parse_odds(text: str, team1: str, team2: str) -> dict:
    """Извлечь коэффициенты из текста. Возвращает {"team1": float|None, "team2": float|None}"""
    system = f"""Ты парсишь букмекерские коэффициенты для матча Dota 2.
Команды: "{team1}" и "{team2}".
Извлеки коэффициенты (дробные числа типо 1.75, 2.30) для каждой команды.

Примеры:
"Спирит 1.8 Тундра 2.1" -> {{"team1": 1.8, "team2": 2.1}}
"на первую 1.65, на вторую 2.40" -> {{"team1": 1.65, "team2": 2.40}}
"1.8 и 2.1" -> {{"team1": 1.8, "team2": 2.1}}
"кэф на {team1} один и восемьдесят" -> {{"team1": 1.80, "team2": null}}

Отвечай ТОЛЬКО JSON."""

    resp = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": text},
        ],
        temperature=0,
        max_tokens=60,
    )
    try:
        return json.loads(resp.choices[0].message.content)
    except Exception:
        return {"team1": None, "team2": None}


async def transcribe_voice(file_path: str) -> str:
    with open(file_path, "rb") as f:
        resp = await client.audio.transcriptions.create(
            file=(file_path, f),
            model="whisper-large-v3",
            language="ru",
            response_format="text",
        )
    return resp.strip() if isinstance(resp, str) else resp.text.strip()
