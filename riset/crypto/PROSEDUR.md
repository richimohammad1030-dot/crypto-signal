# Prosedur riset · CRYPTO

Instruksi untuk routine **"Riset Bot Crypto"** (setiap Jumat 00:59 WIB).
Tujuan: menemukan perbaikan bot crypto yang terbukti dengan data, lalu **mengusulkannya** ke pemilik.
Routine tidak pernah mengubah bot live. Perubahan dipasang hanya setelah pemilik setuju di chat.
Riset XAU dikerjakan routine terpisah (`riset/xau/`). Jangan menyentuh berkas XAU.

**Wajib baca dulu `riset/ATURAN_BERSAMA.md`** (sumber ide, uji signifikansi, data terkunci, uji maju). Aturan di sana
berlaku di atas kriteria LOLOS di bawah: lolos kriteria di bawah = lolos tahap 1 saja.

## 0. Aturan keras
- **Jangan ubah** file bot: `signal_bot.py`, `gold_bot.py`, `templates.py`, `gold_templates.py`, `commands.py`,
  `jurnal.py`, `kesehatan.py`, `baseline.json`, file state (`*.json` di root), dan `.github/`.
- Hanya tulis di `riset/crypto/` dan `riset/laporan/crypto/`.
- Kerjakan di branch baru `claude/riset-crypto-YYYY-MM-DD` (tanggal WIB hari ini), commit, lalu push branch itu.
  Workflow `kirim-laporan-riset.yml` otomatis mengirim ringkasan ke chat pribadi pemilik dan menyalin berkas riset ke main.
- Jangan membuat routine, scheduled task, atau pengingat baru.

## 1. Persiapan data (±5-8 menit)
```bash
pip install -q --break-system-packages numpy pandas scikit-learn scipy
COINS=$(python3 -c "import signal_bot as s; print(' '.join(s.COINS))")
python3 riset/unduh_crypto.py /tmp/data "$COINS"
python3 riset/backtest_crypto.py . /tmp/data /tmp/data/trades_crypto.csv
```
`backtest_crypto.py` memakai mesin asli bot (`signal_bot.Engine`), jadi selalu mengikuti versi juara yang sedang live.
Hasilnya berisi faktor setiap trade (trend, ext, dist, slpct, mom20, slope, breadth, rank, btc, fund).
Jika unduhan gagal, tetap buat laporan yang menjelaskan kegagalannya.

Data KONFIRMASI & walk-forward (sekali per sesi bila dibutuhkan, ±10 menit setelah unduh_pit): candle spot Agu 2017 - Sep 2019 +
snapshot CMC lama, digabung dengan data baru: `python3 riset/crypto/eksperimen/unduh_lama.py . /tmp/data /tmp/data_lama`
(butuh `/tmp/data/pit` dari `riset/unduh_pit.py` dan candle koin tambahan). Buang duplikat: `rm /tmp/data_lama/klines/{BCC,VEN}.json`
(BCC di CMC = Bitconnect, data Binance BCCUSDT = Bitcoin Cash; VEN = VET).

Data terkunci / daftar koin sesuai masanya (tahap 3 ATURAN_BERSAMA dan review bulanan, **hanya jika dibutuhkan**, ±15-40 menit):
`python3 riset/unduh_pit.py /tmp/data`, lalu unduh koin tambahan H1 + funding: `python3 riset/unduh_crypto.py /tmp/data "$(cat /tmp/data/pit/extra.txt)"`;
jalankan `python3 riset/pit.py swing . /tmp/data` untuk juara, dan versi penantang dengan engine eksperimen.

