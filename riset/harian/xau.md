# Rutinitas harian XAU · Wed 25 Nov 2026 08:06 WIB
Dibuat otomatis oleh riset/harian.py (GitHub Actions). Sesi riset: baca ini, JANGAN ulangi langkahnya kecuali ada GAGAL.

### Unduh Setra OK (0.2 mnt)
```
XAU candle: 11465 mulai 2024-12-16 s.d. 2026-11-25 00:00
```

### Unduh Dukascopy OK (9.0 mnt)
```
XAU Dukascopy candle: 70365 mulai 2015-01-01 s.d. 2026-11-24 23:00
```

### Gabung 2004-skrg OK (0.0 mnt)
```
138602 candle (lama 68237 + baru 70365)
```

### Replay kesetaraan (wajib IDENTIK) OK (0.0 mnt)
```
xau_replay.json: bot 463 trade vs riset 463 (KOMBO 62 MR 238 K6 98 SUS 65) -> IDENTIK
xau_panjang.json: bot 2857 trade vs riset 2857 (KOMBO 419 MR 1268 K6 700 SUS 470) -> IDENTIK
KESIMPULAN: mesin bot = riset baseline
```

### Penyebab SL 7 hari OK (0.0 mnt)
```
Trade 7 hari terakhir: 4 · SL: 3 · total -0.43R
- Fri 20 Nov 07:00 MR BUY entry 3607.19 SL Fri 20 Nov 09:00 -1.00R → CELAH: MR BUY lawan tren H1, ATR rel 1.35, kena SL setelah 2 jam · historis MR lawan tren: SL 30% dari 1134 trade
- Mon 23 Nov 07:00 MR SELL entry 3584.20 SL Mon 23 Nov 21:00 -1.00R → CELAH: MR SELL searah tren H1, ATR rel 1.75, kena SL setelah 14 jam · historis MR searah tren: SL 26% dari 1183 trade
- Tue 24 Nov 07:00 MR BUY entry 3631.66 SL Tue 24 Nov 22:00 -0.92R → CELAH: MR BUY lawan tren H1, ATR rel 1.33, kena SL setelah 15 jam · historis MR lawan tren: SL 30% dari 1134 trade
Ringkasan penyebab SL: CELAH 3
Tindakan: NEWS = aman; LONJAKAN = catat; DATA & CELAH = wajib dianalisa di laporan (pola berulang -> ide baru).
```

### Bayangan (live vs menu) OK (0.1 mnt)
```
Sejak 02 Nov 2026 (biaya 0,40 USD/trade):
  BASELINE (live)    trade  15 · win   33% · total  +0.94R
  Tanpa susulan      trade  14 · win   29% · total  +0.31R
  Tanpa kombinasi (hibrida 6 Nov) trade  15 · win   40% · total  +1.42R
  Tanpa hibrida (#40 saja) trade  15 · win   40% · total  -2.38R
  MR SELL lama 71,22 (sblm #40) trade  16 · win   31% · total  -4.15R
  Connors MA200 (#42) trade  15 · win   40% · total  +1.42R
  Connors MA100 (#42) trade  15 · win   40% · total  +1.42R
  Hibrida MA200 (#42b) trade  15 · win   40% · total  +1.42R
  MR saja            trade  12 · win   25% · total  -4.93R
  K6 saja            trade   5 · win   80% · total  +5.63R
  Juara lama (OCO)   trade  17 · win   53% · total +11.24R
  PENANTANG          trade  15 · win   40% · total  -2.12R
  LIVE (catatan bot) trade  15 · total kotor  +2.98R
```
