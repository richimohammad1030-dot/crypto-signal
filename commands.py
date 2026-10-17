"""
Perintah Telegram untuk menyinkronkan bot dengan posisi Anda yang sebenarnya.
Bot hanya membaca pesan dari TELEGRAM_CHAT_ID Anda sendiri.
"""
import json, os, time, urllib.request, urllib.parse, datetime as dt

PANDUAN_UMUM = """<b>📘 Panduan umum strategi</b>

<b>1. Risiko per trade</b>
Bot menghitung ukuran posisi dari variable <code>MODAL_USDT</code> dan <code>RISK_PCT</code> di GitHub.
Contoh modal 1.000 USDT, risiko 0,5% → rugi maksimal per trade 5 USDT jika kena SL awal.
Mulai kecil (0,3–0,5%). Maksimal 10 posisi sekaligus, jadi risiko total maksimal ±10× risiko per trade.

<b>2. Margin & leverage</b>
• Selalu <b>Isolated</b> (bukan Cross).
• Leverage hanya untuk menghemat margin; risiko ditentukan oleh ukuran posisi & SL, bukan leverage.
• Pakai leverage ≤ angka "leverage maks aman" di pesan order (maks 5×), agar posisi tidak terlikuidasi sebelum SL.

<b>3. Order masuk</b>
• Pesan "BUY STOP X" → order <b>Stop Market</b> sisi Buy/Long, harga pemicu X.
• Pesan "SELL STOP X" → order <b>Stop Market</b> sisi Sell/Short, harga pemicu X.
• Pemicu memakai <b>Last Price</b>.

<b>4. Stop loss</b>
• Pasang SL saat order dibuat (fitur TP/SL) atau segera setelah terisi.
• SL = Stop Market, <b>reduce-only</b>, pemicu Last Price, harga sesuai pesan. <b>Tidak ada TP.</b>

<b>5. Trailing stop (geser SL)</b>
• Pesan "⬆️ geser SL ... → Y": ubah SL posisi itu ke Y. Jangan pakai fitur "Trailing Stop" bawaan exchange — aturannya berbeda.
• SL hanya digeser ke arah untung. Jika SL sudah melewati harga entry, posisi berstatus <b>SL+</b> (minimal impas).

<b>6. Laporkan ke bot</b>
/terisi KOIN harga · /tidak KOIN · /tutup KOIN harga · /status
Bot membaca perintah setiap ±1 jam."""

PANDUAN_BINANCE = """<b>📗 Binance Futures (USDⓈ-M)</b>

<b>Persiapan (sekali per koin)</b>
1. Buka Futures → pilih pasangan, misal BTCUSDT Perpetual.
2. Klik tulisan <b>Cross</b> → pilih <b>Isolated</b> → Confirm.
3. Klik angka leverage (misal 20x) → atur ke ≤ "leverage maks aman" di pesan → Confirm.

<b>Pasang order masuk</b>
4. Tab order: pilih <b>Stop Market</b> (di dropdown "Stop Limit").
5. <b>Stop Price</b> = harga di pesan; pemicu <b>Last</b>.
6. <b>Size</b> = ukuran koin di pesan (ubah satuan ke koin, bukan USDT, jika perlu).
7. Centang <b>TP/SL</b> → isi <b>Stop Loss</b> = SL di pesan (trigger Last). Kosongkan Take Profit.
8. Klik <b>Buy/Long</b> (untuk BUY STOP) atau <b>Sell/Short</b> (untuk SELL STOP).

<b>Setelah terisi</b>
9. Tab <b>Positions</b> → pastikan kolom TP/SL menampilkan SL. Jika belum: klik ikon pensil TP/SL → isi Stop Loss → Confirm.
10. Kirim ke bot: <code>/terisi BTC 79800</code> (harga isi sebenarnya).

<b>Geser SL</b>
11. Positions → ikon pensil di kolom TP/SL → ubah harga Stop Loss → Confirm.

<b>Batalkan order</b>
12. Tab <b>Open Orders</b> → Cancel pada order koin itu."""

