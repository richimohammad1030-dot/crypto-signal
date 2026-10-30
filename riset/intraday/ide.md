# Daftar ide riset · INTRADAY

Status: `antri` (belum diuji) · `diuji` (sedang) · `perlu-data` · `uji-maju` (lolos tahap 1-3) · `lolos` (siap diusulkan) · `gagal` · `dipasang`
Ide dari literatur ditandai `[lit]` (nilai tambah, tidak wajib). Aturan lengkap: `riset/ATURAN_BERSAMA.md`.
Prioritas: 1 = paling penting. Nomor I-xx tetap agar rujukan di jurnal riset tidak berubah.

| # | Ide | Prioritas | Status | Catatan |
|---|---|---|---|---|
| I-01 | Modul A: kurangi sinyal yang tidak terisi (±10% terisi) | 1 | dipasang | 27 Okt 2026 (v2): limit 0,25 ATR, berlaku 2 jam, ATR ≥ 1,5%: fill total 14% → 71%, alert ±11/minggu |
| I-02 | Modul B: kadaluarsa 6 / 8 jam vs 12 jam (order menunggu terlalu lama memblok slot) | - | gagal | 30 Okt 2026: 4/6/8/10/16 jam semua lebih buruk; 12 jam puncak (rasio lama 5,66, baru 2,00); 8 jam rasio baru 1,19 |
| I-03 | Batas order menunggu per modul (mis. A maks 1, B maks 2) agar A tidak mengusir B atau sebaliknya | - | gagal | 30 Okt 2026: 6 varian; terbaik A≤1 rasio baru +14% tetapi lama -10%, 3/7 tahun; batas B merusak |
| I-04 | Rem harian: berhenti kirim order baru setelah 2 SL di hari yang sama | 2 | antri | Hari terburuk = beberapa SL beruntun saat crash |
| I-05 | Filter open interest untuk modul B: lewati saat OI turun tajam 1-4 jam sebelum 07:00 (likuidasi berjalan) | 3 | perlu-data | Data metrics Binance 2022+ hanya untuk 20 koin (lihat log) |
| I-06 | Modul B short tanpa syarat funding > 0 (filter BTC mungkin sudah cukup) | 3 | antri | B-short +0,12R/trade |
| I-07 | Prioritas order: volatilitas (vr) tertinggi dulu vs market cap | 3 | antri | Di uji awal prioritas vr kadang lebih baik di slot besar |
| I-08 | Risiko per trade berbeda per modul (mis. B 1%, A 0,5%) | 4 | antri | Ukur dengan ekuitas compounding, bukan R |
| I-09 | Slot ke-3 hanya untuk order high conviction (B vr ≥ 1,3, modul A, modul B, top 10) | - | gagal | 27 Okt 2026 (v1): aturan terbaik di 2020-2023 (B vr≥1,3) rasio baru 1,74 vs juara 1,80 |
| I-11 | Conviction HARIAN: hari tertentu 3 posisi, lainnya 2 (fitur 07:00: jumlah kandidat B, volatilitas kandidat, volatilitas BTC) | - | gagal | 27 Okt 2026 (modul B): 18 aturan; terbaik di 2020-2023 rasio baru 0,79 vs tetap 3 posisi 1,41 |
| I-12 | Modul A: tetangga v2 (limit 0,25-0,5 ATR, berlaku 30-120 mnt) dengan ATR ≥ 1,5% semuanya rasio baru 1,6-2,8; uji ATR ≥ 1,25% / 2% | 3 | antri | Filter volatilitas paling menentukan kualitas modul A |
| I-13 | Modul B saja (tanpa A) sebagai versi "sinyal pagi" murni untuk channel | 4 | antri | 3 posisi: fill 61%, rasio baru 1,41, CAGR 1% ±30% (lebih rendah dari v2) |
| I-15 | Modul A hanya untuk peringkat 1-25, atau dimatikan (B saja), dinilai DENGAN daftar koin sesuai masanya | 1 | perlu-data | 30 Okt 2026 PIT OOS: A 1-25 + B rasio 1,29 vs juara 0,65 (P 0,96), B saja 1,03; IS tidak membedakan → menunggu keputusan pemilik / uji maju |
| I-17 | Gaya scalping: SL/TP tetap 1:1 untuk modul A (40 varian) dan B (12 varian), PIT | - | gagal | 30 Okt 2026: A terbaik IS OOS +0,009R; B 1:1 rasio 0,78 vs 1,03 |
| I-16 | Batas risiko gabungan dengan swing: lewati order intraday di koin yang sedang dipegang swing searah | 2 | antri | 1.737 trade tumpang tindih; DD gabungan 25% |
| I-10 | Optimasi parameter modul B (kedalaman limit, SL, TP, ambang vr) | - | gagal | 27 Okt 2026: terbaik di 2020-2023 tidak lebih baik di 2024-skrg; 81 tetangga juara semua positif |
| I-14 | Modul A: syarat tren BTC H1 searah (seperti modul B) atau jeda modul A saat BTC tren turun | 2 | antri | Review 30 Okt 2026: modul A 2025 -6,1R, 2026 +0,7R; 6 bln terakhir +0,013R/trade vs B-long +0,16R |
