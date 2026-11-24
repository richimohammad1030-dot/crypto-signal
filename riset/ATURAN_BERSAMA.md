# Aturan riset bersama · CRYPTO SWING, XAU, INTRADAY

Berlaku sejak 30 Okt 2026 (disetujui pemilik). Wajib dibaca routine riset sebelum PROSEDUR masing-masing bot.
Tujuan: riset semakin kuat dari waktu ke waktu tanpa tertipu kebetulan (overfitting) karena data yang sama dipakai berulang.

## A. Sumber ide
Setiap riset mingguan menguji **2 ide**:
1. Ide teratas berstatus `antri` di `ide.md` bot tersebut.
2. **Satu ide baru** yang bukan sekadar menggeser angka parameter juara: logika masuk/keluar baru, filter jenis baru,
   data baru, perilaku pasar yang terlihat di hasil live, dsb.
   - Ide boleh berasal dari pengamatan data/live sendiri.
   - **Literatur (paper, publikasi kuant, buku) adalah nilai tambah, tidak wajib.** Jika ada, tandai `[lit]` di ide.md dan
     cantumkan sumbernya (judul + tautan) di laporan.
   - Ide yang sudah `gagal` tidak diuji ulang kecuali ada data baru yang relevan (sebutkan datanya).
Laporan menyebut **total ide yang sudah pernah diuji** untuk bot itu (makin banyak percobaan, makin besar peluang lolos karena kebetulan).

## B. Tahap uji (berurutan; gagal di satu tahap = berhenti)
1. **Uji utama** (sesuai PROSEDUR bot): periode lama + periode baru, per tahun/kuartal, tanpa 2% trade terbaik, replay penuh.
2. **Uji signifikansi**: `python riset/signifikansi.py <juara.csv> <penantang.csv> <awal periode baru>`
   (atau `signifikansi.banding(...)` dari skrip). Syarat: **P_rasio_lebih_baik ≥ 0,90**.
   Jika 0,70-0,90 → status `perlu-data` (menjanjikan, belum meyakinkan). 0,50-0,70 DENGAN arah konsisten (R/thn dan R/DD
   tidak lebih buruk di semua jendela uji) → status `kandidat` (bagian E.3). Selain itu → `gagal`.
3. **Uji data terkunci** (hanya sekali per ide, setelah lolos tahap 1-2; **dilarang** dipakai untuk memilih/menyetel parameter):
   - Crypto swing & intraday: daftar koin **sesuai masanya** (`riset/pit.py`, data `riset/unduh_pit.py`), termasuk koin yang
     sudah delisting. Syarat: rasio R/DD penantang tidak lebih buruk dari juara pada daftar ini.
   - XAU: sejak audit 30 Okt 2026 data Dukascopy 2015 - Jan 2025 sudah dipakai memilih (2015-2021) dan menguji (2022 - Jan 2025).
     Tahap 3 XAU = konfirmasi sekali di Setra Feb 2025 - skrg (tidak lebih buruk dari juara); data benar-benar baru hanya lewat uji maju.
   Catat di log bahwa data terkunci sudah dipakai untuk ide itu.
4. **Uji maju**: ide yang lolos tahap 1-3 berstatus `uji-maju` (bukan langsung diusulkan). Setiap minggu, bandingkan penantang
   vs juara **hanya pada data baru sejak tanggal lolos**. Usulan ke pemilik baru diajukan setelah minimal **6 minggu** dan
   **jumlah trade minimal** (swing 30, intraday 60, XAU 20) dengan penantang tidak lebih buruk dari juara.
   Pemilik boleh memutuskan lebih cepat setelah membaca buktinya.

Status ide: `antri` · `disaring` (gugur di saringan cepat, E.2) · `diuji` · `kandidat` (bayangan saja, E.3) · `perlu-data` · `uji-maju` (lolos tahap 1-3, sedang diuji maju) · `lolos` (siap diusulkan) ·
`gagal` · `dipasang`.

## C. Review bulanan (tambahan)
- **Risiko gabungan swing + intraday** (dikerjakan di review bulanan INTRADAY):
  `python riset/risiko_gabungan.py <trades_swing.csv> <trades_intraday.csv> 1 1` (seluruh periode) dan dengan tanggal mulai
  2024-01-01. Laporkan korelasi harian, hari keduanya rugi, drawdown gabungan, risiko terbuka maksimum bersamaan,
  dan trade intraday di koin yang sedang dipegang swing. Jika drawdown gabungan > 30% (risiko 1% keduanya) → tandai PERINGATAN.
- **Bias koin selamat** (review bulanan CRYPTO dan INTRADAY, cukup sebulan sekali): jalankan juara dengan daftar koin sesuai
  masanya dan laporkan selisihnya terhadap daftar tetap. Angka sesuai masanya adalah **ekspektasi yang lebih jujur**.