PANDUAN_OKX = """<b>📘 OKX (Perpetual / Swap)</b>

<b>Persiapan (sekali per koin)</b>
1. Trade → <b>Perpetual</b> → pilih misal BTC-USDT-SWAP.
2. Mode margin: klik <b>Cross</b> → pilih <b>Isolated</b>.
3. Klik leverage → atur ≤ "leverage maks aman" di pesan.

<b>Pasang order masuk</b>
4. Jenis order: <b>Trigger</b> (atau "Stop").
5. <b>Trigger price</b> = harga di pesan; pemicu <b>Last</b>; order price = <b>Market</b>.
6. <b>Amount</b> = ukuran di pesan (pilih satuan koin; OKX bisa memakai satuan kontrak, cek nilai kontrak).
7. Aktifkan <b>TP/SL</b> → isi <b>SL trigger</b> = SL di pesan, Market. Kosongkan TP.
8. Klik <b>Buy/Long</b> atau <b>Sell/Short</b> sesuai pesan.

<b>Setelah terisi</b>
9. Tab <b>Positions</b> → cek TP/SL. Jika belum ada: klik <b>TP/SL</b> → isi SL → Confirm.
10. Kirim ke bot: <code>/terisi BTC 79800</code>.

<b>Geser SL</b>
11. Positions → TP/SL → ubah harga SL → Confirm (atau tab "Algo orders" → Amend).

<b>Batalkan order</b>
12. Tab <b>Open orders / Algo orders</b> → Cancel."""

BANTUAN = """<b>🤖 Perintah bot</b>
/status — posisi terbuka, order pending, hasil bulan ini
/terisi KOIN harga — order terisi (contoh: <code>/terisi SOL 100.5</code>)
/tidak KOIN — order tidak dipasang/tidak terisi, hapus dari catatan
/tutup KOIN harga — posisi sudah ditutup (contoh: <code>/tutup ETH 2290</code>)
/panduan — panduan umum (risiko, leverage, SL, trailing)
/panduan binance · /panduan okx — langkah di exchange
Perintah dibaca bot setiap ±1 jam."""


def _api(method, params):
    tok = os.environ.get("TELEGRAM_TOKEN")
    data = urllib.parse.urlencode(params).encode()
    with urllib.request.urlopen(f"https://api.telegram.org/bot{tok}/{method}", data=data, timeout=40) as r:
        return json.load(r)


