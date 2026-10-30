# Jurnal riset · INTRADAY

Catatan setiap ide yang diuji: tanggal, ide, angka utama, keputusan. Ide yang gagal tidak diuji ulang
kecuali ada data baru yang relevan. Semua angka net fee (maker 0,02% / taker 0,07%), slippage, dan funding.
Periode lama 2020-2023 dipakai untuk memilih; periode baru 2024-Okt 2026 hanya untuk menguji.

## 2026-10-27 · Fondasi (riset di chat bersama pemilik)
Permintaan pemilik: bot crypto kedua dengan trade intraday/scalping, ada sinyal hampir setiap hari, TP/SL jelas.

**Jalur yang GAGAL (jangan diuji ulang tanpa data baru):**
- Holding ala XAU untuk strategi swing (filter tren + breakout 3-24 candle, SL 1,5-3 ATR, TP 2-4R, tutup 23:00 WIB):
  16 kombinasi semua rugi; versi persis XAU -0,12R/trade, tanpa biaya pun -0,03R.
- Literatur intraday (H1, 49 koin, tutup 23:00): seasonality BTC 22-24 UTC, intraday TSMOM (Shen dkk. 2022),
  noise-area breakout (Zarattini/Concretum), breakout range sesi Asia: semua rugi setelah biaya.
- Scalping 5m (10 koin, 2023-2026): EMA 9/21, VWAP reversion 2SD, Bollinger+RSI, Connors RSI2:
  edge kotor +0,01% s.d. +0,03%/trade, rugi bahkan dengan biaya maker.
- Modul per rezim volatilitas (stop order breakout, straddle OCO, market momentum, limit mean-reversion) dengan
  tutup 23:00: hanya limit mean-reversion saat volatilitas tinggi yang positif; gabungan harian +0,015R/trade.
  (Sempat +0,14R karena bias memilih modul dari order yang sudah terisi; sudah diperbaiki.)
- Cross-sectional harian (long terkuat/short terlemah, reversal, funding carry): -0,02 s.d. -0,07R/posisi 2024-2026.
- Open interest + rasio taker (20 koin, 2022-2026): flush likuidasi +0,05R di 2022-2023 tetapi -0,06R di 2024-2026 (overfit).

**Jalur yang LOLOS:**
- Dip RSI2 limit (tren naik) di H1 lalu 15m: +0,09R/trade di 2024-2026, positif tiap tahun.
- Tanpa tutup paksa 23:00 + sistem kadaluarsa: modul B (limit pagi saat volatilitas tinggi) menjadi kuat.

**Optimasi & penguncian:**
- Diagnosa: hold > 8 jam rata-rata -0,13 s.d. -0,25R → time stop. Hari terburuk = 10-19 order terisi bersamaan → batas posisi.
  Kerugian 2025 dari sisi LONG → filter tren BTC.
- Parameter modul B dipilih dari 864 kombinasi (Calmar 2020-2023): SL 1,5 ATR, filter BTC, time stop 24 jam.
  81 tetangga parameter: semua positif di 2024-2026, 2025 positif di semua.
- **Model realistis**: order menunggu ikut memakan slot / dibatalkan saat posisi penuh. Angka turun dari simulasi
  sederhana (yang mengabaikan order menunggu): 3 posisi 53 → ±30 R/thn di 2024-2026. Semua angka resmi memakai model realistis.
- Jumlah posisi & order menunggu (dipilih Calmar 2020-2023): **2 posisi, maks 12 order menunggu**.
- Slot dinamis 2/3 berdasarkan conviction (I-09): gagal.

**Juara v1 dikunci** (lihat `STRATEGI.md`, `PARAM` di `riset/backtest_intraday.py`):
2.963 trade, win 66,9%, +0,092R/trade, +41R/thn, DD 14,4R, PF 1,32.
2020-2023: +0,113R, rasio 5,67 · 2024-skrg: +0,060R, rasio 1,85. Semua tahun positif (2024 +15R terlemah).
Fill rate order 14% (dari 15 order dikirim ±2 terisi). Win beruntun maks 21, kalah beruntun maks 8.

## 2026-10-27 · Revisi pemilik → juara v2
Keberatan pemilik atas v1: fill rate 14% (±60 alert/minggu, mengganggu anggota), risiko harus 1% (bukan 0,5%),
dan 2 vs 3 posisi belum diuji dengan conviction harian.
- **Modul B saja** (model realistis): 3 posisi / 3 order menunggu: fill 61%, +0,073R (2024-skrg), rasio baru 1,41,
  CAGR risiko 1% ±30%. Lebih rendah dari gabungan → modul A tetap dipakai, tetapi dirancang ulang.
