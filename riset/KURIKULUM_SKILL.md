# Kurikulum skill bot (dibuat 11 Nov 2026, permintaan pemilik)

Tujuan: pengetahuan bot terus bertambah dan tidak terkunci pada strategi yang sudah diuji. "Belajar" = riset Jumat membangun
cara MESIN mengenali sebuah konsep pasar, lalu MEMBUKTIKAN dengan data bahwa konsep itu nyata dan berguna. Satu skill aktif
per bot; satu langkah per Jumat. Prioritas: **XAU** (chat ini). Crypto swing & intraday memakai kurikulum yang sama di chat
masing-masing (status mereka dicatat di log riset masing-masing).

## Aturan umum tiap skill
- **Tahap 0 · Definisi mesin**: tulis aturan pengenal yang pasti (tanpa penilaian subjektif, tanpa melihat masa depan).
- **Tahap 1 · PAHAM** (konsepnya nyata): perilaku harga di sekitar objek yang dikenali berbeda NYATA dari objek acak
  pembanding (lokasi/waktu acak dengan sebaran jarak yang sama). Syarat: P ≥ 0,90 (bootstrap blok bulanan) di 2004-2014 DAN
  2015-2026, dan kedua arah. Laporkan varian mana yang nyata dan mana yang tidak.
- **Tahap 2 · BISA MEMAKAI** (berguna untuk bot): skill dipakai sebagai filter, penempatan SL/keluar, atau strategi mandiri
  dalam jendela tetap 07:00-23:00 WIB; harus memperbaiki sistem live di walk-forward 2004-2026 (P ≥ 0,90) — naik edge/trade,
  turun DD, atau berkurang tahun minus — tanpa merusak kriteria pemilik.
- **Tahap 3 · LIVE**: bayangan ≥ 4 minggu, lalu usulan pasang (persetujuan pemilik + replay identik).
- **Notifikasi**: setiap tahap lulus ditulis di ringkasan Telegram riset Jumat sebagai
  `🎓 SKILL <nama>: LULUS TAHAP <n> (<PAHAM/BISA MEMAKAI/LIVE>)` + 2-3 kalimat apa yang dipelajari.
  Gagal 3 putaran berturut-turut di satu tahap → laporkan `📕 SKILL <nama>: BELUM LULUS` + apa yang dipelajari, lalu pemilik
  memilih: lanjut dengan definisi baru atau pindah skill.
- Semua hasil (termasuk yang gagal) dicatat di log & ide riset bot terkait; skrip di `riset/<bot>/eksperimen/skill_<nama>*.py`.

## PROGRAM KILAT (pemilik, 20 Nov 2026) — mengalahkan "satu langkah per Jumat" dan "pemilik memilih setelah 3 gagal"
Tujuan: skill cepat dikuasai lalu dipakai di bot live, agar banyak skill berikutnya bisa dipelajari.
1. **Skill dikerjakan PERTAMA di setiap sesi riset** (XAU, crypto, intraday 2 sesi/minggu PERMANEN — keputusan pemilik 26 Nov 2026; ATURAN_BERSAMA E.5) dan **boleh beberapa tahap
   dalam satu sesi**: tahap 1 menguji SEMUA jenis/varian sekaligus; jenis yang lulus langsung masuk tahap 2 di sesi yang sama.
2. **Tahap 1 PAHAM = perilaku beda nyata dari acak, KE ARAH MANA PUN** (lebih sering pantul ATAU lebih sering tembus /
   lanjut). Pelajaran lintas bot wajib dipakai: di crypto & intraday level PERIODE/SWING-D1 terbukti lebih sering DITEMBUS;
   XAU dan bot lain wajib menguji arah tembus juga, bukan hanya pantul.
3. **Tahap 2 lewat saringan cepat**: semua cara pakai (filter, SL/TP di level, prioritas, strategi mandiri) × varian disaring
   di periode pilih (ATURAN_BERSAMA E.2), 2 teratas ke walk-forward penuh. P ≥ 0,90 → LULUS; P 0,50-0,70 arah konsisten →
   `kandidat` dan **langsung masuk MENU bayangan** (dipantau rutinitas harian tiap hari).
4. **Batas waktu: 3 sesi per tahap** (± 1,5 minggu). Gagal 3 sesi → sekali definisi baru terbaik; bila tetap gagal → skill
   DITUTUP dengan status `📕 DIPELAJARI: tidak berguna untuk bot ini` (itu juga pengetahuan) dan **otomatis pindah ke skill
   berikutnya tanpa menunggu pemilik** (pemilik boleh membatalkan lewat chat).
