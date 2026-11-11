# Prosedur riset · XAU

Instruksi untuk scheduled task **"Riset Bot XAU"** (setiap Jumat 00:18 WIB).
Tujuan: menemukan perbaikan bot XAU intraday multi-strategi yang terbukti dengan data, lalu **mengusulkannya** ke pemilik.
Riset tidak pernah mengubah bot live. Perubahan dipasang hanya setelah pemilik setuju di chat.
Riset crypto & intraday crypto dikerjakan task terpisah. Jangan menyentuh berkas mereka.

**Juara sejak 2 Nov 2026 = multi-strategi** (`riset/xau/STRATEGI.md`, ide #34). Maksimal 1 posisi/hari, keputusan 07:00 WIB:
mean reversion RSI(2) H1 (≤ 43,76 BUY / ≥ 85 SELL market sejak 6 Nov 2026 [ide #40, dulu 71,22]; bila tren harian turun [close 07:00 ≤ SMA100]
cermin: SELL ≥ 70 / BUY ≤ 15 [hibrida #42b]; SL 3 ATR, tanpa TP) diprioritaskan; selain itu breakout K6
(1 stop order searah tren EMA200 H1 + batas batal, SL 1,5 ATR, TP 4R). Sejak 6 Nov 2026 + **susulan** (ide #37): hari K6 dilewati
→ RSI(2) di jam keputusan pertama 09:00-21:00 WIB (≤ 25,41 / ≥ 77,10 market, SL 3 ATR, TP 1R). Semua ditutup 23:00 WIB. Risiko 0,5%.
Pantau bayangan "Tanpa susulan" vs BASELINE (susulan lebih buruk di Setra saat dipasang, n 46).
Edge XAU intraday bergantung rezim (mean reversion kuat saat emas tenang, tren kuat saat volatil) dan tipis (PF ±1,07).
Jangan memakai kesimpulan riset crypto untuk XAU tanpa diuji ulang dengan data XAU.

**Wajib baca dulu `riset/ATURAN_BERSAMA.md`** (sumber ide, signifikansi, uji maju) dan `riset/xau/STRATEGI.md`.

## 0. Aturan keras
- **Aturan tetap pemilik: sinyal dikirim 07:00 WIB dan semua order/posisi ditutup 23:00 WIB. Jangan pernah mengusulkan
  perubahan bagian ini** (jam pasang, jam tutup, hold multi-hari). Yang boleh diteliti: arah, cara masuk, SL/TP, filter,
  strategi tambahan dalam menu, aturan pemilihan strategi, risiko.
- Syarat pemilik untuk usulan: win rate ≥ 40% (boleh ≥ 35% bila RR ≥ 1,5), PF > 1, ≥ 3 trade/minggu, menang/kalah beruntun
  tidak timpang, mayoritas tahun untung, karakter intraday.
- **Jangan ubah** file bot: `signal_bot.py`, `gold_bot.py`, `templates.py`, `gold_templates.py`, `commands.py`,
  `jurnal.py`, `kesehatan.py`, `baseline.json`, file state (`*.json` di root), dan `.github/`.
- Hanya tulis di `riset/xau/` dan `riset/laporan/xau/`.
- Kerjakan di branch baru `claude/riset-xau-YYYY-MM-DD` (tanggal WIB hari ini), commit, lalu push branch itu.
  Workflow `kirim-laporan-riset.yml` otomatis mengirim ringkasan ke chat pribadi pemilik dan menyalin berkas riset ke main.
- Jangan membuat scheduled task, routine, atau pengingat baru.

## 1. Persiapan data & cek kesetaraan (±5-20 menit)
```bash
pip install -q --break-system-packages numpy pandas scipy
python3 riset/unduh_xau.py /tmp/data                       # Setra (data bot), sejak Feb 2025
python3 riset/unduh_xau_panjang.py /tmp/data 2015         # Dukascopy 2015-skrg (bibit di riset/data/, hanya bulan baru diunduh)
python3 riset/replay_xau.py . /tmp/data/xau.json /tmp/data/xau_panjang.json   # wajib IDENTIK; jika BEDA laporkan sebagai temuan utama
python3 riset/xau/bayangan.py . /tmp/data/xau.json /tmp/data/xau_panjang.json # uji maju: live vs menu strategi sejak 2 Nov 2026
```
Mesin riset: `riset/xau/eksperimen/audit_mesin.py` (OCO/K6, fitur), `strat_mesin.py` (strategi market/limit/stop dalam jendela
07:00-23:00), `multi_mesin.py` (juara multi-strategi; konstanta dibaca dari `gold_bot.py`). Data sambung untuk konfirmasi:
`audit_mesin.sambung(dukascopy, setra)`. Biaya 0,40 USD/trade (+ stress slip 0,20 USD).
**Candle ambigu**: ±6% hari candle H1 menyentuh dua level sekaligus; bot memilih BUY. Untuk varian OCO pakai
`ambigu=dict` dari `eksperimen/ambigu_m1_2022_2026.json` (+ `audit_m1.py` untuk hari baru); strat_mesin memakai hasil terburuk.
Jika unduhan gagal, tetap buat laporan yang menjelaskan kegagalannya.

## 2. Tentukan mode
- Jika **Jumat berikutnya sudah masuk bulan baru** (hari ini Jumat terakhir bulan ini) → **REVIEW BULANAN** (langkah 3 + 4).
- Selain itu → **RISET MINGGUAN** (langkah 3 saja).

## 3. Riset mingguan
**SIKLUS JUMAT (pemilik, 11 Nov 2026) — urutan wajib, laporan dengan bagian tetap:**
1. **Kesehatan minggu ini** (bukan menilai strategi; ±5 trade terlalu sedikit): sinyal live = replay data final? data Setra
   macet/cadangan dipakai? sinyal terlambat? selisih live vs backtest minggu itu.
2. **Penyebab SL minggu ini:** `python3 riset/xau/sebab_sl.py . /tmp/data/xau.json 7 /tmp/data/xau_2004.json` (perbarui
   VERSI_SEJAK di skrip tiap aturan bot berubah). Kategori: NEWS (event USD high-impact 60 mnt sebelum masuk s.d. SL) = aman ·
   LONJAKAN (candle SL ≥ 2,5 ATR tanpa news) = dicatat · DATA (live ≠ replay) = WAJIB dianalisa sebagai bug · CELAH (salah
   analisa) = WAJIB dianalisa: komponen, arah vs tren, ATR, dan bandingkan dengan porsi SL historis komponen di kondisi sama
   (normal atau tidak). CELAH berulang (≥ 2 SL komponen & kondisi sama dalam 4 minggu, di atas porsi historis) → buka ide baru.
3. **Akumulasi live vs bayangan** (bayangan.py) — penilaian strategi hanya dari akumulasi ≥ 4-8 minggu.
4. **Satu putaran perbaikan** (arah utama di bawah) dengan walk-forward 2004-2026.
4b. **Satu langkah KURIKULUM SKILL** (`riset/KURIKULUM_SKILL.md`; XAU: skill 1 SNR). Kerjakan tahap berikutnya dari skill
   aktif, perbarui status di `riset/xau/SKILL.md` (bukan file kurikulum bersama), dan tulis di ringkasan `🎓 SKILL ...: LULUS TAHAP n` bila lulus (atau progres).
5. **Gerbang pasang:** perbaikan teknis (bug/data/pesan) boleh diusulkan dipasang minggu itu juga. Perubahan STRATEGI wajib
   P ≥ 0,90 walk-forward + replay IDENTIK + bayangan ≥ 4 minggu; maksimal 1 perubahan strategi per bulan.
6. **Ringkasan Telegram** berbagian: Kesehatan · Penyebab SL · Live vs bayangan · Riset · Skill · Usulan (butuh "pasang"/"tidak" pemilik).
**PROGRAM UTAMA (pemilik, 6 Nov 2026): TAMBAL-CELAH sampai TIDAK ADA TAHUN MINUS, baru setelah itu optimasi besar untung.**
Tiap Jumat satu putaran: (a) bedah celah sistem dasar (`eksperimen/celah_ma200.py`: per tahun × komponen, kondisi pasar, bulan
terburuk); (b) cari 1-2 ide BARU dari luar (indikator/strategi/literatur) yang khusus menutup celah terbesar; (c) uji dengan
`eksperimen/tambal1.py` sebagai pola; (d) metrik utama = jumlah tahun minus & tahun terburuk (bukan total R), tetangga parameter
harus ikut bagus; (e) penambal yang lolos dikonfirmasi di data yang belum dilihat: XAU 2004-2014 (SUDAH di repo:
`riset/data/xau_dukascopy_h1_2004_2014.json.gz`; gabung: `python3 riset/gabung_xau_lama.py /tmp/data/xau_sambung.json
/tmp/data/xau_2004.json`, tanpa unduh) dan perak.

**PEMBAGIAN DATA 2004-2026 (pemilik, 6 Nov 2026):**
- LANGKAH 1 (sekali, Jumat 13 Nov 2026): uji APA ADANYA (tanpa ubah parameter) bot live hibrida MA100, hibrida MA200, #40
  (tanpa hibrida), MR SELL 71,22, dan penambal #50 di **2004-2014** (data yang belum pernah dilihat; 2015-2026 sudah
  "terkontaminasi" karena dipakai merancang). Tabel per tahun 2004-2014 + tahun minus + terburuk. Ini vonis paling jujur;
  catat di log bahwa 2004-2014 sudah dipakai setelah langkah ini.
- LANGKAH 2 (seterusnya, semua ide baru): **walk-forward berlabuh** — pilih parameter hanya dari 2004..Y, uji Y+1..Y+2,
  geser 2 tahun: pilih ≤2010→uji 2011-12, ≤2012→2013-14, ≤2014→2015-16, ≤2016→2017-18, ≤2018→2019-20, ≤2020→2021-22,
  ≤2022→2023-24, ≤2024→2025-26. Laporkan tabel per tahun 2011-2026 yang SEMUANYA hasil uji, jumlah tahun minus, tahun
  terburuk, dan P gabungan semua jendela uji vs sistem dasar (≥ 0,90). Pemilihan di tiap jendela memakai aturan yang sama
  (skor = tahun minus paling sedikit, lalu R/thn; tetangga parameter harus ikut bagus).
- Pemeriksaan tambahan: periode Setra Feb 2025-skrg (data broker) dan perak. Uji maju bot live = hakim terakhir.
- Catatan teknis: indikator lambat (MA200 hari dll.) butuh pemanasan — mulai hitung trade setelah indikator terbentuk.
 Catat putaran & celah tersisa di log.md. Sistem dasar sekarang: bot live hibrida MA100 (vonis 2005-2014: 7/22 tahun minus, lihat log 10 Nov); kandidat terkuat: #58 V2
(kombinasi RSI2+tren+CLV); penambal #50. ARAH UTAMA SEJAK 10 Nov 2026 (log "Tambal-celah putaran 2"): menambal per tahun hanya memindahkan rugi; peluang tahun minus
dengan edge +0,071R/trade × 239 trade/thn ≈ 19% (±4 dari 22 tahun walau stabil). Fokus = NAIKKAN EDGE PER TRADE / turunkan
variansi tahunan: (1) buang/perkecil komponen ber-edge ±0 (mis. susulan BUY -17R/22 thn), (2) perbesar porsi komponen ber-edge
tinggi (kombinasi #58), (3) ukuran posisi per komponen sebanding edge-nya, (4) cari komponen baru ber-edge ≥ +0,15R/trade.
Ukuran sukses: rata R/trade, simpangan R tahunan, jumlah tahun minus 2005-2026, P vs live.
1. **Uji maju** (selalu): tulis hasil `bayangan.py` (trade, win, total R per strategi menu vs live) dan selisih live vs baseline.
2. Uji 2 ide: ide teratas berstatus `antri` dari `riset/xau/ide.md`, **ditambah 1 ide baru** (ATURAN_BERSAMA bagian A; literatur
   = nilai tambah). Ide yang sudah `gagal` tidak diuji ulang tanpa data baru yang relevan.
3. Skrip di `riset/xau/eksperimen/<nama-ide>.py`. Pembagian data tetap: **pilih 2015-2021**, **uji 2022 - Jan 2025** (Dukascopy),
   **konfirmasi Feb 2025 - skrg** (Setra, data sambung). Parameter hanya boleh dipilih di periode pilih; uji tetangga parameter.
4. Bandingkan dengan juara (`multi_mesin.baseline`), bersih biaya, per periode dan 12 tahun: trade/minggu, win rate, RR, PF,
   R/thn, drawdown (R & % pada 0,5%), menang/kalah beruntun, tahun untung, tanpa 2% trade terbaik, slip +0,20 USD.
5. Keputusan: **LOLOS tahap 1** bila memenuhi syarat pemilik di periode pilih, tetangga ikut lolos, dan PF > 1 di uji & Setra;
   lalu **signifikansi** `signifikansi.banding` vs juara di periode uji (P_rasio ≥ 0,90; 0,70-0,90 `perlu-data`), lalu **uji maju**
   ≥ 6 minggu & ≥ 20 trade (tambahkan ke menu `bayangan.py`) sebelum diusulkan. Selain itu **GAGAL** (catat alasannya).
6. Catat di `riset/xau/log.md` dan perbarui `riset/xau/ide.md` (penomoran lanjut dari nomor tertinggi XAU maupun crypto).

## 4. Review bulanan (hanya Jumat terakhir bulan ini)
Tambahan selain langkah 3:
1. Statistik juara terbaru per periode + per strategi (MR vs K6), per kuartal, alasan keluar (SL / TP / tutup 23:00).
2. Live (`gold_state.json` field `hist`, label strategi di indeks 7; `jurnal/xau-*.json`) vs backtest sejak `LIVE_START` XAU
   (`kesehatan.py`). Selisih besar = masalah eksekusi atau data.
3. Ringkas kandidat penantang & usulan yang menunggu persetujuan pemilik (apa yang diubah, bukti tiap periode, dampak profit/DD).

## 5. Keluaran
- `riset/laporan/xau/riset-YYYY-MM-DD.md` - laporan lengkap (angka, tabel, kesimpulan).
- `riset/laporan/xau/riset-YYYY-MM-DD.txt` - ringkasan untuk Telegram, **maks 3.500 karakter**, HTML Telegram sederhana
  (hanya `<b>` dan `<pre>`), bahasa Indonesia, gaya sama dengan bot: judul tebal `RISET XAU` atau `REVIEW BULANAN XAU`,
  tanggal, garis `────────────────────`, judul bagian tebal dengan garis di bawahnya, tanpa emoji.
  Baris di dalam `<pre>` maksimal ±38 karakter.
  Isi: mode, uji maju (live vs menu), ide yang diuji dan keputusannya, kandidat penantang, dan untuk review bulanan:
  ringkasan live vs backtest, daftar usulan.
- Karakter `<`, `>`, `&` di luar tag HTML harus ditulis sebagai `&lt;`, `&gt;`, `&amp;`.
