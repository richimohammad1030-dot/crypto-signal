# Daftar ide riset

Status: `antri` (belum diuji) · `diuji` (sedang) · `lolos` (kandidat penantang) · `gagal` · `perlu-data` · `dipasang`
Prioritas: 1 = paling penting.

| # | Bot | Ide | Prioritas | Status | Catatan |
|---|---|---|---|---|---|
| 1 | crypto | Batas posisi searah: maksimal N posisi SELL atau BUY sekaligus (coba N = 4, 5, 6) | 1 | gagal | 23 Okt 2026: N 4/5/6 (slot & pos) memangkas DD tetapi rasio 2024-skrg -20% s.d. -50%, total R -29% s.d. -48% |
| 2 | crypto | Sinyal LOW conviction dilewati atau risiko setengah (replay penuh, slot ikut berubah) | 1 | gagal | 23 Okt 2026: lewati rasio -3%/-5%; risiko 1/2 -1% (lama) / +13% (baru). Tinjau ulang risiko 1/2 bila tren baru berlanjut |
| 3 | crypto | Filter short lebih ketat: short hanya jika tren BTC juga turun | 2 | antri | Short melemah 2024-2026 (rata-rata +0,04R) |
| 4 | crypto | Open interest Binance (arsip metrics data.binance.vision): breakout dengan OI naik vs turun | 2 | antri | Data baru, belum dipakai bot |
| 5 | xau | Filter lebar range 04:00-07:00 dibanding ATR (lewati range terlalu sempit/lebar) | 2 | antri | |
| 6 | xau | Lewati hari dengan news USD dampak tinggi sebelum 23:00 WIB | 3 | antri | Kalender ForexFactory hanya minggu berjalan; perlu sumber histori |
| 7 | xau | Target TP 3R atau 5R vs 4R sekarang | 3 | antri | Parameter inti, butuh bukti kuat |
| 8 | crypto | Ukuran risiko mengikuti jumlah posisi terbuka (risiko per trade turun saat banyak posisi searah) | 3 | antri | |
| 9 | crypto | Trailing stop 48 / 96 candle vs 72 sekarang | 4 | antri | Parameter inti, butuh bukti sangat kuat |
| 10 | crypto | Model ML (uji ulang bulanan otomatis di laporan angka) | - | perlu-data | Okt 2026: belum mengalahkan label 4 faktor |
| 11 | crypto | Sinyal SELL LOW conviction dilewati (BUY LOW tetap), replay penuh | 2 | antri | 23 Okt 2026: SELL LOW -0,05R/trade di 2024-2026 (163 trade), satu-satunya kelompok negatif |
| 12 | crypto | Batas posisi searah hanya untuk SELL (BUY bebas), replay penuh | 3 | antri | Dari ide #1: batas semua arah memotong tren BUY besar di 2024-2026 |
