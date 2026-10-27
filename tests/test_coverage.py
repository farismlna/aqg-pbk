import pytest

from app.pipeline.chunker import Chunk, chunk_pages
from app.pipeline.coverage import build_coverage
from app.pipeline.planner import make_planner_output
from app.schemas import PlannerStatus


@pytest.fixture(scope="module")
def potongan_demo(halaman_demo):
    return chunk_pages(halaman_demo, module_id="DEMO")


def test_judul_lengkap_tanpa_ganda(potongan_demo):
    liputan = build_coverage(potongan_demo)
    assert [j.split()[0] for j in liputan.headings] == [
        "4.1",
        "4.2",
        "5.1",
        "5.2",
        "5.3",
    ]


def test_konstruksi_kode_memuat_for_if_dan_panggilan(potongan_demo):
    liputan = build_coverage(potongan_demo)
    assert "For" in liputan.code_constructs
    assert "Call:range" in liputan.code_constructs
    assert "If" in liputan.code_constructs
    assert "Call:print" in liputan.code_constructs
    assert len(liputan.code_constructs) == len(set(liputan.code_constructs))


def test_tanpa_potongan_liputan_kosong():
    liputan = build_coverage([])
    assert liputan.headings == []
    assert liputan.code_constructs == []


def test_blok_kode_tidak_valid_dilewati():
    potongan = [
        Chunk(
            chunk_id="MOD-P01-C01",
            page=1,
            heading="4.1 Contoh",
            text="Contoh yang tidak lengkap.",
            tokens=5,
            code_blocks=("x = ",),
        )
    ]
    liputan = build_coverage(potongan)
    assert liputan.headings == ["4.1 Contoh"]
    assert liputan.code_constructs == []


def test_planner_ok_dengan_coverage(potongan_demo):
    potongan = potongan_demo[:1]
    hasil = make_planner_output(
        "Perulangan", potongan, ["range", "interval setengah terbuka"]
    )
    assert hasil.status == PlannerStatus.OK
    assert hasil.chunk_ids == ["DEMO-P01-C01"]
    assert hasil.coverage.headings[0].startswith("4.1")
    assert "For" in hasil.coverage.code_constructs


def test_planner_tanpa_potongan_materi_tidak_cukup():
    hasil = make_planner_output("Pemrograman Berorientasi Objek", [], [])
    assert hasil.status == PlannerStatus.INSUFFICIENT_CONTEXT
    assert hasil.chunk_ids == []
    assert hasil.key_concepts == []
    assert hasil.coverage.headings == []


def test_planner_ok_tanpa_konsep_kunci_ditolak(potongan_demo):
    with pytest.raises(ValueError, match="key_concepts"):
        make_planner_output("Perulangan", potongan_demo[:1], [])
