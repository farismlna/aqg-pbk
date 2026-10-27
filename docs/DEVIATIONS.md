# Penyimpangan yang Dicatat (DEVIATIONS)

Setiap perbedaan antara proposal dan purwarupa dicatat di sini,
supaya tidak disembunyikan. Dokumen ini diperbarui pada setiap
fase kalau ada keputusan baru.

Sumber kebenaran saat ini adalah repo Faris di GitHub
(`aqg-pbk`, commit `fb1feb8`, 27 Oktober 2026) yang dibangun
bersama Claude Web. Salinan di workspace Muse adalah cerminan
dari repo itu, ditambah README, `app/main.py`, pengujian health,
katalog miskonsepsi, dan dokumen ini. Jangan membangun dari
scaffold Fase 1 Muse yang lama, karena scaffold itu memakai
API config, skema, dan lokasi token yang berbeda dan sudah
digantikan oleh repo ini.

## Sudah diputuskan

1. **Desain prompt dan batas token.** Proposal menulis batas
   1.500 token tanpa menyatakan apakah batas itu untuk konteks
   terambil saja atau untuk seluruh request. Purwarupa
   menetapkan 1.500 berlaku untuk konteks terambil saja, lalu
   memakai prompt ringkas dengan contoh JSON di dalam teksnya
   (bukan skema JSON lengkap yang dikirim terpisah). Prompt
   itu terukur 328 token, batas prompt 600 token, total
   rakitan 1.800 token. Pengukuran 1.000/2.200 token yang
   pernah dibuat Muse berlaku untuk desain prompt yang lebih
   panjang dan sudah digantikan oleh desain ini. Kedua angka
   itu tidak boleh dicampur.
2. **Tumpang tindih potongan 0 token.** Angka 50 token yang
   pernah dikunci sebelumnya digantikan oleh 0 token, karena
   pemotong teks bekerja per bagian materi dan per blok kode
   utuh, dan pengujiannya menuntut isi potongan utuh tanpa
   hilang atau ganda. `chunk_pages` menolak nilai tumpang
   tindih selain 0. Keputusan ini tercatat sebagai keputusan
   sementara di kontrak data, dan hanya boleh diubah bersama
   pengujian pemotong yang baru.
3. **Penandaan distraktor.** Proposal menuntut satu distraktor
   per tipe miskonsepsi per soal. Purwarupa menghapus aturan
   itu, mengizinkan tipe ganda dan tag `other`, supaya
   penandaan jujur. Contoh: distraktor 30 pada soal
   skor/pengali ditandai `other` dengan catatan
   partial_branch_update.
4. **Field coverage.** Keluaran Planner punya field `coverage`
   berisi heading dan konstruk kode yang tercakup, tanpa
   tampilan baru di v1. Field ini diisi dari potongan terambil
   pada Fase 2A lanjutan (app/pipeline/coverage.py).

## Belum diputuskan atau masih terbuka

5. **Label isian rumpang.** Skema memakai `syntax_error`
   untuk kedua jawaban salah isian rumpang, yaitu `if`
   terpisah (subtipe `independent-if`) dan `else if`
   (subtipe `else-if-separate`), padahal `if` terpisah itu
   berjalan dan bukan kesalahan sintaks. Kontrak data bagian
   9 sudah mencatat keraguan ini. Nama payung
   `syntax_or_structure` pernah diusulkan, tetapi belum
   diadopsi di kode yang sudah di-commit. Keputusan ini
   ditunda sampai validator isian rumpang pada Fase 2B.
6. **Retriever TF-IDF.** Proposal menulis dense embeddings +
   vector database. Purwarupa memakai TF-IDF + cosine
   (scikit-learn) di `app/pipeline/retriever.py`, karena untuk
   modul maksimal 10 halaman cara itu deterministik, offline,
   dan tidak butuh torch di Windows. Retriever hanya
   mengembalikan potongan beserta skornya; gerbang skor untuk
   materi yang tidak cukup dibuat di orchestrator Fase 2B.
7. **Sandbox subprocess.** Tanpa Docker di Windows, sandbox
   subprocess bukan batas keamanan yang sesungguhnya. Hal
   itu harus ditulis di README sebelum sandbox dipakai.
   Cara ini hanya diterima karena v1 menjalankan kode replay
   yang sudah ditulis sebelumnya. Belum diimplementasikan.
8. **Penyorotan sumber tingkat chunk.** Penyorotan di Teacher
   Dashboard direncanakan pada tingkat teks chunk, bukan
   penyorotan di dalam file PDF. Belum diimplementasikan.
9. **Validator berurutan dengan short-circuit.** Validator
   dijalankan berurutan schema, ast, lint, sandbox, lalu
   fill_blank, dan berhenti di kegagalan pertama, supaya
   kode yang sudah terbukti rusak tidak ikut dijalankan
   atau diperiksa gayanya.
10. **Gerbang skor di orchestrator.** Bila potongan teratas
    berskor 0, materi dinyatakan tidak cukup
    (`insufficient_context`) tanpa mencoba kandidat apa
    pun. Ambang ini adalah 0 persis, bukan ambang yang
    disetel (tuned).
11. **Sandbox subprocess.** Sandbox diimplementasikan pada
    Fase 2B (`app/pipeline/validators/sandbox.py`) sebagai
    subprocess dengan batas waktu 2 detik dan keluaran
    yang dibatasi, dan tetap bukan batas keamanan yang
    sesungguhnya tanpa Docker di Windows.

## Sudah diputuskan (Fase 3)

12. **Penyimpanan SQLite lokal.** Penyimpanan v1 memakai
    `sqlite3` bawaan Python dengan berkas `data/aqg.db`
    (diabaikan git), bukan database relasional kampus.
    Butir soal disimpan sebagai JSON utuh ditambah status
    kurasi, supaya skema `Item` tidak berubah.
13. **Modul hasil upload hanya di memori.** Upload
    mengganti potongan aktif selama server berjalan dan
    berkasnya tidak ditulis permanen. Restart server
    kembali ke modul demo. Keterbatasan ini disengaja
    untuk v1 dan harus dihapus bila penyimpanan modul
    permanen ditambahkan.
14. **Umpan balik jawaban benar dan jawaban tak dikenal.**
    Jawaban benar mendapat umpan balik yang dibangun dari
    `explanation` pada kunci. Jawaban salah yang tidak
    cocok dengan distraktor mana pun mendapat umpan balik
    umum yang juga memakai `explanation` kunci, bukan
    umpan balik distraktor yang salah.
15. **Generate tidak menimpa.** Generate atau regenerate
    yang menemukan `item_id` yang sudah tersimpan
    mengembalikan butir lama apa adanya, supaya kurasi
    dosen tidak hilang.