- **Portofolio 3 bot** (review bulanan XAU): `python riset/portofolio.py swing=<csv>:1 intraday=<csv>:1 xau=<csv>:0.5`
  (CSV dari backtest_crypto.py, backtest_intraday.py, backtest_xau.py dengan data 2004-skrg). Laporkan tahun minus gabungan,
  terburuk, DD gabungan, korelasi bulanan.
- **Ide yang `uji-maju`**: laporkan perkembangannya (jumlah trade data baru, R penantang vs juara).

## D. Catatan hasil fondasi (30 Okt 2026)
- Swing, daftar tetap vs sesuai masanya (2020-Okt 2026): +93 vs +74 R/thn, avg +0,264 vs +0,208R, DD 16,3 vs 26,4R.
  2024-skrg: +72 vs +52 R/thn, DD 16,0 vs 15,3R. Strategi tetap positif setiap tahun, tetapi backtest daftar tetap
  melebih-lebihkan hasil ±20-28%.
- Kalibrasi signifikansi: intraday v1 → v2 (27 Okt) P_rasio_lebih_baik hanya 0,66 di 2024-skrg. Perbaikan dari backtest
  sering lebih tidak pasti daripada kelihatannya; itulah alasan tahap 2-4.
- XAU, data terkunci Dukascopy (2015 - Jan 2025): juara RUGI -0,061R/trade bersih (-157R, 2.579 trade); untung hanya di
  rezim volatil 2024-2026. Data Dukascopy setara Setra (99% trade searah di periode sama). Lihat riset/xau/log.md.
