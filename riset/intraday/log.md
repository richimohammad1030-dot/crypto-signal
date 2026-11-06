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

## 2026-10-30 · Intraday 1:1 (bukan scalping): modul A peringkat 1-25 diperkuat + modul B 1:1 (permintaan pemilik, risiko 1%)
PIT, 3 posisi / 3 order menunggu. Skrip: `eksperimen/pit_a_diperkuat_b11_2026-10-30.py`.
- **Modul A diperkuat** (56 varian, peringkat 1-25): exit RSI (hold 2 jam) vs 1:1 (SL 2/3 ATR, hold 4/8/24 jam), filter tren BTC,
  ATR ≥ 1,5/2%, dip standar vs dalam (RSI2 < 2). Terbaik di KEDUA periode: **1:1, SL 3 ATR, hold maks 4 jam, BTC tren naik,
  ATR ≥ 1,5%, dip standar, limit 0,5 ATR** → rasio A saja IS 2,69 / OOS 1,35 (juara A di 1-25: IS 2,75 / OOS 0,74). Peringkat ke-4
  menurut IS saja (terbaik IS: RSI + BTC, IS 2,91 / OOS 0,63).
- **Gabungan** (OOS 2024-skrg; avg / R/thn / DD / rasio / CAGR 1% / DD ekuitas / P>juara):
  juara A+B: +0,021 / +15,5 / 23,9 / 0,65 / 15% / 23% / - ·
  A 1-25 + B: +0,045 / +21,3 / 16,5 / 1,29 / 22% / 16% / 0,96 ·
  **A diperkuat 1:1 + B (TP open)**: +0,059 / +23,3 / 17,2 / **1,36** / **25%** / **17%** / **0,94** (±37 trade/bln) ·
  A diperkuat 1:1 + B 1:1 SL1,0 h24: +0,061 / +24,1 / 21,1 / 1,14 / 25% / 20% / 0,84 ·
  A diperkuat 1:1 + B 1:1 SL1,5 h24: +0,068 / +26,4 / 26,9 / 0,98 / 28% / 25% / 0,85 · B 1:1 hold 12 jam lebih buruk (rasio 0,56-0,68).
- Kesimpulan: 1:1 memperkuat modul A; untuk modul B, 1:1 menaikkan profit sedikit tetapi DD naik 17% → 20-25% (B sekarang RR ±0,67:1).
  Seluruh periode (IS+OOS) risiko 1%: A diperkuat + B CAGR 44% DD 17%; + B 1:1 SL1,0 CAGR 42% DD 26%. Menunggu keputusan pemilik.

## 2026-10-30 · Rasio TP:SL 0,5 / 1 / 1,5 / 2 (permintaan pemilik: win rate tinggi + R lumayan, risiko 1%)
PIT, modul A diperkuat (peringkat 1-25, BTC naik, ATR ≥ 1,5%, limit 0,5 ATR) + modul B. Skrip: `eksperimen/pit_rasio_tp_sl_2026-10-30.py`.
- Modul A saja (SL 3 ATR, hold 4 jam; OOS win / rasio): TP 0,5× 64,5% / 1,41 · 1× 58,4% / 1,35 · 1,5× 58,4% / 1,76 · **2× 58,4% / 1,96**
  (IS 3,21, terbaik di kedua periode). Dengan hold 4 jam TP ≥ 1× jarang tersentuh: TP 2× → 80% keluar karena batas waktu (+0,23R),
  TP 3,5%, SL 16%. Artinya exit nyata modul A = batas 4 jam; TP jauh hanya pengaman.
- Modul B saja (limit 1 ATR dari open; OOS win / rasio / DD): TP 0,5× SL1,5 70,8% / 1,00 / 14,8R · 1× 54,4% / 0,78 / 28,3R ·
  1,5× 46% / 0,61 / 44,6R · 2× 42% / 0,73 / 44,0R. B sekarang (TP di open = 0,67× SL) tetap terbaik; RR besar → DD melonjak.
