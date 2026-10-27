"""Titik masuk FastAPI.

Menyediakan health check, route Fase 3 (modul, kurasi
dosen, dan kuis siswa), dan frontend Fase 4 (HTML, CSS,
dan JavaScript vanila dari folder app/static). Galat tak
terduga dijawab 500 dengan pesan umum, tanpa traceback
mentah.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app import config
from app.api import router

STATIC_DIR = config.BASE_DIR / "app" / "static"

app = FastAPI(title="AQG-DDP Prototype", version="0.4.0-phase4")
app.include_router(router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.exception_handler(Exception)
async def _galat_internal(request: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, HTTPException):
        raise exc
    return JSONResponse(
        status_code=500, content={"detail": "Terjadi galat internal."}
    )


@app.get("/")
def index():
    """Halaman utama frontend (routing memakai hash di JavaScript)."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "version": "0.4.0-phase4",
        "language": "Python 3.10+",
        "python_target": "3.13",
        "tokenizer": config.TOKENIZER_NAME,
        "mode": "replay",
    }
