"""
FastAPI backend для Dota 2 Predict Web App
"""
import asyncio
import os
import tempfile
import secrets
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

ADMIN_LOGIN    = "admin"
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "changeme")
_sessions: set[str] = set()

def _get_session(request: Request) -> str | None:
    return request.cookies.get("dota_sess")

def _is_auth(request: Request) -> bool:
    token = _get_session(request)
    return token is not None and token in _sessions

import api
import heroes as hero_db
import parser as nlp
import insights as insight_db
import history as history_db
import schedule as schedule_mod
from predictor import predict
from session import Session

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    public = {"/api/login", "/api/logout"}
    if request.url.path.startswith("/api/") and request.url.path not in public:
        if not _is_auth(request):
            return JSONResponse({"error": "Unauthorized"}, status_code=401)
    return await call_next(request)


@app.on_event("startup")
async def startup():
    insight_db.init_db()
    history_db.init_db()
    try:
        heroes_data = await api.fetch_heroes()
    except Exception as e:
        print(f"Warning: could not load heroes at startup ({e}), will retry on first request")
        heroes_data = []
    hero_db.init_heroes(heroes_data)
    print(f"Loaded {len(heroes_data)} heroes.")


# ──────────────────────────────────────────────
# API endpoints
# ──────────────────────────────────────────────

class LoginBody(BaseModel):
    login: str
    password: str

@app.post("/api/login")
async def login(body: LoginBody, response: Response):
    if body.login == ADMIN_LOGIN and body.password == ADMIN_PASSWORD:
        token = secrets.token_hex(32)
        _sessions.add(token)
        response.set_cookie("dota_sess", token, httponly=True, samesite="strict", max_age=30*24*3600)
        return {"ok": True}
    raise HTTPException(status_code=401, detail="Неверный логин или пароль")

@app.post("/api/logout")
async def logout(request: Request, response: Response):
    token = _get_session(request)
    if token:
        _sessions.discard(token)
    response.delete_cookie("dota_sess")
    return {"ok": True}


@app.get("/api/heroes")
async def get_heroes():
    return hero_db.get_all_heroes()


@app.get("/api/heroes/search")
async def search_heroes(q: str = ""):
    if not q or len(q) < 1:
        return []
    return hero_db.suggest_heroes(q, limit=8)


@app.get("/api/teams/search")
async def search_team(q: str = ""):
    if not q or len(q) < 2:
        return None
    team = await api.search_team(q)
    return team


class TextBody(BaseModel):
    text: str

class ParseHeroBody(BaseModel):
    text: str
    team1: str = ""
    team2: str = ""

class PredictBody(BaseModel):
    team1: dict
    team2: dict
    picks: dict            # {"team1": [{id, localized_name, roles}], "team2": [...]}
    bans: dict             # {"team1": [...], "team2": [...]}
    odds: Optional[dict] = None       # {"team1": float, "team2": float}
    live_data: Optional[dict] = None  # {"kills_team1": int, "kills_team2": int, "gold_advantage": int}


@app.post("/api/parse/teams")
async def parse_teams_endpoint(body: TextBody):
    return await nlp.parse_teams(body.text)


@app.post("/api/parse/hero")
async def parse_hero_endpoint(body: ParseHeroBody):
    return await nlp.parse_pick_ban(body.text, body.team1, body.team2)


@app.post("/api/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    suffix = ".ogg"
    if audio.filename:
        ext = os.path.splitext(audio.filename)[1]
        if ext:
            suffix = ext
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await audio.read())
        tmp_path = tmp.name
    try:
        text = await nlp.transcribe_voice(tmp_path)
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.unlink(tmp_path)


@app.get("/api/schedule")
async def get_schedule():
    return await schedule_mod.get_matches()


@app.get("/api/insights")
async def get_insights():
    return insight_db.get_all()

@app.post("/api/insights")
async def add_insight(body: TextBody):
    return await insight_db.parse_and_save(body.text)

@app.delete("/api/insights/{insight_id}")
async def delete_insight(insight_id: int):
    insight_db.delete_insight(insight_id)
    return {"ok": True}


@app.get("/api/history")
async def get_history():
    return history_db.get_all()

@app.get("/api/history/stats")
async def get_history_stats():
    return history_db.get_stats()

class ResultBody(BaseModel):
    actual_winner: str

@app.patch("/api/history/{prediction_id}/result")
async def set_result(prediction_id: int, body: ResultBody):
    row = history_db.set_result(prediction_id, body.actual_winner)
    if not row:
        raise HTTPException(status_code=404, detail="Предикт не найден")
    return row


@app.post("/api/predict")
async def run_predict(body: PredictBody):
    s = Session()
    s.team1 = body.team1
    s.team2 = body.team2
    s.picks = body.picks
    s.bans = body.bans
    s.odds = body.odds
    s.live_data = body.live_data
    try:
        result = await predict(s)
        if not body.live_data:
            pred_id = history_db.save_prediction(result, body.picks)
            result["prediction_id"] = pred_id
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────
# Serve React static files
# ──────────────────────────────────────────────

FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "frontend", "dist")

if os.path.exists(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        index = os.path.join(FRONTEND_DIST, "index.html")
        return FileResponse(index)
