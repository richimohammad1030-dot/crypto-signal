# Riset intraday · 6 Nov 2026 (sore) · TAHAP 0 + PROGRAM OPTIMASI putaran 1

Permintaan pemilik: verifikasi "untung di semua tahun" sebelum optimasi. Data s.d. 6 Nov 2026 ±15:00 WIB (49 koin bot + 177 koin
sesuai masanya, H1 + funding + 15m, unduh lengkap). Juara v3 dan bot live **tidak diubah**. Skrip di `riset/intraday/eksperimen/`.

## 1. Tahap 0 · hasil: LULUS (tipis), tidak tahan uji stres

Uji utama = daftar koin sesuai masanya (PIT, 119 koin terpakai termasuk delisting), replay penuh portofolio (3 posisi, 3 order menunggu),
biaya juara: limit/TP maker 0,02%, SL/market/batas waktu taker 0,07% (fee + slippage), funding tiap settlement. Risiko 1%/trade.

| Tahun | Trade | /minggu | R bersih | R/trade | Win | RR | PF | DD (R) | Menang/kalah beruntun | Tanpa 2% terbaik (per tahun) | Tanpa 2% (global) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2020 (Mar-) | 443 | 10,4 | +38,0 | +0,086 | 62,1% | 0,78 | 1,28 | 14,4 | 13 / 9 | +24,0 | +21,7 |
| 2021 | 770 | 14,8 | +92,6 | +0,120 | 62,5% | 0,86 | 1,43 | 6,4 | 13 / 7 | +62,7 | +36,2 |
| 2022 | 295 | 5,8 | +35,6 | +0,121 | 66,8% | 0,70 | 1,41 | 6,8 | 12 / 6 | +31,2 | +34,4 |
| 2023 | 344 | 6,8 | +24,9 | +0,072 | 64,0% | 0,69 | 1,22 | 9,4 | 14 / 7 | +18,1 | +20,5 |
| 2024 | 495 | 9,8 | +25,3 | +0,051 | 62,2% | 0,70 | 1,15 | 15,8 | 21 / 6 | +10,6 | +10,6 |
| **2025** | 328 | 6,5 | **+9,4** | +0,029 | 61,0% | 0,69 | 1,08 | 13,6 | 12 / 8 | **+1,6** | +4,2 |
| 2026 (-6 Nov) | 293 | 6,7 | +33,7 | +0,115 | 67,6% | 0,66 | 1,38 | 5,2 | 12 / 6 | +29,3 | +33,7 |
| Semua | 2.968 | 8,5 | +259,5 | +0,087 | 63,3% | 0,74 | 1,28 | 15,8 | 21 / 9 | +161,2 | |

Tahun terburuk **2025 (+9,4R)**. Bulan positif 69%; 12 bulan bergulir terendah +5,5R (0 dari 70 jendela minus).

**Pembanding & ketahanan (R per tahun 2020 → 2026)**

| Versi | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 | Tahun minus |
|---|---|---|---|---|---|---|---|---|
| PIT biaya juara (uji utama) | +38 | +93 | +36 | +25 | +25 | +9 | +34 | - |
| Daftar tetap biaya juara | +39 | +72 | +34 | +30 | +26 | +18 | +39 | - |
| PIT **stres eksekusi** | +30 | +68 | +19 | +13 | +8 | **-7** | +25 | 2025 (tanpa 2%: 2024, 2025) |
| Daftar tetap stres | +31 | +57 | +16 | +10 | +13 | +4 | +26 | tanpa 2%: 2024, 2025 |

Stres = taker 0,12% (slippage +0,05%) dan limit entry/TP hanya terisi jika harga menembus 0,05% (antrian). Total PIT turun 40% (+260 → +155R).

**Per komponen (PIT, R bersih / trade)**

| | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 | Total |
|---|---|---|---|---|---|---|---|---|
| A-long | +19/129 | +46/382 | +2/33 | +9/54 | +17/129 | +3/32 | +3/36 | +98/795 |
| B-long | +15/276 | +42/279 | +40/165 | +13/267 | +6/288 | **-3/205** | +22/197 | +134/1677 |
| B-short | +4/38 | +5/109 | **-6/97** | +4/23 | +3/78 | +10/91 | +8/60 | +27/496 |
| Sesi isi 07-15 WIB | +26 | +51 | +32 | +25 | +12 | +6 | +29 | +180/2053 |
| Sesi isi 15-20 WIB | +2 | +9 | +1 | **-5** | **-3** | +4 | +5 | +14/442 |
| Sesi isi 20-02 WIB | +4 | +18 | +2 | +4 | +10 | -2 | +0 | +36/287 |
| Sesi isi 02-07 WIB | +6 | +15 | +0 | +1 | +7 | +1 | -0 | +30/186 |

Long +232R (tahun terlemah 2025 -0,1R), short +27R (2022 -6,1R). Per koin: 71 dari 119 positif; terburuk FIL -7,0, ALGO -6,9, HBAR -4,7;
terbaik ADA +31,7, ETH +22,3, LINK +21,8. Tanpa koin terbaik di tiap tahun, semua tahun tetap positif (2025 +6R).

**Kesimpulan Tahap 0:** syarat pemilik terpenuhi pada model biaya juara (semua tahun > 0, termasuk tanpa 2% terbaik), sehingga
program yang berlaku = **OPTIMASI**. Tetapi lulusnya tipis: 2025 tanpa 2% terbaik hanya +1,6R dan berubah minus pada eksekusi sedikit
lebih buruk. Karena itu PROGRAM UTAMA menambahkan **pagar stres** (usulan, menunggu persetujuan): kandidat tidak boleh memperburuk
tahun terburuk pada uji stres.