def fetch_commands(state):
    """Ambil pesan baru dari chat pemilik saja. Return list teks perintah."""
    tok, chat = os.environ.get("TELEGRAM_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not tok or not chat:
        return []
    try:
        res = _api("getUpdates", {"offset": state.get("tg_offset", 0), "timeout": 0, "allowed_updates": json.dumps(["message"])})
    except Exception as e:
        print("Gagal membaca perintah Telegram:", e)
        return []
    cmds = []
    for u in res.get("result", []):
        state["tg_offset"] = u["update_id"] + 1
        m = u.get("message") or {}
        if str((m.get("chat") or {}).get("id")) != str(chat):
            continue          # abaikan pesan dari orang lain
        t = (m.get("text") or "").strip()
        if t.startswith("/"):
            cmds.append(t)
    return cmds


def _num(x):
    return float(x.replace(",", ".")) if x is not None else None


def handle(state, text, last_price, fmt, exit_label, wib):
    """Proses satu perintah. Return teks balasan."""
    parts = text.split()
    cmd = parts[0].split("@")[0].lower()
    coins = state.setdefault("coins", {})
    if cmd in ("/start", "/bantuan", "/help"):
        return BANTUAN
    if cmd == "/panduan":
        sub = parts[1].lower() if len(parts) > 1 else ""
        return PANDUAN_BINANCE if sub == "binance" else PANDUAN_OKX if sub == "okx" else PANDUAN_UMUM
    if cmd == "/status":
        lines = ["<b>📋 Status</b>"]
        pos = [(c, v["pos"]) for c, v in coins.items() if v.get("pos")]
        pend = [(c, v["pend"]) for c, v in coins.items() if v.get("pend")]
        lines.append(f"Posisi terbuka: {len(pos)} · order pending: {len(pend)}")
        for c, p in pos:
            d, e, sl = p[0], p[1], p[2]
            r0 = p[4] if len(p) > 4 else abs(e - sl)
            locked = (sl - e) * d / r0 if r0 else 0
            tag = "SL+ (terkunci %+.2fR)" % locked if locked > -0.15 else "SL awal"
            lines.append(f"• <b>{c}</b> {'BUY' if d==1 else 'SELL'} entry {fmt(e)} · SL {fmt(sl)} · {tag}")
        for c, p in pend:
            lines.append(f"• {c} pending {'BUY STOP' if p[0]==1 else 'SELL STOP'} {fmt(p[1])} · SL {fmt(p[2])}")
        now = dt.datetime.now(dt.timezone.utc)
        month = [h for h in state.get("hist", []) if dt.datetime.fromtimestamp(h[3], dt.timezone.utc).strftime("%Y-%m") == now.strftime("%Y-%m")]
        if month:
            tot = sum(h[6] for h in month)
            lines.append(f"\nBulan ini: {len(month)} trade selesai · total {tot:+.2f}R")
        return "\n".join(lines)
    if cmd in ("/terisi", "/tidak", "/tutup"):
        if len(parts) < 2:
            return "Format: " + {"/terisi": "/terisi KOIN harga", "/tidak": "/tidak KOIN", "/tutup": "/tutup KOIN harga"}[cmd]
        c = parts[1].upper().replace("USDT", "")
        if c not in coins:
            return f"Koin {c} tidak ada dalam catatan bot."
        st = coins[c]
        try:
            price = _num(parts[2]) if len(parts) > 2 else None
        except ValueError:
            return "Harga tidak valid. Contoh: /terisi SOL 100.5"
        if cmd == "/terisi":
            if st.get("pend"):
                d, en, sl = st["pend"]
                e = price or en
                st["pos"] = [d, e, sl, int(time.time()), abs(e - sl)]
                st["pend"] = None
                return f"✅ Dicatat: {c} {'BUY' if d==1 else 'SELL'} terisi di {fmt(e)} · SL {fmt(sl)}"
            if st.get("pos"):
                if price:
                    p = st["pos"]
                    p[1] = price
                    if len(p) > 4:
                        p[4] = abs(price - p[2])
                    else:
                        p.append(abs(price - p[2]))
                return f"✅ {c} sudah tercatat terbuka · entry {fmt(st['pos'][1])}"
            return f"Tidak ada order {c} di catatan bot."
        if cmd == "/tidak":
            had = "posisi" if st.get("pos") else "order" if st.get("pend") else None
            st["pos"] = None
            st["pend"] = None
            if not had:
                return f"Tidak ada order/posisi {c} di catatan."
            return f"🗑️ {had.capitalize()} {c} dihapus dari catatan. Order baru bisa muncul lagi di cek 4-jam berikutnya jika sinyal masih ada."
        if cmd == "/tutup":
            if not st.get("pos"):
                return f"Tidak ada posisi {c} yang tercatat terbuka."
            d, e, sl, t0 = st["pos"][:4]
            r0 = st["pos"][4] if len(st["pos"]) > 4 else abs(e - sl)
            ex = price or last_price(c)
            if ex is None:
                return "Harga penutupan tidak diketahui. Kirim: /tutup KOIN harga"
            R = (ex - e) * d / r0 if r0 else 0.0
            state.setdefault("hist", []).append([c, d, t0, int(time.time()), e, ex, round(R, 3)])
            st["pos"] = None
            return f"🏁 {c} ditutup di {fmt(ex)}\n{exit_label(R)}"
    return "Perintah tidak dikenal. Kirim /bantuan"
