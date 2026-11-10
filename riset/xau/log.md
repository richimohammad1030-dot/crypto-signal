# Jurnal riset · XAU

Catatan setiap ide yang diuji: tanggal, ide, angka utama, keputusan. Ide yang gagal tidak diuji ulang
kecuali ada data baru yang relevan.

## 2026-10-20 · Fondasi
- **Backtest XAU** (Feb 2025 - Okt 2026): 425 trade, win rate 41%, +0,18R/trade kotor (+0,16R setelah biaya 0,40 USD),
  drawdown terburuk 14,1R. Histori sumber data hanya tersedia sejak Feb 2025.

## 2026-10-23 · Pemisahan riset
- Riset XAU dipisah dari crypto: routine, prosedur, daftar ide, jurnal, dan laporan sendiri.
  Kriteria lolos disesuaikan dengan data XAU yang hanya ±20 bulan (lihat riset/xau/PROSEDUR.md).

## 2026-10-30 · Review bulanan Oktober
- **Juara** (Feb 2025 - 29 Okt 2026, bersih biaya 0,40 USD): 433 trade, +66,4R, +0,153R/trade, win 41%, DD 15,2R, R/DD 4,37.
  P1 2025 R/DD 1,81; P2 2026 R/DD 3,22. 2026Q4 sejauh ini -1,1R (21 trade). Keluar: SL 55%, TP 7%, tutup 23:00 38% (+1,17R kotor).
- **Live vs backtest** sejak 18 Okt 2026: 9 trade, sisi dan R identik 9/9 (total -0,74R kotor).
- **#5 Filter lebar range/ATR** (ambang kuantil 20/80% dari 2025): lewati sempit R/DD 1,81→1,68 dan 3,22→2,71; lewati lebar
  1,95 dan 2,87; keduanya 1,58 dan 1,15. **GAGAL**: ujung distribusi tetap untung, kalah di 4-6 dari 7 kuartal.
  Zona 0,88-1,06 negatif di kedua paruh → ide baru #18 (prioritas rendah).
- **#13 Sisi searah tren** (EMA200/100/50 H1; satu sisi atau lawan tren risiko 1/2): EMA200 satu sisi R/DD 1,03 / 3,19;
  terbaik EMA50 lawan tren 1/2 3,17 / 3,69 tapi hanya tidak lebih buruk di 3/7 kuartal. **GAGAL**; sensitif terhadap periode EMA.
- Kandidat penantang: tidak ada. Usulan menunggu persetujuan: tidak ada.

## 2026-10-30 · Data terkunci Dukascopy 2015-2026 (fondasi riset diperkuat, chat bersama pemilik)
Sumber: `riset/unduh_xau_panjang.py` (Dukascopy BID, 69.952 candle H1, Jan 2015 - Okt 2026). Validasi vs Setra (Feb 2025-skrg):
418 dari 433 trade sama waktu buka, arah hasil sama 99%; hasil +68,7R vs +66,4R (bersih). Data Dukascopy setara data bot.
- **Juara di 2015 - Jan 2025 (data terkunci): RUGI.** 2.579 trade, win 34,4%, -0,061R/trade bersih, total -157R, DD 222R.
  Per tahun (R bersih): 2015 -26 · 2016 -38 · 2017 -28 · 2018 -38 · 2019 -35 · 2020 +3 · 2021 -14 · 2022 +5 · 2023 -25 ·
  2024 +20 · 2025 +48 · 2026 +38. Positif hanya 5 dari 12 tahun.
- Kotor (tanpa biaya) 2015-2023 ±0 (-0,06 s.d. +0,08R/trade); biaya tetap 0,40 USD = 0,08-0,12R saat r0 hanya 3-5 USD.
  Edge muncul saat volatilitas emas tinggi: r0/harga 0,44% (2025) dan 0,62% (2026) vs 0,26-0,40% sebelumnya;
  2024 (+0,126R kotor) dan 2020/2022 juga relatif lebih baik.
