# Prosedur riset · INTRADAY

Instruksi untuk routine **"Riset Bot Intraday"** (setiap Jumat 01:37 WIB).
Tujuan: menemukan perbaikan strategi intraday yang terbukti dengan data, lalu **mengusulkannya** ke pemilik.
Routine tidak pernah mengubah juara (`PARAM` di `riset/backtest_intraday.py`) maupun bot live.
Perubahan dipasang hanya setelah pemilik setuju di chat. Riset crypto (swing) dan XAU dikerjakan routine terpisah.

**Wajib baca dulu `riset/ATURAN_BERSAMA.md`** (sumber ide, uji signifikansi, data terkunci, uji maju). Aturan di sana
berlaku di atas kriteria LOLOS di bawah: lolos kriteria di bawah = lolos tahap 1 saja.

## SIKLUS JUMAT (pemilik, 11 Nov 2026; diadaptasi dari riset XAU) — urutan wajib, laporan dengan bagian tetap
1. **Kesehatan minggu ini** (bukan menilai strategi; ±5-10 trade/minggu terlalu sedikit): sinyal live = replay data final?
   `python3 riset/intraday/sebab_sl.py . /tmp/data 7` mencetak baris "Kesetaraan sejak ..." (live vs replay per trade, beda koin/
   waktu isi/alasan keluar/R). Cek juga: cron terlambat (waktu isi live vs replay), data Binance macet, koin baru listing.
   Catatan: backtest/replay melewati koin dengan data < 5.000 candle 15m (±52 hari) atau < 1.400 candle H1; bot live tidak
   → koin baru listing (mis. HYPE spot sejak 24 Sep 2026) bisa membuat live ≠ replay. Ini keterbatasan replay, bukan bug bot.
2. **Penyebab SL minggu ini:** `python3 riset/intraday/sebab_sl.py . /tmp/data 7` (perbarui `VERSI_SEJAK` di skrip tiap aturan
   bot berubah). Kategori: DATA (live ≠ replay) = WAJIB dianalisa sebagai bug · NEWS (event USD high-impact 60 mnt sebelum isi
   s.d. SL) = aman · LONJAKAN (candle 15m SL ≥ 2,5 ATR; "pasar" bila BTC ikut ≥ 2 ATR) = dicatat · CELAH = WAJIB dianalisa:
   modul, tren BTC, ATR relatif, dan porsi SL historis modul itu di kondisi sama (normal atau tidak). CELAH berulang (≥ 2 SL
   modul & kondisi sama dalam 28 hari, porsi > 1,25× historis) → buka ide baru.
3. **Akumulasi live vs bayangan:** `python3 riset/intraday/bayangan.py . /tmp/data` (live vs replay juara vs kandidat uji-maju,
   per minggu ISO). Penilaian strategi hanya dari akumulasi ≥ 4-8 minggu (≥ 60 trade sebelum usulan).
4. **Satu putaran riset** (ARAH UTAMA di bawah) dengan PEMBAGIAN DATA di bawah.
4b. **Satu langkah KURIKULUM SKILL** (`riset/KURIKULUM_SKILL.md`; intraday: skill 1 SNR, status di bagian SKILL di bawah).
5. **Gerbang pasang:** perbaikan teknis (bug/data/pesan) boleh diusulkan dipasang minggu itu juga. Perubahan STRATEGI wajib
   P ≥ 0,90 walk-forward + replay IDENTIK (`riset/replay_intraday.py`) + bayangan ≥ 4 minggu; maksimal 1 perubahan strategi/bulan.
6. **Ringkasan Telegram** berbagian: Kesehatan · Penyebab SL · Live vs bayangan · Riset · Skill · Usulan (butuh "pasang"/"tidak").
   Skill yang lulus ditulis `🎓 SKILL <nama>: LULUS TAHAP <n> (<PAHAM/BISA MEMAKAI/LIVE>)` (satu-satunya emoji yang dipakai).

## PEMBAGIAN DATA (pemilik, 11 Nov 2026)
- **Seluruh data tersedia dipakai**: Binance spot Mar 2020-sekarang (data utama, daftar koin sesuai masanya = uji utama) +
  **2018-2019** (`eksperimen/unduh_2018.py`, belum pernah dipakai merancang juara mana pun sampai 11 Nov 2026).
- **Konfirmasi (sekali per ide, tidak untuk memilih):** 2018-01 s.d. 2020-02 = periode yang belum dipakai merancang.
  Vonis apa adanya juara v3 di periode ini dibuat 11 Nov 2026 (lihat log); sejak itu periode ini hanya untuk konfirmasi ide yang
  sudah lolos walk-forward. Keterbatasan: futures/funding Binance baru ada Sep 2019 → sebelum itu funding 0 dan B-short tidak aktif.
