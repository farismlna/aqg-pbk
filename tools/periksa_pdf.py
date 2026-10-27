"""Memeriksa PDF modul demo: jumlah halaman dan spasi pada kode.

Cara pakai (dari folder proyek):
    python tools\\periksa_pdf.py
"""

import sys
from pathlib import Path

# Supaya "from app ..." dikenali saat skrip dijalankan langsung.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pypdf import PdfReader  # noqa: E402

from app import config  # noqa: E402

# Baris yang indentasinya harus tetap utuh setelah diambil dari PDF.
BARIS_WAJIB = [
    "4 |     total += i",
    "    for elemen in range(start, stop):",
    "        # blok instruksi yang diulang",
    '3 |     print("A")',
]


def main() -> None:
    berkas = config.MODULE_DIR / "modul_demo.pdf"
    pembaca = PdfReader(str(berkas))
    jumlah_halaman = len(pembaca.pages)
    teks = "\n".join(
        (halaman.extract_text() or "") for halaman in pembaca.pages
    )

    print(f"Jumlah halaman : {jumlah_halaman} (batas {config.MAX_PDF_PAGES})")
    hilang = 0
    for baris in BARIS_WAJIB:
        ada = baris in teks
        print(f"{'ADA   ' if ada else 'HILANG'} : {baris!r}")
        if not ada:
            hilang += 1

    if hilang or jumlah_halaman > config.MAX_PDF_PAGES:
        raise SystemExit("PEMERIKSAAN GAGAL")
    print("PEMERIKSAAN LOLOS")


if __name__ == "__main__":
    main()