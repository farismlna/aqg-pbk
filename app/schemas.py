"""Bentuk data (skema) untuk prototipe AQG-DDP.

Skema = aturan bentuk data yang boleh diterima. Data yang melanggar
aturan akan ditolak dengan pesan yang jelas.

Aturan penting yang sudah dikunci:
- Tipe kesalahan pengecoh boleh "other" dan boleh sama antar pengecoh
  (tidak ada aturan satu-tiap-tipe).
- Tipe "other" wajib punya catatan (misconception_note).
- Soal isian rumpang wajib punya tanda ____ dan daftar jawaban yang
  diterima.
- Keluaran Planner punya kolom coverage (heading + konstruksi kode).
"""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

BLANK_MARKER = "____"
MIN_MCQ_DISTRACTORS = 3


def _norm(teks: str) -> str:
    """Menyamakan teks: huruf kecil, spasi berlebih dibuang."""
    return " ".join(teks.split()).lower()


class StrictModel(BaseModel):
    """Dasar semua skema. extra="forbid" = kolom yang tidak dikenal
    ditolak, sehingga salah ketik nama kolom langsung ketahuan."""

    model_config = ConfigDict(extra="forbid")


# --- Daftar pilihan tetap -------------------------------------------------

class ItemFormat(StrEnum):
    MCQ = "mcq"                      # pilihan ganda
    FILL_IN_BLANK = "fill_in_blank"  # isian rumpang


class MisconceptionType(StrEnum):
    OFF_BY_ONE = "off_by_one"
    ASSIGNMENT_ERROR = "assignment_error"
    LOGIC_ERROR = "logic_error"
    SYNTAX_ERROR = "syntax_error"
    OTHER = "other"


class PlannerStatus(StrEnum):
    OK = "ok"
    INSUFFICIENT_CONTEXT = "insufficient_context"  # materi tidak cukup


# --- Bagian-bagian butir soal ---------------------------------------------

class Feedback(StrictModel):
    """Umpan balik tiga bagian untuk satu jawaban."""

    diagnosis: str = Field(min_length=1)    # apa yang mungkin dipikirkan siswa
    explanation: str = Field(min_length=1)  # mengapa salah / konsepnya
    next_step: str = Field(min_length=1)    # saran langkah berikutnya


class Distractor(StrictModel):
    """Satu jawaban salah (pengecoh).

    Untuk pilihan ganda, option_id wajib terisi (misalnya "B").
    Untuk isian rumpang, option_id dikosongkan: ini adalah jawaban
    salah yang diperkirakan akan diketik siswa.
    """

    option_id: str | None = None
    text: str = Field(min_length=1)
    misconception_type: MisconceptionType
    subtype: str | None = None
    misconception_note: str | None = None
    mutated_code: str | None = None  # kode yang menghasilkan jawaban ini
    feedback: Feedback

    @model_validator(mode="after")
    def _other_wajib_catatan(self) -> "Distractor":
        if self.misconception_type == MisconceptionType.OTHER:
            catatan = self.misconception_note or ""
            if not catatan.strip():
                raise ValueError(
                    "Tipe 'other' wajib punya misconception_note."
                )
        return self


class AnswerKey(StrictModel):
    """Kunci jawaban."""

    option_id: str | None = None      # wajib untuk pilihan ganda
    text: str = Field(min_length=1)
    expected_output: str | None = None  # keluaran program yang benar
    explanation: str = Field(min_length=1)


# --- Butir soal ------------------------------------------------------------

def _periksa_mcq(item: "Item") -> None:
    if len(item.distractors) < MIN_MCQ_DISTRACTORS:
        raise ValueError(
            f"Pilihan ganda butuh minimal {MIN_MCQ_DISTRACTORS} pengecoh."
        )
    if item.answer_key.option_id is None:
        raise ValueError("Kunci pilihan ganda wajib punya option_id.")

    semua_id = [item.answer_key.option_id]
    semua_teks = [_norm(item.answer_key.text)]
    for pengecoh in item.distractors:
        if pengecoh.option_id is None:
            raise ValueError("Semua pengecoh pilihan ganda wajib punya option_id.")
        semua_id.append(pengecoh.option_id)
        semua_teks.append(_norm(pengecoh.text))

    if len(set(semua_id)) != len(semua_id):
        raise ValueError("option_id harus unik.")
    if len(set(semua_teks)) != len(semua_teks):
        raise ValueError(
            "Teks pilihan harus berbeda satu sama lain "
            "(termasuk berbeda dari kunci)."
        )


def _periksa_isian(item: "Item") -> None:
    if item.code is None or BLANK_MARKER not in item.code:
        raise ValueError(f"Soal isian wajib punya kode berisi {BLANK_MARKER}.")
    diterima = [_norm(j) for j in item.accepted_answers]
    if _norm(item.answer_key.text) not in diterima:
        raise ValueError("accepted_answers wajib memuat jawaban kunci.")
    for pengecoh in item.distractors:
        if _norm(pengecoh.text) in diterima:
            raise ValueError(
                f"Jawaban salah '{pengecoh.text}' ternyata ada di accepted_answers."
            )


