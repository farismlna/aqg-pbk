import ast
import re

import pytest

from app import config
from app.errors import ChunkError
from app.pipeline.chunker import chunk_pages
from app.pipeline.ingest import Page
from app.pipeline.tokens import count_tokens

KODE_4_1 = "\n".join([
    "n = 4",
    "total = 0",
    "for i in range(1, n):",
    "    total += i",
    'print("Total akumulasi deret:", total)',
])


def baris_asli(halaman):
    """Baris asli modul tanpa baris kosong, garis hias '=====',
    dan teks sebelum judul pertama (halaman judul dokumen)."""
    hasil = []
    for h in halaman:
        for baris in h.text.splitlines():
            baris = baris.rstrip()
            if not baris.strip():
                continue
            if set(baris.strip()) == {"="}:
                continue
            hasil.append(baris)
    awal = next(
        i for i, b in enumerate(hasil)
        if re.match(r"^(\d+\.\d+\s|Topik\s+\d+\s*:)", b, re.IGNORECASE)
    )
    return hasil[awal:]


def baris_dari_potongan(potongan):
    return [b for p in potongan for b in p.text.splitlines()]


def test_semua_potongan_dalam_batas_token(halaman_demo):
    for p in chunk_pages(halaman_demo, module_id="DEMO"):
        assert p.tokens <= config.CHUNK_TOKENS
        assert count_tokens(p.text) == p.tokens


def test_id_unik_dan_berformat(halaman_demo):
    potongan = chunk_pages(halaman_demo, module_id="DEMO")
    daftar_id = [p.chunk_id for p in potongan]
    assert len(set(daftar_id)) == len(daftar_id)
    for nilai in daftar_id:
        assert re.fullmatch(r"DEMO-P\d{2}-C\d{2}", nilai)


def test_judul_bagian_lengkap(halaman_demo):
    potongan = chunk_pages(halaman_demo, module_id="DEMO")
    awalan = {p.heading.split()[0] for p in potongan}
    assert awalan == {"4.1", "4.2", "5.1", "5.2", "5.3"}


def test_judul_dokumen_dibuang_dan_topik_ikut_bagian(halaman_demo):
    potongan = chunk_pages(halaman_demo, module_id="DEMO")
    for p in potongan:
        assert "MODUL PRAKTIKUM" not in p.text
        assert not p.heading.startswith("Topik")
    assert potongan[0].text.splitlines()[0].startswith("Topik 04")


def test_modul_tanpa_judul_dipertahankan():
    halaman = [Page(number=1, text="Paragraf tentang variabel.\nParagraf tentang tipe data.")]
    potongan = chunk_pages(halaman)
    assert len(potongan) == 1
    assert potongan[0].heading == "(tanpa judul)"
    assert potongan[0].text.splitlines() == [
        "Paragraf tentang variabel.",
        "Paragraf tentang tipe data.",
    ]


def test_isi_utuh_tanpa_hilang_atau_ganda(halaman_demo):
    potongan = chunk_pages(halaman_demo, module_id="DEMO")
    assert baris_dari_potongan(potongan) == baris_asli(halaman_demo)


def test_blok_kode_tidak_terpotong(halaman_demo):
    for p in chunk_pages(halaman_demo, module_id="DEMO"):
        garis = [
            b for b in p.text.splitlines() if set(b.strip()) == {"-"}
        ]
        assert len(garis) % 2 == 0


def test_kode_diambil_bersih_dan_valid(halaman_demo):
    potongan = chunk_pages(halaman_demo, module_id="DEMO")
    semua_kode = [k for p in potongan for k in p.code_blocks]
    assert len(semua_kode) == 5
    assert KODE_4_1 in semua_kode
    for kode in semua_kode:
        ast.parse(kode)


def test_batas_kecil_memakai_pemecahan_baris(halaman_demo, monkeypatch):
    awal = chunk_pages(halaman_demo, module_id="DEMO")
    monkeypatch.setattr(config, "CHUNK_TOKENS", 100)
    kecil = chunk_pages(halaman_demo, module_id="DEMO")
    assert len(kecil) > len(awal)
    for p in kecil:
        assert p.tokens <= 100
    assert baris_dari_potongan(kecil) == baris_asli(halaman_demo)


def test_satu_baris_terlalu_panjang_ditolak():
    halaman = [Page(number=1, text="kata " * 500)]
    with pytest.raises(ChunkError):
        chunk_pages(halaman)


def test_tumpang_tindih_belum_didukung(halaman_demo, monkeypatch):
    monkeypatch.setattr(config, "CHUNK_OVERLAP_TOKENS", 10)
    with pytest.raises(ChunkError):
        chunk_pages(halaman_demo)