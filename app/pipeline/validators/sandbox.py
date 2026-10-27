"""Kotak pasir (sandbox): menjalankan kode Python dengan batas.

Bukan batas keamanan yang sesungguhnya: di Windows tanpa
Docker, ini hanya subprocess biasa dengan batas waktu,
lingkungan yang dibersihkan, dan keluaran yang dibatasi.
Cara ini hanya diterima karena v1 menjalankan kode replay
yang sudah ditulis sebelumnya, bukan kode dari pengguna
yang tidak dikenal.

Keluaran ditulis ke berkas sementara, lalu hanya dibaca
sampai batas byte, supaya perulangan print yang tak
berujung tidak memenuhi memori.
"""

import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass

from app import config


@dataclass(frozen=True)
class SandboxResult:
    """Hasil satu kali menjalankan kode di sandbox."""

    stdout: str
    stderr: str
    returncode: int | None
    timed_out: bool
    truncated: bool

    @property
    def ok(self) -> bool:
        """True bila proses selesai tanpa timeout dan tanpa galat."""
        return not self.timed_out and self.returncode == 0


def run_code(code: str) -> SandboxResult:
    """Menjalankan kode dan mengembalikan hasilnya."""
    lingkungan = {"PATH": os.environ.get("PATH", "")}
    if os.name == "nt":
        # Python di Windows butuh SYSTEMROOT untuk berjalan.
        if "SYSTEMROOT" in os.environ:
            lingkungan["SYSTEMROOT"] = os.environ["SYSTEMROOT"]
    with tempfile.TemporaryDirectory() as folder:
        keluar = os.path.join(folder, "stdout.txt")
        galat = os.path.join(folder, "stderr.txt")
        with open(keluar, "wb") as f_out, open(galat, "wb") as f_err:
            proses = subprocess.Popen(
                [sys.executable, "-I", "-c", code],
                cwd=folder,
                env=lingkungan,
                stdout=f_out,
                stderr=f_err,
            )
            try:
                proses.wait(timeout=config.SANDBOX_TIMEOUT_SECONDS)
                timed_out = False
            except subprocess.TimeoutExpired:
                proses.kill()
                proses.wait()
                timed_out = True
        batas = config.SANDBOX_MAX_OUTPUT_BYTES
        with open(keluar, "rb") as f:
            mentah = f.read(batas + 1)
        with open(galat, "rb") as f:
            mentah_galat = f.read(batas + 1)
    return SandboxResult(
        stdout=mentah[:batas].decode("utf-8", errors="replace"),
        stderr=mentah_galat[:batas].decode("utf-8", errors="replace"),
        returncode=proses.returncode,
        timed_out=timed_out,
        truncated=len(mentah) > batas or len(mentah_galat) > batas,
    )