5. **Tahap 3 LIVE**: lulus tahap 2 → masuk bayangan hari itu juga → setelah ≥ 4 minggu bayangan + replay IDENTIK, usulan pasang
   dikirim di ringkasan Telegram (pemilik boleh memutuskan lebih cepat setelah membaca bukti). Skill yang sedang di bayangan
   tidak menghalangi skill berikutnya dimulai.
6. **Target SNR**: setiap bot sudah LULUS tahap 2 (masuk bayangan) atau DITUTUP paling lambat **Jumat 4 Des 2026**.
   Langkah berikut per bot (20 Nov):
   - XAU: tahap 1 putaran 2 = supply-demand (segar, sentuhan pertama, konfluensi) DAN uji arah TEMBUS untuk semua jenis
     (swing D1/H4, PDH/PDL, PWH/PWL); jenis yang lulus → tahap 2 di sesi yang sama (filter KOMBO/MR/K6, SL di balik level,
     strategi tembus/pantul mandiri 07:00-21:00).
   - Crypto swing: tahap 1b sudah menjawab (tembusan tidak memberi info arah) → jangan ulang 1b; langsung tahap 2 di `_wf.py`:
     (ii) SL di balik SWING-D1/PERIODE vs SL 8 ATR, (iii) prioritas slot sinyal yang baru menembus PWH/PWL, (i) filter
     entry dekat level lawan.
   - Intraday: I-35 (filter modul B dekat level PERIODE, P_rasio 0,91 pasca-hoc / 0,68 WF) → status `kandidat`, masuk bayangan;
     tahap 2 putaran 2 = SWING-D1 dengan saringan semua cara pakai.
   - FX major (masuk 23 Nov): lihat bagian "FX MAJOR" di bawah; target SNR FX = Minggu 20 Des 2026.

## PENERAPAN SKILL KE BOT LIVE (pemilik, 23 Nov 2026) — berlaku semua bot
1. Skill yang LULUS tahap 1, 2 dan 3 **langsung diusulkan dipasang** sebagai tambahan pada strategi live (bot sekarang +
   skill). Karena mengubah strategi, **wajib persetujuan pemilik**; usulan di ringkasan Telegram memuat: cara pakai skill,
   hasil walk-forward, bayangan ≥ 4 minggu, replay IDENTIK, dan versi lama yang disimpan untuk kembali.
2. Setelah dipasang: bandingkan "bot + skill" vs "bot tanpa skill" (bayangan versi lama tetap jalan di MENU) tiap sesi riset,
   minimal 4 minggu / 20 trade, plus backtest penuh.
3. Bila hasilnya LEBIH BURUK: skill **tidak langsung dicabut**. Riset berikutnya mengoptimasi strategi DENGAN skill itu
   (menyesuaikan entry, SL/TP, filter atau jadwal strategi agar cocok dengan skill) — skill dianggap pengetahuan permanen
   yang tidak tergantikan oleh edge tunggal. Versi hasil optimasi tetap wajib lolos gerbang yang sama (walk-forward
   P ≥ 0,90, tanpa menambah tahun minus) dan persetujuan pemilik.
4. Pengaman: bila setelah 3 sesi optimasi tetap lebih buruk dan drawdown live melewati batas bot, usulkan kembali ke versi lama
   sementara (keputusan pemilik) sambil optimasi berlanjut di bayangan.

## Skill 1 · SNR (support & resistance) — AKTIF untuk XAU
Pilihan pemilik (11 Nov): semua jenis diuji; level dari H4 & D1, dipakai untuk keputusan di H1.
- **Tahap 0 · Pengenal (4 jenis):**
  a) **Swing level**: pivot fraktal (n = 2/3/5 candle tiap sisi) di H4 & D1; level berdekatan (≤ 0,25 ATR D1) digabung jadi
     satu zona; kekuatan = jumlah sentuhan, umur, timeframe.
  b) **High/low periode sebelumnya**: high/low hari (blok 07:00-07:00 WIB) & minggu sebelumnya.
  c) **Angka bulat**: kelipatan 10 / 25 / 50 / 100 USD.
  d) **Zona supply-demand**: candle dasar (1-3 candle kecil) sebelum gerak impulsif ≥ 2 ATR; zona = range dasar; segar
     (belum disentuh) vs sudah disentuh.