- **Walk-forward berlabuh per 2 tahun** untuk SEMUA ide baru: pilih parameter hanya dari 2020..Y, uji Y+1..Y+2, geser 2 tahun:
  pilih ≤2021 → uji 2022-23 · pilih ≤2023 → uji 2024-25 · pilih ≤2025 → uji 2026-27. Laporkan tabel per tahun 2022-2026 yang
  SEMUANYA hasil uji, jumlah tahun minus, tahun terburuk, dan P gabungan semua jendela uji vs juara (`signifikansi.banding`, ≥ 0,90).
  Aturan pemilihan sama di tiap jendela (skor = tahun minus paling sedikit, lalu R/thn; tetangga parameter harus ikut bagus).
  Pola skrip: `eksperimen/kombinasi_2026-11-11.py` (pemilihan per jendela + uji pembanding).
- Indikator lambat butuh pemanasan (EMA200 H1/15m, SMA100 harian): hitung trade setelah indikator terbentuk.
- Uji maju bot live = hakim terakhir.

## ARAH UTAMA (pemilik, 11 Nov 2026)
- **Semua tahun untung → OPTIMASI; belum → naikkan EDGE PER TRADE / turunkan variansi tahunan** (bukan menambal tahun per tahun:
  menambal hanya memindahkan rugi).
- **Status 11 Nov 2026: BELUM → arah = NAIKKAN EDGE PER TRADE** (usulan, menunggu konfirmasi pemilik). Data perancangan 2020-2026
  semua tahun untung (PIT, biaya juara; terburuk 2025 +9,4R), tetapi vonis apa adanya di data yang belum pernah dilihat
  (Mar 2018 - Feb 2020) memberi **2019 -5,6R** (stres -17,2R), avg +0,022R/trade. R tahunan 2018-2026: rata +31, simpangan 28 →
  peluang tahun minus ±13%/tahun (2020-2026 saja ±7%; era 2024+ ±5%). Edge 2024-skrg +0,061R/trade, fee = 17% edge kotor
  (2025: 42%). Ukuran sukses: R/trade (bersih & stres), simpangan R tahunan, peluang tahun minus, jumlah tahun minus 2018-2026
  (2018-19 hanya konfirmasi), P vs juara walk-forward.
- Prioritas jalur edge: (1) buang/perkecil bagian ber-edge ±0 (B-long saat Alligator H1 berlawanan -0,018R/trade, sesi 15 & 17 WIB,
  koin PF < 1 berulang); (2) perbesar porsi bagian ber-edge tinggi (A-long +0,124R, ZEC/UNI/ADA-tipe); (3) turunkan biaya per trade
  (fee = ±0,019R/trade: lebih banyak maker, keluar limit); (4) cari komponen baru ber-edge ≥ +0,15R/trade dengan sumber edge berbeda
  (skill SNR: tembus level hari/minggu sebelumnya).
- Tiap putaran boleh menjelajah **pustaka indikator/strategi klasik** dan **KOMBINASI 2-4 komponen yang sepakat**, selalu dengan
  **uji pembanding** (porsi lolos di N teratas vs semua kombinasi; bila tidak lebih tinggi = tidak ada informasi, hanya kebetulan).
  Pola: `riset/xau/eksperimen/pustaka.py` & `kombinasi.py`, versi intraday `eksperimen/kombinasi_2026-11-11.py`.
  Filter pasca-trade hanya saringan awal; kandidat wajib replay penuh (slot berubah).

## SKILL (KURIKULUM_SKILL.md) · intraday
Skill aktif: **1 · SNR**. Status: Tahap 0 (definisi mesin) selesai 11 Nov 2026; **Tahap 1 PAHAM: LULUS untuk jenis PERIODE**
(high/low hari & minggu sebelumnya) dan SWING-D1 — efeknya kebalikan teori klasik: level lebih sering DITEMBUS dari level acak
(P ≥ 0,95 di 2020-22 & 2023-26, kedua arah). Swing H4 nyata tetapi sangat kecil (±0,4 poin); angka bulat & supply-demand belum.
**Tahap 1b LULUS 13 Nov 2026 untuk PERIODE**: tembusan lebih sering lanjut +1 ATR dari acak (+1..+3 poin, P ≥ 0,96, kedua periode & arah),
tetapi drift 12 jam tidak konsisten (`eksperimen/skill_snr_1b_2026-11-13.py`) → pakai sebagai filter risiko, bukan strategi tembus.
Langkah berikutnya: Tahap 2 BISA MEMAKAI (filter order limit B/A di dekat level
PERIODE, SL di balik level, strategi tembus mandiri) dengan walk-forward. Skrip: `eksperimen/skill_snr_2026-11-11.py`.