## PROGRAM UTAMA (pemilik, 6 Nov 2026): OPTIMASI (untung lebih besar tanpa merusak "semua tahun positif")
**Syarat "semua tahun positif" (pemilik, 6 Nov 2026): setiap tahun kalender 2020-skrg R bersih REAL >= +1R, daftar koin tetap.**
Cek: `python3 riset/crypto/eksperimen/tahap0_semua_tahun.py . /tmp/data` (±1 menit, baris `SYARAT`). Biaya REAL: entry stop &
SL/stagnan taker 0,05% + slip 0,03%, TP 25% maker 0,02%, funding aktual per settlement; KONS = slip 0,10%. Tahun = tahun tutup.
**Tahap 0 (6 Nov 2026) LULUS**: juara v2 REAL per tahun 2020 +112,5 · 2021 +120,3 · 2022 +50,1 · 2023 +102,8 · 2024 +113,5 ·
2025 +25,6 · 2026 +40,8R (s.d. 5 Nov); total +562,8R, DD 17,5R. Daftar sesuai masanya (`eksperimen/tahap0_pit.py`): terburuk
2025 +17,5R, DD 30,8R. KONS: terburuk 2025 +19,7R. (Des 2019 = 5 trade pemanasan, bukan tahun data.)
Risiko yang dipantau (dilaporkan, bukan syarat): peluang tahun minus bootstrap 2025 9,4% · 2026 1,8% · lainnya <= 0,2%;
tanpa 2% trade terbaik per tahun 2025 -12,6R; hasil ditopang ekor (2% trade terbaik = 34-80% R tahunan, 2025: 149%);
40/49 koin positif (bukan bergantung koin).

Syarat penantang OPTIMASI (semua wajib):
1. Setiap tahun R bersih REAL >= +1R (daftar tetap) — `t0.lulus(df)`.
2. DD tidak naik > 25% dari juara (R; untuk ide ukuran posisi: MaxDD % ekuitas pada risiko yang sama/ disamakan).
3. Tujuan naik: R/thn (ide aturan) atau CAGR pada MaxDD % yang disamakan (ide ukuran posisi — R/DD tidak berubah bila
   semua risiko dikali sama, jadi kenaikan risiko % saja BUKAN perbaikan).
4. Parameter dipilih lewat walk-forward berlabuh (PEMBAGIAN DATA); tetangga parameter harus ikut bagus; laporkan jumlah varian.
5. Signifikansi ATURAN_BERSAMA B2: P_rasio_lebih_baik >= 0,90 di periode uji, lalu daftar sesuai masanya sekali
   (syarat 1 juga harus terpenuhi di sana), lalu uji maju.
6. Laporkan juga peluang tahun minus (`t0.p_minus`) dan tanpa 2% terbaik; penantang yang memperburuk 2025 secara nyata ditandai.

