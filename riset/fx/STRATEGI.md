# Strategi juara · FX MAJOR (live uji maju sejak 20 Nov 2026)

Disetujui pemilik 20 Nov 2026 (riset `forex_major/riset_putaran1-7.py`). Mesin live = `forex_major/fx_live.py`
(fungsi backtest yang sama → live identik dengan riset). Bot: `fx_bot.py`, workflow `.github/workflows/fx.yml`.

## Aturan tetap pemilik (jangan diusulkan berubah)
- Intraday: sinyal UTAMA **07:00 WIB**, semua order/posisi ditutup **23:00 WIB**.
- 3 bot dengan karakter berbeda yang saling menutup celah (bukan 3 varian satu mesin):
  UTAMA (07:00) → SUSULAN (bila UTAMA tidak terisi, jam keputusan setelah kadaluarsa s/d 21:00) → bot ke-3 tindak lanjut.
- Pair: EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, USDCHF, NZDUSD. Risiko 0,75%/posisi (variabel repo `FX_RISK_PCT`).
- Syarat pemilik: ≥ 4 trade/minggu, tanpa tahun minus, pertumbuhan > 10%/thn, WR ≥ 35-40%, PF > 1, beruntun tidak timpang.

## Juara
| Bot | Kapan | Aturan |
|---|---|---|
| UTAMA | 07:00 WIB Selasa-Jumat | Buy stop di high minggu lalu, sell stop di low minggu lalu (OCO per pair; sisi yang levelnya sudah tertembus kemarin tidak dipasang). SL 0,3 × ATR(14) D1, TP 0,6 × ATR, SL ke entry di +0,5R. Berlaku s/d 14:00 WIB. Maks 2 posisi/hari, 1/pair, maks 2 searah USD. |
| SUSULAN | candle close 15:00 WIB | Pair yang UTAMA-nya tidak terisi: pasang ulang level minggu lalu yang belum tertembus hari itu (OCO), SL 0,3 ATR, TP 0,8 ATR, s/d 23:00 WIB. |
| LANJUT | setelah UTAMA/SUSULAN kena TP sebelum 20:00 WIB | Market searah di candle berikutnya, SL 0,4 ATR, TP 0,3 ATR. |

Senin: tanpa sinyal (breakout level minggu lalu di hari Senin terbukti sering palsu).

## Bukti (Dukascopy H1 2015-2026, spread Exness Standard Cent + 0,2 pip)
- Gabungan 3 bot: PF 1,27 (IS 2015-22 1,33 · OOS 2023-26 1,17 · Setra 2025-26 lolos), +226R, DD 36R, WR 42%, 3,4 trade/mgg,
  10/12 tahun plus, terburuk −8R. ±9,5%/thn di 0,5% → ±14%/thn di 0,75%.
- Per bot (R rata-rata/trade · WR): UTAMA +0,07 · 22% (sisanya banyak impas BE) · SUSULAN +0,12 · 48% · LANJUT +0,14 · 66%.
- M5 Dukascopy 2020-2026 (4 pair): H1 sedikit optimis (PF H1 1,39 vs M5 1,30 untuk varian sejenis) → angka H1 = batas atas.
- Uji pair baru (USDCAD/NZDUSD tidak dipakai menyetel versi awal): lemah → edge breakout mingguan tidak sama kuat di semua pair.

## Yang sudah GAGAL (jangan diuji ulang tanpa data/definisi baru)
Asian breakout, Trinity H4, NR/ORB Crabel, turtle soup harian & mingguan, squeeze BB/KC, trend pullback, momentum London,
RSI2 (harian & H1, termasuk susulan gaya XAU 0/192), fade NY, momentum kemarin, Donchian 2-20 hari, fade Senin, musiman jam
(Breedon-Ranaldo), PENGISI hari tanpa entry (fade Asia, balik ke tengah range), BALAS setelah SL (0/48 & 0/58; PF ≈ 1,0).

## Label conviction (24 Nov 2026, di pesan sinyal)
Skor = rezim tenang (ATR14/ATR100 D1 < 0,9) +1 · berlawanan tren besar (sisi order vs close kemarin terhadap EMA200 D1) +1 ·
pair (EURUSD/USDJPY +1, USDCAD −1). HIGH ≥ 2 · MEDIUM 1 · LOW ≤ 0 (`forex_major/fx_live.conviction`).
R/trade IS 2015-22 / OOS 2023-26 (semua bot): HIGH +0,24/+0,20 · MEDIUM +0,15/+0,04 · LOW +0,01/−0,04 (29/40/31% sinyal).
Catatan jujur: faktor pair ikut melihat OOS → label = kualitas historis, bukan filter. Semua sinyal tetap dikirim.