## PROGRAM UTAMA (pemilik, 6 Nov 2026): OPTIMASI — untung lebih besar tanpa merusak "semua tahun positif"
**UPDATE 11 Nov 2026:** vonis data 2018-2019 (belum pernah dilihat) → 2019 minus → arah sekarang NAIKKAN EDGE PER TRADE (lihat
ARAH UTAMA di atas). Jalur 1-5 di bawah tetap menjadi daftar ide, tetapi ukuran suksesnya R/trade & variansi tahunan.
**Tahap 0 (6 Nov 2026, `eksperimen/tahap0_semua_tahun_2026-11-06.py`): LULUS, tetapi TIPIS.** Juara v3, daftar koin sesuai masanya,
biaya juara (maker 0,02%, taker 0,07% termasuk slippage, funding): setiap tahun 2020-2026 R bersih > 0, juga tanpa 2% trade terbaik
(per tahun maupun global). Tahun terburuk **2025 +9,4R** (tanpa 2% terbaik hanya **+1,6R**). Daftar tetap juga lulus (2025 +18,0R).
**Uji stres eksekusi** (taker 0,12% + limit hanya terisi jika harga menembus 0,05%): **2025 -6,5R**, tanpa 2% terbaik 2024 & 2025
minus → "semua tahun positif" belum tahan terhadap eksekusi yang sedikit lebih buruk. Celah terbesar: **B-long 2024-2025**
(+5,7R / -2,8R; koin peringkat 1-10, BTC naik > 10% dalam 30 hari) dan sesi isi 15-20 WIB.

Tiap Jumat satu putaran, jalur bertahap (lanjutkan dari jalur berikutnya yang belum selesai):
1. Ukuran posisi / volatility targeting — **putaran 1 selesai 6 Nov 2026**: I-25 `uji-maju`, I-08 & I-24 gagal.
2. Pemilihan koin & sesi (B-long peringkat 1-10, sesi 15-20 WIB, akhir pekan vs hari kerja, peringkat 26-50).
3. Aturan keluar (terutama B-long yang paling peka biaya eksekusi).
4. Filter rezim (BTC naik > 10%/30 hari untuk B-long, jarak BTC ke EMA200).
5. Strategi tambahan dengan sumber edge berbeda (bukan dip/reversal lagi).
Ide dicari dari literatur/internet bila ada (tandai `[lit]`, cantumkan judul + tautan). Skrip: `eksperimen/opt<N>_*.py`
(pola: `opt1_ukuran_posisi_2026-11-06.py` untuk bobot pasca-trade; `pit_2026-11-06.py` untuk logika order baru + replay penuh).
Tabel per tahun dibuat ulang dengan `tahap0_semua_tahun_2026-11-06.py`; bedah kondisi pasar dengan `celah_2026-11-06.py`.

**Syarat LOLOS putaran optimasi** (di atas kriteria langkah 3.4 dan ATURAN_BERSAMA):
- PIT biaya standar: **tidak ada tahun minus**, juga tanpa 2% trade terbaik per tahun.
- Drawdown (R) tidak naik > 25% dari juara; rasio R/DD naik ≥ 10% di 2020-2023 **dan** 2024-skrg; **P_rasio ≥ 0,90**.
- Trade/minggu tidak turun di bawah ±5/minggu per tahun (juara 5,8-14,8) kecuali pemilik setuju.
- **Pagar stres** (usulan, menunggu persetujuan pemilik): tahun terburuk pada uji stres eksekusi tidak lebih buruk dari juara (-6,5R).
- Tetangga parameter ikut lolos (mayoritas). Parameter dipilih di 2020-2023; 2024-skrg hanya menguji.
- Lolos → `uji-maju` (≥ 6 minggu & ≥ 60 trade data baru sejak tanggal lolos), baru diusulkan.
**Uji maju:** I-25 (bobot dispersi) DIHENTIKAN 11 Nov 2026 — gagal konfirmasi 2018-Feb 2020 (lebih buruk tiap tahun, 2019 -10,3 vs
-5,6R, DD 25,7 vs 17,9R; `eksperimen/konfirmasi_i25_2018_2026-11-11.py`). Kolom I-25 di `bayangan.py` hanya pembanding.
Tidak ada kandidat uji-maju lain saat ini.