- **Conviction harian (I-11)**: 9 fitur jam 07:00 × 2 arah × 2 batas order. Aturan terbaik di 2020-2023 (3 posisi jika
  volatilitas kandidat < median) rasio baru 0,79 vs tetap 3 posisi 1,41. **Gagal.** Tidak ada aturan harian yang lebih
  baik dari jumlah posisi tetap.
- **Desain ulang modul A (I-01)**: 30 kombinasi (limit 0,25-1,5 ATR × berlaku 30/60/120 mnt × ATR ≥ 1%/1,5%) bersama B,
  3 posisi. Filter ATR ≥ 1,5% konsisten menurunkan DD 2024-skrg (11-16R vs 17-29R). Dipilih: fill total ≥ 65% dan rasio
  2020-2023 terbaik → limit 0,25 ATR, berlaku 2 jam, ATR ≥ 1,5%.
- **Jumlah posisi**: rasio 2020-2023: 1 → 2,65 · 2 → 5,70 · 3 → 5,66 · 4 → 4,58 · 5 → 4,04. 2 dan 3 seri;
  dipilih **3** karena berada di dataran (tetangga 2 dan 4 sama-sama tinggi), bukan berdasarkan hasil 2024-skrg.
- **Juara v2 dikunci**: 4.886 trade, fill 70,9%, win 66,5%, +0,064R/trade, +47R/thn, DD 13,4R, PF 1,30.
  2020-2023 rasio 5,66 · 2024-skrg rasio 2,24 (v1: 1,85). Semua tahun positif (2025 terlemah +10,5R).
  Risiko 1%: CAGR ±58%, DD ekuitas 14,0%; periode uji 2024-skrg CAGR ±33%.
- Koreksi angka: simulasi awal (sebelum model realistis) mengabaikan order menunggu yang memakan slot dan memilih dari
  order yang sudah terisi, sehingga terlalu optimis (CAGR 76-95%). Semua angka resmi memakai model realistis.

## 2026-10-27 · Live
- `intraday_bot.py` memakai mesin per-candle yang sama dengan backtest (order bayangan untuk jeda sinyal per koin,
  portofolio 3 posisi / 3 order menunggu, pembatalan saat penuh). Replay 2020-2026: 4.883 dari 4.886 trade identik
  (selisih R maks 0,14 pada trade di celah data Binance 2020-2021); 2025-2026: 1.086 = 1.086 trade, selisih R ≤ 0,00005.
- Jadwal: tiap 15 menit (cron-job.org), pesan saat ada kejadian + ringkasan 2 jam. Channel sama dengan swing, label 🟠 INTRADAY.

## 2026-10-30 · Review bulanan + riset I-02, I-03
Data diperbarui s.d. 30 Okt 2026 01:45 WIB (49 koin + BTC, H1 + funding + 15m, tanpa kegagalan unduh).
Juara v2 (data baru): 4.931 trade, fill 70,9%, win 66,4%, +0,062R/trade, +45,9R/thn, DD 13,4R, rasio 3,41.
2020-2023 rasio 5,66 (tetap) · 2024-skrg +0,040R, rasio 2,00 (turun dari 2,24 karena Okt 2026 -6,8R).
- **I-02 kadaluarsa B** (4/6/8/10/12/16 jam, replay penuh): rasio lama 4,85/5,33/5,39/5,45/**5,66**/4,80,
  baru 1,29/1,00/1,19/1,44/**2,00**/2,05. Jam pendek menaikkan DD baru (17-20R) dan menurunkan R. 16 jam baru sedikit lebih baik
  tetapi lama -15%. **GAGAL**: 12 jam sudah puncak.
- **I-03 batas order menunggu per modul** (A≤1, A≤2, B≤1, B≤2, A≤1+B≤2, A≤2+B≤1; total tetap 3): semua rasio lama turun
  (-1% s.d. -25%). A≤1 rasio baru +14% (2,29) tetapi lama -10%, 3/7 tahun, tanpa_top2 215 vs 230. **GAGAL**.
- Review: modul A melemah (2025 -6,1R, 2026 +0,7R; 6 bln terakhir +0,013R/trade), B-long kuat (+0,16R 6 bln). 6 bln terakhir
  total +0,059R/trade ≥ rata-rata 2024-skrg (+0,040R) → bukan PERINGATAN. Ide baru I-14 (filter BTC modul A).
