import pytest

from app import config
from app.errors import TokenBudgetError
from app.pipeline.tokens import check_budget, count_tokens


def test_teks_kosong_bernilai_nol():
    assert count_tokens("") == 0


def test_hello_world_dua_token():
    assert count_tokens("hello world") == 2


def test_anggaran_aman():
    laporan = check_budget("Tulis satu soal.", ["potongan satu", "potongan dua"])
    assert laporan["prompt_tokens"] > 0
    assert laporan["retrieved_tokens"] > 0
    assert laporan["total_tokens"] == (
        laporan["prompt_tokens"] + laporan["retrieved_tokens"]
    )
    assert laporan["total_tokens"] <= config.MAX_TOTAL_TOKENS


def test_prompt_terlalu_panjang():
    teks = "kata " * 1000
    with pytest.raises(TokenBudgetError):
        check_budget(teks, ["potongan"])


def test_potongan_terlalu_panjang():
    teks = "kata " * 1000
    with pytest.raises(TokenBudgetError):
        check_budget("prompt pendek", [teks])


def test_terlalu_banyak_potongan():
    with pytest.raises(TokenBudgetError):
        check_budget("prompt pendek", ["a", "b", "c", "d"])


def test_konfigurasi_konsisten():
    assert config.MAX_RETRIEVED_TOKENS == config.TOP_K * config.CHUNK_TOKENS
    assert config.MAX_TOTAL_TOKENS == 1800