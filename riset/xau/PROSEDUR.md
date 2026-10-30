# Prosedur riset · XAU

Instruksi untuk routine **"Riset Bot XAU"** (setiap Jumat 00:18 WIB).
Tujuan: menemukan perbaikan bot XAU (Gold Daily Straddle) yang terbukti dengan data, lalu **mengusulkannya** ke pemilik.
Routine tidak pernah mengubah bot live. Perubahan dipasang hanya setelah pemilik setuju di chat.
Riset crypto dikerjakan routine terpisah (`riset/crypto/`). Jangan menyentuh berkas crypto.

Strategi XAU berbeda total dengan crypto: satu instrumen, breakout harian dari range 04:00-07:00 WIB
(BUY STOP dan SELL STOP sekaligus, OCO), SL 1,5 x ATR, TP 4R, semua ditutup pukul 23:00 WIB.
Jangan memakai kesimpulan riset crypto untuk XAU tanpa diuji ulang dengan data XAU.

**Wajib baca dulu `riset/ATURAN_BERSAMA.md`** (sumber ide, uji signifikansi, data terkunci, uji maju). Aturan di sana
berlaku di atas kriteria LOLOS di bawah: lolos kriteria di bawah = lolos tahap 1 saja.

## 0. Aturan keras
- **Aturan tetap pemilik (31 Okt 2026): sinyal dikirim 07:00 WIB dan semua order/posisi ditutup 23:00 WIB. Jangan pernah
  mengusulkan perubahan bagian ini** (jam pasang, jam tutup, hold multi-hari). Yang boleh diteliti: arah, cara masuk, SL/TP, filter, risiko.
- **Jangan ubah** file bot: `signal_bot.py`, `gold_bot.py`, `templates.py`, `gold_templates.py`, `commands.py`,
  `jurnal.py`, `kesehatan.py`, `baseline.json`, file state (`*.json` di root), dan `.github/`.
- Hanya tulis di `riset/xau/` dan `riset/laporan/xau/`.
- Kerjakan di branch baru `claude/riset-xau-YYYY-MM-DD` (tanggal WIB hari ini), commit, lalu push branch itu.
  Workflow `kirim-laporan-riset.yml` otomatis mengirim ringkasan ke chat pribadi pemilik dan menyalin berkas riset ke main.
- Jangan membuat routine, scheduled task, atau pengingat baru.

## 1. Persiapan data (±1 menit)
```bash
pip install -q --break-system-packages numpy pandas scipy
python3 riset/unduh_xau.py /tmp/data
python3 riset/backtest_xau.py . /tmp/data/xau.json /tmp/data/trades_xau.csv
```
`backtest_xau.py` memakai mesin asli bot (`gold_bot.GoldEngine`), jadi selalu mengikuti versi juara yang sedang live.
Data XAU (Setra, sumber yang sama dengan bot) hanya tersedia sejak **Februari 2025**.

**Sejak audit 30 Okt 2026** (lihat `riset/xau/log.md`):
- Mesin eksperimen: `riset/xau/eksperimen/audit_mesin.py` (identik dengan bot; parameter, filter, bobot per sisi, fitur tren/volatilitas).
- Pembagian data: pilih **2015-2021**, uji **2022 - Jan 2025** (Dukascopy), konfirmasi **Feb 2025 - skrg** (Setra; data sambung
  `audit_mesin.sambung`). Dukascopy 2015 - Jan 2025 **sudah terpakai** (bukan data terkunci lagi); data bersih hanya data baru (uji maju).
- **Bias candle ambigu**: ±6% hari candle H1 saat terisi menyentuh high DAN low range; bot memilih BUY, padahal SELL lebih sering
  duluan (47/86 hari 2022-skrg). Pakai `ambigu=dict` dari `eksperimen/ambigu_m1_2022_2026.json` (+ `audit_m1.py` untuk hari baru)
  saat membandingkan varian; laporkan angka "asumsi bot" dan "urutan M1".
