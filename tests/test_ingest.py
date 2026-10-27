import pytest
from reportlab.pdfgen import canvas

from app import config
from app.errors import IngestError
from app.pipeline.ingest import load_pdf


def buat_pdf(jalur, jumlah_halaman, dengan_teks=True):
    """Membuat PDF sederhana untuk pengujian."""
    kanvas = canvas.Canvas(str(jalur))
    for nomor in range(1, jumlah_halaman + 1):
        if dengan_teks:
            kanvas.drawString(50, 800, f"Isi halaman {nomor}")
        kanvas.showPage()
    kanvas.save()
    return jalur


def test_modul_demo_terbaca(halaman_demo):
    assert 1 <= len(halaman_demo) <= config.MAX_PDF_PAGES
    assert halaman_demo[0].number == 1
    assert "Topik 04" in halaman_demo[0].text


def test_berkas_tidak_ada(tmp_path):
    with pytest.raises(IngestError, match="tidak ditemukan"):
        load_pdf(tmp_path / "tidak_ada.pdf")


def test_terlalu_banyak_halaman(tmp_path):
    pdf = buat_pdf(tmp_path / "panjang.pdf", config.MAX_PDF_PAGES + 1)
    with pytest.raises(IngestError, match="halaman"):
        load_pdf(pdf)


def test_pdf_tanpa_teks_ditolak(tmp_path):
    pdf = buat_pdf(tmp_path / "kosong.pdf", 1, dengan_teks=False)
    with pytest.raises(IngestError, match="teks"):
        load_pdf(pdf)


def test_berkas_terlalu_besar(tmp_path, monkeypatch):
    pdf = buat_pdf(tmp_path / "kecil.pdf", 1)
    monkeypatch.setattr(config, "MAX_PDF_BYTES", 100)
    with pytest.raises(IngestError, match="besar"):
        load_pdf(pdf)