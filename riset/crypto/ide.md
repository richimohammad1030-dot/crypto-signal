# Daftar ide riset · CRYPTO

Status: `antri` (belum diuji) · `diuji` (sedang) · `perlu-data` · `uji-maju` (lolos tahap 1-3) · `lolos` (siap diusulkan) · `gagal` · `dipasang`
Ide dari literatur ditandai `[lit]` (nilai tambah, tidak wajib). Aturan lengkap: `riset/ATURAN_BERSAMA.md`.
Prioritas: 1 = paling penting.
Nomor ide tetap mengikuti daftar awal agar rujukan di jurnal riset tidak berubah.

| # | Ide | Prioritas | Status | Catatan |
|---|---|---|---|---|
| 1 | Batas posisi searah: maksimal N posisi SELL atau BUY sekaligus (coba N = 4, 5, 6) | 1 | gagal | 23 Okt 2026: N 4/5/6 (slot & pos) memangkas DD tetapi rasio 2024-skrg -20% s.d. -50%, total R -29% s.d. -48% |
| 2 | Sinyal LOW conviction dilewati atau risiko setengah (replay penuh, slot ikut berubah) | 1 | gagal | 23 Okt 2026: lewati rasio -3%/-5%; risiko 1/2 -1% (lama) / +13% (baru). Tinjau ulang 30 Okt (v2): risiko 1/2 -2%/+4%, tetap gagal |
| 3 | Filter short lebih ketat: short hanya jika tren BTC juga turun | 2 | gagal | 30 Okt 2026 (v2): A (BTC turun) rasio -37%/-40%, B (blok BTC naik) -8%/-21%, DD naik. Slot terisi BUY lebih lemah |
| 4 | Open interest Binance (arsip metrics data.binance.vision): breakout dengan OI naik vs turun | 2 | antri | Data baru, belum dipakai bot |
| 8 | Ukuran risiko mengikuti jumlah posisi terbuka (risiko per trade turun saat banyak posisi searah) | 3 | antri |  |
| 9 | Trailing stop 48 / 96 candle vs 72 sekarang | 4 | antri | Parameter inti, butuh bukti sangat kuat |
| 10 | Model ML (uji ulang bulanan otomatis di laporan angka) | - | perlu-data | Okt 2026: belum mengalahkan label 4 faktor. 30 Okt 2026 (v2): ML terbaik 0,18R vs label 0,32R |
| 11 | Sinyal SELL LOW conviction dilewati (BUY LOW tetap), replay penuh | 2 | gagal | 30 Okt 2026 (v2): lewati rasio -5%/-26%; risiko 1/2 -1%/+4%. Di v2 SELL LOW +0,02R (2024-skrg) |
| 12 | Batas posisi searah hanya untuk SELL (BUY bebas), replay penuh | 3 | antri | Dari ide #1: batas semua arah memotong tren BUY besar di 2024-2026 |
| 19 | Risiko SELL 0,5% (semua label), BUY tetap 1% — slot tidak berubah | 2 | antri | 30 Okt 2026: SELL 2024-skrg +0,06R/trade, DD 18,3R; filter SELL (#3, #11) gagal karena slot terisi sinyal lebih buruk |
| 20 | Analisis MEDIUM melemah 2025-2026: faktor mana yang bergeser | 3 | antri | 30 Okt 2026: MEDIUM +0,007R vs LOW +0,045R (2025-2026) |
