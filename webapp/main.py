from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from bot.services.db import load_assessment
from bot.services.translate import translate_phrase, translate_word

app = FastAPI(title="Supreme-Speak-Clone Mini App")

app.mount("/static", StaticFiles(directory="webapp/static"), name="static")


@app.get("/correction/{session_id}")
async def correction_page(session_id: str) -> FileResponse:
    # HTML один и тот же для всех сессий — данные подтягиваются JS-ом
    # с клиента через /api/assessment/{session_id}, session_id уже есть в URL.
    return FileResponse("webapp/static/correction.html")


@app.get("/pronunciation/{session_id}")
async def pronunciation_page(session_id: str) -> FileResponse:
    return FileResponse("webapp/static/pronunciation.html")


@app.get("/transcript/{session_id}")
async def transcript_page(session_id: str) -> FileResponse:
    return FileResponse("webapp/static/transcript.html")


@app.get("/api/assessment/{session_id}")
async def get_assessment(session_id: str) -> dict:
    data = await load_assessment(session_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return data


class TranslateWordRequest(BaseModel):
    word: str
    context_sentence: str


class TranslatePhraseRequest(BaseModel):
    phrase: str


@app.post("/api/translate/word")
async def api_translate_word(body: TranslateWordRequest) -> dict:
    return await translate_word(body.word, body.context_sentence)


@app.post("/api/translate/phrase")
async def api_translate_phrase(body: TranslatePhraseRequest) -> dict:
    return await translate_phrase(body.phrase)