- **Tahap 1 · Uji "paham"**: peristiwa = candle H1 menyentuh zona (≤ 0,1 ATR) datang dari luar zona. Hasil dalam 1-12 candle:
  MEMANTUL (bergerak ≥ 1 ATR menjauh tanpa menembus ≥ 0,5 ATR) vs TEMBUS. Bandingkan dengan level acak pembanding. Laporkan:
  peluang pantul, lift vs acak, per jenis/timeframe/kekuatan/arah/periode, dan apakah tembusan zona kuat diikuti lanjutan.
- **Tahap 2 · Uji "bisa memakai"** (minimal 3 cara): (i) filter: lewati/kurangi entry KOMBO/MR/K6 bila ada zona lawan kuat
  dalam ≤ 1 ATR; (ii) SL di balik zona terdekat (vs SL ATR); (iii) strategi mandiri pantul/tembus zona di jam 07:00-21:00.
- **Tahap 3**: bayangan & usulan pasang.

## FX MAJOR · Skill 1 SNR (mulai 23 Nov 2026)
Status di `riset/fx/SKILL.md`. Data: Dukascopy H1 2015-2026 7 pair (periode uji "paham" = 2015-2020 DAN 2021-2026), level dari
H4 (dibentuk dari H1) & D1, keputusan H1, hari 07:00-07:00 WIB. Angka bulat per pair: 00/50 pip (JPY: 0,50/1,00).
Pelajaran bot lain WAJIB dipakai (hemat sesi): pembanding acak yang ADIL (candle acak juga menyentuh level nyata lain — XAU
23 Nov), uji arah pantul DAN tembus, konfluensi ≥ 2/≥ 3 jenis, hasil per pair & gabungan.
Catatan: UTAMA & SUSULAN FX sudah berbasis level minggu lalu (PWH/PWL) — tahap 2 menguji SNR sebagai filter/SL/TP pada level
itu (mis. zona lawan di jalur TP, konfluensi level minggu lalu + swing D1, SL di balik zona), bukan hanya strategi mandiri.
FX 1 sesi/minggu (Minggu) → boleh beberapa tahap per sesi; batas 3 sesi per tahap tetap berlaku.

## Antrian skill berikutnya (urutan usulan, pemilik boleh mengubah)
2. Struktur pasar (higher high/low, break of structure, change of character)
3. Price action di level (pin bar, engulfing, inside bar tepat di zona SNR)
4. Sesi & likuiditas (range Asia, buka London/NY, sapuan likuiditas di atas/bawah high-low)
5. Volume & volume profile (volume tick Dukascopy)
6. Kalender news (perilaku sebelum/sesudah event USD berdampak tinggi)
7. Antar-pasar (indeks dolar, perak, imbal hasil — bila datanya bisa diperoleh)
8. Konfluensi multi-timeframe (gabungan skill yang sudah lulus)

## Status (dicatat di folder riset masing-masing bot; workflow laporan hanya menyalin riset/<bot>/ ke main)
| Bot | File status | Keadaan 11 Nov 2026 |
|---|---|---|
| XAU | `riset/xau/SKILL.md` | skill 1 SNR, tahap 0 mulai Jumat 13 Nov |
| Crypto swing | `riset/crypto/KURIKULUM.md` | skill 1 SNR (lihat file) |
| Intraday | `riset/intraday/PROSEDUR.md` bagian SKILL | skill 1 SNR: tahap 1 PAHAM lulus untuk jenis PERIODE (11 Nov) |
| FX major | `riset/fx/SKILL.md` | skill 1 SNR, tahap 0+1 mulai sesi Minggu 29 Nov 2026 |

## SNR = MILESTONE T10 (pemilik, 26 Nov 2026) — mengalahkan poin 4 & 6 PROGRAM KILAT untuk skill SNR
- Kriteria berhasil: SNR lulus **tahap 2 BISA MEMAKAI di keempat bot (XAU, FX, crypto swing, intraday) paling lambat 31 Des 2026**;
  tahap 3 (bayangan ≥ 4 minggu → live) dikerjakan awal 2027.
- SNR **tidak ditutup** sebelum 31 Des. Gagal 3 sesi = wajib DEFINISI/CARA PAKAI BARU (bukan berhenti): SL/TP di level, filter
  arah, prioritas slot, konfluensi dengan skill lain, level timeframe lain, jarak ke level sebagai bobot risiko, dst. Tiap
  definisi baru ditulis sebagai keluarga di `riset/<bot>/massal/keluarga_usulan.py` agar ratusan variannya diuji malam itu.
