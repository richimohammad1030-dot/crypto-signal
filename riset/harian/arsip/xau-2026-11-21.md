# Rutinitas harian XAU · Sat 21 Nov 2026 05:49 WIB
Dibuat otomatis oleh riset/harian.py (GitHub Actions). Sesi riset: baca ini, JANGAN ulangi langkahnya kecuali ada GAGAL.

### Unduh Setra OK (0.3 mnt)
```
XAU candle: 11471 mulai 2024-12-12 s.d. 2026-11-20 21:00
```

### Unduh Dukascopy OK (20.8 mnt)
```
XAU Dukascopy candle: 70296 mulai 2015-01-01 s.d. 2026-11-19 23:00
```

### Gabung 2004-skrg OK (0.0 mnt)
```
138554 candle (lama 68237 + baru 70317)
```

### Replay kesetaraan (wajib IDENTIK) OK (0.0 mnt)
```
xau_replay.json: bot 463 trade vs riset 463 (KOMBO 62 MR 237 K6 98 SUS 66) -> IDENTIK
xau_panjang.json: bot 2854 trade vs riset 2854 (KOMBO 419 MR 1265 K6 700 SUS 470) -> IDENTIK
KESIMPULAN: mesin bot = riset baseline
```

### Penyebab SL 7 hari OK (0.0 mnt)
```
Trade 7 hari terakhir: 5 · SL: 1 · total +6.08R
- Fri 20 Nov 07:00 MR BUY entry 3607.19 SL Fri 20 Nov 09:00 -1.00R → CELAH: MR BUY lawan tren H1, ATR rel 1.35, kena SL setelah 2 jam · historis MR lawan tren: SL 30% dari 1133 trade
Ringkasan penyebab SL: CELAH 1
Tindakan: NEWS = aman; LONJAKAN = catat; DATA & CELAH = wajib dianalisa di laporan (pola berulang -> ide baru).
```

### Bayangan (live vs menu) OK (0.1 mnt)
```
Sejak 02 Nov 2026 (biaya 0,40 USD/trade):
  BASELINE (live)    trade  13 · win   38% · total  +2.87R
  Tanpa susulan      trade  12 · win   33% · total  +2.24R
  Tanpa kombinasi (hibrida 6 Nov) trade  13 · win   46% · total  +3.36R
  Tanpa hibrida (#40 saja) trade  12 · win   50% · total  -0.40R
  MR SELL lama 71,22 (sblm #40) trade  13 · win   38% · total  -2.17R
  Connors MA200 (#42) trade  13 · win   46% · total  +3.36R
  Connors MA100 (#42) trade  13 · win   46% · total  +3.36R
  Hibrida MA200 (#42b) trade  13 · win   46% · total  +3.36R
  MR saja            trade  10 · win   30% · total  -3.00R
  K6 saja            trade   5 · win   80% · total  +5.63R
  Juara lama (OCO)   trade  15 · win   53% · total +10.44R
  PENANTANG          trade  12 · win   50% · total  -0.05R
  LIVE (catatan bot) trade  13 · total kotor  +4.90R
```
