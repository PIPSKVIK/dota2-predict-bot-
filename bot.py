import asyncio
import os
import tempfile
from dotenv import load_dotenv

load_dotenv()

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    InputMediaPhoto,
)
from aiogram.filters import Command

import api
import heroes as hero_db
import parser as nlp
from session import get_session, reset_session, Stage
from predictor import predict

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()


# ──────────────────────────────────────────────
# Клавиатура выбора команды
# ──────────────────────────────────────────────

def teams_keyboard(s, action: str = "pick") -> InlineKeyboardMarkup:
    t1 = s.team1["name"]
    t2 = s.team2["name"]
    p1, p2 = s.picks_count()
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=f"{t1} ({p1}/5)", callback_data=f"team:team1:{action}"),
        InlineKeyboardButton(text=f"{t2} ({p2}/5)", callback_data=f"team:team2:{action}"),
    ]])


def bans_keyboard(s) -> InlineKeyboardMarkup:
    t1 = s.team1["name"]
    t2 = s.team2["name"]
    b1, b2 = s.bans_count()
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"🚫 {t1} ({b1})", callback_data="team:team1:ban"),
            InlineKeyboardButton(text=f"🚫 {t2} ({b2})", callback_data="team:team2:ban"),
        ],
        [InlineKeyboardButton(text="➡️ Перейти к пикам", callback_data="skip_bans")],
    ])


# ──────────────────────────────────────────────
# Команды
# ──────────────────────────────────────────────

@dp.message(Command("start"))
async def cmd_start(message: Message):
    reset_session(message.from_user.id)
    await message.answer(
        "👋 Привет! Я предсказываю результаты Dota 2 матчей.\n\n"
        "Напиши или скажи голосом <b>две команды</b>, например:\n"
        "• <i>Team Spirit vs Team Liquid</i>\n"
        "• <i>Спирит и Ликвид на ESL One</i>",
        parse_mode="HTML",
    )


@dp.message(Command("reset"))
async def cmd_reset(message: Message):
    reset_session(message.from_user.id)
    await message.answer("🔄 Сессия сброшена. Начни заново — назови две команды.")


@dp.message(Command("status"))
async def cmd_status(message: Message):
    s = get_session(message.from_user.id)
    if s.stage == Stage.TEAMS:
        await message.answer("⏳ Жду команды.")
        return
    await message.answer(_picks_status(s), parse_mode="HTML")


# ──────────────────────────────────────────────
# Callbacks (кнопки)
# ──────────────────────────────────────────────

@dp.callback_query(F.data.startswith("team:"))
async def cb_team_select(callback: CallbackQuery):
    _, team_key, action = callback.data.split(":")
    s = get_session(callback.from_user.id)
    s.pending_team = team_key
    team_name = s.team1["name"] if team_key == "team1" else s.team2["name"]
    verb = "забанить" if action == "ban" else "пикнул"
    await callback.answer()
    await callback.message.answer(
        f"{'🚫' if action == 'ban' else '⚔️'} <b>{team_name}</b> {verb} кого? Напиши или скажи героя:",
        parse_mode="HTML",
    )


@dp.callback_query(F.data.startswith("hero:"))
async def cb_hero_suggest(callback: CallbackQuery):
    _, team_key, hero_id_str = callback.data.split(":")
    s = get_session(callback.from_user.id)
    hero = hero_db._heroes_by_id.get(int(hero_id_str))
    if not hero:
        await callback.answer("Герой не найден")
        return
    await callback.answer()
    s.pending_team = team_key
    await handle_hero_input(callback.message, s, hero["localized_name"])


@dp.callback_query(F.data.startswith("odd:"))
async def cb_odd_team(callback: CallbackQuery):
    _, team_key = callback.data.split(":")
    s = get_session(callback.from_user.id)
    s.pending_odd = team_key
    team_name = s.team1["name"] if team_key == "team1" else s.team2["name"]
    await callback.answer()
    await callback.message.answer(
        f"💰 Кэф на <b>{team_name}</b>? Напиши или скажи число:",
        parse_mode="HTML",
    )


