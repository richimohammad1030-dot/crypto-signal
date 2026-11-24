# Rutinitas harian XAU · Tue 24 Nov 2026 10:04 WIB
Dibuat otomatis oleh riset/harian.py (GitHub Actions). Sesi riset: baca ini, JANGAN ulangi langkahnya kecuali ada GAGAL.

### Unduh Setra OK (0.2 mnt)
```
XAU candle: 11465 mulai 2024-12-13 s.d. 2026-11-24 02:00
```

### Unduh Dukascopy OK (13.8 mnt)
```
XAU Dukascopy candle: 70342 mulai 2015-01-01 s.d. 2026-11-23 23:00
```

### Gabung 2004-skrg OK (0.0 mnt)
```
138581 candle (lama 68237 + baru 70344)
```

### Replay kesetaraan (wajib IDENTIK) OK (0.0 mnt)
```
xau_replay.json: bot 463 trade vs riset 463 (KOMBO 62 MR 238 K6 98 SUS 65) -> IDENTIK
xau_panjang.json: bot 2856 trade vs riset 2856 (KOMBO 419 MR 1267 K6 700 SUS 470) -> IDENTIK
KESIMPULAN: mesin bot = riset baseline
```

### Penyebab SL 7 hari OK (0.0 mnt)
```
Trade 7 hari terakhir: 4 · SL: 2 · total +4.49R
- Fri 20 Nov 07:00 MR BUY entry 3607.19 SL Fri 20 Nov 09:00 -1.00R → CELAH: MR BUY lawan tren H1, ATR rel 1.35, kena SL setelah 2 jam · historis MR lawan tren: SL 30% dari 1134 trade
- Mon 23 Nov 07:00 MR SELL entry 3584.20 SL Mon 23 Nov 21:00 -1.00R → CELAH: MR SELL searah tren H1, ATR rel 1.75, kena SL setelah 14 jam · historis MR searah tren: SL 26% dari 1183 trade
Ringkasan penyebab SL: CELAH 2
Tindakan: NEWS = aman; LONJAKAN = catat; DATA & CELAH = wajib dianalisa di laporan (pola berulang -> ide baru).
```

### Bayangan (live vs menu) OK (0.1 mnt)
```
Sejak 02 Nov 2026 (biaya 0,40 USD/trade):
  BASELINE (live)    trade  15 · win   40% · total  +1.99R
  Tanpa susulan      trade  14 · win   36% · total  +1.36R
  Tanpa kombinasi (hibrida 6 Nov) trade  15 · win   47% · total  +2.48R
  Tanpa hibrida (#40 saja) trade  14 · win   50% · total  -1.28R
  MR SELL lama 71,22 (sblm #40) trade  15 · win   40% · total  -3.05R
  Connors MA200 (#42) trade  15 · win   47% · total  +2.48R
  Connors MA100 (#42) trade  15 · win   47% · total  +2.48R
  Hibrida MA200 (#42b) trade  15 · win   47% · total  +2.48R
  MR saja            trade  12 · win   33% · total  -3.88R
  K6 saja            trade   5 · win   80% · total  +5.63R
  Juara lama (OCO)   trade  16 · win   56% · total +12.25R
  PENANTANG          trade  14 · win   50% · total  -0.90R
  LIVE (catatan bot) trade  14 · total kotor  +3.90R
```
