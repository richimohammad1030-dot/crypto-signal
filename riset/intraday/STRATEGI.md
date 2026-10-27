# Strategi INTRADAY · juara terkunci v2 (27 Okt 2026)

Status: **dikunci**, belum live. Belum ada bot/workflow; riset mingguan memakai mesin `riset/backtest_intraday.py`.
Parameter juara ada di `PARAM` pada skrip itu. Perubahan juara hanya lewat riset + persetujuan pemilik.
v2 menggantikan v1 (fill rate v1 hanya 14%, ditolak pemilik).

## Aturan
Data: Binance spot, 49 koin bot crypto (`signal_bot.COINS`), candle 15 menit + H1. Waktu dalam WIB.

**Modul B · sinyal pagi 07:00 WIB** (dari candle H1 yang close 07:00)
- Koin tren naik (close > EMA200, EMA100 > EMA200) atau tren turun, **searah tren BTC**.
- Short hanya jika funding rata-rata 72 jam > 0 (sama dengan filter bot crypto).
- Volatilitas tinggi: ATR(14) H1 ≥ 1,1 × rata-rata ATR 14 hari **dan** ≥ 1,34% harga.
- Order: LIMIT di open 07:00 − 1 ATR H1 (long) / + 1 ATR (short).
- TP: harga open 07:00 (limit). SL: 1,5 ATR H1. Kadaluarsa order 12 jam. Time stop 24 jam.

**Modul A · alert kapan saja** (candle 15m)
- Tren naik 15m (EMA100/200), RSI(2) < 5 atau RSI(14) < 30, **ATR(14) 15m ≥ 1,5% harga**.
- Order: LIMIT long **0,25 ATR** di bawah close. **Kadaluarsa 2 jam**.
- SL 3 ATR. Exit saat RSI(2) > 70 (market). Time stop 2 jam.

**Portofolio**
- Maks **3 posisi** terisi bersamaan, maks **3 order menunggu**, satu order/posisi per koin.
- Saat posisi penuh, order lain yang menunggu **dibatalkan**.
- Prioritas order di waktu sama: market cap terbesar.
- **Risiko 1% per trade** (standar yang disepakati pemilik).

## Hasil backtest (net fee, slippage, funding · Mar 2020 - Okt 2026, model realistis)
Model realistis: order yang menunggu memakan slot, order lain dibatalkan saat posisi penuh.

| | Semua | 2020-2023 | 2024-skrg |
|---|---|---|---|
| Trade | 4.886 (±743/thn, ±62/bln, ±14/minggu) | 3.021 | 1.865 |
| **Fill rate** (terisi / dikirim) | **70,9%** | 70,8% | 71,0% |
| Order dikirim | ±20/minggu (±3/hari) | | |
| Win rate | 66,5% | 68,2% | 63,9% |
| R/trade | +0,064 | +0,076 | +0,044 |
| Total R/tahun | +47 | +60 | +30 |
| Profit factor | 1,30 | 1,38 | 1,18 |
| Drawdown terburuk | 13,4R | 10,6R | 13,4R |
| Rasio R/thn ÷ DD | 3,53 | 5,66 | 2,24 |
| Win / kalah beruntun maks | 26 / 9 | 26 / 8 | 20 / 9 |

**Risiko 1%:** CAGR ±58%, drawdown ekuitas maks 14,0%. Periode uji 2024-skrg: CAGR ±33%, DD 14,0%.
Per tahun: 2020 +50% · 2021 +184% · 2022 +49% · 2023 +49% · 2024 +49% · 2025 +10% · 2026 +35% (s.d. Okt).
Hari dengan posisi baru ±62%, hari dengan sinyal dikirim ±70%. Bulan positif 70%, bulan terburuk -9,2R.
Per modul: A long 2.991 trade +0,051R · B long 1.475 trade +0,089R · B short 420 trade +0,067R.
Cara keluar: RSI 48%, TP 25%, SL 16%, waktu 11%.

## Riwayat
Lihat `riset/intraday/log.md`.
