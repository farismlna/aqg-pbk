"""Adapter replay: kandidat soal dibaca dari berkas JSON.

Bukan LLM live. Setiap berkas di folder replay adalah satu
kandidat butir soal, ditulis sebelumnya (termasuk yang
sengaja gagal, supaya validator terbukti menolaknya).
Keterlambatan buatan, bila ada, harus ditandai
"simulated": true oleh pemanggil, bukan disajikan
sebagai waktu terukur.
"""

import json
from pathlib import Path

from app import config


class ReplayAdapter:
    """Sumber kandidat dari daftar dict atau folder JSON."""

    def __init__(self, candidates: list[dict]) -> None:
        self._candidates = list(candidates)

    @classmethod
    def from_files(cls, folder: Path | None = None) -> "ReplayAdapter":
        """Membaca semua berkas *.json di folder replay, terurut nama."""
        folder = Path(folder) if folder is not None else config.REPLAY_DIR
        berkas = sorted(folder.glob("*.json"))
        kandidat: list[dict] = []
        for jalur in berkas:
            with open(jalur, encoding="utf-8") as f:
                kandidat.append(json.load(f))
        return cls(kandidat)

    def candidates(self) -> list[dict]:
        return list(self._candidates)
