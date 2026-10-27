"""Memotong teks modul menjadi potongan (chunk) berukuran paling banyak 400 token.

Aturan pemotongan:
1. Potongan tidak pernah memotong di tengah baris.
2. Satu potongan hanya berisi satu bagian materi (satu judul "N.N ...").
3. Blok kode (antara dua garis putus-putus) dijaga utuh. Hanya bila satu
   blok sendirian melebihi batas, blok itu dipecah per baris.
4. Baris judul topik ("Topik 04: ...") selalu digabung ke bagian bernomor
   berikutnya, begitu pula bagian bernomor yang sangat pendek (kurang dari
   MIN_SECTION_TOKENS), supaya tidak ada potongan kecil tak bermakna.
5. Teks sebelum judul pertama (halaman judul dokumen) dibuang, asalkan
   modul punya minimal satu judul. Modul tanpa judul dipertahankan utuh.
6. Tidak ada tumpang tindih antar potongan.
"""

import re
from dataclasses import dataclass

from app import config
from app.errors import ChunkError
from app.pipeline.ingest import Page
from app.pipeline.tokens import count_tokens

HEADING_RE = re.compile(r"^\d+\.\d+\s+\S")
TOPIK_RE = re.compile(r"^Topik\s+\d+\s*:", re.IGNORECASE)
DECOR_RE = re.compile(r"^={5,}$")
DASH_RE = re.compile(r"^-{5,}$")
CAPTION_RE = re.compile(r"^Contoh\b", re.IGNORECASE)
CODE_PREFIX_RE = re.compile(r"^\s*\d+ \|( |$)")
NO_HEADING = "(tanpa judul)"


@dataclass(frozen=True)
class Chunk:
    """Satu potongan teks beserta keterangannya."""

    chunk_id: str
    page: int
    heading: str
    text: str
    tokens: int
    code_blocks: tuple[str, ...]


@dataclass(frozen=True)
class _Line:
    page: int
    text: str
    block_id: int | None  # nomor blok kode bila baris ini ada di dalam blok


def _count(lines: list[_Line]) -> int:
    return count_tokens("\n".join(baris.text for baris in lines))


def _read_lines(pages: list[Page]) -> list[_Line]:
    """Mengubah halaman menjadi daftar baris bersih.

    Baris kosong dan garis hias "=====" dibuang. Spasi di awal baris
    (indentasi kode) dipertahankan; hanya spasi di akhir yang dibuang.
    """
    hasil: list[_Line] = []
    dalam_blok: int | None = None
    penghitung = 0
    for halaman in pages:
        for baris in halaman.text.splitlines():
            baris = baris.rstrip()
            if not baris.strip():
                continue
            if DECOR_RE.match(baris.strip()):
                continue
            if DASH_RE.match(baris.strip()):
                if dalam_blok is None:
                    dalam_blok = penghitung
                    penghitung += 1
                else:
                    dalam_blok = None
                hasil.append(_Line(halaman.number, baris, None))
                continue
            hasil.append(_Line(halaman.number, baris, dalam_blok))
    return hasil


def _is_heading(baris: _Line) -> bool:
    if baris.block_id is not None:
        return False
    teks = baris.text.strip()
    return bool(HEADING_RE.match(teks) or TOPIK_RE.match(teks))


def _split_sections(lines: list[_Line]) -> list[tuple[str | None, list[_Line]]]:
    bagian: list[tuple[str | None, list[_Line]]] = []
    judul: str | None = None
    saat_ini: list[_Line] = []
    for baris in lines:
        if _is_heading(baris):
            if saat_ini:
                bagian.append((judul, saat_ini))
            judul = baris.text.strip()
            saat_ini = [baris]
        else:
            saat_ini.append(baris)
    if saat_ini:
        bagian.append((judul, saat_ini))
    return bagian


def _is_topic_title(judul: str | None) -> bool:
    return judul is not None and bool(TOPIK_RE.match(judul))


def _merge_small(
    sections: list[tuple[str | None, list[_Line]]],
) -> list[tuple[str | None, list[_Line]]]:
    """Menggabungkan bagian pendek dan judul topik ke bagian berikutnya.

    Bagian tanpa judul di awal (halaman judul dokumen) dibuang bila modul
    punya judul. Baris judul topik selalu ikut ke bagian bernomor berikutnya.
    """
    hasil: list[tuple[str | None, list[_Line]]] = []
    bawa: list[_Line] = []
    for indeks, (judul, baris) in enumerate(sections):
        if judul is None and len(sections) > 1:
            continue
        gabungan = bawa + baris
        terakhir = indeks == len(sections) - 1
        if not terakhir and (
            _is_topic_title(judul)
            or _count(gabungan) < config.MIN_SECTION_TOKENS
        ):
            bawa = gabungan
            continue
        hasil.append((judul, gabungan))
        bawa = []
    return hasil


