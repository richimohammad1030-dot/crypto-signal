# Prosedur riset · INTRADAY

Instruksi untuk routine **"Riset Bot Intraday"** (setiap Jumat 01:37 WIB).
Tujuan: menemukan perbaikan strategi intraday yang terbukti dengan data, lalu **mengusulkannya** ke pemilik.
Routine tidak pernah mengubah juara (`PARAM` di `riset/backtest_intraday.py`) maupun bot live.
Perubahan dipasang hanya setelah pemilik setuju di chat. Riset crypto (swing) dan XAU dikerjakan routine terpisah.

**Wajib baca dulu `riset/ATURAN_BERSAMA.md`** (sumber ide, uji signifikansi, data terkunci, uji maju). Aturan di sana
berlaku di atas kriteria LOLOS di bawah: lolos kriteria di bawah = lolos tahap 1 saja.

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