@dp.callback_query(F.data == "skip_odds")
async def cb_skip_odds(callback: CallbackQuery):
    s = get_session(callback.from_user.id)
    s.pending_odd = None
    await callback.answer()
    await run_prediction(callback.message, s)


@dp.callback_query(F.data == "skip_bans")
async def cb_skip_bans(callback: CallbackQuery):
    s = get_session(callback.from_user.id)
    s.stage = Stage.PICKS
    s.pending_team = None
    await callback.answer()
    await callback.message.answer(
        "Ок, без банов. Теперь называй пики!\n\n" + _picks_status(s),
        parse_mode="HTML",
        reply_markup=teams_keyboard(s),
    )


# ──────────────────────────────────────────────
# Голосовые сообщения
# ──────────────────────────────────────────────

@dp.message(F.voice)
async def handle_voice(message: Message):
    file = await bot.get_file(message.voice.file_id)
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        tmp_path = tmp.name

    await bot.download_file(file.file_path, destination=tmp_path)
    try:
        text = await nlp.transcribe_voice(tmp_path)
    finally:
        os.unlink(tmp_path)

    if not text:
        await message.answer("Не смог распознать голос, попробуй ещё раз.")
        return

    await message.answer(f"🎤 <i>{text}</i>", parse_mode="HTML")
    await process_text(message, text)


# ──────────────────────────────────────────────
# Текстовые сообщения
# ──────────────────────────────────────────────

@dp.message(F.text)
async def handle_text(message: Message):
    text = message.text.strip()
    if text.startswith("/"):
        return
    await process_text(message, text)


# ──────────────────────────────────────────────
# Основная логика
# ──────────────────────────────────────────────

async def process_text(message: Message, text: str):
    uid = message.from_user.id
    s = get_session(uid)

    if s.stage == Stage.TEAMS:
        await handle_teams_stage(message, s, text)
        return

    # Если команда уже выбрана кнопкой — текст это просто герой
    if s.pending_team:
        await handle_hero_input(message, s, text)
        return

    # Если ждём кэф для конкретной команды
    if s.pending_odd:
        await handle_odds_stage(message, s, text)
        return

    if s.stage == Stage.BANS:
        if text.lower() in ("нет", "no", "пропустить", "skip", "дальше"):
            s.stage = Stage.PICKS
            await message.answer(
                "Ок, без банов. Теперь называй пики!\n\n" + _picks_status(s),
                parse_mode="HTML",
                reply_markup=teams_keyboard(s),
            )
        else:
            await handle_pick_ban_text(message, s, text, is_ban_stage=True)

    elif s.stage == Stage.PICKS:
        await handle_pick_ban_text(message, s, text, is_ban_stage=False)

    elif s.stage == Stage.ODDS:
        await handle_odds_stage(message, s, text)


async def handle_teams_stage(message: Message, s, text: str):
    parsed = await nlp.parse_teams(text)
    t1_name = parsed.get("team1")
    t2_name = parsed.get("team2")
    tournament = parsed.get("tournament")

    if not t1_name or not t2_name:
        await message.answer(
            "Не понял команды. Попробуй так:\n"
            "<i>Team Spirit vs Team Liquid</i>",
            parse_mode="HTML",
        )
        return

    await message.answer("🔍 Ищу команды...")

    t1 = await api.search_team(t1_name)
    t2 = await api.search_team(t2_name)

    if not t1:
        await message.answer(f"❌ Не нашёл команду <b>{t1_name}</b>.", parse_mode="HTML")
        return
    if not t2:
        await message.answer(f"❌ Не нашёл команду <b>{t2_name}</b>.", parse_mode="HTML")
        return

    s.team1 = {"id": t1["team_id"], "name": t1["name"], "logo": t1.get("logo_url")}
    s.team2 = {"id": t2["team_id"], "name": t2["name"], "logo": t2.get("logo_url")}
    if tournament:
        s.tournament = tournament

    t_line = f"\n🎯 Турнир: {tournament}" if tournament else ""
    await message.answer(
        f"✅ <b>{t1['name']}</b> vs <b>{t2['name']}</b>{t_line}\n\n"
        f"Добавить баны? Нажми на команду которая банит, или пропусти.",
        parse_mode="HTML",
        reply_markup=bans_keyboard(s),
    )
    s.stage = Stage.BANS


