/* Frontend AQG-DDP: JavaScript vanila, tanpa framework.
   Semua teks dari server ditampilkan lewat textContent,
   tidak pernah ditempel sebagai HTML mentah. Routing
   memakai hash: #/dosen dan #/siswa. */
"use strict";

function $(id) {
  return document.getElementById(id);
}

function buatElemen(tag, isi, kelas) {
  const el = document.createElement(tag);
  if (kelas) {
    el.className = kelas;
  }
  if (isi !== undefined && isi !== null) {
    el.textContent = isi;
  }
  return el;
}

const pesanEl = $("pesan");

function tampilPesan(teks) {
  pesanEl.textContent = teks;
}

async function bacaGalat(respons) {
  try {
    const data = await respons.json();
    const detail = data.detail;
    if (typeof detail === "string") {
      return detail;
    }
    if (detail && typeof detail.message === "string") {
      return detail.message;
    }
    return "Respons " + respons.status;
  } catch (galat) {
    return "Respons " + respons.status;
  }
}

async function api(path, opsi) {
  const respons = await fetch(path, opsi);
  if (!respons.ok) {
    throw new Error(await bacaGalat(respons));
  }
  return respons.json();
}

function apiJson(path, metode, badan) {
  return api(path, {
    method: metode,
    headers: { "Content-Type": "application/json" },
    body: badan === undefined ? undefined : JSON.stringify(badan),
  });
}

/* --- Routing hash --- */

function tampilkanBerdasarkanHash() {
  const keSiswa = location.hash === "#/siswa";
  $("tampilan-dosen").hidden = keSiswa;
  $("tampilan-siswa").hidden = !keSiswa;
  const tautanDosen = $("tautan-dosen");
  const tautanSiswa = $("tautan-siswa");
  if (keSiswa) {
    tautanSiswa.setAttribute("aria-current", "page");
    tautanDosen.removeAttribute("aria-current");
    muatKuis();
  } else {
    tautanDosen.setAttribute("aria-current", "page");
    tautanSiswa.removeAttribute("aria-current");
    muatModul();
    muatItems();
  }
}

window.addEventListener("hashchange", tampilkanBerdasarkanHash);

/* --- Teacher Dashboard --- */

let itemTersimpan = [];
let itemSedangDiedit = null;

const LABEL_STATUS = {
  draft: "● Draft",
  approved: "✓ Disetujui",
  published: "★ Terbit",
  rejected: "✗ Ditolak",
};

function sorotPotongan(chunkId) {
  document.querySelectorAll(".potongan-sorot").forEach((el) => {
    el.classList.remove("potongan-sorot");
  });
  const target = document.getElementById("potongan-" + chunkId);
  if (target) {
    target.classList.add("potongan-sorot");
    target.scrollIntoView({ behavior: "smooth", block: "center" });
  }
}

async function muatModul() {
  try {
    const info = await api("/api/modules");
    $("info-modul").textContent =
      "Modul aktif: " +
      info.filename +
      " (" +
      info.pages +
      " halaman, " +
      info.chunks +
      " potongan, id " +
      info.module_id +
      ")";
    const wadah = $("daftar-potongan");
    wadah.replaceChildren();
    (info.potongan || []).forEach((potongan) => {
      const artikel = buatElemen("article", undefined, "potongan");
      artikel.id = "potongan-" + potongan.chunk_id;
      artikel.appendChild(
        buatElemen(
          "h4",
          potongan.heading + " (" + potongan.chunk_id + ", halaman " + potongan.page + ")"
        )
      );
      artikel.appendChild(buatElemen("pre", potongan.text));
      wadah.appendChild(artikel);
    });
  } catch (galat) {
    tampilPesan("Gagal memuat modul: " + galat.message);
  }
}

