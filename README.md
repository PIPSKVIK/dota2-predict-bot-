# Dota 2 Predict

> **Pet project** — built for fun and personal use while watching Dota 2 tournaments.

A web app that predicts Dota 2 match outcomes based on team picks. Enter picks for both teams via voice or text — get win probability with a breakdown by factors.

Special thanks to [Liquipedia](https://liquipedia.net) for their open API with match schedules and team data — half of this wouldn't work without it.

## Стек

- **Бэкенд**: Python + FastAPI + uvicorn
- **Фронт**: React + Vite
- **БД**: SQLite (`insights.db`) — инсайды + история предиктов
- **Данные**: OpenDota API (H2H, рейтинги, героев)
- **LLM**: Groq — транскрипция голоса (Whisper) + парсинг текста (Llama 3.3)

## Запуск локально

**Бэкенд:**
```bash
cd dota2-predict-bot
pip install -r requirements.txt
cp .env.example .env  # заполни токены
python -m uvicorn main:app --port 8000 --reload
```

**Фронт:**
```bash
cd frontend
npm install
npm run dev
```

Открыть: http://localhost:5174

## .env

```
BOT_TOKEN=...          # Telegram бот (не используется в веб-версии)
GROQ_API_KEY=...       # Groq API — голос + парсинг
OPENDOTA_API_KEY=      # опционально, без него работает с лимитами
ADMIN_PASSWORD=...     # пароль для входа в приложение
```

## Структура

```
main.py           — FastAPI, все эндпоинты, авторизация
predictor.py      — логика предсказания (H2H, рейтинг, каунтеры, синергии, мета)
api.py            — запросы к OpenDota API
heroes.py         — список героев, русские алиасы, поиск
parser.py         — Groq: транскрипция голоса, парсинг пиков/команд
insights.py       — мета-инсайды: хранение в SQLite, парсинг через LLM
history.py        — история предиктов: сохранение, результаты, статистика
session.py        — модель сессии (используется предиктором)
bot.py            — Telegram бот (старая версия, не используется)

frontend/
  src/
    App.jsx                    — главный компонент, навигация, авторизация
    api/index.js               — все API-запросы
    components/
      HeroSearch.jsx           — поиск героя с автодополнением и голосом
      HeroChip.jsx             — чип выбранного героя
      TeamSearch.jsx           — поиск команды
      VoiceButton.jsx          — кнопка записи голоса
      PredictResult.jsx        — экран результата + live-обновление
    hooks/
      useVoiceRecorder.js      — хук записи аудио через MediaRecorder
    pages/
      Login.jsx                — экран авторизации
      Insights.jsx             — мета-инсайды
      History.jsx              — история предиктов
```

## Флоу приложения

1. **Команды** — поиск по названию (текст или голос), валидация через OpenDota
2. **Баны** — до 7 банов на команду (опционально)
3. **Пики** — 5 героев на команду, поиск с автодополнением (↑↓ + Enter)
4. **Кэфы** — коэффициенты букмекера (опционально, влияют на анализ ставки)
5. **Результат** — % победы каждой команды + факторы + история встреч

## Факторы предикта

| Фактор | Вес |
|---|---|
| H2H история | 28% |
| Рейтинг команд | 19% |
| Каунтеры героев | 19% |
| Синергии пиков | 14% |
| Winrate героев | 10% |
| Фит пиков команды | 5% |
| Мета-инсайды | 5% |

При live-обновлении (килы + голд) добавляется live-фактор с весом до 50%.

## API эндпоинты

```
POST /api/login                     — авторизация
POST /api/logout                    — выход

GET  /api/heroes                    — все герои
GET  /api/heroes/search?q=          — поиск героя
GET  /api/teams/search?q=           — поиск команды

POST /api/predict                   — расчёт предикта
POST /api/transcribe                — транскрипция аудио
POST /api/parse/teams               — парсинг команд из текста
POST /api/parse/hero                — парсинг героя из текста

GET  /api/insights                  — список инсайдов
POST /api/insights                  — добавить инсайд
DELETE /api/insights/:id            — удалить инсайд

GET  /api/history                   — история предиктов
GET  /api/history/stats             — статистика точности
PATCH /api/history/:id/result       — внести результат матча
```

## Деплой

Планируется на Timeweb VPS (82.97.249.170), рядом с WoW AH Analyzer.
