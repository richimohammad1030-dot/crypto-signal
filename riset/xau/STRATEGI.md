# Strategi XAU · juara K6 (dipasang 2 Nov 2026)

Status: **LIVE mulai sinyal Senin 2 Nov 2026 07:00 WIB** (`gold_bot.py`, workflow `gold.yml`). Risiko **1% per trade** (pilihan pemilik).
Perubahan hanya lewat riset + persetujuan pemilik; mesin bot harus lolos `riset/replay_xau.py` (identik dengan riset).
Riwayat: Gold Daily Straddle OCO 2 sisi (live 18 Okt 2026) → **K6** (31 Okt 2026, pilihan pemilik setelah audit 30 Okt).

## Aturan tetap pemilik (tidak boleh diubah)
Sinyal dikirim **07:00 WIB**; semua order & posisi ditutup **23:00 WIB**.

## Aturan
- Data: XAU/USD H1 (Setra). Range = high & low 3 candle H1 yang close 05:00, 06:00, 07:00 WIB (04:00-07:00).
- Tren = close candle 07:00 vs **EMA200 close H1**. Naik → ORDER UTAMA **BUY STOP** di high range, BATAS BATAL = low range.
  Turun (atau sama) → ORDER UTAMA **SELL STOP** di low range, BATAS BATAL = high range.
- Jika batas batal tersentuh lebih dulu → order dibatalkan, hari itu tanpa trade. Jika satu candle H1 menyentuh keduanya,
  mesin menganggap sisi BUY duluan (sama dengan riset; ide #23 akan memperbaikinya dengan candle 1-5 menit).
- SL = 1,5 × ATR(14) H1 dari level order. TP = 4R. Order tidak terisi dibatalkan dan posisi ditutup 23:00 WIB.
- Order diabaikan bila jarak SL ≤ 0,5 USD.

## Ekspektasi jujur (bersih biaya 0,40 USD, risiko 1%; urutan candle ambigu dari M1 untuk 2022-skrg)
| Periode | Trade/bln | Win | Exp | R/thn | DD R | DD% | CAGR |
|---|---|---|---|---|---|---|---|
| 2015-2021 (emas tenang, urutan ambigu = asumsi bot) | 10,0 | 35,2% | -0,017R | -2,0 | 39,3 | 36,6% | -3,4% |
| 2022 - Jan 2025 | 10,8 | 36,2% | +0,090R | +11,6 | 26,7 | 23,8% | +10,4% |
| Feb 2025 - Okt 2026 (Setra) | 11,5 | 40,2% | +0,226R | +31,2 | 13,8 | 13,4% | +33,9% |

Pembanding juara lama (OCO 2 sisi) di periode sama: -25,2 / ±0,0 / +29,3 R/thn. Signifikansi K6 vs juara lama (2022 - Jan 2025): P 0,939.
Tidak ada edge permanen: strategi kuat hanya saat emas tren kuat & volatil. Kalah beruntun 17 pernah terjadi (2022-skrg).