function kartuItem(tersimpan) {
  const item = tersimpan.item;
  const artikel = buatElemen("article", undefined, "kartu");
  const kepala = buatElemen("div");
  const lencana = buatElemen(
    "span",
    LABEL_STATUS[tersimpan.status] || tersimpan.status,
    "lencana status-" + tersimpan.status
  );
  kepala.appendChild(lencana);
  kepala.appendChild(
    buatElemen("strong", item.item_id + " · " + item.item_format + " · " + item.topic)
  );
  artikel.appendChild(kepala);
  artikel.appendChild(buatElemen("p", item.stem));
  if (item.code) {
    artikel.appendChild(buatElemen("pre", item.code));
  }
  const kunci = item.answer_key;
  artikel.appendChild(
    buatElemen(
      "p",
      "Kunci: " +
        (kunci.option_id ? kunci.option_id + " " : "") +
        kunci.text +
        " — " +
        kunci.explanation
    )
  );
  const daftar = document.createElement("ul");
  item.distractors.forEach((pengecoh) => {
    const baris =
      (pengecoh.option_id ? pengecoh.option_id + ". " : "") +
      pengecoh.text +
      " — " +
      pengecoh.misconception_type +
      (pengecoh.misconception_note ? " (" + pengecoh.misconception_note + ")" : "");
    daftar.appendChild(buatElemen("li", baris));
  });
  artikel.appendChild(daftar);
  const pil = buatElemen("button", "Sumber: " + item.source_chunk_id, "pil-sumber");
  pil.type = "button";
  pil.dataset.chunkId = item.source_chunk_id;
  artikel.appendChild(pil);

  const aksi = buatElemen("div", undefined, "aksi-kartu");
  [
    ["approve", "Approve"],
    ["reject", "Reject"],
    ["publish", "Publish"],
    ["regenerate", "Regenerate"],
    ["edit", "Edit"],
  ].forEach(([nama, label]) => {
    const tombol = buatElemen("button", label);
    tombol.type = "button";
    tombol.dataset.aksi = nama;
    tombol.dataset.id = item.item_id;
    aksi.appendChild(tombol);
  });
  artikel.appendChild(aksi);
  return artikel;
}

async function muatItems() {
  try {
    const status = $("saring-status").value;
    const path = status ? "/api/items?status=" + status : "/api/items";
    itemTersimpan = await api(path);
    const wadah = $("daftar-item");
    wadah.replaceChildren();
    if (itemTersimpan.length === 0) {
      wadah.appendChild(
        buatElemen("p", "Belum ada butir soal. Jalankan generate di atas.", "keterangan")
      );
      return;
    }
    itemTersimpan.forEach((tersimpan) => {
      wadah.appendChild(kartuItem(tersimpan));
    });
  } catch (galat) {
    tampilPesan("Gagal memuat butir soal: " + galat.message);
  }
}

$("daftar-item").addEventListener("click", async (acara) => {
  const pil = acara.target.closest(".pil-sumber");
  if (pil) {
    sorotPotongan(pil.dataset.chunkId);
    return;
  }
  const tombol = acara.target.closest("button[data-aksi]");
  if (!tombol) {
    return;
  }
  const id = tombol.dataset.id;
  const aksi = tombol.dataset.aksi;
  if (aksi === "edit") {
    bukaEdit(id);
    return;
  }
  try {
    await apiJson("/api/items/" + id + "/" + aksi, "POST", {});
    tampilPesan("Tindakan " + aksi + " untuk " + id + " berhasil.");
    await muatItems();
  } catch (galat) {
    tampilPesan("Gagal " + aksi + " " + id + ": " + galat.message);
  }
});

$("saring-status").addEventListener("change", muatItems);

$("form-upload").addEventListener("submit", async (acara) => {
  acara.preventDefault();
  const data = new FormData(acara.target);
  try {
    const hasil = await api("/api/modules", { method: "POST", body: data });
    tampilPesan(
      "Upload berhasil: " + hasil.filename + " (" + hasil.chunks + " potongan)."
    );
    $("pdf-modul").src = "/api/modules/file?t=" + Date.now();
    await muatModul();
  } catch (galat) {
    tampilPesan("Gagal upload: " + galat.message);
  }
});

