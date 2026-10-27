"""Menghitung jumlah token pada prompt sistem.

Cara pakai (dari folder proyek):
    python tools\\hitung_prompt.py
"""

import sys
from pathlib import Path

# Supaya "from app ..." dikenali saat skrip dijalankan langsung.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config  # noqa: E402
from app.pipeline.tokens import count_tokens  # noqa: E402


def main() -> None:
    berkas = config.PROMPT_DIR / "system_prompt.txt"
    teks = berkas.read_text(encoding="utf-8")
    jumlah = count_tokens(teks)
    batas = config.MAX_PROMPT_TOKENS - config.TASK_INSTRUCTION_RESERVE
    print(f"Token prompt sistem : {jumlah}")
    print(f"Batas untuk prompt  : {batas}")
    print(f"Sisa                : {batas - jumlah}")


if __name__ == "__main__":
    main()