## 2. Bedah celah (kondisi pasar, PIT)
- 2025 B-long: koin peringkat 1-10 -9,1R (69 trade); saat BTC naik > 10% dalam 30 hari -10,0R (70 trade); Mei 2025 -10,5R.
- Dispersi return 24 jam antar 25 koin teratas: rendah avg +0,053R · sedang +0,080R · tinggi +0,129R (tidak monoton di setiap tahun:
  2022-2023 dispersi rendah justru bagus).
- Akhir pekan +0,137R/trade vs hari kerja +0,070R (akhir pekan lebih baik di 5 dari 7 tahun).
- Jarak BTC ke EMA200 H1: jauh di atas +0,111R vs sedang/dekat +0,045R.

## 3. OPTIMASI putaran 1 · jalur ukuran posisi
Bobot risiko per trade dihitung pasca-trade (order, slot, isi tidak berubah), dinormalisasi: rata-rata bobot 2020-2023 = 1.
Kriteria: rasio R/DD +10% di 2020-23 dan 2024-skrg, semua tahun > 0 (juga tanpa 2% terbaik), DD naik ≤ 25%, P ≥ 0,90, pagar stres.

| Varian | Rasio 20-23 | Rasio 24-skrg | DD R | DD ekuitas | CAGR 1% (semua / 24+) | P | 2025 (tanpa 2%) | Stres terburuk | Keputusan |
|---|---|---|---|---|---|---|---|---|---|
| Juara v3 | 3,49 | 1,51 | 15,8 | 15,6% | 45,7% / 25,6% | - | +9 (+2) | -6,5 | - |
| I-08 A1,5 · B-long 0,75 · B-short 0,5 | 4,28 | 2,06 | 12,7 | 13,1% | 48,8% / 24,9% | 0,91 | +7 (**-5**) | -3,8 | gagal |
| I-08 A1,5 · B-long 0,75 · B-short 0,75 | 4,13 | 2,09 | 12,8 | 12,8% | 48,1% / 26,1% | 0,95 | +9 (**-3**) | -4,0 | gagal |
| I-24 vol-managed [0,5; 2] | 4,26 | 1,45 | 16,7 | 15,7% | 46,2% / 25,7% | 0,33 | +13 (+3) | -5,7 | gagal |
| **I-25 dispersi k=1 [0,5; 2]** | **4,44** | **1,89** | 17,7 | 17,5% | **54,6% / 34,7%** | **0,95** | +13 (+4) | **0,0** | **uji-maju** |
| I-25 k=0,5 [0,5; 1,5] | 4,04 | 1,72 | 16,4 | 16,1% | 51,1% / 30,9% | 0,96 | +12 (+3) | -2,9 | lolos |
| I-25 k=1,5 [0,5; 2] | 4,24 | 1,91 | 18,3 | 18,0% | 54,8% / 35,4% | 0,92 | +13 (+4) | 0,0 | lolos |

I-25 per tahun (R): +48 / +114 / +22 / +27 / +34 / +13 / +41 (2022 turun dari +36 ke +22). Daftar tetap: rasio 2024-skrg 2,20 → 3,01.
Tetangga definisi dispersi (k=1): jendela 12 j (rasio 4,56 / 2,14) dan 48 j (3,99 / 2,43), median 180 hari (4,35 / 1,98) dan 730 hari
(4,53 / 1,82), 48 j + 50 koin (3,89 / 2,04) **lolos**; 10 koin teratas (4,74 / 1,31, P 0,59) dan 12 j + 10 koin **gagal**;
50 koin batas (P 0,90). Jadi 6 dari 9 definisi lolos; semesta terlalu sempit (didominasi BTC/ETH) tidak bekerja.

Kelemahan I-25 yang perlu diketahui: risiko naik saat pasar "terpecah" (bobot maks ±1,5%, risiko terbuka bersamaan maks 4,4% vs 3%),
DD naik 12%, dan 2022 lebih lemah. Data terkunci intraday (daftar koin sesuai masanya) sudah menjadi uji utama sejak v3, jadi satu-satunya
konfirmasi yang tersisa adalah **uji maju** (≥ 6 minggu dan ≥ 60 trade sejak 6 Nov 2026). Backtest ini kemungkinan tetap optimis:
ide dipilih setelah melihat bedah celah di data yang sama, dan total ide intraday yang sudah diuji kini 17.

## 4. Kandidat berikutnya
1. I-25 uji maju (bobot dihitung ulang tiap Jumat untuk trade baru; tidak ada perubahan bot).
2. I-26 B-long: lewati/kurangi koin peringkat 1-10 saat BTC naik > 10%/30 hari (celah 2025) — jalur 2/4.
3. I-27 batasi order yang terisi di sesi 15-20 WIB (lemah, minus di uji stres) — jalur 2.

## 5. Butuh persetujuan pemilik
- **Pagar stres** sebagai syarat tetap program optimasi (tahun terburuk pada uji stres tidak boleh memburuk).
- Tidak ada perubahan bot/juara yang diusulkan sekarang; I-25 baru diusulkan setelah uji maju.

## Sumber
- Moreira, A. & Muir, T. (2017). Volatility-Managed Portfolios. Journal of Finance 72(4). https://www.nber.org/papers/w22208
- Cederburg, S., O'Doherty, M., Wang, F. & Yan, X. (2020). On the performance of volatility-managed portfolios. JFE 138(1). https://www.lehigh.edu/~xuy219/research/COWY.pdf
- Jegadeesh, N., Luo, J., Subrahmanyam, A. & Titman, S. (2025). Short-Term Reversals and Longer-Term Momentum around the World. Review of Financial Studies. https://doi.org/10.1093/rfs/hhaf057