- **Juara sejak 2 Nov 2026 = multi-strategi MR (RSI2) + K6** (`riset/xau/STRATEGI.md`, ide #34). Acuan riset:
  `eksperimen/multi_mesin.baseline(D, A, F, ambigu=...)`; `backtest_xau.py` otomatis mengikuti bot. Setiap minggu jalankan
  `python riset/xau/bayangan.py . /tmp/data/xau.json /tmp/data/xau_panjang.json` (uji maju: baseline vs MR saja, K6 saja, juara lama,
  PENANTANG). Usulan pergantian/bobot hanya setelah ≥ 6 minggu & ≥ 20 trade, dan `riset/replay_xau.py` wajib IDENTIK.
Data terkunci (tahap 3 ATURAN_BERSAMA): `python3 riset/unduh_xau_panjang.py /tmp/data 2015` → `/tmp/data/xau_panjang.json`
(Dukascopy, harga BID, 2015-sekarang; bibit s.d. Okt 2026 ada di `riset/data/xau_dukascopy_h1.json.gz`, jadi hanya
bulan baru yang diunduh, ±5-20 menit karena dibatasi server). **Juara sendiri rugi di periode ini (lihat log 30 Okt 2026).** Hanya dipakai periode **2015 - Jan 2025**
untuk konfirmasi ide yang sudah lolos tahap 1-2: `python3 riset/backtest_xau.py . /tmp/data/xau_panjang.json <out.csv>`.
Hitung juga hasil bersih biaya 0,40 USD per trade (biaya dalam R = 0,40 / r0, r0 = |entry - exit| / |R|).
Jika unduhan gagal, tetap buat laporan yang menjelaskan kegagalannya.

## 2. Tentukan mode
- Jika **Jumat berikutnya sudah masuk bulan baru** (hari ini Jumat terakhir bulan ini) → **REVIEW BULANAN** (langkah 3 + 4).
- Selain itu → **RISET MINGGUAN** (langkah 3 saja).

## 3. Riset mingguan: uji 1-2 ide XAU
1. Uji 2 ide: ide teratas berstatus `antri` dari `riset/xau/ide.md`, **ditambah 1 ide baru** sesuai
   ATURAN_BERSAMA bagian A (literatur = nilai tambah, tidak wajib).
2. Tulis hipotesis singkat, lalu uji dengan skrip di `riset/xau/eksperimen/<nama-ide>.py`
   (salin dan modifikasi `backtest_xau.py`; ide yang mengubah kapan order dipasang/ditutup wajib replay penuh).
3. Bandingkan dengan juara (aturan yang sedang live), **setelah biaya**:
   - Paruh pertama **Feb-Des 2025** dan paruh kedua **2026-sekarang**, serta per kuartal.
   - Total R, R rata-rata, win rate, drawdown terburuk, rasio total R / drawdown, jumlah trade.
   - Ketahanan: hasil tanpa 2% trade terbaik.
4. Keputusan (kriteria lebih ketat karena data hanya ±20 bulan):
   - **LOLOS** jika rasio R/drawdown membaik ≥ 15% di paruh pertama **dan** paruh kedua, tidak lebih buruk di ≥ 5 dari
     7 kuartal terakhir, jumlah trade tidak turun lebih dari 40%, dan tidak bergantung pada segelintir trade besar.
     Ide ini lanjut ke tahap 2-4 ATURAN_BERSAMA
     (signifikansi, data terkunci, uji maju) sebelum menjadi **kandidat penantang**.
   - **GAGAL** jika tidak memenuhi. Catat alasannya agar tidak diuji ulang.
   - **PERLU DATA** jika hasil menjanjikan tetapi jumlah trade per kuartal terlalu sedikit untuk dinilai.
5. Catat di `riset/xau/log.md` (tanggal, ide, angka utama, keputusan) dan perbarui status di `riset/xau/ide.md`.
   Tambahkan ide XAU baru ke `riset/xau/ide.md` dengan status `antri`
   (lanjutkan penomoran dari nomor tertinggi di daftar XAU maupun crypto, agar nomor tidak bentrok).

## 4. Review bulanan (hanya Jumat terakhir bulan ini)
Tambahan selain langkah 3:
1. Statistik juara terbaru dari backtest (per kuartal, BUY vs SELL, alasan keluar: SL / TP / tutup 23:00).
2. Bandingkan hasil live (`gold_state.json` field `hist`, `jurnal/xau-*.json`) dengan backtest periode yang sama
   (sejak `LIVE_START` XAU di `kesehatan.py`). Selisih besar menandakan masalah eksekusi atau data.
3. Rangkum semua **kandidat penantang** XAU yang masih berlaku beserta buktinya, dan usulan yang masih menunggu
   persetujuan pemilik: apa yang diubah, bukti paruh pertama dan kedua, dampak ke profit dan drawdown.

## 5. Keluaran
- `riset/laporan/xau/riset-YYYY-MM-DD.md` - laporan lengkap (angka, tabel, kesimpulan).
- `riset/laporan/xau/riset-YYYY-MM-DD.txt` - ringkasan untuk Telegram, **maks 3.500 karakter**, HTML Telegram sederhana
  (hanya `<b>` dan `<pre>`), bahasa Indonesia, gaya sama dengan bot: judul tebal `RISET XAU` atau `REVIEW BULANAN XAU`,
  tanggal, garis `────────────────────`, judul bagian tebal dengan garis di bawahnya, tanpa emoji.
  Baris di dalam `<pre>` maksimal ±38 karakter.
  Isi: mode, ide yang diuji dan keputusannya, kandidat penantang (jika ada), dan untuk review bulanan:
  ringkasan live vs backtest, daftar usulan.
- Karakter `<`, `>`, `&` di luar tag HTML harus ditulis sebagai `&lt;`, `&gt;`, `&amp;`.
