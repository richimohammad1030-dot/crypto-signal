# RISET CRYPTO · Tahap 0 "untung di semua tahun" + Tambal-celah putaran 1 · 6 Nov 2026

Branch `claude/riset-crypto-2026-11-06`. Bot live tidak diubah. Data: 49 koin daftar bot (HYPE dilewati, data kurang),
candle H1 Binance Okt 2019 - 6 Nov 2026, funding Binance s.d. 31 Okt lalu Hyperliquid. Juara = v2 (24 Okt 2026).

## Kesimpulan
**Tahap 0 TIDAK LULUS.** Setelah biaya realistis, setiap tahun 2020-2026 memang untung, tetapi **2025 menjadi minus
(-12,6R) bila 2% trade terbaik tahun itu dibuang**, dan 2026 tipis. Dengan daftar koin sesuai masanya (ekspektasi yang lebih
jujur) ada tiga tahun minus tanpa 2% terbaik (2022, 2025, 2026) dan DD 30,8R. Program yang berlaku: **TAMBAL-CELAH**.
Putaran 1 menguji 2 penambal dari literatur (filter pasar berombak). Keduanya gagal.

## 1. Model biaya (baru; backtest lain di repo memakai R kotor)
| Komponen | REAL | KONS |
|---|---|---|
| Entry (stop breakout) | taker 0,05% + slip 0,03% | taker 0,05% + slip 0,10% |
| TP 25% di 1R (limit) | maker 0,02% | maker 0,02% |
| Keluar SL / cut-loss stagnan | taker 0,05% + slip 0,03% | taker 0,05% + slip 0,10% |
| Funding | rate aktual tiap settlement selama posisi terbuka, nilai posisi = qty × harga | sama |

Biaya rata-rata per trade: fee 0,019R (KONS 0,035R) + funding +0,014R (long bayar +0,025R, short menerima 0,002R).
Nilai posisi per 1R median 10,3x, sehingga biaya 0,1% harga ≈ 0,01R. Gap saat fill sudah ditangani mesin (fill di open).
Asumsi slippage belum diverifikasi dengan data eksekusi nyata (bot hanya mengirim sinyal).

## 2. Per tahun kalender (tahun tutup posisi), daftar koin tetap, R bersih REAL
| Tahun | Trade | R bersih | Win | PF | DD (R) | Tanpa 2% terbaik (per tahun) | Tanpa 2% (global) | Kotor | KONS |
|---|---|---|---|---|---|---|---|---|---|
| 2020 | 304 | +112,5 | 47,4% | 2,48 | 9,7 | +74,5 | +62,3 | +129,9 | +107,8 |
| 2021 | 336 | +120,3 | 42,0% | 2,41 | 8,1 | +62,1 | +34,2 | +137,2 | +116,9 |
| 2022 | 337 | +50,1 | 39,5% | 1,52 | 16,8 | +24,6 | +43,3 | +56,9 | +45,3 |
| 2023 | 371 | +102,8 | 39,1% | 1,99 | 17,1 | +41,1 | +20,5 | +113,8 | +95,1 |
| 2024 | 371 | +113,5 | 43,1% | 2,12 | 17,5 | +26,5 | +30,1 | +125,1 | +107,4 |
| **2025** | 382 | **+25,6** | 38,7% | 1,23 | 16,3 | **-12,6** | **-1,1** | +32,8 | +19,7 (tanpa 2%: -18,4) |
| 2026* | 329 | +40,8 | 36,8% | 1,42 | 17,2 | +8,1 (tipis) | +17,6 | +48,7 | +34,4 |
| Semua | 2.435 | +562,8 | | | 17,5 | | | +641,7 | +523,7 |

\*2026 s.d. 5 Nov (disetahunkan ±48R). Rata-rata tahunan penuh 2020-2025 = 87,5R → ambang "tipis" 8,8R.
Tahun terburuk: 2025. Tahun tipis: 2026 versi tanpa 2% terbaik (+8,1R). Des 2019 = 5 trade pemanasan (-2,8R), bukan tahun data.
Dengan tahun BUKA posisi hasilnya sama (2025: +25,6 / tanpa 2% -12,6R).

