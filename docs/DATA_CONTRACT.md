# Kontrak Data AQG-DDP (Fase 1)

Dokumen ini mencatat bentuk data dan angka yang dikunci untuk prototipe.
Sumber kebenaran di kode adalah `app/schemas.py` (bentuk data) dan
`app/config.py` (angka). Jika kontrak asli yang sudah dikunci berbeda
dari dokumen ini, perbarui dokumen ini dan kodenya bersama-sama.

## 1. Angka yang dikunci

| Hal | Nilai | Catatan |
|---|---|---|
| Versi Python (aplikasi dan kotak pasir) | 3.13 | |
| Penghitung token | cl100k_base | Perkiraan untuk model non-OpenAI |
| Ukuran potongan teks | 400 token | |
| Tumpang tindih potongan | 0 token | Keputusan sementara |
| Bagian materi minimum | 60 token | Bagian lebih pendek digabung ke bagian berikutnya |
| Jumlah potongan diambil (top-k) | 3 | |
| Maksimum potongan teks diambil | 1200 token | 3 potongan x 400 |
| Maksimum prompt | 600 token | Prompt sistem paling banyak 520 + cadangan kalimat tugas 80 |
| Total per panggilan | 1800 token | 1200 + 600 |
| Batas modul PDF | 10 halaman, 5 MB | Batas 5 MB adalah usulan |
| Panjang baris kode | 79 karakter | Aturan PEP 8 |
| Kotak pasir | 2 detik, keluaran 10000 byte | Batas waktu dan batas keluaran |

## 2. Butir soal (`Item`)

| Kolom | Wajib | Arti |
|---|---|---|
| `item_id` | ya | Nomor unik butir soal |
| `item_format` | ya | `mcq` (pilihan ganda) atau `fill_in_blank` (isian rumpang) |
| `topic` | ya | Topik materi |
| `stem` | ya | Kalimat pertanyaan |
| `code` | tergantung | Kode pada soal; wajib berisi `____` untuk isian rumpang |
| `answer_key` | ya | Kunci jawaban (bagian 3) |
| `distractors` | ya | Daftar jawaban salah (bagian 4) |
| `accepted_answers` | isian saja | Semua jawaban yang diterima; wajib memuat kunci |
| `source_chunk_id` | ya | Potongan materi sumber |
| `source_page` | ya | Halaman sumber, mulai dari 1 |

Aturan pilihan ganda: minimal 3 pengecoh, semua pilihan punya `option_id`
yang unik, dan teks semua pilihan harus berbeda (termasuk dari kunci).

Aturan isian rumpang: kode berisi `____`, `accepted_answers` memuat kunci,
dan jawaban salah tidak boleh ada di `accepted_answers`.

## 3. Kunci jawaban (`AnswerKey`)

| Kolom | Wajib | Arti |
|---|---|---|
| `option_id` | pilihan ganda | Huruf pilihan, misalnya A |
| `text` | ya | Teks jawaban benar |
| `expected_output` | tidak | Keluaran program yang benar |
| `explanation` | ya | Penjelasan mengapa benar |

## 4. Jawaban salah (`Distractor`) dan umpan balik (`Feedback`)

| Kolom | Wajib | Arti |
|---|---|---|
| `option_id` | pilihan ganda | Huruf pilihan; kosong untuk isian rumpang |
| `text` | ya | Teks jawaban salah |
| `misconception_type` | ya | Jenis kesalahan pemahaman (bagian 5) |
| `subtype` | tidak | Rincian jenis, misalnya `independent-if` |
| `misconception_note` | untuk `other` | Catatan; wajib jika jenisnya `other` |
| `mutated_code` | tidak | Kode yang menghasilkan jawaban salah ini |
| `feedback` | ya | Umpan balik tiga bagian |

Umpan balik (`Feedback`) punya tiga bagian wajib:
`diagnosis` (dugaan pemikiran siswa), `explanation` (penjelasan),
dan `next_step` (saran langkah berikutnya).

## 5. Jenis kesalahan pemahaman

Pilihan: `off_by_one`, `assignment_error`, `logic_error`, `syntax_error`,
dan `other`. Tidak ada aturan satu-tiap-jenis: satu butir soal boleh
punya dua pengecoh dengan jenis yang sama. Jenis `other` wajib disertai
`misconception_note`.

## 6. Keluaran Planner

| Kolom | Wajib | Arti |
|---|---|---|
| `topic` | ya | Topik yang direncanakan |
| `status` | ya | `ok` atau `insufficient_context` (materi tidak cukup) |
| `chunk_ids` | jika `ok` | Potongan materi yang dipakai |
| `key_concepts` | jika `ok` | Konsep kunci; harus kosong jika materi tidak cukup |
| `coverage` | ya | Cakupan materi (di bawah) |

Cakupan (`Coverage`): `headings` (judul bagian materi yang tersentuh)
dan `code_constructs` (konstruksi kode yang tersentuh, misalnya `For`).
Pada versi 1 cakupan hanya ada di data, tanpa tampilan baru.

## 7. Laporan pemeriksaan