- Gerbang tahap 2 TIDAK dilonggarkan (P ≥ 0,90 walk-forward + aturan anti-optimis ATURAN_BERSAMA G). Kalau sampai 31 Des tetap
  gagal di satu bot, laporkan jujur cara pakai terbaik + P-nya; jangan memaksakan lolos.
- Skill 2 (struktur pasar) boleh mulai paralel hanya bila tidak mengurangi sesi SNR.

## KURIKULUM SKILL TEKNIKAL + ATURAN PERCEPATAN (pemilik, 26 Nov 2026, revisi) — mengalahkan "Antrian skill berikutnya" di atas
Inti (pemilik): skill = kemampuan ANALISA TEKNIKAL yang mempertajam strategi yang ada — entry lebih presisi, SL lebih jarang,
TP lebih tepat. Bukan strategi baru. Daftar 13 skill & target waktu di `riset/kurikulum.json`: SNR → struktur pasar
(BOS/CHoCH, SBR/RBS) → price action konfirmasi → Fibonacci → supply-demand/order block/FVG → trendline & channel → moving
average dinamis → divergence & momentum → volume (profile, VWAP, OBV) → pola chart → likuiditas & sesi → Elliott wave →
konfluensi multi-timeframe. Tiap skill punya `mencegah` (kesalahan/penyebab SL yang dihindari) dan `menambah` (presisi).
**Tahap 2 wajib diukur terhadap penyebab SL juara**: berapa SL yang akan dicegah skill itu vs berapa trade menang yang ikut
hilang (ATURAN_BERSAMA G — mitigasi SL), plus efek pada presisi entry (MAE, jarak SL) dan TP (MFE yang tertangkap).
1. **Target ketat per skill** (hari kalender sejak mulai): tahap 0+1 PAHAM ≤ 4 hari · tahap 2 BISA MEMAKAI ≤ 10-14 hari
   (`target_hari` tiap skill). Total 13 skill ≤ ±5,5 bulan bila tepat target (lebih cepat bila lulus cepat). Tahap 3 (bayangan ≥ 28 hari → live) berjalan
   PARALEL dan tidak menahan skill berikutnya. Pengecualian: SNR (T10) batas tahap 2 = 31 Des 2026.
2. **Selesai cepat = langsung lanjut**: begitu skill lulus tahap 2 (masuk bayangan) — atau bila SNR bot itu sudah sampai
   tahap 3 sebelum akhir tahun — sesi yang sama/berikutnya LANGSUNG memulai skill berikutnya di `kurikulum.json`. Tidak menunggu
   batas waktu, tidak menunggu bot lain. Tiap bot maju dengan kecepatannya sendiri; skill bisa dipelajari tidak urut bila datanya
   belum ada (mis. volume FX), catat alasannya.
3. **Lewat batas**: skill yang melewati `target_hari` = status TERLAMBAT (merah di dashboard). Wajib definisi/cara pakai baru
   (keluarga di `riset/<bot>/massal/keluarga_usulan.py`) dengan tambahan maks 7 hari; tetap gagal → `ditutup` dengan catatan
   "dipelajari: tidak berguna untuk bot ini" dan pindah ke skill berikutnya. SNR tidak ditutup sebelum 31 Des.
4. **Penanda kecepatan** (dicatat otomatis dashboard dari tanggal di `status.json` → `kurikulum`): kecepatan = target_hari ÷
   hari aktual sampai lulus tahap 2. ≥ 2× = "kilat", ≥ 1,25× = "cepat", ≥ 1× = "tepat waktu", < 1× = "terlambat".
   Bot/skill yang kilat dicatat di laporan sebagai bahan eksplorasi: apa yang membuatnya cepat (data, mesin, sifat pasar).
5. **Tiap sesi WAJIB memperbarui** `riset/<bot>/status.json` → `kurikulum[i]`: `status` (belum/belajar/bayangan/live/ditutup),
   `tahap`, tanggal `mulai`, `t1` (lulus paham), `t2` (lulus bisa memakai), `t3` (live), `catatan` singkat. Juga `skill` (skill
   aktif) agar kartu skill dashboard ikut berubah.
6. Gerbang tiap tahap tetap sama ketat (P ≥ 0,90 + ATURAN_BERSAMA G). Cepat tidak boleh berarti longgar.
