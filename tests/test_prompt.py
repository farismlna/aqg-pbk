import json

from app import config
from app.pipeline.tokens import count_tokens
from app.schemas import AnswerKey, Distractor, Feedback, Item

PROMPT = config.PROMPT_DIR / "system_prompt.txt"


def baca_prompt() -> str:
    return PROMPT.read_text(encoding="utf-8")


def ambil_contoh_json() -> dict:
    """Mengambil baris contoh JSON (yang diawali {"item_id") dari prompt."""
    for baris in baca_prompt().splitlines():
        if baris.startswith('{"item_id"'):
            return json.loads(baris)
    raise AssertionError("Baris contoh JSON tidak ditemukan di prompt.")


def test_prompt_ada():
    assert PROMPT.exists()


def test_prompt_muat_dalam_anggaran():
    batas = config.MAX_PROMPT_TOKENS - config.TASK_INSTRUCTION_RESERVE
    assert count_tokens(baca_prompt()) <= batas


def test_contoh_json_cocok_dengan_skema():
    contoh = ambil_contoh_json()
    assert set(contoh) == set(Item.model_fields)
    assert set(contoh["answer_key"]) == set(AnswerKey.model_fields)
    pengecoh = contoh["distractors"][0]
    assert set(pengecoh) <= set(Distractor.model_fields)
    assert set(pengecoh["feedback"]) == set(Feedback.model_fields)