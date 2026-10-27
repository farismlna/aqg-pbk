from app import config
from app.schemas import (
    AnswerKey,
    Coverage,
    Distractor,
    Feedback,
    Item,
    PlannerOutput,
)

DOKUMEN = config.BASE_DIR / "docs" / "DATA_CONTRACT.md"


def baca_dokumen() -> str:
    return DOKUMEN.read_text(encoding="utf-8")


def test_dokumen_ada():
    assert DOKUMEN.exists()


def test_semua_kolom_tercatat():
    teks = baca_dokumen()
    for model in (Item, AnswerKey, Distractor, Feedback, PlannerOutput, Coverage):
        for nama in model.model_fields:
            assert f"`{nama}`" in teks, (
                f"Kolom {nama} ({model.__name__}) belum ada di DATA_CONTRACT.md"
            )


def test_angka_terkunci_tercatat():
    teks = baca_dokumen()
    angka_terkunci = (
        config.CHUNK_TOKENS,
        config.TOP_K,
        config.MAX_RETRIEVED_TOKENS,
        config.MAX_PROMPT_TOKENS,
        config.MAX_TOTAL_TOKENS,
        config.MAX_LINE_LENGTH,
        config.SANDBOX_MAX_OUTPUT_BYTES,
    )
    for angka in angka_terkunci:
        assert str(angka) in teks, f"Angka {angka} belum ada di DATA_CONTRACT.md"