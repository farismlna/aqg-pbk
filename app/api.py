"""Route API Fase 3: kurasi dosen dan kuis siswa.

Dosen: upload modul, generate, lihat, edit, approve,
reject, publish, regenerate. Siswa: sesi anonim, daftar
soal terbit, jawab, rekap. Tidak ada data pribadi yang
diterima atau disimpan: sesi hanya UUID, jejak jawaban
hanya mencatat UUID sesi, ID soal, jawaban, benar atau
salah, dan waktu.
"""

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, Response


from app import config, storage
from app.errors import ChunkError, IngestError, TokenBudgetError
from app.llm.replay import ReplayAdapter
from app.pipeline.module_store import (
    DEMO_MODULE_ID,
    ModuleStore,
    get_module_store,
)
from app.pipeline.orchestrator import Orchestrator
from app.pipeline.validators.validate_item import validate_item
from app.quiz import grade, strip_item
from app.schemas import (
    AnswerRequest,
    AnswerResponse,
    GenerateRequest,
    Item,
    ItemStatus,
    QuizItem,
    RegenerateRequest,
    StoredItem,
)

router = APIRouter(prefix="/api")


def get_store() -> ModuleStore:
    """Modul aktif untuk proses ini."""
    return get_module_store()


def _teks_prompt() -> str:
    """Teks prompt sistem untuk pemeriksaan anggaran token.

    Bila berkas prompt tidak ada, anggaran diperiksa hanya
    atas potongan terambil (seperti pengujian Fase 2B).
    """
    try:
        return (config.PROMPT_DIR / "system_prompt.txt").read_text(
            encoding="utf-8"
        )
    except OSError:
        return ""


def _info_modul(store: ModuleStore) -> dict:
    aktif = store.active
    return {
        "module_id": aktif.module_id,
        "filename": aktif.filename,
        "pages": aktif.pages,
        "chunks": len(aktif.chunks),
        "chunk_ids": [potongan.chunk_id for potongan in aktif.chunks],
        "potongan": [
            {
                "chunk_id": potongan.chunk_id,
                "heading": potongan.heading,
                "page": potongan.page,
                "text": potongan.text,
            }
            for potongan in aktif.chunks
        ],
    }
    
    
@router.get("/modules/file")
def berkas_modul(store: ModuleStore = Depends(get_store)):
    """Isi PDF modul aktif, untuk panel PDF Teacher Dashboard.

    Modul demo dibaca dari disk; modul hasil upload
    dikembalikan dari isi PDF yang disimpan di memori.
    """
    aktif = store.active
    if aktif.module_id == DEMO_MODULE_ID:
        jalur = config.MODULE_DIR / "modul_demo.pdf"
        return FileResponse(
            jalur, media_type="application/pdf", filename="modul_demo.pdf"
        )
    if aktif.pdf_bytes is None:
        raise HTTPException(
            status_code=404, detail="Berkas PDF modul tidak tersedia."
        )
    return Response(
        content=aktif.pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'inline; filename="{aktif.filename or "modul.pdf"}"'
            )
        },
    )


def _jalankan_orchestrator(
    store: ModuleStore, topic: str, query: str, key_concepts: list[str], limit: int
) -> dict:
    """Menjalankan orchestrator dan menyimpan yang lolos sebagai draft.

    Mengembalikan dict berisi planner_output, daftar StoredItem,
    dan daftar penolakan. Generate ulang tidak menimpa butir
    yang sudah tersimpan (lihat app/storage.py).
    """
    potongan = store.active.chunks
    if not potongan:
        raise HTTPException(status_code=500, detail="Tidak ada materi aktif.")
    orchestrator = Orchestrator(
        potongan, ReplayAdapter.from_files(), _teks_prompt()
    )
    try:
        hasil = orchestrator.run(topic, query, key_concepts, limit=limit)
    except TokenBudgetError as galat:
        raise HTTPException(status_code=422, detail=str(galat)) from galat
    diterima: list[StoredItem] = []
    ditolak: list[dict] = []
    diterima_per_id = {item.item_id: item for item in hasil.items}
    for percobaan in hasil.attempts:
        if percobaan.accepted:
            item = diterima_per_id[percobaan.candidate_id]
            diterima.append(
                storage.save_item(item, ItemStatus.DRAFT, percobaan.report)
            )
        else:
            ditolak.append(
                {
                    "candidate_id": percobaan.candidate_id,
                    "failed_validators": percobaan.report.failed_names(),
                }
            )
    return {
        "planner": hasil.planner_output,
        "items": diterima,
        "rejected": ditolak,
    }


