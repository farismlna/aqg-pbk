import pytest

from app import config
from app.errors import RetrievalError
from app.pipeline.chunker import Chunk, chunk_pages
from app.pipeline.retriever import Retriever, retrieve
from app.pipeline.tokens import count_tokens


@pytest.fixture(scope="module")
def potongan_demo(halaman_demo):
    return chunk_pages(halaman_demo, module_id="DEMO")


def test_range_mengambil_potongan_41_teratas(potongan_demo):
    hasil = retrieve(potongan_demo, "range interval setengah terbuka")
    assert hasil[0].chunk.heading.startswith("4.1")
    assert hasil[0].score > 0


def test_elif_mengambil_potongan_51_teratas(potongan_demo):
    hasil = retrieve(potongan_demo, "elif percabangan rantai")
    assert hasil[0].chunk.heading.startswith("5.1")
    assert hasil[0].score > 0


def test_operator_logika_mengambil_potongan_53_teratas(potongan_demo):
    hasil = retrieve(potongan_demo, "operator logika and or not")
    assert hasil[0].chunk.heading.startswith("5.3")
    assert hasil[0].score > 0


def test_skor_menurun_dan_dalam_rentang(potongan_demo):
    hasil = retrieve(potongan_demo, "range")
    skor = [h.score for h in hasil]
    assert skor == sorted(skor, reverse=True)
    assert all(0 <= s <= 1 for s in skor)


def test_jumlah_default_sama_dengan_top_k(potongan_demo):
    hasil = retrieve(potongan_demo, "range")
    assert len(hasil) == config.TOP_K
    assert len({h.chunk.chunk_id for h in hasil}) == len(hasil)


def test_top_k_lebih_besar_dari_potongan_mengembalikan_semua(potongan_demo):
    hasil = retrieve(potongan_demo, "range", top_k=99)
    assert len(hasil) == len(potongan_demo)


def test_total_token_tiga_teratas_dalam_batas(potongan_demo):
    hasil = retrieve(potongan_demo, "range interval setengah terbuka")
    total = sum(count_tokens(h.chunk.text) for h in hasil)
    assert total <= config.MAX_RETRIEVED_TOKENS


def test_urutan_deterministik(potongan_demo):
    pengambil = Retriever(potongan_demo)
    pertama = [h.chunk.chunk_id for h in pengambil.retrieve("range")]
    kedua = [h.chunk.chunk_id for h in pengambil.retrieve("range")]
    assert pertama == kedua


def test_tanpa_potongan_ditolak():
    with pytest.raises(RetrievalError, match="Tidak ada potongan"):
        Retriever([])


def test_pertanyaan_kosong_ditolak(potongan_demo):
    with pytest.raises(RetrievalError, match="tidak boleh kosong"):
        retrieve(potongan_demo, "   ")


def test_top_k_nol_ditolak(potongan_demo):
    with pytest.raises(RetrievalError, match="top_k"):
        retrieve(potongan_demo, "range", top_k=0)


def test_chunk_tunggal_selalu_terambil():
    potongan = [
        Chunk(
            chunk_id="MOD-P01-C01",
            page=1,
            heading="4.1 Contoh",
            text="range menghasilkan deret bilangan.",
            tokens=6,
            code_blocks=(),
        )
    ]
    hasil = retrieve(potongan, "kata yang tidak ada di mana pun")
    assert len(hasil) == 1
    assert hasil[0].score == 0