- Live vs backtest (27-30 Okt): 4 trade tertutup (PEPE, modul A) identik R dan waktu keluar; ZRO terbuka di kedua mesin.

## 2026-10-30 · Fondasi riset diperkuat (chat bersama pemilik) · bias koin selamat
Aturan baru: `riset/ATURAN_BERSAMA.md` (2 ide/minggu termasuk 1 ide baru, signifikansi ≥ 0,90, data terkunci, uji maju).
- **Daftar koin sesuai masanya** (`riset/pit_intraday.py`, 195 koin termasuk yang delisting) vs daftar tetap, juara v2:
  semua: +0,052R vs +0,064R, DD 23,9 vs 13,4R · 2020-2023: rasio 5,58 vs 5,66 (hampir sama) ·
  **2024-skrg: +0,021R vs +0,044R, R/thn +15,5 vs +30,0, DD 23,9 vs 13,4R, rasio 0,65 vs 2,24**. Per tahun PIT:
  2024 +9 · 2025 -1 · 2026 +35.
- Diagnosa 2024-skrg (PIT): **modul A ±0,000R/trade (1.236 trade, tanpa edge)**; B-long +0,039R; B-short +0,084R.
  Peringkat 11-25 +0,061R; 1-10 +0,022R; 26-50 -0,002R. Koin di luar daftar kini -0,008R (597 trade).
  Kesimpulan: edge modul A di 2024-skrg sebagian besar berasal dari daftar koin yang sudah "tahu pemenang". Modul B tahan uji.
- Kalibrasi signifikansi: v1 → v2 P_rasio_lebih_baik 0,66 (2024-skrg). Ide baru I-15, I-16 (prioritas 1).
- Cek kesehatan & rekap intraday aktif (baseline.json["intraday"], R bersih 2024-skrg). Risiko gabungan swing+intraday
  (risiko 1%): korelasi harian -0,05, DD gabungan 25,0% (swing 16,3 / intraday 13,4), risiko terbuka maks 13%,
  1.737 trade intraday di koin yang sedang dipegang swing (8 berlawanan arah).

## 2026-10-30 · Eksplorasi PIT: struktur, scalping SL/TP 1:1 (permintaan pemilik)
Semua dengan daftar koin sesuai masanya (PIT), 3 posisi / 3 order menunggu. IS = 2020-2023, OOS = 2024-skrg.
- Struktur (OOS avg / R/thn / DD / rasio): juara A+B +0,021 / +15,5 / 23,9 / 0,65 · **B saja** +0,056 / +18,3 / 17,7 / 1,03 ·
  A saja +0,006 / +3,1 / 13,3 / 0,23 · **A hanya peringkat 1-25 + B** +0,045 / +21,3 / 16,5 / **1,29** · semua 1-25 +0,053 / +21,2 / 17,1 / 1,24.
  Catatan penting: di IS juara tetap terbaik (rasio 5,58 vs 4,25); IS 2020-2023 tidak membedakan versi yang tahan di 2024-skrg
  (perubahan rezim pasar altcoin). Ide I-15 lahir dari diagnosa OOS → bukti OOS-nya "terpakai", wajib uji maju.
- **Modul A gaya scalping SL/TP tetap 1:1** (SL 0,5/1/1,5/2/3 ATR × hold 2/4/8/24 jam × limit 0,25/0,5; 40 varian): **GAGAL**.
  SL kecil (0,5 ATR) -0,12 s.d. -0,14R/trade; terbaik menurut IS (SL 3 ATR, hold 2 jam, limit 0,5) OOS +0,009R, rasio 0,24.
  Win rate 1:1 ±50% → biaya memakan edge.
- **Modul B 1:1** (12 varian): terbaik menurut IS (SL 1,5 ATR, limit 1 ATR, TP 1,5 ATR dari entry, hold 24 jam) OOS +0,068R,
  R/thn +21,9, tetapi DD 28,3 (rasio 0,78) vs B sekarang (TP di open) rasio 1,03. **GAGAL** (rasio lebih buruk).
- Signifikansi vs juara (OOS 2024-skrg): A 1-25 + B P_rasio 0,96 (seluruh periode 0,34); B saja 0,84; B 1:1 0,73.
  Risiko 1% OOS: juara CAGR 15% DD 23% · A 1-25 + B CAGR 22% DD 16% (±40 trade/bln) · B saja 19% DD 17% (±27 trade/bln).
- Status: I-15 (A hanya peringkat 1-25) → `uji-maju` atas persetujuan pemilik / keputusan pemilik; scalping 1:1 → `gagal` (I-17).