Tiap Jumat 1-2 jalur (pola: `eksperimen/tambal1_choppy.py` → `t0.run_replay(gate)` + `t0.add_costs` + `t0.ringkas_tahun`;
untuk aturan keluar/ukuran butuh mesin turunan). Urutan jalur (cari ide juga dari literatur, cantumkan sumber):
a. #54 TP sebagian bertingkat (33-50% di 1R / TP kedua di 2-3R) — juga menurunkan ketergantungan ekor.
b. Ukuran posisi: Kelly fraksional dengan batas DD, risiko ikut label conviction (HIGH > LOW), #19 risiko SELL 0,5%.
   (#48 vol BTC sudah gagal 6 Nov.)
c. Jumlah/pemilihan koin dan slot paralel/korelasi (#8, #12; 10 slot = optimum 23 Okt pada DD disamakan).
d. Trailing (#9) dan filter rezim (filter entry sering gagal: #1, #3, #4, #11, #52, #53 — butuh alasan baru).
e. Strategi tambahan dengan sumber edge berbeda: #55 RSI(2) mean-reversion, portofolio terpisah.
Hasil penting 6 Nov (putaran tambal-celah 1, tetap berlaku): filter pasar berombak #52 (ER Kaufman) dan #53 (ADX Wilder) gagal.


## SIKLUS JUMAT (pemilik, 11 Nov 2026) — urutan wajib, laporan dengan bagian tetap
Disalin dari riset XAU dan disesuaikan untuk crypto swing (±7 trade/minggu, posisi 2-10 hari, 10 slot).
1. **Kesehatan minggu ini** (bukan menilai strategi): live = replay data final? Jalankan
   `python3 riset/crypto/sebab_sl.py . /tmp/data 7` → baris KESEHATAN (live vs replay sejak versi aktif; replay memakai sumber
   funding bot = Hyperliquid dulu). Selisih yang wajar: koin yang tidak ada di replay (HYPE: data Binance terlalu pendek untuk
   pemanasan replay) dan efek slot berantai darinya. Selisih lain = DATA (bug) → wajib dianalisa. Cek juga: unduhan/funding
   gagal diam-diam (lengkapi_funding_hl.py), sinyal terlambat, workflow bot gagal.
2. **Penyebab SL minggu ini** (skrip yang sama; perbarui `VERSI_SEJAK` di skrip tiap aturan bot berubah). SL = "kena SL" R <= -0,9.
   Kategori: NEWS (event USD high-impact ForexFactory 3 jam sebelum candle SL, atau kejadian besar crypto di
   `riset/crypto/kejadian.json` ±1 hari — TAMBAH kejadian besar minggu itu ke file ini) = aman · LONJAKAN (candle SL >= 2,5 ATR
   H1; "pasar" bila BTC juga) = dicatat · DATA (live ≠ replay) = WAJIB dianalisa sebagai bug · CELAH = WAJIB dianalisa: arah,
   label, BTC searah/lawan, ATR relatif, umur, dan porsi SL historis kelompok yang sama (normal atau tidak). CELAH berulang
   (>= 2 SL kelompok arah × label × BTC dalam 28 hari, porsi di atas historis dengan P binomial < 0,10) → buka ide baru.
3. **Akumulasi live vs bayangan**: `python3 riset/crypto/bayangan.py . /tmp/data` (menu: v2 live, tanpa stagnan, tanpa TP 25%,
   v1, #19 SELL 0,5%, LOW 1/2; tambahkan penantang uji-maju). Penilaian strategi hanya dari akumulasi >= 4-8 minggu.
4. **Satu putaran riset** (ARAH RISET di bawah) dengan walk-forward (PEMBAGIAN DATA).
4b. **Satu langkah KURIKULUM SKILL** (`riset/KURIKULUM_SKILL.md`; status crypto di `riset/crypto/KURIKULUM.md`; skill aktif: SNR).
   Kerjakan tahap berikutnya, perbarui status, dan tulis di ringkasan `🎓 SKILL <nama>: LULUS TAHAP <n> (<PAHAM/BISA MEMAKAI/LIVE>)`
   bila lulus (atau progres / `📕 SKILL <nama>: BELUM LULUS` setelah 3 putaran gagal di satu tahap).
5. **Gerbang pasang:** perbaikan TEKNIS (bug/data/pesan) boleh diusulkan dipasang minggu itu juga (tetap replay identik). Perubahan
   STRATEGI wajib P >= 0,90 walk-forward + replay IDENTIK + bayangan >= 4 minggu; maksimal 1 perubahan strategi per bulan.
6. **Ringkasan Telegram** berbagian: Kesehatan · Penyebab SL · Live vs bayangan · Riset · Skill · Usulan (butuh "pasang"/"tidak").

## PEMBAGIAN DATA (pemilik, 11 Nov 2026)
- Pakai SELURUH data: candle spot Binance Agu 2017 - skrg (trade mulai Nov 2017 setelah pemanasan), daftar koin SESUAI MASANYA.
- **LANGKAH 1 (sudah, 11 Nov 2026):** vonis APA ADANYA bot live di Nov 2017 - Nov 2019 (data yang belum pernah dipakai merancang)
  → `eksperimen/tahap0_lama.py`; hasil di log.md. Sejak itu 2017-2019 ikut walk-forward (bukan lagi data "baru").
- **LANGKAH 2 (semua ide baru): walk-forward berlabuh per 2 tahun** — `eksperimen/_wf.py` (`load`, `run(gate, ubah)`, `walk`):
  pilih <= 2019 → uji 2020-21 · <= 2021 → uji 2022-23 · <= 2023 → uji 2024-25 · <= 2025 → uji 2026-27. Tabel per tahun 2020-skrg
  yang SEMUANYA hasil uji, jumlah tahun < +1R, tahun terburuk, dan P gabungan semua jendela uji vs sistem dasar
  (`riset/signifikansi.py` pada CSV uji tersambung, awal periode uji 2020-01-01; syarat >= 0,90). Aturan pilih di tiap jendela
  sama: tahun < +1R paling sedikit, lalu R/thn; tetangga parameter harus ikut bagus.
- Sistem dasar (juara v2 di `_wf.py`): 2018 +81 · 2019 +90 · 2020 +83 · 2021 +95 · 2022 +34 · 2023 +100 · 2024 +80 · 2025 +15 ·
  2026 +37R (bersih REAL, sesuai masanya; sebelum Sep 2019 SELL diizinkan karena funding belum ada, lihat log 11 Nov).
- Data KONFIRMASI (dipakai sekali per ide, dilarang memilih parameter): periode yang belum pernah dipakai merancang. Saat ini:
  **data yang datang sesudah tanggal ide dibuat** (uji maju/bayangan) dan koin di luar daftar bot. Bila ada data lebih tua yang
  bisa diperoleh (mis. bursa lain sebelum 2017), itu jadi konfirmasi berikutnya.
- Daftar koin TETAP (backtest_crypto.py, tahap0_semua_tahun.py) tetap dipakai untuk cek cepat & syarat "+1R tiap tahun", tetapi
  keputusan ide memakai walk-forward sesuai masanya.

## ARAH RISET (pemilik, 11 Nov 2026)
- Semua tahun sudah >= +1R → **OPTIMASI UNTUNG** (sizing, koin, keluar, komponen baru) TANPA menambah tahun < +1R.
  Bila suatu saat ada tahun minus → naikkan EDGE PER TRADE / turunkan variansi tahunan (bukan menambal tahun per tahun).
- Ukuran sukses: R/trade, R/thn, simpangan R tahunan, peluang tahun minus Φ(-rata/simpangan) (`eksperimen/evaluasi_live.py`),
  tahun < +1R di walk-forward, DD. Catatan 11 Nov: P(minus) 1-1,4% dengan rata 2018/2020-2025, tetapi ±18% bila edge tetap di
  level 2025-skrg (±28-36R/thn) → prioritas = edge per trade di rezim terbaru.
- **Eksplorasi pustaka & kombinasi** (pola riset/xau/eksperimen/pustaka.py & kombinasi.py): strategi/indikator klasik di luar yang
  dipakai sekarang (mis. Ichimoku, Supertrend, Parabolic SAR, MACD, Alligator, Bollinger squeeze/fade, Donchian/turtle soup, NR7,
  Heikin-Ashi, RSI(2), CLV, OBV/volume, funding/OI) sebagai komponen suara arah (+1/-1/0) di candle cek; uji (a) MANDIRI dan
  (b) sebagai filter/penguat sinyal breakout, dan KOMBINASI 2-4 komponen yang SEPAKAT. Pilih di periode pilih walk-forward;
  **uji pembanding**: porsi lolos konfirmasi (semua jendela uji positif) di 20/100 teratas vs di semua kombinasi — bila tidak
  jauh lebih tinggi, hasil teratas = kebetulan. Laporkan jumlah kombinasi yang dinilai.

## 2. Tentukan mode
- Jika **Jumat berikutnya sudah masuk bulan baru** (hari ini Jumat terakhir bulan ini) → **REVIEW BULANAN** (langkah 3 + 4).
- Selain itu → **RISET MINGGUAN** (langkah 3 saja).

## 3. Riset mingguan: uji 1-2 ide crypto
1. Uji 2 ide: ide teratas berstatus `antri` dari `riset/crypto/ide.md`, **ditambah 1 ide baru** sesuai
   ATURAN_BERSAMA bagian A (literatur = nilai tambah, tidak wajib).
2. Tulis hipotesis singkat, lalu uji dengan skrip di `riset/crypto/eksperimen/<nama-ide>.py`.
   Ide yang memengaruhi urutan atau slot posisi (filter sinyal, batas posisi, aturan keluar) wajib replay penuh,
   bukan filter setelah backtest.
3. Bandingkan dengan juara (aturan yang sedang live):
   - Walk-forward (PEMBAGIAN DATA) per tahun 2020-skrg; juga periode lama 2020-2023 & baru 2024-skrg daftar tetap (cek cepat).
   - Total R, R rata-rata, win rate, drawdown terburuk, rasio total R / drawdown.
   - Ketahanan: hasil tanpa 2% trade terbaik.
4. Keputusan:
   - **LOLOS** jika rasio R/drawdown membaik ≥ 10% di periode lama **dan** baru, tidak lebih buruk di ≥ 4 dari 6 tahun terakhir,
     dan tidak bergantung pada segelintir trade besar. Ide ini lanjut ke tahap 2-4 ATURAN_BERSAMA
     (signifikansi, data terkunci, uji maju) sebelum menjadi **kandidat penantang**.
   - **GAGAL** jika tidak memenuhi. Catat alasannya agar tidak diuji ulang.
   - **PERLU DATA** jika hasil bergantung pada data yang belum cukup (misalnya data live).
5. Catat di `riset/crypto/log.md` (tanggal, ide, angka utama, keputusan) dan perbarui status di `riset/crypto/ide.md`.
   Tambahkan ide crypto baru yang muncul dari analisis ke `riset/crypto/ide.md` dengan status `antri`
   (lanjutkan penomoran dari nomor tertinggi di daftar crypto maupun XAU, agar nomor tidak bentrok).

## 4. Review bulanan (hanya Jumat terakhir bulan ini)
Tambahan selain langkah 3:
1. Statistik juara terbaru dari backtest (per tahun, per label conviction, long vs short).
2. Bandingkan hasil live (`state.json` field `hist`, `jurnal/crypto-*.json`) dengan backtest periode yang sama
   (sejak `LIVE_START` crypto di `kesehatan.py`). Selisih besar menandakan masalah eksekusi atau data.
3. Cek apakah label conviction masih valid (HIGH > MEDIUM > LOW, juga di tahun terakhir).
4. Uji ML walk-forward: `python3 riset/ml_walkforward.py` membutuhkan file pickle dengan kolom `score` dan `year`;
   buat dari CSV backtest dengan aturan skor yang sama seperti `riset/analisis.py`.
5. **Bias koin selamat** (ATURAN_BERSAMA bagian C): `python3 riset/pit.py swing . /tmp/data`, laporkan selisih tetap vs sesuai masanya.
6. Rangkum semua **kandidat penantang** crypto yang masih berlaku beserta buktinya, dan usulan yang masih menunggu
   persetujuan pemilik: apa yang diubah, bukti periode lama dan baru, dampak ke profit dan drawdown.

## 5. Keluaran
- `riset/laporan/crypto/riset-YYYY-MM-DD.md` - laporan lengkap (angka, tabel, kesimpulan).
- Sejak 11 Nov 2026 ringkasan mengikuti bagian SIKLUS JUMAT langkah 6 (Kesehatan · Penyebab SL · Live vs bayangan · Riset ·
  Skill · Usulan); baris skill boleh memakai 🎓/📕 sesuai kurikulum.
- `riset/laporan/crypto/riset-YYYY-MM-DD.txt` - ringkasan untuk Telegram, **maks 3.500 karakter**, HTML Telegram sederhana
  (hanya `<b>` dan `<pre>`), bahasa Indonesia, gaya sama dengan bot: judul tebal `RISET CRYPTO` atau `REVIEW BULANAN CRYPTO`,
  tanggal, garis `────────────────────`, judul bagian tebal dengan garis di bawahnya, tanpa emoji.
  Baris di dalam `<pre>` maksimal ±38 karakter.
  Isi: mode, ide yang diuji dan keputusannya, kandidat penantang (jika ada), dan untuk review bulanan:
  ringkasan live vs backtest, status label, hasil uji ML, daftar usulan.
- Karakter `<`, `>`, `&` di luar tag HTML harus ditulis sebagai `&lt;`, `&gt;`, `&amp;`.