def _make_units(lines: list[_Line]) -> list[list[_Line]]:
    """Membagi baris menjadi unit yang tidak boleh dipisah.

    Satu baris teks = satu unit. Satu blok kode (dari garis pembuka sampai
    garis penutup) = satu unit, bersama baris keterangan "Contoh ..." di atasnya.
    """
    unit: list[list[_Line]] = []
    i = 0
    n = len(lines)
    while i < n:
        if DASH_RE.match(lines[i].text.strip()):
            j = i + 1
            while j < n and not DASH_RE.match(lines[j].text.strip()):
                j += 1
            akhir = min(j, n - 1)
            blok = lines[i : akhir + 1]
            if (
                unit
                and len(unit[-1]) == 1
                and CAPTION_RE.match(unit[-1][0].text.strip())
            ):
                blok = unit.pop() + blok
            unit.append(blok)
            i = akhir + 1
        else:
            unit.append([lines[i]])
            i += 1
    return unit


def _fit_unit(unit: list[_Line]) -> list[list[_Line]]:
    """Mengembalikan unit apa adanya bila muat; bila tidak, pecah per baris."""
    if _count(unit) <= config.CHUNK_TOKENS:
        return [unit]
    bagian: list[list[_Line]] = []
    for baris in unit:
        jumlah = _count([baris])
        if jumlah > config.CHUNK_TOKENS:
            raise ChunkError(
                f"Satu baris terlalu panjang untuk dipotong: {jumlah} token "
                f"(batas {config.CHUNK_TOKENS}) pada halaman {baris.page}."
            )
        bagian.append([baris])
    return bagian


def _pack(units: list[list[_Line]]) -> list[list[_Line]]:
    """Menyusun unit ke dalam potongan secara berurutan (greedy)."""
    potongan: list[list[_Line]] = []
    saat_ini: list[_Line] = []
    for unit in units:
        for bagian in _fit_unit(unit):
            kandidat = saat_ini + bagian
            if saat_ini and _count(kandidat) > config.CHUNK_TOKENS:
                potongan.append(saat_ini)
                saat_ini = list(bagian)
            else:
                saat_ini = kandidat
    if saat_ini:
        potongan.append(saat_ini)
    return potongan


def _extract_code_blocks(lines: list[_Line]) -> tuple[str, ...]:
    """Mengambil kode bersih (tanpa nomor baris) dari baris-baris sebuah potongan."""
    kelompok: list[tuple[int, list[str]]] = []
    for baris in lines:
        if baris.block_id is None:
            continue
        bersih = CODE_PREFIX_RE.sub("", baris.text, count=1)
        if kelompok and kelompok[-1][0] == baris.block_id:
            kelompok[-1][1].append(bersih)
        else:
            kelompok.append((baris.block_id, [bersih]))
    return tuple("\n".join(isi) for _, isi in kelompok)


def chunk_pages(pages: list[Page], module_id: str = "MOD") -> list[Chunk]:
    """Memotong halaman modul menjadi daftar Chunk."""
    if config.CHUNK_OVERLAP_TOKENS != 0:
        raise ChunkError("Tumpang tindih potongan belum didukung (harus 0).")

    baris_semua = _read_lines(pages)
    if not baris_semua:
        raise ChunkError("Tidak ada teks yang bisa dipotong.")

    sections = _merge_small(_split_sections(baris_semua))
    hasil: list[Chunk] = []
    nomor_per_halaman: dict[int, int] = {}
    for judul, baris_bagian in sections:
        for baris_potongan in _pack(_make_units(baris_bagian)):
            halaman = baris_potongan[0].page
            nomor = nomor_per_halaman.get(halaman, 0) + 1
            nomor_per_halaman[halaman] = nomor
            teks = "\n".join(baris.text for baris in baris_potongan)
            jumlah = count_tokens(teks)
            if jumlah > config.CHUNK_TOKENS:
                raise ChunkError(
                    f"Potongan melebihi batas: {jumlah} token "
                    f"(batas {config.CHUNK_TOKENS})."
                )
            hasil.append(
                Chunk(
                    chunk_id=f"{module_id}-P{halaman:02d}-C{nomor:02d}",
                    page=halaman,
                    heading=judul or NO_HEADING,
                    text=teks,
                    tokens=jumlah,
                    code_blocks=_extract_code_blocks(baris_potongan),
                )
            )
    return hasil