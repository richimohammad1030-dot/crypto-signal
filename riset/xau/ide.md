# Daftar ide riset · XAU

Status: `antri` (belum diuji) · `diuji` (sedang) · `perlu-data` · `uji-maju` (lolos tahap 1-3) · `lolos` (siap diusulkan) · `gagal` · `dipasang`
Ide dari literatur ditandai `[lit]` (nilai tambah, tidak wajib). Aturan lengkap: `riset/ATURAN_BERSAMA.md`.
Prioritas: 1 = paling penting.
Nomor ide tetap mengikuti daftar awal agar rujukan di jurnal riset tidak berubah.

| # | Ide | Prioritas | Status | Catatan |
|---|---|---|---|---|
| 5 | Filter lebar range 04:00-07:00 dibanding ATR (lewati range terlalu sempit/lebar) | 2 | gagal | 30 Okt 2026: ujung sempit/lebar tetap untung; R/DD 2026 turun di semua varian |
| 6 | Lewati hari dengan news USD dampak tinggi sebelum 23:00 WIB | 3 | antri | Kalender ForexFactory hanya minggu berjalan; perlu sumber histori |
| 7 | Target TP 3R atau 5R vs 4R sekarang | - | gagal | Audit 30 Okt 2026 (2015-2021): TP 0,5-6R & tanpa TP semua -23 s.d. -31R/thn (juara -25) |
| 13 | Hanya satu sisi OCO yang searah tren harian (misalnya close H1 vs EMA200 H1) | 2 | gagal | 30 Okt 2026: EMA200 merusak 2025; EMA50/100 sensitif periode, kalah di ≥4/7 kuartal; sisi unggul berganti antar tahun |
| 14 | Jam tutup posisi 21:00 atau 01:00 WIB vs 23:00 sekarang | - | gagal | Audit 30 Okt 2026 (2015-2021): tutup 20:00-04:00 WIB semua -19 s.d. -24R/thn; tidak mengubah rugi |
| 15 | Lewati hari tertentu (Senin atau Jumat) | - | gagal | Audit 30 Okt 2026: hari terburuk berganti (Setra Kamis, 2015-2026 Rabu); lewati 1 hari -15 s.d. -26R/thn |
| 16 | Range 03:00-07:00 atau 05:00-08:00 vs 04:00-07:00 sekarang | - | gagal | Audit 30 Okt 2026 (2015-2021): range 1-6 candle, pasang 08/09/10/14/19 WIB semua negatif (-9 s.d. -46R/thn) |
| 17 | SL 1,2 atau 1,8 x ATR vs 1,5 sekarang | - | gagal | Audit 30 Okt 2026 (2015-2021): SL 1-3 ATR & SL di sisi range semua negatif; SL 2,5 ATR -11R/thn (kurang rugi, tetap rugi) |
| 18 | Lewati hari dengan rasio range/ATR di zona 0,88-1,06 (kuintil K2 2025) | 4 | antri | Negatif di 2025 (-15,2R) dan 2026 (-11,2R), tapi pola tak monoton; uji ulang setelah ≥ 2 kuartal data baru |
| 21 | Filter rezim volatilitas: trade hanya jika ATR harian/H1 relatif terhadap harga di atas ambang (mis. ≥ persentil 50 setahun), atau saat tren emas kuat | - | gagal | Audit 30 Okt 2026: versi relatif (persentil/rata 1 thn, ATR D1) negatif 2015-2021; versi absolut/biaya (K1-K4) P uji 0,54-0,68 [lit] Lundström, Day trading returns across volatility states |
| 22 | **K6**: OCO tetap 2 sisi, hari dilewati jika sisi LAWAN tren H1 EMA200 yang terisi duluan (praktik: sisi lawan lot minimum sebagai pemicu batal). Varian K6b: sisi lawan risiko 1/2 | 1 | dipasang | 31 Okt 2026: dipasang atas keputusan pemilik (risiko 1%, live 2 Nov 2026), replay bot = riset IDENTIK (Setra 233, Dukascopy 1.476 trade). Audit 30 Okt 2026: P uji 0,939 (K6b 0,946), Setra R/DD 3,93 vs juara 2,37; tetap -2R/thn di 2015-2021. Uji maju: ≥ 6 minggu & ≥ 20 trade sejak 30 Okt 2026 |
| 23 | Bot: tentukan sisi terisi dari candle 1m/5m Setra bila candle H1 menyentuh high DAN low range (sekarang selalu BUY) | 1 | antri | Perbaikan akurasi, bukan strategi. Audit 30 Okt 2026: 6,2% hari ambigu, SELL duluan 47/86 (2022-skrg); backtest Setra +43 → +29R/thn |
| 24 | Resolusi M1 hari ambigu 2015-2021 (101 hari) agar angka periode pilih tidak optimis | 3 | antri | `eksperimen/audit_m1.py` (unduhan Dukascopy dibatasi ±1 hari/menit) |
| 25 | Analog/rezim walk-forward: pilih varian bulanan dari periode masa lalu yang mirip (tren, volatilitas) | - | gagal | 31 Okt 2026: sejak 2018 analog k=24 rasio 1,81 vs K6 tetap 1,99 (P 0,49); k kecil jauh lebih buruk |
| 26 | Logika tren harian (Donchian/EMA/momentum D1) dalam jendela tetap 07:00-23:00 | - | gagal | 31 Okt 2026: 880 varian, 0 lolos di 2015-2021; terbaik -4,5R/thn di 2022-Jan 2025 |
| 27 | Musiman kalender (lewati/pilih bulan tertentu) | - | gagal | 31 Okt 2026: peringkat bulan tidak konsisten antar periode (korelasi +0,26 / -0,13) |
| 28 | Strategi literatur dalam jendela 07-23: bias jam (selalu SELL/BUY), pembalikan overnight, momentum intraday, fade range Asia OCO, tren EMA200 market [lit] | - | gagal | 31 Okt 2026: tidak lulus kriteria pemilik di 2015-2021 (kecuali RSI2); lihat log |
| 29 | Mean reversion RSI(2) H1 jam 07:00 (beli oversold / jual overbought, SL 3 ATR) [lit] Connors | - | gagal | 31 Okt 2026: lulus kriteria pemilik 2015-2021 (win 50%, PF 1,06) tetapi PF 0,95-1,01 di 2022 - Jan 2025 |
| 30 | Portofolio K6 + RSI2 fade (tren + mean reversion saling melengkapi) | 2 | perlu-data | 31 Okt 2026 hipotesis pasca-lihat: 6 trade/mg, win 44%, PF 1,07, 8/12 tahun; butuh uji maju |
| 31 | K6 / RSI2 / portofolio dengan exit RR tinggi (kriteria longgar win ≥ 35%, RR ≥ 1,5) | - | gagal | 31 Okt 2026: 1/3.956 lulus di 2015-2021, gagal di uji (kalah beruntun 21) |
| 32 | Pemilih rezim (bulanan/harian: efficiency ratio × volatilitas) antara K6 dan RSI2 | - | gagal | 31 Okt 2026: rezim rata-rata 1,7 bln, persistensi 41%; pemilih walk-forward -21R; aturan kebalikan sama baiknya |
| 33 | Tahun analog (pola bulanan tahun mirip) | - | gagal | 31 Okt 2026: arah benar 48% vs selalu naik 53% |