$("form-generate").addEventListener("submit", async (acara) => {
  acara.preventDefault();
  const konsep = $("input-konsep")
    .value.split(",")
    .map((s) => s.trim())
    .filter((s) => s.length > 0);
  const badan = {
    topic: $("input-topik").value.trim(),
    query: $("input-query").value.trim(),
    key_concepts: konsep,
    limit: Math.min(10, Math.max(1, parseInt($("input-batas").value, 10) || 2)),
  };
  try {
    const hasil = await apiJson("/api/generate", "POST", badan);
    tampilPesan(
      "Generate selesai: " +
        hasil.items.length +
        " diterima, " +
        hasil.rejected.length +
        " ditolak."
    );
    await muatItems();
  } catch (galat) {
    tampilPesan("Gagal generate: " + galat.message);
  }
});

/* --- Edit butir --- */

function bukaEdit(itemId) {
  const tersimpan = itemTersimpan.find((t) => t.item.item_id === itemId);
  if (!tersimpan) {
    return;
  }
  itemSedangDiedit = JSON.parse(JSON.stringify(tersimpan.item));
  const item = itemSedangDiedit;
  $("edit-judul").textContent = "Edit butir soal " + item.item_id;
  $("edit-stem").value = item.stem;
  $("edit-kode").value = item.code || "";
  $("edit-kunci").value = item.answer_key.text;
  $("edit-penjelasan-kunci").value = item.answer_key.explanation;
  $("edit-diterima").value = (item.accepted_answers || []).join(", ");
  const wadah = $("edit-pengecoh");
  wadah.replaceChildren();
  item.distractors.forEach((pengecoh, indeks) => {
    const judul = buatElemen(
      "p",
      "Pengecoh " + (pengecoh.option_id || indeks + 1) + " (" + pengecoh.misconception_type + ")"
    );
    wadah.appendChild(judul);
    const labelTeks = buatElemen("label", "Teks pengecoh");
    const inputTeks = document.createElement("input");
    inputTeks.type = "text";
    inputTeks.required = true;
    inputTeks.value = pengecoh.text;
    inputTeks.className = "edit-pengecoh-teks";
    labelTeks.appendChild(inputTeks);
    wadah.appendChild(labelTeks);
    const labelCatatan = buatElemen("label", "Catatan miskonsepsi (wajib bila tipe other)");
    const inputCatatan = document.createElement("input");
    inputCatatan.type = "text";
    inputCatatan.value = pengecoh.misconception_note || "";
    inputCatatan.className = "edit-pengecoh-catatan";
    labelCatatan.appendChild(inputCatatan);
    wadah.appendChild(labelCatatan);
  });
  $("form-edit").hidden = false;
  $("form-edit").scrollIntoView({ behavior: "smooth", block: "start" });
  $("edit-stem").focus();
}

$("tombol-batal-edit").addEventListener("click", () => {
  itemSedangDiedit = null;
  $("form-edit").hidden = true;
});