class Item(StrictModel):
    """Satu butir soal (pilihan ganda atau isian rumpang)."""

    item_id: str = Field(min_length=1)
    item_format: ItemFormat
    topic: str = Field(min_length=1)
    stem: str = Field(min_length=1)          # kalimat pertanyaan
    code: str | None = None                  # kode pada soal
    answer_key: AnswerKey
    distractors: list[Distractor] = Field(default_factory=list)
    accepted_answers: list[str] = Field(default_factory=list)
    source_chunk_id: str = Field(min_length=1)
    source_page: int = Field(ge=1)

    @model_validator(mode="after")
    def _periksa_sesuai_format(self) -> "Item":
        if self.item_format == ItemFormat.MCQ:
            _periksa_mcq(self)
        else:
            _periksa_isian(self)
        return self


# --- Keluaran Planner -----------------------------------------------------

class Coverage(StrictModel):
    """Cakupan materi: heading dan konstruksi kode yang tersentuh."""

    headings: list[str] = Field(default_factory=list)
    code_constructs: list[str] = Field(default_factory=list)


class PlannerOutput(StrictModel):
    topic: str = Field(min_length=1)
    status: PlannerStatus
    chunk_ids: list[str] = Field(default_factory=list)
    key_concepts: list[str] = Field(default_factory=list)
    coverage: Coverage = Field(default_factory=Coverage)

    @model_validator(mode="after")
    def _periksa_status(self) -> "PlannerOutput":
        if self.status == PlannerStatus.OK:
            if not self.chunk_ids or not self.key_concepts:
                raise ValueError(
                    "Status 'ok' wajib punya chunk_ids dan key_concepts."
                )
        else:
            if self.key_concepts:
                raise ValueError(
                    "Status 'insufficient_context' tidak boleh punya key_concepts."
                )
        return self


# --- Laporan hasil pemeriksaan --------------------------------------------

class ValidatorResult(StrictModel):
    name: str = Field(min_length=1)
    passed: bool
    detail: str = ""


class ValidationReport(StrictModel):
    results: list[ValidatorResult] = Field(default_factory=list)

    def all_passed(self) -> bool:
        """True hanya jika ada hasil dan semuanya lolos.

        Laporan kosong dianggap BELUM lolos (belum diperiksa).
        """
        return bool(self.results) and all(r.passed for r in self.results)

    def failed_names(self) -> list[str]:
        return [r.name for r in self.results if not r.passed]
    
# --- Penyimpanan dan API (Fase 3) ------------------------------------------

class ItemStatus(StrEnum):
    """Status kurasi satu butir soal yang tersimpan."""

    DRAFT = "draft"            # baru dibuat, belum dikurasi
    APPROVED = "approved"      # disetujui dosen, belum terbit
    PUBLISHED = "published"    # terbit, bisa dikerjakan siswa
    REJECTED = "rejected"      # ditolak, tidak bisa terbit


class StoredItem(StrictModel):
    """Butir soal yang tersimpan beserta status kurasi dan laporan validator."""

    item: Item
    status: ItemStatus = ItemStatus.DRAFT
    report: ValidationReport | None = None


class GenerateRequest(StrictModel):
    """Permintaan generate: topik, pertanyaan, konsep kunci, batas jumlah."""

    topic: str = Field(min_length=1)
    query: str = Field(min_length=1)
    key_concepts: list[str] = Field(min_length=1)
    limit: int = Field(default=10, ge=1, le=10)


class RegenerateRequest(StrictModel):
    """Permintaan regenerate untuk satu butir soal yang sudah ada."""

    query: str = ""
    key_concepts: list[str] = Field(default_factory=list)
    limit: int = Field(default=1, ge=1, le=10)


class QuizDistractor(StrictModel):
    """Pengecoh versi siswa: hanya huruf pilihan dan teksnya.

    Jenis miskonsepsi dan umpan balik disembunyikan sampai
    siswa menjawab, supaya tidak membocorkan jawaban.
    """

    option_id: str | None = None
    text: str = Field(min_length=1)


class QuizItem(StrictModel):
    """Butir soal versi siswa: tanpa kunci jawaban dan tanpa umpan balik."""

    item_id: str = Field(min_length=1)
    item_format: ItemFormat
    topic: str = Field(min_length=1)
    stem: str = Field(min_length=1)
    code: str | None = None
    distractors: list[QuizDistractor] = Field(default_factory=list)
    source_chunk_id: str = Field(min_length=1)
    source_page: int = Field(ge=1)


class AnswerRequest(StrictModel):
    """Jawaban siswa: UUID sesi, ID soal, dan jawaban yang dipilih/diketik."""

    session_id: str = Field(min_length=1)
    item_id: str = Field(min_length=1)
    chosen: str = Field(min_length=1)


class AnswerResponse(StrictModel):
    """Hasil penilaian: benar atau salah, umpan balik, dan keluaran yang benar."""

    item_id: str = Field(min_length=1)
    correct: bool
    feedback: Feedback
    expected_output: str | None = None
