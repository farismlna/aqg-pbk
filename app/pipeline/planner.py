"""Perencana (Planner) dari potongan yang sudah terambil.

Planner di sini tidak memanggil model bahasa. Ia hanya merangkum
hasil pengambilan menjadi PlannerOutput yang sesuai skema:
status ok bila ada potongan dan ada konsep kunci, dan status
insufficient_context bila tidak ada potongan yang terambil.
Coverage dihitung dari potongan dengan app/pipeline/coverage.py.
"""

from app.pipeline.chunker import Chunk
from app.pipeline.coverage import build_coverage
from app.schemas import Coverage, PlannerOutput, PlannerStatus


def make_planner_output(
    topic: str, chunks: list[Chunk], key_concepts: list[str]
) -> PlannerOutput:
    """Membuat PlannerOutput dari potongan terambil.

    Tanpa potongan, hasilnya insufficient_context dengan konsep
    kunci dan coverage yang kosong, sesuai aturan skema.
    """
    if not chunks:
        return PlannerOutput(
            topic=topic,
            status=PlannerStatus.INSUFFICIENT_CONTEXT,
            chunk_ids=[],
            key_concepts=[],
            coverage=Coverage(),
        )
    if not key_concepts:
        raise ValueError(
            "Status 'ok' wajib punya key_concepts; berikan konsep kunci "
            "atau pakai daftar potongan kosong untuk insufficient_context."
        )
    return PlannerOutput(
        topic=topic,
        status=PlannerStatus.OK,
        chunk_ids=[c.chunk_id for c in chunks],
        key_concepts=list(key_concepts),
        coverage=build_coverage(chunks),
    )
