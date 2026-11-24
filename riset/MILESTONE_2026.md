# MILESTONE 31 Des 2026 — arah kerja riset semua bot (pemilik, 24 Nov 2026)

Setiap sesi riset WAJIB membuka file ini, memilih pekerjaan yang paling memperkecil celah ke target, dan menutup sesi
dengan menambah satu baris di `riset/<bot>/RAPOR.md` (file di folder bot ikut tersalin ke main; file ini tidak). Riset yang tidak menyentuh celah target = prioritas rendah.

## Target (per bot, pada risiko live, data penuh tiap bot + walk-forward)
| # | Syarat | Ukuran |
|---|---|---|
| T1 | Tidak ada tahun minus | Tiap tahun kalender ≥ 0 (minimal impas) setelah biaya |
| T2 | Adaptif terhadap edge | Lolos walk-forward (pilihan strategi/parameter bergulir) DAN punya monitor edge: risiko otomatis turun bila PF 12 bulan bergulir < 1 (diusulkan, persetujuan pemilik) |
| T3 | Profit factor | PF > 1,1 seluruh periode, juga di OOS dan Setra/data baru |
| T4 | Win rate | ≥ 40% |
| T5 | Pertumbuhan | Rata-rata ≥ 10%/thn per bot (tanpa compounding, % ekuitas pada risiko live) |
| T6 | Drawdown | DD ekuitas maks ≤ 20% |
| T7 | Kalah beruntun | ≤ 10 trade berturut-turut — berlaku juga untuk crypto (keputusan pemilik 24 Nov) |
| T8 | Frekuensi | XAU ≥ 3 trade/mgg · FX ≥ 3/mgg · crypto & intraday sesuai aturan bot |
| T9 | Lolos data baru | Hasil OOS & Setra tidak jauh di bawah backtest (P_rasio, ATURAN_BERSAMA) |

"Mencapai milestone" pada 31 Des = tiap bot punya versi (juara atau penantang) yang lolos T1-T9 di backtest + walk-forward
dan sudah berjalan di bayangan. Pemasangan live tetap lewat persetujuan pemilik (uji maju 6 minggu boleh dipersingkat oleh
pemilik setelah membaca bukti).

## Rapor awal (24 Nov 2026, dari STRATEGI/log masing-masing bot)
| Bot | T1 tahun minus | T3 PF | T4 WR | T5 %/thn | T6 DD | T7 kalah beruntun | Celah utama |
|---|---|---|---|---|---|---|---|
| XAU (0,5%) | ❌ 6/22 (2015-26: 2/12) | ✅ 1,16 | ✅ 46% | ❌ ±8,5% | ❌ 23,5% | ❌ 15 | tahun minus, DD, beruntun, pertumbuhan |
| Crypto swing (1%) | ✅ 0 | ✅ 1,85 (2025: 1,23) | ✅ 40,8% (tipis) | ✅ ±80% | ✅ 17,5% | ❌ 25 | kalah beruntun; edge melemah sejak 2025 |
| Intraday (1%) | ✅ 0 (2020-26) | ✅ 1,28 (2024+: 1,19) | ✅ 63% | ✅ ±39% | ✅ 15,6% | ✅ 9 | hampir lulus; T2 monitor edge |
| FX major (0,75%) | ❌ 2/12 | ✅ 1,27 (OOS 1,17) | ✅ 42% | ✅ ±14% | ❌ ±27% (36R) | ? diukur | tahun minus, DD; baru live 20 Nov |
T2 (monitor edge) belum ada di bot mana pun. T8/T9 dicek per kandidat.

**Saringan massal pertama (24 Nov, lokal):** XAU 1.351 varian · FX 231 · intraday 161 · crypto 155.
- XAU: monitor PF per strategi (365 hari, < 1,0) memotong DD 23,5% → 13% dan tahun minus IS 6 → 3; rasio 0,26 → 0,50
  (= ±10%/thn pada DD 20% bila risiko ±0,8%). Belum ada varian XAU tanpa tahun minus → celah utama Des.
- FX: monitor PF per pair → IS 0 tahun minus & 7/7 target, tetapi OOS 2023-26 masih 1 tahun minus & DD 23%.
- Intraday: juara sudah 7/7 di IS & OOS; tinggal T2 (monitor edge di bot live).
- Crypto: semua lolos kecuali T7 (kalah beruntun 25; IS & OOS). Catatan jujur: sistem tren WR ±42% dengan ±350 trade/thn
  hampir pasti punya runtun 10+ kalah; T7 ≤ 10 berarti mengubah karakter strategi — perlu keputusan pemilik.

## Rencana mingguan
| Minggu | Pekerjaan | Hasil yang ditagih |
|---|---|---|
| 24-30 Nov | Mesin saringan massal (GitHub Actions malam, tanpa token) XAU dulu, lalu crypto & intraday; bank ide; rapor otomatis | Run malam pertama XAU; ≥ 200 varian/malam |
| 1-7 Des | Saringan massal 4 bot jalan tiap malam; SNR target 4 Des; FX SNR tahap 0-1 | Tiap bot ≥ 1 penantang di bayangan |
| 8-14 Des | Serang celah: XAU tahun minus/DD/beruntun, FX tahun minus/DD, crypto beruntun; desain monitor edge (T2) | Kandidat XAU & FX yang lolos T1 di backtest |
| 15-21 Des | Uji penuh + walk-forward kandidat; SNR FX 20 Des | Tiap bot punya versi lolos T1-T9 (backtest + WF) |
| 22-31 Des | Usulan lengkap ke pemilik (bukti + rapor) | Milestone: semua bot lolos di backtest+WF dan di bayangan |

## Rapor mingguan
Di `riset/xau/RAPOR.md`, `riset/crypto/RAPOR.md`, `riset/intraday/RAPOR.md`, `riset/fx/RAPOR.md`; dicetak juga sebagai bagian
tetap "Milestone" di ringkasan Telegram tiap sesi (✅/❌ per T1-T9 + celah yang dikerjakan).
