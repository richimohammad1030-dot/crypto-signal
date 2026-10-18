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

PANDUAN_ANGGOTA = """<b>📌 PANDUAN ANGGOTA — Sinyal Crypto Futures</b>

<b>Cara kerja</b>
Sinyal trend-following di 24 koin besar (futures USDT perpetual). Dicek setiap 4 jam (03, 07, 11, 15, 19, 23 WIB). Maksimal 10 posisi/order sekaligus. Tidak ada TP: keuntungan dikunci dengan SL yang terus digeser.

<b>Arti pesan</b>
🆕 SINYAL BARU → pasang order Stop Market + SL sesuai angka
♻️ UPDATE ORDER → order Anda BELUM terisi tapi angkanya berubah (high/low 20 hari atau volatilitas bergeser) → edit order ke angka baru
❌ ORDER DIBATALKAN → cancel order pending koin itu (alasan tertulis)
✅ POSISI TERBUKA → order terisi; pastikan SL terpasang
🔁 GESER SL → ubah SL posisi itu ke angka baru (lihat "Cara kerja SL+")
📊 UPDATE POSISI → ringkasan semua posisi terbuka setiap 4 jam: harga kini, % & R berjalan, SL, status SL+
🏁 POSISI DITUTUP → hasil akhir: ❌ SL awal (rugi) · 🟡 SL+ impas · ✅ SL+ untung

<b>Cara kerja SL+ (trailing)</b>
Setiap 4 jam bot menghitung SL baru: BUY → low terendah 3 hari terakhir, SELL → high tertinggi 3 hari terakhir. SL hanya dipindah jika lebih menguntungkan. Bot mengirim angka pasti di pesan 🔁 GESER SL — cukup samakan SL di exchange dengan angka itu.
Begitu SL melewati harga entry, posisi berstatus SL+ (tidak bisa rugi lagi). Jangan pakai fitur Trailing Stop bawaan exchange: aturannya (jarak % tetap, bergerak tiap detik) berbeda dari strategi ini dan membuat hasil tidak sama.

<b>1. Ukuran posisi (WAJIB dihitung sendiri)</b>
Ukuran (koin) = (Modal × Risiko%) ÷ |Entry − SL|
Contoh: modal 1.000 USDT, risiko 0,5% = 5 USDT; entry 100, SL 95 → 5 ÷ 5 = 1 koin.
Saran risiko 0,3–0,5% per trade. Maksimal 10 posisi bersamaan.

<b>2. Margin & leverage</b>
• Selalu <b>Isolated</b>.
• Leverage ≤ "leverage maks aman" di pesan (maks 5×). Leverage tidak menambah risiko selama ukuran posisi dihitung dengan rumus di atas.

<b>3. Order masuk</b>
• BUY STOP → order <b>Stop Market</b> Buy/Long, harga pemicu = angka sinyal (pemicu Last Price).
• SELL STOP → order <b>Stop Market</b> Sell/Short.

<b>4. Stop loss</b>
Pasang SL (Stop Market, reduce-only, Last Price) saat order dibuat atau segera setelah terisi. Tanpa TP.

<b>5. Geser SL</b>
Ubah SL manual sesuai pesan "geser SL". Jangan pakai fitur Trailing Stop bawaan exchange (aturannya berbeda).

<b>Binance Futures</b>
Isolated + leverage → order <b>Stop Market</b> (Stop Price = sinyal, Last) → centang <b>TP/SL</b>, isi Stop Loss → Buy/Long atau Sell/Short. Geser SL: tab Positions → pensil TP/SL. Batal: Open Orders → Cancel.

<b>OKX</b>
Perpetual → Isolated + leverage → order <b>Trigger</b> (trigger = sinyal, Last, harga Market) → aktifkan <b>TP/SL</b>, isi SL → Buy/Long atau Sell/Short. Geser SL: Positions → TP/SL. Batal: Algo orders → Cancel.

<b>⚠️ Risiko</b>
Win rate ±40%: kalah beruntun itu normal. Gunakan exchange yang legal (terdaftar OJK). Bukan saran investasi; gunakan dana yang siap hilang."""

