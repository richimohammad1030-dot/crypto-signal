# Momentum Candle XAU - catatan hasil

**13 Nov 2026 - KOREKSI:** backtest awal (grid 336 kombinasi) bias optimis. Di bar M1 tempat limit order terisi, simulasi
menghitung TP memakai seluruh range bar, padahal harga bisa menyentuh TP SEBELUM menyentuh harga limit.
TP hanya 0,46x jarak SL, jadi bias ini mengubah PF 0,73 menjadi 1,27.
Validasi: laporan Strategy Tester MT5 Exness (XAUUSDc, M5, 2026-01-01..11-13, tick nyata): 1414 trade, WR 63%, PF 0,80, -62% balance.
Simulasi tanpa bias (STRICT=1, default sekarang): 2026 WR 60%, PF 0,70. Cocok dengan MT5.
Grid ulang tanpa bias: 0 dari 336 kombinasi PF > 1. File lama = BIAS_hasil_grid_lama_JANGAN_DIPAKAI.csv.
Kesimpulan: pullback + TP ujung ekor + SL fibo 74,5% (RR ~0,46) tidak punya edge setelah spread. EA v1.00 tidak boleh dipakai live.

**15 Nov 2026 - Opsi 1 (pullback RR besar) & Opsi 2 (breakout market), backtest_v2.py tanpa bias, spread $0,30, 2020-01..2026-11 (tanpa 2023-06/07):**
456 kombinasi, hanya 5 yang PF > 1, terbaik PF 1,03. Opsi 1: tidak ada PF > 1 (terbaik 0,98).
Terbaik Opsi 2: bodi $4, market di open berikutnya, SL 2xATR14, TP 3R, tahan s/d 24:00 WIB: n 2390 (1,4/hari), WR 31,5%, PF 1,02, +36R,
DD 51R, kalah beruntun 16, 6/7 tahun positif. Spread $0,24: PF 1,04 (+61R). Spread 0: PF 1,10. Edge setara nol (wajar terjadi
secara kebetulan dari 456 percobaan). Kesimpulan: momentum candle M5 XAU sebagai sinyal tunggal tidak punya edge yang layak.
