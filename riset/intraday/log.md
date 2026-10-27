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
