"""Pengaturan terpusat prototipe AQG-DDP.

Semua angka yang sudah "dikunci" dalam kontrak data ada di sini,
supaya tidak tersebar di banyak berkas. Mengubah angka di sini
berarti mengubah kontrak.
"""

from pathlib import Path

# --- Lokasi folder ---
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PROMPT_DIR = DATA_DIR / "prompts"
MODULE_DIR = DATA_DIR / "modules"
REPLAY_DIR = DATA_DIR / "replay"

# --- Anggaran token ---
# Token = potongan kecil teks yang dihitung oleh model bahasa.
# Penghitung token yang dipakai: cl100k_base (perkiraan, bukan angka
# resmi untuk model non-OpenAI).
TOKENIZER_NAME = "cl100k_base"
CHUNK_TOKENS = 400            # ukuran maksimum satu potongan teks
CHUNK_OVERLAP_TOKENS = 0      # tumpang tindih antar potongan (ubah bila kontrak Anda menyebut lain)
TOP_K = 3                     # jumlah potongan yang diambil
MAX_RETRIEVED_TOKENS = 1200   # 3 potongan x 400 token
MAX_PROMPT_TOKENS = 600       # instruksi sistem + skema + tugas
MAX_TOTAL_TOKENS = MAX_RETRIEVED_TOKENS + MAX_PROMPT_TOKENS  # 1800

# --- Batas modul PDF ---
MAX_PDF_PAGES = 10
MAX_PDF_BYTES = 5 * 1024 * 1024   # 5 MB (usulan; ubah bila perlu)

# --- Aturan gaya kode (PEP 8) ---
MAX_LINE_LENGTH = 79

# --- Kotak pasir (tempat aman menjalankan kode) ---
SANDBOX_TIMEOUT_SECONDS = 2.0
SANDBOX_MAX_OUTPUT_BYTES = 10_000