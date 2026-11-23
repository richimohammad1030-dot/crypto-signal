# Prosedur riset · FX MAJOR

Instruksi untuk scheduled task **"Riset Bot FX"** (Minggu dini hari, 1×/minggu). Wajib baca dulu `riset/ATURAN_BERSAMA.md`
(bagian B & E) dan `riset/fx/STRATEGI.md`.

## 0. Aturan keras
- Aturan tetap pemilik di STRATEGI.md (07:00/23:00 WIB, struktur 3 bot saling menutup celah) tidak pernah diusulkan berubah.
- Jangan ubah file bot & mesin live: `fx_bot.py`, `forex_major/fx_live.py`, `forex_major/backtest.py`, `forex_major/riset_putaran*.py`,
  file bot lain, `fx_state.json`, `.github/`. Eksperimen ditulis di `riset/fx/eksperimen/` (boleh `import` dari `forex_major/`).
- Hanya tulis di `riset/fx/` dan `riset/laporan/fx/`. Branch `claude/riset-fx-YYYY-MM-DD`, commit, push → workflow
  `kirim-laporan-riset.yml` mengirim ringkasan `.txt` ke chat pribadi pemilik dan menyalin berkas ke main.
- Hasil riset = usulan. Tidak ada yang dipasang tanpa persetujuan pemilik. Maks 1 perubahan strategi/bulan.

## 1. Baca rutinitas harian (jangan diulang)
`riset/harian/fx.md`: replay (wajib IDENTIK), penyebab SL 7 hari + kesehatan, live vs bayangan. Jalankan ulang
`python riset/fx/harian_fx.py . 7` hanya bila GAGAL/BEDA atau lebih tua dari 36 jam.
Celah berulang di penyebab SL (≥ 3 kali kategori sama) → jadikan ide.

## 2. Data
- Dukascopy H1 2015-skrg: `forex_major/data/<PAIR>_h1_<tahun>.json.gz` (7 pair). Tahun berjalan: unduh ulang lewat
  workflow `fx-data.yml` bila perlu (atau `python forex_major/unduh_data.py 2026 <PAIR>` di Actions; Dukascopy diblokir dari sesi).
- Dukascopy M5 2020-2026 (4 pair): `forex_major/data_m5/` — validasi presisi kandidat final.
- Setra H1 (sejak 2025): `python forex_major/unduh_setra.py 1h` (FX_PAIRS untuk pair tambahan) — cek data terkunci.
- Spread: `riset_putaran6.py` memasang spread asli Exness (+0,2 pip). Jangan memakai spread lebih kecil.

## 3. Sesi
0. **SKILL dulu** (`riset/KURIKULUM_SKILL.md`: PROGRAM KILAT, PENERAPAN SKILL, bagian FX MAJOR). Kerjakan langkah skill aktif
   pertama di setiap sesi (boleh beberapa tahap), skrip `riset/fx/eksperimen/skill_snr*.py`, status di `riset/fx/SKILL.md`,
   bagian tetap "Skill" di ringkasan Telegram (`🎓 SKILL SNR: LULUS TAHAP n` / `📕 BELUM LULUS`).
1. Saringan cepat maks 10 ide/varian (satu skrip) pada IS 2015-2022 saja. Templat cepat (juara 3 bot direproduksi persis, ±3 dtk):
   `riset/fx/eksperimen/saringan_2026_11_22.py` (`juara()`, `gen_after()` untuk pemicu setelah SL/BE, `ystat()`); uji penuh: `uji_penuh_2026_11_22.py`.
2. 2-3 teratas → uji penuh: IS, OOS 2023-2026, Setra, per tahun, gabungan 3 bot (`fx_live.all_days` dengan juara diganti),
   M5 bila lolos. Minimal 1 ide = sumber edge baru (bukan tambalan SL/TP juara).
3. Gerbang: PF IS & OOS > 1,05 (lebih baik dari juara pada metrik yang diincar), Setra > 1,0, tidak menambah tahun minus,
   lalu `riset/signifikansi.py` (P_rasio ≥ 0,90) dan uji maju ≥ 6 minggu & ≥ 20 trade sebelum diusulkan.
4. Kandidat (P_rasio 0,50-0,90 arah konsisten) → tambahkan ke MENU `riset/fx/harian_fx.py` (bagian MENU saja).
5. Laporan `riset/laporan/fx/riset-YYYY-MM-DD.md` + ringkasan `.txt` (≤ 3500 karakter): tabel + kesimpulan, total ide diuji.
   Perbarui `riset/fx/ide.md` dan `riset/fx/log.md`.

## 4. Fokus prioritas (urut)
1. Threshold pemilik yang belum tercapai: ≥ 4 trade/mgg (kini 3,4), tanpa tahun minus (kini 10/12), > 10%/thn.
2. Bot ke-3 BALAS setelah SL yang benar-benar punya edge (pemilik ingin balas loss; varian tanpa edge = martingale, dilarang).
3. Celah berulang dari penyebab SL.
