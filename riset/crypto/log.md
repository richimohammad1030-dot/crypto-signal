# Jurnal riset · CRYPTO

Catatan setiap ide yang diuji: tanggal, ide, angka utama, keputusan. Ide yang gagal tidak diuji ulang
kecuali ada data baru yang relevan.

## 2026-10-20 · Fondasi
- **Backtest crypto** (Des 2019 - Okt 2026, 49 koin): 2222 trade, win rate 40%, +0,32R/trade, profit factor 2,0,
  drawdown terburuk 25,7R. Short lemah di 2024-2026 (+0,04R/trade) dibanding long (+0,38R).
- **Perbaikan data backtest:** arsip funding Binance belum ada untuk bulan berjalan, sehingga short bulan berjalan
  tersaring. Sekarang memakai funding Hyperliquid (sumber bot live) untuk periode tersebut.
- **Label conviction 4 faktor** (jarak SL, jarak dari EMA200, peringkat, tren BTC): HIGH +0,57R / +0,68R vs
  LOW +0,14R / -0,01R (2020-2023 / 2024-2026). HIGH > LOW di 7 dari 7 tahun. **Dipasang.**
- **Uji ML walk-forward** (4 model, 11 faktor, 2022-2026): selisih HIGH-LOW terbaik ML 0,31R vs label 0,52R.
  **Gagal** mengalahkan label. Diuji ulang otomatis setiap bulan.

## 2026-10-23 · Riset mingguan
- Data lengkap (49 koin). Juara: 2230 trade, +707R, DD 25,7R; rasio R/DD 21,8 (2020-2023) / 8,8 (2024-skrg).
  Replay gerbang no-op identik dengan backtest_crypto.py.
- **#1 Batas posisi searah** (N 4/5/6, varian slot & pos, replay penuh): rasio lama +2% s.d. +46%, baru -20% s.d. -50%,
  DD terburuk turun ke ±15R (slot) tetapi total R -29% s.d. -48%. **Gagal** (periode baru memburuk di semua varian).
- **#2 LOW conviction**: dilewati (replay penuh) rasio -3% / -5%; risiko setengah -1% / +13%, DD 22,9R. **Gagal**
  (tidak +10% di periode lama). Risiko setengah paling dekat lolos.
- Ide baru: #11 SELL LOW dilewati (SELL LOW -0,05R di 2024-2026), #12 batas searah khusus SELL.

## 2026-10-23 · Riset (chat) → dipasang 24 Okt 2026: versi v2
- Pembanding TSMOM 28/1 (Han, Kang & Ryu) long-only & long-short (11 varian, data sama, fee 0,06%/sisi + funding aktual):
  semua kalah dari juara, terutama 2024-skrg. Filter regime TSMOM untuk SELL (A-D) gagal di replay penuh.
- Aturan keluar (replay penuh, net): TP penuh 2-15R, SL impas, batas hold 10/15 hari **gagal**.
  **Cut-loss stagnan** (umur ≥ 2 hari & R < -0,2) **lolos**: rasio R/DD +28% / +39%, 5/6 tahun, tanpa 2% terbaik 2024-skrg -9,1R → +8,3R.
- **TP 25% di 1R** di atas stagnan: win rate 35,9% → 40,7%, Sharpe 1,74 → 1,81, MaxDD ekuitas -16,8% → -13,5% (risiko sama).
- Slot 3/5/7/8/10/12/15 (DD disamakan -16,8%): 10 slot optimal (CAGR 89%); 5 slot 50%.
- **Dipasang atas persetujuan pemilik**: 10 slot + stagnan + TP 25% di 1R, risiko default 1%
  (backtest net: CAGR ±109%, MaxDD -19,7%, 7/7 tahun untung). Replay engine baru identik dengan replay riset (2418 trade).
  baseline.json crypto dibuat ulang; LIVE_START crypto = 24 Okt 2026.

## 2026-10-30 · Review bulanan (Jumat terakhir Okt)
- Data 49 koin (HYPE dilewati backtest: 848 candle). Funding HL ADA/ETC tersimpan kosong oleh unduhan (gagal diam-diam),
  dilengkapi dengan `eksperimen/lengkapi_funding_hl.py`. JST/QNT/NIGHT tidak ada di Hyperliquid.
- Juara v2: 2424 trade, +641,2R, +0,265R/trade, DD 16,3R; rasio 26,9 (2020-2023) / 12,7 (2024-skrg).
  Replay `eksperimen/_replay.py` (gerbang no-op) identik dengan backtest_crypto.py.
