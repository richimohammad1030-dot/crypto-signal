"""Backtest strategi INTRADAY (juara terkunci v2, 27 Okt 2026). Mandiri: hanya butuh numpy.

Model eksekusi realistis berbasis event:
- Order limit yang dikirim bisa menunggu sampai kadaluarsa; maks PEND order menunggu sekaligus.
- Posisi terisi maks CAP. Saat posisi penuh, order lain yang menunggu dibatalkan (pesan "batalkan" dari bot).
- Satu order/posisi per koin. Prioritas order di waktu yang sama: market cap terbesar.
- Biaya: limit/TP maker 0,02%, market/SL/time stop taker 0,07% (fee + slippage). Funding dihitung tiap settlement.

Modul (parameter di PARAM, bisa ditimpa skrip eksperimen):
  A  dip 15m, kapan saja : tren naik 15m (EMA100>EMA200, close>EMA200), RSI2<5 atau RSI14<30, ATR15/harga >= 1,5%.
                           LONG limit 0,25 ATR di bawah close, kadaluarsa 2 jam, SL 3 ATR, exit RSI2>70, time stop 2 jam.
  B  pagi 07:00 WIB       : data H1 di close 07:00. Tren koin searah tren BTC (short hanya jika funding > 0),
                           ATR H1 >= 1,1 x rata-rata 14 hari dan >= 1,34% harga. Limit 1 ATR H1 dari open 07:00,
                           TP di harga open, SL 1,5 ATR H1, kadaluarsa 12 jam, time stop 24 jam.
Pemakaian: python backtest_intraday.py <repo_dir> <data_dir> <out_csv> [CAP] [PEND]
Data: <data>/klines (H1) + funding + funding_hl dari unduh_crypto.py, <data>/k15m dari unduh_intraday.py.
"""
import bisect, collections, csv, json, os, sys, time
import numpy as np

PARAM = dict(
    CAP=3, PEND=3, START=1583020800,                       # 1 Mar 2020 (pemanasan EMA)
    MAKER=0.02, TAKER=0.07,
    A_ON=True, A_VMIN=0.015, A_OFF=0.25, A_SL=3.0, A_VALID_MIN=120, A_HOLD_JAM=2, A_RSI_EXIT=70,
    B_ON=True, B_K=1.0, B_SL=1.5, B_TPF=1.0, B_VALID_JAM=12, B_HOLD_JAM=24, B_VR=1.1, B_ATRP=0.0134, B_BTC=True, B_SHORT=True,
)
IS_END = 1704067200   # 2020-2023 = periode lama (pemilihan), 2024-sekarang = periode baru (uji)


# ------------------------------------------------------------------ indikator
def ema(x, n):
    a = 2 / (n + 1); o = np.empty_like(x); o[0] = x[0]
    for i in range(1, len(x)): o[i] = a * x[i] + (1 - a) * o[i - 1]
    return o

def wilder(x, n):
    o = np.empty_like(x); o[0] = x[0]
    for i in range(1, len(x)): o[i] = (o[i - 1] * (n - 1) + x[i]) / n
    return o

def rsi(C, n):
    d = np.diff(C, prepend=C[0]); g, l = wilder(np.clip(d, 0, None), n), wilder(np.clip(-d, 0, None), n)
    return np.where(l > 0, 100 - 100 / (1 + g / np.where(l > 0, l, 1)), 100.0)

def prep(rows):
    r = np.array([x[:5] for x in rows], float); T, O, H, L, C = r.T
    tr = np.maximum(H - L, np.maximum(abs(H - np.roll(C, 1)), abs(L - np.roll(C, 1)))); tr[0] = H[0] - L[0]
    E1, E2 = ema(C, 100), ema(C, 200)
    return dict(T=T.astype(np.int64), O=O, H=H, L=L, C=C, A=wilder(tr, 14), R2=rsi(C, 2), R14=rsi(C, 14),
                reg=np.where((C > E2) & (E1 > E2), 1, np.where((C < E2) & (E1 < E2), -1, 0)))

def jload(p):
    try: return json.load(open(p))
    except Exception: return []


# ------------------------------------------------------------------ data
def load(data_dir, coins):
    now_ms = time.time() * 1000
    H1, M15 = {}, {}
    for c in coins:
        h = [x for x in jload(f"{data_dir}/klines/{c}.json") if x[5] < now_ms]
        m = jload(f"{data_dir}/k15m/{c}.json")
        if len(h) < 1400 or len(m) < 5000: continue
        H1[c], M15[c] = prep(h), prep(m)
        fb = jload(f"{data_dir}/funding/{c}.json"); fh = jload(f"{data_dir}/funding_hl/{c}.json")
        H1[c]["fb"] = ([x[0] for x in fb], [x[1] for x in fb]); H1[c]["fh"] = ([x[0] for x in fh], [x[1] for x in fh])
        lb = fb[-1][0] if fb else 0
        ser = sorted(fb + [[t, r * 8] for t, r in fh if t > lb and t % 28800 == 0])   # HL per jam -> setara 8 jam
        M15[c]["ft"] = [x[0] for x in ser]; M15[c]["fr"] = [x[1] for x in ser]
        M15[c]["h1"] = {int(t): k for k, t in enumerate(H1[c]["T"])}
    bm = dict(zip(H1["BTC"]["T"].tolist(), H1["BTC"]["reg"].tolist()))
    for G in H1.values(): G["btc"] = np.array([bm.get(t, 0) for t in G["T"].tolist()])
    return H1, M15

