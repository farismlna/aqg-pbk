import pytest

from app.pipeline.validators.ast_check import validate_ast
from app.pipeline.validators.lint_check import validate_lint
from app.pipeline.validators.sandbox_check import validate_sandbox
from app.pipeline.validators.schema_check import validate_schema
from app.schemas import Item


def _fb():
    return {
        "diagnosis": "Anda mungkin mengira ...",
        "explanation": "Yang sebenarnya terjadi adalah ...",
        "next_step": "Coba telusuri nilai variabel baris demi baris.",
    }


def _mcq(**ubah):
    kode = "\n".join([
        "skor = 10",
        "pengali = 2",
        "if skor > 5:",
        "    pengali = pengali * 2",
        "    skor == skor + 5",
        "print(skor * pengali)",
    ])
    data = {
        "item_id": "MCQ-01",
        "item_format": "mcq",
        "topic": "Percabangan",
        "stem": "Apa keluaran program berikut?",
        "code": kode,
        "answer_key": {
            "option_id": "A",
            "text": "40",
            "expected_output": "40",
            "explanation": "== hanya membandingkan, skor tetap 10.",
        },
        "distractors": [
            {"option_id": "B", "text": "60", "misconception_type": "assignment_error", "feedback": _fb()},
            {"option_id": "C", "text": "20", "misconception_type": "logic_error", "feedback": _fb()},
            {
                "option_id": "D", "text": "30", "misconception_type": "other",
                "misconception_note": "partial_branch_update",
                "feedback": _fb(),
            },
        ],
        "source_chunk_id": "DEMO-P02-C01",
        "source_page": 2,
    }
    data.update(ubah)
    return data


def test_schema_valid_dan_tidak_valid():
    item, hasil = validate_schema(_mcq())
    assert item is not None and hasil.passed
    item, hasil = validate_schema({"item_id": "X"})
    assert item is None and not hasil.passed
    assert hasil.name == "schema"


def test_ast_kode_valid_lolos():
    item, _ = validate_schema(_mcq())
    assert validate_ast(item).passed


def test_ast_kode_sintaks_salah_ditolak():
    item, _ = validate_schema(_mcq(code="if x > 5\n    print(x)"))
    assert not validate_ast(item).passed


def test_ast_mutated_code_syntax_error_harus_gagal_parse():
    data = _mcq()
    data["distractors"][0] = {
        "option_id": "B", "text": "if x = 5:", "misconception_type": "syntax_error",
        "mutated_code": "if x = 5:", "feedback": _fb(),
    }
    item, _ = validate_schema(data)
    assert validate_ast(item).passed
    data["distractors"][0]["mutated_code"] = "x = 5"
    item, _ = validate_schema(data)
    assert not validate_ast(item).passed


def test_lint_kode_valid_lolos():
    item, _ = validate_schema(_mcq())
    assert validate_lint(item).passed


def test_lint_baris_panjang_ditolak():
    item, _ = validate_schema(_mcq(code="# " + "x" * 90 + "\nprint(40)"))
    # Kode di atas tetap menghasilkan 40, jadi hanya lint yang menolak.
    assert not validate_lint(item).passed
    assert validate_ast(item).passed


def test_lint_indentasi_tab_ditolak():
    item, _ = validate_schema(_mcq(code="if True:\n\tprint(40)"))
    assert not validate_lint(item).passed


def test_sandbox_kunci_benar_lolos():
    item, _ = validate_schema(_mcq())
    assert validate_sandbox(item).passed


def test_sandbox_kunci_salah_ditolak():
    data = _mcq()
    data["answer_key"]["expected_output"] = "60"
    item, _ = validate_schema(data)
    hasil = validate_sandbox(item)
    assert not hasil.passed
    assert "60" in hasil.detail
