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
   Jika 0,70-0,90 → status `perlu-data` (menjanjikan, belum meyakinkan). Di bawah 0,70 → `gagal`.
3. **Uji data terkunci** (hanya sekali per ide, setelah lolos tahap 1-2; **dilarang** dipakai untuk memilih/menyetel parameter):
   - Crypto swing & intraday: daftar koin **sesuai masanya** (`riset/pit.py`, data `riset/unduh_pit.py`), termasuk koin yang
     sudah delisting. Syarat: rasio R/DD penantang tidak lebih buruk dari juara pada daftar ini.
   - XAU: data **Dukascopy 2015 - Jan 2025** (`riset/unduh_xau_panjang.py`), periode yang tidak dipakai merancang juara.
     Syarat: rasio R/DD penantang tidak lebih buruk dari juara (setelah biaya).
   Catat di log bahwa data terkunci sudah dipakai untuk ide itu.
4. **Uji maju**: ide yang lolos tahap 1-3 berstatus `uji-maju` (bukan langsung diusulkan). Setiap minggu, bandingkan penantang
   vs juara **hanya pada data baru sejak tanggal lolos**. Usulan ke pemilik baru diajukan setelah minimal **6 minggu** dan
   **jumlah trade minimal** (swing 30, intraday 60, XAU 20) dengan penantang tidak lebih buruk dari juara.
   Pemilik boleh memutuskan lebih cepat setelah membaca buktinya.

Status ide: `antri` · `diuji` · `perlu-data` · `uji-maju` (lolos tahap 1-3, sedang diuji maju) · `lolos` (siap diusulkan) ·
`gagal` · `dipasang`.

## C. Review bulanan (tambahan)
- **Risiko gabungan swing + intraday** (dikerjakan di review bulanan INTRADAY):
  `python riset/risiko_gabungan.py <trades_swing.csv> <trades_intraday.csv> 1 1` (seluruh periode) dan dengan tanggal mulai
  2024-01-01. Laporkan korelasi harian, hari keduanya rugi, drawdown gabungan, risiko terbuka maksimum bersamaan,
  dan trade intraday di koin yang sedang dipegang swing. Jika drawdown gabungan > 30% (risiko 1% keduanya) → tandai PERINGATAN.
- **Bias koin selamat** (review bulanan CRYPTO dan INTRADAY, cukup sebulan sekali): jalankan juara dengan daftar koin sesuai
  masanya dan laporkan selisihnya terhadap daftar tetap. Angka sesuai masanya adalah **ekspektasi yang lebih jujur**.
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