def funding_avg72(G, t):
    for (ts, rs), need in ((G["fb"], 6), (G["fh"], 24)):
        a, b = bisect.bisect_right(ts, t - 72 * 3600), bisect.bisect_right(ts, t)
        if b - a >= need: return sum(rs[a:b]) / (b - a)
    return None

def funding_cost(D, t0, t1, d):
    a, b = bisect.bisect_right(D["ft"], t0), bisect.bisect_right(D["ft"], t1)
    return d * sum(D["fr"][a:b])


# ------------------------------------------------------------------ simulasi satu order
def sim(D, i0, d, lim, r0, tp, valid_bars, hold_bars, rsi_exit, P):
    T, O, H, L, C, R2 = D["T"], D["O"], D["H"], D["L"], D["C"], D["R2"]; n = len(T)
    t_exp = int(T[i0]) + valid_bars * 900
    for j in range(i0, min(i0 + valid_bars, n)):
        if (d == 1 and L[j] <= lim) or (d == -1 and H[j] >= lim):
            fill, j0 = (min(lim, O[j]) if d == 1 else max(lim, O[j])), j; break
    else:
        return dict(filled=False, t_exp=t_exp), min(i0 + valid_bars, n)
    sl = fill - d * r0
    for j in range(j0, min(j0 + hold_bars, n)):
        if (d == 1 and L[j] <= sl) or (d == -1 and H[j] >= sl):
            px = sl if j == j0 else (min(sl, O[j]) if d == 1 else max(sl, O[j])); cx, why = P["TAKER"], "SL"; break
        if tp is not None and ((d == 1 and H[j] >= tp) or (d == -1 and L[j] <= tp)) and not (j == j0 and d * (C[j] - tp) < 0):
            px, cx, why = tp, P["MAKER"], "TP"; break     # di candle isi, TP hanya jika close melewati TP
        if rsi_exit and j > j0 and ((d == 1 and R2[j] > rsi_exit) or (d == -1 and R2[j] < 100 - rsi_exit)):
            px, cx, why = C[j], P["TAKER"], "RSI"; break
    else:
        j = min(j0 + hold_bars, n) - 1; px, cx, why = C[j], P["TAKER"], "WAKTU"
    pnl = d * (px - fill) - (P["MAKER"] + cx) / 100 * fill - funding_cost(D, int(T[j0]), int(T[j]), d) * fill
    return dict(filled=True, t_exp=t_exp, t_fill=int(T[j0]), t_exit=int(T[j]) + 900, R=float(pnl / r0), why=why,
                entry=float(fill), exit=float(px)), j + 1


