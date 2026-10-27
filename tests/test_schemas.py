import pytest
from pydantic import ValidationError

from app.schemas import (
    Item,
    PlannerOutput,
    ValidationReport,
    ValidatorResult,
)


def umpan_balik() -> dict:
    return {
        "diagnosis": "Anda mungkin mengira ...",
        "explanation": "Yang sebenarnya terjadi adalah ...",
        "next_step": "Coba telusuri nilai variabel baris demi baris.",
    }


def item_pilihan_ganda() -> dict:
    kode = "\n".join([
        "skor = 10",
        "pengali = 2",
        "if skor > 5:",
        "    pengali = pengali * 2",
        "    skor == skor + 5",
        "print(skor * pengali)",
    ])
    return {
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
            {
                "option_id": "B",
                "text": "60",
                "misconception_type": "assignment_error",
                "feedback": umpan_balik(),
            },
            {
                "option_id": "C",
                "text": "20",
                "misconception_type": "logic_error",
                "feedback": umpan_balik(),
            },
            {
                "option_id": "D",
                "text": "30",
                "misconception_type": "other",
                "misconception_note": "Hanya sebagian pembaruan yang dihitung.",
                "feedback": umpan_balik(),
            },
        ],
        "source_chunk_id": "MOD5-P02-C01",
        "source_page": 2,
    }


def item_isian() -> dict:
    kode = "\n".join([
        "nilai = 95",
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
            "expected_output": "A",
            "explanation": "elif hanya diperiksa jika kondisi sebelumnya salah.",
        },
        "accepted_answers": ["elif"],
        "distractors": [
            {
                "text": "if",
                "misconception_type": "syntax_error",
                "subtype": "independent-if",
                "feedback": umpan_balik(),
            },
            {
                "text": "else if",
                "misconception_type": "syntax_error",
                "subtype": "else-if-separate",
                "feedback": umpan_balik(),
            },
        ],
        "source_chunk_id": "MOD5-P03-C02",
        "source_page": 3,
    }


def test_pilihan_ganda_valid():
    item = Item.model_validate(item_pilihan_ganda())
    assert item.answer_key.text == "40"
    assert len(item.distractors) == 3


def test_tipe_kesalahan_ganda_diperbolehkan():
    data = item_pilihan_ganda()
    data["distractors"][2]["misconception_type"] = "logic_error"
    data["distractors"][2].pop("misconception_note")
    item = Item.model_validate(data)
    tipe = [d.misconception_type for d in item.distractors]
    assert tipe.count("logic_error") == 2


def test_other_tanpa_catatan_ditolak():
    data = item_pilihan_ganda()
    data["distractors"][2].pop("misconception_note")
    with pytest.raises(ValidationError):
        Item.model_validate(data)


def test_other_dengan_catatan_diterima():
    item = Item.model_validate(item_pilihan_ganda())
    assert item.distractors[2].misconception_type == "other"
    assert item.distractors[2].misconception_note


def test_pengecoh_sama_dengan_kunci_ditolak():
    data = item_pilihan_ganda()
    data["distractors"][0]["text"] = "40"
    with pytest.raises(ValidationError):
        Item.model_validate(data)


def test_pilihan_ganda_kurang_dari_tiga_pengecoh_ditolak():
    data = item_pilihan_ganda()
    data["distractors"] = data["distractors"][:2]
    with pytest.raises(ValidationError):
        Item.model_validate(data)


def test_isian_valid_seed_elif():
    item = Item.model_validate(item_isian())
    assert "nilai = 95" in item.code
    assert item.accepted_answers == ["elif"]


def test_isian_tanpa_tanda_kosong_ditolak():
    data = item_isian()
    data["code"] = data["code"].replace("____", "elif")
    with pytest.raises(ValidationError):
        Item.model_validate(data)


def test_isian_kunci_tidak_ada_di_jawaban_diterima_ditolak():
    data = item_isian()
    data["accepted_answers"] = ["if"]
    with pytest.raises(ValidationError):
        Item.model_validate(data)


def test_kolom_tidak_dikenal_ditolak():
    data = item_pilihan_ganda()
    data["warna"] = "merah"
    with pytest.raises(ValidationError):
        Item.model_validate(data)


def test_planner_ok_dengan_coverage():
    planner = PlannerOutput.model_validate({
        "topic": "Perulangan",
        "status": "ok",
        "chunk_ids": ["MOD4-P01-C01"],
        "key_concepts": ["range", "indeks"],
        "coverage": {
            "headings": ["4.1 Perulangan for"],
            "code_constructs": ["For", "Call:range"],
        },
    })
    assert planner.coverage.headings == ["4.1 Perulangan for"]
    assert "For" in planner.coverage.code_constructs


def test_planner_materi_tidak_cukup():
    planner = PlannerOutput.model_validate({
        "topic": "Pemrograman Berorientasi Objek",
        "status": "insufficient_context",
    })
    assert planner.key_concepts == []
    assert planner.coverage.headings == []


def test_planner_ok_tanpa_konsep_ditolak():
    with pytest.raises(ValidationError):
        PlannerOutput.model_validate({
            "topic": "Perulangan",
            "status": "ok",
            "chunk_ids": ["MOD4-P01-C01"],
            "key_concepts": [],
        })


def test_laporan_validasi():
    kosong = ValidationReport()
    assert kosong.all_passed() is False

    laporan = ValidationReport(results=[
        ValidatorResult(name="ast", passed=True),
        ValidatorResult(name="lint", passed=False, detail="baris terlalu panjang"),
    ])
    assert laporan.all_passed() is False
    assert laporan.failed_names() == ["lint"]