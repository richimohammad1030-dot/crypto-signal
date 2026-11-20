"""Backtest bot FX MAJOR (EURUSD, GBPUSD, USDJPY, AUDUSD) di data H1 BID (Dukascopy).
Aturan tetap (pemilik, 20 Nov 2026): intraday, sinyal pagi 07:00 WIB (+ sinyal susulan), semua ditutup 23:00 WIB,
risiko 0,5%/trade, maks 4 posisi/hari, maks 1 posisi/pair/hari, maks 2 posisi searah USD/hari.
Waktu: WIB = UTC+7. Hari trading = 00:00-16:00 UTC (07:00-23:00 WIB).
Biaya: spread konservatif dikurangkan dari tiap trade (dalam R). SL & TP di candle yang sama -> dianggap SL.
Pemakaian: python forex_major/backtest.py [strategi ...]   (tanpa argumen = semua)"""
import gzip, glob, json, os, sys, math, time
import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
PAIRS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]
PIP = {"EURUSD": 1e-4, "GBPUSD": 1e-4, "USDJPY": 1e-2, "AUDUSD": 1e-4}
SPREAD = {"EURUSD": 1.5, "GBPUSD": 2.0, "USDJPY": 1.5, "AUDUSD": 1.8}     # pip, konservatif
RISK = 0.005; MAX_DAY = 4; MAX_USD_SAME = 2
DAY_END = 16 * 3600                                                     # 23:00 WIB


def usd_dir(pair, side):           # +1 = long USD
    return side if pair.startswith("USD") else -side


# ---------------- data ----------------
class Pair:
    def __init__(self, name, rows):
        a = np.asarray(rows, dtype=float)
        self.name = name; self.t = a[:, 0].astype(np.int64); self.o, self.h, self.l, self.c = a[:, 1], a[:, 2], a[:, 3], a[:, 4]
        self.pip = PIP[name]; self.spread = SPREAD[name] * PIP[name]
        day = self.t // 86400
        self.days, self.day_start = np.unique(day, return_index=True)
        self.day_end = np.append(self.day_start[1:], len(self.t))
        self.d1 = self._agg(86400); self.h1 = self._agg(3600); self.h4 = self._agg(14400)

    def _agg(self, sec):
        k = self.t // sec; u, s = np.unique(k, return_index=True); e = np.append(s[1:], len(k))
        return dict(t=u * sec, o=self.o[s], h=np.maximum.reduceat(self.h, s), l=np.minimum.reduceat(self.l, s), c=self.c[e - 1])

    def day_slice(self, d):
        i = np.searchsorted(self.days, d)
        if i >= len(self.days) or self.days[i] != d: return None
        return self.day_start[i], self.day_end[i]


def load(pair):
    rows = []
    for f in sorted(glob.glob(f"{ROOT}/data/{pair}_h1_*.json.gz")):
        rows += json.load(gzip.open(f, "rt"))
    return Pair(pair, rows) if rows else None


# ---------------- indikator ----------------
def ema(x, n):
    out = np.empty_like(x); a = 2 / (n + 1); out[0] = x[0]
    for i in range(1, len(x)): out[i] = a * x[i] + (1 - a) * out[i - 1]
    return out

def sma(x, n):
    c = np.cumsum(np.insert(x, 0, 0.0)); out = np.full(len(x), np.nan); out[n - 1:] = (c[n:] - c[:-n]) / n; return out

def std(x, n):
    out = np.full(len(x), np.nan)
    if len(x) >= n:
        w = np.lib.stride_tricks.sliding_window_view(x, n); out[n - 1:] = w.std(axis=1)
    return out

def atr(b, n=14):
    pc = np.insert(b["c"][:-1], 0, b["c"][0])
    tr = np.maximum(b["h"] - b["l"], np.maximum(abs(b["h"] - pc), abs(b["l"] - pc)))
    out = np.empty_like(tr); out[0] = tr[0]
    for i in range(1, len(tr)): out[i] = out[i - 1] + (tr[i] - out[i - 1]) / n
    return out

