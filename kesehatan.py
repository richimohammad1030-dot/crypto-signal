"""Lapis 2 - cek kesehatan strategi.
Membandingkan hasil live (catatan bot) dengan rentang normal dari backtest (baseline.json).
Pesan dikirim ke chat pribadi pemilik saja, bukan ke channel."""
import datetime as dt, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
WIB = dt.timezone(dt.timedelta(hours=7))
LINE = "────────────────────"
LIVE_START = {"crypto": dt.datetime(2026, 10, 24, tzinfo=WIB).timestamp(),   # versi v2 (stagnan + TP 25%) mulai 24 Okt 2026
              "xau": dt.datetime(2026, 10, 18, tzinfo=WIB).timestamp(),
              "intraday": dt.datetime(2026, 10, 30, 16, 0, tzinfo=WIB).timestamp()}   # juara v3 live 30 Okt 2026
MIN_LABEL = 20          # minimal trade per label sebelum perbandingan label dinilai


def _stats(R):
    if not R:
        return dict(n=0, cum=0.0, wr=0.0, dd=0.0, streak=0)
    c = peak = dd = 0.0; s = best = 0
    for r in R:
        c += r; peak = max(peak, c); dd = max(dd, peak - c)
        s = s + 1 if r <= 0 else 0; best = max(best, s)
    return dict(n=len(R), cum=c, wr=sum(r > 0 for r in R) / len(R) * 100, dd=dd, streak=best)


def _band(base, n):
    """Rentang normal untuk n trade: interpolasi linier antar titik patokan terdekat."""
    keys = sorted(int(k) for k in base["band"])
    n = min(max(n, keys[0]), keys[-1])
    lo = max(k for k in keys if k <= n); hi = min(k for k in keys if k >= n)
    A, B = base["band"][str(lo)], base["band"][str(hi)]
    w = 0 if hi == lo else (n - lo) / (hi - lo)
    mix = lambda x, y: [a + (b - a) * w for a, b in zip(x, y)]
    return n, {key: mix(A[key], B[key]) for key in A}


def build(bot, hist, labels=None, judul_periode="", periode_R=None, now=None):
    """hist: list [sym, d, t0, t1, entry, exit, R] (state['hist']). labels: {(sym, t0): 'HIGH'|...}.
    periode_R: list R untuk periode laporan (minggu/bulan). Return teks HTML Telegram atau None jika baseline belum ada."""
    try:
        base = json.load(open(os.path.join(HERE, "baseline.json")))[bot]
    except Exception:
        return None
    now = now or dt.datetime.now(WIB)
    live = sorted([h for h in hist if h[3] >= LIVE_START[bot]], key=lambda h: h[3])
    R = [h[6] for h in live]
    s = _stats(R)
    nama = {"crypto": "CRYPTO SWING", "xau": "XAU", "intraday": "CRYPTO INTRADAY"}.get(bot, bot.upper())
    L = [f"<b>CEK KESEHATAN {nama}</b>", judul_periode or now.strftime("%d %b %Y"), LINE]
    if periode_R is not None:
        L.append(f"Trade selesai periode ini: <b>{len(periode_R)}</b> · hasil <b>{sum(periode_R):+.2f}R</b>")
    L.append(f"Total sejak live: <b>{s['n']}</b> trade · <b>{s['cum']:+.2f}R</b>")
    status, notes = "NORMAL", []
    if s["n"] == 0:
        L += ["", "Belum ada trade selesai. Status belum bisa dinilai."]
        return "\n".join(L)
    k, b = _band(base, s["n"])
    rows = []
    def chk(name, val, txt, lo=None, hi=None, hard=None):
        nonlocal status
        st = "OK"
        if hard is not None and hard[0](val):
            st = "WASPADA"; status = "WASPADA"
        elif (lo is not None and val < lo) or (hi is not None and val > hi):
            st = "PANTAU"
            if status == "NORMAL":
                status = "PERHATIKAN"
        rows.append(f"{name:<9}{txt}  {st}")
    cum = b["cum"]
    col = lambda v, r: f"{v:>7}  {r:<12}"
    chk("Hasil", s["cum"], col(f"{s['cum']:+.1f}R", f"{cum[1]:+.1f}..{cum[3]:+.1f}"), lo=cum[1], hard=(lambda v: v < cum[0],))
    chk("Win rate", s["wr"], col(f"{s['wr']:.0f}%", f"{b['wr'][0]:.0f}..{b['wr'][1]:.0f}%"), lo=b["wr"][0], hi=b["wr"][1] if s["n"] >= 30 else None)
    chk("Drawdown", s["dd"], col(f"{s['dd']:.1f}R", f"maks {b['dd'][0]:.1f}"), hi=b["dd"][0],
        hard=(lambda v: v > max(b["dd"][1], base["maxdd"]),))
    chk("Loss run", s["streak"], col(f"{s['streak']}", f"maks {b['streak'][0]:.0f}"), hi=b["streak"][0],
        hard=(lambda v: v > max(b["streak"][1], base["streak"]),))
    L += ["", f"<b>DIBANDING BACKTEST</b>", LINE, f"Rentang normal untuk {k} trade:",
          "<pre>" + f"{'':<9}{'Live':>7}  {'Normal':<12}" + "\n" + "\n".join(rows) + "</pre>"]
    if bot == "crypto" and labels:
        by = {}
        for h in live:
            lab = labels.get((h[0] if h[0].endswith("USDT") else h[0] + "USDT", h[2]))
            if lab:
                by.setdefault(lab, []).append(h[6])
        if all(len(by.get(x, [])) >= MIN_LABEL for x in ("HIGH", "LOW")):
            hi, lo = sum(by["HIGH"]) / len(by["HIGH"]), sum(by["LOW"]) / len(by["LOW"])
            L.append(f"High vs Low: {hi:+.2f}R vs {lo:+.2f}R per trade" + ("" if hi > lo else "  PERHATIKAN"))
        else:
            L.append(f"High vs Low: belum cukup data (min {MIN_LABEL} trade per label)")
    if s["n"] < 10:
        notes.append("Data masih sedikit, status masih kasar.")
    msg = {"NORMAL": "Hasil masih dalam rentang wajar strategi.",
           "PERHATIKAN": "Ada angka di tepi rentang normal. Pantau, belum perlu tindakan.",
           "WASPADA": "Hasil di luar rentang terburuk backtest. Pertimbangkan mengurangi risiko sambil menunggu review."}[status]
    L += ["", f"Status: <b>{status}</b>", msg] + notes
    return "\n".join(L)
