# Strategi XAU · juara MULTI-STRATEGI (dipasang 2 Nov 2026)

Status: **LIVE mulai sinyal Senin 2 Nov 2026 07:00 WIB** (`gold_bot.py`, workflow `gold.yml`). Risiko **0,5% per trade** (pilihan pemilik).
Perubahan hanya lewat riset + persetujuan pemilik; mesin bot wajib lolos `riset/replay_xau.py` (identik dengan
`riset/xau/eksperimen/multi_mesin.baseline`). Konstanta strategi ada di `gold_bot.py` (dibaca juga oleh riset).
Riwayat: Gold Daily Straddle OCO 2 sisi (live 18 Okt 2026) → multi-strategi MR + K6 (31 Okt 2026, ide #34).

## Aturan tetap pemilik (tidak boleh diubah)
Sinyal dikirim **07:00 WIB**; semua order & posisi ditutup **23:00 WIB**. Karakter intraday: masuk & selesai di hari yang sama.

## Aturan (maksimal 1 posisi per hari, diputuskan dari candle H1 yang close 07:00 WIB)
**A. Mean reversion (prioritas)** — RSI(2) close H1 (Wilder, alpha 1/2):
- RSI(2) ≤ **43,76** → BUY market; RSI(2) ≥ **71,22** → SELL market (ambang = kuantil 35% / 65% hari 2015-2021).
- Masuk di open candle 07:00-08:00. SL = **3 × ATR(14) H1**. Tanpa TP. Ditutup 23:00 WIB.

**B. Breakout searah tren (K6)** — hanya bila RSI(2) tidak ekstrem:
- Range = high & low 3 candle H1 (04:00-07:00 WIB). Tren = close 07:00 vs **EMA200 H1**.
- Tren naik → BUY STOP di high range, batas batal = low range; tren turun → SELL STOP di low range, batas batal = high range.
- Batas batal tersentuh lebih dulu → order dibatalkan, hari itu tanpa trade. SL = 1,5 × ATR(14) H1, TP = 4R.
- Candle H1 yang menyentuh keduanya: mesin menganggap sisi BUY duluan (ide #23 untuk perbaikan).
- Order diabaikan bila jarak SL ≤ 0,5 USD.

## Ekspektasi (bersih biaya 0,40 USD; urutan candle ambigu M1 untuk 2022-skrg; risiko 0,5%)
| Periode | Trade/mg | MR / K6 | Win | RR | PF | R/thn | DD R | DD% | CAGR | W/L maks | Tahun+ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2015-2021 | 4,2 | 1.256 / 252 | 47% | 1,16 | 1,03 | +2,9 | 23 | 11,7% | +1,1% | 7/8 | 5/7 |
| 2022 - Jan 2025 | 4,3 | 571 / 115 | 45% | 1,33 | 1,10 | +9,9 | 37 | 17,2% | +4,7% | 9/8 | 3/4 |
| Feb 2025 - Okt 2026 | 4,3 | 350 / 41 | 48% | 1,28 | 1,17 | +15,6 | 17 | 8,1% | +7,8% | 10/6 | 2/2 |
| 12 tahun | 4,2 | 2.177 / 408 | 47% | 1,22 | 1,07 | +6,6 | 37 | 17,2% | +3,0% | 10/8 | 9/12 |

Per tahun (R): 2015 +2 · 2016 +3 · 2017 +10 · 2018 -4 · 2019 -5 · 2020 +4 · 2021 +10 · 2022 +28 · 2023 -24 · 2024 +24 · 2025 +16 · 2026 +14.
Per strategi (12 thn): MR win 49%, RR 1,11, PF 1,06 · K6 win 37%, RR 1,96, PF 1,13. ±84% trade berasal dari MR.

**Catatan jujur**: aturan dirakit setelah melihat semua periode (ide #34) → belum terbukti di data baru; edge tipis (PF 1,07).
Penyetelan 324 kombinasi tidak menghasilkan versi yang signifikan lebih baik (P ≤ 0,56). Catatan bayangan semua strategi menu:
`python riset/xau/bayangan.py . <xau.json> <xau_panjang.json>` (dipakai riset Jumat untuk uji maju).