def rsi(x, n):
    d = np.diff(x, prepend=x[0]); up = np.where(d > 0, d, 0.0); dn = np.where(d < 0, -d, 0.0)
    au = np.empty_like(x); ad = np.empty_like(x); au[0] = ad[0] = 1e-12
    for i in range(1, len(x)):
        au[i] = au[i - 1] + (up[i] - au[i - 1]) / n; ad[i] = ad[i - 1] + (dn[i] - ad[i - 1]) / n
    return 100 - 100 / (1 + au / np.maximum(ad, 1e-12))


# ---------------- order & simulasi ----------------
def order(pair, strat, side, kind, price, sl, tp, t_on, oco=None, t_off=None):
    return dict(pair=pair, strat=strat, side=side, kind=kind, price=price, sl=sl, tp=tp, t_on=t_on, oco=oco, t_off=t_off)


def simulate_pair(P, orders, d):
    """Simulasi order satu pair satu hari. Kembalikan daftar trade (waktu isi, ...)."""
    sl_ = P.day_slice(d)
    if sl_ is None: return []
    s, e = sl_; end = d * 86400 + DAY_END
    trades = []; dead = set()
    for od in sorted(orders, key=lambda x: x["t_on"]):
        key = od["oco"]
        if key is not None and key in dead: continue
        risk = abs(od["price"] - od["sl"]) if od["kind"] != "market" else None
        filled = None; t_off = min(od["t_off"] or end, end)
        i0 = s + np.searchsorted(P.t[s:e], od["t_on"])
        for i in range(i0, e):
            if P.t[i] >= t_off: break
            side = od["side"]
            if od["kind"] == "market":
                px = P.o[i]; filled = (i, px); break
            if od["kind"] == "stop":
                if (side > 0 and P.h[i] >= od["price"]) or (side < 0 and P.l[i] <= od["price"]):
                    px = max(od["price"], P.o[i]) if side > 0 else min(od["price"], P.o[i]); filled = (i, px); break
            else:  # limit
                if (side > 0 and P.l[i] <= od["price"]) or (side < 0 and P.h[i] >= od["price"]):
                    px = min(od["price"], P.o[i]) if side > 0 else max(od["price"], P.o[i]); filled = (i, px); break
        if filled is None: continue
        if key is not None:
            # OCO: kaki lain hanya batal bila kaki ini terisi lebih dulu
            others = [x for x in orders if x is not od and x["oco"] == key]
            dead.add(key)
            # cek apakah kaki lain sebenarnya terisi lebih awal -> dihitung di iterasi lain; sederhana: pilih yang terisi duluan
            for x in others:
                fx = first_fill(P, x, s, e, min(x["t_off"] or end, end))
                if fx is not None and fx < filled[0]:
                    od = x; filled = (fx, fill_price(P, x, fx)); break
        i, px = filled; side = od["side"]; sl, tp = od["sl"], od["tp"]
        if od["kind"] == "market":
            # SL/TP relatif ditentukan strategi sebagai jarak bila market
            pass
        risk = abs(px - sl)
        if risk <= 0: continue
        exit_px, exit_i, why = None, None, "close"
        for j in range(i, e):
            if P.t[j] >= end: break
            hit_sl = (P.l[j] <= sl) if side > 0 else (P.h[j] >= sl)
            hit_tp = (P.h[j] >= tp) if side > 0 else (P.l[j] <= tp)
            if j == i and od["kind"] != "market":
                # candle pengisian: hanya SL yang dihitung (konservatif)
                hit_tp = hit_tp and not hit_sl and ((P.c[j] >= tp) if side > 0 else (P.c[j] <= tp))
            if hit_sl: exit_px, exit_i, why = sl, j, "sl"; break
            if hit_tp: exit_px, exit_i, why = tp, j, "tp"; break
            exit_i = j
        if exit_px is None: exit_px = P.c[exit_i]
        R = side * (exit_px - px) / risk - P.spread / risk
        trades.append(dict(t=int(P.t[i]), pair=P.name, strat=od["strat"], side=side, R=R, why=why, risk_pips=risk / P.pip))
    return trades


