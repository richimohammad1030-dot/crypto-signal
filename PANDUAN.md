# Panduan Bot Sinyal Crypto Futures (gratis, tanpa VPS, tanpa TradingView Premium)

Bot ini berjalan otomatis di **GitHub Actions** setiap 4 jam, membaca data harga publik, lalu mengirim
instruksi ke **Telegram** Anda. Bot **tidak** punya akses ke akun exchange; Anda yang memasang order.

## Isi folder
| File | Fungsi |
|---|---|
| `signal_bot.py` | Mesin strategi + pengirim pesan Telegram |
| `.github/workflows/signal.yml` | Jadwal otomatis (03, 07, 11, 15, 19, 23 WIB) |
| `state.json` | Dibuat otomatis: mencatat order & posisi yang sedang berjalan |

---

## Langkah 1 — Buat bot Telegram (±3 menit)
1. Buka Telegram, cari **@BotFather**, kirim `/newbot`, ikuti instruksinya.
2. Simpan **token** yang diberikan (contoh: `123456789:AAE...`). Jangan bagikan ke siapa pun.
3. Buka chat dengan bot baru Anda, kirim pesan apa saja (misalnya `halo`).
4. Di browser buka: `https://api.telegram.org/bot<TOKEN>/getUpdates` (ganti `<TOKEN>`).
   Cari `"chat":{"id": ...}` — angka itu adalah **chat id** Anda.

## Langkah 2 — Buat repository GitHub (±5 menit)
1. Daftar/login di github.com.
2. Klik **New repository** → beri nama, misalnya `crypto-signal` → pilih **Private** → **Create repository**.
3. Klik **uploading an existing file** → unggah `signal_bot.py` dan `PANDUAN.md` → **Commit changes**.
4. Klik **Add file → Create new file**, ketik nama file persis: `.github/workflows/signal.yml`
   lalu salin-tempel seluruh isi file `signal.yml` dari folder ini → **Commit changes**.
   (Folder berawalan titik sering tidak ikut saat upload biasa, jadi dibuat manual seperti ini.)

## Langkah 3 — Masukkan rahasia & pengaturan
Di repository: **Settings → Secrets and variables → Actions**
- Tab **Secrets** → **New repository secret**:
  - `TELEGRAM_TOKEN` = token dari BotFather
  - `TELEGRAM_CHAT_ID` = chat id Anda
- Tab **Variables** → **New repository variable** (opsional, untuk menghitung ukuran posisi):
  - `RISK_PCT` = risiko per trade dalam persen, misalnya `0.67` (default) atau `0.3` untuk lebih aman
  - `MODAL_USDT` = modal futures Anda dalam USDT, misalnya `1000`

Lalu **Settings → Actions → General → Workflow permissions** → pilih **Read and write permissions** → Save.

## Langkah 4 — Jalankan pertama kali
**Actions** → **Sinyal Crypto Futures** → **Run workflow**. Dalam 1–3 menit Telegram Anda menerima
daftar order awal. Setelah itu bot berjalan sendiri setiap 4 jam (bisa terlambat beberapa menit; tidak masalah
karena yang dipasang adalah stop order).

---

## Arti pesan & yang harus Anda lakukan
| Pesan | Tindakan di exchange (futures USDT-M, **isolated margin**, leverage 2–5×) |
|---|---|
| 🆕 **BUY STOP** / 🔴 **SELL STOP** harga X, SL Y | Pasang order **Stop Market** dengan harga pemicu X. Setelah terisi, pasang **Stop Market reduce-only** di Y sebagai SL. Ukuran sesuai pesan (jika `MODAL_USDT` diisi). |
| ♻️ **GANTI** | Batalkan order lama koin itu, pasang order baru dengan angka di pesan |
| ❌ **batalkan order pending** | Batalkan order koin itu yang belum terisi |
| ✅ **kemungkinan TERISI** | Cek di exchange; pastikan SL sudah terpasang |
| ⬆️ **geser SL** | Ubah SL posisi itu ke harga baru (hanya ke arah untung) |
| 🏁 **posisi selesai** | Posisi sudah kena SL; tidak perlu tindakan selain memastikan posisi tertutup |

Tidak ada TP: keuntungan dikunci oleh SL yang terus digeser.

## Catatan penting
- **Maksimal 10 slot** (posisi + order pending). Bot otomatis membatalkan order lain saat 10 posisi terbuka.
- Bot "mengira" order terisi berdasarkan harga candle. Jika di exchange Anda ternyata **tidak** terisi
  (atau sebaliknya), ikuti kondisi nyata di exchange; bot akan menyesuaikan saat posisi/order berikutnya.
- Data harga: Binance spot (publik). Data funding untuk filter short: Hyperliquid (publik). QNT hanya long.
- GitHub bisa menonaktifkan jadwal jika repository tidak ada aktivitas lama; bot menulis `state.json` setiap
  berjalan sehingga biasanya tetap aktif. Jika berhenti, buka tab Actions → **Enable workflow**.
- Pastikan exchange yang Anda gunakan **legal & terdaftar di OJK**.
- Hasil backtest 2020–2026 (aturan bot ini): ±65%/tahun pada drawdown ±20% (risiko 0,67%/trade),
  ekspektasi realistis lebih rendah (±25–50%). Bukan saran investasi; mulai dengan dana kecil.
