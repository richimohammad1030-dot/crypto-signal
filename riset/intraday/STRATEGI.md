# Strategi INTRADAY · juara terkunci v1 (27 Okt 2026)

Status: **dikunci**, belum live. Belum ada bot/workflow; riset mingguan memakai mesin `riset/backtest_intraday.py`.
Parameter juara ada di `PARAM` pada skrip itu. Perubahan juara hanya lewat riset + persetujuan pemilik.

## Aturan
Data: Binance spot, 49 koin bot crypto (`signal_bot.COINS`), candle 15 menit + H1. Waktu dalam WIB.

**Modul B · sinyal pagi 07:00 WIB** (dari candle H1 yang close 07:00)
- Koin tren naik (close > EMA200, EMA100 > EMA200) atau tren turun, **searah tren BTC**.
- Short hanya jika funding rata-rata 72 jam > 0 (sama dengan filter bot crypto).
- Volatilitas tinggi: ATR(14) H1 ≥ 1,1 × rata-rata ATR 14 hari **dan** ≥ 1,34% harga.
- Order: LIMIT di open 07:00 − 1 ATR H1 (long) / + 1 ATR (short).
- TP: harga open 07:00 (limit). SL: 1,5 ATR H1. Kadaluarsa order 12 jam. Time stop 24 jam.

**Modul A · alert kapan saja** (candle 15m)
- Tren naik 15m (EMA100/200), RSI(2) < 5 atau RSI(14) < 30, ATR(14) 15m ≥ 1% harga.
- Order: LIMIT long 1,5 ATR di bawah close. Kadaluarsa 30 menit.
- SL 3 ATR. Exit saat RSI(2) > 70 (market). Time stop 2 jam.

**Portofolio**
- Maks **2 posisi** terisi bersamaan, maks 12 order menunggu sekaligus, satu order/posisi per koin.
- Saat 2 posisi terisi, semua order lain yang menunggu **dibatalkan**.
- Prioritas order di waktu sama: market cap terbesar.
- Risiko per trade: 1% (0,5% untuk konservatif).

## Hasil backtest (net fee, slippage, funding · Mar 2020 - Okt 2026)
| | Semua | 2020-2023 | 2024-skrg |
|---|---|---|---|
| Trade | 2.963 (±451/thn, ±37/bln) | 1.747 | 1.216 |
| Win rate | 66,9% | 68,2% | 65,1% |
| R/trade | +0,092 | +0,113 | +0,060 |
| Total R/tahun | +41 | +52 | +27 |
| Profit factor | 1,32 | 1,42 | 1,20 |
| Drawdown terburuk | 14,4R | 9,1R | 14,4R |
| Rasio R/thn ÷ DD | 2,86 | 5,67 | 1,85 |
| Win / kalah beruntun maks | 21 / 8 | 21 / 7 | 14 / 8 |
| Order terisi dari yang dikirim | 14% | 15% | 14% |

Per tahun (R): 2020 +38 · 2021 +81 · 2022 +33 · 2023 +47 · 2024 +15 · 2025 +20 · 2026 +38.
Risiko 1%: CAGR ±49%, drawdown ekuitas maks ±14%. Risiko 0,5%: CAGR ±22%, drawdown ±7%.
Hari dengan posisi baru ±56%. Hold median ±2 jam. Cara keluar: TP 41%, RSI 25%, SL 25%, waktu 8%.

## Riwayat keputusan (ringkas)
Lihat `riset/intraday/log.md` (fondasi 27 Okt 2026) untuk semua jalur yang diuji dan alasan gagal/lolos.