`ValidationReport` berisi daftar `ValidatorResult` (nama, lolos atau tidak,
rincian). Laporan kosong dianggap belum lolos.

## 8. Contoh yang dikunci

Soal pilihan ganda MCQ-01 (kode: `skor = 10`, `pengali = 2`, lalu `if skor > 5:`
berisi `pengali = pengali * 2` dan `skor == skor + 5`, lalu `print(skor * pengali)`):

- Kunci A: `40`.
- B: `60`, jenis `assignment_error`.
- C: `20`, jenis `logic_error`.
- D: `30`, jenis `other` (hanya sebagian pembaruan yang dihitung).

Soal isian FIB-01: `nilai = 95`, soal meminta program hanya mencetak "A".

- Kunci: `elif` (keluaran: A).
- `if` menghasilkan A lalu B (subtipe `independent-if`).
- `else if` menyebabkan SyntaxError (subtipe `else-if-separate`).

## 9. Catatan terbuka

- Subtipe `independent-if` bertipe `syntax_error`, padahal programnya
  berjalan. Pertimbangkan nama jenis yang lebih tepat di fase berikutnya.
- Tumpang tindih potongan 0 token adalah keputusan sementara.
- Cara pengambilan potongan diputuskan di Fase 2A: TF-IDF + cosine (scikit-learn).
- Teks sebelum judul pertama (halaman judul dokumen) dibuang dari potongan
  bila modul punya judul. Baris judul topik ikut ke bagian bernomor berikutnya.
- Fase 2B: validator dijalankan berurutan schema, ast, lint, sandbox,
  fill_blank dan berhenti di kegagalan pertama. Gerbang skor orchestrator:
  skor teratas 0 berarti materi tidak cukup, tanpa mencoba kandidat.
  Kandidat replay ada 8 berkas di data/replay (2 bagus, 6 sengaja gagal).

## 10. Penyimpanan dan status kurasi (Fase 3)

Penyimpanan memakai SQLite bawaan Python, berkas
`data/aqg.db` (diabaikan git). Tabel `items` menyimpan
butir soal sebagai JSON utuh ditambah kolom status dan
laporan validator; tabel `attempts` menyimpan jejak
jawaban: UUID sesi, ID soal, jawaban yang dipilih, benar
atau salah, dan waktu. Tidak ada nama, NIM, atau data
pribadi lain.

Status kurasi: `draft`, `approved`, `published`,
`rejected`. Alurnya draft ke approved ke published;
rejected bersifat final. Edit menjalankan ulang semua
validator dan mengembalikan status ke draft. Generate
ulang tidak menimpa butir yang sudah tersimpan.

Model tambahan Fase 3: `StoredItem` (`item`, `status`,
`report`), `GenerateRequest` (`topic`, `query`,
`key_concepts`, `limit`), `RegenerateRequest` (`query`,
`key_concepts`, `limit`), `QuizItem` dan `QuizDistractor`
(versi siswa tanpa kunci dan umpan balik), `AnswerRequest`
(`session_id`, `item_id`, `chosen`), `AnswerResponse`
(`item_id`, `correct`, `feedback`, `expected_output`).

Endpoint Fase 3: `POST /api/modules` (upload PDF, batas
sama dengan pembaca PDF), `GET /api/modules`,
`POST /api/generate`, `GET /api/items`, `GET /api/items/{id}`,
`PUT /api/items/{id}`, `POST /api/items/{id}/approve`,
`/reject`, `/publish`, `/regenerate`,
`POST /api/quiz/session`, `GET /api/quiz`,
`POST /api/quiz/answer`, `GET /api/quiz/summary`.
Galat dijawab tanpa traceback mentah: 404 bila tidak
ditemukan, 409 bila transisi status tidak sah, 422 bila
validator atau UUID sesi tidak sah, 500 dengan pesan
umum bila galat tak terduga.

## 11. Frontend (Fase 4)

Frontend memakai HTML, CSS, dan JavaScript vanila dari
`app/static/`, tanpa build dan tanpa aset luar. Route `/`
mengembalikan `index.html`; routing memakai hash:
`#/dosen` untuk Teacher Dashboard dan `#/siswa` untuk
Student View. Berkas statis dilayani di `/static/`.

Route `GET /api/modules/file` mengembalikan isi PDF modul
aktif untuk panel PDF: modul demo dibaca dari disk, modul
hasil upload dikembalikan dari isi PDF yang disimpan di
memori. Respons `GET /api/modules` juga memuat daftar
`potongan` berisi `chunk_id`, `heading`, `page`, dan
`text` tiap potongan, untuk daftar potongan dan
penyorotan sumber di dashboard.

`QuizItem` untuk pilihan ganda memuat kunci sebagai salah
satu pilihan, diurutkan menurut huruf pilihan, tanpa
penanda mana yang benar dan tanpa umpan balik. Untuk
isian rumpang, kunci tidak ditampilkan.

Jumlah pengujian akhir Fase 4: 100, terakhir diukur
27 Oktober 2026 (95 sebelum Fase 4, ditambah 5 pengujian
frontend). Naskah demo ada di `docs/DEMO_SCRIPT.md`.
