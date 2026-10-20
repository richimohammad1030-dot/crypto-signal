# Prosedur riset (Lapis 3)

Dokumen ini adalah instruksi untuk routine Claude yang berjalan **setiap Jumat 01:00 WIB**.
Tujuan: menemukan perbaikan bot yang terbukti dengan data, lalu **mengusulkannya** ke pemilik.
Routine tidak pernah mengubah bot live. Perubahan hanya dipasang setelah pemilik setuju di chat.

## 0. Aturan keras
- **Jangan ubah** file bot: `signal_bot.py`, `gold_bot.py`, `templates.py`, `gold_templates.py`, `commands.py`,
  `jurnal.py`, `kesehatan.py`, `baseline.json`, file state (`*.json` di root), dan `.github/`.
- Hanya tulis di dalam folder `riset/`.
- Kerjakan di branch baru `claude/riset-YYYY-MM-DD` (tanggal WIB hari ini), commit, lalu push branch itu.
  Workflow `kirim-laporan-riset.yml` otomatis mengirim ringkasan ke chat pribadi pemilik dan menyalin
  `riset/laporan/`, `riset/log.md`, `riset/ide.md` ke main.
- Jangan membuat routine, scheduled task, atau pengingat baru.

## 1. Persiapan data (±5-8 menit)
```bash
pip install -q --break-system-packages numpy pandas scikit-learn scipy
COINS=$(python3 -c "import signal_bot as s; print(' '.join(s.COINS))")
python3 riset/unduh_crypto.py /tmp/data "$COINS"
python3 riset/unduh_xau.py /tmp/data
python3 riset/backtest_crypto.py . /tmp/data /tmp/data/trades_crypto.csv
python3 riset/backtest_xau.py . /tmp/data/xau.json /tmp/data/trades_xau.csv
```
Hasil backtest crypto berisi faktor setiap trade (trend, ext, dist, slpct, mom20, slope, breadth, rank, btc, fund).
Jika unduhan gagal, tetap buat laporan yang menjelaskan kegagalannya.

## 2. Tentukan mode
- Jika **Jumat berikutnya sudah masuk bulan baru** (hari ini Jumat terakhir bulan ini) → **REVIEW BULANAN** (langkah 3 + 4).
- Selain itu → **RISET MINGGUAN** (langkah 3 saja).

## 3. Riset mingguan: uji 1-2 ide
1. Ambil 1-2 ide teratas berstatus `antri` dari `riset/ide.md` (prioritas tertinggi dulu).
2. Tulis hipotesis singkat, lalu uji dengan skrip di `riset/eksperimen/<nama-ide>.py`
   (salin dan modifikasi `backtest_crypto.py`/`backtest_xau.py`, atau filter hasil trade jika ide tidak memengaruhi slot).
   Jika ide memengaruhi urutan atau slot posisi (filter sinyal, batas posisi), wajib replay penuh, bukan filter setelahnya.
3. Bandingkan dengan versi juara (aturan sekarang):
   - Periode lama 2020-2023 **dan** periode baru 2024-sekarang, serta per tahun.
   - Total R, R rata-rata, win rate, drawdown terburuk, rasio total R / drawdown.
   - Ketahanan: hasil tanpa 2% trade terbaik.
4. Keputusan:
   - **LOLOS** jika rasio R/drawdown membaik ≥ 10% di periode lama **dan** baru, tidak lebih buruk di ≥ 4 dari 6 tahun terakhir,
     dan tidak bergantung pada segelintir trade besar. Ide ini menjadi **kandidat penantang**.
   - **GAGAL** jika tidak memenuhi. Catat alasannya agar tidak diuji ulang.
   - **PERLU DATA** jika hasil bergantung pada data yang belum cukup (misalnya data live).
5. Catat di `riset/log.md` (tanggal, ide, angka utama, keputusan) dan perbarui status di `riset/ide.md`.
   Tambahkan ide baru yang muncul dari analisis ke `riset/ide.md` dengan status `antri`.

## 4. Review bulanan (hanya Jumat terakhir bulan ini)
Tambahan selain langkah 3:
1. Jalankan `python3 riset/analisis.py . /tmp/data/trades_crypto.csv /tmp/data/trades_xau.csv` untuk statistik, label, dan uji ML.
   Jangan commit `baseline.json` (yang memperbarui adalah workflow laporan angka tanggal 1).
2. Bandingkan hasil live (`state.json`, `gold_state.json`, `jurnal/`) dengan backtest periode yang sama.
   Selisih besar menandakan masalah eksekusi atau data.
3. Cek apakah label conviction masih valid (HIGH > MEDIUM > LOW, juga di tahun terakhir).
4. Rangkum semua **kandidat penantang** yang masih berlaku beserta buktinya, dan usulan yang masih menunggu persetujuan pemilik.
   Usulan ditulis jelas: apa yang diubah, bukti periode lama dan baru, dampak ke profit dan drawdown.

## 5. Keluaran
- `riset/laporan/riset-YYYY-MM-DD.md` - laporan lengkap (angka, tabel, kesimpulan).
- `riset/laporan/riset-YYYY-MM-DD.txt` - ringkasan untuk Telegram, **maks 3.500 karakter**, HTML Telegram sederhana
  (hanya `<b>` dan `<pre>`), bahasa Indonesia, gaya sama dengan bot: judul tebal, tanggal, garis `────────────────────`,
  judul bagian tebal dengan garis di bawahnya, tanpa emoji. Baris di dalam `<pre>` maksimal ±38 karakter.
  Isi: mode (riset mingguan / review bulanan), ide yang diuji dan keputusannya, kandidat penantang (jika ada),
  dan untuk review bulanan: ringkasan live vs backtest, status label, hasil uji ML, daftar usulan.
- Karakter `<`, `>`, `&` di luar tag HTML harus ditulis sebagai `&lt;`, `&gt;`, `&amp;`.
