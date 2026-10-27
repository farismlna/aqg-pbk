"""Titik masuk FastAPI.

Menyediakan health check dan route Fase 3 (modul, kurasi
dosen, dan kuis siswa). Galat tak terduga dijawab 500
dengan pesan umum, tanpa traceback mentah.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app import config
from app.api import router

app = FastAPI(title="AQG-DDP Prototype", version="0.3.0-phase3")
app.include_router(router)


@app.exception_handler(Exception)
async def _galat_internal(request: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, HTTPException):
        raise exc
    return JSONResponse(
        status_code=500, content={"detail": "Terjadi galat internal."}
    )


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "version": "0.3.0-phase3",
        "language": "Python 3.10+",
        "python_target": "3.13",
        "tokenizer": config.TOKENIZER_NAME,
        "mode": "replay",
    }
