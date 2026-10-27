"""Orchestrator Fase 2B: ambil, rencanakan, coba, validasi.

Alur:
1. Retriever mengambil potongan (TF-IDF). Gerbang skor:
   bila potongan teratas berskor 0 (tidak ada kata
   pertanyaan yang muncul di materi), materi dinyatakan
   tidak cukup dan Planner mengembalikan
   insufficient_context, tanpa mencoba kandidat apa pun.
2. Anggaran token diperiksa atas prompt yang dirakit dan
   potongan yang terambil.
3. Planner merangkum potongan terambil + konsep kunci.
4. Setiap kandidat dari adapter dicoba berurutan dengan
   validator schema, ast, lint, sandbox, lalu fill_blank.
   Kandidat yang gagal ditolak dan dicatat alasannya;
   kandidat yang lolos diterima, sampai batas jumlah
   yang diminta atau kandidat habis.

Orchestrator tidak memanggil LLM dan tidak memutuskan
sendiri isi soal: ia hanya menjalankan kandidat replay
melalui validator yang sama untuk semua.
"""

from dataclasses import dataclass, field

from app.llm.base import CandidateSource
from app.pipeline.chunker import Chunk
from app.pipeline.planner import make_planner_output
from app.pipeline.retriever import Retriever
from app.pipeline.tokens import check_budget
from app.pipeline.validators.ast_check import validate_ast
from app.pipeline.validators.fill_blank_check import validate_fill_blank
from app.pipeline.validators.lint_check import validate_lint
from app.pipeline.validators.sandbox_check import validate_sandbox
from app.pipeline.validators.schema_check import validate_schema
from app.schemas import Item, PlannerOutput, ValidationReport, ValidatorResult


@dataclass(frozen=True)
class Attempt:
    """Satu kali percobaan kandidat melalui semua validator."""

    candidate_id: str
    report: ValidationReport
    accepted: bool


@dataclass(frozen=True)
class OrchestratorResult:
    """Hasil satu kali menjalankan orchestrator."""

    planner_output: PlannerOutput
    attempts: list[Attempt] = field(default_factory=list)
    items: list[Item] = field(default_factory=list)


class Orchestrator:
    """Menjalankan alur 2B dari potongan dan sumber kandidat."""

    def __init__(
        self,
        chunks: list[Chunk],
        source: CandidateSource,
        prompt_text: str = "",
    ) -> None:
        self._chunks = list(chunks)
        self._source = source
        self._prompt_text = prompt_text

    def run(
        self,
        topic: str,
        query: str,
        key_concepts: list[str],
        limit: int = 1,
    ) -> OrchestratorResult:
        """Menjalankan alur dan mengembalikan hasil + jejak percobaan."""
        if limit < 1:
            raise ValueError(f"limit harus minimal 1, bukan {limit}.")
        pengambil = Retriever(self._chunks)
        terambil = pengambil.retrieve(query)
        if not terambil or terambil[0].score <= 0:
            # Gerbang skor: tidak ada potongan yang relevan.
            return OrchestratorResult(
                planner_output=make_planner_output(topic, [], []),
                attempts=[],
                items=[],
            )
        potongan = [s.chunk for s in terambil]
        # Anggaran token: prompt + potongan terambil. Melempar
        # TokenBudgetError bila prompt atau potongan melanggar batas.
        check_budget(self._prompt_text, [c.text for c in potongan])
        planner = make_planner_output(topic, potongan, key_concepts)

        attempts: list[Attempt] = []
        diterima: list[Item] = []
        for kandidat in self._source.candidates():
            if len(diterima) >= limit:
                break
            candidate_id = str(
                kandidat.get("item_id", "tanpa-id")
                if isinstance(kandidat, dict)
                else "tanpa-id"
            )
            if not isinstance(kandidat, dict):
                report = ValidationReport(results=[
                    ValidatorResult(
                        name="schema",
                        passed=False,
                        detail="Kandidat bukan objek JSON.",
                    )
                ])
                attempts.append(
                    Attempt(candidate_id, report, accepted=False)
                )
                continue
            item, hasil_schema = validate_schema(kandidat)
            if item is None:
                report = ValidationReport(results=[hasil_schema])
                attempts.append(
                    Attempt(candidate_id, report, accepted=False)
                )
                continue
            hasil: list[ValidatorResult] = [hasil_schema]
            # Validator dijalankan berurutan dan berhenti di
            # kegagalan pertama: validator berikutnya tidak
            # bermakna bila kode sudah terbukti rusak.
            for periksa in (
                validate_ast,
                validate_lint,
                validate_sandbox,
                validate_fill_blank,
            ):
                hasil.append(periksa(item))
                if not hasil[-1].passed:
                    break
            report = ValidationReport(results=hasil)
            if report.all_passed():
                attempts.append(Attempt(candidate_id, report, accepted=True))
                diterima.append(item)
            else:
                attempts.append(Attempt(candidate_id, report, accepted=False))
        return OrchestratorResult(
            planner_output=planner,
            attempts=attempts,
            items=diterima,
        )
