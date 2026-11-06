# Strategi XAU · juara MULTI-STRATEGI HIBRIDA (dipasang 2 Nov 2026; + susulan, MR SELL ≥ 85, hibrida tren harian sejak 6 Nov 2026)

Status: **LIVE mulai sinyal Senin 2 Nov 2026 07:00 WIB** (`gold_bot.py`, workflow `gold.yml`). Risiko **0,5% per trade** (pilihan pemilik).
Perubahan hanya lewat riset + persetujuan pemilik; mesin bot wajib lolos `riset/replay_xau.py` (identik dengan
`riset/xau/eksperimen/multi_mesin.baseline`). Konstanta strategi ada di `gold_bot.py` (dibaca juga oleh riset).
Riwayat: Gold Daily Straddle OCO 2 sisi (live 18 Okt 2026) → multi-strategi MR + K6 (31 Okt 2026, ide #34) → + susulan
(ide #37, live 6 Nov 2026, pilihan pemilik: pasang langsung).

## Aturan tetap pemilik (tidak boleh diubah)
Sinyal dikirim **07:00 WIB**; semua order & posisi ditutup **23:00 WIB**. Karakter intraday: masuk & selesai di hari yang sama.

## Aturan (maksimal 1 posisi per hari, diputuskan dari candle H1 yang close 07:00 WIB)
**A. Mean reversion (prioritas)** — RSI(2) close H1 (Wilder, alpha 1/2):
- RSI(2) ≤ **43,76** → BUY market (kuantil 35% hari 2015-2021); RSI(2) ≥ **85** → SELL market (sejak 6 Nov 2026, ide #40;
  sebelumnya 71,22 = kuantil 65%). Hari RSI(2) 71,22–85 (jenuh beli ringan, SELL-nya lemah di 3 periode) → K6.
- Masuk di open candle 07:00-08:00. SL = **3 × ATR(14) H1**. Tanpa TP. Ditutup 23:00 WIB.

**A'. Hibrida tren harian (ide #42b, sejak 6 Nov 2026)** — tren harian = close H1 07:00 vs **SMA 100 close 07:00** terakhir:
- Tren NAIK (atau riwayat < 100 hari): ambang A di atas (BUY ≤ 43,76, SELL ≥ 85).
- Tren TURUN: cermin Connors — **SELL bila RSI(2) ≥ 70**, BUY hanya bila RSI(2) ≤ **15**. SL/keluar sama dengan A.
- Riwayat close 07:00 disimpan bot di `gold_state.json` (`c07`, 150 hari) dengan bibit `gold_c07_seed.json` (Setra Feb 2025 - Okt 2026).
- Sumber: Connors & Alvarez (2008) RSI(2) + filter MA panjang dan cerminnya untuk short.

**B. Breakout searah tren (K6)** — hanya bila RSI(2) tidak ekstrem:
- Range = high & low 3 candle H1 (04:00-07:00 WIB). Tren = close 07:00 vs **EMA200 H1**.
- Tren naik → BUY STOP di high range, batas batal = low range; tren turun → SELL STOP di low range, batas batal = high range.
- Batas batal tersentuh lebih dulu → order dibatalkan, hari itu tanpa trade. SL = 1,5 × ATR(14) H1, TP = 4R.
- Candle H1 yang menyentuh keduanya: mesin menganggap sisi BUY duluan (ide #23 untuk perbaikan).
- Order diabaikan bila jarak SL ≤ 0,5 USD.

**C. Susulan (ide #37)** — hanya pada hari K6 dilewati (batas batal tersentuh lebih dulu):
- Satu kali keputusan di candle H1 pertama yang close **09:00/11:00/.../21:00 WIB** sejak batas batal tersentuh (= jam run bot).
- RSI(2) ≤ **25,41** → BUY market; ≥ **77,10** → SELL market (kuantil 35%/65% jam keputusan 2015-2021). Tidak ekstrem → tanpa trade.
- Masuk di open candle berikutnya. SL = **3 × ATR(14) H1** (ATR candle keputusan), **TP = 1R**. Ditutup 23:00 WIB.
- Jam sinyal 07:00 tetap: susulan hanya pengganti di hari yang order 07:00-nya batal; tetap maks 1 posisi/hari.

## Data & keterlambatan (live saja; tidak memengaruhi backtest/replay)
- Data utama Setra. Candle di jam pasar tutup/istirahat (17:00 ET, akhir pekan; waktu New York) dibuang (ide #47).
- Candle terakhir > 2 jam di hari bursa → cadangan Dukascopy (BID) + peringatan ke pemilik. Sejak 6 Nov 2026 (ide #47) 48 jam
  terakhir Setra DIGANTI Dukascopy (bukan hanya disambung), candle cadangan dicatat di state `cad_log`, dan pesan sinyal diberi tanda.
- Candle 07:00 baru diproses ≥ 10:00 WIB → sinyal hari itu TERLAMBAT: tidak dikirim sebagai order dan tidak dicatat.
- Candle keputusan susulan baru diproses ≥ 1 jam setelah close (candle masuk sudah lewat) → susulan TERLAMBAT, tidak dicatat.

## Ekspektasi (bersih biaya 0,40 USD; urutan candle ambigu M1 untuk 2022-skrg; risiko 0,5%)
| Periode | Trade/mg | MR / K6 | Win | RR | PF | R/thn | DD R | DD% | CAGR | W/L maks | Tahun+ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2015-2021 | 4,2 | 1.256 / 252 | 47% | 1,16 | 1,03 | +2,9 | 23 | 11,7% | +1,1% | 7/8 | 5/7 |
| 2022 - Jan 2025 | 4,3 | 571 / 115 | 45% | 1,33 | 1,10 | +9,9 | 37 | 17,2% | +4,7% | 9/8 | 3/4 |
| Feb 2025 - Okt 2026 | 4,3 | 350 / 41 | 48% | 1,28 | 1,17 | +15,6 | 17 | 8,1% | +7,8% | 10/6 | 2/2 |
| 12 tahun | 4,2 | 2.177 / 408 | 47% | 1,22 | 1,07 | +6,6 | 37 | 17,2% | +3,0% | 10/8 | 9/12 |

Per tahun (R): 2015 +2 · 2016 +3 · 2017 +10 · 2018 -4 · 2019 -5 · 2020 +4 · 2021 +10 · 2022 +28 · 2023 -24 · 2024 +24 · 2025 +16 · 2026 +14.
Per strategi (12 thn): MR win 49%, RR 1,11, PF 1,06 · K6 win 37%, RR 1,96, PF 1,13. ±84% trade berasal dari MR.

**VERSI LIVE sejak 6 Nov 2026 (susulan + #40 + HIBRIDA #42b)** — bersih biaya, urutan ambigu M1, risiko 0,5%:
| Periode | Trade/mg | MR / K6 / SUS | Win | RR | PF | R/thn | DD R | DD% | CAGR | W/L maks | Tahun+ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2015-2021 | 4,6 | 874 / 450 / 321 | 47% | 1,21 | 1,09 | +9,4 | 23 | 11,1% | +4,4% | 8/10 | 5/7 |
| 2022 - Jan 2025 | 4,6 | 412 / 207 / 125 | 48% | 1,36 | 1,28 | +28,6 | 24 | 11,6% | +14,8% | 14/9 | 3/4 |
| Feb 2025 - Okt 2026 | 4,7 | 262 / 97 / 67 | 48% | 1,33 | 1,22 | +23,2 | 17 | 8,2% | +11,8% | 8/7 | 2/2 |
| 12 tahun | 4,6 | 1.548 / 754 / 513 | 48% | 1,27 | 1,16 | +16,5 | 28 | 13,4% | +8,2% | 14/10 | 9/12 |

Per tahun (R): 2015 +18 · 2016 +21 · 2017 +26 · 2018 -7 · 2019 +14 · 2020 +2 · 2021 -8 · 2022 +46 · 2023 -1 · 2024 +34 · 2025 +35 · 2026 +14.
Catatan jujur #42b: dipilih di 2015-2021 dari 12 varian; P uji 0,68 dan P Setra 0,86 (di bawah syarat 0,90); 2018 & 2021 lebih
buruk dari versi #40. Bayangan "Tanpa hibrida (#40 saja)" dan "Hibrida MA200" memantau alternatifnya.

**Versi 6 Nov pagi (susulan + ide #40 MR SELL ≥ 85, tanpa hibrida)** — bersih biaya, urutan ambigu M1, risiko 0,5%:
| Periode | Trade/mg | MR / K6 / SUS | Win | RR | PF | R/thn | DD R | DD% | CAGR | W/L maks | Tahun+ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2015-2021 | 4,6 | 894 / 425 / 328 | 48% | 1,19 | 1,11 | +10,4 | 20 | 9,6% | +5,0% | 12/10 | 4/7 |
| 2022 - Jan 2025 | 4,6 | 435 / 192 / 117 | 48% | 1,36 | 1,24 | +24,7 | 25 | 12,0% | +12,6% | 14/9 | 4/4 |
| Feb 2025 - Okt 2026 | 4,7 | 279 / 79 / 67 | 47% | 1,28 | 1,13 | +13,9 | 18 | 8,6% | +6,8% | 8/9 | 1/2 |
| 12 tahun | 4,6 | 1.608 / 696 / 512 | 48% | 1,25 | 1,15 | +14,6 | 25 | 12,0% | +7,2% | 14/10 | 8/12 |

Per tahun (R): 2015 -6 · 2016 +28 · 2017 +39 · 2018 -5 · 2019 +15 · 2020 +3 · 2021 -2 · 2022 +30 · 2023 +1 · 2024 +36 · 2025 +35 · 2026 -2.
Per strategi: MR win 50% PF 1,12 +72R · K6 win 37% PF 1,15 +67R · SUS win 55% PF 1,21 +33R.
Catatan jujur ide #40: ditemukan dari statistik SEMUA periode (rawan kebetulan); P uji 0,87 (X80 0,95); Setra ≈ sama (+13,9 vs
+13,6); tahun untung 8/12 (sebelumnya 9/12) dan 2026 berjalan -2 vs +8; aturan asimetris memihak tren naik emas. Uji silang
perak (uji_xag.py) masih riset lanjutan; bayangan "MR SELL lama 71,22" memantau versi sebelumnya.

**Dengan susulan, MR SELL 71,22 (versi 6 Nov pagi, sebelum ide #40)** — sama, tapi urutan ambigu M1 untuk K6 & hari susulan:
| Periode | Trade/mg | Win | RR | PF | R/thn | DD R | DD% | CAGR | W/L maks | Tahun+ |
|---|---|---|---|---|---|---|---|---|---|---|
| 2015-2021 | 4,7 | 48% | 1,13 | 1,04 | +3,8 | 25 | 12,2% | +1,6% | 8/8 | 5/7 |
| 2022 - Jan 2025 | 4,8 | 48% | 1,27 | 1,15 | +15,9 | 31 | 14,4% | +7,8% | 8/9 | 3/4 |
| Feb 2025 - Okt 2026 | 4,8 | 48% | 1,24 | 1,14 | +13,6 | 21 | 10,1% | +6,7% | 10/8 | 2/2 |
| 12 tahun | 4,8 | 48% | 1,19 | 1,08 | +8,4 | 31 | 14,4% | +3,9% | 10/9 | 9/12 |

Per tahun (R): 2015 +7 · 2016 +8 · 2017 +13 · 2018 -7 · 2019 0 · 2020 -4 · 2021 +10 · 2022 +34 · 2023 -10 · 2024 +22 · 2025 +19 · 2026 +8.
Susulan sendiri (12 thn): 325 trade, win 56%, RR 0,97, PF 1,21, +21R. Di Setra (n 46) susulan lebih buruk (gabung +13,6 vs +15,6
R/thn tanpa susulan) → dipantau lewat bayangan "Tanpa susulan"; evaluasi ulang setelah ±20 trade susulan live (±7 bulan).

**Catatan jujur**: aturan dirakit setelah melihat semua periode (ide #34) → belum terbukti di data baru; edge tipis (PF 1,07).
Penyetelan 324 kombinasi tidak menghasilkan versi yang signifikan lebih baik (P ≤ 0,56). Catatan bayangan semua strategi menu:
`python riset/xau/bayangan.py . <xau.json> <xau_panjang.json>` (dipakai riset Jumat untuk uji maju).
