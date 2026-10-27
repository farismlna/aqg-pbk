import time

from app.pipeline.validators.sandbox import run_code


def test_sandbox_print_sederhana():
    hasil = run_code('print("halo")')
    assert hasil.ok and hasil.stdout.strip() == "halo" and not hasil.timed_out


def test_sandbox_galat_ditangkap():
    hasil = run_code("raise ValueError('rusak')")
    assert not hasil.ok and "ValueError" in hasil.stderr


def test_sandbox_perulangan_tak_berujung_dibunuh():
    mulai = time.time()
    hasil = run_code("while True:\n    pass")
    assert hasil.timed_out
    assert time.time() - mulai < 5


def test_sandbox_keluaran_dibatasi():
    hasil = run_code("while True:\n    print('x')")
    assert hasil.timed_out
    assert len(hasil.stdout.encode()) <= 10000 + 100