# --- Modul ---------------------------------------------------------------

@router.post("/modules")
async def upload_modul(
    file: UploadFile = File(...), store: ModuleStore = Depends(get_store)
) -> dict:
    """Mengunggah modul PDF dan menjadikannya modul aktif.

    Memakai batas yang sama dengan pembaca PDF: maksimal
    10 halaman dan 5 MB, teks saja (bukan hasil pindai).
    Modul aktif lama dipertahankan bila upload gagal.
    Modul hasil upload hanya hidup selama server berjalan;
    restart kembali ke modul demo (lihat DEVIATIONS.md).
    """
    data = await file.read()
    try:
        aktif = store.replace_from_bytes(data, file.filename or "modul.pdf")
    except (IngestError, ChunkError) as galat:
        raise HTTPException(status_code=400, detail=str(galat)) from galat
    return {
        "module_id": aktif.module_id,
        "filename": aktif.filename,
        "pages": aktif.pages,
        "chunks": len(aktif.chunks),
        "chunk_ids": [potongan.chunk_id for potongan in aktif.chunks],
    }


@router.get("/modules")
def info_modul(store: ModuleStore = Depends(get_store)) -> dict:
    """Keterangan modul aktif saat ini."""
    return _info_modul(store)


# --- Generate dan kurasi dosen --------------------------------------------

@router.post("/generate")
def generate(
    permintaan: GenerateRequest, store: ModuleStore = Depends(get_store)
) -> dict:
    """Menjalankan orchestrator dan menyimpan yang lolos sebagai draft."""
    return _jalankan_orchestrator(
        store,
        permintaan.topic,
        permintaan.query,
        permintaan.key_concepts,
        permintaan.limit,
    )


@router.get("/items", response_model=list[StoredItem])
def daftar_items(
    status: ItemStatus | None = Query(default=None),
) -> list[StoredItem]:
    """Daftar butir tersimpan, dapat disaring menurut status kurasi."""
    return storage.list_items(status)


@router.get("/items/{item_id}", response_model=StoredItem)
def detail_item(item_id: str) -> StoredItem:
    """Satu butir tersimpan beserta status dan laporan validatornya."""
    tersimpan = storage.get_item(item_id)
    if tersimpan is None:
        raise HTTPException(status_code=404, detail="Butir tidak ditemukan.")
    return tersimpan


@router.put("/items/{item_id}", response_model=StoredItem)
def edit_item(item_id: str, item: Item) -> StoredItem:
    """Mengedit butir: isi baru harus lolos semua validator,
    dan status kembali ke draft. Edit yang gagal tidak
    mengubah butir yang tersimpan."""
    if item.item_id != item_id:
        raise HTTPException(
            status_code=422,
            detail="item_id pada isi tidak sama dengan item_id pada alamat.",
        )
    if storage.get_item(item_id) is None:
        raise HTTPException(status_code=404, detail="Butir tidak ditemukan.")
    laporan = validate_item(item)
    if not laporan.all_passed():
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Edit tidak lolos validator.",
                "report": laporan.model_dump(mode="json"),
            },
        )
    hasil = storage.replace_item(item, laporan)
    assert hasil is not None
    return hasil


def _ambil_atau_404(item_id: str) -> StoredItem:
    tersimpan = storage.get_item(item_id)
    if tersimpan is None:
        raise HTTPException(status_code=404, detail="Butir tidak ditemukan.")
    return tersimpan


@router.post("/items/{item_id}/approve", response_model=StoredItem)
def approve_item(item_id: str) -> StoredItem:
    """Menyetujui draft. Hanya draft yang bisa disetujui."""
    tersimpan = _ambil_atau_404(item_id)
    if tersimpan.status != ItemStatus.DRAFT:
        raise HTTPException(
            status_code=409,
            detail=f"Hanya draft yang bisa disetujui (status saat ini: {tersimpan.status.value}).",
        )
    hasil = storage.set_status(item_id, ItemStatus.APPROVED)
    assert hasil is not None
    return hasil