- Intraday, daftar koin sesuai masanya 2024-skrg: rasio 0,65 vs 2,24 (daftar tetap); modul A tanpa edge. Lihat riset/intraday/log.md.
- XAU, audit 30 Okt 2026: juara rugi 8 dari 12 tahun (2015-2026); backtest Setra optimis ±1/3 karena candle ambigu dianggap BUY
  (urutan M1: +43 → +29R/thn). Tidak ada edge permanen; K6 (ide #22) uji maju. Lihat riset/xau/log.md.

- Portofolio 3 bot, 20 Nov 2026 (`riset/portofolio.py`; risiko swing 1%, intraday 1%, XAU 0,5%; % dijumlah, tanpa majemuk):
  2020-2026 per tahun gabungan +176/+205/+112/+144/+175/+67/+112%, **tahun minus gabungan 0/7** (XAU sendiri 1/7, 2021 -3,9%;
  XAU 2004-2026 sendiri 7/23), terburuk 2025 +67%, DD gabungan 21,2% (swing 16,3 · intraday 13,3 · XAU 13,0), korelasi
  bulanan swing-intraday +0,19 · swing-XAU +0,14 · intraday-XAU -0,03, bulan ketiganya rugi 6/83. Catatan jujur: swing memakai
  daftar koin tetap (melebih-lebihkan ±20-28%) dan R kotor; seluruh periode ini sudah dipakai merancang → angka optimis.
  Kesimpulan: target "tanpa tahun minus" sudah tercapai di level portofolio; XAU paling berharga sebagai diversifikasi
  (korelasi ±0) → sumber edge baru dinilai dari sumbangannya ke portofolio.

## E. PERCEPATAN RISET (pemilik, 20 Nov 2026) — berlaku untuk ketiga bot, mengalahkan aturan lama yang bertentangan
Masalah yang diperbaiki: tiap sesi habis untuk rutinitas, hanya 2 ide/minggu, dan hampir semua ide berupa tambalan kecil pada
juara (filter/bobot/TP/SL) yang secara statistik hampir mustahil lolos P_rasio → riset terasa tanpa progres.

1. **Rutinitas sudah dikerjakan GitHub Actions tiap hari** (`riset/harian.py`, workflow `riset-harian.yml`, 23:47 WIB):
   unduh data, replay kesetaraan, penyebab SL 7 hari, bayangan. Sesi riset **membaca `riset/harian/<bot>.md`** untuk bagian
   Kesehatan · Penyebab SL · Live vs bayangan, dan **tidak menjalankan ulang** langkah itu kecuali tertulis GAGAL/BEDA atau
   hasilnya lebih tua dari 36 jam. Unduhan data untuk eksperimen tetap boleh (XAU: bibit Dukascopy di `riset/data/` kini
   diperbarui otomatis tiap bulan penuh; bulan berjalan dari Setra). Arsip 21 hari: `riset/harian/arsip/`.
2. **Saringan cepat (tiap sesi MAKSIMAL 10 ide/varian, satu skrip saringan per sesi — hemat token)**: semua ide dari ide.md + ide baru diuji kasar dulu di **periode pilih saja**
   (XAU ≤ 2014 + walk-forward jendela pertama; crypto/intraday ≤ 2021), metrik: R/trade, tahun minus, DD, jumlah trade.
   Hanya **2-3 teratas** yang lanjut ke tahap B penuh (walk-forward + signifikansi + data terkunci). Ide yang gugur di
   saringan berstatus `disaring` (boleh diuji lagi bila ada data/definisi baru). **Semua ide yang disaring ikut dihitung**
   dalam "total ide diuji" (kejujuran soal bias). Lulus saringan BUKAN bukti; gerbang tahap B tidak dilonggarkan.
3. **Status `kandidat`** (P_rasio 0,50-0,70 dengan arah konsisten): langsung ditambahkan ke MENU bayangan bot (bayangan.py) dan
   dipantau otomatis tiap hari oleh rutinitas harian **hanya pada data baru sejak tanggal masuk**. Maksimal 3 kandidat per bot.
   Naik ke `uji-maju` bila setelah ≥ 6 minggu & jumlah trade minimum (bagian B.4) penantang lebih baik dari juara;
   `gagal` bila setelah 8 minggu tidak lebih baik. Kandidat tidak pernah diusulkan dipasang tanpa melewati gerbang B.
4. **Arah: SUMBER EDGE BARU, bukan tambalan.** Dari ide yang masuk tahap B penuh tiap sesi, **minimal 1 harus sumber edge baru**
   (strategi/komponen/pasar baru yang korelasinya rendah dengan juara), bukan filter/bobot/SL/TP pada juara. Tambalan pada juara
   hanya diuji bila datang dari CELAH berulang (sebab_sl) atau skill yang sudah lulus tahap 1.
   **"Tahun minus" juga dinilai di level PORTOFOLIO 3 bot** (`riset/portofolio.py`, risiko sesuai bot live): sumber edge baru
   dinilai dari sumbangannya pada tahun minus & DD portofolio, bukan hanya botnya sendiri.
5. **Jadwal bergilir, tiap bot 2 sesi/minggu HANYA SAMPAI 4 Des 2026** (masa kilat SNR): XAU Senin & Kamis · crypto Selasa &
   Jumat · intraday Rabu & Sabtu. **Mulai 5 Des 2026 kembali 1 sesi/minggu per bot** (XAU Senin · crypto Selasa · intraday
   Rabu) untuk hemat token (pemilik, 20 Nov). Laporan ringkas: tabel + kesimpulan, tanpa mengulang isi riset/harian. **Review bulanan = sesi terakhir bot itu di bulan berjalan**
   (sesi berikutnya bot itu jatuh di bulan baru). Gerbang pasang tetap maksimal 1 perubahan strategi per bulan per bot.
6. **Kurikulum skill = PROGRAM KILAT** (lihat `riset/KURIKULUM_SKILL.md` bagian "Program kilat"): dikerjakan PERTAMA di setiap
   sesi, boleh beberapa tahap per sesi, batas waktu per tahap 3 sesi lalu otomatis pindah definisi/skill.

## F. MILESTONE & SARINGAN MASSAL (pemilik, 24 Nov 2026) — berlaku semua bot, mengalahkan aturan lama yang bertentangan
1. Arah kerja = `riset/MILESTONE_2026.md` (target T1-T9 per bot, tenggat 31 Des 2026). Tiap sesi memilih pekerjaan yang paling
   memperkecil celah ke target dan menambah satu baris di `riset/<bot>/RAPOR.md`. Ringkasan Telegram punya bagian tetap
   "Milestone" (✅/❌ T1-T9 versi terbaik + celah yang dikerjakan).
2. Saringan massal: workflow `saringan-malam.yml` (01:17 WIB) menjalankan bank ide `riset/massal/<bot>.py` tanpa token dan
   menulis `riset/<bot>/massal/terbaru.md` + `penantang.json`. Sesi riset TIDAK lagi menulis skrip saringan dari nol:
   a) baca `terbaru.md`; b) 1-3 penantang teratas → walk-forward + P_rasio + Setra (gerbang lama tetap); lolos/kandidat →
      MENU bayangan; c) tambah ≥ 1 KELUARGA baru (10-500 varian) ke `riset/massal/<bot>.py` yang menyerang celah target
      terbesar — malam itu juga diuji otomatis; d) keluarga wajib memakai `ke_inti`/`inti.nilai` agar penilaian sama.
3. Penantang = lolos `inti.penantang` (IS lebih baik dari juara pada tahun minus / rasio ≥ 1,25x, OOS PF > 1,1, tidak menambah
   tahun minus OOS). Penantang BUKAN usulan live. Gerbang live tetap: P_rasio ≥ 0,90 + uji maju (pemilik boleh mempersingkat).
4. Banyak varian = banyak lolos kebetulan: utamakan penantang yang tetangga parameternya juga lolos, dan keluarga dengan alasan
   (literatur/celah nyata), bukan grid acak.
5. Perubahan risiko per trade (mis. naik agar T5 ≥ 10%/thn tercapai dengan DD ≤ 20%) hanya usulan; keputusan pemilik.
