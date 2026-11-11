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