async def handle_hero_input(message: Message, s, hero_raw: str):
    """Герой введён после нажатия кнопки — команда уже известна."""
    team_key = s.pending_team
    is_ban = s.stage == Stage.BANS

    hero = hero_db.find_hero(hero_raw)
    if not hero:
        suggestions = hero_db.suggest_heroes(hero_raw)
        if suggestions:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=h["localized_name"],
                    callback_data=f"hero:{team_key}:{h['id']}"
                ) for h in suggestions[:3]],
                [InlineKeyboardButton(
                    text=h["localized_name"],
                    callback_data=f"hero:{team_key}:{h['id']}"
                ) for h in suggestions[3:5]] if len(suggestions) > 3 else [],
            ])
            await message.answer(
                f"❓ Не нашёл <b>{hero_raw}</b>. Может имелось в виду:",
                parse_mode="HTML",
                reply_markup=kb,
            )
        else:
            await message.answer(
                f"❌ Не знаю героя: <b>{hero_raw}</b>. Напиши по-английски.",
                parse_mode="HTML",
            )
        return

    team_name = s.team1["name"] if team_key == "team1" else s.team2["name"]
    s.pending_team = None

    if is_ban:
        bans = s.bans[team_key]
        if any(h["id"] == hero["id"] for h in bans):
            await message.answer(f"⚠️ {hero['localized_name']} уже забанен.")
            s.pending_team = None
            await message.answer("Выбери команду:", reply_markup=bans_keyboard(s))
            return
        bans.append(hero)
        await message.answer(
            f"🚫 <b>{team_name}</b> забанили <b>{hero['localized_name']}</b>",
            parse_mode="HTML",
            reply_markup=bans_keyboard(s),
        )
    else:
        picks = s.picks[team_key]
        if len(picks) >= 5:
            await message.answer(f"⚠️ За {team_name} уже 5 пиков!")
            await message.answer(_picks_status(s), parse_mode="HTML", reply_markup=teams_keyboard(s))
            return
        if any(h["id"] == hero["id"] for h in picks):
            await message.answer(f"⚠️ {hero['localized_name']} уже пикнут.")
            await message.answer(_picks_status(s), parse_mode="HTML", reply_markup=teams_keyboard(s))
            return

        picks.append(hero)
        if s.picks_complete():
            await message.answer(
                f"✅ <b>{team_name}</b> пикнули <b>{hero['localized_name']}</b>",
                parse_mode="HTML",
            )
            await ask_odds(message, s)
        else:
            await message.answer(
                f"✅ <b>{team_name}</b> пикнули <b>{hero['localized_name']}</b>\n\n" + _picks_status(s),
                parse_mode="HTML",
                reply_markup=teams_keyboard(s),
            )


async def handle_pick_ban_text(message: Message, s, text: str, is_ban_stage: bool):
    """Fallback — если пользователь пишет полную фразу без кнопки."""
    parsed = await nlp.parse_pick_ban(text, team1=s.team1["name"], team2=s.team2["name"])
    team_raw = parsed.get("team")
    action = parsed.get("action", "pick")
    hero_raw = parsed.get("hero")

    if not hero_raw:
        kb = bans_keyboard(s) if is_ban_stage else teams_keyboard(s)
        await message.answer("Не понял героя. Нажми кнопку команды и назови героя:", reply_markup=kb)
        return

    team_key = _resolve_team(s, team_raw)
    if team_key is None:
        kb = bans_keyboard(s) if is_ban_stage else teams_keyboard(s)
        await message.answer("Не понял команду. Нажми кнопку:", reply_markup=kb)
        return

    s.pending_team = team_key
    await handle_hero_input(message, s, hero_raw)


