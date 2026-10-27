"""Penyimpanan SQLite Fase 3.

Dua tabel:

- items: butir soal sebagai JSON utuh (skema Item tidak
  berubah) ditambah kolom status kurasi dan laporan
  validator. Generate yang menemukan item_id yang sudah
  ada tidak menimpa isinya, supaya kurasi yang sudah
  dilakukan dosen tidak hilang.
- attempts: jejak jawaban siswa. Hanya UUID sesi, ID soal,
  jawaban yang dipilih, benar atau salah, dan waktu.
  Tidak ada nama, NIM, atau data pribadi lain.

Setiap fungsi membaca config.DATABASE_PATH pada saat
dipanggil, supaya pengujian bisa mengarahkannya ke
berkas sementara. Berkas database diabaikan git
(pola *.db di .gitignore).
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app import config
from app.schemas import Item, ItemStatus, StoredItem, ValidationReport

_SKEMA = """
CREATE TABLE IF NOT EXISTS items (
    item_id TEXT PRIMARY KEY,
    payload TEXT NOT NULL,
    status TEXT NOT NULL,
    report TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    item_id TEXT NOT NULL,
    chosen TEXT NOT NULL,
    correct INTEGER NOT NULL,
    answered_at TEXT NOT NULL
);
"""


def _jalur(path: Path | None) -> Path:
    return Path(path) if path is not None else config.DATABASE_PATH


def _sambung(path: Path | None) -> sqlite3.Connection:
    sambungan = sqlite3.connect(_jalur(path))
    sambungan.row_factory = sqlite3.Row
    return sambungan


def init_db(path: Path | None = None) -> None:
    """Membuat tabel bila belum ada. Aman dipanggil berulang kali."""
    with _sambung(path) as sambungan:
        sambungan.executescript(_SKEMA)


def _sekarang() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dari_baris(baris: sqlite3.Row) -> StoredItem:
    return StoredItem(
        item=Item.model_validate_json(baris["payload"]),
        status=ItemStatus(baris["status"]),
        report=(
            ValidationReport.model_validate_json(baris["report"])
            if baris["report"]
            else None
        ),
    )


def save_item(
    item: Item,
    status: ItemStatus,
    report: ValidationReport | None,
    path: Path | None = None,
) -> StoredItem:
    """Menyimpan butir baru. Bila item_id sudah ada, isi lama
    dipertahankan dan yang lama itulah yang dikembalikan."""
    init_db(path)
    sekarang = _sekarang()
    with _sambung(path) as sambungan:
        sambungan.execute(
            "INSERT OR IGNORE INTO items"
            " (item_id, payload, status, report, created_at, updated_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (
                item.item_id,
                item.model_dump_json(),
                status.value,
                report.model_dump_json() if report is not None else None,
                sekarang,
                sekarang,
            ),
        )
    tersimpan = get_item(item.item_id, path)
    assert tersimpan is not None
    return tersimpan


def get_item(item_id: str, path: Path | None = None) -> StoredItem | None:
    """Mengambil satu butir tersimpan, atau None bila tidak ada."""
    init_db(path)
    with _sambung(path) as sambungan:
        baris = sambungan.execute(
            "SELECT * FROM items WHERE item_id = ?", (item_id,)
        ).fetchone()
    return _dari_baris(baris) if baris is not None else None


def list_items(
    status: ItemStatus | None = None, path: Path | None = None
) -> list[StoredItem]:
    """Daftar butir tersimpan, urut waktu simpan. Bila status
    diberikan, hanya status itu yang dikembalikan."""
    init_db(path)
    with _sambung(path) as sambungan:
        if status is None:
            baris_semua = sambungan.execute(
                "SELECT * FROM items ORDER BY rowid"
            ).fetchall()
        else:
            baris_semua = sambungan.execute(
                "SELECT * FROM items WHERE status = ? ORDER BY rowid",
                (status.value,),
            ).fetchall()
    return [_dari_baris(baris) for baris in baris_semua]


def replace_item(
    item: Item, report: ValidationReport | None, path: Path | None = None
) -> StoredItem | None:
    """Mengganti isi butir yang sudah ada (hasil edit) dan
    mengembalikan statusnya ke draft. Mengembalikan None
    bila item_id tidak ditemukan."""
    init_db(path)
    with _sambung(path) as sambungan:
        hasil = sambungan.execute(
            "UPDATE items SET payload = ?, status = ?, report = ?,"
            " updated_at = ? WHERE item_id = ?",
            (
                item.model_dump_json(),
                ItemStatus.DRAFT.value,
                report.model_dump_json() if report is not None else None,
                _sekarang(),
                item.item_id,
            ),
        )
        if hasil.rowcount == 0:
            return None
    return get_item(item.item_id, path)


def set_status(
    item_id: str, status: ItemStatus, path: Path | None = None
) -> StoredItem | None:
    """Mengubah status kurasi. Mengembalikan None bila
    item_id tidak ditemukan. Aturan transisi status
    diperiksa di lapisan API, bukan di sini."""
    init_db(path)
    with _sambung(path) as sambungan:
        hasil = sambungan.execute(
            "UPDATE items SET status = ?, updated_at = ? WHERE item_id = ?",
            (status.value, _sekarang(), item_id),
        )
        if hasil.rowcount == 0:
            return None
    return get_item(item_id, path)


def save_attempt(
    session_id: str,
    item_id: str,
    chosen: str,
    correct: bool,
    path: Path | None = None,
) -> None:
    """Mencatat satu jawaban siswa. Tidak ada data pribadi
    yang disimpan di sini."""
    init_db(path)
    with _sambung(path) as sambungan:
        sambungan.execute(
            "INSERT INTO attempts"
            " (session_id, item_id, chosen, correct, answered_at)"
            " VALUES (?, ?, ?, ?, ?)",
            (session_id, item_id, chosen, 1 if correct else 0, _sekarang()),
        )


def list_attempts(
    session_id: str, path: Path | None = None
) -> list[dict]:
    """Jejak jawaban satu sesi, urut waktu menjawab."""
    init_db(path)
    with _sambung(path) as sambungan:
        baris_semua = sambungan.execute(
            "SELECT item_id, chosen, correct, answered_at FROM attempts"
            " WHERE session_id = ? ORDER BY id",
            (session_id,),
        ).fetchall()
    return [
        {
            "item_id": baris["item_id"],
            "chosen": baris["chosen"],
            "correct": bool(baris["correct"]),
            "answered_at": baris["answered_at"],
        }
        for baris in baris_semua
    ]
