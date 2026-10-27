<div align="center">

# AQG-DDP

### Automated Question Generation dan Distraktor Cerdas untuk Dasar-Dasar Programming

Purwarupa pembangkit soal Python yang ter-grounding ketat pada modul dosen, dengan distraktor berbasis miskonsepsi dan umpan balik formatif berbahasa Indonesia.

![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python&logoColor=white)
![Status](https://img.shields.io/badge/Status-Prototype-orange)
![LLM](https://img.shields.io/badge/LLM-Replay%20only-lightgrey)

</div>

---

##  Daftar Isi

- [Tentang](#-tentang)
- [Fitur Utama](#-fitur-utama)
- [Teknologi](#️-teknologi)
- [Angka yang Dikunci](#-angka-yang-dikunci)
- [Memulai](#-memulai)
- [Penggunaan](#-penggunaan)
- [API (Fase 3)](#-api-fase-3)
- [Frontend (Fase 4)](#️-frontend-fase-4)
- [Struktur Proyek](#-struktur-proyek)
- [Pengujian](#-pengujian)
- [Dokumentasi](#-dokumentasi)
- [Roadmap](#️-roadmap)
- [Peringatan Penting](#️-peringatan-penting)
- [Lisensi](#-lisensi)

---

##  Tentang

AQG-DDP adalah purwarupa untuk mata kuliah Dasar-Dasar Programming (DDP). Dosen mengunggah modul Python, purwarupa mengambil potongan materi yang relevan, merencanakan soal, lalu menghasilkan kandidat soal yang harus lolos serangkaian validator sebelum bisa dipakai. Dosen mengkurasi soal di Teacher Dashboard (Approve, Edit, Regenerate, Reject, Publish), dan mahasiswa mengerjakan kuis yang sudah terbit di Student View dengan umpan balik tiga bagian dalam Bahasa Indonesia: dugaan pemikiran siswa, penjelasan aturan Python yang sebenarnya, dan langkah perbaikan yang konkret.

Purwarupa ini **tidak memakai LLM live**. Di versi 1, kandidat soal dibaca dari berkas JSON yang sudah ditulis sebelumnya melalui adapter replay, supaya seluruh alur, validator, dan orchestrator bisa diuji secara deterministik dan offline. Adapter LLM live dapat diganti belakangan tanpa mengubah orchestrator, selama ia mengembalikan daftar kandidat dengan bentuk yang sama.

Modul demo yang dipakai adalah modul sintetis Topik 04 (perulangan dan pengindeksan) dan Topik 05 (percabangan), yang diberi label sintetis secara eksplisit di dalam teksnya.

##  Fitur Utama

| Fitur | Keterangan |
|---|---|
| Grounding ketat ke modul | Soal hanya disusun dari potongan modul yang terambil; materi di luar modul tidak dipakai. |
| Pembaca PDF | Modul PDF teks maksimal 10 halaman dan 5 MB; PDF hasil pindai berupa gambar ditolak. |
| Pemotong teks | Potongan maksimal 400 token, tidak pernah memotong di tengah baris, satu potongan hanya berisi satu bagian materi, dan blok kode dijaga utuh. |
| Retriever TF-IDF | Pengambilan potongan memakai TF-IDF + cosine similarity (scikit-learn), deterministik dan offline. |
| Coverage Planner | Keluaran Planner memuat heading dan konstruksi kode yang tercakup dari potongan terambil. |
| Validator berurutan | Schema, AST, linter PEP 8, sandbox eksekusi, dan keunikan isian rumpang, berhenti di kegagalan pertama. |
| Gerbang skor | Bila potongan teratas berskor 0, materi dinyatakan tidak cukup (`insufficient_context`) tanpa mencoba kandidat apa pun. |
| Adapter replay | Kandidat dibaca dari berkas JSON, termasuk 6 kandidat yang sengaja gagal supaya validator terbukti menolaknya. |
| Orchestrator | Menjalankan alur ambil, rencanakan, coba, dan validasi, lengkap dengan jejak percobaan (`attempts`). |
| Kurasi dosen | Alur status draft ke approved ke published, rejected final; edit divalidasi ulang dan kembali ke draft. |
| Kuis siswa | Sesi anonim berbasis UUID, soal terbit tanpa kunci dan umpan balik, penilaian langsung dengan umpan balik tiga bagian, dan rekap sesi. |
| Teacher Dashboard | Split-pane: PDF modul dan potongan teks di kiri, kartu soal di kanan, dengan penyorotan potongan sumber. |

##  Teknologi

| Teknologi | Kegunaan |
|---|---|
| Python 3.13 | Bahasa aplikasi dan kotak pasir (3.14 dapat dipakai bila semua wheel terpasang). |
| FastAPI | Kerangka API dan penyajian frontend. |
| Pydantic v2 | Skema data dan validasi bentuk butir soal. |
| tiktoken (`cl100k_base`) | Penghitung token untuk anggaran prompt dan potongan. |
| pypdf | Pembaca PDF modul. |
| scikit-learn | Retriever TF-IDF + cosine similarity. |
| pycodestyle | Linter PEP 8 untuk gaya kode soal. |
| sqlite3 (bawaan Python) | Penyimpanan lokal butir soal dan jejak jawaban. |
| HTML, CSS, JavaScript vanila | Frontend tanpa build dan tanpa aset luar. |
| pytest | Pengujian otomatis. |
| reportlab | Pembuat PDF modul demo (hanya untuk pengembangan). |

##  Angka yang Dikunci

Angka-angka ini adalah kontrak. Sumber kebenaran di kode adalah `app/config.py` (angka) dan `app/schemas.py` (bentuk data). Mengubah angka di sini berarti mengubah kontrak.

| Hal | Nilai |
|---|---|
| Versi Python aplikasi dan kotak pasir | 3.13 |
| Penghitung token | tiktoken `cl100k_base` |
| Ukuran potongan teks | Maksimal 400 token |
| Tumpang tindih potongan | 0 token |
| Potongan yang diambil (top-k) | 3 |
| Konteks terambil maksimal | 1.200 token |
| Prompt maksimal | 600 token (prompt sistem maksimal 520 + cadangan tugas 80) |
| Total per panggilan | 1.800 token |
| Batas modul PDF | 10 halaman, 5 MB |
| Panjang baris kode | Maksimal 79 karakter (PEP 8) |
| Kotak pasir | Timeout 2 detik, keluaran maksimal 10.000 byte |

Penyimpanan memakai SQLite lokal, berkas `data/aqg.db`, yang diabaikan git (pola `*.db` di `.gitignore`).

##  Cara Memulai

### Prasyarat

- Python 3.13 (jalankan `py -3.13 --version` di Windows; bila tidak ada, pakai Python 3.14 dengan perintah yang sama).
- Git.
- PowerShell di Windows, atau terminal bash di Linux/Mac.

### Instalasi

Windows (PowerShell, dari folder proyek):

```bat
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

Linux atau Mac:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

Folder `.venv` tidak ikut di-commit dan tidak perlu dikirim; ia dibuat ulang dengan perintah di atas bila terhapus. Jangan mengubah batas token tanpa mengukur ulang dengan `app/pipeline/tokens.py`.

## ▶ Penggunaan

Jalankan pengujian:

```bat
pytest
```

Lihat hasil pemotongan modul demo:

```bat
python tools\lihat_potongan.py
```

Hitung token prompt sistem:

```bat
python tools\hitung_prompt.py
```

Periksa PDF modul demo (jumlah halaman dan indentasi kode):

```bat
python tools\periksa_pdf.py
```

Jalankan server:

```bat
uvicorn app.main:app --reload
```

Lalu buka di browser:

```
http://127.0.0.1:8000/
```

Health check ada di:

```
http://127.0.0.1:8000/api/health
```

Respons yang diharapkan:

```json
{"status": "ok", "version": "0.4.0-phase4", "language": "Python 3.10+", "python_target": "3.13", "tokenizer": "cl100k_base", "mode": "replay"}
```

Sebelum demo, hapus `data/aqg.db` bila ada, supaya database mulai dari keadaan kosong. Berkas itu dibuat ulang otomatis saat server berjalan dan tidak ikut di-commit.

##  API (Fase 3)

Penyimpanan memakai SQLite lokal (`data/aqg.db`, diabaikan git). Modul hasil upload hanya hidup selama server berjalan; restart kembali ke modul demo.

| Route | Kegunaan |
|---|---|
| `POST /api/modules` | Upload modul PDF (maks 10 halaman, 5 MB) |
| `GET /api/modules` | Keterangan modul aktif beserta daftar potongan |
| `GET /api/modules/file` | Isi PDF modul aktif untuk panel PDF |
| `POST /api/generate` | Generate kandidat, simpan sebagai draft |
| `GET /api/items`, `GET /api/items/{id}` | Lihat butir tersimpan |
| `PUT /api/items/{id}` | Edit (divalidasi ulang, kembali ke draft) |
| `POST /api/items/{id}/approve`, `/reject`, `/publish`, `/regenerate` | Kurasi |
| `POST /api/quiz/session` | Terbitkan UUID sesi anonim |
| `GET /api/quiz` | Soal terbit tanpa kunci dan umpan balik |
| `POST /api/quiz/answer` | Jawab dan terima umpan balik tiga bagian |
| `GET /api/quiz/summary` | Rekap sesi |

Galat dijawab tanpa traceback mentah: 404 bila tidak ditemukan, 409 bila transisi status tidak sah, 422 bila validator atau UUID sesi tidak sah, dan 500 dengan pesan umum bila galat tak terduga.

##  Frontend (Fase 4)

Jalankan server dengan `uvicorn app.main:app --reload`, lalu buka `http://127.0.0.1:8000/` di browser. Teacher Dashboard ada di `#/dosen` (upload modul, generate, kurasi, panel PDF dan potongan), Student View ada di `#/siswa` (satu soal per layar, umpan balik langsung, rekap sesi). Frontend memakai HTML, CSS, dan JavaScript vanila tanpa build, dan semua teks dari server ditampilkan dengan aman tanpa HTML mentah. Status soal selalu memakai teks dan ikon, bukan warna saja, dan semua pasangan warna memenuhi kontras minimal 4,5:1.

## 📁 Struktur Proyek

```
aqg-pbk/
├── app/
│   ├── main.py                  # Titik masuk FastAPI + penyajian frontend
│   ├── api.py                   # Route Fase 3 (modul, kurasi, kuis)
│   ├── config.py                # Angka yang dikunci
│   ├── errors.py                # Jenis galat khusus aplikasi
│   ├── quiz.py                  # Penilaian dan umpan balik siswa
│   ├── schemas.py               # Skema Pydantic: Item, Planner, ValidationReport, API
│   ├── storage.py               # Penyimpanan SQLite
│   ├── static/                  # Frontend vanila (index.html, style.css, app.js)
│   ├── pipeline/
│   │   ├── tokens.py            # Penghitung token dan anggaran token
│   │   ├── ingest.py            # Pembaca PDF modul
│   │   ├── chunker.py           # Pemotong teks per bagian dan blok kode
│   │   ├── retriever.py         # Retriever TF-IDF + cosine
│   │   ├── coverage.py          # Coverage Planner dari potongan terambil
│   │   ├── planner.py           # PlannerOutput (ok / insufficient_context)
│   │   ├── module_store.py      # Modul aktif (demo atau hasil upload)
│   │   ├── orchestrator.py      # Alur ambil, rencanakan, coba, validasi
│   │   └── validators/          # schema, ast, lint, sandbox, fill_blank, validate_item
│   └── llm/
│       ├── base.py              # Antarmuka sumber kandidat
│       └── replay.py            # Adapter replay dari berkas JSON
├── data/
│   ├── modules/                 # Modul demo sintetis (txt + pdf)
│   ├── prompts/                 # Prompt sistem dan skema JSON
│   ├── misconceptions/          # Katalog jenis miskonsepsi
│   └── replay/                  # Kandidat replay (2 bagus, 6 sengaja gagal)
├── docs/
│   ├── DATA_CONTRACT.md         # Kontrak data dan angka yang dikunci
│   ├── DEVIATIONS.md            # Penyimpangan dari proposal yang dicatat
│   └── DEMO_SCRIPT.md           # Naskah demo 6 menit
├── tests/                       # Pengujian otomatis (lihat tabel di bawah)
├── tools/                       # Pembuat dan pemeriksa PDF demo, penghitung prompt
├── requirements.txt             # Dependensi aplikasi
├── requirements-dev.txt         # Dependensi aplikasi + pengembangan
└── pytest.ini                   # Konfigurasi pytest
```

##  Pengujian

100 pengujian, terakhir diukur 27 Oktober 2026 (95 sebelum Fase 4, ditambah 5 pengujian frontend).

| Area | Berkas pengujian | Jumlah |
|---|---|---|
| Skema data | `test_schemas.py` | 14 |
| Pemotong teks | `test_chunker.py` | 11 |
| Validator | `test_validators.py` | 9 |
| Token | `test_token.py` | 7 |
| Coverage | `test_coverage.py` | 7 |
| Retriever | `test_retriever.py` | 12 |
| Pembaca PDF | `test_ingest.py` | 5 |
| Orchestrator | `test_orchestrator.py` | 5 |
| Sandbox | `test_sandbox.py` | 4 |
| Prompt | `test_prompt.py` | 3 |
| Kontrak dokumen | `test_contract_doc.py` | 3 |
| Isian rumpang | `test_fill_blank.py` | 3 |
| Health check | `test_api_health.py` | 1 |
| API | `test_api.py` | 11 |
| Frontend | `test_frontend.py` | 5 |
| **Total** | | **100** |

Hasil yang diharapkan dari `pytest` adalah `100 passed`. Pengujian orchestrator membuktikan penolakan yang tepat: `BAD-SCHEMA-01` ditolak schema, `BAD-AST-01` ditolak ast, `BAD-KEY-01` ditolak sandbox, `BAD-DUPLICATE-01` ditolak schema, `BAD-LINT-01` ditolak lint, dan `BAD-FILL-01` ditolak fill_blank, sementara `MCQ-01` dan `FIB-01` diterima.

## 📚 Dokumentasi

- `docs/DATA_CONTRACT.md`: bentuk data setiap model, angka yang dikunci, contoh soal yang dikunci, dan catatan terbuka.
- `docs/DEVIATIONS.md`: setiap perbedaan antara proposal dan purwarupa, termasuk desain prompt, tumpang tindih 0 token, retriever TF-IDF, gerbang skor, sandbox subprocess, penyimpanan SQLite, modul upload di memori, dan frontend vanila.
- `docs/DEMO_SCRIPT.md`: naskah demo 6 menit beserta persiapan dan kalimat kejujuran yang harus diucapkan.
- Dokumen proposal proyek (di luar repo ini): `Proposal_Project_AQG_DDP.docx`, mata kuliah Pengajaran Berbantuan Komputer (PBK).

##  Roadmap

- [x] **Fase 1**: Kerangka dan kontrak data.
- [x] **Fase 2A**: Ingest, chunking, retriever, dan coverage.
- [x] **Fase 2B**: Validator, adapter replay, dan orchestrator.
- [x] **Fase 3**: API dan penyimpanan (Teacher Dashboard API, kurasi, dan publish).
- [x] **Fase 4**: Frontend Teacher Dashboard dan Student View.
- [ ] **Fase 5**: Integrasi dan penguatan demo (dokumen final, naskah demo, verifikasi clean checkout, tag per fase).

## ⚠️ Peringatan Penting

- **Sandbox bukan batas keamanan.** Sandbox di sini adalah subprocess biasa dengan batas waktu dan keluaran yang dibatasi, tanpa Docker di Windows. Cara ini hanya diterima karena versi 1 menjalankan kode replay yang sudah ditulis sebelumnya, bukan kode dari pengguna yang tidak dikenal.
- **Bukan LLM live.** Semua kandidat pada versi ini berasal dari berkas replay. Jangan mengklaim hasil, waktu, atau skor apa pun sebagai hasil model bahasa.
- **Hitungan token adalah perkiraan.** `cl100k_base` adalah perkiraan untuk model selain OpenAI; angka token di sini adalah angka terukur dengan tokenizer itu, bukan angka pasti untuk semua model.
- **Modul hasil upload hanya di memori.** Upload mengganti potongan aktif selama server berjalan dan berkasnya tidak ditulis permanen. Restart server kembali ke modul demo.
- **Label isian rumpang masih terbuka.** Skema memakai `syntax_error` untuk `if` terpisah (subtipe `independent-if`) padahal programnya berjalan. Keraguan ini dicatat di `docs/DATA_CONTRACT.md` bagian 9 dan belum diputuskan.

## 📄 Lisensi

Belum ada lisensi. Proyek tugas mata kuliah Pengajaran Berbantuan Komputer (PBK).