def odds_keyboard(s) -> InlineKeyboardMarkup:
    t1 = s.team1["name"]
    t2 = s.team2["name"]
    o = s.odds or {}
    label1 = f"{t1}  {o['team1']}" if o.get("team1") else t1
    label2 = f"{t2}  {o['team2']}" if o.get("team2") else t2
    rows = [[
        InlineKeyboardButton(text=label1, callback_data="odd:team1"),
        InlineKeyboardButton(text=label2, callback_data="odd:team2"),
    ]]
    # Кнопка "Рассчитать" появляется когда хотя бы один кэф введён
    if o.get("team1") or o.get("team2"):
        rows.append([InlineKeyboardButton(text="📊 Рассчитать →", callback_data="skip_odds")])
    else:
        rows.append([InlineKeyboardButton(text="Пропустить →", callback_data="skip_odds")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def ask_odds(message: Message, s):
    s.stage = Stage.ODDS
    s.odds = {}
    await message.answer(
        f"💰 <b>Коэффициенты BetBoom</b>\n\n"
        f"Нажми на команду и введи её кэф:",
        parse_mode="HTML",
        reply_markup=odds_keyboard(s),
    )


async def handle_odds_stage(message: Message, s, text: str):
    # Если нажата кнопка команды — ждём просто число
    if s.pending_odd:
        try:
            val = float(text.replace(",", ".").strip())
            if val < 1.0:
                raise ValueError
        except ValueError:
            await message.answer("Введи корректный кэф, например: <i>1.85</i>", parse_mode="HTML")
            return
        if not s.odds:
            s.odds = {}
        s.odds[s.pending_odd] = val
        s.pending_odd = None
        await message.answer(
            f"✅ Записал. Добавь второй кэф или нажми «Рассчитать»:",
            reply_markup=odds_keyboard(s),
        )
        return

    # Фолбэк — написал сразу оба кэфа текстом
    parsed = await nlp.parse_odds(text, s.team1["name"], s.team2["name"])
    o1 = parsed.get("team1")
    o2 = parsed.get("team2")
    if not o1 and not o2:
        await message.answer(
            "Не понял. Нажми на кнопку команды и введи кэф:",
            reply_markup=odds_keyboard(s),
        )
        return
    s.odds = {"team1": o1, "team2": o2}
    await run_prediction(message, s)


async def run_prediction(message: Message, s):
    await message.answer("⏳ Анализирую данные, подожди...")
    try:
        result = await predict(s)
    except Exception as e:
        await message.answer(f"❌ Ошибка при анализе: {e}")
        return

    t1 = result["team1"]
    t2 = result["team2"]
    p1 = result["team1_pct"]
    p2 = result["team2_pct"]
    h2h_total = result["h2h_total"]
    h2h_wins = result["team1_h2h_wins"]
    h2h_losses = h2h_total - h2h_wins

    winner = t1 if p1 > p2 else t2
    winner_pct = max(p1, p2)

    bar1 = _pct_bar(p1)
    bar2 = _pct_bar(p2)

    picks1 = " · ".join(h["localized_name"] for h in s.picks["team1"])
    picks2 = " · ".join(h["localized_name"] for h in s.picks["team2"])

    h2h_line = (
        f"📊 <b>H2H:</b> {t1} <b>{h2h_wins}</b> – <b>{h2h_losses}</b> {t2}  <i>({h2h_total} матчей)</i>"
        if h2h_total else "📊 <b>H2H:</b> нет данных"
    )

    text = (
        f"🎯 <b>ПРОГНОЗ МАТЧА</b>\n"
        f"{'─' * 28}\n\n"
        f"🔵 <b>{t1}</b>\n"
        f"   {picks1}\n\n"
        f"🔴 <b>{t2}</b>\n"
        f"   {picks2}\n\n"
        f"{'─' * 28}\n\n"
        f"{bar1} <b>{p1}%</b>  ·  <b>{p2}%</b> {bar2}\n"
        f"<b>{t1}</b>  ·  <b>{t2}</b>\n\n"
        f"{'─' * 28}\n\n"
        f"{h2h_line}\n\n"
        f"🏆 Победитель по прогнозу: <b>{winner}</b> ({winner_pct}%)\n\n"
        f"<i>/reset — новый матч</i>"
    )

    # Логотипы команд
    logo1 = s.team1.get("logo")
    logo2 = s.team2.get("logo")
    if logo1 and logo2:
        try:
            await message.answer_media_group([
                InputMediaPhoto(media=logo1, caption=t1),
                InputMediaPhoto(media=logo2, caption=t2),
            ])
        except Exception:
            pass  # если логотип недоступен — просто пропускаем

    await message.answer(text, parse_mode="HTML")

    if s.odds:
        await message.answer(_value_analysis(s, p1, p2), parse_mode="HTML")

    s.stage = Stage.DONE


# ──────────────────────────────────────────────
# Хелперы
# ──────────────────────────────────────────────

def _resolve_team(s, team_raw: str | None) -> str | None:
    if not team_raw:
        return None
    q = team_raw.lower()
    if q in s.team1["name"].lower() or s.team1["name"].lower() in q:
        return "team1"
    if q in s.team2["name"].lower() or s.team2["name"].lower() in q:
        return "team2"
    for word in q.split():
        if len(word) > 2 and word in s.team1["name"].lower():
            return "team1"
        if len(word) > 2 and word in s.team2["name"].lower():
            return "team2"
    return None


def _picks_status(s) -> str:
    p1, p2 = s.picks_count()
    t1_picks = ", ".join(h["localized_name"] for h in s.picks["team1"]) or "—"
    t2_picks = ", ".join(h["localized_name"] for h in s.picks["team2"]) or "—"
    return (
        f"⚔️ <b>{s.team1['name']}</b> {p1}/5: {t1_picks}\n"
        f"⚔️ <b>{s.team2['name']}</b> {p2}/5: {t2_picks}"
    )


def _value_analysis(s, p1: float, p2: float) -> str:
    o = s.odds
    t1, t2 = s.team1["name"], s.team2["name"]
    lines = ["💰 <b>Анализ ставки (BetBoom)</b>\n"]

    def team_block(name, our_pct, odd):
        if not odd:
            return None
        implied_pct = round(100 / odd, 1)
        our_prob = our_pct / 100
        ev = round(our_prob * odd - 1, 3)  # Expected Value на 1 единицу
        value_delta = round(our_pct - implied_pct, 1)

        if value_delta >= 5:
            verdict = "✅ <b>ЕСТЬ VALUE</b>"
        elif value_delta >= 2:
            verdict = "⚠️ Слабый value"
        else:
            verdict = "❌ Нет value"

        return (
            f"{verdict}\n"
            f"<b>{name}</b>: кэф {odd}\n"
            f"  Рынок считает: {implied_pct}%\n"
            f"  Наш предикт:   {our_pct}%\n"
            f"  EV на 100₽: {'+' if ev >= 0 else ''}{round(ev * 100, 1)}₽"
        )

    b1 = team_block(t1, p1, o.get("team1"))
    b2 = team_block(t2, p2, o.get("team2"))
    if b1:
        lines.append(b1)
    if b2:
        if b1:
            lines.append("")
        lines.append(b2)

    return "\n".join(lines)


def _pct_bar(pct: float) -> str:
    """Мини-бар 5 блоков для одной стороны"""
    filled = round(pct / 20)  # 0-5 блоков
    return "█" * filled + "░" * (5 - filled)


# ──────────────────────────────────────────────
# Запуск
# ──────────────────────────────────────────────

async def main():
    print("Загружаю героев...")
    heroes_data = await api.fetch_heroes()
    hero_db.init_heroes(heroes_data)
    print(f"Загружено {len(heroes_data)} героев.")
    print("Бот запущен.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
