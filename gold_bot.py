"""
Bot sinyal "Gold Daily Straddle" (XAUUSD) -> channel Telegram khusus XAU.

Aturan (versi optimasi yang sudah di-backtest, chart H1):
- 07:00 WIB (candle H1 yang close 07:00): range = high & low 3 candle H1 terakhir.
- BUY STOP di high range, SELL STOP di low range (OCO: satu terisi, yang lain dibatalkan).
- SL = 1,5 x ATR(14) dari entry. TP = 4R (6 x ATR).
- 23:00 WIB: order yang belum terisi dibatalkan, posisi yang masih terbuka ditutup.
Bot hanya membaca data publik & mengirim pesan; tidak punya akses ke akun broker.
"""
import json, os, sys, time, urllib.request, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(HERE, "gold_state.json")
CRYPTO_STATE = os.path.join(HERE, "state.json")       # tempat id channel XAU disimpan oleh pemroses perintah
RANGE_N, SL_ATR, RR, ATR_N = 3, 1.5, 4.0, 14
PLACE_HOUR_UTC = 23     # jam BUKA candle H1 (UTC) yang close 07:00 WIB
CLOSE_HOUR_UTC = 15     # jam BUKA candle H1 (UTC) yang close 23:00 WIB
SYM = "XAUUSD"
LINE = "━━━━━━━━━━━━━━━━━━"

sys.path.insert(0, HERE)
from signal_bot import tg_send, http_json, atr          # pakai fungsi yang sama dengan bot crypto
import commands


def fmt(p):
    return f"{p:,.2f}"


def wib(ts):
    return (dt.datetime.fromtimestamp(ts, dt.timezone.utc) + dt.timedelta(hours=7)).strftime("%a %d %b %H:%M WIB")


