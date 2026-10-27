"""Pengujian API Fase 3: modul, kurasi, dan kuis siswa.

Setiap pengujian memakai database SQLite sementara dan
modul demo yang dimuat ulang, supaya tidak ada keadaan
yang bocor antar pengujian dan tidak ada berkas yang
tertulis ke folder data proyek.
"""

import pytest
from fastapi.testclient import TestClient

from app import config, storage
from app.main import app
from app.pipeline.module_store import reset_module_store

client = TestClient(app)

PERMINTAAN_GENERATE = {
    "topic": "Percabangan",
    "query": "percabangan if elif",
    "key_concepts": ["if", "elif", "else"],
    "limit": 2,
}


@pytest.fixture(autouse=True)
def db_sementara(tmp_path, monkeypatch):
    """Arahkan database ke berkas sementara dan mulai dari modul demo."""
    monkeypatch.setattr(config, "DATABASE_PATH", tmp_path / "uji.db")
    reset_module_store()
    yield
    reset_module_store()


def generate_dua() -> list:
    respons = client.post("/api/generate", json=PERMINTAAN_GENERATE)
    assert respons.status_code == 200, respons.text
    return respons.json()["items"]


def terbitkan(item_id: str) -> None:
    assert client.post(f"/api/items/{item_id}/approve").status_code == 200
    assert client.post(f"/api/items/{item_id}/publish").status_code == 200


def test_generate_menyimpan_draft_dan_menolak_yang_gagal():
    # Batas 10 supaya semua 8 kandidat replay dicoba, bukan
    # berhenti setelah 2 yang diterima (perilaku orchestrator).
    permintaan = dict(PERMINTAAN_GENERATE, limit=10)
    respons = client.post("/api/generate", json=permintaan)
    assert respons.status_code == 200
    data = respons.json()
    assert data["planner"]["status"] == "ok"
    ids = [item["item"]["item_id"] for item in data["items"]]
    assert ids == ["MCQ-01", "FIB-01"]
    assert all(item["status"] == "draft" for item in data["items"])
    assert {r["candidate_id"] for r in data["rejected"]} == {
        "BAD-SCHEMA-01",
        "BAD-AST-01",
        "BAD-KEY-01",
        "BAD-DUPLICATE-01",
        "BAD-LINT-01",
        "BAD-FILL-01",
    }


def test_generate_tanpa_materi_tidak_mencoba_kandidat():
    respons = client.post(
        "/api/generate",
        json={
            "topic": "Pewarisan",
            "query": "kelas pewarisan enkapsulasi polimorfisme",
            "key_concepts": ["kelas"],
            "limit": 2,
        },
    )
    assert respons.status_code == 200
    data = respons.json()
    assert data["planner"]["status"] == "insufficient_context"
    assert data["items"] == []
    assert data["rejected"] == []


def test_generate_kedua_tidak_menimpa_yang_sudah_disetujui():
    generate_dua()
    terbitkan("MCQ-01")
    generate_dua()
    detail = client.get("/api/items/MCQ-01").json()
    assert detail["status"] == "published"


def test_alur_kurasi_dan_transisi_tidak_sah():
    generate_dua()
    # Draft tidak bisa langsung terbit.
    assert client.post("/api/items/FIB-01/publish").status_code == 409
    terbitkan("MCQ-01")
    # Yang sudah terbit tidak bisa disetujui lagi atau ditolak.
    assert client.post("/api/items/MCQ-01/approve").status_code == 409
    assert client.post("/api/items/MCQ-01/reject").status_code == 409
    # Item yang tidak ada: 404.
    assert client.get("/api/items/TIDAK-ADA").status_code == 404
    # Saring menurut status.
    terbit = client.get("/api/items", params={"status": "published"}).json()
    assert [item["item"]["item_id"] for item in terbit] == ["MCQ-01"]


def test_edit_gagal_tidak_mengubah_yang_tersimpan_lalu_edit_benar():
    generate_dua()
    asli = client.get("/api/items/MCQ-01").json()["item"]
    rusak = dict(asli)
    rusak["code"] = "skor = 10\nif skor > 5\n    print(1)"
    respons = client.put("/api/items/MCQ-01", json=rusak)
    assert respons.status_code == 422
    assert "report" in respons.json()["detail"]
    masih_asli = client.get("/api/items/MCQ-01").json()
    assert masih_asli["item"]["code"] == asli["code"]
    # Edit yang sah: hanya mengubah stem, status kembali ke draft.
    terbitkan("MCQ-01")
    diubah = dict(asli)
    diubah["stem"] = "Berapakah keluaran program berikut?"
    respons = client.put("/api/items/MCQ-01", json=diubah)
    assert respons.status_code == 200, respons.text
    assert respons.json()["status"] == "draft"
    assert respons.json()["item"]["stem"] == "Berapakah keluaran program berikut?"
    # item_id pada isi harus sama dengan pada alamat.
    diubah["item_id"] = "MCQ-99"
    assert client.put("/api/items/MCQ-01", json=diubah).status_code == 422


