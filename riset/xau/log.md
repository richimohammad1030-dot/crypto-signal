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
