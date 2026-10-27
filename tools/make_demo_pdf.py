"""Membuat PDF modul demo dari data/modules/modul_demo.txt.

Cara pakai (dari folder proyek):
    python tools\\make_demo_pdf.py

Hasil: data/modules/modul_demo.pdf (huruf Courier supaya spasi
indentasi kode tetap terjaga).
"""

import sys
from pathlib import Path

# Supaya "from app ..." dikenali saat skrip dijalankan langsung.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.pdfgen import canvas  # noqa: E402

from app import config  # noqa: E402

FONT = "Courier"
FONT_SIZE = 10
LEADING = 12          # jarak antar baris (poin)
MARGIN_X = 50
MARGIN_Y = 50


def main() -> None:
    sumber = config.MODULE_DIR / "modul_demo.txt"
    tujuan = config.MODULE_DIR / "modul_demo.pdf"

    teks = sumber.read_text(encoding="utf-8")
    baris_semua = teks.expandtabs(4).splitlines()

    for nomor, baris in enumerate(baris_semua, start=1):
        try:
            baris.encode("latin-1")
        except UnicodeEncodeError as galat:
            raise SystemExit(
                f"Baris {nomor} memuat karakter yang tidak didukung huruf "
                f"Courier standar: {galat.object[galat.start:galat.end]!r}"
            )

    lebar, tinggi = A4
    kanvas = canvas.Canvas(str(tujuan), pagesize=A4)
    kanvas.setTitle("Modul Demo Sintetis AQG-DDP")

    halaman = 1
    kanvas.setFont(FONT, FONT_SIZE)
    y = tinggi - MARGIN_Y
    for baris in baris_semua:
        if y < MARGIN_Y:
            kanvas.showPage()
            halaman += 1
            kanvas.setFont(FONT, FONT_SIZE)
            y = tinggi - MARGIN_Y
        kanvas.drawString(MARGIN_X, y, baris)
        y -= LEADING
    kanvas.save()

    print(f"PDF dibuat: {tujuan} ({halaman} halaman)")


if __name__ == "__main__":
    main()