def first_fill(P, od, s, e, t_off):
    i0 = s + np.searchsorted(P.t[s:e], od["t_on"])
    for i in range(i0, e):
        if P.t[i] >= t_off: return None
        if od["kind"] == "market": return i
        if od["kind"] == "stop" and ((od["side"] > 0 and P.h[i] >= od["price"]) or (od["side"] < 0 and P.l[i] <= od["price"])): return i
        if od["kind"] == "limit" and ((od["side"] > 0 and P.l[i] <= od["price"]) or (od["side"] < 0 and P.h[i] >= od["price"])): return i
    return None


def fill_price(P, od, i):
    if od["kind"] == "market": return P.o[i]
    if od["kind"] == "stop": return max(od["price"], P.o[i]) if od["side"] > 0 else min(od["price"], P.o[i])
    return min(od["price"], P.o[i]) if od["side"] > 0 else max(od["price"], P.o[i])


def portfolio(trades):
    """Terapkan batas: maks 4/hari, 1/pair/hari, 2 searah USD/hari (urut waktu isi)."""
    out = []; byday = {}
    for tr in sorted(trades, key=lambda x: x["t"]):
        d = tr["t"] // 86400; st = byday.setdefault(d, dict(n=0, pairs=set(), usd={1: 0, -1: 0}))
        u = usd_dir(tr["pair"], tr["side"])
        if st["n"] >= MAX_DAY or tr["pair"] in st["pairs"] or st["usd"][u] >= MAX_USD_SAME: continue
        st["n"] += 1; st["pairs"].add(tr["pair"]); st["usd"][u] += 1; out.append(tr)
    return out


def metrics(trades, n_days):
    if not trades: return dict(n=0)
    R = np.array([t["R"] for t in trades]); win = R > 0
    eq = np.cumsum(R); dd = float((np.maximum.accumulate(np.insert(eq, 0, 0))[1:] - eq).max())
    streak = cur = 0
    for w in win:
        cur = 0 if w else cur + 1; streak = max(streak, cur)
    wstreak = cur = 0
    for w in win:
        cur = cur + 1 if w else 0; wstreak = max(wstreak, cur)
    years = {}
    for t in trades:
        y = time.gmtime(t["t"]).tm_year; years[y] = years.get(y, 0) + t["R"]
    gp, gl = R[win].sum(), -R[~win].sum()
    eqm = 1.0
    for r in R: eqm *= 1 + RISK * r
    yrs = n_days / 365.2425
    return dict(n=len(R), wr=float(win.mean()), pf=float(gp / gl) if gl > 0 else float("inf"), totR=float(R.sum()),
                ddR=dd, lose_streak=streak, win_streak=wstreak, per_week=len(R) / (n_days / 7),
                cagr=float(eqm ** (1 / yrs) - 1) if yrs > 0 else 0, years={y: round(v, 1) for y, v in sorted(years.items())},
                pos_years=sum(v > 0 for v in years.values()), n_years=len(years))


# ---------------- strategi ----------------
# Tiap strategi: fungsi(P, ctx) -> dict hari -> [order]. Semua indikator hanya memakai bar yang sudah selesai.

def prev_daily(P):
    """Peta hari -> indeks D1 hari sebelumnya (bar lengkap terakhir sebelum 00:00 UTC hari itu)."""
    D = P.d1; dd = D["t"] // 86400
    return {int(d): i - 1 for i, d in enumerate(dd) if i > 0}, D


