# Strategi INTRADAY · juara terkunci v3 (30 Okt 2026)

Status: **dikunci, LIVE sejak 30 Okt 2026** (`intraday_bot.py`, workflow `intraday.yml`, tiap 15 menit). Riset mingguan memakai
`riset/backtest_intraday.py` (daftar koin bot) **dan** `riset/pit_intraday.py` (daftar koin sesuai masanya = ekspektasi jujur).
Kesetaraan mesin live vs backtest: `riset/replay_intraday.py`. Parameter juara: `PARAM` di `riset/backtest_intraday.py`.
Perubahan juara hanya lewat riset + persetujuan pemilik. Riwayat: v1 (27 Okt) → v2 (27 Okt, fill 71%) → **v3** (30 Okt, pilihan pemilik
"strategi #2" setelah uji koin sesuai masanya menunjukkan modul A v2 tanpa edge di 2024-skrg).

## Aturan
Data: Binance spot, 49 koin bot crypto (`signal_bot.COINS`, urut market cap), candle 15 menit + H1. Waktu dalam WIB. Risiko **1% per trade**.

**Modul A · dip 15m, kapan saja** (rasio TP:SL **2:1**)
- Hanya koin **peringkat 1-25** dan saat **tren BTC H1 naik** (candle H1 terakhir yang sudah close).
- Koin tren naik 15m (close > EMA200, EMA100 > EMA200), RSI(2) < 5 atau RSI(14) < 30, ATR(14) 15m ≥ 1,5% harga.
- Order: LIMIT long **0,5 ATR** di bawah close. Kadaluarsa 2 jam.
- SL **3 ATR**. TP **2 × SL (6 ATR)**. **Tutup paksa setelah 4 jam** (bot kirim "TUTUP SEKARANG").
  Catatan: TP 2× jarang tersentuh (±3,5%); ±80% trade keluar di batas 4 jam (rata-rata +0,23R), ±16% kena SL.

**Modul B · sinyal pagi 07:00 WIB** (rasio TP:SL **±0,67:1**, tidak berubah dari v2)
- Koin tren naik/turun searah tren BTC; short hanya jika funding rata-rata 72 jam > 0.
- ATR(14) H1 ≥ 1,1 × rata-rata 14 hari dan ≥ 1,34% harga.
- LIMIT di open 07:00 ∓ 1 ATR H1. TP di harga open 07:00. SL 1,5 ATR H1. Kadaluarsa 12 jam. Tutup paksa 24 jam.

**Portofolio**: maks 3 posisi terbuka, maks 3 order menunggu, 1 order/posisi per koin, posisi penuh → order lain dibatalkan,
prioritas market cap.

## Hasil backtest (net fee, slippage, funding · Mar 2020 - Okt 2026, risiko 1%)
**Daftar koin sesuai masanya (ekspektasi jujur, 195 koin termasuk delisting)**

| | 2024-skrg (uji) | Seluruh periode |
|---|---|---|
| Trade | 1.091 (±33/bln) | 2.944 (±37/bln) |
| Win rate (A / B) | 63,4% (60% / 64%) | 63,3% (58% / 65%) |
| Rata-rata menang / kalah | +0,63R / -0,92R | +0,63R / -0,85R |
| RR tercapai | 0,69 | 0,74 |
| Expectancy | +0,064R | +0,088R |
| Profit factor | 1,19 | 1,28 |
| R per tahun | +24,9 | +39,3 |
| Drawdown (R) | 16,3 | 16,3 |
| CAGR (compounding) | **27%** | **46%** |
| Drawdown ekuitas maks | **15,6%** | 15,6% |
| Menang / kalah beruntun maks | 21 / 8 | 21 / 9 |
| Bulan positif · bulan terburuk | 71% · -8,4R | 71% · -8,4R |

Per tahun (R): 2020 +37 · 2021 +93 · 2022 +36 · 2023 +25 · 2024 +25 · 2025 +9 · 2026 +35. P(lebih baik dari v2) = 0,96.

**Daftar koin bot (tetap)**: 2.665 trade, win 64,1%, +0,098R/trade, +39,8R/thn, DD 13,3R, rasio 2,98 (2024-skrg rasio 2,34).
Selisih ke angka sesuai masanya = bias koin selamat; gunakan angka sesuai masanya sebagai ekspektasi.
