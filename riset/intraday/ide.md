# Daftar ide riset · INTRADAY

Status: `antri` (belum diuji) · `diuji` (sedang) · `lolos` (kandidat penantang) · `gagal` · `perlu-data` · `dipasang`
Prioritas: 1 = paling penting. Nomor I-xx tetap agar rujukan di jurnal riset tidak berubah.

| # | Ide | Prioritas | Status | Catatan |
|---|---|---|---|---|
| I-01 | Modul A: kurangi sinyal yang tidak terisi (±10% terisi). Filter tambahan RSI2 < 2, atau limit 1,0-1,25 ATR | 1 | antri | ±60 order dikirim/minggu, terlalu banyak alert untuk anggota |
| I-02 | Modul B: kadaluarsa 6 / 8 jam vs 12 jam (order menunggu terlalu lama memblok slot) | 1 | antri | Fill modul B ±60%, tetapi order 12 jam menahan slot |
| I-03 | Batas order menunggu per modul (mis. A maks 4, B maks 8) agar A tidak mengusir B atau sebaliknya | 2 | antri | |
| I-04 | Rem harian: berhenti kirim order baru setelah 2 SL di hari yang sama | 2 | antri | Hari terburuk = beberapa SL beruntun saat crash |
| I-05 | Filter open interest untuk modul B: lewati saat OI turun tajam 1-4 jam sebelum 07:00 (likuidasi berjalan) | 3 | perlu-data | Data metrics Binance 2022+ hanya untuk 20 koin (lihat log) |
| I-06 | Modul B short tanpa syarat funding > 0 (filter BTC mungkin sudah cukup) | 3 | antri | B-short +0,12R/trade |
| I-07 | Prioritas order: volatilitas (vr) tertinggi dulu vs market cap | 3 | antri | Di uji awal prioritas vr kadang lebih baik di slot besar |
| I-08 | Risiko per trade berbeda per modul (mis. B 1%, A 0,5%) | 4 | antri | Ukur dengan ekuitas compounding, bukan R |
| I-09 | Slot ke-3 hanya untuk order high conviction (B vr ≥ 1,3, modul A, modul B, top 10) | - | gagal | 27 Okt 2026: aturan terbaik di 2020-2023 (B vr≥1,3) rasio baru 1,74 vs juara 1,80 |
| I-10 | Optimasi parameter modul B (kedalaman limit, SL, TP, ambang vr) | - | gagal | 27 Okt 2026: terbaik di 2020-2023 tidak lebih baik di 2024-skrg; 81 tetangga juara semua positif |