- Gabungan OOS 2024-skrg (win / CAGR 1% / DD ekuitas / P>juara): semua 0,5: 71,2% / 23% / 17% / 0,91 · semua 1: 55,2% / 28% / 25% / 0,85 ·
  semua 1,5: 48,4% / 38% / 34% / 0,82 · semua 2: 45,3% / 46% / 33% / 0,89 ·
  **A TP 2× (SL 3 ATR, maks 4 jam) + B tetap: 63,4% / 27% / 16% / 0,96** (seluruh periode CAGR 46%, rasio OOS 1,57) ·
  A TP 1,5× + B tetap: 63,4% / 26% / 15% / 0,96 · A TP 1× + B tetap: 63,4% / 25% / 17% / 0,94 · A TP 0,5× (hold 24j) + B tetap: 65,8% / 26% / 20% / 0,96.

## 2026-10-30 · Matriks rasio TP:SL modul A × modul B (boleh berbeda; permintaan pemilik)
PIT, A diperkuat (SL 3 ATR, maks 4 jam; TP 0,5× pakai maks 24 jam) × B (SL 1,5 ATR; TP 0,5× / 0,67× sekarang / 1× / 1,5× / 2×), 20 kombinasi.
Skrip: `eksperimen/pit_matriks_rasio_2026-10-30.py`. Pola: B dengan TP ≥ 1× selalu menaikkan DD ke 24-36%; A dengan TP 1,5-2× terbaik.
OOS 2024-skrg (win / RR tercapai / exp / PF / CAGR 1% / DD / rasio / P>juara; seluruh periode CAGR / DD):
- **A 2× + B 0,5×**: 68,7% / 0,55 / +0,056R / 1,20 / 24% / **13,5%** / **1,59** / 0,96 · semua 40% / 13,5% · bulan positif 65%, bulan terburuk -7R
- A 1,5× + B 0,5×: 68,7% / 0,54 / +0,055R / 1,20 / 23% / 13,3% / 1,58 / 0,95 · semua 39% / 13,4%
- **A 2× + B 0,67× (B sekarang)**: 63,4% / 0,69 / +0,064R / 1,19 / **27%** / 15,6% / 1,53 / 0,96 · semua **46%** / 15,6% · bulan positif 71%
- A 1,5× + B 0,67×: 63,4% / 0,68 / +0,063R / 1,19 / 26% / 15,4% / 1,52 / 0,96 · semua 45% / 15,4%
- A 1× + B 0,67×: 63,4% / 0,68 / +0,060R / 1,18 / 25% / 16,7% / 1,32 / 0,94
- A 2× + B 1×: 55,2% / 0,95 / +0,072R / 1,17 / 30% / 23,8% / 1,08 / 0,88 · A 2× + B 2×: 45,3% / 1,47 / +0,109R / 1,22 / 46% / 33,3% / 1,05 / 0,89
Win/kalah beruntun maks 21/8 untuk semua kombinasi teratas. IS rasio: A2+B0,5 3,25 · A2+B0,67 3,47 (tertinggi bersama A1+B0,67).

## 2026-10-30 · Juara v3 dipasang (pilihan pemilik: strategi #2)
- Modul A: peringkat 1-25, BTC H1 naik, limit 0,5 ATR, SL 3 ATR, TP 2× SL, tutup paksa 4 jam (tanpa exit RSI). Modul B tetap.
- Verifikasi: `pit_intraday.py` mereproduksi eksperimen persis (2.944 trade; 2024-skrg 1.091 trade, +0,064R, rasio 1,57).
  Daftar tetap: 2.665 trade, +0,098R, rasio 2,98 (2024-skrg 2,34). Replay mesin bot: 2.662/2.665 identik (3 = celah data 2020-2021).