def s1_asian_breakout(P, tp_r=1.5, min_atr=0.15, max_atr=0.8):
    """Range Asia 00-07 UTC (07-14 WIB) -> stop order OCO di kedua sisi saat London buka; SL tengah range."""
    idx, D = prev_daily(P); A = atr(D); out = {}
    for d, j in idx.items():
        sl_ = P.day_slice(d)
        if sl_ is None or j < 20: continue
        s, e = sl_; t0 = d * 86400; m = (P.t[s:e] < t0 + 7 * 3600)
        if m.sum() < 5: continue
        hi, lo = P.h[s:e][m].max(), P.l[s:e][m].min(); rng = hi - lo
        if not (min_atr * A[j] <= rng <= max_atr * A[j]): continue
        mid = (hi + lo) / 2; buf = 2 * P.pip; on = t0 + 7 * 3600
        b = hi + buf; sl = mid; out[d] = [order(P.name, "S1", 1, "stop", b, sl, b + tp_r * (b - sl), on, oco=("S1", d), t_off=t0 + 12 * 3600)]
        s_ = lo - buf; out[d].append(order(P.name, "S1", -1, "stop", s_, mid, s_ - tp_r * (mid - s_), on, oco=("S1", d), t_off=t0 + 12 * 3600))
    return out


def s2_xau_adapt(P):
    """Adaptasi bot XAU: RSI2 harian ekstrem -> mean reversion (market 07:00 WIB); selain itu stop order searah EMA200 H1."""
    idx, D = prev_daily(P); A = atr(D); R2 = rsi(D["c"], 2); H = P.h1; E = ema(H["c"], 200); out = {}
    for d, j in idx.items():
        if j < 200: continue
        t0 = d * 86400; a = A[j]; hi = np.searchsorted(H["t"], t0) - 1
        if hi < 200: continue
        if R2[j] < 10 or R2[j] > 90:
            side = 1 if R2[j] < 10 else -1; px = D["c"][j]
            # market saat buka: SL/TP dari harga close kemarin sebagai acuan
            out[d] = [order(P.name, "S2", side, "limit" if side > 0 else "limit", px, px - side * 0.6 * a, px + side * 0.6 * a, t0)]
        else:
            side = 1 if H["c"][hi] > E[hi] else -1
            lv = D["h"][j] if side > 0 else D["l"][j]
            out[d] = [order(P.name, "S2", side, "stop", lv, lv - side * 0.5 * a, lv + side * 1.0 * a, t0)]
    return out


def s3_trinity(P):
    """Trinity H4: Inside Bar (stop di sisi mother bar, searah breakout) & Fakey (IB yang ditembus palsu lalu balik)."""
    H = P.h4; A = atr(H); out = {}
    tH = H["t"]
    for k in range(3, len(tH)):
        t_end = tH[k] + 14400; d = t_end // 86400
        if (t_end % 86400) >= DAY_END - 4 * 3600: continue
        m, ib = k - 1, k                                   # mother bar m, inside bar k
        if H["h"][ib] < H["h"][m] and H["l"][ib] > H["l"][m]:
            hi, lo = H["h"][m], H["l"][m]; r = hi - lo
            if r < 0.3 * A[k]: continue
            out.setdefault(d, [])
            out[d].append(order(P.name, "S3", 1, "stop", hi, lo + r * 0.5, hi + r, t_end, oco=("S3", int(tH[k])), t_off=t_end + 8 * 3600))
            out[d].append(order(P.name, "S3", -1, "stop", lo, hi - r * 0.5, lo - r, t_end, oco=("S3", int(tH[k])), t_off=t_end + 8 * 3600))
        # Fakey: k-2 mother, k-1 inside, bar k menembus satu sisi tapi tutup kembali di dalam mother
        mm, ii = k - 2, k - 1
        if H["h"][ii] < H["h"][mm] and H["l"][ii] > H["l"][mm]:
            if H["l"][k] < H["l"][ii] and H["c"][k] > H["l"][ii]:
                e_ = H["h"][k]; sl = H["l"][k]
                out.setdefault(d, []).append(order(P.name, "S3", 1, "stop", e_, sl, e_ + 2 * (e_ - sl), t_end, t_off=t_end + 8 * 3600))
            elif H["h"][k] > H["h"][ii] and H["c"][k] < H["h"][ii]:
                e_ = H["l"][k]; sl = H["h"][k]
                out.setdefault(d, []).append(order(P.name, "S3", -1, "stop", e_, sl, e_ - 2 * (sl - e_), t_end, t_off=t_end + 8 * 3600))
    return out