$("form-edit-isi").addEventListener("submit", async (acara) => {
  acara.preventDefault();
  if (!itemSedangDiedit) {
    return;
  }
  const item = JSON.parse(JSON.stringify(itemSedangDiedit));
  item.stem = $("edit-stem").value;
  const kode = $("edit-kode").value.trim();
  item.code = kode.length > 0 ? $("edit-kode").value : null;
  item.answer_key.text = $("edit-kunci").value;
  item.answer_key.explanation = $("edit-penjelasan-kunci").value;
  if (item.item_format === "fill_in_blank") {
    item.accepted_answers = $("edit-diterima")
      .value.split(",")
      .map((s) => s.trim())
      .filter((s) => s.length > 0);
  }
  const teksPengecoh = wadahPengecoh("edit-pengecoh-teks");
  const catatanPengecoh = wadahPengecoh("edit-pengecoh-catatan");
  item.distractors.forEach((pengecoh, indeks) => {
    pengecoh.text = teksPengecoh[indeks].value;
    const catatan = catatanPengecoh[indeks].value.trim();
    pengecoh.misconception_note = catatan.length > 0 ? catatan : null;
  });
  try {
    const respons = await fetch("/api/items/" + item.item_id, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(item),
    });
    if (!respons.ok) {
      const data = await respons.json().catch(() => null);
      const laporan = data && data.detail && data.detail.report;
      if (laporan) {
        const gagal = laporan.results
          .filter((r) => !r.passed)
          .map((r) => r.name)
          .join(", ");
        throw new Error("Edit tidak lolos validator: " + gagal + ".");
      }
      throw new Error(await bacaGalatDariData(data, respons.status));
    }
    tampilPesan("Edit " + item.item_id + " tersimpan dan kembali ke draft.");
    itemSedangDiedit = null;
    $("form-edit").hidden = true;
    await muatItems();
  } catch (galat) {
    tampilPesan("Gagal menyimpan edit: " + galat.message);
  }
});

function wadahPengecoh(kelas) {
  return Array.from(document.querySelectorAll("." + kelas));
}

async function bacaGalatDariData(data, status) {
  if (data && typeof data.detail === "string") {
    return data.detail;
  }
  return "Respons " + status;
}

/* --- Student View --- */

let sesiId = sessionStorage.getItem("aqg-sesi");
let kuis = [];
let indeksSoal = 0;
let sudahDijawab = false;

async function muatKuis() {
  try {
    if (!sesiId) {
      const sesi = await apiJson("/api/quiz/session", "POST", {});
      sesiId = sesi.session_id;
      sessionStorage.setItem("aqg-sesi", sesiId);
    }
    kuis = await api("/api/quiz");
    $("rekap").hidden = true;
    if (kuis.length === 0) {
      $("kuis-kosong").hidden = false;
      $("kartu-soal").hidden = true;
      return;
    }
    $("kuis-kosong").hidden = true;
    if (indeksSoal >= kuis.length) {
      indeksSoal = 0;
    }
    tampilkanSoal(indeksSoal);
  } catch (galat) {
    tampilPesan("Gagal memuat kuis: " + galat.message);
  }
}

function tampilkanKode(kode) {
  const wadah = $("soal-kode");
  wadah.replaceChildren();
  if (!kode) {
    wadah.hidden = true;
    return;
  }
  wadah.hidden = false;
  kode.split("\n").forEach((baris, i) => {
    const div = buatElemen("div", undefined, "baris-kode");
    div.appendChild(buatElemen("span", String(i + 1), "nomor"));
    div.appendChild(buatElemen("span", baris.length > 0 ? baris : " "));
    wadah.appendChild(div);
  });
}

function tampilkanSoal(indeks) {
  indeksSoal = indeks;
  sudahDijawab = false;
  const soal = kuis[indeks];
  $("soal-nomor").textContent =
    "Soal " + (indeks + 1) + " dari " + kuis.length + " · " + soal.topic;
  $("soal-stem").textContent = soal.stem;
  tampilkanKode(soal.code);
  $("umpan-balik").hidden = true;
  $("umpan-balik").className = "umpan-balik";
  $("tombol-coba-lagi").hidden = true;
  $("tombol-berikutnya").hidden = true;
  $("kartu-soal").hidden = false;
  $("rekap").hidden = true;

  const wadahPilihan = $("soal-pilihan");
  wadahPilihan.replaceChildren();
  const wadahIsian = $("soal-isian");
  if (soal.item_format === "mcq") {
    wadahIsian.hidden = true;
    soal.distractors.forEach((pilihan) => {
      const tombol = buatElemen(
        "button",
        (pilihan.option_id ? pilihan.option_id + ". " : "") + pilihan.text
      );
      tombol.type = "button";
      tombol.dataset.pilihan = pilihan.option_id || pilihan.text;
      tombol.addEventListener("click", () => jawab(pilihan.option_id || pilihan.text));
      wadahPilihan.appendChild(tombol);
    });
  } else {
    wadahIsian.hidden = false;
    $("jawaban-isian").value = "";
    $("jawaban-isian").focus();
  }
}

