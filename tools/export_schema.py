"""Membuat berkas JSON Schema dari skema pydantic.

Hasilnya (data/prompts/output_schema.json) dipakai sebagai dokumentasi
dan untuk memeriksa berkas replay. TIDAK dikirim ke model, karena
terlalu panjang untuk anggaran 600 token.

Cara pakai (dari folder proyek):
    python tools\\export_schema.py
"""

import json
import sys
from pathlib import Path

# Supaya "from app ..." dikenali saat skrip dijalankan langsung.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config  # noqa: E402
from app.schemas import Item  # noqa: E402


def main() -> None:
    skema = Item.model_json_schema()
    config.PROMPT_DIR.mkdir(parents=True, exist_ok=True)
    tujuan = config.PROMPT_DIR / "output_schema.json"
    tujuan.write_text(
        json.dumps(skema, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Skema ditulis ke {tujuan}")
    print(f"Jumlah kolom tingkat atas: {len(skema.get('properties', {}))}")


if __name__ == "__main__":
    main()