def s4_nr_orb(P, nr=4, stretch=0.3):
    """Crabel: hari kemarin NR4/NR7 -> ORB dari harga buka London (07 UTC) +- stretch*ATR, SL = sisi lawan."""
    idx, D = prev_daily(P); A = atr(D); rg = D["h"] - D["l"]; out = {}
    for d, j in idx.items():
        if j < 20 or rg[j] > rg[j - nr + 1:j + 1].min(): continue
        sl_ = P.day_slice(d)
        if sl_ is None: continue
        s, e = sl_; t0 = d * 86400; i = s + np.searchsorted(P.t[s:e], t0 + 7 * 3600)
        if i >= e: continue
        op = P.o[i]; k = stretch * A[j]
        out[d] = [order(P.name, "S4", 1, "stop", op + k, op - k * 0.5, op + k + 1.5 * k * 1.5, t0 + 7 * 3600, oco=("S4", d)),
                  order(P.name, "S4", -1, "stop", op - k, op + k * 0.5, op - k - 1.5 * k * 1.5, t0 + 7 * 3600, oco=("S4", d))]
    return out


def s5_turtle_soup(P):
    """Turtle Soup harian: harga tembus high/low kemarin (setelah 07 UTC) lalu balik -> stop order balik di level itu."""
    idx, D = prev_daily(P); A = atr(D); H = P.h1; out = {}
    for d, j in idx.items():
        if j < 20: continue
        t0 = d * 86400; a = A[j]; ph, pl = D["h"][j], D["l"][j]
        i0 = np.searchsorted(H["t"], t0 + 7 * 3600); i1 = np.searchsorted(H["t"], t0 + 13 * 3600)
        for i in range(i0, min(i1, len(H["t"]))):
            if H["h"][i] > ph + 0.1 * a and H["c"][i] < ph:
                ext = H["h"][max(i0 - 7, 0):i + 1].max()
                out.setdefault(d, []).append(order(P.name, "S5", -1, "stop", ph, ext + 0.05 * a, ph - 2 * (ext + 0.05 * a - ph), H["t"][i] + 3600, t_off=H["t"][i] + 4 * 3600)); break
            if H["l"][i] < pl - 0.1 * a and H["c"][i] > pl:
                ext = H["l"][max(i0 - 7, 0):i + 1].min()
                out.setdefault(d, []).append(order(P.name, "S5", 1, "stop", pl, ext - 0.05 * a, pl + 2 * (pl - ext + 0.05 * a), H["t"][i] + 3600, t_off=H["t"][i] + 4 * 3600)); break
    return out


def s6_squeeze(P):
    """Squeeze H1: BB(20,2) di dalam KC(20,1.5) lalu close keluar BB -> market searah, SL 1 ATR, TP 2 ATR."""
    H = P.h1; c = H["c"]; m = sma(c, 20); sd = std(c, 20); A = atr(H, 20); em = ema(c, 20)
    sq = ((m + 2 * sd) < (em + 1.5 * A)) & ((m - 2 * sd) > (em - 1.5 * A)); out = {}
    for i in range(25, len(c)):
        t_end = H["t"][i] + 3600; hr = (t_end % 86400) // 3600
        if not (7 <= hr <= 13) or not sq[i - 5:i].any(): continue
        side = 1 if c[i] > m[i] + 2 * sd[i] else -1 if c[i] < m[i] - 2 * sd[i] else 0
        if not side: continue
        d = t_end // 86400
        if any(o["strat"] == "S6" for o in out.get(d, [])): continue
        out.setdefault(d, []).append(order(P.name, "S6", side, "stop", c[i], c[i] - side * A[i], c[i] + side * 2 * A[i], t_end, t_off=t_end + 3600))
    return out


