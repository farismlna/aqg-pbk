"""Membaca PDF modul menjadi daftar halaman teks.

Pemeriksaan yang dilakukan sebelum teks diambil:
- berkas ada dan ukurannya tidak melebihi batas,
- PDF tidak terkunci kata sandi,
- jumlah halaman tidak melebihi batas,
- PDF benar-benar berisi teks (bukan hasil pindai berupa gambar).
"""

from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

from app import config
from app.errors import IngestError


@dataclass(frozen=True)
class Page:
    """Satu halaman PDF. Nomor halaman dimulai dari 1."""

    number: int
    text: str


def load_pdf(path) -> list[Page]:
    """Membaca PDF dan mengembalikan daftar halaman.

    Melempar IngestError dengan pesan yang jelas bila PDF tidak bisa dipakai.
    """
    berkas = Path(path)
    if not berkas.is_file():
        raise IngestError(f"Berkas tidak ditemukan: {berkas}")

    ukuran = berkas.stat().st_size
    if ukuran > config.MAX_PDF_BYTES:
        raise IngestError(
            f"Berkas terlalu besar: {ukuran} byte "
            f"(batas {config.MAX_PDF_BYTES} byte)."
        )

    try:
        pembaca = PdfReader(str(berkas))
        if pembaca.is_encrypted:
            raise IngestError("PDF terkunci kata sandi dan tidak bisa dibaca.")

        jumlah = len(pembaca.pages)
        if jumlah == 0:
            raise IngestError("PDF tidak memiliki halaman.")
        if jumlah > config.MAX_PDF_PAGES:
            raise IngestError(
                f"PDF terlalu banyak halaman: {jumlah} "
                f"(batas {config.MAX_PDF_PAGES} halaman)."
            )

        halaman = [
            Page(number=nomor, text=(h.extract_text() or ""))
            for nomor, h in enumerate(pembaca.pages, start=1)
        ]
    except IngestError:
        raise
    except Exception as galat:  # pypdf bisa melempar bermacam galat
        raise IngestError(f"PDF tidak bisa dibaca: {galat}") from galat

    if not any(h.text.strip() for h in halaman):
        raise IngestError(
            "PDF tidak berisi teks yang bisa dibaca "
            "(mungkin hasil pindai berupa gambar)."
        )
    return halaman