- **#3 SELL searah BTC** (A: hanya saat BTC turun, B: blok saat BTC naik; replay penuh): rasio -37%/-40% (A), -8%/-21% (B),
  DD naik ke 23,8R / 17,2R. **Gagal**: SELL yang tersaring untung, slot terisi BUY lebih lemah.
- **#11 SELL LOW dilewati** (replay penuh): rasio -5% / -26%, total R -46R. Risiko 1/2: -1% / +4%. **Gagal**.
  Di mesin v2 SELL LOW +0,11R / +0,02R (tidak lagi negatif).
- Tinjau ulang #2 (LOW risiko 1/2) di v2: -2% / +4%, 4/6 tahun. Tetap gagal.
- Live vs backtest sejak 24 Okt: 6/6 trade tutup identik (+0,306R). Beda slot SUI (backtest) vs NEAR (live) berasal dari
  order HYPE di bot live (backtest tidak memuat HYPE). Bukan masalah eksekusi.
- Label: HIGH > MEDIUM > LOW (semua), HIGH > LOW 7/7 tahun. MEDIUM melemah 2025-2026 (+0,007R vs LOW +0,045R).
- ML walk-forward: label selisih 0,32R (5/5) vs ML terbaik 0,18R (3/5). Belum lebih baik.
- Ide baru: #19 risiko SELL 0,5%, #20 analisis MEDIUM melemah.

## 2026-10-30 · Fondasi riset diperkuat (chat bersama pemilik) · bias koin selamat
Aturan baru: `riset/ATURAN_BERSAMA.md`. Data koin sesuai masanya: `riset/unduh_pit.py` + `riset/pit.py`.
- **Juara v2, daftar tetap vs sesuai masanya** (195 koin termasuk delisting; mesin asli bot, order baru hanya di 50 besar bulan itu):
  semua +0,264R vs +0,208R, R/thn +93 vs +74, DD 16,3 vs 26,4R, rasio 5,69 vs 2,81 ·
  2020-2023 rasio 6,60 vs 3,41 · 2024-skrg R/thn +72 vs +52, DD 16,0 vs 15,3R, rasio 4,47 vs 3,37.
  Per tahun PIT: 2020 +134 · 2021 +98 · 2022 +34 · 2023 +92 · 2024 +92 · 2025 +21 · 2026 +32 (semua positif).
- Koin di luar daftar kini: 725 trade, +0,131R/trade (tetap positif). Trade yang dibuat saat koin BELUM 50 besar (daftar tetap):
  234 trade +0,257R. Bias datang terutama dari prioritas slot berdasarkan peringkat hari ini, bukan koin "mati".
- Kesimpulan: strategi tahan uji, tetapi ekspektasi jujur ±20-28% lebih rendah dan DD bisa ±26R. Angka PIT = patokan ekspektasi.

## 2026-11-06 · Riset mingguan
- Data 49 koin (HYPE dilewati backtest: data kurang). Funding HL bulan berjalan lengkap (kecuali JST/QNT/NIGHT, tidak ada di HL).
  Juara v2: 2435 trade, +641,7R, +0,264R/trade, DD 16,3R; rasio 26,9 (2020-2023) / 12,7 (2024-skrg).
- **Data baru: open interest Binance** (`eksperimen/unduh_oi.py`, arsip harian metrics → OI per jam, 49/49 koin).
  Arsip mulai Des 2021 untuk sebagian besar koin (BTC Sep 2020); 1796 dari 2435 trade juara punya OI 7 hari.
- **#4 OI naik vs turun** (gerbang replay penuh; OI tidak tersedia = izinkan): A OI 7 hari naik (semua) rasio -0%/-59%,
  B OI 7 hari naik (BUY saja) +0%/-55%, C tolak OI 7 hari < -10% +13%/-14% (2/6 tahun), D OI 3 hari naik +3%/-34%.
  Hanya 2022-2023: C +14%, lainnya -8% s.d. +1%. **Gagal** (periode baru memburuk di semua varian).
  Diagnostik tidak konsisten antar horizon: BUY OI 7 hari turun +0,31/+0,54R vs naik +0,23/+0,20R, tetapi OI 3 hari naik lebih baik.
- **#48 [lit] Risiko dikelola volatilitas BTC 30 hari** (Moreira & Muir 2017; ukuran saja, slot tetap): 1/vol rasio -14%/-16%,
  1/vol² -25%/-15%, vol > 1,25x median → 0,5: -9%/-0%, 1/vol batas 0,25-2: -8%/-19%. **Gagal**. Kuartil vol tertinggi
  buruk hanya di 2024-skrg (+0,04R), di 2020-2023 +0,35R.
- Tidak ada ide yang lolos tahap 1 → uji signifikansi dan data terkunci tidak dipakai. Ide baru: #49 (SELL 0,5% bila OI 7 hari turun).