### Daftar koin sesuai masanya (226 koin termasuk delisting), R bersih REAL
| Tahun | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|
| R bersih | +106,8 | +93,6 | +25,3 | +81,6 | +81,9 | +17,5 | +26,1 |
| Tanpa 2% terbaik | +59,7 | +34,4 | **-1,4** | +19,5 | +19,5 | **-10,0** | **-2,6** |

Total 432,7R (vs 562,8R daftar tetap, -23%), DD 30,8R (vs 17,5R). Angka ini patokan ekspektasi yang lebih jujur.

### Per koin (koin mana yang menopang)
- 40 dari 49 koin positif. 8 koin terbaik (ADA 45,8 · DOGE 45,3 · XLM 43,8 · SOL 40,9 · XRP 39,3 · ETH 37,5 · BTC 33,4 · SHIB 32,0R)
  = 56% total. **Tanpa 8 koin itu pun setiap tahun positif** (2025 +13,2R, 2026 +13,6R).
- Tanpa koin terbaik tahun itu: semua tahun tetap positif (2025 +18,1R).
- Jadi hasil **tidak** ditopang segelintir koin, melainkan segelintir **trade**: 2% trade terbaik = 34-80% R tahunan
  (2025: 149%, 8 trade +38,2R: ZEC, XRP, HBAR, ETH ×2, JST, WLD, AVAX). 2024 bergantung pada XLM +36,4R (satu trade).

## 3. Bedah celah 2025 (R bersih REAL)
- Arah: BUY 174 trade +0,15R, SELL 208 trade 0,00R. Tanpa 2% terbaik: BUY -9,4, SELL -3,2R.
- Label: HIGH +0,29R, MEDIUM **-0,05R** (154 trade), LOW +0,06R.
- Keluar: trade untung rata-rata 0,95R (tahun lain 1,1-1,4R); cut-loss stagnan 129 (terbanyak).
- Pasar: BTC 30 hari vol 55-75% -0,12R; rezim BTC netral -0,01R; hanya 25/44 koin positif.
- Bulan terburuk: Jan -13,2, Agu -11,8, Des -7,3R. Bulan terbaik: Jul +27,2R.
- Gambaran: tahun berombak, tren pendek, untung kecil, kerugian kecil tapi banyak. Bukan masalah satu arah atau satu koin.
- Celah lain: 2022 (BUY -0,04R; minus di daftar sesuai masanya), 2026 (tipis, MEDIUM +0,03R).

## 4. Tambal-celah putaran 1 (replay penuh, R bersih REAL, 9 varian)
| Varian | Trade | Total R | DD | Rasio lama / baru | Tahun minus (biasa / tanpa 2%) | 2025 / tanpa 2% |
|---|---|---|---|---|---|---|
| Juara | 2.435 | 562,8 | 17,5 | 22,5 / 10,3 | 0 / 1 | +25,6 / -12,6 |
| #52 ER ≥ 0,15 | 2.457 | 398,5 | 19,9 | 16,4 / 4,0 | 0 / 3 | +23,7 / -12,1 |
| #52 ER ≥ 0,20 | 2.353 | 396,8 | 19,6 | 18,8 / 3,8 | 0 / 3 | +17,9 / -19,2 |
| #52 ER ≥ 0,25 | 2.220 | 321,7 | 25,0 | 18,0 / 1,8 | 1 / 3 | -5,7 / -34,1 |
| #52 ER ≥ 0,30 | 2.027 | 323,2 | 23,4 | 13,2 / 3,3 | 1 / 2 | -7,7 / -27,7 |
| #52 ER ≥ 0,35 | 1.772 | 276,4 | 27,9 | 11,8 / 1,8 | 1 / 1 | -15,8 / -32,8 |
| #53 ADX ≥ 15 | 2.369 | 487,8 | 22,6 | 16,6 / 6,0 | 0 / 2 | +24,0 / -13,5 |
| #53 ADX ≥ 20 | 2.248 | 353,9 | 23,8 | 13,0 / 2,3 | 1 / 2 | +4,6 / -24,9 |
| #53 ADX ≥ 25 | 1.847 | 319,1 | 23,4 | 20,9 / 2,7 | 2 / 2 | -5,5 / -23,9 |
| #53 ADX ≥ 30 | 1.437 | 210,4 | 17,2 | 10,2 / 2,2 | 1 / 2 | -6,7 / -21,7 |

