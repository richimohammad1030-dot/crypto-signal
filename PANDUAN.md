# Panduan Bot Sinyal Crypto Futures (gratis, tanpa VPS, tanpa TradingView Premium)

Bot ini berjalan otomatis di **GitHub Actions** setiap 4 jam, membaca data harga publik, lalu mengirim
instruksi ke **Telegram** Anda. Bot **tidak** punya akses ke akun exchange; Anda yang memasang order.

## Isi folder
| File | Fungsi |
|---|---|
| `signal_bot.py` | Mesin strategi + pengirim pesan Telegram |
| `.github/workflows/signal.yml` | Jadwal otomatis setiap 2 jam (strategi dicek 03, 07, 11, 15, 19, 23 WIB) |
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

### Label sinyal: 🟢 HIGH · 🟡 MEDIUM · 🔴 LOW
Setiap order diberi label kualitas setup berdasarkan backtest 2223 trade (Des 2019 – Okt 2026).
Skor dari 4 faktor yang terbukti konsisten di 2020–2023 **dan** 2024–2026:
- Jarak SL dalam % (volatilitas): < 7,88% → +1 · > 12,63% → −1
- Jarak harga dari EMA200 (dalam ATR): < 4,23 → +1 · > 5,55 → −1 (belum terlalu jauh dari tren)
- Peringkat market cap: 7 besar → +1 · di luar 15 besar → −1
- Tren BTC: searah posisi → +1 · berlawanan → −1

HIGH = skor ≥ 2 · MEDIUM = 0–1 · LOW = skor ≤ −1.

| Label | Porsi trade | Win rate | Rata-rata 2020–2023 | Rata-rata 2024–2026 |
|---|---|---|---|---|
| 🟢 HIGH | 31% | 44% | +0,57R | +0,68R |
| 🟡 MEDIUM | 39% | 40% | +0,40R | +0,12R |
| 🔴 LOW | 30% | 36% | +0,14R | −0,01R |

HIGH lebih baik dari LOW di **setiap tahun** 2020–2026. Catatan: label adalah gambaran historis, bukan
jaminan; trade LOW sesekali tetap menghasilkan profit besar. Ukuran risiko per trade tetap sama untuk
semua label kecuali Anda memutuskan lain. Backtest memakai funding Binance sebagai pengganti Hyperliquid
dan daftar 50 koin saat ini (ada bias koin yang "bertahan"), tanpa biaya trading.

---

## Perintah Telegram (sinkron dengan posisi Anda yang sebenarnya)
Bot tidak terhubung ke akun exchange, jadi bot hanya *memperkirakan* order terisi dari harga.
Laporkan kondisi sebenarnya lewat chat ke bot (dibaca setiap ±2 jam):

| Perintah | Fungsi |
|---|---|
| `/status` | Posisi terbuka (entry, SL, status SL awal / SL+), order pending, hasil bulan ini |
| `/terisi KOIN harga` | Order sudah terisi, misal `/terisi SOL 100.5` |
| `/tidak KOIN` | Order tidak dipasang / tidak terisi — hapus dari catatan |
| `/tutup KOIN harga` | Posisi sudah ditutup, misal `/tutup ETH 2290` |
| `/panduan` · `/panduan binance` · `/panduan okx` | Panduan risiko, leverage, stop order, SL & geser SL |

Setiap posisi selesai dilaporkan sebagai **❌ Kena SL awal (−1R)**, **🟡 SL+ impas**, atau **✅ SL+ untung (+xR)**.
Setiap order menyertakan **leverage maks aman** (isolated) agar tidak terlikuidasi sebelum SL.

---

## Channel untuk anggota (anggota hanya membaca)
1. Telegram → **New Channel** → beri nama → pilih Private atau Public.
2. Channel → **Administrators** → **Add Admin** → cari bot Anda → izinkan **Post Messages** dan **Pin Messages** → Save.
3. Dalam ±2 jam bot mendeteksi channel otomatis dan memberi tahu Anda di chat pribadi.
4. Kirim **/kirim_panduan** ke bot (chat pribadi) → panduan anggota diposting & di-pin di channel.

Setelah itu:
- **Semua sinyal & update** (order baru, ganti, batal, terisi, geser SL, SL/SL+) dikirim ke **channel**.
- **Ukuran posisi pribadi** (dari `MODAL_USDT`) dan balasan perintah hanya dikirim ke **chat pribadi** Anda.
- Anggota tidak bisa mengirim perintah; perintah dari selain chat id Anda diabaikan.
- Cek channel aktif: **/channel**. Jika bot dikeluarkan dari admin, sinyal kembali ke chat pribadi.

---

## Rekap performa
- Otomatis ke channel: **mingguan setiap Senin** (minggu lalu) dan **bulanan setiap tanggal 1** (bulan lalu), di cek pertama hari itu.
- Manual (chat pribadi): `/rekap`, `/rekap bulan`, `/rekap minggu lalu`, `/rekap bulan lalu`.
- Posting ke channel kapan saja: `/rekap_channel`, `/rekap_channel bulan`, `/rekap_channel minggu lalu`.
- Isi: total R & estimasi %, jumlah trade (✅ untung · 🟡 SL+ impas · ❌ loss), win rate, profit factor, rata-rata R,
  trade terbaik/terburuk, drawdown, kalah beruntun, kurva harian, posisi terbuka & R yang sudah terkunci.
- Estimasi % = total R × `RISK_PCT`. Rekap dihitung dari catatan bot, jadi lapor `/terisi`, `/tidak`, `/tutup` agar akurat.

---

## Bot XAU — Gold Daily Straddle (channel terpisah)
- Jadwal: Senin–Jumat setiap 2 jam, 07:00–23:00 WIB (`gold.yml`). 07:00 kirim order OCO hari itu; 23:00 batalkan/tutup.
- Data: XAU/USD H1 dari Setra (server MT5). Hasil backtest dengan data ini: 424 trade, +67R (2025–2026, biaya 0,40 USD).
- Channel: buat channel baru yang **namanya mengandung "XAU", "Gold", atau "Emas"**, jadikan bot admin (Post & Pin Messages).
  Bot otomatis mengenalinya sebagai channel XAU (±2 jam), lalu kirim `/kirim_panduan_xau` untuk pin panduan anggota.
- Perintah pribadi: `/status_xau`, `/rekap_xau`, `/rekap_xau bulan`, `/rekap_xau minggu lalu`.
- Variable opsional: `XAU_RISK_PCT` (default 0.5) untuk estimasi % di rekap.
