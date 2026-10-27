"""Menampilkan hasil pemotongan modul demo (untuk diperiksa dengan mata).

Cara pakai (dari folder proyek):
    python tools\\lihat_potongan.py
"""

import sys
from pathlib import Path

# Supaya "from app ..." dikenali saat skrip dijalankan langsung.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config  # noqa: E402
from app.pipeline.chunker import chunk_pages  # noqa: E402
from app.pipeline.ingest import load_pdf  # noqa: E402


def main() -> None:
    halaman = load_pdf(config.MODULE_DIR / "modul_demo.pdf")
    potongan = chunk_pages(halaman, module_id="DEMO")

    print(f"Jumlah potongan: {len(potongan)} (batas {config.CHUNK_TOKENS} token per potongan)")
    print()
    for p in potongan:
        baris_pertama = p.text.splitlines()[0]
        print(f"{p.chunk_id} | hal {p.page} | {p.tokens:>3} token | {len(p.code_blocks)} blok kode")
        print(f"    judul : {p.heading}")
        print(f"    mulai : {baris_pertama[:70]}")


if __name__ == "__main__":
    main()