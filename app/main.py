"""Titik masuk FastAPI.

Saat ini hanya menyediakan health check supaya server bisa
dijalankan dan diuji. Route modul, item, dan kuis dibuat
pada Fase 3. Frontend dibuat pada Fase 4.
"""

from fastapi import FastAPI

from app import config

app = FastAPI(title="AQG-DDP Prototype", version="0.2.0-phase2a")


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "version": "0.2.0-phase2a",
        "language": "Python 3.10+",
        "python_target": "3.13",
        "tokenizer": config.TOKENIZER_NAME,
        "mode": "replay",
    }
