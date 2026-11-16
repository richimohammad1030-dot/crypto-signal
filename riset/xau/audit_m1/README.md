# Audit simulasi XAU per menit (16 Nov 2026)

Menguji ulang trade bot XAU live (KOMBO/MR/K6/SUSULAN) memakai candle M1 Dukascopy BID 2020 - Okt 2026, sinyal & parameter
sama dengan `multi_mesin.py`. Jalankan: `M1DIR=<folder xau_m1_*.csv.gz> python cmp1.py` (juga `grid.py`, `stats.py`).
Data M1 ada di branch `claude/data-xau-m1`.

Hasil:
- Mesin H1 identik dengan laporan (2005-2026 +17,2R/thn). Per menit: arah trade sama 100%, selisih rata-rata 0,003R/trade;
  total +142R vs +154R (H1 optimis ±8%, hampir semua dari hari K6 dua sisi dalam satu candle).
- Stres eksekusi 2020-2026: spread 0,30 +23,6R/thn; + slip SL 0,20 + telat 5 mnt +21R/thn; spread 0,50 + slip 0,30 + telat 10 mnt +14R/thn.
- Edge ±0,07R/trade; biaya flat 0,80 USD menghapus edge di 2005-2021 (tetap +21R/thn di 2022-2026).
- 2005-2014 (paling bersih): +12,7R/thn, CI95 +0,9..+24,8, 4/10 tahun minus.

PENTING data M1: bulan musim panas AS dari HistData bergeser +1 jam (EST tanpa DST). `data.load_m1_fixed()` memperbaikinya
dengan mencocokkan tiap bulan ke H1 Dukascopy repo. Riset momentum memakai data yang belum dikoreksi.
