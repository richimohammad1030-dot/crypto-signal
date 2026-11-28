# Rutinitas harian XAU · Sat 28 Nov 2026 07:15 WIB
Dibuat otomatis oleh riset/harian.py (GitHub Actions). Sesi riset: baca ini, JANGAN ulangi langkahnya kecuali ada GAGAL.

### Unduh Setra OK (0.3 mnt)
```
XAU candle: 11453 mulai 2024-12-19 s.d. 2026-11-27 21:00
```

### Unduh Dukascopy OK (19.0 mnt)
```
XAU Dukascopy candle: 70429 mulai 2015-01-01 s.d. 2026-11-27 19:00
```

### Gabung 2004-skrg OK (0.0 mnt)
```
138659 candle (lama 68237 + baru 70422)
```

### Replay kesetaraan (wajib IDENTIK) OK (0.1 mnt)
```
xau_replay.json: bot 482 trade vs riset 482 (KOMBO 7 MR 28 K6 14 SUS 16 OCO 417) -> IDENTIK
xau_panjang.json: bot 2878 trade vs riset 2878 (KOMBO 367 MR 1060 K6 617 SUS 421 OCO 413) -> IDENTIK
KESIMPULAN: mesin bot = riset baseline
```

### Penyebab SL 7 hari OK (0.0 mnt)
```
Trade 7 hari terakhir: 4 · SL: 4 · total -3.92R
- Mon 23 Nov 07:00 MR SELL entry 3584.20 SL Mon 23 Nov 21:00 -1.00R → DATA: replay: tidak ada trade
- Tue 24 Nov 07:00 MR BUY entry 3631.66 SL Tue 24 Nov 22:00 -0.92R → CELAH: MR BUY lawan tren H1, ATR rel 1.33, kena SL setelah 15 jam · historis MR lawan tren: SL 30% dari 1130 trade
- Wed 25 Nov 07:00 K6 SELL entry 3546.55 SL Wed 25 Nov 09:00 -1.00R → DATA: replay: tidak ada trade
- Fri 27 Nov 09:00 SUS SELL entry 3594.16 SL Fri 27 Nov 12:00 -1.00R → DATA: replay: tidak ada trade
Ringkasan penyebab SL: DATA 3, CELAH 1
Tindakan: NEWS = aman; LONJAKAN = catat; DATA & CELAH = wajib dianalisa di laporan (pola berulang -> ide baru).
```

### Bayangan (live vs menu) OK (0.1 mnt)
```
Sejak 02 Nov 2026 (biaya 0,40 USD/trade):
  LIVE v2 (sejak 30 Nov 2026) trade  20 · win   60% · total +16.64R
  Mesin dasar (KOMBO SL 2,0, tanpa lapisan v2) trade  18 · win   44% · total  +4.43R
  Tanpa susulan      trade  13 · win   46% · total  +5.17R
  Tanpa kombinasi (hibrida 6 Nov) trade  17 · win   47% · total  +5.77R
  Tanpa hibrida (#40 saja) trade  18 · win   39% · total  -3.06R
  MR SELL lama 71,22 (sblm #40) trade  18 · win   33% · total  -3.47R
  Connors MA200 (#42) trade  17 · win   47% · total  +5.77R
  Connors MA100 (#42) trade  17 · win   47% · total  +5.77R
  Hibrida MA200 (#42b) trade  17 · win   47% · total  +5.77R
  MR saja            trade  10 · win   30% · total  -2.47R
  K6 saja            trade   6 · win   83% · total  +8.63R
  Juara lama (OCO)   trade  20 · win   60% · total +16.64R
  KANDIDAT X010 rezim (27 Nov) trade  18 · win   44% · total  +7.30R
  KANDIDAT X010 + OCO adaptif (27 Nov) trade  20 · win   60% · total +16.64R
  KANDIDAT #93v2 tanpa OCO (P 0,93) trade  18 · win   44% · total  +6.11R
  KANDIDAT #93v2 + OCO adaptif trade  20 · win   60% · total +16.64R
  PENANTANG          trade  18 · win   39% · total  +1.90R
  LIVE (catatan bot) trade  17 · total kotor  +0.98R
```
