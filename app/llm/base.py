"""Antarmuka sumber kandidat soal (adapter LLM).

Di v1, satu-satunya sumber adalah ReplayAdapter yang
membaca kandidat yang sudah ditulis sebelumnya dari
berkas JSON. Adapter LLM live diganti belakangan tanpa
mengubah orchestrator, selama ia mengembalikan daftar
dict kandidat dengan bentuk yang sama.
"""

from typing import Protocol


class CandidateSource(Protocol):
    """Sumber kandidat: mengembalikan daftar dict butir soal."""

    def candidates(self) -> list[dict]:
        """Mengembalikan semua kandidat, dalam urutan coba."""
        ...
