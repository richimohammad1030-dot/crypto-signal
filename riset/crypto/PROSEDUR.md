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

Data terkunci / daftar koin sesuai masanya (tahap 3 ATURAN_BERSAMA dan review bulanan, **hanya jika dibutuhkan**, ±15-40 menit):
`python3 riset/unduh_pit.py /tmp/data`, lalu unduh koin tambahan H1 + funding: `python3 riset/unduh_crypto.py /tmp/data "$(cat /tmp/data/pit/extra.txt)"`;
jalankan `python3 riset/pit.py swing . /tmp/data` untuk juara, dan versi penantang dengan engine eksperimen.

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
   - Periode lama 2020-2023 **dan** periode baru 2024-sekarang, serta per tahun.
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
- `riset/laporan/crypto/riset-YYYY-MM-DD.txt` - ringkasan untuk Telegram, **maks 3.500 karakter**, HTML Telegram sederhana
  (hanya `<b>` dan `<pre>`), bahasa Indonesia, gaya sama dengan bot: judul tebal `RISET CRYPTO` atau `REVIEW BULANAN CRYPTO`,
  tanggal, garis `────────────────────`, judul bagian tebal dengan garis di bawahnya, tanpa emoji.
  Baris di dalam `<pre>` maksimal ±38 karakter.
  Isi: mode, ide yang diuji dan keputusannya, kandidat penantang (jika ada), dan untuk review bulanan:
  ringkasan live vs backtest, status label, hasil uji ML, daftar usulan.
- Karakter `<`, `>`, `&` di luar tag HTML harus ditulis sebagai `&lt;`, `&gt;`, `&amp;`.
