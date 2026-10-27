"""Jenis galat khusus aplikasi AQG-DDP."""


class AqgError(Exception):
    """Induk semua galat khusus aplikasi ini."""


class TokenBudgetError(AqgError):
    """Dilempar ketika anggaran token terlampaui."""


class IngestError(AqgError):
    """Dilempar ketika PDF modul tidak bisa dipakai."""


class ChunkError(AqgError):
    """Dilempar ketika teks tidak bisa dipotong sesuai aturan."""