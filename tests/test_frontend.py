"""Pengujian penyajian frontend Fase 4 dan berkas modul.

Memeriksa route halaman utama, berkas statis, berkas PDF
modul, dan pilihan kuis yang memuat kunci sebagai salah
satu pilihan tanpa penanda. Alur klik di browser diperiksa
manual dengan daftar periksa Fase 4, bukan di sini.
"""

import pytest
from fastapi.testclient import TestClient

from app import config
from app.main import app
from app.pipeline.module_store import reset_module_store

client = TestClient(app)


@pytest.fixture(autouse=True)
def db_sementara(tmp_path, monkeypatch):
    """Database sementara dan modul demo yang dimuat ulang."""
    monkeypatch.setattr(config, "DATABASE_PATH", tmp_path / "uji.db")
    reset_module_store()
    yield
    reset_module_store()


def test_halaman_utama_mengembalikan_html():
    respons = client.get("/")
    assert respons.status_code == 200
    assert "text/html" in respons.headers["content-type"]
    assert "AQG-DDP" in respons.text
    assert "/static/app.js" in respons.text
    assert "/static/style.css" in respons.text


def test_berkas_statis_terlayani():
    css = client.get("/static/style.css")
    assert css.status_code == 200
    assert "status-published" in css.text
    js = client.get("/static/app.js")
    assert js.status_code == 200
    assert "/api/quiz/session" in js.text
    assert "innerHTML" not in js.text


def test_berkas_modul_demo_adalah_pdf():
    respons = client.get("/api/modules/file")
    assert respons.status_code == 200
    assert respons.headers["content-type"] == "application/pdf"
    assert respons.content[:4] == b"%PDF"


def test_berkas_modul_hasil_upload():
    pdf_demo = (config.MODULE_DIR / "modul_demo.pdf").read_bytes()
    unggah = client.post(
        "/api/modules",
        files={"file": ("modul.pdf", pdf_demo, "application/pdf")},
    )
    assert unggah.status_code == 200
    respons = client.get("/api/modules/file")
    assert respons.status_code == 200
    assert respons.content[:4] == b"%PDF"
    assert respons.content == pdf_demo


def test_kuis_memuat_kunci_sebagai_pilihan_tanpa_penanda():
    client.post(
        "/api/generate",
        json={
            "topic": "Percabangan",
            "query": "percabangan if elif",
            "key_concepts": ["if", "elif", "else"],
            "limit": 2,
        },
    )
    assert client.post("/api/items/MCQ-01/approve").status_code == 200
    assert client.post("/api/items/MCQ-01/publish").status_code == 200
    kuis = client.get("/api/quiz").json()
    assert len(kuis) == 1
    soal = kuis[0]
    assert [p["option_id"] for p in soal["distractors"]] == ["A", "B", "C", "D"]
    assert {p["text"] for p in soal["distractors"]} == {"40", "60", "20", "30"}
    for pilihan in soal["distractors"]:
        assert "feedback" not in pilihan
        assert "misconception_type" not in pilihan