def fetch_xau(n=1000):
    """Candle H1 XAU/USD (Setra/MT5). Return list [open_time_s, o, h, l, c] yang SUDAH close."""
    d = http_json(f"https://setra.id/api/md/candles?symbol=XAU%2FUSD&tf=1h&limit={n}")
    rows = [[c["t"] // 1000, c["o"], c["h"], c["l"], c["c"]] for c in d.get("data", [])]
    now = time.time()
    rows = [r for r in rows if r[0] + 3600 <= now]          # buang candle yang belum close
    dedup = {r[0]: r for r in rows}
    return [dedup[k] for k in sorted(dedup)]


class GoldEngine:
    """Urutan per candle sama persis dengan backtest:
       1) order terisi?  2) posisi kena SL/TP?  3) jam tutup 23:00  4) jam pasang 07:00"""
    def __init__(self, state, notify):
        self.s, self.notify = state, notify
        self.trades = []

    def record(self, d, e, ex, r0, t0, t1, why):
        R = (ex - e) * d / r0 if r0 else 0.0
        self.trades.append((t0, t1, d, e, ex, r0))
        self.s.setdefault("hist", []).append(["XAU", d, t0, t1, e, ex, round(R, 3)])
        self.notify("exit", d=d, entry=e, exit=ex, R=R, t0=t0, t=t1, why=why)

    def step(self, i, T, O, H, L, C, A):
        s = self.s
        t, hr = T[i], (T[i] // 3600) % 24
        pend, pos = s.get("pend"), s.get("pos")
        # 1) order pending terisi? (BUY STOP dicek lebih dulu)
        if pos is None and pend:
            b, sl_ = pend["buy"], pend["sell"]
            hit = None
            if H[i] >= b[0]:
                hit = (1, max(b[0], O[i]), b[1], b[2])
            elif L[i] <= sl_[0]:
                hit = (-1, min(sl_[0], O[i]), sl_[1], sl_[2])
            if hit:
                d, fill, slp, tpp = hit
                r0 = abs(fill - slp)
                s["pend"] = None
                s["pos"] = {"d": d, "e": fill, "sl": slp, "tp": tpp, "r0": r0, "t0": t}
                self.notify("fill", d=d, entry=fill, sl=slp, tp=tpp, t=t)
                if (d == 1 and L[i] <= slp) or (d == -1 and H[i] >= slp):
                    s["pos"] = None
                    self.record(d, fill, slp, r0, t, t, "kena SL di candle yang sama")
        # 2) kelola posisi (SL dicek lebih dulu dari TP)
        elif pos is not None and pos["t0"] < t:
            d = pos["d"]
            if (d == 1 and L[i] <= pos["sl"]) or (d == -1 and H[i] >= pos["sl"]):
                s["pos"] = None; self.record(d, pos["e"], pos["sl"], pos["r0"], pos["t0"], t, "kena SL")
            elif (d == 1 and H[i] >= pos["tp"]) or (d == -1 and L[i] <= pos["tp"]):
                s["pos"] = None; self.record(d, pos["e"], pos["tp"], pos["r0"], pos["t0"], t, "kena TP")
        # 3) jam tutup 23:00 WIB
        if hr == CLOSE_HOUR_UTC:
            if s.get("pend"):
                s["pend"] = None
                self.notify("expire")
            if s.get("pos"):
                p = s["pos"]; s["pos"] = None
                self.record(p["d"], p["e"], C[i], p["r0"], p["t0"], t, "ditutup jam 23:00")
        # 4) jam pasang 07:00 WIB
        if hr == PLACE_HOUR_UTC and s.get("pos") is None:
            hi, lo, a = max(H[i - RANGE_N + 1:i + 1]), min(L[i - RANGE_N + 1:i + 1]), A[i]
            if abs(hi - (hi - SL_ATR * a)) > 0.5:      # sama dengan backtest: abaikan order dengan SL < 0,5 USD
                s["pend"] = {"buy": [hi, hi - SL_ATR * a, hi + RR * SL_ATR * a],
                             "sell": [lo, lo + SL_ATR * a, lo - RR * SL_ATR * a],
                             "t": t, "hi": hi, "lo": lo}
                self.notify("order", pend=s["pend"], t=t, price=C[i])

    def run(self, rows, since):
        T = [r[0] for r in rows]; O = [r[1] for r in rows]; H = [r[2] for r in rows]; L = [r[3] for r in rows]; C = [r[4] for r in rows]
        A = atr(H, L, C, ATR_N)
        start = 250 if self.s.get("replay") else 50
        for i in range(start, len(rows)):
            if T[i] > since:
                self.step(i, T, O, H, L, C, A)
                self.s["last_ts"] = T[i]
        return C[-1] if C else None


# ---------------------------------------------------------------- templat bubble
def make_notifier(buf, risk_pct):
    def notify(kind, **k):
        if kind == "order":
            p = k["pend"]; b, s = p["buy"], p["sell"]
            warn = []
            px = k.get("live")
            if px is not None and px >= b[0]:
                warn.append("⚠️ Harga sudah di atas BUY STOP — order BUY akan langsung terisi di harga pasar.")
            if px is not None and px <= s[0]:
                warn.append("⚠️ Harga sudah di bawah SELL STOP — order SELL akan langsung terisi di harga pasar.")
            buf.append(
                f"🌅 <b>ORDER HARI INI · {SYM}</b>\n{LINE}\n"
                f"📐 Range 04:00–07:00 WIB: {fmt(p['lo'])} – {fmt(p['hi'])}\n\n"
                f"🟢 <b>BUY STOP</b>  {fmt(b[0])}\n"
                f"   🛑 SL {fmt(b[1])} · 🎯 TP {fmt(b[2])}\n\n"
                f"🔴 <b>SELL STOP</b> {fmt(s[0])}\n"
                f"   🛑 SL {fmt(s[1])} · 🎯 TP {fmt(s[2])}\n"
                f"{LINE}\n"
                f"🔗 OCO: jika satu terisi, <b>batalkan</b> yang lain.\n"
                f"⏰ Berlaku s.d. <b>23:00 WIB</b> (order dibatalkan & posisi ditutup).\n"
                f"⚖️ Risiko per order: {risk_pct}% modal · SL {fmt(abs(b[0]-b[1]))} USD"
                + ("\n" + "\n".join(warn) if warn else ""))
        elif kind == "fill":
            arah = "🟢 BUY" if k["d"] == 1 else "🔴 SELL"
            lawan = "SELL STOP" if k["d"] == 1 else "BUY STOP"
            buf.append(
                f"✅ <b>POSISI TERBUKA · {SYM}</b> · {arah}\n{LINE}\n"
                f"🎯 Entry : <b>{fmt(k['entry'])}</b> (±{wib(k['t'])})\n"
                f"🛑 SL    : {fmt(k['sl'])}\n"
                f"🏁 TP    : {fmt(k['tp'])} (4R)\n"
                f"{LINE}\n"
                f"👉 <b>Batalkan {lawan}</b> (OCO). Posisi ditutup paling lambat 23:00 WIB.")
        elif kind == "exit":
            arah = "🟢 BUY" if k["d"] == 1 else "🔴 SELL"
            gerak = k["exit"] - k["entry"]
            buf.append(
                f"🏁 <b>POSISI DITUTUP · {SYM}</b> · {arah}\n{LINE}\n"
                f"🎯 Entry  : {fmt(k['entry'])}\n"
                f"🚪 Keluar : <b>{fmt(k['exit'])}</b> ({k['why']})\n"
                f"📈 Gerak  : {gerak * k['d']:+.2f} USD\n"
                f"{LINE}\n"
                + ("⏰ Jika masih terbuka di akun Anda, <b>tutup sekarang</b>.\n" if "23:00" in k["why"] else "")
                + label(k["R"]))
        elif kind == "expire":
            buf.append(f"⏰ <b>23:00 WIB · {SYM}</b>\n{LINE}\nOrder hari ini tidak terisi.\n👉 <b>Batalkan</b> BUY STOP & SELL STOP yang masih aktif.")
    return notify


def label(R):
    if R >= 3.5:
        return f"🎯 <b>Kena TP</b> ({R:+.2f}R)"
    if R >= 0.15:
        return f"✅ <b>Untung</b> ({R:+.2f}R)"
    if R > -0.15:
        return f"🟡 <b>Impas</b> ({R:+.2f}R)"
    if R <= -0.9:
        return f"❌ <b>Kena SL</b> ({R:+.2f}R)"
    return f"⚠️ <b>Rugi sebagian</b> ({R:+.2f}R)"


def update_bubble(pos, px):
    d, e = pos["d"], pos["e"]
    R = (px - e) * d / pos["r0"] if pos["r0"] else 0
    return (f"📊 <b>UPDATE POSISI · {SYM}</b> · {'🟢 BUY' if d == 1 else '🔴 SELL'}\n{LINE}\n"
            f"Entry {fmt(e)} → kini <b>{fmt(px)}</b>\n"
            f"{'🟢' if R > 0 else '🔴' if R < 0 else '⚪'} {(px - e) * d:+.2f} USD · <b>{R:+.2f}R</b> berjalan\n"
            f"🛑 SL {fmt(pos['sl'])} · 🎯 TP {fmt(pos['tp'])}\n"
            f"⏰ Ditutup paling lambat 23:00 WIB")


# ---------------------------------------------------------------- main
def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    risk_pct = float(os.environ.get("XAU_RISK_PCT") or "0.5")
    state = json.load(open(STATE_FILE)) if os.path.exists(STATE_FILE) else {"last_ts": 0}
    cstate = json.load(open(CRYPTO_STATE)) if os.path.exists(CRYPTO_STATE) else {}
    target = cstate.get("gold_channel_id")      # None -> kirim ke chat pribadi pemilik
    try:
        rows = fetch_xau()
    except Exception as e:
        tg_send(f"⚠️ Bot XAU gagal mengambil data harga: {e}"); sys.exit(1)
    if len(rows) < 100:
        tg_send("⚠️ Bot XAU: data harga tidak cukup."); sys.exit(1)
    first = state.get("last_ts", 0) == 0
    if first:
        # run pertama: mulai dari jam tutup (23:00 WIB) terakhir agar order/posisi hari ini ikut terbentuk
        closes = [r[0] for r in rows if (r[0] // 3600) % 24 == CLOSE_HOUR_UTC]
        since = closes[-1] if closes else rows[-1][0] - 1
    else:
        since = state["last_ts"]
    buf = []
    eng = GoldEngine(state, make_notifier(buf, risk_pct))
    px = eng.run(rows, since)
    # peringatan jika harga live sudah melewati level order (pesan pagi tiba beberapa menit setelah 07:00)
    for k, m in enumerate(buf):
        if m.startswith("🌅") and state.get("pend"):
            b, s = state["pend"]["buy"][0], state["pend"]["sell"][0]
            if px >= b or px <= s:
                buf[k] = m + f"\n⚠️ Harga terakhir {fmt(px)} sudah melewati salah satu level order."
    for m in buf:
        tg_send(m, chat=target)
    if state.get("pos") and not any(m.startswith("✅") for m in buf):
        tg_send(update_bubble(state["pos"], px), chat=target)
    # rekap otomatis: mingguan (Senin, cek pertama) & bulanan (tanggal 1)
    now_wib = dt.datetime.now(commands.WIB)
    wk, _ = commands.period_bounds("minggu", now_wib, previous=True)
    if now_wib.weekday() == 0 and state.get("recap_week") != wk.isoformat():
        tg_send(commands.build_recap(state, "minggu", True, risk_pct, now_wib, fmt).replace("REKAP", "REKAP XAU"), chat=target)
        state["recap_week"] = wk.isoformat()
    mo, _ = commands.period_bounds("bulan", now_wib, previous=True)
    if now_wib.day == 1 and state.get("recap_month") != mo.isoformat():
        tg_send(commands.build_recap(state, "bulan", True, risk_pct, now_wib, fmt).replace("REKAP", "REKAP XAU"), chat=target)
        state["recap_month"] = mo.isoformat()
    json.dump(state, open(STATE_FILE, "w"), indent=1)
    print(*buf, sep="\n\n")


if __name__ == "__main__":
    main()
