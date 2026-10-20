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
from signal_bot import tg_send, http_json, atr, upcoming_news          # pakai fungsi yang sama dengan bot crypto
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
        self.notify("exit", d=d, entry=e, exit=ex, R=R, t0=t0, t=t1, why=why, r0=r0)

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


# Templat pesan ada di gold_templates.py


# ---------------------------------------------------------------- main
def send_health(state, start, end, jenis):
    """Lapis 2: cek kesehatan strategi XAU ke chat pribadi pemilik (bukan channel)."""
    try:
        import kesehatan
        hist = state.get("hist", [])
        per = [h[6] for h in hist if start.timestamp() <= h[3] < end.timestamp()]
        last = end - dt.timedelta(days=1)
        judul = f"{jenis} {start:%d %b} - {last:%d %b %Y}" if jenis == "Minggu" else f"{jenis} {start:%B %Y}"
        txt = kesehatan.build("xau", hist, None, judul, per)
        if txt:
            tg_send(txt)
    except Exception as e:
        print("Cek kesehatan gagal:", e)


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
    import gold_templates as gt
    ev = gt.new_events()
    base_notify = gt.make_notifier(ev)
    import jurnal
    T_, H_, L_ = [r[0] for r in rows], [r[2] for r in rows], [r[3] for r in rows]
    def notify(kind, **k):
        if kind == "order":   # faktor saat order dipasang (dipakai riset)
            p = k["pend"]; a = abs(p["buy"][0] - p["buy"][1]) / SL_ATR
            state["feat"] = dict(range=round(p["hi"] - p["lo"], 3), atr=round(a, 3),
                                 range_atr=round((p["hi"] - p["lo"]) / a, 3) if a else None,
                                 hari=dt.datetime.fromtimestamp(p["t"], commands.WIB).strftime("%a"))
        if kind == "exit":    # Lapis 1: catat trade selesai ke jurnal
            r0 = k.get("r0")
            try:
                mfe, mae = jurnal.mfe_mae(T_, H_, L_, k["t0"], k["t"], k["d"], k["entry"], r0)
                jurnal.append("xau", dict(sym=SYM, d=k["d"], t0=k["t0"], t1=k["t"], entry=k["entry"], exit=k["exit"],
                                          R=round(k["R"], 3), alasan=k.get("why"), r0=round(r0, 3) if r0 else None,
                                          mfe=mfe, mae=mae, **(state.get("feat") or {})))
            except Exception as e:
                print("Jurnal gagal ditulis:", e)
        base_notify(kind, **k)
    eng = GoldEngine(state, notify)
    px = eng.run(rows, since)
    t_last = rows[-1][0] + 3600
    # Maksimal 2 bubble: (1) SINYAL order/pembatalan, (2) UPDATE terisi/ditutup/posisi berjalan
    buf = []
    # Peringatan news: event USD berdampak tinggi dalam 3 jam ke depan dan sebelum tutup 23:00 WIB
    # (setelah itu bot tidak punya posisi/order). Dikirim sekali per event, sebelum bubble lain.
    now = time.time()
    w = dt.datetime.fromtimestamp(now, dt.timezone.utc) + dt.timedelta(hours=7)
    close_ts = (w.replace(hour=23, minute=0, second=0, microsecond=0) - dt.timedelta(hours=7)).replace(tzinfo=dt.timezone.utc).timestamp()
    sent = state.get("news_sent", [])
    news = [n for n in upcoming_news(now) if n[0] <= close_ts and f"{n[0]}|{n[1]}" not in sent]
    if news:
        nb = gt.news_bubble(news, state.get("pos"), state.get("pend"), px, now)
        buf.append(nb)
        tg_send(nb, chat=target)
        state["news_sent"] = (sent + [f"{n[0]}|{n[1]}" for n in news])[-50:]
    for b in (gt.signal_bubble(ev, t_last, risk_pct, live_px=px if state.get("pend") else None),
              gt.update_bubble(ev, state.get("pos"), px, t_last) if state.get("last_ts", 0) > since or ev["fill"] or ev["exit"] else None):
        if b:
            buf.append(b)
            tg_send(b, chat=target)
    # rekap otomatis mingguan: Jumat malam setelah candle tutup 23:00 WIB diproses (hasil Senin-Jumat lengkap).
    # Cadangan: jika rekap Jumat terlewat, dikirim di run pertama hari Senin. Bulanan tetap tanggal 1.
    now_wib = dt.datetime.now(commands.WIB)
    wk, _ = commands.period_bounds("minggu", now_wib, previous=True)        # minggu lalu
    this_wk, _ = commands.period_bounds("minggu", now_wib)                   # minggu ini
    fri_close = this_wk + dt.timedelta(days=4, hours=22)                     # candle Jumat 22:00-23:00 WIB
    if (now_wib.weekday() == 4 and state.get("last_ts", 0) >= fri_close.timestamp()
            and state.get("recap_week") != this_wk.isoformat()):
        # now = Senin depan + previous=True -> periode minggu ini, tanpa label "(berjalan)"
        tg_send(commands.build_recap(state, "minggu", True, risk_pct, now_wib + dt.timedelta(days=3), fmt).replace("REKAP", "REKAP XAU"), chat=target)
        state["recap_week"] = this_wk.isoformat()
        send_health(state, this_wk, this_wk + dt.timedelta(days=7), "Minggu")
    elif now_wib.weekday() == 0 and state.get("recap_week") != wk.isoformat():
        tg_send(commands.build_recap(state, "minggu", True, risk_pct, now_wib, fmt).replace("REKAP", "REKAP XAU"), chat=target)
        state["recap_week"] = wk.isoformat()
        send_health(state, wk, wk + dt.timedelta(days=7), "Minggu")
    mo, _ = commands.period_bounds("bulan", now_wib, previous=True)
    # bot XAU hanya jalan Senin-Jumat: jika tanggal 1 jatuh di akhir pekan, rekap bulanan dikirim di run pertama bulan itu
    if now_wib.day <= 3 and state.get("recap_month") != mo.isoformat():
        tg_send(commands.build_recap(state, "bulan", True, risk_pct, now_wib, fmt).replace("REKAP", "REKAP XAU"), chat=target)
        state["recap_month"] = mo.isoformat()
        send_health(state, mo, commands.period_bounds("bulan", now_wib)[0], "Bulan")
    json.dump(state, open(STATE_FILE, "w"), indent=1)
    print(*buf, sep="\n\n")


if __name__ == "__main__":
    main()
