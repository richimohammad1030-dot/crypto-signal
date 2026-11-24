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

**24 Nov 2026 - v3, aturan dari video Rizky Aditama (backtest_v3.py, tanpa bias, spread $0,30, data 2020-01..2026-11 lengkap):**
2160 kombinasi (bodi x ekor x sesi x lokasi x manajemen). Sesi Asia jelas terbaik (median PF 1,00; 269 dari 351 kombinasi PF>1).
London/NY/semua jam: median PF 0,87-0,92. Ekor W1 (sisi asal < sisi tujuan) > W0 lama. Entry market + SL lebar > limit 23,6%.
KANDIDAT: bodi >= $4, ekor W1, sinyal 07-14 WIB, bukan pucuk (|close-EMA50| <= 2 ATR), market di open berikutnya, SL 3xATR14, TP 1,5R, maks 1 jam:
n 756 (0,44/hari), WR 51%, PF 1,21, +45R, DD 14R, kalah beruntun 8, per tahun 20:+1 21:-1 22:+3 23:-2 24:+1 25:+8 26:+34.
Ketahanan: semua tetangga PF 1,06-1,37 (jam 07-12: 1,37; bodi $5: 1,31; spread $0,50: 1,14). Profit tetap terkumpul di 2026.
Risiko pemilihan berlebih (2160 percobaan): wajib divalidasi Strategy Tester MT5 (tick nyata) + demo sebelum live.

**24 Nov 2026 - frekuensi & SL/TP tetap 1:1:** kandidat Asia (bodi $4) di 2026 = 2,0 trade/hari (rata-rata 7 tahun 0,44/hari karena 2020-24 sepi).
SL=TP tetap 1:1: $1 (100 pip) median PF 0,45 (spread $0,30 = 30% TP), $2 0,72, $3 0,82, $5 0,90, $10 0,94 -> tidak ada yang layak.
Tambah sesi = tambah sinyal tapi edge turun: bodi $4 Asia 07-16 2,5/hari PF2026 1,26; Asia+NY 3,3/hari PF 1,04 (7 thn); semua jam 4,9/hari PF 1,00.
