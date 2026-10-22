# Jurnal riset

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
- **Backtest XAU** (Feb 2025 - Okt 2026): 425 trade, win rate 41%, +0,18R/trade kotor (+0,16R setelah biaya 0,40 USD),
  drawdown terburuk 14,1R. Histori sumber data hanya tersedia sejak Feb 2025.

## 2026-10-23 · Riset mingguan
- Data lengkap (49 koin, XAU s.d. 22 Okt). Juara crypto: 2230 trade, +707R, DD 25,7R; rasio R/DD 21,8 (2020-2023) / 8,8 (2024-skrg).
  Replay gerbang no-op identik dengan backtest_crypto.py.
- **#1 Batas posisi searah** (N 4/5/6, varian slot & pos, replay penuh): rasio lama +2% s.d. +46%, baru -20% s.d. -50%,
  DD terburuk turun ke ±15R (slot) tetapi total R -29% s.d. -48%. **Gagal** (periode baru memburuk di semua varian).
- **#2 LOW conviction**: dilewati (replay penuh) rasio -3% / -5%; risiko setengah -1% / +13%, DD 22,9R. **Gagal**
  (tidak +10% di periode lama). Risiko setengah paling dekat lolos.
- Ide baru: #11 SELL LOW dilewati (SELL LOW -0,05R di 2024-2026), #12 batas searah khusus SELL.
