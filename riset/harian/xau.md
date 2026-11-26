# Rutinitas harian XAU · Thu 26 Nov 2026 07:41 WIB
Dibuat otomatis oleh riset/harian.py (GitHub Actions). Sesi riset: baca ini, JANGAN ulangi langkahnya kecuali ada GAGAL.

### Unduh Setra OK (0.3 mnt)
```
XAU candle: 11465 mulai 2024-12-17 s.d. 2026-11-25 23:00
```

### Unduh Dukascopy GAGAL (30.0 mnt)
```
WAKTU HABIS setelah 1800 detik
```

### Gabung 2004-skrg OK (0.0 mnt)
```
138624 candle (lama 68237 + baru 70387)
```

### Replay kesetaraan (wajib IDENTIK) OK (0.0 mnt)
```
xau_replay.json: bot 463 trade vs riset 463 (KOMBO 62 MR 238 K6 98 SUS 65) -> IDENTIK
xau_panjang.json: bot 2842 trade vs riset 2842 (KOMBO 416 MR 1259 K6 698 SUS 469) -> IDENTIK
KESIMPULAN: mesin bot = riset baseline
```

### Penyebab SL 7 hari OK (0.0 mnt)
```
Trade 7 hari terakhir: 4 · SL: 4 · total -3.92R
- Fri 20 Nov 07:00 MR BUY entry 3607.19 SL Fri 20 Nov 09:00 -1.00R → CELAH: MR BUY lawan tren H1, ATR rel 1.35, kena SL setelah 2 jam · historis MR lawan tren: SL 30% dari 1134 trade
- Mon 23 Nov 07:00 MR SELL entry 3584.20 SL Mon 23 Nov 21:00 -1.00R → CELAH: MR SELL searah tren H1, ATR rel 1.75, kena SL setelah 14 jam · historis MR searah tren: SL 26% dari 1183 trade
- Tue 24 Nov 07:00 MR BUY entry 3631.66 SL Tue 24 Nov 22:00 -0.92R → CELAH: MR BUY lawan tren H1, ATR rel 1.33, kena SL setelah 15 jam · historis MR lawan tren: SL 30% dari 1134 trade
- Wed 25 Nov 07:00 K6 SELL entry 3546.55 SL Wed 25 Nov 09:00 -1.00R → CELAH: K6 SELL searah tren H1, ATR rel 1.11, kena SL setelah 2 jam · historis K6 searah tren: SL 55% dari 1226 trade
Ringkasan penyebab SL: CELAH 4
Tindakan: NEWS = aman; LONJAKAN = catat; DATA & CELAH = wajib dianalisa di laporan (pola berulang -> ide baru).
```

### Bayangan (live vs menu) OK (0.1 mnt)
```
Sejak 02 Nov 2026 (biaya 0,40 USD/trade):
  BASELINE (live)    trade  16 · win   31% · total  -0.08R
  Tanpa susulan      trade  15 · win   27% · total  -0.71R
  Tanpa kombinasi (hibrida 6 Nov) trade  16 · win   38% · total  +0.41R
  Tanpa hibrida (#40 saja) trade  15 · win   40% · total  -3.34R
  MR SELL lama 71,22 (sblm #40) trade  16 · win   31% · total  -5.11R
  Connors MA200 (#42) trade  16 · win   38% · total  +0.41R
  Connors MA100 (#42) trade  16 · win   38% · total  +0.41R
  Hibrida MA200 (#42b) trade  16 · win   38% · total  +0.41R
  MR saja            trade  12 · win   25% · total  -4.93R
  K6 saja            trade   6 · win   67% · total  +4.61R
  Juara lama (OCO)   trade  18 · win   50% · total +10.23R
  PENANTANG          trade  15 · win   40% · total  -3.07R
  LIVE (catatan bot) trade  16 · total kotor  +1.98R
```
