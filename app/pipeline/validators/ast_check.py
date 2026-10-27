"""Validator: sintaks Python (ast.parse) sebuah butir soal.

Aturan:
- Kode soal harus bisa diuraikan ast.parse. Untuk isian
  rumpang, tanda ____ diganti dulu dengan kunci jawaban,
  karena ____ sendiri bukan Python yang valid.
- Bila sebuah pengecoh membawa mutated_code dan bertipe
  syntax_error, kode mutasi itu WAJIB gagal diuraikan.
  Bila ia justru lolos, klaim "kesalahan sintaks"-nya salah.
"""

import ast

from app.schemas import BLANK_MARKER, Item, MisconceptionType, ValidatorResult


def _kode_terisi(item: Item) -> str:
    if item.code is None:
        return ""
    if item.item_format.value == "fill_in_blank":
        return item.code.replace(BLANK_MARKER, item.answer_key.text)
    return item.code


def validate_ast(item: Item) -> ValidatorResult:
    """Memeriksa sintaks kode soal dan kode mutasi pengecoh."""
    kode = _kode_terisi(item)
    if not kode.strip():
        return ValidatorResult(
            name="ast", passed=False, detail="Soal tidak punya kode."
        )
    try:
        ast.parse(kode)
    except SyntaxError as galat:
        return ValidatorResult(
            name="ast",
            passed=False,
            detail=f"Kode soal gagal diuraikan: {type(galat).__name__}: {galat}",
        )

    for pengecoh in item.distractors:
        if (
            pengecoh.mutated_code
            and pengecoh.misconception_type == MisconceptionType.SYNTAX_ERROR
        ):
            try:
                ast.parse(pengecoh.mutated_code)
            except SyntaxError:
                continue
            return ValidatorResult(
                name="ast",
                passed=False,
                detail=(
                    "mutated_code pengecoh syntax_error justru lolos "
                    f"ast.parse: {pengecoh.text!r}"
                ),
            )
    return ValidatorResult(
        name="ast", passed=True, detail="Kode soal lolos ast.parse."
    )
