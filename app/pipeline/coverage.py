"""Menghitung coverage dari potongan materi yang terambil.

Coverage adalah bagian dari keluaran Planner (lihat app/schemas.py):
judul bagian materi yang tersentuh, dan konstruksi kode yang
tersentuh. Heading diambil apa adanya dari potongan, dengan
urutan kemunculan yang dipertahankan dan tanpa ganda. Konstruksi
kode diambil dari blok kode potongan dengan ast, misalnya For
dan Call:range. Blok kode yang tidak bisa diuraikan ast dilewati,
supaya satu cuplikan yang tidak lengkap tidak menggagalkan
seluruh pengambilan.
"""

import ast

from app.pipeline.chunker import Chunk
from app.schemas import Coverage

# Nama simpul ast yang tidak memberi arti sebagai konstruksi kode.
_ABAIKAN = {
    "Module",
    "Expr",
    "Load",
    "Store",
    "Del",
    "Name",
    "Constant",
    "Pass",
    "Break",
    "Continue",
    "alias",
    "keyword",
    "arguments",
    "arg",
    "comprehension",
}


def _nama_panggilan(simpul: ast.Call) -> str:
    """Nama fungsi yang dipanggil, misalnya Call:range atau Call:len."""
    fungsi = simpul.func
    if isinstance(fungsi, ast.Name):
        return f"Call:{fungsi.id}"
    if isinstance(fungsi, ast.Attribute):
        return f"Call:{fungsi.attr}"
    return "Call"


def _konstruksi_dari_kode(kode: str, terkumpul: list[str]) -> None:
    """Menambahkan konstruksi kode dari satu blok, tanpa ganda."""
    try:
        pohon = ast.parse(kode)
    except SyntaxError:
        return
    for simpul in ast.walk(pohon):
        if isinstance(simpul, ast.Call):
            nama = _nama_panggilan(simpul)
        else:
            nama = type(simpul).__name__
        if nama in _ABAIKAN:
            continue
        if nama not in terkumpul:
            terkumpul.append(nama)


def build_coverage(chunks: list[Chunk]) -> Coverage:
    """Menghitung coverage dari potongan, dalam urutan potongan."""
    judul: list[str] = []
    for potongan in chunks:
        if potongan.heading not in judul:
            judul.append(potongan.heading)
    konstruksi: list[str] = []
    for potongan in chunks:
        for blok in potongan.code_blocks:
            _konstruksi_dari_kode(blok, konstruksi)
    return Coverage(headings=judul, code_constructs=konstruksi)
