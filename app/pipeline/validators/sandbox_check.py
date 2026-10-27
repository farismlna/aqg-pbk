"""Validator: kunci jawaban harus cocok dengan hasil eksekusi.

Menjalankan kode soal di sandbox, lalu membandingkan
keluaran sebenarnya dengan expected_output pada kunci.
Untuk isian rumpang, kode dijalankan dalam keadaan
sudah diisi kunci jawaban.
"""

from app import config
from app.pipeline.validators.sandbox import run_code
from app.schemas import BLANK_MARKER, Item, ValidatorResult


def _kode_terisi(item: Item) -> str:
    if item.code is None:
        return ""
    if item.item_format.value == "fill_in_blank":
        return item.code.replace(BLANK_MARKER, item.answer_key.text)
    return item.code


def validate_sandbox(item: Item) -> ValidatorResult:
    """Memeriksa keluaran eksekusi sama dengan expected_output."""
    if item.answer_key.expected_output is None:
        return ValidatorResult(
            name="sandbox",
            passed=True,
            detail="Tidak ada expected_output, pemeriksaan eksekusi dilewati.",
        )
    kode = _kode_terisi(item)
    if not kode.strip():
        return ValidatorResult(
            name="sandbox", passed=False, detail="Soal tidak punya kode."
        )
    hasil = run_code(kode)
    if hasil.timed_out:
        return ValidatorResult(
            name="sandbox",
            passed=False,
            detail=f"Kode kehabisan waktu (batas {config.SANDBOX_TIMEOUT_SECONDS} detik).",
        )
    if not hasil.ok:
        return ValidatorResult(
            name="sandbox",
            passed=False,
            detail=f"Kode gagal dijalankan: {hasil.stderr.strip()}",
        )
    keluaran = hasil.stdout.strip()
    diharapkan = item.answer_key.expected_output.strip()
    if keluaran != diharapkan:
        return ValidatorResult(
            name="sandbox",
            passed=False,
            detail=f"Keluaran sebenarnya {keluaran!r}, kunci mengklaim {diharapkan!r}.",
        )
    return ValidatorResult(
        name="sandbox",
        passed=True,
        detail=f"Keluaran eksekusi cocok dengan kunci: {keluaran!r}.",
    )