## 0. Aturan keras
- **Jangan ubah** file bot: `signal_bot.py`, `gold_bot.py`, `templates.py`, `gold_templates.py`, `commands.py`,
  `jurnal.py`, `kesehatan.py`, `baseline.json`, file state (`*.json` di root), `.github/`,
  dan **juara intraday**: `intraday_bot.py`, `intraday_state.json`, `riset/backtest_intraday.py`, `riset/unduh_intraday.py`,
  `riset/replay_intraday.py`, `riset/intraday/STRATEGI.md`.
- Hanya tulis di `riset/intraday/` (kecuali STRATEGI.md) dan `riset/laporan/intraday/`.
- Kerjakan di branch baru `claude/riset-intraday-YYYY-MM-DD` (tanggal WIB hari ini), commit, lalu push branch itu.
  Workflow `kirim-laporan-riset.yml` otomatis mengirim ringkasan ke chat pribadi pemilik dan menyalin berkas riset ke main.
- Jangan membuat routine, scheduled task, atau pengingat baru.

## 1. Persiapan data (±10-15 menit)
```bash
pip install -q --break-system-packages numpy pandas scipy
COINS=$(python3 -c "import signal_bot as s; print(' '.join(s.COINS))")
python3 riset/unduh_crypto.py /tmp/data "$COINS"       # candle H1 + funding
python3 riset/unduh_intraday.py /tmp/data "$COINS"     # candle 15 menit
python3 riset/backtest_intraday.py . /tmp/data /tmp/data/trades_intraday.csv
# WAJIB untuk intraday: daftar koin sesuai masanya (ekspektasi jujur; ±30-40 menit unduhan pertama)
python3 riset/unduh_pit.py /tmp/data
python3 riset/unduh_crypto.py /tmp/data "$(cat /tmp/data/pit/extra.txt)"
python3 riset/unduh_intraday.py /tmp/data "$(cat /tmp/data/pit/extra.txt)"
python3 riset/pit_intraday.py . /tmp/data            # juara; penantang: tambah argumen JSON parameter
# Siklus Jumat: kesehatan, penyebab SL, live vs bayangan
python3 riset/intraday/sebab_sl.py . /tmp/data 7
python3 riset/intraday/bayangan.py . /tmp/data
# Hanya untuk KONFIRMASI ide yang sudah lolos walk-forward (±25 menit, 150 koin): data 2017-08 s.d. 2019-12
python3 riset/intraday/eksperimen/unduh_2018.py . /tmp/data /tmp/data18
```
Statistik lengkap juara (per periode/tahun/koin/arah/jam, DD & lama pulih, biaya & funding, peluang tahun minus):
`python3 riset/intraday/eksperimen/evaluasi_2026-11-11.py . /tmp/data /tmp/out`.
Sejak v3 (30 Okt 2026), keputusan LOLOS/GAGAL intraday memakai hasil **sesuai masanya** (`pit_intraday.py`) sebagai uji utama;
hasil daftar tetap hanya pembanding. Ide yang butuh logika baru: salin `orders()` ke skrip eksperimen dan gunakan
`pit_intraday.run_pit` sebagai pola (lihat `eksperimen/pit_*.py`).
Output terakhir adalah statistik juara (semua, 2020-2023, 2024-sekarang, per tahun). Simpan untuk pembanding.
Jika unduhan gagal, tetap buat laporan yang menjelaskan kegagalannya.

Data terkunci / daftar koin sesuai masanya (tahap 3 ATURAN_BERSAMA dan review bulanan, **hanya jika dibutuhkan**, ±15-40 menit):
`python3 riset/unduh_pit.py /tmp/data`, lalu unduh koin tambahan H1 + funding + 15m: `unduh_crypto.py` dan `unduh_intraday.py` dengan `$(cat /tmp/data/pit/extra.txt)`;
jalankan `python3 riset/pit_intraday.py . /tmp/data` untuk juara vs penantang (parameter lewat argumen JSON).

## 2. Tentukan mode
- Jika **Jumat berikutnya sudah masuk bulan baru** (hari ini Jumat terakhir bulan ini) → **REVIEW BULANAN** (langkah 3 + 4).
- Selain itu → **RISET MINGGUAN** (langkah 3 saja).

## 3. Riset mingguan: uji 1-2 ide
1. Uji 2 ide: ide teratas berstatus `antri` dari `riset/intraday/ide.md`, **ditambah 1 ide baru** sesuai
   ATURAN_BERSAMA bagian A (literatur = nilai tambah, tidak wajib).