Keputusan: **#52 dan #53 GAGAL.** Semua ambang memperburuk periode lama (tempat ambang seharusnya dipilih) maupun baru,
termasuk 2025 yang menjadi sasaran. ER saat entry juga tidak berpola terhadap hasil (kuartil 0,17-0,29R), jadi kerugian
datang dari order breakout yang batal dan slot yang terisi sinyal lain. Pelajaran: menyaring entry di sistem ini
berulang kali gagal (#1, #3, #4, #11, #52, #53); penambal berikutnya sebaiknya mengubah bentuk hasil atau menambah sumber edge.
Uji signifikansi dan data terkunci tidak dipakai (tidak ada yang lolos tahap 1).

## 5. Kandidat putaran berikutnya
1. **#54 TP lebih awal/lebih besar** (33-50% di 1R, atau TP kedua 25% di 2-3R): langsung menyerang ketergantungan pada ekor.
   Risiko: total R turun (TP penuh 2-15R pernah gagal 23 Okt, tetapi TP sebagian bertingkat belum diuji).
2. **#55 [lit] Strategi pelengkap mean-reversion RSI(2)** (Connors & Alvarez 2008) di koin besar saat tren lemah: edge berbeda
   untuk tahun berombak. Diuji sebagai portofolio terpisah dengan biaya REAL (biaya lebih berat karena trade lebih sering).
3. **#19 Risiko SELL 0,5%** (antri lama): SELL 2025 0,00R; efek kecil tetapi murah diuji.

## 6. Butuh keputusan pemilik
- **Definisi lulus "tanpa 2% terbaik"**: per tahun (dipakai di sini, ketat) atau global (2% terbaik seluruh periode dibuang;
  2025 -1,1R, lebih dekat lulus). Untuk sistem tren yang untungnya datang dari ekor, versi per tahun mungkin sangat sulit
  dicapai tanpa mengorbankan total R. Saya tetap memakai versi per tahun sampai pemilik memutuskan.
- **Model biaya** REAL (slip 0,03%) adalah asumsi. Jika eksekusi nyata lebih buruk, pakai KONS (2025 tanpa 2% -18,4R).
- Tidak ada usulan perubahan bot live dari putaran ini.

## Sumber
- P. J. Kaufman, *Smarter Trading* (1995) — Efficiency Ratio; ringkasan: [LuxAlgo, Kaufman Efficiency Ratio](https://www.luxalgo.com/library/concept/kaufman-efficiency-ratio/), [MoneyShow (Price Headley)](https://moneyshow.com/articles/daytraders-26970)
- J. W. Wilder Jr., *New Concepts in Technical Trading Systems* (1978) — ADX; [Wikipedia: Average directional movement index](https://en.wikipedia.org/wiki/Average_directional_movement_index), [StockCharts ChartSchool: ADX](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/average-directional-index-adx)
- L. Connors & C. Alvarez, *Short Term Trading Strategies That Work* (2008) — RSI(2); [LuxAlgo: RSI-2](https://www.luxalgo.com/library/concept/rsi-2/)

Skrip: `riset/crypto/eksperimen/tahap0_semua_tahun.py`, `tahap0_pit.py`, `celah_crypto.py`, `tambal1_choppy.py`.

## Tambahan (6 Nov 2026, 15:30 WIB): keputusan pemilik
Syarat ditetapkan: **setiap tahun kalender R bersih REAL >= +1R** (daftar tetap). Juara v2 terburuk 2025 +25,6R
(sesuai masanya +17,5R, KONS +19,7R) → **Tahap 0 LULUS**, program berlaku **OPTIMASI** (lihat PROSEDUR).
Peluang tahun minus (bootstrap): 2025 9,4%, 2026 1,8%, tahun lain ≤ 0,2% — dipantau, bukan syarat.
