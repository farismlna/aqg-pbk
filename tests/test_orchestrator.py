import pytest

from app import config
from app.errors import TokenBudgetError
from app.llm.replay import ReplayAdapter
from app.pipeline.chunker import chunk_pages
from app.pipeline.orchestrator import Orchestrator
from app.schemas import PlannerStatus


@pytest.fixture(scope="module")
def potongan_demo(halaman_demo):
    return chunk_pages(halaman_demo, module_id="DEMO")


def test_orchestrator_menerima_yang_bagus_menolak_yang_gagal(potongan_demo):
    adapter = ReplayAdapter.from_files()
    hasil = Orchestrator(potongan_demo, adapter).run(
        "Percabangan", "elif percabangan rantai", ["elif", "if"], limit=10
    )
    assert hasil.planner_output.status == PlannerStatus.OK
    assert [i.item_id for i in hasil.items] == ["MCQ-01", "FIB-01"]
    ditolak = {a.candidate_id: a.report.failed_names() for a in hasil.attempts if not a.accepted}
    assert "schema" in ditolak["BAD-SCHEMA-01"]
    assert "ast" in ditolak["BAD-AST-01"]
    assert "sandbox" in ditolak["BAD-KEY-01"]
    assert "schema" in ditolak["BAD-DUPLICATE-01"]
    assert "lint" in ditolak["BAD-LINT-01"]
    assert "fill_blank" in ditolak["BAD-FILL-01"]


def test_orchestrator_materi_tidak_cukup_tanpa_percobaan(potongan_demo):
    adapter = ReplayAdapter.from_files()
    hasil = Orchestrator(potongan_demo, adapter).run(
        "Pemrograman Berorientasi Objek",
        "kelas pewarisan enkapsulasi polimorfisme",
        ["kelas"],
    )
    assert hasil.planner_output.status == PlannerStatus.INSUFFICIENT_CONTEXT
    assert hasil.attempts == [] and hasil.items == []


def test_orchestrator_anggaran_token_dilanggar(potongan_demo):
    adapter = ReplayAdapter.from_files()
    prompt_panjang = "kata " * 2000
    with pytest.raises(TokenBudgetError):
        Orchestrator(potongan_demo, adapter, prompt_text=prompt_panjang).run(
            "Percabangan", "elif percabangan", ["elif"]
        )


def test_replay_adapter_membaca_berkas_terurut():
    adapter = ReplayAdapter.from_files()
    kandidat = adapter.candidates()
    assert len(kandidat) == 8
    assert kandidat[0]["item_id"] == "MCQ-01"
    assert kandidat[-1]["item_id"] == "BAD-FILL-01"


def test_orchestrator_limit_satu_hanya_satu_diterima(potongan_demo):
    adapter = ReplayAdapter.from_files()
    hasil = Orchestrator(potongan_demo, adapter).run(
        "Percabangan", "elif percabangan rantai", ["elif"], limit=1
    )
    assert len(hasil.items) == 1
    assert hasil.items[0].item_id == "MCQ-01"
