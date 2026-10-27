"""Logika Student View: menyembunyikan kunci dan menilai jawaban.

Daftar soal untuk siswa tidak menandai jawaban mana yang
benar dan tidak memuat umpan balik, supaya jawaban tidak
bocor sebelum siswa menjawab. Untuk pilihan ganda, kunci
ikut ditampilkan sebagai salah satu pilihan, diurutkan
menurut huruf pilihan, tanpa penanda mana yang benar.
Umpan balik baru diberikan setelah jawaban dinilai:
jawaban benar mendapat penjelasan dari kunci, jawaban
salah mendapat umpan balik distraktor yang cocok, dan
jawaban salah yang tidak cocok dengan distraktor mana pun
mendapat umpan balik umum dari penjelasan kunci.
"""


from app.schemas import Feedback, Item, QuizDistractor, QuizItem


def _norm(teks: str) -> str:
    """Menyamakan teks: huruf kecil, spasi berlebih dibuang."""
    return " ".join(teks.split()).lower()


def strip_item(item: Item) -> QuizItem:
    """Versi siswa dari satu butir soal, tanpa penanda kunci dan umpan balik.

    Pilihan ganda: kunci ikut menjadi salah satu pilihan,
    diurutkan menurut huruf pilihan. Isian rumpang: kunci
    tidak ditampilkan; siswa mengetik jawabannya.
    """
    if item.item_format.value == "mcq":
        pilihan = [
            QuizDistractor(option_id=d.option_id, text=d.text)
            for d in item.distractors
        ]
        pilihan.append(
            QuizDistractor(
                option_id=item.answer_key.option_id,
                text=item.answer_key.text,
            )
        )
        pilihan.sort(key=lambda p: p.option_id or "")
    else:
        pilihan = [
            QuizDistractor(option_id=d.option_id, text=d.text)
            for d in item.distractors
        ]
    return QuizItem(
        item_id=item.item_id,
        item_format=item.item_format,
        topic=item.topic,
        stem=item.stem,
        code=item.code,
        distractors=pilihan,
        source_chunk_id=item.source_chunk_id,
        source_page=item.source_page,
    )


def _umpan_balik_benar(item: Item) -> Feedback:
    return Feedback(
        diagnosis="Jawaban benar.",
        explanation=item.answer_key.explanation,
        next_step="Lanjut ke soal berikutnya.",
    )


def _umpan_balik_umum(item: Item) -> Feedback:
    return Feedback(
        diagnosis="Jawaban belum tepat.",
        explanation=item.answer_key.explanation,
        next_step="Telusuri kembali kode baris demi baris, lalu coba jawaban lain.",
    )


def grade(item: Item, chosen: str) -> tuple[bool, Feedback]:
    """Menilai satu jawaban.

    Pilihan ganda benar bila huruf pilihan atau teksnya sama
    dengan kunci. Isian rumpang benar bila teksnya ada di
    accepted_answers (perbandingan tidak peka huruf besar
    dan spasi berlebih). Mengembalikan (benar, umpan balik).
    """
    jawaban = chosen.strip()
    if item.item_format.value == "mcq":
        kunci = item.answer_key
        if kunci.option_id is not None and jawaban.upper() == kunci.option_id.upper():
            return True, _umpan_balik_benar(item)
        if _norm(jawaban) == _norm(kunci.text):
            return True, _umpan_balik_benar(item)
        for pengecoh in item.distractors:
            if pengecoh.option_id is not None and jawaban.upper() == pengecoh.option_id.upper():
                return False, pengecoh.feedback
            if _norm(jawaban) == _norm(pengecoh.text):
                return False, pengecoh.feedback
        return False, _umpan_balik_umum(item)

    diterima = [_norm(jawaban) for jawaban in item.accepted_answers]
    if _norm(jawaban) in diterima:
        return True, _umpan_balik_benar(item)
    for pengecoh in item.distractors:
        if _norm(jawaban) == _norm(pengecoh.text):
            return False, pengecoh.feedback
    return False, _umpan_balik_umum(item)