BANTUAN = """<b>🤖 Perintah bot</b>
/status — posisi terbuka, order pending, hasil bulan ini
/terisi KOIN harga — order terisi (contoh: <code>/terisi SOL 100.5</code>)
/tidak KOIN — order tidak dipasang/tidak terisi, hapus dari catatan
/tutup KOIN harga — posisi sudah ditutup (contoh: <code>/tutup ETH 2290</code>)
/panduan — panduan umum (risiko, leverage, SL, trailing)
/panduan binance · /panduan okx — langkah di exchange
/rekap · /rekap bulan — rekap performa minggu/bulan berjalan
/rekap minggu lalu · /rekap bulan lalu — rekap periode sebelumnya
/rekap_channel [minggu|bulan] [lalu] — posting rekap ke channel
/channel — cek channel sinyal
/kirim_panduan — posting & pin panduan anggota di channel
Perintah hanya berlaku dari chat pribadi Anda dan dibaca bot setiap ±1 jam."""


WIB = dt.timezone(dt.timedelta(hours=7))
BULAN = ["", "Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


def period_bounds(kind, now=None, previous=False):
    """Batas periode dalam WIB. kind 'minggu' (Senin-Minggu) atau 'bulan'. Return (awal, akhir) datetime WIB."""
    now = (now or dt.datetime.now(WIB)).astimezone(WIB)
    if kind == "bulan":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if previous:
            start = (start - dt.timedelta(days=1)).replace(day=1)
        nxt = (start.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
        return start, nxt
    start = (now - dt.timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    if previous:
        start -= dt.timedelta(days=7)
    return start, start + dt.timedelta(days=7)


def _spark(vals):
    bars = "▁▂▃▄▅▆▇█"
    if not vals:
        return ""
    lo, hi = min(vals), max(vals)
    if hi - lo < 1e-9:
        return bars[3] * len(vals)
    return "".join(bars[int((v - lo) / (hi - lo) * 7)] for v in vals)


def build_recap(state, kind="minggu", previous=False, risk_pct=0.67, now=None, fmt=lambda x: f"{x:g}"):
    """Satu bubble rekap performa (HTML Telegram)."""
    start, end = period_bounds(kind, now, previous)
    t0, t1 = start.timestamp(), end.timestamp()
    tr = [h for h in state.get("hist", []) if t0 <= h[3] < t1]          # h = [koin, arah, t_buka, t_tutup, entry, exit, R]
    last_day = end - dt.timedelta(days=1)
    if kind == "bulan":
        title, rng = "REKAP BULANAN", f"{BULAN[start.month]} {start.year}"
    else:
        title, rng = "REKAP MINGGUAN", f"{start.day} {BULAN[start.month]} – {last_day.day} {BULAN[last_day.month]} {last_day.year}"
    if not previous:
        rng += " (berjalan)"
    L = [f"<b>━━━━━━━━━━━━━━━━━━━━</b>",
         f"📈 <b>{title}</b>",
         f"🗓 {rng}",
         f"<b>━━━━━━━━━━━━━━━━━━━━</b>"]
    if tr:
        R = [h[6] for h in tr]
        tot = sum(R)
        win = [r for r in R if r >= 0.15]
        be = [r for r in R if -0.15 < r < 0.15]
        loss = [r for r in R if r <= -0.15]
        gp, gl = sum(r for r in R if r > 0), -sum(r for r in R if r < 0)
        pf = (gp / gl) if gl > 0 else None
        best = max(tr, key=lambda h: h[6]); worst = min(tr, key=lambda h: h[6])
        eq = pk = dd = 0.0; streak = mstreak = 0
        for h in sorted(tr, key=lambda h: h[3]):
            eq += h[6]; pk = max(pk, eq); dd = min(dd, eq - pk)
            streak = streak + 1 if h[6] <= -0.15 else 0; mstreak = max(mstreak, streak)
        # kurva harian (kumulatif R)
        days = (end - start).days
        cum, curve = 0.0, []
        for k in range(days):
            ds, de = (start + dt.timedelta(days=k)).timestamp(), (start + dt.timedelta(days=k + 1)).timestamp()
            if ds > (now or dt.datetime.now(WIB)).timestamp():
                break
            cum += sum(h[6] for h in tr if ds <= h[3] < de); curve.append(cum)
        icon = "🟢" if tot > 0 else "🔴" if tot < 0 else "⚪"
        L += [f"{icon} <b>Hasil: {tot:+.2f}R</b>  (≈ {tot * risk_pct:+.1f}%)",
              f"🎯 Trade selesai: <b>{len(R)}</b>  ✅{len(win)} · 🟡{len(be)} · ❌{len(loss)}",
              f"📊 Win rate: <b>{len(win) / len(R) * 100:.0f}%</b>",
              f"⚖️ Profit factor: <b>{pf:.2f}</b>" if pf is not None else "⚖️ Profit factor: <b>∞</b> (tanpa loss)",
              f"📐 Rata-rata: <b>{tot / len(R):+.2f}R</b> / trade",
              f"🏆 Terbaik: {best[0]} {best[6]:+.2f}R",
              f"💥 Terburuk: {worst[0]} {worst[6]:+.2f}R",
              f"📉 Drawdown: {dd:.2f}R · kalah beruntun maks {mstreak}",
              f"📈 Kurva: <code>{_spark(curve)}</code>"]
    else:
        L.append("Belum ada trade yang selesai pada periode ini.")
    opn = [(c, v["pos"]) for c, v in state.get("coins", {}).items() if v.get("pos")]
    if opn:
        lock = 0.0
        for c, p in opn:
            r0 = p[4] if len(p) > 4 else abs(p[1] - p[2])
            lock += (p[2] - p[1]) * p[0] / r0 if r0 else 0
        L.append(f"📂 Posisi terbuka: <b>{len(opn)}</b> · SL terkunci {lock:+.2f}R")
    L += [f"<b>━━━━━━━━━━━━━━━━━━━━</b>",
          f"<i>% = estimasi pada risiko {risk_pct}%/trade · ✅ ≥ +0,15R · 🟡 SL+ impas · ❌ loss</i>"]
    return "\n".join(L)


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
        res = _api("getUpdates", {"offset": state.get("tg_offset", 0), "timeout": 0, "allowed_updates": json.dumps(["message", "my_chat_member"])})
    except Exception as e:
        print("Gagal membaca perintah Telegram:", e)
        return []
    cmds = []
    for u in res.get("result", []):
        state["tg_offset"] = u["update_id"] + 1
        mcm = u.get("my_chat_member")
        if mcm:
            # Bot dijadikan admin channel -> simpan id channel otomatis
            ch = mcm.get("chat") or {}
            status = (mcm.get("new_chat_member") or {}).get("status")
            if ch.get("type") == "channel":
                if status == "administrator":
                    state["channel_id"] = ch.get("id")
                    state["channel_title"] = ch.get("title")
                    cmds.append("/_channel_ok")
                elif status in ("left", "kicked", "member") and state.get("channel_id") == ch.get("id"):
                    state.pop("channel_id", None)
                    cmds.append("/_channel_off")
            continue
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
    if cmd == "/_channel_ok":
        return (f"📢 Bot sudah menjadi admin channel <b>{state.get('channel_title')}</b>. "
                "Mulai sekarang semua sinyal & update dikirim ke channel. "
                "Kirim /kirim_panduan untuk mem-posting & pin panduan anggota di channel.")
    if cmd == "/_channel_off":
        return "📢 Bot tidak lagi menjadi admin channel. Sinyal kembali dikirim ke chat pribadi Anda."
    if cmd == "/channel":
        return (f"Channel aktif: <b>{state.get('channel_title')}</b>" if state.get("channel_id")
                else "Belum ada channel. Jadikan bot admin channel (izin: Post Messages & Pin Messages).")
    if cmd == "/kirim_panduan":
        return "/_kirim_panduan" if state.get("channel_id") else "Belum ada channel. Jadikan bot admin channel dulu."
    if cmd in ("/rekap", "/rekap_channel"):
        kind = "bulan" if len(parts) > 1 and parts[1].lower().startswith("bul") else "minggu"
        prev = len(parts) > 2 and parts[2].lower() in ("lalu", "kemarin", "sebelumnya")
        txt = build_recap(state, kind, prev, float(os.environ.get("RISK_PCT") or "0.67"), fmt=fmt)
        if cmd == "/rekap_channel":
            if not state.get("channel_id"):
                return "Belum ada channel."
            return "/_post_channel\n" + txt
        return txt
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