- LIVE_START intraday = 30 Okt 2026 16:00 WIB; baseline.json["intraday"] dibuat ulang dari juara v3.
- Pemilik meminta riset mingguan tetap berjalan untuk mengoptimalkan v3. Mulai sekarang keputusan intraday wajib memakai uji
  daftar koin sesuai masanya (PROSEDUR langkah 1-3).

## 2026-11-06 · Riset mingguan: I-22 (A-short cermin), I-23 [lit] (dip idiosinkratis)
Data diperbarui s.d. 6 Nov 2026 ±02:00 WIB (49 koin + BTC, 177 koin tambahan PIT; H1 + funding + 15m, tanpa kegagalan unduh).
Skrip: `eksperimen/pit_2026-11-06.py` (salinan `orders()` + replay penuh portofolio, PIT = uji utama, daftar tetap = pembanding).
Juara v3 (data baru) · PIT: 2.965 trade, +0,087R, DD 15,8R, rasio 2,45 · 2020-23 rasio 3,49 · **2024-skrg +0,060R, R/thn +23,6, rasio 1,49**
(saat dikunci 1,57) · per tahun 38/93/36/25/25/9/32. Daftar tetap: 2.689 trade, +0,096R, rasio 2,90 (2024-skrg 2,17).
- **I-22 modul A cermin SHORT saat BTC H1 turun** (ditambahkan ke juara; 11 varian PIT): dasar rasio lama 2,80 vs 3,49 (-20%),
  baru 0,75 vs 1,49 (-50%), 1/7 tahun, tanpa_top2 114 vs 160, P 0,00. Modul A-short 2024-skrg 111 trade **-16,6R** (-0,15R/trade);
  hanya 2022 terbantu (+45 vs +36). Tetangga (tanpa funding, RSI 90/65 & 97/75, limit 0,25/0,75, hold 3/6 j, SL 2 ATR, TP 1×,
  peringkat 1-50) semua lebih buruk (rasio baru 0,41-1,12). Daftar tetap: rasio baru 1,01 vs 2,17. **GAGAL**: lonjakan di tren turun
  tidak berbalik dalam 4 jam seperti dip di tren naik (asimetri long/short), dan order short memakan slot modul B.
- **I-23 [lit] modul A hanya dip idiosinkratis** (lewati jika RSI2 BTC 15m < 5/10/20/30/50): rasio lama -19% s.d. -55%,
  baru -23% s.d. -36%, P 0,07-0,32; daftar tetap juga gagal (rasio lama -37% s.d. -55%). **GAGAL**. Di PIT 2024-skrg edge modul A
  justru terkumpul saat BTC ikut turun (sisa sinyal dengan RSI2 BTC ≥ 50 hanya 54 trade +1,3R), tetapi di daftar tetap polanya
  terbalik → tidak konsisten, tidak dijadikan ide baru. Sumber: Da, Liu & Schaumburg (2014), "A Closer Look at the Short-Term
  Return Reversal", Management Science 60(3).
- Data terkunci tidak dipakai (tidak ada ide lolos tahap 1-2). Total ide intraday bernomor yang sudah diuji: 14 (I-01 s.d. I-23,
  di luar ±15 jalur fondasi 27 Okt). Kandidat penantang: tidak ada; juara v3 tetap.

