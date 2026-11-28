# Jurnal riset · FX MAJOR

## 20 Nov 2026 — riset awal & pemasangan (sesi bersama pemilik)
- Data: Dukascopy H1 2015-2026 (7 pair), M5 2020-2026 (4 pair), Setra H1 2025-2026. Spread asli Exness Standard Cent.
- Putaran 1: 8 kandidat klasik semua minus (spread konservatif). Putaran 2: N3 breakout level minggu lalu lolos.
- Putaran 3-4: level lain merusak edge; Senin dilewati memperbaiki; 7 pair (pilihan pemilik) → 3,1/mgg.
- Putaran 5-6: PENGISI & BALAS gagal; susulan gaya XAU (RSI2) gagal 0/192; SUSULAN "pasang ulang level" lolos 18/18.
- Putaran 7: optimasi bersama UTAMA+SUSULAN (11/12 thn), bot ke-3 LANJUT setelah TP lolos 2/108.
- Dipasang (uji maju ke chat pribadi): UTAMA + SUSULAN + LANJUT, risiko 0,75%. Belum mencapai: ≥ 4/mgg, tanpa tahun minus.

## 22 Nov 2026 — riset mingguan #1 (riset biasa)
- Rutinitas harian 21 Nov dibaca: replay IDENTIK (0 trade), tanpa SL. Juara direproduksi persis di skrip eksperimen (3 dtk/run).
- Saringan 10 ide (IS 2015-22): 4 sumber edge baru (level bulan lalu, range minggu berjalan, akhir bulan fix, momentum USD) PF 0,82-1,01;
  semua penambah frekuensi merusak edge. Uji penuh 3 teratas (13 tembus ulang, 14 pasang ulang BE, 15 BALAS palsu): semua gagal
  (OOS/Setra/M5). Data terkunci Setra sudah dipakai untuk ide 13, 14, 15.
- BALAS setelah SL: 3 definisi baru tanpa edge → tidak diusulkan. Tidak ada kandidat baru; MENU tetap. Total ide ±1.410.


## 27 Nov 2026 — sesi dorong bersama pemilik
- SNR tahap 0+1 LULUS (dimajukan). Tahap 2 putaran 1: bobot SUPDEM 0,5× kandidat (P 0,80-0,84).
- Edge baru: SUSULAN dilewati/0,5× bila range 5 hari > kuantil 80% WF (P 0,92; + SNR 0,95). OOS terkontaminasi (fitur dipilih setelah melihat 2023). Stres +0,05R: PF OOS juara 1,05.
- Bank massal: keluarga_usulan.py F008-F011 (146 varian, 91 penantang; teratas masih 2023 minus & runtun 13).

## 29 Nov 2026 — riset mingguan + REVIEW BULANAN November
- **Temuan data (blocker):** feed Setra FX tertinggal 12-20 jam dari harga nyata (per pair; korelasi 0,99-1,00 pada lag; jangkar ECB:
  Dukascopy 2,8 pip vs Setra 16 pip, Setra+15 jam 3,2 pip). Senin Setra 5-12 candle. Replay BEDA (4 live vs 9 replay, data Setra
  berubah antar unduhan). Trade live NZDUSD −3,32R = artefak. Validasi Setra 2025-26 (T9) batal. XAU Setra juga lag 18 jam (info).
- Mitigasi SL backtest: 749 SL = palsu ≤2 jam 34% · sempat untung lalu balik 32% · perlahan 30% · SL lalu TP 5%; 2 kategori teratas
  didominasi SUSULAN. F014 (SUSULAN s/d 22:00) kandidat → MENU; F013 (BE SUSULAN) ditolak.
- SNR tahap 2 put.2 (konfluensi di level) & put.3 (jarak zona, F012) gagal → sesi berikut definisi baru (sesi 3/3).
- Edge baru: nilai relatif pairs (F015) gagal. Saringan massal dijalankan lokal: 188 varian, 18 penantang (16 F012, 1 F014, 1 F013).