@router.post("/items/{item_id}/reject", response_model=StoredItem)
def reject_item(item_id: str) -> StoredItem:
    """Menolak draft atau butir yang disetujui. Penolakan bersifat final."""
    tersimpan = _ambil_atau_404(item_id)
    if tersimpan.status not in (ItemStatus.DRAFT, ItemStatus.APPROVED):
        raise HTTPException(
            status_code=409,
            detail=f"Status {tersimpan.status.value} tidak bisa ditolak.",
        )
    hasil = storage.set_status(item_id, ItemStatus.REJECTED)
    assert hasil is not None
    return hasil


@router.post("/items/{item_id}/publish", response_model=StoredItem)
def publish_item(item_id: str) -> StoredItem:
    """Menerbitkan butir yang disetujui. Hanya yang disetujui bisa terbit."""
    tersimpan = _ambil_atau_404(item_id)
    if tersimpan.status != ItemStatus.APPROVED:
        raise HTTPException(
            status_code=409,
            detail=f"Hanya yang disetujui yang bisa diterbitkan (status saat ini: {tersimpan.status.value}).",
        )
    hasil = storage.set_status(item_id, ItemStatus.PUBLISHED)
    assert hasil is not None
    return hasil


@router.post("/items/{item_id}/regenerate")
def regenerate_item(
    item_id: str,
    permintaan: RegenerateRequest,
    store: ModuleStore = Depends(get_store),
) -> dict:
    """Menjalankan ulang orchestrator untuk topik butir ini.

    Kandidat yang lolos disimpan sebagai draft baru; butir
    lama tidak diubah. Bila kandidatnya sama dengan yang
    sudah tersimpan, yang dikembalikan adalah butir lama.
    """
    tersimpan = _ambil_atau_404(item_id)
    konsep = permintaan.key_concepts or [tersimpan.item.topic]
    return _jalankan_orchestrator(
        store,
        tersimpan.item.topic,
        permintaan.query or tersimpan.item.topic,
        konsep,
        permintaan.limit,
    )


# --- Kuis siswa ------------------------------------------------------------

@router.post("/quiz/session")
def buat_sesi() -> dict:
    """Menerbitkan UUID sesi anonim. Tidak ada nama atau NIM yang diminta."""
    return {"session_id": str(uuid.uuid4())}


@router.get("/quiz", response_model=list[QuizItem])
def daftar_kuis() -> list[QuizItem]:
    """Soal yang sudah terbit, tanpa kunci jawaban dan umpan balik."""
    terbit = storage.list_items(ItemStatus.PUBLISHED)
    return [strip_item(tersimpan.item) for tersimpan in terbit]


def _uuid_sesi(session_id: str) -> str:
    try:
        return str(uuid.UUID(session_id))
    except ValueError as galat:
        raise HTTPException(
            status_code=422, detail="session_id harus berupa UUID."
        ) from galat


@router.post("/quiz/answer", response_model=AnswerResponse)
def jawab_kuis(jawaban: AnswerRequest) -> AnswerResponse:
    """Menilai satu jawaban, mencatat jejak, dan mengembalikan umpan balik.

    Hanya soal yang sudah terbit yang bisa dijawab.
    """
    sesi = _uuid_sesi(jawaban.session_id)
    tersimpan = storage.get_item(jawaban.item_id)
    if tersimpan is None or tersimpan.status != ItemStatus.PUBLISHED:
        raise HTTPException(
            status_code=404, detail="Soal tidak ditemukan atau belum terbit."
        )
    benar, umpan_balik = grade(tersimpan.item, jawaban.chosen)
    storage.save_attempt(sesi, jawaban.item_id, jawaban.chosen, benar)
    return AnswerResponse(
        item_id=jawaban.item_id,
        correct=benar,
        feedback=umpan_balik,
        expected_output=tersimpan.item.answer_key.expected_output,
    )


@router.get("/quiz/summary")
def rekap_kuis(session_id: str = Query(...)) -> dict:
    """Rekap satu sesi: jumlah soal dijawab dan jumlah yang benar."""
    sesi = _uuid_sesi(session_id)
    jejak = storage.list_attempts(sesi)
    return {
        "session_id": sesi,
        "total": len(jejak),
        "correct": sum(1 for baris in jejak if baris["correct"]),
        "answers": jejak,
    }
