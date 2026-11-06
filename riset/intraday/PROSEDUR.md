# Prosedur riset · INTRADAY

Instruksi untuk routine **"Riset Bot Intraday"** (setiap Jumat 01:37 WIB).
Tujuan: menemukan perbaikan strategi intraday yang terbukti dengan data, lalu **mengusulkannya** ke pemilik.
Routine tidak pernah mengubah juara (`PARAM` di `riset/backtest_intraday.py`) maupun bot live.
Perubahan dipasang hanya setelah pemilik setuju di chat. Riset crypto (swing) dan XAU dikerjakan routine terpisah.

**Wajib baca dulu `riset/ATURAN_BERSAMA.md`** (sumber ide, uji signifikansi, data terkunci, uji maju). Aturan di sana
berlaku di atas kriteria LOLOS di bawah: lolos kriteria di bawah = lolos tahap 1 saja.

## PROGRAM UTAMA (pemilik, 6 Nov 2026): OPTIMASI — untung lebih besar tanpa merusak "semua tahun positif"
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
**Uji maju yang berjalan:** I-25 (bobot dispersi, sejak 6 Nov 2026). Trade juara sama persis; hitung ulang bobot per trade baru
dengan `opt1_ukuran_posisi_2026-11-06.py` dan bandingkan R berbobot vs juara hanya untuk trade dengan `t` ≥ 2026-11-06.

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
```
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
3. Bandingkan dengan juara:
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