## 2026-11-06 · TAHAP 0 "untung di semua tahun" (permintaan pemilik) → TIDAK LULUS → program TAMBAL-CELAH
- Skrip: `eksperimen/tahap0_semua_tahun.py` (biaya realistis di atas mesin asli), `eksperimen/tahap0_pit.py`, `eksperimen/celah_crypto.py`.
  Biaya REAL: entry stop / SL / stagnan taker 0,05% + slip 0,03%, TP 25% maker 0,02%, funding aktual per settlement
  (Binance, lalu HL setelah arsip habis). Rata-rata per trade: fee 0,019R, funding +0,014R (long +0,025R, short -0,002R);
  KONS (slip 0,10%) fee 0,035R. Nilai posisi per 1R median 10,3x.
- Juara v2 daftar tetap (tahun tutup), kotor → REAL: total 641,7 → 562,8R, DD 16,3 → 17,5R. Per tahun REAL
  2020 +112,5 · 2021 +120,3 · 2022 +50,1 · 2023 +102,8 · 2024 +113,5 · 2025 +25,6 · 2026 +40,8 (s.d. 5 Nov).
  Tanpa 2% trade terbaik per tahun: 74,5 · 62,1 · 24,6 · 41,1 · 26,5 · **-12,6** · 8,1 (global: 2025 -1,1R). KONS: 2025 -18,4R.
  Tahun buka (bukan tutup) memberi kesimpulan sama. Des 2019 (5 trade pemanasan) -2,8R, tidak dihitung tahun.
- Sesuai masanya (226 koin, REAL): total 432,7R, DD 30,8R; per tahun 106,8 · 93,6 · 25,3 · 81,6 · 81,9 · 17,5 · 26,1;
  tanpa 2% terbaik 2022 -1,4 · 2025 -10,0 · 2026 -2,6R. (Pemakaian review bias koin selamat, bukan uji ide.)
- Celah: bukan koin (40/49 koin positif, tanpa 8 koin terbaik tiap tahun tetap positif; 2025 hanya 25/44 koin positif)
  melainkan ekor: 2% trade terbaik = 34-80% R tahunan, 149% di 2025. 2025: BUY +0,15R, SELL 0,00R, MEDIUM -0,05R,
  trade untung rata-rata 0,95R (tahun lain 1,1-1,4R), bulan terburuk Jan -13,2 / Agu -11,8R. ER 20 hari saat entry tidak
  berpola (kuartil 0,17-0,29R).
- **#52 [lit] Efficiency Ratio Kaufman 20 hari ≥ 0,15/0,20/0,25/0,30/0,35** (gerbang replay penuh, R REAL): total 276-399R
  (juara 563), tahun minus tanpa 2% = 1-3 (juara 1), 2025 tanpa 2% -12,1 s.d. -34,1R, 2024 ikut minus. **Gagal**.
- **#53 [lit] ADX(14) harian Wilder ≥ 15/20/25/30**: total 210-488R, tahun minus 0-2, tanpa 2% minus 2 (2025 & 2026). **Gagal**.
  Rasio lama juga turun di semua 9 varian (11,8-20,9 vs 22,5) → tidak ada ambang yang dipilih.
- Total ide crypto yang pernah diuji: ±15 (9 di ide.md termasuk #52, #53, + ±6 kelompok uji fondasi/v2; varian putaran ini: 9). Ide baru: #54 TP lebih awal/lebih besar, #55 strategi pelengkap
  mean-reversion (edge berbeda) untuk tahun berombak.

## 2026-11-06 · Keputusan pemilik: syarat Tahap 0 = setiap tahun R bersih REAL >= +1R → LULUS → program OPTIMASI
- Pemilik menetapkan syarat "semua tahun positif" = tiap tahun kalender R bersih REAL >= +1R (versi "tanpa 2% terbaik" tidak lagi syarat).
- Juara v2: terburuk 2025 +25,6R (daftar tetap), +17,5R (sesuai masanya), +19,7R (KONS) → **LULUS**. PROGRAM UTAMA di PROSEDUR
  diganti menjadi OPTIMASI (syarat penantang: tiap tahun >= +1R, DD naik <= 25%, P >= 0,90, pilih 2020-2023 / uji 2024-skrg).
- Risiko dipantau: peluang tahun minus (bootstrap trade tiap tahun, 20.000x) 2025 9,4% · 2026 1,8% · 2022 0,2% · lainnya 0%.
  Skrip: `tahap0_semua_tahun.py` kini mencetak baris SYARAT dan peluang tahun minus (`lulus`, `p_minus`).
- #54 dan #55 tetap antri, kini sebagai jalur optimasi (a, e).
