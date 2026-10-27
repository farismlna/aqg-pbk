"""Mengambil potongan materi yang paling relevan dengan pertanyaan.

Cara kerja: TF-IDF + cosine similarity (scikit-learn). Ini adalah
penyimpangan yang dicatat dari proposal, yang menulis dense
embeddings + vector database. Untuk modul maksimal 10 halaman,
TF-IDF deterministik, offline, dan tidak butuh torch di Windows.

Retriever tidak memutuskan apakah materi cukup atau tidak. Ia
hanya mengembalikan potongan beserta skornya, terurut dari yang
paling relevan. Keputusan cukup atau tidak (gerbang skor) dibuat
di orchestrator pada Fase 2B, supaya aturan itu bisa diuji
terpisah dari pengurutan ini.
"""

from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app import config
from app.errors import RetrievalError
from app.pipeline.chunker import Chunk


@dataclass(frozen=True)
class ScoredChunk:
    """Satu potongan beserta skor kemiripannya (0 sampai 1)."""

    chunk: Chunk
    score: float


class Retriever:
    """Pengambil potongan yang dibangun sekali dari daftar potongan."""

    def __init__(self, chunks: list[Chunk]) -> None:
        if not chunks:
            raise RetrievalError("Tidak ada potongan materi untuk diambil.")
        self._chunks = list(chunks)
        # Pola \w+ (bukan \w\w+) supaya pengenal satu huruf pada kode,
        # misalnya i dan n, tetap dihitung sebagai kata.
        self._vectorizer = TfidfVectorizer(
            lowercase=True, token_pattern=r"(?u)\b\w+\b"
        )
        try:
            self._matrix = self._vectorizer.fit_transform(
                [c.text for c in self._chunks]
            )
        except ValueError as galat:
            raise RetrievalError(
                f"Kamus TF-IDF kosong, potongan tidak bisa diindeks: {galat}"
            ) from galat

    def retrieve(self, query: str, top_k: int | None = None) -> list[ScoredChunk]:
        """Mengembalikan paling banyak top_k potongan, terurut menurun.

        Ikatan skor dipecahkan menurut chunk_id supaya urutannya
        deterministik pada setiap pemanggilan yang sama.
        """
        if not query or not query.strip():
            raise RetrievalError("Pertanyaan pengambilan tidak boleh kosong.")
        jumlah = config.TOP_K if top_k is None else top_k
        if jumlah < 1:
            raise RetrievalError(f"top_k harus minimal 1, bukan {jumlah}.")
        jumlah = min(jumlah, len(self._chunks))

        vektor = self._vectorizer.transform([query])
        skor = cosine_similarity(vektor, self._matrix)[0]
        urutan = sorted(
            range(len(self._chunks)),
            key=lambda i: (-float(skor[i]), self._chunks[i].chunk_id),
        )
        return [
            ScoredChunk(chunk=self._chunks[i], score=float(skor[i]))
            for i in urutan[:jumlah]
        ]


def retrieve(chunks: list[Chunk], query: str, top_k: int | None = None) -> list[ScoredChunk]:
    """Jalan pintas: membangun Retriever sekali, lalu mengambil sekali."""
    return Retriever(chunks).retrieve(query, top_k=top_k)