- Kesimpulan: edge juara XAU kemungkinan besar bergantung pada rezim volatilitas tinggi 2024-2026 (reli emas), bukan permanen.
  Ide baru #21 (filter rezim volatilitas, prioritas 1). Hasil periode Setra tetap dipakai sebagai uji utama; data terkunci untuk
  konfirmasi sesuai ATURAN_BERSAMA (filter #21 boleh dirancang dengan alasan ekonomi, lalu dicek sekali di 2015 - Jan 2025).

## 2026-10-30 · AUDIT MENYELURUH (permintaan pemilik, chat) · data Dukascopy 2015-2026 + Setra
Skrip: `riset/xau/eksperimen/audit_*.py` (mesin `audit_mesin.py`, identik trade-per-trade dengan `backtest_xau.py` di Setra 433/433
dan Dukascopy 3.024/3.024). Biaya 0,40 USD/trade, stress slip +0,20 USD. Pembagian data ditetapkan SEBELUM eksplorasi:
**pilih 2015-2021 · uji 2022 - Jan 2025 (Dukascopy) · konfirmasi Feb 2025 - skrg (Setra, data sambung untuk pemanasan fitur)**.
Catatan: dengan audit ini data Dukascopy 2015 - Jan 2025 **sudah terpakai** untuk memilih/menguji (bukan lagi data terkunci).

**1. Reproduksi & validasi**
- Setra: 433 trade, +66,4R, +0,153R/trade, DD 15,2R, R/DD 4,37 (cocok dengan log). Dukascopy 2015-Jan 2025: 2.579 trade, -0,061R, -157R (cocok).
- Setra vs Dukascopy (periode sama, 19 Feb 2025 - 29 Okt 2026): candle 10.308 sama waktu, selisih close median 0,26 USD (bid vs mid),
  korelasi rentang 0,998; trade 433/433 hari sama, arah 98,4%, arah+tanda hasil 97,2%, korelasi R 0,977.
  **Koreksi log 30 Okt**: pada periode yang sama Dukascopy +61,0R vs Setra +66,4R (angka +68,7R memakai periode sejak 1 Feb, 445 trade).
- Bibit data `riset/data/xau_dukascopy_h1.json.gz` ternyata tidak pernah ter-commit (`.gitignore: data/`); kini di-commit (s.d. Sep 2026).

**2. Kelemahan model: candle ambigu (PENTING)**
- 6,2% hari (2015-skrg 187/3.023; era Setra 38/444 = 8,6%; 2022-skrg 86 hari) candle H1 saat terisi menyentuh high DAN low range. Bot & backtest selalu memilih BUY.
- Urutan sebenarnya dari candle M1 Dukascopy (`audit_m1.py`, hasil `ambigu_m1_2022_2026.json`): 2022-skrg BUY duluan 39, **SELL duluan 47**;
  Setra-era BUY 14 / SELL 24. Asumsi BUY melebih-lebihkan hasil (emas naik): juara Feb 2025-skrg **+43,3 → +29,3R/thn, DD 15,2 → 21,5R,
  R/DD 4,96 → 2,37**; 2022-Jan 2025 +5,8 → ±0R/thn. 2015-2021 belum diresolusi (angka = batas atas). Pencatatan live (`hist`) juga
  bisa salah sisi di hari ambigu. Semua angka di bawah memakai urutan M1 untuk 2022-skrg.

**3. Diagnosa juara (2015-skrg, bersih)**
- Per tahun (R): 2015 -26 · 2016 -38 · 2017 -29 · 2018 -38 · 2019 -35 · 2020 +4 · 2021 -14 · 2022 -3 · 2023 -22 · 2024 +10 · 2025 +33 · 2026 +32.
  Untung 4 dari 12 tahun. Kotor (tanpa biaya) 2015-2023 ±0 (-0,06 s.d. +0,08R/trade); biaya 0,05-0,13R/trade sebelum 2024.
- Kuartal: sangat acak (2022Q4 +33R, 2023Q1-Q2 -36R, 2025Q1 +37R). Keluar: SL 58% (-1,075R), TP 6% (+3,92R), tutup 23:00 36% (+0,98R).
- Arah: BUY -0,001R/trade, SELL -0,061R. Hari: tidak konsisten (Setra: Kamis terburuk; 12 tahun: Rabu terburuk). Jam terisi 07-08 WIB = 90% trade.
- Rezim volatilitas: kuintil ATR H1/harga teratas kotor +0,137R, kuintil lain ±0; tetapi per periode TIDAK stabil (≥0,45%: 2015-21 +0,11,
  2022-25 -0,24, Setra +0,03). Versi relatif (ATR vs rata-rata/persentil 1 tahun) tidak monoton.
- **Tren H1 EMA200** satu-satunya pemisah yang konsisten di ketiga periode: trade searah vs lawan (kotor) 2015-21 +0,075 / -0,078,
  2022-25 +0,171 / -0,011, Setra +0,301 / +0,059. D1 EMA50 tidak konsisten (terbalik di Setra).
- Hari terburuk: kalah beruntun maks 21; DD terdalam 226R (2015-2023).

**4. Eksplorasi (seleksi hanya 2015-2021; 75 varian satu-dimensi + grid 126 + tren 12 + kombinasi 24)**
- Tetap NEGATIF di 2015-2021 (R/thn; juara -25,2): TP 0,5/1/1,5/2/3/6R/tanpa TP -23 s.d. -31 · SL 1/1,25/1,75/2/2,5/3 ATR -10 s.d. -54 ·
  SL di sisi range -32 s.d. -190 · tutup 20:00-04:00 WIB -19 s.d. -24 · range 1-6 candle -13 s.d. -29 · pasang 08/09/10 WIB -9 s.d. -14 ·
  London 14 WIB -17/-27 · NY 19 WIB -46 · buffer entry 0,1-0,5 ATR -24 s.d. -30 · breakeven 1R/2R -23/-25 · lewati 1 hari -15 s.d. -26 ·
  hanya searah tren (1 sisi) -19 s.d. -25 · ATR vs 1 thn ≥ 0,8-1,2 -4 s.d. -23 · persentil 1 thn ≥ 30-70 -6 s.d. -17 ·
  ATR D1 ≥ 0,8-1,4% -9 s.d. -27 · filter kurva ekuitas (N 20-150) -6 s.d. -13.
- Positif hanya filter volatilitas absolut/biaya dengan trade sangat sedikit: ATR H1 ≥ 0,35% +1,2R/thn (2,3 trade/bln); biaya ≤ 0,05R
  (SL ≥ 8 USD) +3,1R/thn (2,6/bln). Grid terbaik (biaya ≤ 0,04-0,05R + range 04-08 WIB, pasang 08): K1-K4 diuji di 2022-Jan 2025:
  P_rasio vs juara 0,54-0,68 → **GAGAL** (tanpa 2% terbaik negatif). Di Setra filter ini hampir tidak aktif (emas mahal → SL selalu besar).
- **K6: OCO tetap 2 sisi, hari dilewati bila sisi LAWAN tren H1 EMA200 yang terisi duluan** (K6b: sisi lawan risiko 1/2).
  Catatan jujur: pilihan EMA200 dipengaruhi diagnosa semua periode; varian terbaik menurut 2015-2021 saja (D1 EMA20) GAGAL di uji
  (P 0,36). Tetangga H1 EMA50/100/150/200/300 (bobot 0 dan 0,5) semuanya lebih baik dari juara di uji (P 0,85-0,93); EMA400 tidak.

**5. Hasil kandidat (bersih biaya; urutan M1 2022-skrg; risiko 1% kecuali disebut)**

| | Periode | Trade/bln | Win | RR | Exp | PF | R/thn | DD R | DD% 1% | CAGR 1% | DD% 0,5% | CAGR 0,5% | W/L maks | Bln+ | Tanpa 2% |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Juara | 2015-2021 | 21,4 | 34,2% | 1,64 | -0,098 | 0,85 | -25,2 | 200,7 | 88,6% | -24,5% | 64,9% | -12,5% | 5/21 | 37% | -317 |
| Juara | 2022-Jan25 | 21,4 | 34,0% | 1,94 | ±0,000 | 1,00 | ±0,0 | 45,7 | 40,8% | -3,1% | 21,8% | -0,8% | 6/15 | 38% | -63 |
| Juara | Setra Feb25-skrg | 21,3 | 39,2% | 1,85 | +0,115 | 1,19 | +29,3 | 21,5 | 19,5% | +29,8% | 10,2% | +14,8% | 4/8 | 67% | +15 |
| K6 | 2015-2021 | 10,0 | 35,2% | 1,79 | -0,017 | 0,97 | -2,0 | 39,3 | 36,6% | -3,4% | 19,1% | -1,4% | 5/13 | 48% | -81 |
| K6 | 2022-Jan25 | 10,8 | 36,2% | 2,01 | +0,090 | 1,14 | +11,6 | 26,7 | 23,8% | +10,4% | 12,6% | +5,5% | 5/17 | 51% | +4 |
| K6 | Setra Feb25-skrg | 11,5 | 40,2% | 2,05 | +0,226 | 1,38 | +31,2 | 13,8 | 13,4% | +33,9% | 6,8% | +16,3% | 5/11 | 67% | +34 |
| K6b | 2015-2021 | 21,4 | 34,2% | 1,72 | -0,053 | 0,89 | -13,6 | 117,1 | 72,2% | -14,3% | 45,8% | -7,0% | 5/21 | 43% | -236 |
| K6b | 2022-Jan25 | 21,4 | 34,0% | 2,03 | +0,023 | 1,05 | +5,8 | 31,3 | 27,5% | +3,8% | 14,7% | +2,4% | 6/15 | 49% | -45 |
| K6b | Setra Feb25-skrg | 21,3 | 39,2% | 1,96 | +0,119 | 1,26 | +30,3 | 16,5 | 15,2% | +32,2% | 7,9% | +15,6% | 4/8 | 67% | +17 |

Per tahun K6 (R): 2015 +3 · 2016 -8 · 2017 +14 · 2018 -10 · 2019 -11 · 2020 +5 · 2021 -6 · 2022 +16 · 2023 ±0 · 2024 +10 · 2025 +47 · 2026 +18.
Signifikansi vs juara (P_rasio): K6 uji **0,939**, Setra 0,768 · K6b uji **0,946**, Setra 0,848. Slip +0,20 USD uji: juara -7,5 · K6 +7,8 · K6b +0,1 R/thn.
Aturan henti DD 20-25R hanya asuransi: mulai 2021/2023 akan berhenti padahal akhirnya +80-90R.

**6. Kesimpulan**: tidak ada edge permanen. Edge bersyarat: muncul di rezim emas tren kuat + volatil (2020, 2024-2026); di rezim tenang
kotor ±0 dan biaya membuatnya rugi. K6 (lewati hari bila sisi lawan tren EMA200 H1 terisi duluan) konsisten mengurangi kerugian dan
lolos tahap 1-3 di pembagian audit (status `uji-maju`), tetapi tetap sedikit rugi di 2015-2021. Pilihan & angka diserahkan ke pemilik;
bot live TIDAK diubah.

## 2026-10-31 · Analog/rezim, musiman, dan logika tren harian (permintaan pemilik, chat)
**Aturan tetap pemilik: sinyal 07:00 WIB dan semua ditutup 23:00 WIB tidak boleh diubah.** Semua kandidat di bawah mematuhinya.
Angka bersih biaya 0,40 USD; varian OCO memakai urutan M1 untuk candle ambigu 2022-skrg.
- **Logika tren harian dalam jendela 07:00-23:00** (`eksperimen/harian_mesin.py`, `harian_scan.py`; 880 varian: arah Donchian 10/20/55,
  EMA D1 20/50/100/200, momentum 20/60/120 hari, selalu long × masuk market/limit 0,25-1 ATR/stop × SL 1-3 ATR × TP 1/2/4R/tanpa;
  seleksi 2015-2021): **0 varian** lolos (≥ 300 trade & positif tanpa 2% terbaik); hanya 3/880 positif; terbaik (momentum 60 hari,
  market, SL 3 ATR, TP 4R) +0,004R/trade di 2015-2021, **-4,5R/thn di 2022-Jan 2025**, +14,2R/thn Setra. "Selalu BUY 07:00-23:00" pun
  rugi 2015-2021 (emas naik ±50% tetapi kenaikannya tidak terjadi di jendela ini setelah biaya). **GAGAL** (ide #26).
- Pembanding saja (melanggar aturan 23:00, bukan kandidat): swing emas multi-hari gaya bot crypto (`swing_pembanding.py`): positif hampir
  tiap tahun tetapi kecil, +0,049R/trade, ±1,4 trade/bln, ±+0,8R/thn.
- **Analog/rezim walk-forward** (`eksperimen/analog_wf.py`): tiap awal bulan ciri 3-6 bulan terakhir (return 63/126 hari, ATR D1/harga,
  ATR vs 1 thn) dicocokkan ke k bulan masa lalu paling mirip (hanya data sebelum keputusan); pilih dari menu tetap (juara, K6, K6b,
  hanya BUY, hanya SELL, SL 2,5 ATR, momentum 60 harian, JEDA). Sejak Feb 2018 (adil, semua aktif):
  K6 tetap +8,0R/thn DD 35R rasio 1,99 · analog k=24 +6,2 / 30 / 1,81 (P vs K6 0,49) · k=12 +3,9 / 41 / 0,84 · k=6 +1,2 / 64 / 0,17 ·
  momentum strategi 12 bln +7,4 / 45 / 1,45 (P 0,51) · juara -3,0 / 131 / -0,20. Analog mengalahkan juara hanya karena sering memilih
  K6/JEDA; tidak mengalahkan K6 tetap, dan sangat sensitif terhadap k. **GAGAL** (ide #25).
- **Musiman kalender** (`eksperimen/musiman.py`): korelasi peringkat bulan 2015-2021 vs 2022-skrg juara +0,26 (p 0,42), K6 -0,13 (p 0,70).
  Hanya April positif di kedua periode (wajar karena kebetulan dari 12 bulan). **GAGAL** (ide #27).
- Kesimpulan: dalam aturan tetap 07:00-23:00, satu-satunya perbaikan yang bertahan tetap K6 (ide #22, uji maju).

## 2026-10-31 · K6 dipasang (keputusan pemilik: risiko 1%, "coba jalankan K6")
- Live 10 trade (19-30 Okt): 4 menang / 6 kalah, +3,3R kotor (untung dari 22 Okt +3,35R dan 30 Okt +4R). K6 akan melewati
  27 & 28 Okt (BUY lawan tren turun, keduanya -1R) → +5,3R. Sampel terlalu kecil untuk menilai.
- OCO pemilik manual (pasang 2 order, batalkan satu setelah terisi). Implementasi K6: 1 order searah tren EMA200 H1 + BATAS BATAL
  (price alert) di sisi range seberang; bot mengirim "HARI INI DILEWATI" bila batas batal tersentuh lebih dulu.
- Uji kesetaraan `riset/replay_xau.py`: bot vs riset K6 IDENTIK (Setra 233/233, Dukascopy 2015-2026 1.476/1.476 trade).
- Patokan cek kesehatan baru `riset/baseline_xau.py` (K6 2022-skrg, urutan M1, R kotor): 642 trade, win 38,3%, +0,191R, DD 24,2R,
  kalah beruntun 17. LIVE_START XAU = 2 Nov 2026 (kesehatan.py, analisis.py). analisis.py tidak menimpa patokan ini.
- XAU_RISK_PCT default 0,5 → 1 (estimasi % rekap). Strategi dikunci di `riset/xau/STRATEGI.md`.

## 2026-10-31 · Frekuensi trade K6 vs syarat pemilik "minimal 1 entry per hari" (`eksperimen/frekuensi.py`)
- Trade per minggu (minggu 5 hari bursa, 2015-skrg): juara 4,97/5 · **K6 2,40/5** (52% minggu ≤ 2 trade, 17% minggu ≥ 4) ·
  K6b (lawan risiko 1/2) dan K6c (lawan risiko 1/4) 4,97/5. Per tahun K6 2,0-2,8/5 → **tidak memenuhi syarat pemilik**.
- K6c (OCO 2 sisi tetap, sisi lawan tren EMA200 H1 risiko 1/4; titik tengah antara K6 dan K6b yang sudah diuji, bukan puncak baru):
  2015-2021 -7,8R/thn DD 76R · 2022-Jan 2025 +8,7R/thn DD 29R · Setra +30,7R/thn DD 13,9R. P_rasio vs juara: pilih 0,962,
  uji 0,943, Setra 0,812; slip +0,20 USD uji +4,0R/thn. (K6: 0,986 / 0,939 / 0,768, slip +7,8; K6b: 0,933 / 0,946 / 0,848, slip +0,1.)
- Pemasangan K6 (commit lokal a77c051) DITAHAN menunggu pilihan pemilik antara K6 (lebih kuat, ±2,4 trade/minggu) dan K6c (trade tiap hari).

## 2026-10-31 · Riset strategi alternatif (kriteria pemilik: win ≥ 40%, PF > 1, ≥ 3 trade/minggu, beruntun seimbang, mayoritas tahun untung)
Aturan tetap 07:00-23:00 WIB. Seleksi 2015-2021, uji 2022 - Jan 2025, konfirmasi Setra. Bila 2 order terisi di candle yang sama →
hasil terburuk (konservatif). Mesin `eksperimen/strat_mesin.py`; skrip `strat_scan.py` (1.152 varian), `mr_scan.py` (1.792),
`mr_uji.py`, `strat_keluarga.py`, `gabung.py`.
- Literatur [lit]: pola jam emas "topi" (Donati & Jung, CBS: naik di jam Asia, turun sisa hari) → "selalu SELL 07-23" rugi di semua
  periode (-9,6 / -18,4 / -6,4 R/thn), pola tidak berlaku 2015-2026. Pembalikan overnight-intraday (Della Corte, Kosowski & Wang 2015):
  2015-21 -2,1, uji -0,4, Setra +22 R/thn. Momentum intraday (Gao, Han, Li & Zhou 2018; Baltussen dkk. 2021): win 26-28%, 2015-21
  -26,6 R/thn. Fade range Asia OCO (limit): win 53-55% tetapi PF 0,83-0,95 di semua periode. Tren EMA200 market: 2015-21 -2,0.
- Lulus kriteria pemilik di 2015-2021: hanya keluarga **RSI(2) fade** (mean reversion H1 jam 07:00; 67 varian, tetangga stabil),
  mis. ambang kuantil 35% (beli RSI2 ≤ 43,8 / jual ≥ 71,2), market, SL 3 ATR, TP 2R: 3,5 trade/mg, win 50%, PF 1,06, W/L 11/9,
  5/7 tahun. **Gagal di uji 2022 - Jan 2025**: PF 0,95-1,01, 2023 -18 s.d. -30R, P_rasio vs juara 0,37-0,52; Setra +6 s.d. +11 R/thn.
  Edge sangat tipis (PF ±1,04 selama 12 tahun; negatif dengan slip +0,20 USD di uji). **GAGAL** (ide #29).
- **Hipotesis** (lahir setelah melihat semua periode, BUKAN bukti): portofolio K6 + RSI2 fade (saling melengkapi: MR kuat 2015-21,
  tren kuat 2022-26), risiko 1% masing-masing: 6 trade/mg, win 44%, PF 1,07, +10,4 R/thn, DD 42R (36%), W/L 7/12, 8/12 tahun untung
  (2019 -16, 2023 -17). Per periode PF 1,01 / 1,08 / 1,25. Perlu uji maju (ide #30).
- Kesimpulan: dalam jendela tetap 07:00-23:00 dengan biaya 0,40 USD, tidak ditemukan strategi yang memenuhi semua kriteria pemilik
  secara konsisten di periode pilih DAN uji. Edge intraday emas bergantung rezim: mean reversion di masa tenang, tren di masa volatil.

## 2026-10-31 · Kriteria longgar: win ≥ 35% + RR terjamin (`eksperimen/rr_scan.py`)
Kriteria (ditetapkan sebelum melihat hasil): win ≥ 35%, RR tercapai ≥ 1,5, PF > 1,05, ≥ 3 trade/mg, kalah beruntun ≤ 2 × menang
beruntun, mayoritas tahun untung. 3.956 kandidat: K6 (SL 1-2 ATR × TP 2/3/4/6R/tanpa), RSI2 fade (kuantil 30/35/40%, ± filter tren,
SL 1,5-3 ATR, TP 1,5/2/3R/tanpa), portofolio K6 + RSI2 (bobot RSI2 1 / 0,5). Seleksi 2015-2021.
- Lulus di 2015-2021: **1** (portofolio K6 SL 1,25 tanpa TP + RSI2 35% searah tren SL 3 TP 3R): pilih win 40%, RR 1,58, PF 1,05,
  W/L 8/16; **uji gagal** (W/L 5/21, P_rasio vs juara 0,77); Setra win 41%, RR 1,92, PF 1,35. 12 thn: win 39%, RR 1,69, PF 1,10,
  +12,1 R/thn, DD 48R (46% ekuitas pada 1%), 8/12 tahun.
- Pola: K6 punya RR ±2 tetapi win 32-35% dan hanya 2,3 trade/mg; RSI2 punya win ±50% tetapi RR ±1,05. Menaikkan TP tidak
  menaikkan RR K6 (exit nyata = tutup 23:00); gabungan keduanya berakhir di win ±39% / RR ±1,6 / PF ±1,04 di masa emas tenang.
- Kesimpulan: kriteria longgar pun tidak terpenuhi secara konsisten. GAGAL (ide #31).

## 2026-10-31 · Bot multi-strategi berbasis rezim: bisakah rezim dideteksi? (`eksperimen/rezim_bulanan.py`, `rezim_harian.py`)
- Rezim bulanan (efficiency ratio close harian × ATR D1/harga, ambang median 2015-2021), Jan 2015 - Okt 2026: TREN-VOLATIL 44 bln,
  SIDEWAYS-VOLATIL 42, TREN-TENANG 30, SIDEWAYS-TENANG 25. **82 pergantian dalam 141 bulan, rata-rata 1,7 bln, terpanjang 5 bln**;
  peluang rezim bulan depan = bulan ini 41%.
- Edge per rezim NYATA bila rezim diketahui di bulan yang sama (R bersih/bln): TREN K6 +1,4/+2,2 vs RSI2 -0,7/+0,6; SIDEWAYS-VOLATIL
  RSI2 +1,1 vs K6 -0,9. Pilihan sempurna 2016-2026: +380R vs K6 saja +67R, RSI2 saja +41R.
- Tetapi rezim BULAN SEBELUMNYA hampir tidak memberi informasi; pemilih rezim walk-forward: **-21R** (lebih buruk dari strategi tunggal).
- Pemilih harian (ER 5/10/20/40 hari, K6 bila tren, RSI2 bila sideways): tidak konsisten; aturan KEBALIKAN (kontrol) sering sama/lebih
  baik (N=40: pilih -5,2 vs kontrol +7,4 R/thn; uji +11,3 vs +0,9). Deteksi rezim dari harga = noise pada skala ini.
- Deteksi lewat performa strategi: dengan sd R per trade ±1,4 dan selisih edge ±0,1R, butuh ±500 trade (±2 tahun) untuk membedakan
  "edge hilang" dari "kalah beruntun biasa" (95%); rezim rata-rata hanya ±1,7 bulan (±20 trade).
- **Tahun analog** (bulan m tahun Y diprediksi dari tahun lalu paling mirip di bulan 1..m-1): arah benar 42/88 = 48% vs selalu "naik"
  53% → tanpa edge. Contoh pemilik 2021 vs 2025: korelasi return bulanan -0,17, arah sama 5/12 bulan, total -4% vs +66%.
  [lit] Musiman yang terbukti di literatur adalah bulan-kalender yang sama (Heston & Sadka 2008; Keloharju, Linnainmaa & Nyberg 2016,
  termasuk komoditas), bukan pemetaan tahun analog; untuk XAU intraday sudah diuji (ide #27, gagal).

## 2026-10-31 · Risiko 2 posisi/hari (K6 + RSI2) vs maks 1 posisi/hari (`eksperimen/dua_posisi.py`)
- Portofolio boleh 2 posisi: 41% hari trade punya 2 posisi (820 berlawanan arah, 242 searah); korelasi R harian -0,30.
  Keduanya kena SL di hari yang sama: 115 hari (4,4%, ±10×/thn). Risiko 1%+1%: rugi terburuk/hari -2,28%, DD 41%.
  Risiko 0,5%+0,5%: terburuk -1,14%/hari, DD 20%, total +61%.
- Versi "maks 1/hari, K6 diprioritaskan" yang sempat dihitung MEMAKAI INFORMASI MASA DEPAN (fill K6 belum diketahui jam 07:00) → dibuang.
- **Aturan sah (diputuskan 07:00): ada sinyal RSI2 → hanya RSI2 market (K6 tidak dipasang); tidak ada → pasang K6.**
  Risiko 1%: 4,2 trade/mg, win 47%, RR 1,22, PF 1,07, W/L maks 10/8, 9/12 tahun untung, rugi terburuk/hari -1,18%, kalah hari beruntun 8,
  DD 37% (majemuk 32%); per periode PF 1,03 / 1,10 / 1,17, R/thn +2,9 / +9,9 / +15,6. Per tahun: 2015 +2 · 2016 +3 · 2017 +10 · 2018 -4 ·
  2019 -5 · 2020 +4 · 2021 +10 · 2022 +28 · 2023 -24 · 2024 +24 · 2025 +16 · 2026 +14. Risiko 0,5%: DD 18,6%.
  Satu-satunya kandidat yang memenuhi kriteria awal pemilik (win ≥ 40%, PF > 1, ≥ 3/mg, beruntun seimbang, mayoritas tahun) di KETIGA
  periode, tetapi dirakit setelah melihat semua periode → status `perlu-data`, wajib uji maju (ide #34).

## 2026-10-31 · Penyetelan bot multi-strategi (`eksperimen/multi_setel.py`) · risiko disetujui pemilik: 0,5%
Aturan main ditetapkan sebelum melihat hasil: seleksi 2015-2021 (kriteria awal pemilik + skor tetangga), diterima hanya bila PF > 1 di uji &
Setra DAN P_rasio vs baseline ≥ 0,90 di uji. Grid 324: RSI2 kuantil 30/35/40% × SL 2/2,5/3 × TP 2/3R/tanpa · K6 SL 1,25/1,5 × TP 4R/tanpa ·
aturan {RSI2 dulu, RSI2 hanya searah tren, RSI2 hanya lawan tren}.
- Lulus 2015-2021: 95, semuanya "RSI2 dulu" (dua aturan lain 0).
- Terbaik menurut skor (RSI2 30% SL 2-3 TP 2R/tanpa, K6 SL 1,25 tanpa TP): PF 1,07-1,28 di ketiga periode, R/thn lebih tinggi
  (12 thn +11,8 vs +6,6), tetapi DD 51-71R vs 37R dan **P_rasio uji vs baseline 0,25-0,56** → TIDAK diterima. Baseline tetap.
- **BASELINE (ide #34)**: maks 1 posisi/hari; RSI2 H1 jam 07:00 ≤ kuantil 35% (43,76) → BUY market / ≥ 71,22 → SELL market, SL 3 ATR,
  tanpa TP; selain itu K6 (SL 1,5 ATR, TP 4R). Tutup 23:00. Risiko 0,5%: 12 thn 4,2 trade/mg, win 47%, RR 1,22, PF 1,07, +6,6 R/thn,
  DD 37R (17,2% ekuitas), CAGR ±3%, W/L 10/8, bulan positif 53%. Per periode PF 1,03 / 1,10 / 1,17.
- Penantang untuk uji maju bayangan: RSI2 30% SL 2,5 TP 2R + K6 SL 1,25 tanpa TP (12 thn PF 1,12, +11,8 R/thn, DD 51R, W/L 12/12).

## 2026-10-31 · Implementasi bot multi-strategi (ide #34, keputusan pemilik: lanjut, risiko 0,5%)
- `gold_bot.py`: mode MR (RSI2 ≤ 43,76 BUY / ≥ 71,22 SELL market, SL 3 ATR, tanpa TP) diprioritaskan; selain itu K6. hist kini
  menyimpan label strategi di indeks 7 (`analisis.py` disesuaikan). XAU_RISK_PCT default 0,5. Pesan, /status_xau, panduan anggota baru.
- Acuan riset `eksperimen/multi_mesin.py` (konstanta dibaca dari gold_bot). `riset/replay_xau.py`: **IDENTIK** Setra 380/380
  (MR 339, K6 41), Dukascopy 2015-2026 2.581/2.581 (MR 2.168, K6 413).
- Patokan kesehatan (`riset/baseline_xau.py`, 2022-skrg, urutan M1, R kotor): 1.077 trade, win 47,6%, +0,079R, PF 1,19, DD 30,5R,
  kalah beruntun 8. LIVE_START XAU 2 Nov 2026.
- Catatan bayangan: `riset/xau/bayangan.py` (baseline, MR saja, K6 saja, juara lama, PENANTANG RSI2 30% 38,49/74,72 SL 2,5 TP 2R +
  K6 SL 1,25 tanpa TP) vs catatan live, untuk uji maju riset Jumat.
- Fakta penting: ±84% trade adalah MR; K6 hanya pada hari RSI2 tidak ekstrem (±1 dari 6 trade).

## 2026-11-02 · Insiden: tidak ada sinyal 07:00 (feed Setra macet sejak Jumat malam) · perbaikan dipasang (persetujuan pemilik)
- Setra H1/5m/1m berhenti di Sabtu 31 Okt 04:59 WIB; pasar buka Senin 06:00 WIB (Dukascopy aktif, gap turun 3.966 → 3.869).
  Run 07:05 WIB sukses tetapi tanpa candle baru → tidak ada pesan. Sinyal seharusnya: BUY market MR (RSI2 1,8).
- Perbaikan `gold_bot.py`: (1) peringatan data macet (> 2 jam di hari bursa) ke chat pribadi, sekali per kejadian + pesan pulih;
  (2) sinyal 07:00 yang baru diproses ≥ 10:00 WIB = TERLAMBAT (tidak dikirim/dicatat); < 10:00 diberi catatan keterlambatan;
  (3) cadangan Dukascopy (M1 harian + tick per jam hari berjalan, BID, hanya prefiks berurutan tanpa lubang).
  Replay tetap IDENTIK (aturan terlambat hanya live). Diuji end-to-end pada kondisi nyata pagi ini dan simulasi 10:30 WIB.
- Temuan sampingan: API Setra (1.000 candle terakhir) tidak memuat 80 candle yang ada di file unduhan riset untuk rentang yang sama →
  ATR live bisa sedikit berbeda dari backtest (pagi ini SL 66,9 vs 71,0 USD). Ide #35.
- 09:05 WIB: cadangan Dukascopy kosong di GitHub Actions. Penyebab (kesalahan kode): file M1 harian diunduh berurutan mulai
  Jumat termasuk Sabtu (pasar tutup); Dukascopy lambat (12-17 dtk/file, 503) → satu timeout menghentikan semuanya (aturan tanpa
  lubang). Perbaikan: hanya jam pasar buka (lewati Sabtu, Minggu < 21:00 UTC, Jumat ≥ 22:00 UTC), file tick per jam bila ≤ 8 jam per
  hari, timeout 60 dtk + log HTTP. Uji: 3 candle (Senin 06:00-08:00 WIB) dalam 66 dtk meski ada 503. API Setra semua timeframe
  masih macet di Sabtu 04:59 WIB.

## 2026-11-02 · SL lebar & lot minimum (pertanyaan pemilik)
- SL MR 3 ATR hari ini 66,9 USD (ATR naik 16,5 → 22,3 karena gap akhir pekan). Median jarak SL MR: 2024 17 · 2025 30 · 2026 56 USD
  (p90 2026 108, maks 336). Dengan 0,01 lot (1 oz) modal ±1.100 USD → risiko ±6%/trade; risiko 0,5% butuh modal ±11.200 USD (2026).
- SL MR 1,5/2/2,5/3 ATR (12 thn): PF 1,07/1,08/1,08/1,07, win 37/42/45/47%, DD 51/42/35/37R, W/L 9/16 · 10/16 · 10/8 · 10/8.
  SL lebih sempit tidak menyelesaikan masalah lot minimum. **Keputusan pemilik: tetap SL 3 ATR**; saran lot otomatis → ide #36
  untuk riset Jumat 6 Nov.

## 2026-11-05 · Ide #37 SINYAL SUSULAN pada hari tanpa trade (permintaan pemilik, chat) · `eksperimen/susulan.py`
Hari tanpa trade = hari K6 dilewati (batas batal tersentuh): 454/3.039 hari (15%, ±0,7/mg); 91% tersentuh sebelum 09:00 WIB.
Model realistis jadwal bot: keputusan di candle pertama yang close 09:00/11:00/.../21:00 WIB setelah batal; masuk candle berikutnya;
tutup 23:00; maks 1 posisi/hari. 450 hari susulan. Seleksi 2015-2021 (skor tetangga SL × TP), uji 2022-Jan 2025, Setra.
- S1 ikuti tembusan, S2 fade tembusan palsu, S4 breakout ulang searah tren, S5 straddle OCO range baru: susulan PF < 1 di pilih
  dan/atau uji; gabungan P_rasio uji vs baseline 0,001-0,28 → GAGAL.
- **S3 mean reversion RSI(2) di jam keputusan** (ambang kuantil 35% jam keputusan 2015-2021: ≤ 25,41 BUY / ≥ 77,10 SELL, market,
  SL 3 ATR, TP 1R; ±92% masuk 09:00 WIB): susulan saja PF 1,10 / 1,88 / 0,81 (n 198 / 81 / 46).
  Gabung baseline: pilih +3,8 vs +2,9 · uji +15,9 vs +9,9 (P_rasio 0,992) · Setra +13,6 vs +15,6 R/thn (DD 21 vs 17R).
  12 thn: 4,8 trade/mg, win 48%, PF 1,08, +8,4 vs +6,6 R/thn, DD 31 vs 37R (DD 0,5% 14,4% vs 17,2%), W/L 10/9, 9/12 tahun;
  slip +0,20 USD uji +11,7 vs +6,2. Per tahun gabung: 2015 +7 · 2016 +8 · 2017 +13 · 2018 -7 · 2019 0 · 2020 -4 · 2021 +10 ·
  2022 +34 · 2023 -10 · 2024 +22 · 2025 +19 · 2026 +8.
  Tetangga (32 varian, kuantil 35/50% × SL 1-3 × TP 1/2/4/tanpa): gabung uji P 0,88-0,99 SEMUA lebih baik dari baseline;
  Setra campuran (SL 1-1,5 + TP ≥ 2R lebih baik, SL 3 lebih buruk) — memilih varian menurut Setra = memilih pasca-lihat.
- Status: lolos tahap 1-2 (uji P 0,99, tetangga stabil); tahap 3 Setra sedikit lebih buruk dari baseline dengan sampel kecil
  (46 trade) → `perlu-data`. Menunggu keputusan pemilik (pasang langsung vs bayangan dulu; ±0,7 trade/mg → 20 trade ±7 bulan).

## 5 Nov 2026 — Optimasi susulan S3 (susulan_opt.py)
- Grid 2700 kombinasi: kuantil 0,25-0,50 × SL 1-3 ATR × TP 1/1,5/2/3/tanpa × masuk market/limit 0,25 ATR ×
  batas keputusan 09:00/≤13:00/≤21:00 WIB × filter tren (tanpa/searah/lawan). Dipilih HANYA di 2015-2021 atas hasil GABUNGAN
  (MR + K6 + susulan), kriteria pemilik + skor tetangga.
- 10 teratas pilih semuanya: limit, SL 1 ATR, hanya jam 09:00, searah tren. Di uji 2022-Jan 2025 GAGAL semua
  (susulan PF 0,67-1,05; P vs baseline 0,14-0,54) → optimasi pilih = overfit, DIBUANG.
- S3 asli (q35%, market, SL 3, TP 1R, semua jam keputusan ≤21:00 WIB, tanpa filter) tetap kandidat paling kokoh.
  Gabungan 12 thn vs baseline: 4,8 vs 4,2 trade/mg; win 48 vs 47%; PF 1,08 vs 1,07; +8,4 vs +6,6 R/thn; DD 31 vs 37R
  (0,5%: 14,4 vs 17,2%); W/L 10/9 vs 10/8; 9/12 thn. Pilih +3,8 vs +2,9; uji +15,9 vs +9,9; Setra +13,6 vs +15,6.
  Susulan sendiri dalam gabungan: 325 trade, win 56%, RR 0,97, PF 1,21, +21R (12 thn).
- Status tetap `perlu-data`; menunggu keputusan pemilik (pasang vs bayangan).

## 5 Nov 2026 — Susulan S3 DIPASANG (pilihan pemilik: pasang langsung; live 6 Nov 2026)
- gold_bot.py: langkah 5 GoldEngine (sus_wait setelah "skip", keputusan sekali di jam UTC 1,3,..,13; pend mode "SUS" market,
  SL 3 ATR, TP 1R, strat "SUS"); SUS_LATE_S 1 jam (live saja). Templat: 🔁 SINYAL SUSULAN, terlambat susulan, urutan bubble
  (dilewati sebelum susulan). commands.py: rekap per strategi + /status_xau + PANDUAN_XAU. multi_mesin.trades_sus + baseline(sus=).
- replay_xau: xau.json 425/425 (MR 339 K6 41 SUS 45) IDENTIK; xau_panjang 2906/2906 (MR 2168 K6 413 SUS 325) IDENTIK.
  (xau_sambung beda 1 = posisi MR terbuka di ujung data 30 Okt, sudah ada sebelum susulan; bukan beda mesin.)
- Simulasi live per run (28 Okt 2026): 07:09 order K6 → 09:09 dilewati + susulan BUY → 23:09 tutup −0,20R; run 09:09 terlewat → TERLAMBAT.
- bayangan.py: menu "Tanpa susulan"; baseline_xau.py: patokan kesehatan termasuk susulan.

## 5 Nov 2026 — Ide #38 "revenge" setelah kena SL (revenge.py, pertanyaan pemilik)
- Posisi ke-2 hari yang sama setelah SL, lot sama; keputusan di jam run berikutnya (close 09:00..21:00 WIB), market, tutup 23:00.
  942 SL dalam 12 thn, 763 bisa di-revenge. 24 varian (arah sama/balik × syarat tanpa/RSI2 × SL 1,5/3 × TP 1R/2R/tanpa).
- Hasil gabungan 12 thn: SEMUA di bawah baseline (+8,4 R/thn); terbaik "balik, SL 3, tanpa TP" +7,8 (DD 33R). P uji vs baseline
  0,01-0,56 (tidak ada yang ≥ 0,90). Revenge searah: PF 0,65-0,84 (12 thn), DD naik hingga 78R. Revenge berbalik: bagus HANYA di
  Setra (+20-25 vs +13,6; PF 1,1-1,4) tetapi rugi di 2015-2021 & 2022-Jan 2025 → khas rezim tren 2025-2026, bukan edge.
- Status: `ditolak`. Tetap maks 1 posisi/hari. "Balik" boleh dicek ulang bila data Setra berlipat (bayangan).

## 5 Nov 2026 — Ide #38b revenge DENGAN DIAGNOSA (revenge_diag.py, koreksi pemilik)
- Setelah SL (< 23:00), di jam run berikutnya bot menilai kenapa gagal lalu memilih aksi sama/balik/lewati (lot sama, market,
  SL 3 ATR, tanpa TP). Diagnosa ditetapkan sebelum melihat hasil: strategi gagal (FADE=MR/SUS, K6) × tren EMA200 / kecepatan SL
  (≤ 2 jam) / harga lanjut vs kembali dari SL / RSI2 / range hari ≥ 2,5 ATR. Aturan per sel dipilih di 2015-2021.
- Langkah 1: tanda rata-rata R per sel BERBALIK antar periode (mis. FADE gagal → balik: pilih +0,00..+0,05, uji -0,07..-0,22,
  Setra +0,09..+0,13; FADE → sama kebalikannya). Diagnosa tidak memprediksi arah revenge secara konsisten.
- Langkah 2 (5 aturan): pilih +4,7..+6,1 vs +3,8 baseline; uji +9,3..+11,1 vs +15,9 (revenge PF 0,66-0,78); Setra +17,9..+21,5
  vs +13,6; 12 thn +8,1..+9,2 vs +8,4. P uji 0,01-0,08 → GAGAL. Pola: 2015-21 & Setra suka "balik", 2022-Jan 2025 suka "sama"
  = bergantung rezim; belum ada detektor rezim yang terbukti (lih. ide #29-#33).
- Status: `ditolak`. Bot tetap maks 1 posisi/hari.

## 5 Nov 2026 — Ide #39 SESI TAMBAHAN 23:00-07:00 WIB (sesi2.py, usulan pemilik; sesi 1 tidak diubah)
- Dekomposisi log-return %/thn (2015-21 / 2022-Jan25 / Setra): sesi 1 07-23 WIB +0,5/+2,9/+3,4; sesi 2 23-07 hari kerja
  +3,5/+8,8/+15,0 (hampir semua di candle close 06:00 & 07:00 WIB; close 04:00 negatif = rollover); gap akhir pekan ±2,1.
- Sesi 2 (masuk 23:00, tutup 07:00, lewati malam Jumat, biaya 0,40 + swap long 0/0,3/0,6 USD/oz/malam; 5 arah × SL × TP = 45):
  di 2015-2021 SEMUA rugi (PF 0,74-0,87 walau swap 0). Swap 0: terbaik "long tren H1 SL 3" gabung 12 thn +9,5 vs +8,4,
  uji +22,6 vs +15,9 (P 0,95), Setra +24,7 vs +13,6, DD 32R — tetapi pilih -0,1 vs +3,8. Dengan swap 0,6: gabung 12 thn
  +4,4, pilih -6,5 (P 0,66). MR RSI2 di 23:00 (2 arah / long) rugi di semua periode.
- Long 05:00→07:00 WIB: Dukascopy +0,52/+0,63 USD kotor (2015-21/2022-25) tetapi Setra -0,03 → efek spread rollover di data BID
  Dukascopy, bukan edge yang bisa ditradingkan.
- Kesimpulan: "kenaikan malam" = tren naik emas 2022-2026 + artefak spread, bukan pola yang bertahan; sesi 2 hanya untung di
  pasar bull dan bergantung swap broker. Status `ditolak` (dicatat: bila pemilik ingin taruhan tren naik jangka panjang,
  itu keputusan alokasi/investasi, bukan edge intraday).

## 5 Nov 2026 — Statistik lengkap bot live + celah (statistik_live.py, celah_uji.py; permintaan pemilik)
- Live (MR+K6+SUS, 12 thn, bersih, M1): R/trade +0,015/+0,064/+0,054 (2015-21/2022-Jan25/Setra). MR BUY +0,052 (12t) vs
  MR SELL -0,010; K6 BUY +0,171 vs K6 SELL -0,064; SUS +0,064 (Setra -0,075). Biaya 0,40 USD = 12,9 / 8,4 / 2,9 R/thn
  (2015-21 biaya memakan 78% R kotor karena ATR kecil). DD terdalam -30,7R (Mei 2023-Feb 2024); DD sekarang -21,2R sejak
  Apr 2026 (dasar Agu 2026) belum pulih. Rabu/Kamis terbaik, Selasa terburuk (2/3 periode negatif).
- Segmen lemah 3/3 periode: K6 SELL; MR SELL RSI 71,22-85; MR ATR rel 1,0-1,25 (tidak monoton = kemungkinan acak).
  Catatan: ±57 segmen diperiksa → ±7 lemah-3/3 diharapkan secara acak; ditemukan 3 → harus diuji sebagai aturan.
- Uji aturan (R/thn 2015-21 · uji · Setra · 12t; baseline +3,8 · +15,9 · +13,6 · +8,4):
  A1 MR SELL ≥ X lalu sisanya K6: X75 +8,0·+17,1·+18,2·+11,9 (P uji 0,61) · X80 +5,6·+26,3·+14,4·+12,3 (0,95) ·
  X85 +10,4·+24,7·+13,9·+14,6 (0,87; DD 25R) · X90 +6,4·+25,5·+14,3·+12,6 (0,78). Semua tetangga lebih baik, Setra ≈ baseline.
  A2 (sisanya tanpa trade) lebih lemah (+9,1..+10,6). B K6+susulan hanya tren naik: P uji 0,27 → ditolak. C A1+B: Setra +22,3
  tetapi uji +23,4 (P 0,82), 3,7 trade/mg.
- Ide #40 = A1 (pilih-saja juga memilih X=85: pilih +10,4 tertinggi). Tahap 2 P 0,87 (X80 0,95), tetangga stabil; Setra tidak
  lebih baik. Risiko: aturan asimetris memihak tren naik emas 12 thn. Status `perlu-data` / menunggu keputusan pemilik.

## 5 Nov 2026 — Ide #41 PEMBAGI TUGAS (strategi saling menutup celah; pembagi.py, gagasan pemilik)
- Tiap hari (07:00) masuk sel kondisi; tiap sel diberi MR / K6(+susulan) / kosong terbaik di 2015-2021, diuji sesudahnya.
- R/thn 2015-21 · uji · Setra · 12t (baseline +3,8 · +15,9 · +13,6 · +8,4; 4,8 trade/mg):
  L1 RSI (7 sel) +11,2 · +12,2 · +6,8 · +10,8 (3,4/mg; P uji 0,43) · L2 RSI×tren (14) +13,8 · +13,3 · -3,8 · +11,0 (P 0,56) ·
  L3 RSI×tren×ATR (42) +20,6 · +8,5 · +4,4 · +15,0 (P 0,27) · L4 ×hari (202 sel, hanya 2 aktif) P uji 0,03.
- Pola klasik overfit: makin banyak sel → makin bagus di data pemilihan, makin buruk di data baru; trade/mg turun (sel "kosong").
  Pembagian sempit berdasar alasan (ide #40: 1 sel, dialihkan ke K6, uji tetangga) lebih kokoh daripada pembagi penuh.
- Status `ditolak` (versi otomatis banyak sel). Arah lanjut: penutup celah diuji juga di pasar lain (mis. XAG/USD) sebelum dipasang.

## 5 Nov 2026 — Ide #40b penutup celah sumber edge berbeda (celah_momentum.py) + persiapan uji perak
- Hari RSI2 71,22..X diberi BUY momentum (SL 3 ATR, TP 2R/tanpa; semua hari / hanya tren naik) vs K6 (ide #40):
  momentum terbaik X85 tren naik TP2 +6,9 · +21,6 · +13,9 · 12t +11,8 (P uji 0,85) < ide #40 X85 +10,4 · +24,7 · +13,9 · +14,6.
  Momentum polos lebih buruk (12t +6,8..+9,6). → K6 tetap penutup celah terbaik. #40b `ditolak`.
- Poin "strategi sumber edge berbeda": bot sudah trade ±4,8 dari 5 hari/mg → hampir tidak ada hari kosong; strategi baru hanya
  bisa menggantikan sel strategi lain (= pembagi tugas, ide #41) atau membuka posisi ke-2 (ditolak pemilik: maks 1/hari).
- Uji silang PERAK (XAG/USD) untuk ide #40: Dukascopy tidak bisa dijangkau dari sesi chat 5 Nov 15:20 WIB (connection reset,
  juga untuk XAU). Skrip siap: riset/unduh_xag.py + riset/xau/eksperimen/uji_xag.py → dijalankan di riset Jumat 6 Nov.

## 5 Nov 2026 — Ide #40 DIPASANG (pemilik: "push sekarang dan ubah bot live"; live 6 Nov 2026)
- gold_bot.py MR_SELL 71,22 → 85 (hari RSI2 71,22-85 → K6, otomatis lewat cabang yang sama). replay_xau: xau.json 413/413
  (MR 270 K6 76 SUS 67) & xau_panjang 2813/2813 (MR 1597 K6 699 SUS 517) IDENTIK.
- Ekspektasi baru (STRATEGI.md): 12 thn +14,6 R/thn, PF 1,15, DD 25R (12% @0,5%), CAGR +7,2%, 4,6 trade/mg, 8/12 thn untung.
  Kelemahan: P uji 0,87; Setra ≈ sama; 2026 berjalan -2 vs +8; asimetris. baseline.json diperbarui (2022+: PF 1,27, DD 18,7R).
- bayangan.py + menu "MR SELL lama 71,22"; uji_xag.py membandingkan bot live vs 71,22 di perak (riset lanjutan, PROSEDUR).

## 5 Nov 2026 — Kenapa 2026 lebih lemah setelah ide #40 (pertanyaan pemilik)
- Hari yang berubah (RSI 71,22-85; ±50/thn): versi baru lebih baik 8 dari 12 tahun (+2..+26R), lebih buruk 2015 (-13), 2021 (-12),
  2022 (-4), 2026 (-10). 2026: emas turun dari 5.387 (Mar) ke 3.997 (Okt) → SELL di jenuh beli ringan justru untung tahun ini.
- Diuji: ambang 85 hanya bila tren D1 (EMA 50/100/200 hari) naik → 12 thn +14,3..+14,9, P uji 0,95-0,97, tetapi 2026 tetap
  -2..-5 → tidak memperbaiki 2026; tidak dipasang (menambah aturan demi 1 tahun = overfit).

## 5 Nov 2026 — Ide #42 "baik tiap tahun, tidak condong BUY" (simetris.py; permintaan pemilik, riset literatur)
- Sumber: Connors & Alvarez (2008) RSI(2) + filter MA 200 hari & cermin short; RSI adaptif persentil bergulir (TradingView
  Adaptive RSI / RSI Median Deviation); saklar rezim ADX harian histeresis 20/30 (Top Gun Fast 1, MQL5); Unger Academy (tren &
  MR emas saling menyeimbangkan; fade high/low hari sebelumnya). Pilih 2015-2021 (skor = R/thn × porsi tahun untung), uji sesudahnya.
- R/thn 2015-21 · uji · Setra · 12t | tahun+ | terburuk | sd tahunan (bot live: +10,4 · +24,7 · +13,9 · +14,6 | 8/12 | -6 | 17,3):
  C Connors cermin MA100 b30 kuat85 (TERPILIH di pilih): +9,9 · +24,0 · +22,4 · +15,5 | 9/12 | -14 (2020) | 15,8 | P uji 0,45, P Setra 0,84
  C MA200 b30 kuat85: +7,5 · +19,8 · +25,9 · +13,5 | 10/12 | -10 (2020) | 12,3 | P uji 0,26, P Setra 0,92
  C MA50: 12t +12,3, Setra +20,6. Tetangga C (MA 50/100/200) semua Setra +20..+26 vs +13,9; 2015 +11..+16, 2026 +14..+20
  (bot live -6 / -2). P (persentil bergulir): 12t +8,1..+11,8, buruk. X (ADX): 12t +11,5..+14,6, sd 18-20 (tidak lebih rata).
- Kesimpulan: Connors cermin = kandidat terbaik untuk tujuan pemilik (tahun turun emas jadi untung, profil tahunan lebih rata),
  tetapi di 2022-Jan 2025 tidak lebih baik (P 0,26-0,45) dan 2020 rugi -10..-14. Status `perlu-data`; bayangan menu
  "Connors MA200/MA100 (#42)" (multi_mesin.sinyal_connors). Bot live tidak diubah (pemilik: pakai bot sekarang).
- Antrian lanjutan (Jumat): #43 fade high/low hari sebelumnya (Unger) sebagai sumber edge baru; #44 Connors + saklar ADX
  (atasi 2020); #45 ukuran posisi target-volatilitas agar R tahunan lebih rata; uji silang perak untuk #42.

## 5 Nov 2026 — Ide #42b HIBRIDA bot live + Connors cermin (hibrida.py, permintaan pemilik)
- Tren D1 naik → aturan MR live persis (≤ 43,76 / ≥ 85); turun → cermin (SELL ≥ 100-b, BUY ≤ 100-kuat); sisanya K6+susulan.
- R/thn 2015-21 · uji · Setra · 12t | tahun+ | terburuk (live +10,4 · +24,7 · +13,9 · +14,6 | 8/12 | -6):
  MA100 SELL≥70 BUY≤15 (TERPILIH di pilih) +9,4 · +28,6 · +23,2 · +16,5 | 9/12 | -8 | DD 28R | P uji 0,68, P Setra 0,86
  MA100 SELL≥70 BUY≤10 +8,6 · +28,8 · +17,9 · +15,2 · MA200 SELL≥70 BUY≤15 +5,8 · +21,4 · +25,4 · +12,8 | 11/12 | -1 | sd 12,7.
  Cermin dengan SELL ≥ 56,24 (= cermin persis 43,76) buruk (P uji 0,03-0,28).
- MA100: 2015 +18 (live -6), 2026 +14 (-2), 2020 +2, 2021 -8, 2018 -7. Tidak ada yang P ≥ 0,90 → `perlu-data`; bayangan
  "Hibrida MA100/MA200 (#42b)" (multi_mesin.sinyal_hibrida). Menunggu keputusan pemilik.

## 5 Nov 2026 — Ide #42b HIBRIDA MA100 DIPASANG (pilihan pemilik "1"; live 6 Nov 2026)
- gold_bot.py: TREND_D1_N 100, MR_SELL_TURUN 70, MR_BUY_TURUN 15; SMA dari close 07:00 (state["c07"] 150 hari + bibit
  gold_c07_seed.json 450 close Setra Feb 2025-Okt 2026; replay hanya rows). Pend MR + "d1"/"ma"; bubble menampilkan tren harian.
  multi_mesin.sinyal_live = sinyal_hibrida (konstanta dari gold_bot); baseline default = live.
- replay_xau: xau.json 413/413 (MR 253 K6 93 SUS 67) & xau_panjang 2811/2811 (MR 1541 K6 753 SUS 517) IDENTIK. Simulasi live
  (1000 candle + bibit) MA = MA data penuh. baseline.json diperbarui. Ekspektasi 12 thn +16,5 R/thn, PF 1,16, DD 28R, 9/12 thn.
- Bayangan: "Tanpa hibrida (#40 saja)", "Hibrida MA200 (#42b)", Connors MA100/MA200, MR SELL lama 71,22.

## 6 Nov 2026 — Riset mingguan (Jumat 6 Nov 2026 WIB)
- Data: Setra 11.480 candle s.d. 5 Nov 2026 16:00 UTC; Dukascopy 70.043 candle 2015 - 4 Nov 2026 (proxy Dukascopy sering
  terputus; semua bulan lengkap). replay_xau: xau.json 462/462 (MR 284 K6 106 SUS 72) & xau_panjang 2814/2814 IDENTIK.
- Uji maju (bayangan.py, sejak 2 Nov 2026, 3 trade): BASELINE -3,02R (3 SL; data final memberi MR SELL 2 Nov) · Tanpa hibrida
  (#40 saja) -1,52R · K6 saja +0,49R · Juara lama OCO +5,44R (4 trade) · LIVE catatan bot -1,11R kotor (+0,89 / -1 / -1).
  Terlalu sedikit untuk menilai (syarat ≥ 6 minggu & ≥ 20 trade).
- TEMUAN: sinyal live 2 Nov 2026 BERBEDA dengan backtest. Setra macet Senin pagi → bot memakai cadangan Dukascopy dan mencatat
  MR BUY (RSI2 1,8, ATR 22,3, entry 3.898,06). Data final Setra dan Dukascopy memberi RSI2 80,5 pada candle yang sama → MR SELL
  (-1R). Live kebetulan untung (+0,89R). Penyebab di jalur fetch_dukascopy belum bisa direproduksi (Dukascopy connection reset
  dari sesi riset). Dicatat sebagai ide #47 (audit cadangan, prioritas 1).
- Ide #36 saran lot (ide36_lot.py): jarak SL + biaya per 0,01 lot (Setra Feb 2025-skrg) median 39 USD (MR 47, K6 22, SUS 50),
  p90 77; 2026 median 53 (MR 58, p90 109). Modal 1.000 USD → 100% sinyal butuh peringatan, risiko 0,01 lot median 3,9%
  (maks 34%); 5.000 → 72% (median 1,0%); 10.000 → 35% (0,6%); 20.000 → 6%; 50.000 → 0,5%. Simulasi majemuk Feb 2025-skrg:
  ideal 0,5% +26%; lot bulat-bawah + terima lot minimum: 1.000 USD +146% DD 43%, 10.000 +28% DD 7%, 20.000 +23% DD 7%;
  + lewati: 10.000 +13% (108 sinyal dilewati). Rancangan & usulan perubahan bot di laporan. Status `lolos` (menunggu pemilik).
- Ide #46 keluar MR lebih awal (Connors; ide46_mr_keluar.py) R/thn 2015-21 · uji · Setra · 12t (BASELINE +9,4 · +28,6 · +21,4 ·
  +16,2): E-RSI 50/60/70/80/90 -0,4/-1,1/-0,7/+0,9/+4,2 di pilih; terbaik E-RSI 90 +4,2 · +31,2 · +10,7 · +12,3 (P uji 0,89,
  P Setra 0,09); E-SMA 5/10 -1,1/0,0 di pilih. Win MR naik 49% → 61-64% tetapi RR turun 1,27 → 0,9. GAGAL tahap 1.
- Uji silang PERAK ide #40 (uji_xag.py, uji_xag_a2.py; 69.916 candle XAG 2015 - Okt 2026, harga x80): seluruh bot rugi di perak
  (bot live PF 0,80, -22 R/thn @2 USD). X85 vs 71,22 R/thn 2015-21 · uji · Setra · 12t @2 USD: -33,0 · -15,4 · -4,9 · -24,2 vs
  -26,0 · -7,4 · -14,5 · -19,4 → X85 lebih baik hanya 1/3 periode, 12 thn lebih buruk (juga @1 & @3 USD). Kriteria PROSEDUR
  (≥ 2/3 periode + 12 thn) GAGAL → usulan ke pemilik: kembali ke 71,22. Nuansa: SELL RSI 71-85 juga negatif di perak (-4,2
  R/thn, semua periode @2 USD) dan "A2" (hari itu tanpa trade) lebih baik dari keduanya; yang buruk adalah penggantinya (K6/SUS
  -9,0 R/thn). Karena sistem tidak punya edge di perak, ini bukti lemah; keputusan di pemilik.

## 6 Nov 2026 — Ide #48 OCO juara lama sebagai UTAMA + strategi live sebagai tambahan (oco_utama.py, pertanyaan pemilik)
- Pemicu: bayangan minggu pertama OCO +5,44R (4 trade) vs live -1,11R (3 trade) — sampel terlalu kecil untuk menilai.
- 12 thn (R/thn 2015-21 · uji · Setra · 12t): OCO saja -25,2 · -0,0 · +29,3 · -10,6 (PF 0,94, DD 226R, kalah beruntun 21,
  untung 4/12 thn: hanya 2020, 2024, 2025, 2026) vs bot live +9,4 · +28,6 · +23,2 · +16,5.
- OCO + MR hibrida live: +6,4 (12t), DD 83R; OCO + MR hanya RSI ekstrem (b 5-30): -12,7..-2,7. Semua P uji vs live ≤ 0,08.
- Kesimpulan: OCO hanya unggul di rezim volatil 2025-2026; menjadikannya utama merugikan 2015-2023. `ditolak`. Bayangan
  "Juara lama (OCO)" tetap dipantau.

## 6 Nov 2026 — Ide #47 perbaikan jalur cadangan data (sinyal salah arah Senin 2 Nov)
- Log GitHub Actions run 2 Nov 02:33 UTC: sinyal MR BUY, close 07:00 = 3.898,06 (= candle Dukascopy Min 23:00 UTC, file tick
  normal: O 3.869,06 H 3.902,05 L 3.869,06 C 3.898,06), RSI2 1,8, ATR 22,31. State 00:05 & 02:06 UTC: last_ts / stale_warn =
  candle Setra **Jumat 21:00 UTC** (jam tutup pasar musim panas AS = 17:00 ET), candle yang tidak ada lagi di Setra sekarang.
  Setra sekarang s.d. Jum 20:00 UTC + Dukascopy Min 23:00 → RSI2 80,3 (SELL). Isi candle buruk tidak bisa direkonstruksi persis
  (satu candle saja tidak cukup untuk RSI 1,8) → ujung data Setra yang macet tidak bisa dipercaya.
- Perbaikan gold_bot.py: (1) _jam_tutup (zona America/New_York: 17:00 ET harian, Jumat ≥ 17:00 s.d. Minggu < 18:00) membuang
  candle Setra & Dukascopy di jam tutup; _pasar_buka/_tepi_pekan ikut ET (otomatis pergantian musim). (2) Setra macet → 48 jam
  terakhir Setra diganti Dukascopy bila cadangan melewati ujung Setra (selain itu sambung seperti dulu). (3) state cad_log
  (≤ 30 candle) & cad_aktif; pesan sinyal diberi "ℹ️ data cadangan Dukascopy, cocokkan dengan chart broker".
- Uji: replay_xau IDENTIK (filter hanya di jalur live; data riset Setra 0 candle jam tutup). Simulasi 2 Nov dengan Dukascopy
  nyata + candle buruk sintetis: cara lama RSI2 38,0 (BUY, salah), cara baru 79,8 (SELL = data final).

## 6 Nov 2026 — Ide #49 meta-strategi ADAPTIF walk-forward (adaptif.py, pemilik: "adaptif di semua kondisi, tanpa tahun minus")
- Tiap awal bulan pilih strategi menu dengan R bersih terbaik N bulan terakhir (masa lalu saja). N 1/3/6/12, ± syarat > 0.
- Hasil (R/thn · tahun minus · terburuk): N1 +5,7 · 3 · -17; N3 +8,3 · 4 · -23; N6 +12,8 · 3 · -16; N12 +7,9 · 5 · -13.
  Semua LEBIH BURUK dari strategi tetap: live hibrida MA100 +16,2 · 3 · -8; hibrida MA200 +12,6 · **1 · -1** (2015 -1;
  2018/2021/2023 ±0); Connors MA200 +13,2 · 2 · -10. Memilih menurut kinerja terakhir = terlambat & berganti-ganti (whipsaw).
- Kesimpulan: adaptasi harus dari KEADAAN PASAR (tren harian, seperti hibrida), bukan dari kinerja terakhir. #49 `ditolak`.
  Hibrida MA200 paling dekat ke target "tanpa tahun minus" (dipilih setelah melihat semua tahun → tetap perlu uji maju).

## 6 Nov 2026 — PROGRAM TAMBAL-CELAH putaran 1 (pemilik: sistem yang untung di SEMUA tahun dulu, lalu optimasi)
- Bedah celah hibrida MA200 (celah_ma200.py): 2015 -1 (MR-naik -12,4 = MA200 belum terbentuk ±10 bln pertama → efek data awal);
  2018 +0 & 2021 +0 = rezim mendatar di sekitar MA200 (hanya 39%/30% hari di atas MA200; trade dekat MA 0-2% dan saat sering
  menyeberang MA rugi di tahun lemah); 2023 +0 = tren kuat (ADX 27) → MR rugi dua arah. Bulan terburuk: 2018-09, 2025-12, 2021-01.
- Penambal (tambal1.py): zona netral 1% → aturan ketat 2 arah: 11/12 thn+, 2016-2026 semua positif, 12t +14,9, DD 22R;
  zona 1% → K6 saja: 12t +16,2, Setra +28,7. Zona 2-3% gagal; kemiringan MA200 (10/20/40 hari) lebih buruk (12t +9,5..+11,0).
- Ide #50 `perlu-data`; #51 data 2004-2014 (unduh terputus, 41 bulan) → putaran berikutnya di riset Jumat (PROSEDUR).
- 6 Nov 2026 14:50 WIB: data XAU H1 Dukascopy 2004-2014 lengkap (132 bulan, 68.237 candle; 2013-2014 ±5.950/thn) disimpan di
  riset/data/xau_dukascopy_h1_2004_2014.json.gz (+ riset/gabung_xau_lama.py). Riset Jumat tidak perlu mengunduh.
- 6 Nov 2026: pembagian data baru (pemilik): Langkah 1 uji apa adanya di 2004-2014 (sekali, Jumat 13 Nov); Langkah 2
  walk-forward berlabuh 2004-2026 (uji per 2 tahun, 2011-2026 semua tahun hasil uji). Ditulis di PROSEDUR.

## 10 Nov 2026 — Ide #52 SUSULAN WAJIB (tiap hari order pagi batal harus ada sinyal; susulan_wajib.py, permintaan pemilik)
- Pemicu: Selasa 10 Nov K6 BUY STOP batal (batas 4.133,25 tersentuh candle 07-08), keputusan susulan 09:00 RSI2 41,0 → tanpa
  susulan (sesuai aturan; bot & replay sama). Fakta: susulan S3 live sudah muncul di 70% hari batal (513/731, 12 thn).
- 200 varian (S3 + pengisi / satu strategi untuk semua hari batal; pengisi MR50/IKUT/FADE/D1/OCO × SL × TP), dipilih 2015-21.
  Terbaik: S3 + IKUT (arah tembusan, market) SL 2 ATR tanpa TP: gabung 12t +17,5 vs +16,5, pilih +12,0 vs +9,4, uji +27,6
  vs +28,6, Setra +21,8 vs +23,2, 10/12 thn, P uji 0,28 / Setra 0,33. S3 + OCO SL 1,5: 12t +17,9, uji +24,4, Setra +23,7.
- Pengisi saja (218 hari, ±0,35 trade/mg): IKUT SL2 2015-21 win 48% PF 1,28 tetapi 2022-Jan25 PF 0,88 dan Setra PF 0,77
  (-1,0 & -1,5 R/thn); OCO & TP 1,5 sama polanya → untung hanya di periode pemilihan. Status `perlu-data`/keputusan pemilik:
  100% cakupan bisa dipenuhi dengan biaya kecil di era terbaru, bukan peningkatan.

## 10 Nov 2026 — Ide #53 PENGISI BEBAS hari batal tanpa S3 (pengisi_bebas.py, pemilik: riset bebas & kreatif)
- 457 hari pengisi 2004-2026. Aturan "jika fitur > median maka arah A selain itu B" (10 fitur × 6 arah × 6 arah) + 6 aturan
  tetap × SL 1/1,5/2/3 × TP 0,3/0,5/0,75/1/1,5/2/tanpa = 8.568 kombinasi. Pilih 2015-21; konfirmasi 2004-14 (data baru) & 2022+.
- 15 teratas pilih (+0,33..+0,54 R/trade, semua SL 1 ATR tanpa TP, win 33-38%) RUGI di 2004-14 (-0,09..-0,46) dan 2022+.
  Dari 200 teratas: positif di 2004-14 48, 2022-Jan25 20, Setra 51, KETIGANYA 0. Semua kombinasi: positif 22% (2004-14),
  13% (2015-21), 14% (2022-Jan25), 42% (Setra). TP kecil (win tinggi) kalah oleh biaya.
- Kesimpulan: hari "order batal + RSI tidak ekstrem" tidak punya edge yang bisa ditemukan dari fitur harga; memaksa sinyal di
  hari ini = membayar biaya. `ditolak`. 2004-2014 dipakai sebagai konfirmasi (tidak untuk memilih).

## 10 Nov 2026 — Ide #54 PUSTAKA STRATEGI KLASIK (pustaka.py; pemilik: keluar dari RSI/EMA)
- 20 strategi (inside bar, turtle soup, fraktal Bill Williams, alligator, fibonacci 61,8, profil waktu TPO/POC sbg proksi volume
  profile [3 varian], donchian, NR7, bollinger fade & squeeze, supertrend, pivot R1/S1, PDH/PDL soup, heikin-ashi, MACD,
  ichimoku, parabolic SAR, stochastic) × SL 1/2 ATR × TP 0,5/1/2/tanpa; pilih 2015-21; konfirmasi 2004-14, 2022-Jan25, Setra.
- PENGISI hari batal: 0/20 untung di semua periode. Pengikut tren (alligator, supertrend, ichimoku, TPO terima di luar VA
  [PF 1,92, cakupan 20%]) untung di 2004-14, 2015-21 & Setra tetapi RUGI di 2022-Jan25 (-2,2..-7,2 R/thn).
- MANDIRI jam 07:00: 1/20 — bollinger fade (close di luar pita 2σ → lawan, SL 2 ATR tanpa TP) +1,8/+1,9/+1,7/+7,5, PF 1,43,
  tetapi hanya 4% hari dan 91% sudah = hari MR live searah (strategi sama, bukan sumber baru). Bollinger squeeze OCO 3/4
  periode (+7,3/+5,9/+0,5/-3,6). Turtle soup 3/4. Lainnya rugi di ≥ 2 periode (fibonacci, pivot, stochastic, NR7 terburuk).
- Belum diuji (riset lanjutan): volume profile ASLI (butuh volume tick Dukascopy, unduh ulang), Elliott wave (tidak bisa
  dimesinkan secara pasti; hanya proksi swing/fraktal). Antrian: #55 diagnosa kenapa pengikut tren gagal 2022-Jan25 di hari
  pengisi (rezim suku bunga/ATR?), #56 bollinger squeeze sebagai strategi tambahan hari tanpa sinyal, #57 volume tick.

## 10 Nov 2026 — Ide #58 KOMBINASI 2-4 indikator klasik (kombinasi.py, kombinasi_integrasi.py; gagasan pemilik)
- 16 komponen suara (ALG, ST, ICH, SAR, MACD, HA, TPO ikut/fade, BB fade, stoch fade, turtle soup, PDH/PDL soup, RSI2 30/70
  fade, EMA200, D1 SMA100, CLV) × kombinasi 2-4 yang SEPAKAT × SL 1/2 × TP 0,5/1/2/tanpa. Pilih 2015-21; konfirmasi 2004-14,
  2022-Jan25, Setra; uji pembanding = porsi lolos 100 teratas vs semua.
- PENGISI hari batal: 0% (100 teratas) vs 2% (semua) → tidak ada edge (konsisten dengan #53/#54).
- MANDIRI 07:00: 100 teratas 34% lolos vs 8% semua (4×) → ada informasi nyata. Pola: RSI2 jenuh (≤30/≥70) + konfirmasi tren
  (Alligator/MACD/SAR/EMA200) + CLV = beli koreksi dalam tren / jual pantulan dalam tren. Mis. ALG+RSIf+CLV SL2 TP2 untung di
  keempat periode (+6,5/+5,1/+6,0/+3,3 R/thn).
- **VONIS PERTAMA BOT LIVE DI 2005-2014 (data baru, apa adanya):** +8,6 R/thn tetapi 2005 -6, 2006 -14, 2013 -24, 2014 -16;
  2005-2026: +13,3 R/thn, DD 56R, 7/22 tahun minus, terburuk -24. (Langkah 1 PROSEDUR sebagian sudah dikerjakan di sini.)
- Integrasi V2 (kombinasi dulu → MR live → K6 + susulan): semua 18 varian V2 > bot live di 2005-2026 (+13,3..+16,7 R/thn).
  Terbaik ALG+MACD+RSIf SL2 tanpa TP: +12,4 · +14,2 · +28,8 · +29,0 (2005-14 · 2015-21 · uji · Setra), 2005-26 +16,6, DD 46R
  (live 56R), 6/22 thn minus, terburuk -17 (live -24). 907 hari kombinasi, 650 tumpang tindih dgn hari MR live.
  V1 (kombinasi mengganti MR) lebih buruk. Celah tersisa: 2005-06 & 2013-14 (rezim bearish/transisi emas), 2018, 2021.
- Status #58 `perlu-data` (dipilih setelah melihat semua periode integrasi; keluarga konsisten). Lanjut riset Jumat: P vs live,
  walk-forward, tambal-celah 2005-06 & 2013-14.

## 10 Nov 2026 — OPTIMASI #58 & DIPASANG (pemilik: "optimasikan ... jika iya terapkan ke bot live"; live 11 Nov 2026)
- optimasi58.py: 15.540 sistem (kombinasi 2-4 dari 16 komponen × SL 1,5/2/2,5/3 × TP 1/1,5/2/3/tanpa) sebagai V2 lengkap,
  dipilih HANYA di 2015-2021. Uji pembanding: 30 teratas 27% mengalahkan live di 2005-14 & uji & Setra vs 5% semua.
- Terpilih: Alligator + MACD + RSI2 (≤30/≥70), SL 1,5 ATR, tanpa TP. Sistem: 2005-14 +12,7 vs +8,6 · 2015-21 +15,1 vs +10,8 ·
  uji +29,0 vs +28,6 · Setra +29,2 vs +23,2 · 2005-26 +17,1 vs +13,3; DD 52 vs 56R; 6 vs 7 tahun minus. P 0,83/0,75/0,29/0,89.
- gold_bot.py: smma(), self.AL/self.MH, kombo(), mode "KOMBO" (prioritas di jam 07:00). multi_mesin: sinyal_kombo, sinyal_live =
  hibrida + kombo, trades_live_mr (strat0), baseline default = live. replay_xau: xau.json 415/415 (KOMBO 52 MR 215 K6 87 SUS 61),
  xau_panjang 2841/2841 (KOMBO 416) IDENTIK. Simulasi pesan 27 Okt (KOMBO BUY RSI 10,6 → +3,18R). baseline.json diperbarui.
  Bayangan: "Tanpa kombinasi (hibrida 6 Nov)".
