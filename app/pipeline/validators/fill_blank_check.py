"""Validator: keunikan jawaban isian rumpang (fill-in-the-blank).

Mengganti tanda ____ dengan setiap kandidat jawaban
(kunci yang diterima + semua jawaban salah yang
diperkirakan), lalu menjalankan tiap versi di sandbox.

Aturan lolos:
- Setiap jawaban yang diterima harus menghasilkan
  persis expected_output.
- Tidak satu pun jawaban salah boleh menghasilkan
  persis expected_output (boleh keluaran lain, atau
  galat, termasuk SyntaxError).

Validator ini hanya berlaku untuk isian rumpang; untuk
pilihan ganda ia lolos begitu saja (dilewati).
"""

from app.pipeline.validators.sandbox import run_code
from app.schemas import BLANK_MARKER, Item, ValidatorResult


def _hasil(kode_terisi: str) -> str:
    """Keluaran eksekusi, atau nama galatnya bila gagal."""
    hasil = run_code(kode_terisi)
    if hasil.timed_out:
        return "TimeoutError"
    if not hasil.ok:
        # Baris terakhir stderr biasanya menyebut nama galatnya.
        baris = [b for b in hasil.stderr.strip().splitlines() if b.strip()]
        if baris:
            return baris[-1].split(":")[0].strip()
        return f"Exit({hasil.returncode})"
    return hasil.stdout.strip()


def validate_fill_blank(item: Item) -> ValidatorResult:
    """Memeriksa keunikan jawaban isian rumpang di sandbox."""
    if item.item_format.value != "fill_in_blank":
        return ValidatorResult(
            name="fill_blank",
            passed=True,
            detail="Bukan soal isian rumpang, pemeriksaan dilewati.",
        )
    if item.code is None or BLANK_MARKER not in item.code:
        return ValidatorResult(
            name="fill_blank",
            passed=False,
            detail="Soal isian wajib punya kode berisi tanda ____.",
        )
    if item.answer_key.expected_output is None:
        return ValidatorResult(
            name="fill_blank",
            passed=False,
            detail="Soal isian wajib punya expected_output untuk diperiksa.",
        )
    diharapkan = item.answer_key.expected_output.strip()
    catatan: list[str] = []
    for jawaban in item.accepted_answers:
        hasil = _hasil(item.code.replace(BLANK_MARKER, jawaban))
        catatan.append(f"{jawaban!r} -> {hasil!r}")
        if hasil != diharapkan:
            return ValidatorResult(
                name="fill_blank",
                passed=False,
                detail=(
                    "Jawaban yang diterima tidak menghasilkan keluaran "
                    f"yang diharapkan: {'; '.join(catatan)}"
                ),
            )
    for pengecoh in item.distractors:
        hasil = _hasil(item.code.replace(BLANK_MARKER, pengecoh.text))
        catatan.append(f"{pengecoh.text!r} -> {hasil!r}")
        if hasil == diharapkan:
            return ValidatorResult(
                name="fill_blank",
                passed=False,
                detail=(
                    "Jawaban salah menghasilkan keluaran yang sama "
                    f"dengan kunci, jadi soal tidak unik: {'; '.join(catatan)}"
                ),
            )
    return ValidatorResult(
        name="fill_blank",
        passed=True,
        detail=f"Hanya jawaban yang diterima yang menghasilkan {diharapkan!r}: {'; '.join(catatan)}",
    )
