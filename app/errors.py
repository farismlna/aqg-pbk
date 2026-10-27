"""Jenis galat khusus aplikasi AQG-DDP."""


class AqgError(Exception):
    """Induk semua galat khusus aplikasi ini."""


class TokenBudgetError(AqgError):
    """Dilempar ketika anggaran token terlampaui."""