2. Tulis hipotesis singkat, lalu uji dengan skrip di `riset/intraday/eksperimen/<nama-ide>.py`.
   Cara standar: `import backtest_intraday as bi` lalu `bi.run(".", "/tmp/data", {"PARAMETER": nilai})`.
   Untuk logika baru, salin fungsi `orders()`/`portfolio()` ke skrip eksperimen dan ubah di sana (jangan ubah file juara).
   **Selalu replay penuh** lewat `portfolio()` (model order menunggu + pembatalan), bukan filter setelah backtest:
   slot, pembatalan, dan urutan isi berubah ketika aturan berubah.
3. Bandingkan dengan juara (sejak 11 Nov 2026 pembagian data = walk-forward berlabuh, lihat PEMBAGIAN DATA; kriteria lama
   "periode lama 2020-2023 / baru 2024-skrg" di bawah tetap dilaporkan sebagai pembanding):
   - Periode lama 2020-2023 **dan** periode baru 2024-sekarang, serta per tahun.
   - R/trade, total R/tahun, win rate, drawdown terburuk (R), rasio R/tahun ÷ drawdown, fill rate.
   - Ketahanan: total R tanpa 2% trade terbaik (`tanpa_top2`).
   - Uji tetangga: geser parameter baru ±1 langkah. Ide yang hanya bagus di satu angka = **GAGAL** (overfit).
4. Keputusan:
   - **LOLOS** jika rasio R/DD membaik ≥ 10% di periode lama **dan** baru, tidak lebih buruk di ≥ 5 dari 7 tahun,
     `tanpa_top2` tidak memburuk, dan tetangga parameternya juga membaik. Ide ini lanjut ke tahap 2-4 ATURAN_BERSAMA
     (signifikansi, data terkunci, uji maju) sebelum menjadi **kandidat penantang**.
   - **GAGAL** jika tidak memenuhi. Catat alasannya agar tidak diuji ulang.
   - **PERLU DATA** jika butuh data yang belum ada (misalnya data live).
   - Jangan memilih parameter karena hasil 2024-sekarang paling bagus; periode baru hanya untuk **menguji**.
5. Catat di `riset/intraday/log.md` (tanggal, ide, angka utama, keputusan) dan perbarui status di `riset/intraday/ide.md`.
   Tambahkan ide baru ke `riset/intraday/ide.md` dengan status `antri` (lanjutkan penomoran I-xx).

## 4. Review bulanan (hanya Jumat terakhir bulan ini)
Tambahan selain langkah 3:
1. Statistik juara terbaru per tahun, per modul (A, B-long, B-short), per cara keluar (TP/RSI/SL/WAKTU).
2. Cek kesehatan edge: R/trade 6 bulan terakhir vs rata-rata 2024-sekarang. Jika 6 bulan terakhir negatif,
   tandai **PERINGATAN** di laporan dan cari penyebabnya (modul mana, arah mana).
3. Bot intraday live sejak 27 Okt 2026: bandingkan `jurnal/intraday-*.json` (kolom `R`) dengan backtest periode yang sama
   (trade dengan koin & waktu isi sama). Selisih besar menandakan masalah eksekusi, data, atau jadwal cron.
4. **Risiko gabungan swing + intraday** dan **bias koin selamat** (ATURAN_BERSAMA bagian C). Butuh CSV swing:
   `python3 riset/unduh_crypto.py /tmp/data "$COINS"` (sudah) lalu `python3 riset/backtest_crypto.py . /tmp/data /tmp/data/trades_swing.csv`.
5. Rangkum semua **kandidat penantang** yang masih berlaku beserta buktinya: apa yang diubah, bukti periode lama dan baru,
   dampak ke profit, drawdown, dan jumlah sinyal.

## 5. Keluaran
- `riset/laporan/intraday/riset-YYYY-MM-DD.md` - laporan lengkap (angka, tabel, kesimpulan).
- `riset/laporan/intraday/riset-YYYY-MM-DD.txt` - ringkasan untuk Telegram, **maks 3.500 karakter**, HTML Telegram sederhana
  (hanya `<b>` dan `<pre>`), bahasa Indonesia, judul tebal `RISET INTRADAY` atau `REVIEW BULANAN INTRADAY`,
  tanggal, garis `────────────────────`, judul bagian tebal dengan garis di bawahnya, tanpa emoji.
  Baris di dalam `<pre>` maksimal ±38 karakter.
  Isi: mode, statistik juara singkat, ide yang diuji dan keputusannya, kandidat penantang (jika ada).
- Karakter `<`, `>`, `&` di luar tag HTML harus ditulis sebagai `&lt;`, `&gt;`, `&amp;`.