## 2026-11-06 (sore) · TAHAP 0 "untung di semua tahun" + PROGRAM UTAMA OPTIMASI putaran 1 (permintaan pemilik)
Data diunduh ulang s.d. 6 Nov 2026 ±15:00 WIB (49 koin + 177 koin PIT; H1 + funding + 15m, tanpa kegagalan).
Skrip: `eksperimen/tahap0_semua_tahun_2026-11-06.py` (tabel per tahun, 4 varian), `celah_2026-11-06.py` (kondisi pasar),
`opt1_ukuran_posisi_2026-11-06.py` + `opt1b_tetangga_dispersi_2026-11-06.py` (jalur ukuran posisi).
- **Tahap 0, PIT biaya juara: LULUS tipis.** 2.968 trade, +259,5R, PF 1,28, DD 15,8R, fill 62%. Per tahun (R / tanpa 2% terbaik per tahun):
  2020 +38,0/+24,0 · 2021 +92,6/+62,7 · 2022 +35,6/+31,2 · 2023 +24,9/+18,1 · 2024 +25,3/+10,6 · **2025 +9,4/+1,6** · 2026 +33,7/+29,3.
  12 bulan bergulir terendah +5,5R (0 dari 70 jendela minus). Per koin 71/119 positif; tanpa koin terbaik tiap tahun tetap positif (2025 +6R).
  Daftar tetap: semua tahun positif, 2025 +18,0R (tanpa 2% +10,5).
- **Uji stres eksekusi** (taker 0,12%, limit/TP harus tembus 0,05%): PIT +155R (-40%), **2025 -6,5R**, tanpa 2% terbaik 2024 -6,3 & 2025 -13,7;
  daftar tetap 2025 +3,8 (tanpa 2% -3,6). Kesimpulan: edge 2024-2025 (±0,03-0,05R/trade) lebih kecil dari ketidakpastian eksekusi.
- **Celah:** B-long 2024 +5,7R / 2025 -2,8R (2025: peringkat 1-10 -9,1R, BTC naik > 10%/30 hari -10,0R, Mei 2025 -10,5R);
  B-short 2022 -6,1R; sesi isi 15-20 WIB +13,5R/442 (stres -12,1R); dispersi rendah avg +0,053R vs tinggi +0,129R; akhir pekan +0,137R vs hari kerja +0,070R.
- Program ditetapkan **OPTIMASI** (aturan pemilik: lulus → optimasi), dengan usulan pagar stres (lihat PROSEDUR PROGRAM UTAMA).
- **Putaran 1 · ukuran posisi** (bobot pasca-trade, trade sama; rata-rata bobot 2020-23 = 1):
  - I-08 risiko per modul (60 kombinasi): terbaik 2020-23 A 1,5 / B-long 0,75 / B-short 0,5 rasio 4,28 (+23%) / 2,06 (+36%), P 0,91, tetapi
    2025 tanpa 2% terbaik -5R; 6 teratas semuanya ≤ 0 di 2025 tanpa 2% → **GAGAL** (syarat semua tahun).
  - I-24 [lit] volatility-managed (Moreira & Muir 2017): rasio lama +10..+27%, baru -16..+6%, P ≤ 0,39 → **GAGAL**
    (sesuai kritik Cederburg dkk. 2020: tidak stabil di luar sampel).
  - **I-25 [lit] bobot dispersi** (std return 24 jam 25 koin teratas ÷ median 365 hari, batas [0,5; 2]): rasio 3,49 → **4,44** (+27%) lama,
    1,51 → **1,89** (+25%) baru, P 0,95, DD 15,8 → 17,7R (+12%), DD ekuitas 15,6 → 17,5%, CAGR 1% 45,7 → 54,6% (2024+ 25,6 → 34,7%).
    Per tahun +48/+114/+22/+27/+34/+13/+41 (2022 turun dari +36), tanpa 2% semua +, stres terburuk -6,5 → 0,0R; daftar tetap rasio baru 2,20 → 3,01.
    Tetangga: k 0,5/1/1,5 × batas 1,5/2 → 5/6 lolos; jendela 12/48 jam, median 180/730 hari, 48j-top50 lolos; top 10 koin & 12j-top10 gagal,
    top 50 batas (P 0,90). Risiko terbuka bersamaan maks 4,4% (juara 3%). → **UJI-MAJU** sejak 6 Nov 2026. Data terkunci intraday (PIT) sudah
    menjadi uji utama sejak v3, jadi tidak ada data baru tersisa selain uji maju.
- Total ide intraday bernomor yang sudah diuji: 17. Juara v3 tidak berubah.
