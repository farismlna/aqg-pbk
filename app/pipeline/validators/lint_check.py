"""Validator: gaya kode PEP 8 (linter pycodestyle).

Hanya aturan yang masuk akal untuk cuplikan soal yang
diperiksa: baris terlalu panjang (diperiksa eksplisit,
karena pycodestyle tidak menandai baris komentar),
indentasi tab (W191) dan indentasi yang salah
(E101/E111/E112/E113/E117), serta galat sintaks
pycodestyle (E9). Aturan baris kosong
antar definisi dan sejenisnya sengaja tidak dipakai, karena
cuplikan soal bukan berkas Python utuh.

Ini Delta 1: ast.parse hanya memeriksa sintaks, bukan gaya.
"""

import io
from contextlib import redirect_stdout

import pycodestyle

from app import config
from app.schemas import BLANK_MARKER, Item, ValidatorResult

_SELECT = ["E101", "E111", "E112", "E113", "E117", "W191", "E9"]


def _kode_terisi(item: Item) -> str:
    if item.code is None:
        return ""
    if item.item_format.value == "fill_in_blank":
        return item.code.replace(BLANK_MARKER, item.answer_key.text)
    return item.code


def validate_lint(item: Item) -> ValidatorResult:
    """Memeriksa gaya kode soal dengan pycodestyle."""
    kode = _kode_terisi(item)
    if not kode.strip():
        return ValidatorResult(
            name="lint", passed=False, detail="Soal tidak punya kode."
        )
    baris = kode.splitlines(keepends=True)
    # Panjang baris diperiksa eksplisit, karena pycodestyle
    # tidak menandai baris yang hanya berisi komentar.
    panjang = [
        f"baris {i}: {len(b.rstrip(chr(10)))} karakter"
        for i, b in enumerate(baris, start=1)
        if len(b.rstrip("\n")) > config.MAX_LINE_LENGTH
    ]
    if panjang:
        return ValidatorResult(
            name="lint",
            passed=False,
            detail=(
                f"Baris melebihi {config.MAX_LINE_LENGTH} karakter: "
                + ", ".join(panjang)
            ),
        )
    if not baris[-1].endswith("\n"):
        baris[-1] = baris[-1] + "\n"
    panduan = pycodestyle.StyleGuide(
        quiet=True,
        max_line_length=config.MAX_LINE_LENGTH,
        select=_SELECT,
    )
    keluaran = io.StringIO()
    with redirect_stdout(keluaran):
        pemeriksa = pycodestyle.Checker(lines=baris, options=panduan.options)
        jumlah = pemeriksa.check_all()
    if jumlah:
        return ValidatorResult(
            name="lint",
            passed=False,
            detail=keluaran.getvalue().strip(),
        )
    return ValidatorResult(
        name="lint",
        passed=True,
        detail=f"Tidak ada pelanggaran PEP 8 yang diperiksa (maks {config.MAX_LINE_LENGTH} karakter per baris).",
    )
