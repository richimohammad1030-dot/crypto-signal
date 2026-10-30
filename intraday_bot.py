"""
Bot sinyal "Crypto Intraday" -> channel Telegram yang sama dengan bot swing (label 🟠 INTRADAY).

Aturan = juara terkunci v2 (riset/intraday/STRATEGI.md, PARAM di riset/backtest_intraday.py):
- Modul B (sinyal pagi 07:00 WIB): koin searah tren BTC & volatilitas tinggi -> LIMIT 1 ATR H1 dari open 07:00,
  TP di harga open, SL 1,5 ATR H1, order berlaku 12 jam, posisi maks 24 jam. Short hanya jika funding > 0.
- Modul A (dip 15m, kapan saja): tren naik 15m, RSI2<5 atau RSI14<30, ATR15 >= 1,5% -> LIMIT long 0,25 ATR di bawah
  close, berlaku 2 jam, SL 3 ATR, TUTUP saat RSI2>70 (bot kirim perintah), posisi maks 2 jam.
- Maks 3 posisi terbuka, maks 3 order menunggu, 1 order/posisi per koin. Posisi penuh -> order lain dibatalkan.
Bot berjalan tiap 15 menit, memproses setiap candle 15m yang sudah close (mesin sama dengan backtest),
mengirim pesan hanya saat ada kejadian, plus ringkasan setiap 2 jam.

Bot ini hanya membaca data publik dan mengirim pesan. Bot TIDAK punya akses ke akun exchange.
"""
import datetime as dt, json, os, sys, time, urllib.parse
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "riset"))
import numpy as np
import backtest_intraday as bi                     # PARAM juara + indikator (satu sumber dengan backtest)

STATE_FILE = os.path.join(HERE, "intraday_state.json")
VERSI = "intraday-v2"
STEP = 900