def s7_trend_pullback(P):
    """Tren harian (close > EMA50 & EMA50 > EMA200) + pullback H1 (RSI14 < 40 lalu naik lagi) -> stop di high bar sinyal."""
    idx, D = prev_daily(P); e50, e200 = ema(D["c"], 50), ema(D["c"], 200); H = P.h1; r = rsi(H["c"], 14); A = atr(H); out = {}
    for d, j in idx.items():
        if j < 200: continue
        up = D["c"][j] > e50[j] > e200[j]; dn = D["c"][j] < e50[j] < e200[j]
        if not (up or dn): continue
        t0 = d * 86400; i0 = np.searchsorted(H["t"], t0 + 7 * 3600); i1 = np.searchsorted(H["t"], t0 + 13 * 3600)
        for i in range(max(i0, 1), min(i1, len(H["t"]))):
            if up and r[i - 1] < 40 <= r[i]:
                e_ = H["h"][i]; sl = e_ - 1.5 * A[i]
                out.setdefault(d, []).append(order(P.name, "S7", 1, "stop", e_, sl, e_ + 2 * (e_ - sl), H["t"][i] + 3600, t_off=H["t"][i] + 3 * 3600)); break
            if dn and r[i - 1] > 60 >= r[i]:
                e_ = H["l"][i]; sl = e_ + 1.5 * A[i]
                out.setdefault(d, []).append(order(P.name, "S7", -1, "stop", e_, sl, e_ - 2 * (sl - e_), H["t"][i] + 3600, t_off=H["t"][i] + 3 * 3600)); break
    return out


def s8_london_hour(P):
    """Candle 1 jam pertama London (07-08 UTC) kuat (badan >= 60% & range >= 0.25 ATR) -> masuk searah, SL ujung lawan, TP 1.5R."""
    idx, D = prev_daily(P); A = atr(D); H = P.h1; pos = {int(t): i for i, t in enumerate(H["t"])}; out = {}
    for d, j in idx.items():
        if j < 20: continue
        i = pos.get(d * 86400 + 7 * 3600)
        if i is None: continue
        o, h, l, c = H["o"][i], H["h"][i], H["l"][i], H["c"][i]; rng = h - l
        if rng < 0.25 * A[j] or abs(c - o) < 0.6 * rng: continue
        side = 1 if c > o else -1; sl = l if side > 0 else h
        out[d] = [order(P.name, "S8", side, "limit", c, sl, c + side * 1.5 * abs(c - sl), d * 86400 + 8 * 3600, t_off=d * 86400 + 10 * 3600)]
    return out


STRATS = dict(S1=s1_asian_breakout, S2=s2_xau_adapt, S3=s3_trinity, S4=s4_nr_orb, S5=s5_turtle_soup,
              S6=s6_squeeze, S7=s7_trend_pullback, S8=s8_london_hour)


def run(names, pairs_data):
    trades = []; days = set()
    for P in pairs_data:
        days |= set(int(x) for x in P.days)
        allo = {}
        for n in names:
            for d, lst in STRATS[n](P).items(): allo.setdefault(d, []).extend(lst)
        for d, lst in allo.items(): trades += simulate_pair(P, lst, d)
    n_days = (max(days) - min(days)) if days else 1
    return portfolio(trades), n_days


if __name__ == "__main__":
    names = sys.argv[1:] or list(STRATS)
    data = [p for p in (load(x) for x in PAIRS) if p]
    print("pair:", [p.name for p in data])
    res = {}
    for n in names:
        tr, nd = run([n], data); m = metrics(tr, nd); res[n] = m
        if m["n"]:
            print(f"{n}: n={m['n']} WR={m['wr']:.0%} PF={m['pf']:.2f} totR={m['totR']:.1f} DD={m['ddR']:.1f}R "
                  f"kalah_beruntun={m['lose_streak']} trade/mgg={m['per_week']:.1f} CAGR={m['cagr']:.1%} "
                  f"tahun+={m['pos_years']}/{m['n_years']} {m['years']}", flush=True)
        else:
            print(f"{n}: tidak ada trade")
    json.dump(res, open(f"{ROOT}/hasil_backtest.json", "w"), indent=1, default=str)
