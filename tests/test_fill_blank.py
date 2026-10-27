from app.pipeline.validators.fill_blank_check import validate_fill_blank
from app.pipeline.validators.schema_check import validate_schema


def _fb():
    return {
        "diagnosis": "Anda mungkin mengira ...",
        "explanation": "Yang sebenarnya terjadi adalah ...",
        "next_step": "Coba telusuri nilai variabel baris demi baris.",
    }


def _fib(nilai=95, diharapkan="A"):
    kode = "\n".join([
        f"nilai = {nilai}",
        "if nilai >= 90:",
        '    print("A")',
        "____ nilai >= 75:",
        '    print("B")',
        "else:",
        '    print("C")',
    ])
    return {
        "item_id": "FIB-01",
        "item_format": "fill_in_blank",
        "topic": "Percabangan",
        "stem": 'Lengkapi bagian kosong agar program hanya mencetak "A".',
        "code": kode,
        "answer_key": {
            "text": "elif",
            "expected_output": diharapkan,
            "explanation": "elif hanya diperiksa jika kondisi sebelumnya salah.",
        },
        "accepted_answers": ["elif"],
        "distractors": [
            {"text": "if", "misconception_type": "syntax_error", "subtype": "independent-if", "feedback": _fb()},
            {"text": "else if", "misconception_type": "syntax_error", "subtype": "else-if-separate", "feedback": _fb()},
        ],
        "source_chunk_id": "DEMO-P01-C03",
        "source_page": 1,
    }


def test_fill_blank_seed_elif_unik():
    item, _ = validate_schema(_fib())
    assert validate_fill_blank(item).passed


def test_fill_blank_benih_lama_tidak_unik():
    # nilai = 80: "if" terpisah juga mencetak "B", sama seperti "elif".
    item, _ = validate_schema(_fib(nilai=80, diharapkan="B"))
    hasil = validate_fill_blank(item)
    assert not hasil.passed
    assert "if" in hasil.detail


def test_fill_blank_dilewati_untuk_pilihan_ganda():
    data = {
        "item_id": "MCQ-01", "item_format": "mcq", "topic": "Percabangan",
        "stem": "Apa keluarannya?", "code": "print(40)",
        "answer_key": {"option_id": "A", "text": "40", "expected_output": "40", "explanation": "x"},
        "distractors": [
            {"option_id": "B", "text": "1", "misconception_type": "logic_error", "feedback": _fb()},
            {"option_id": "C", "text": "2", "misconception_type": "logic_error", "feedback": _fb()},
            {"option_id": "D", "text": "3", "misconception_type": "logic_error", "feedback": _fb()},
        ],
        "source_chunk_id": "X", "source_page": 1,
    }
    item, _ = validate_schema(data)
    assert validate_fill_blank(item).passed
