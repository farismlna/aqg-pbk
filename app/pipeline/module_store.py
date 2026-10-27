"""Modul aktif Fase 3: potongan materi yang dipakai generate.

Saat server mulai, modul aktif adalah modul demo. Upload
modul baru mengganti potongan aktif selama server berjalan.
Modul hasil upload hanya disimpan di memori: berkasnya
tidak ditulis permanen, sehingga restart server kembali
ke modul demo. Isi PDF hasil upload disimpan di memori
supaya bisa ditampilkan di panel PDF Teacher Dashboard.
Keterbatasan ini dicatat di DEVIATIONS.md dan disengaja 
untuk v1, supaya pengujian tidak menulis berkas ke folder 
data dan perilaku server mudah diulang.
"""

import tempfile
from dataclasses import dataclass
from pathlib import Path

from app import config
from app.errors import ChunkError, IngestError
from app.pipeline.chunker import Chunk, chunk_pages
from app.pipeline.ingest import load_pdf

DEMO_MODULE_ID = "DEMO"
UPLOADED_MODULE_ID = "UPLOADED"


@dataclass(frozen=True)
class ActiveModule:
    """Keadaan modul aktif: id, nama berkas, potongan, jumlah halaman.

    pdf_bytes hanya terisi untuk modul hasil upload (isi PDF
    untuk panel PDF); modul demo dibaca dari disk oleh
    endpoint berkas modul, jadi nilainya None.
    """

    module_id: str
    filename: str | None
    chunks: list[Chunk]
    pages: int
    pdf_bytes: bytes | None = None



class ModuleStore:
    """Menyimpan modul aktif dan menggantinya dari berkas upload."""

    def __init__(self) -> None:
        self._active = self._muat_demo()

    @staticmethod
    def _muat_demo() -> ActiveModule:
        halaman = load_pdf(config.MODULE_DIR / "modul_demo.pdf")
        potongan = chunk_pages(halaman, module_id=DEMO_MODULE_ID)
        return ActiveModule(
            module_id=DEMO_MODULE_ID,
            filename="modul_demo.pdf",
            chunks=potongan,
            pages=len(halaman),
        )

    @property
    def active(self) -> ActiveModule:
        return self._active

    def replace_from_bytes(self, data: bytes, filename: str) -> ActiveModule:
        """Mengganti modul aktif dari isi berkas PDF yang diunggah.

        Melempar IngestError bila berkas bukan PDF, terlalu
        besar, atau tidak bisa dibaca; melempar ChunkError
        bila teksnya tidak bisa dipotong. Modul aktif lama
        dipertahankan bila penggantian gagal.
        """
        if data.lstrip()[:4] != b"%PDF":
            raise IngestError("Berkas yang diunggah bukan PDF.")
        if len(data) > config.MAX_PDF_BYTES:
            raise IngestError(
                f"Berkas terlalu besar: {len(data)} byte "
                f"(batas {config.MAX_PDF_BYTES} byte)."
            )
        with tempfile.NamedTemporaryFile(
            suffix=".pdf", delete=False
        ) as berkas_sementara:
            berkas_sementara.write(data)
            jalur = Path(berkas_sementara.name)
        try:
            halaman = load_pdf(jalur)
        finally:
            jalur.unlink(missing_ok=True)
        potongan = chunk_pages(halaman, module_id=UPLOADED_MODULE_ID)
        if not potongan:
            raise ChunkError("Tidak ada potongan yang dihasilkan dari PDF.")
        self._active = ActiveModule(
            module_id=UPLOADED_MODULE_ID,
            filename=filename,
            chunks=potongan,
            pages=len(halaman),
            pdf_bytes=data,
        )
        return self._active

    def reset(self) -> None:
        """Kembali ke modul demo. Dipakai pengujian dan restart logis."""
        self._active = self._muat_demo()


_STORE: ModuleStore | None = None


def get_module_store() -> ModuleStore:
    """Satu-satunya ModuleStore untuk proses ini (dibuat saat pertama dipakai)."""
    global _STORE
    if _STORE is None:
        _STORE = ModuleStore()
    return _STORE


def reset_module_store() -> None:
    """Membuang ModuleStore supaya pemakaian berikutnya memuat modul demo lagi."""
    global _STORE
    _STORE = None
