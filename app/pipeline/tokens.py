"""Penghitung token dan pemeriksa anggaran token.

Dipakai untuk memastikan prompt (instruksi) dan potongan teks yang
diambil tidak melewati batas yang sudah dikunci di app/config.py.
"""

from functools import lru_cache

import tiktoken

from app import config
from app.errors import TokenBudgetError


@lru_cache(maxsize=1)
def _get_encoder():
    """Memuat penghitung token sekali saja, lalu dipakai ulang."""
    return tiktoken.get_encoding(config.TOKENIZER_NAME)


def count_tokens(text: str) -> int:
    """Menghitung jumlah token dalam sebuah teks."""
    if not text:
        return 0
    # disallowed_special=() membuat teks seperti "<|endoftext|>"
    # dihitung sebagai teks biasa, bukan menimbulkan galat.
    return len(_get_encoder().encode(text, disallowed_special=()))


def check_budget(prompt_text: str, chunks: list[str]) -> dict:
    """Memeriksa anggaran token. Melempar TokenBudgetError bila dilanggar.

    Aturan:
    - prompt_text (instruksi + skema + tugas) paling banyak 600 token.
    - jumlah potongan paling banyak 3.
    - tiap potongan paling banyak 400 token.
    - total potongan paling banyak 1.200 token.

    Mengembalikan laporan berisi jumlah token tiap bagian.
    """
    prompt_tokens = count_tokens(prompt_text)
    if prompt_tokens > config.MAX_PROMPT_TOKENS:
        raise TokenBudgetError(
            f"Prompt terlalu panjang: {prompt_tokens} token "
            f"(batas {config.MAX_PROMPT_TOKENS})."
        )

    if len(chunks) > config.TOP_K:
        raise TokenBudgetError(
            f"Terlalu banyak potongan: {len(chunks)} (batas {config.TOP_K})."
        )

    retrieved_tokens = 0
    for nomor, potongan in enumerate(chunks, start=1):
        jumlah = count_tokens(potongan)
        if jumlah > config.CHUNK_TOKENS:
            raise TokenBudgetError(
                f"Potongan ke-{nomor} terlalu panjang: {jumlah} token "
                f"(batas {config.CHUNK_TOKENS})."
            )
        retrieved_tokens += jumlah

    if retrieved_tokens > config.MAX_RETRIEVED_TOKENS:
        raise TokenBudgetError(
            f"Total potongan terlalu besar: {retrieved_tokens} token "
            f"(batas {config.MAX_RETRIEVED_TOKENS})."
        )

    return {
        "prompt_tokens": prompt_tokens,
        "retrieved_tokens": retrieved_tokens,
        "total_tokens": prompt_tokens + retrieved_tokens,
    }