def test_kuis_menyembunyikan_kunci_dan_menilai_jawaban():
    generate_dua()
    # Belum terbit: kuis kosong dan jawaban ditolak.
    assert client.get("/api/quiz").json() == []
    sesi = client.post("/api/quiz/session").json()["session_id"]
    assert (
        client.post(
            "/api/quiz/answer",
            json={"session_id": sesi, "item_id": "MCQ-01", "chosen": "A"},
        ).status_code
        == 404
    )
    terbitkan("MCQ-01")
    terbitkan("FIB-01")
    kuis = client.get("/api/quiz").json()
    assert [soal["item_id"] for soal in kuis] == ["MCQ-01", "FIB-01"]
    for soal in kuis:
        assert "answer_key" not in soal
        for pengecoh in soal["distractors"]:
            assert "feedback" not in pengecoh
            assert "misconception_type" not in pengecoh
    # Jawaban salah pilihan ganda: umpan balik distraktornya.
    salah = client.post(
        "/api/quiz/answer",
        json={"session_id": sesi, "item_id": "MCQ-01", "chosen": "B"},
    )
    assert salah.status_code == 200
    assert salah.json()["correct"] is False
    assert salah.json()["feedback"]["diagnosis"] == "Anda mungkin mengira ..."
    assert salah.json()["expected_output"] == "40"
    # Jawaban benar isian rumpang.
    benar = client.post(
        "/api/quiz/answer",
        json={"session_id": sesi, "item_id": "FIB-01", "chosen": "elif"},
    )
    assert benar.json()["correct"] is True
    assert benar.json()["expected_output"] == "A"
    # Rekap sesi.
    rekap = client.get("/api/quiz/summary", params={"session_id": sesi}).json()
    assert rekap["total"] == 2
    assert rekap["correct"] == 1


def test_session_id_harus_uuid():
    generate_dua()
    terbitkan("MCQ-01")
    assert (
        client.post(
            "/api/quiz/answer",
            json={
                "session_id": "bukan-uuid",
                "item_id": "MCQ-01",
                "chosen": "A",
            },
        ).status_code
        == 422
    )
    assert (
        client.get(
            "/api/quiz/summary", params={"session_id": "bukan-uuid"}
        ).status_code
        == 422
    )


def test_upload_modul_mengganti_modul_aktif_dan_menolak_bukan_pdf():
    pdf_demo = (config.MODULE_DIR / "modul_demo.pdf").read_bytes()
    respons = client.post(
        "/api/modules",
        files={"file": ("modul.pdf", pdf_demo, "application/pdf")},
    )
    assert respons.status_code == 200, respons.text
    assert respons.json()["module_id"] == "UPLOADED"
    assert respons.json()["chunks"] == 5
    info = client.get("/api/modules").json()
    assert info["filename"] == "modul.pdf"
    assert info["module_id"] == "UPLOADED"
    # Bukan PDF: modul aktif tetap yang sudah diunggah.
    respons = client.post(
        "/api/modules",
        files={"file": ("teks.txt", b"halo", "text/plain")},
    )
    assert respons.status_code == 400
    assert client.get("/api/modules").json()["module_id"] == "UPLOADED"


def test_upload_terlalu_besar_ditolak(monkeypatch):
    # Muat modul demo dulu, sebelum batas diperkecil, supaya
    # pembuatan ModuleStore tidak ikut terkena batas pengujian.
    assert client.get("/api/modules").status_code == 200
    monkeypatch.setattr(config, "MAX_PDF_BYTES", 10)
    pdf_demo = (config.MODULE_DIR / "modul_demo.pdf").read_bytes()
    respons = client.post(
        "/api/modules",
        files={"file": ("modul.pdf", pdf_demo, "application/pdf")},
    )
    assert respons.status_code == 400
    assert client.get("/api/modules").json()["module_id"] == "DEMO"


def test_galat_internal_tanpa_traceback(monkeypatch):
    def _rusak(status=None, path=None):
        raise RuntimeError("rusak sengaja")

    monkeypatch.setattr(storage, "list_items", _rusak)
    klien = TestClient(app, raise_server_exceptions=False)
    respons = klien.get("/api/items")
    assert respons.status_code == 500
    assert respons.json() == {"detail": "Terjadi galat internal."}
    assert "Traceback" not in respons.text
    assert "rusak sengaja" not in respons.text


def test_regenerate_menjalankan_ulang_tanpa_mengubah_butir_lama():
    generate_dua()
    terbitkan("MCQ-01")
    respons = client.post("/api/items/MCQ-01/regenerate", json={})
    assert respons.status_code == 200, respons.text
    assert respons.json()["planner"]["status"] == "ok"
    # Butir lama tetap terbit; regenerate tidak menimpanya.
    assert client.get("/api/items/MCQ-01").json()["status"] == "published"