# ------------------------------------------------------------------ semua order kandidat
def orders(H1, M15, P):
    out = []
    for c, D in M15.items():
        T, C, A, R2, R14, reg = D["T"], D["C"], D["A"], D["R2"], D["R14"], D["reg"]
        if P["A_ON"]:
            nxt = 0
            for i in np.flatnonzero((reg == 1) & ((R2 < 5) | (R14 < 30)) & (A / C >= P["A_VMIN"])):
                if i < max(nxt, 900) or i + 1 >= len(T) or T[i] < P["START"]: continue
                r, nxt = sim(D, i + 1, 1, C[i] - P["A_OFF"] * A[i], P["A_SL"] * A[i], None,
                             P["A_VALID_MIN"] // 15, P["A_HOLD_JAM"] * 4, P["A_RSI_EXIT"], P)
                out.append(dict(r, t=int(T[i + 1]), c=c, m="A", d=1, vr=0.0))
        if P["B_ON"]:
            G = H1[c]; GA = G["A"]; nxt = 0
            for i in np.flatnonzero(T % 86400 == 0):        # candle 00:00 UTC = 07:00 WIB
                if i < max(nxt, 900) or T[i] < P["START"]: continue
                k = D["h1"].get(int(T[i]) - 3600)
                if k is None or k < 400: continue
                a = GA[k]; vr = a / GA[k - 336:k].mean(); tr = int(G["reg"][k])
                if vr < P["B_VR"] or a / G["C"][k] < P["B_ATRP"] or tr == 0: continue
                if P["B_BTC"] and int(G["btc"][k]) != tr: continue
                if tr == -1 and (not P["B_SHORT"] or (funding_avg72(G, int(G["T"][k])) or 0) <= 0): continue
                o = D["O"][i]; lim = o - tr * P["B_K"] * a
                r, nxt = sim(D, i, tr, lim, P["B_SL"] * a, lim + tr * P["B_TPF"] * P["B_K"] * a,
                             P["B_VALID_JAM"] * 4, P["B_HOLD_JAM"] * 4, None, P)
                out.append(dict(r, t=int(T[i]), c=c, m="B", d=tr, vr=float(vr)))
    return out


# ------------------------------------------------------------------ portofolio (model bot)
def portfolio(ords, coins, cap, pend_max):
    rank = {c: i for i, c in enumerate(coins)}
    ev = sorted(ords, key=lambda o: (o["t"], rank[o["c"]]))
    pend, pos, sent, taken = [], [], [], []
    def settle(now):
        nonlocal pend, pos
        while True:
            cand = [(o["t_fill"], rank[o["c"]], k) for k, (_, o) in enumerate(pend) if o["filled"] and o["t_fill"] < now]
            if not cand: break
            tf, _, k = min(cand); o = pend[k][1]
            pos = [(e, c) for e, c in pos if e > tf]
            pend = [p for p in pend if p[1] is not o and (p[0] > tf)]
            if len(pos) < cap:
                pos.append((o["t_exit"], o["c"])); taken.append(o)
                if len(pos) >= cap: pend = []                 # posisi penuh -> order lain dibatalkan
        pend = [p for p in pend if p[0] > now]
        pos = [(e, c) for e, c in pos if e > now]
    for o in ev:
        settle(o["t"])
        if o["c"] in {c for _, c in pos} | {x["c"] for _, x in pend} or len(pend) >= pend_max or len(pos) >= cap: continue
        sent.append(o)
        pend.append(((o["t_fill"] + 1) if o["filled"] else o["t_exp"], o))
    settle(2_000_000_000)
    return sent, taken


# ------------------------------------------------------------------ statistik
def stats(trades, sent=None, a=None, b=None):
    f = [o for o in trades if (a is None or o["t"] >= a) and (b is None or o["t"] < b)]
    if not f: return dict(n=0)
    s = [o for o in (sent or []) if (a is None or o["t"] >= a) and (b is None or o["t"] < b)]
    R = np.array([o["R"] for o in sorted(f, key=lambda o: o["t_exit"])])
    t0, t1 = (a or min(o["t"] for o in f)), (b or max(o["t_exit"] for o in f)); yrs = max((t1 - t0) / 31557600, 0.1)
    day = collections.defaultdict(float)
    for o in f: day[o["t_exit"] // 86400] += o["R"]
    eq = np.cumsum([day[k] for k in sorted(day)]); dd = float((np.maximum.accumulate(np.concatenate([[0], eq]))[1:] - eq).max())
    w = l = bw = bl = 0
    for r in R:
        w, l = (w + 1, 0) if r > 0 else (0, l + 1); bw, bl = max(bw, w), max(bl, l)
    top = np.sort(R)[::-1][max(1, len(R) // 50):]                 # tanpa 2% trade terbaik
    return dict(n=int(len(R)), per_tahun=round(len(R) / yrs), win=round(float((R > 0).mean() * 100), 1), avgR=round(float(R.mean()), 4),
                totR=round(float(R.sum()), 1), totR_thn=round(float(R.sum() / yrs), 1), pf=round(float(R[R > 0].sum() / -R[R <= 0].sum()), 2),
                maxDD=round(dd, 1), rasio=round(float(R.sum() / yrs) / max(dd, 1), 2), win_beruntun=bw, kalah_beruntun=bl,
                tanpa_top2=round(float(top.sum()), 1), fill=round(len(f) / len(s) * 100, 1) if s else None)

def run(repo, data_dir, P=None):
    sys.path.insert(0, repo)
    import signal_bot as sb
    P = dict(PARAM, **(P or {}))
    H1, M15 = load(data_dir, sb.COINS)
    ords = orders(H1, M15, P)
    sent, taken = portfolio(ords, sb.COINS, P["CAP"], P["PEND"])
    return P, sent, sorted(taken, key=lambda o: o["t_exit"])

if __name__ == "__main__":
    REPO, DATA, OUT = sys.argv[1:4]
    over = {}
    if len(sys.argv) > 4: over["CAP"] = int(sys.argv[4])
    if len(sys.argv) > 5: over["PEND"] = int(sys.argv[5])
    P, sent, taken = run(REPO, DATA, over)
    keys = ["t", "t_fill", "t_exit", "c", "m", "d", "vr", "entry", "exit", "R", "why"]
    with open(OUT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore"); w.writeheader(); w.writerows(taken)
    print("parameter:", P)
    print("SEMUA      ", stats(taken, sent))
    print("2020-2023  ", stats(taken, sent, b=IS_END))
    print("2024-skrg  ", stats(taken, sent, a=IS_END))
    yr = collections.defaultdict(list)
    for o in taken: yr[time.gmtime(o["t"]).tm_year].append(o["R"])
    print("per tahun  ", {y: (len(v), round(sum(v), 1)) for y, v in sorted(yr.items())})