async function jawab(pilihan) {
  if (sudahDijawab) {
    return;
  }
  const soal = kuis[indeksSoal];
  try {
    const hasil = await apiJson("/api/quiz/answer", "POST", {
      session_id: sesiId,
      item_id: soal.item_id,
      chosen: pilihan,
    });
    sudahDijawab = true;
    document.querySelectorAll("#soal-pilihan button").forEach((tombol) => {
      tombol.disabled = true;
      if (tombol.dataset.pilihan === pilihan) {
        tombol.classList.add("pilihan-dipilih");
      }
    });
    const umpan = $("umpan-balik");
    umpan.hidden = false;
    umpan.className = "umpan-balik " + (hasil.correct ? "benar" : "salah");
    $("umpan-status").textContent = hasil.correct
      ? "✓ Benar"
      : "✗ Belum tepat";
    $("umpan-diagnosis").textContent = hasil.feedback.diagnosis;
    $("umpan-penjelasan").textContent = hasil.feedback.explanation;
    $("umpan-langkah").textContent = hasil.feedback.next_step;
    $("umpan-keluaran").textContent = hasil.expected_output
      ? "Keluaran yang benar: " + hasil.expected_output
      : "";
    $("tombol-coba-lagi").hidden = false;
    const tombolBerikutnya = $("tombol-berikutnya");
    tombolBerikutnya.hidden = false;
    tombolBerikutnya.textContent =
      indeksSoal + 1 < kuis.length ? "Soal berikutnya" : "Lihat rekap";
  } catch (galat) {
    tampilPesan("Gagal menjawab: " + galat.message);
  }
}

$("tombol-jawab-isian").addEventListener("click", () => {
  const jawaban = $("jawaban-isian").value.trim();
  if (jawaban.length === 0) {
    $("jawaban-isian").focus();
    return;
  }
  jawab(jawaban);
});

$("jawaban-isian").addEventListener("keydown", (acara) => {
  if (acara.key === "Enter") {
    acara.preventDefault();
    $("tombol-jawab-isian").click();
  }
});

$("tombol-coba-lagi").addEventListener("click", () => {
  tampilkanSoal(indeksSoal);
});

$("tombol-berikutnya").addEventListener("click", () => {
  if (indeksSoal + 1 < kuis.length) {
    tampilkanSoal(indeksSoal + 1);
  } else {
    tampilkanRekap();
  }
});

async function tampilkanRekap() {
  $("kartu-soal").hidden = true;
  try {
    const rekap = await api(
      "/api/quiz/summary?session_id=" + encodeURIComponent(sesiId)
    );
    $("rekap-teks").textContent =
      "Kamu menjawab " +
      rekap.correct +
      " benar dari " +
      rekap.total +
      " jawaban.";
    const daftar = $("rekap-daftar");
    daftar.replaceChildren();
    rekap.answers.forEach((jawaban) => {
      daftar.appendChild(
        buatElemen(
          "li",
          jawaban.item_id +
            ": " +
            jawaban.chosen +
            " — " +
            (jawaban.correct ? "Benar" : "Belum tepat")
        )
      );
    });
    $("rekap").hidden = false;
  } catch (galat) {
    tampilPesan("Gagal memuat rekap: " + galat.message);
  }
}

$("tombol-ulangi").addEventListener("click", () => {
  sesiId = null;
  sessionStorage.removeItem("aqg-sesi");
  indeksSoal = 0;
  muatKuis();
});

tampilkanBerdasarkanHash();