# ======================================================================= mesin (dipakai live & replay)
class Engine:
    """Memproses candle 15m satu per satu, urutan sama dengan backtest_intraday.portfolio().
    s["orders"]: semua order (termasuk 'bayangan' yang tidak dikirim, agar jeda sinyal per koin sama dengan backtest).
    Order: c, m, d, lim, r0, tp, t0, vb, hb, rsi, st (pend/open/done), live (pend/open/done/cancel/none), dst."""

    def __init__(self, state, P, coins, notify, funding_fn=None, cost_fn=None):
        self.s, self.P, self.coins, self.notify = state, P, coins, notify
        self.rank = {c: i for i, c in enumerate(coins)}
        self.funding_fn = funding_fn or (lambda c, t: None)
        self.cost_fn = cost_fn or (lambda c, t0, t1, d: 0.0)
        self.s.setdefault("orders", []); self.s.setdefault("done_t", {}); self.s.setdefault("hist", [])

    def live(self, *st):
        return [o for o in self.s["orders"] if o["live"] in st]

    # ------------------------------------------------------------- satu candle (open time t) untuk semua koin
    def step(self, t, data):
        P = self.P
        cand = {}
        for c, D in data.items():
            i = D["ix"].get(t)
            if i is not None: cand[c] = i
        orders = self.s["orders"]
        # 1) order bayangan terisi di candle t
        filled_now = []
        for o in orders:
            if o["st"] != "pend" or o["c"] not in cand or not (o["t0"] <= t <= o["t0"] + (o["vb"] - 1) * STEP): continue
            D, i = data[o["c"]], cand[o["c"]]
            if (o["d"] == 1 and D["L"][i] <= o["lim"]) or (o["d"] == -1 and D["H"][i] >= o["lim"]):
                o["st"], o["t_fill"] = "open", t
                o["fill"] = float(min(o["lim"], D["O"][i]) if o["d"] == 1 else max(o["lim"], D["O"][i]))
                o["sl"] = o["fill"] - o["d"] * o["r0"]
                filled_now.append(o)
        # 2) portofolio: isi sesuai urutan market cap; posisi penuh -> order lain dibatalkan
        for o in sorted(filled_now, key=lambda o: self.rank[o["c"]]):
            if o["live"] != "pend": continue
            if len(self.live("open")) < P["CAP"]:
                o["live"] = "open"; self.notify("fill", o, t)
                if len(self.live("open")) >= P["CAP"]:
                    for x in self.live("pend"):
                        x["live"] = "cancel"; self.notify("cancel", x, t, "posisi penuh (maks %d)" % P["CAP"])
            else:
                o["live"] = "cancel"; self.notify("cancel", o, t, "posisi penuh (maks %d)" % P["CAP"])
        # 3) keluar posisi di candle t (SL dulu, lalu TP, lalu RSI, lalu batas waktu)
        for o in orders:
            if o["st"] != "open" or o["c"] not in cand: continue
            D, i = data[o["c"]], cand[o["c"]]; d, sl = o["d"], o["sl"]
            O, H, L, C = D["O"][i], D["H"][i], D["L"][i], D["C"][i]
            px = why = None
            if (d == 1 and L <= sl) or (d == -1 and H >= sl):
                px = sl if t == o["t_fill"] else (min(sl, O) if d == 1 else max(sl, O)); why = "SL"
            elif o["tp"] is not None and ((d == 1 and H >= o["tp"]) or (d == -1 and L <= o["tp"])) and not (t == o["t_fill"] and d * (C - o["tp"]) < 0):
                px, why = o["tp"], "TP"
            elif o["rsi"] and t > o["t_fill"] and ((d == 1 and D["R2"][i] > o["rsi"]) or (d == -1 and D["R2"][i] < 100 - o["rsi"])):
                px, why = C, "RSI"
            elif t >= o["t_fill"] + (o["hb"] - 1) * STEP:
                px, why = C, "WAKTU"
            if px is None: continue
            cx = P["MAKER"] if why == "TP" else P["TAKER"]
            fill = o["fill"]
            o.update(st="done", exit=float(px), t_exit=t + STEP, why=why,
                     R_gross=float(d * (px - fill) / o["r0"]),
                     R=float((d * (px - fill) - (P["MAKER"] + cx) / 100 * fill - self.cost_fn(o["c"], o["t_fill"], t, d) * fill) / o["r0"]))
            self.s["done_t"][o["c"] + o["m"]] = t
            if o["live"] == "open":
                o["live"] = "done"; self.notify("exit", o, t)
                self.s["hist"].append([o["c"], o["m"], d, o["t_fill"], t + STEP, fill, float(px), round(o["R"], 4), why, round(o["R_gross"], 4)])
        # 4) order bayangan kadaluarsa
        for o in orders:
            if o["st"] == "pend" and t >= o["t0"] + (o["vb"] - 1) * STEP:
                o["st"] = "done"; self.s["done_t"][o["c"] + o["m"]] = t
                if o["live"] == "pend":
                    o["live"] = "done"; self.notify("expire", o, t)
        # 5) sinyal baru dari close candle t -> order berlaku mulai candle t+15m
        new = []
        busy = {(o["c"], o["m"]) for o in orders if o["st"] in ("pend", "open")}
        t1 = t + STEP
        for c in self.coins:
            if c not in cand: continue
            D, i = data[c], cand[c]
            if P["A_ON"] and (c, "A") not in busy and self.s["done_t"].get(c + "A", -1) < t and i >= 900:   # riwayat min. 900 candle, sama dengan backtest
                A, Cc = D["A"][i], D["C"][i]
                if D["reg"][i] == 1 and (D["R2"][i] < 5 or D["R14"][i] < 30) and A / Cc >= P["A_VMIN"]:
                    new.append(dict(c=c, m="A", d=1, lim=float(Cc - P["A_OFF"] * A), r0=float(P["A_SL"] * A), tp=None, t0=t1,
                                    vb=P["A_VALID_MIN"] // 15, hb=P["A_HOLD_JAM"] * 4, rsi=P["A_RSI_EXIT"]))
            if P["B_ON"] and t1 % 86400 == 0 and (c, "B") not in busy and self.s["done_t"].get(c + "B", -1) <= t and "h1" in D and i + 1 >= 900:
                b = D["h1"](t1)                     # info H1 di close 07:00 WIB: (a, vr, tren, tren_btc, harga_open) atau None
                if b:
                    a, vr, tr, btc, o_px, atrp = b
                    if vr >= P["B_VR"] and atrp >= P["B_ATRP"] and tr != 0 and (not P["B_BTC"] or btc == tr):
                        if tr == 1 or (P["B_SHORT"] and (self.funding_fn(c, t1 - 3600) or 0) > 0):
                            lim = o_px - tr * P["B_K"] * a
                            new.append(dict(c=c, m="B", d=tr, lim=float(lim), r0=float(P["B_SL"] * a), tp=float(lim + tr * P["B_TPF"] * P["B_K"] * a),
                                            t0=t1, vb=P["B_VALID_JAM"] * 4, hb=P["B_HOLD_JAM"] * 4, rsi=None, vr=float(vr)))
        for o in sorted(new, key=lambda o: self.rank[o["c"]]):
            active = {x["c"] for x in self.live("pend", "open")}
            ok = o["c"] not in active and len(self.live("pend")) < P["PEND"] and len(self.live("open")) < P["CAP"]
            o.update(st="pend", live="pend" if ok else "none")
            orders.append(o)
            if ok: self.notify("order", o, t1)
        # bersihkan order selesai (simpan seperlunya)
        self.s["orders"] = [o for o in orders if o["st"] != "done" or o["live"] in ("open", "pend")]


# ======================================================================= data live
def fetch_15m(coin, n=1000):
    import signal_bot as sb
    d = sb.http_json(f"https://data-api.binance.vision/api/v3/klines?symbol={coin}USDT&interval=15m&limit={n}")
    now_ms = time.time() * 1000
    closed = [[k[0] // 1000, float(k[1]), float(k[2]), float(k[3]), float(k[4])] for k in d if k[6] < now_ms]
    cur_open = next((float(k[1]) for k in d if k[6] >= now_ms), None)       # open candle berjalan (harga 07:00 untuk modul B)
    return closed, (d[-1][0] // 1000 if d else None), cur_open

def fetch_1h(coin, n=1000):
    import signal_bot as sb
    d = sb.http_json(f"https://data-api.binance.vision/api/v3/klines?symbol={coin}USDT&interval=1h&limit={n}")
    now_ms = time.time() * 1000
    return [[k[0] // 1000, float(k[1]), float(k[2]), float(k[3]), float(k[4]), k[6]] for k in d if k[6] < now_ms]

def h1_info_fn(G, btc, o_px_fn):
    """Fungsi info modul B di waktu t1 (00:00 UTC): pakai candle H1 yang open t1-3600 (close 07:00 WIB)."""
    gix = {int(x): k for k, x in enumerate(G["T"])}
    bix = {int(x): k for k, x in enumerate(btc["T"])}
    def f(t1):
        k = gix.get(t1 - 3600); kb = bix.get(t1 - 3600)
        if k is None or k < 400 or kb is None: return None
        a = float(G["A"][k]); vr = a / float(np.mean(G["A"][k - 336:k]))
        o_px = o_px_fn(t1)
        if o_px is None: return None
        return (a, vr, int(G["reg"][k]), int(btc["reg"][kb]), float(o_px), a / float(G["C"][k]))
    return f


# ======================================================================= pesan Telegram
LINE = "────────────────────"
TAG = "🟠 <b>INTRADAY</b>"
MOD = {"A": "Dip 15m", "B": "Sinyal pagi"}

BULAN = ["", "Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]

def wib(ts, fmt="%d %b %H:%M"):
    w = dt.datetime.fromtimestamp(ts, dt.timezone.utc) + dt.timedelta(hours=7)
    return w.strftime(fmt.replace("%b", BULAN[w.month])) + " WIB"

def build_messages(ev, s, now, fmt, prices):
    """ev: list (jenis, order, t, alasan). Return list teks pesan untuk channel."""
    import html
    pre = lambda rows: "<pre>" + html.escape("\n".join(rows)) + "</pre>"
    side = lambda o: ("BUY" if o["d"] == 1 else "SELL")
    out = []
    orders = [e for e in ev if e[0] == "order"]
    if orders:
        L = [f"{TAG} · <b>SINYAL BARU</b>", wib(now, "%d %b %Y · %H:%M"), LINE,
             "Pasang LIMIT order + SL. Order otomatis batal jika belum terisi sampai batas waktu."]
        rows = []
        for _, o, t, _ in orders:
            e = o["lim"]; sl = e - o["d"] * o["r0"]
            rows += [f"{o['c']}USDT  {side(o)} LIMIT  · {MOD[o['m']]}",
                     f"   Entry : {fmt(e)}",
                     f"   SL    : {fmt(sl)}  ({abs(e - sl) / e * 100:.2f}%)"]
            if o["tp"] is not None:
                rows.append(f"   TP    : {fmt(o['tp'])}  ({abs(o['tp'] - e) / e * 100:.2f}%)")
            else:
                rows.append(f"   TP    : tunggu perintah TUTUP dari bot")
            import signal_bot as sb
            rows += [f"   Lev   : maks {sb.safe_lev(e, sl)}x",
                     f"   Berlaku s.d. {wib(o['t0'] + o['vb'] * STEP, '%H:%M')}",
                     f"   Hold maks {o['hb'] // 4} jam", ""]
        L.append(pre(rows[:-1])); out.append("\n".join(L))
    upd = [e for e in ev if e[0] in ("fill", "exit", "cancel", "expire")]
    if upd:
        L = [f"{TAG} · <b>UPDATE</b>", wib(now, "%d %b %Y · %H:%M"), LINE]
        f_ = [e for e in upd if e[0] == "fill"]
        x_ = [e for e in upd if e[0] == "exit"]
        c_ = [e for e in upd if e[0] in ("cancel", "expire")]
        if f_:
            L += ["", "<b>ORDER TERISI</b>", "Pastikan SL terpasang" + (" dan TP." if any(o["tp"] is not None for _, o, _, _ in f_) else ".")]
            rows = []
            for _, o, t, _ in f_:
                rows += [f"{o['c']}USDT  {side(o)}  · {MOD[o['m']]}", f"   Entry : {fmt(o['fill'])}", f"   SL    : {fmt(o['sl'])}"]
                rows += [f"   TP    : {fmt(o['tp'])}"] if o["tp"] is not None else [f"   Tutup : saat perintah TUTUP / maks {wib(o['t_fill'] + o['hb'] * STEP, '%H:%M')}"]
                rows.append("")
            L.append(pre(rows[:-1]))
        manual = [e for e in x_ if e[1]["why"] in ("RSI", "WAKTU")]
        auto = [e for e in x_ if e[1]["why"] in ("TP", "SL")]
        if manual:
            L += ["", "<b>⚡ TUTUP SEKARANG (market)</b>", "Tutup posisi di harga pasar dan hapus SL/TP-nya."]
            rows = []
            for _, o, t, _ in manual:
                why = "target tercapai (RSI pulih)" if o["why"] == "RSI" else "batas waktu hold"
                rows += [f"{o['c']}USDT  {side(o)}", f"   Harga : {fmt(o['exit'])}", f"   Hasil : {o['R_gross']:+.2f}R", f"   Alasan: {why}", ""]
            L.append(pre(rows[:-1]))
        if auto:
            L += ["", "<b>POSISI SELESAI</b>"]
            rows = []
            for _, o, t, _ in auto:
                rows += [f"{o['c']}USDT  {side(o)}  · {'✅ TP' if o['why'] == 'TP' else '❌ SL'}",
                         f"   Entry : {fmt(o['fill'])}", f"   Keluar: {fmt(o['exit'])}", f"   Hasil : {o['R_gross']:+.2f}R", ""]
            L.append(pre(rows[:-1]))
        if c_:
            L += ["", "<b>BATALKAN ORDER</b>", "Hapus limit order ini di exchange."]
            L.append(pre([f"{o['c']}USDT  {('kadaluarsa' if k == 'expire' else why)}" for k, o, t, why in c_]))
        if L[3] == "": del L[3]
        out.append("\n".join(L))
    return out

def build_digest(s, now, fmt, prices):
    import html
    pre = lambda rows: "<pre>" + html.escape("\n".join(rows)) + "</pre>"
    pos = [o for o in s["orders"] if o["live"] == "open"]
    pend = [o for o in s["orders"] if o["live"] == "pend"]
    L = [f"{TAG} · <b>RINGKASAN 2 JAM</b>", wib(now, "%d %b %Y · %H:%M"), LINE]
    if pos:
        tot = 0.0; rows = []
        for o in pos:
            px = prices.get(o["c"]); R = o["d"] * (px - o["fill"]) / o["r0"] if px else 0.0; tot += R
            rows += [f"{o['c']}USDT  {'BUY' if o['d'] == 1 else 'SELL'}  · {MOD[o['m']]}", f"   Entry : {fmt(o['fill'])}",
                     f"   Kini  : {fmt(px) if px else '-'}  ({R:+.2f}R)", f"   SL    : {fmt(o['sl'])}"]
            rows += [f"   TP    : {fmt(o['tp'])}"] if o["tp"] is not None else []
            rows += [f"   Maks  : {wib(o['t_fill'] + o['hb'] * STEP, '%H:%M')}", ""]
        L += [f"<b>POSISI TERBUKA</b> ({len(pos)}/{bi.PARAM['CAP']}) · berjalan <b>{tot:+.2f}R</b>", pre(rows[:-1])]
    else:
        L.append("Tidak ada posisi terbuka.")
    if pend:
        rows = [f"{o['c']}USDT  {'BUY' if o['d'] == 1 else 'SELL'} LIMIT {fmt(o['lim'])} · s.d. {wib(o['t0'] + o['vb'] * STEP, '%H:%M')}" for o in pend]
        L += ["", f"<b>ORDER MENUNGGU</b> ({len(pend)})", pre(rows)]
    today = (dt.datetime.fromtimestamp(now, dt.timezone.utc) + dt.timedelta(hours=7)).date()
    done = [h for h in s.get("hist", []) if (dt.datetime.fromtimestamp(h[4], dt.timezone.utc) + dt.timedelta(hours=7)).date() == today]
    if done:
        Rg = [h[9] for h in done]
        L += ["", f"Hari ini: {len(done)} trade selesai · {sum(r > 0 for r in Rg)} untung · total <b>{sum(Rg):+.2f}R</b>"]
    return "\n".join(L)


# ======================================================================= rekap & cek kesehatan
def _recap_state(s, net=False):
    """Format hist intraday -> format rekap bersama [koin, arah, t_buka, t_tutup, entry, exit, R].
    net=False: R kotor (sama dengan angka di pesan channel). net=True: R bersih (dibanding backtest)."""
    return {"hist": [[h[0], h[2], h[3], h[4], h[5], h[6], h[7] if net else h[9]] for h in s.get("hist", [])], "coins": {}}

def send_recaps(s, target, risk_pct):
    import commands, kesehatan, signal_bot as sb
    now_wib = dt.datetime.now(commands.WIB)
    rec, net = _recap_state(s), _recap_state(s, net=True)
    def health(start, end, jenis):
        per = [h[6] for h in net["hist"] if start.timestamp() <= h[3] < end.timestamp()]
        last = end - dt.timedelta(days=1)
        judul = f"{jenis} {start:%d %b} - {last:%d %b %Y}" if jenis == "Minggu" else f"{jenis} {start:%B %Y}"
        txt = kesehatan.build("intraday", net["hist"], None, judul, per)
        if txt: sb.tg_send("🟠 " + txt)
    wk, _ = commands.period_bounds("minggu", now_wib, previous=True)
    if now_wib.weekday() == 0 and s.get("recap_week") != wk.isoformat():
        sb.tg_send(f"{TAG}\n" + commands.build_recap(rec, "minggu", True, risk_pct, now_wib, sb.fmt), chat=target)
        s["recap_week"] = wk.isoformat(); health(wk, wk + dt.timedelta(days=7), "Minggu")
    mo, _ = commands.period_bounds("bulan", now_wib, previous=True)
    if now_wib.day == 1 and s.get("recap_month") != mo.isoformat():
        sb.tg_send(f"{TAG}\n" + commands.build_recap(rec, "bulan", True, risk_pct, now_wib, sb.fmt), chat=target)
        s["recap_month"] = mo.isoformat(); health(mo, commands.period_bounds("bulan", now_wib)[0], "Bulan")


# ======================================================================= main
def main():
    import signal_bot as sb, jurnal
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
    P = dict(bi.PARAM)
    risk_pct = float(os.environ.get("INTRADAY_RISK_PCT") or 1)
    modal = float(os.environ.get("MODAL_USDT") or 0)
    s = json.load(open(STATE_FILE)) if os.path.exists(STATE_FILE) else {"last_t": 0}
    latest_closed = (int(time.time()) // STEP) * STEP - STEP
    if s.get("last_t", 0) >= latest_closed and os.environ.get("FORCE") != "1":
        print("Candle 15m terakhir sudah diproses."); return

    coins = sb.COINS
    def load15(c):
        try: return c, fetch_15m(c)
        except Exception as e: return c, None
    with ThreadPoolExecutor(8) as ex: raw = dict(ex.map(load15, coins))
    data, errors, cur_open = {}, [], {}
    for c, r in raw.items():
        if not r or len(r[0]) < 900: errors.append(c); continue
        D = bi.prep(r[0]); D["ix"] = {int(t): k for k, t in enumerate(D["T"])}; data[c] = D
        if r[2] is not None and r[1] is not None: cur_open[(c, r[1])] = r[2]
    if not data:
        sb.tg_send("⚠️ Bot intraday gagal mengambil data harga."); sys.exit(1)
    newest = max(int(D["T"][-1]) for D in data.values())
    start = s["last_t"] + STEP if s.get("last_t") else newest
    times = list(range(start, newest + STEP, STEP))
    # modul B: data H1 hanya saat ada batas 07:00 WIB di rentang candle yang diproses
    if any((t + STEP) % 86400 == 0 for t in times):
        def load1h(c):
            try: return c, bi.prep(fetch_1h(c))
            except Exception: return c, None
        with ThreadPoolExecutor(8) as ex: H = {c: g for c, g in ex.map(load1h, coins) if g is not None and len(g["T"]) > 400}
        if "BTC" in H:
            for c, D in data.items():
                if c in H:
                    def o_px(t1, c=c, D=D):
                        k = D["ix"].get(t1)
                        return float(D["O"][k]) if k is not None else cur_open.get((c, t1))
                    D["h1"] = h1_info_fn(H[c], H["BTC"], o_px)
    ev = []
    eng = Engine(s, P, coins, lambda kind, o, t, why="": ev.append((kind, o, t, why)), funding_fn=sb.fetch_funding_avg)
    for t in times: eng.step(t, data)
    s["last_t"] = newest
    prices = {c: float(D["C"][-1]) for c, D in data.items()}
    for k, o, t, why in ev:            # Lapis 1: jurnal trade selesai
        if k == "exit":
            jurnal.append("intraday", dict(sym=o["c"] + "USDT", modul=o["m"], d=o["d"], t0=o["t_fill"], t1=o["t_exit"], entry=o["fill"],
                                           exit=o["exit"], R=round(o["R"], 3), R_kotor=round(o["R_gross"], 3), alasan=o["why"], versi=VERSI))
    now = time.time()
    target = None
    try: target = json.load(open(os.path.join(HERE, "state.json"))).get("channel_id")   # channel yang sama dengan bot swing
    except Exception: pass
    for msg in build_messages(ev, s, now, sb.fmt, prices):
        sb.tg_send(msg, chat=target)
    # ringkasan tiap 2 jam (jam genap WIB), sekali per jendela
    w = dt.datetime.fromtimestamp(now, dt.timezone.utc) + dt.timedelta(hours=7)
    key = f"{w:%Y-%m-%d}-{w.hour // 2}"
    if s.get("digest") != key:
        sb.tg_send(build_digest(s, now, sb.fmt, prices), chat=target); s["digest"] = key
    # Rekap otomatis ke channel (mingguan setiap Senin, bulanan tanggal 1) + cek kesehatan ke chat pribadi (Lapis 2)
    try:
        send_recaps(s, target, risk_pct)
    except Exception as e:
        print("Rekap/cek kesehatan gagal:", e)
    # ukuran posisi pribadi pemilik
    if modal:
        priv = []
        for k, o, t, _ in ev:
            if k == "order":
                risk = modal * risk_pct / 100; qty = risk / o["r0"]
                priv.append(f"• {o['c']}USDT {'BUY' if o['d'] == 1 else 'SELL'} LIMIT {sb.fmt(o['lim'])}: ±{qty:.6g} koin (±{qty * o['lim']:,.0f} USDT, risiko {risk:,.2f} USDT)")
        if priv: sb.tg_send(f"🔒 🟠 <b>Ukuran posisi intraday</b> (modal {modal:,.0f} USDT, risiko {risk_pct}%)\n" + "\n".join(priv))
    if errors: print("Data gagal:", ", ".join(errors))
    json.dump(s, open(STATE_FILE, "w"), indent=1)
    print(f"candle {wib(times[0])} s.d. {wib(times[-1])} · kejadian {len(ev)} · posisi {len(eng.live('open'))} · order {len(eng.live('pend'))}")

if __name__ == "__main__":
    main()
