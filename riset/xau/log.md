# Jurnal riset · XAU

Catatan setiap ide yang diuji: tanggal, ide, angka utama, keputusan. Ide yang gagal tidak diuji ulang
kecuali ada data baru yang relevan.

## 2026-10-20 · Fondasi
- **Backtest XAU** (Feb 2025 - Okt 2026): 425 trade, win rate 41%, +0,18R/trade kotor (+0,16R setelah biaya 0,40 USD),
  drawdown terburuk 14,1R. Histori sumber data hanya tersedia sejak Feb 2025.

## 2026-10-23 · Pemisahan riset
- Riset XAU dipisah dari crypto: routine, prosedur, daftar ide, jurnal, dan laporan sendiri.
  Kriteria lolos disesuaikan dengan data XAU yang hanya ±20 bulan (lihat riset/xau/PROSEDUR.md).

## 2026-10-30 · Review bulanan Oktober
- **Juara** (Feb 2025 - 29 Okt 2026, bersih biaya 0,40 USD): 433 trade, +66,4R, +0,153R/trade, win 41%, DD 15,2R, R/DD 4,37.
  P1 2025 R/DD 1,81; P2 2026 R/DD 3,22. 2026Q4 sejauh ini -1,1R (21 trade). Keluar: SL 55%, TP 7%, tutup 23:00 38% (+1,17R kotor).
- **Live vs backtest** sejak 18 Okt 2026: 9 trade, sisi dan R identik 9/9 (total -0,74R kotor).
- **#5 Filter lebar range/ATR** (ambang kuantil 20/80% dari 2025): lewati sempit R/DD 1,81→1,68 dan 3,22→2,71; lewati lebar
  1,95 dan 2,87; keduanya 1,58 dan 1,15. **GAGAL**: ujung distribusi tetap untung, kalah di 4-6 dari 7 kuartal.
  Zona 0,88-1,06 negatif di kedua paruh → ide baru #18 (prioritas rendah).
- **#13 Sisi searah tren** (EMA200/100/50 H1; satu sisi atau lawan tren risiko 1/2): EMA200 satu sisi R/DD 1,03 / 3,19;
  terbaik EMA50 lawan tren 1/2 3,17 / 3,69 tapi hanya tidak lebih buruk di 3/7 kuartal. **GAGAL**; sensitif terhadap periode EMA.
- Kandidat penantang: tidak ada. Usulan menunggu persetujuan: tidak ada.

## 2026-10-30 · Data terkunci Dukascopy 2015-2026 (fondasi riset diperkuat, chat bersama pemilik)
Sumber: `riset/unduh_xau_panjang.py` (Dukascopy BID, 69.952 candle H1, Jan 2015 - Okt 2026). Validasi vs Setra (Feb 2025-skrg):
418 dari 433 trade sama waktu buka, arah hasil sama 99%; hasil +68,7R vs +66,4R (bersih). Data Dukascopy setara data bot.
- **Juara di 2015 - Jan 2025 (data terkunci): RUGI.** 2.579 trade, win 34,4%, -0,061R/trade bersih, total -157R, DD 222R.
  Per tahun (R bersih): 2015 -26 · 2016 -38 · 2017 -28 · 2018 -38 · 2019 -35 · 2020 +3 · 2021 -14 · 2022 +5 · 2023 -25 ·
  2024 +20 · 2025 +48 · 2026 +38. Positif hanya 5 dari 12 tahun.
- Kotor (tanpa biaya) 2015-2023 ±0 (-0,06 s.d. +0,08R/trade); biaya tetap 0,40 USD = 0,08-0,12R saat r0 hanya 3-5 USD.
  Edge muncul saat volatilitas emas tinggi: r0/harga 0,44% (2025) dan 0,62% (2026) vs 0,26-0,40% sebelumnya;
  2024 (+0,126R kotor) dan 2020/2022 juga relatif lebih baik.
- Kesimpulan: edge juara XAU kemungkinan besar bergantung pada rezim volatilitas tinggi 2024-2026 (reli emas), bukan permanen.
  Ide baru #21 (filter rezim volatilitas, prioritas 1). Hasil periode Setra tetap dipakai sebagai uji utama; data terkunci untuk
  konfirmasi sesuai ATURAN_BERSAMA (filter #21 boleh dirancang dengan alasan ekonomi, lalu dicek sekali di 2015 - Jan 2025).
