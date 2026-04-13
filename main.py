"""
FastAPI backend для Dota 2 Predict Web App
"""
import asyncio
import os
import tempfile
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

import api
import heroes as hero_db
import parser as nlp
from predictor import predict
from session import Session

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    heroes_data = await api.fetch_heroes()
    hero_db.init_heroes(heroes_data)
    print(f"Loaded {len(heroes_data)} heroes.")


# ──────────────────────────────────────────────
# API endpoints
# ──────────────────────────────────────────────

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
    picks: dict   # {"team1": [{id, localized_name, roles}], "team2": [...]}
    bans: dict    # {"team1": [...], "team2": [...]}
    odds: Optional[dict] = None  # {"team1": float, "team2": float}


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


@app.post("/api/predict")
async def run_predict(body: PredictBody):
    # Создаём session-like объект для predictor
    s = Session()
    s.team1 = body.team1
    s.team2 = body.team2
    s.picks = body.picks
    s.bans = body.bans
    s.odds = body.odds
    try:
        result = await predict(s)
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
