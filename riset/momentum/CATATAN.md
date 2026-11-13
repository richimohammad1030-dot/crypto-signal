# Momentum Candle XAU - catatan hasil

**13 Nov 2026 - KOREKSI:** backtest awal (grid 336 kombinasi) bias optimis. Di bar M1 tempat limit order terisi, simulasi
menghitung TP memakai seluruh range bar, padahal harga bisa menyentuh TP SEBELUM menyentuh harga limit.
TP hanya 0,46x jarak SL, jadi bias ini mengubah PF 0,73 menjadi 1,27.
Validasi: laporan Strategy Tester MT5 Exness (XAUUSDc, M5, 2026-01-01..11-13, tick nyata): 1414 trade, WR 63%, PF 0,80, -62% balance.
Simulasi tanpa bias (STRICT=1, default sekarang): 2026 WR 60%, PF 0,70. Cocok dengan MT5.
Grid ulang tanpa bias: 0 dari 336 kombinasi PF > 1. File lama = BIAS_hasil_grid_lama_JANGAN_DIPAKAI.csv.
Kesimpulan: pullback + TP ujung ekor + SL fibo 74,5% (RR ~0,46) tidak punya edge setelah spread. EA v1.00 tidak boleh dipakai live.
