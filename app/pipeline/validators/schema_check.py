"""Validator: bentuk data (skema) sebuah butir soal.

Memakai model Pydantic di app/schemas.py sebagai satu-satunya
aturan bentuk data. Validator ini tidak menilai isi soal,
hanya apakah bentuknya sesuai kontrak.
"""

from pydantic import ValidationError

from app.schemas import Item, ValidatorResult


def validate_schema(data: dict) -> tuple[Item | None, ValidatorResult]:
    """Memeriksa satu kandidat (dict) terhadap skema Item.

    Mengembalikan (item, hasil). Bila bentuknya salah, item
    adalah None dan hasil berisi pesan galat Pydantic.
    """
    try:
        item = Item.model_validate(data)
    except ValidationError as galat:
        return None, ValidatorResult(
            name="schema",
            passed=False,
            detail=str(galat),
        )
    return item, ValidatorResult(
        name="schema",
        passed=True,
        detail="Bentuk data sesuai skema Item.",
    )
