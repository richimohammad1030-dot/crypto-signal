"""Riset putaran 4: optimasi N3 dua arah di 7 pair major (pilihan pemilik 20 Nov 2026: 7 pair, >= 4 trade/minggu).
Hanya filter UNIVERSAL (sama untuk semua pair, tanpa memilih pair) agar tidak overfitting:
  dist  : level maksimal sejauh dist*ATR dari close kemarin (level jauh = jarang terisi / telat)
  vol   : rezim volatilitas ATR14/ATR100 harian (none / tinggi >= 0.9 / rendah <= 1.1)
  dow   : hari dilewati (none / Senin / Jumat)
  slm, tpm : SL & TP dalam ATR harian
  be    : pindah SL ke entry setelah +be R (0 = tidak)
Seleksi: >= 4 trade/minggu, PF IS (2015-2022) & OOS (2023-2026) > 1,05, Setra > 1,0; peringkat min(PF IS, PF OOS).
Pemakaian: python forex_major/riset_putaran4.py [bagian] [jumlah_bagian]"""
import itertools, json, os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import backtest as B
from backtest import order, atr, prev_daily
from riset_putaran2 import pf
from riset_putaran3 import score, fmt

ROOT = os.path.dirname(os.path.abspath(__file__))
ALL = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD"]


def n3o(P, dist=9.0, vol="none", dow="none", slm=0.4, tpm=0.8, be=0.0):
    idx, D = prev_daily(P); A = atr(D); A100 = atr(D, 100); out = {}; wk = (D["t"] // 86400 + 3) // 7
    for d, j in idx.items():
        if j < 110: continue
        wd = (d + 3) % 7                     # 0 = Senin
        if (dow == "mon" and wd == 0) or (dow == "fri" and wd == 4): continue
        rv = A[j] / A100[j]
        if (vol == "high" and rv < 0.9) or (vol == "low" and rv > 1.1): continue
        m = wk == ((d + 3) // 7 - 1)
        if not m.any(): continue
        ph, pl = D["h"][m].max(), D["l"][m].min(); a = A[j]; t0 = d * 86400; c = D["c"][j]; lst = []
        if D["h"][j] < ph and (ph - c) <= dist * a:
            lst.append(order(P.name, "N3", 1, "stop", ph, ph - slm * a, ph + tpm * a, t0, oco=("N3", d)))
        if D["l"][j] > pl and (c - pl) <= dist * a:
            lst.append(order(P.name, "N3", -1, "stop", pl, pl + slm * a, pl - tpm * a, t0, oco=("N3", d)))
        for o in lst: o["be"] = be
        if lst: out[d] = lst
    return out


# breakeven: bungkus find_exit agar SL pindah ke entry setelah harga bergerak +be R
_orig_exit = B.find_exit
def _exit_be(P, side, i, k, sl, tp, e, end, px_fill, be=0.0):
    if be <= 0: return _orig_exit(P, side, i, k, sl, tp, e, end, px_fill)
    risk = abs(px_fill - sl); trig = px_fill + side * be * risk
    # cari titik pemicu BE dulu (berhenti di SL/TP bila lebih dulu)
    x, why = _orig_exit(P, side, i, k, sl, trig, e, end, px_fill)
    if why != "tp": return x, why
    # dari candle pemicu: lanjut dengan SL = entry (konservatif: mulai candle berikutnya)
    j = next((q for q in range(i, e) if (P.h[q] >= trig if side > 0 else P.l[q] <= trig)), None)
    if j is None or j + 1 >= e or P.t[j + 1] >= end: return P.c[min(j or i, e - 1)], "close"
    return _orig_exit(P, side, j + 1, 0, px_fill, tp, e, end, P.o[j + 1])

def simulate_be(P, orders, d):
    be = orders[0].get("be", 0.0) if orders else 0.0
    if be <= 0: return B.simulate_pair(P, orders, d)
    B.find_exit = lambda *a: _exit_be(*a, be=be)
    try: return B.simulate_pair(P, orders, d)
    finally: B.find_exit = _orig_exit


def run(kw, data):
    tr = []; days = set()
    for P in data:
        days |= set(int(x) for x in P.days)
        for d, lst in n3o(P, **kw).items(): tr += simulate_be(P, lst, d)
    return tr, (max(days) - min(days)) if days else 1


GRID = dict(dist=[9.0, 1.0, 0.6], vol=["none", "high", "low"], dow=["none", "mon", "fri"],
            slm=[0.3, 0.4, 0.5], tpm=[0.8, 1.2], be=[0.0, 0.5])

if __name__ == "__main__":
    part, nparts = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (0, 1)
    duka = [B.load(p) for p in ALL]
    os.environ["FX_DATA"] = "data_setra/{pair}_1h.json.gz"; setra = [B.load(p) for p in ALL]
    keys = list(GRID); combos = list(itertools.product(*[GRID[k] for k in keys]))[part::nparts]; rows = []
    for vals in combos:
        kw = dict(zip(keys, vals)); tr, nd = run(kw, duka); ts, _ = run(kw, setra); s = score(tr, nd, ts)
        trp = B.portfolio(tr)
        s["pf_newpairs"] = pf([t for t in trp if t["pair"] in ("USDCAD", "USDCHF", "NZDUSD")])[0]
        s["lolos"] = s["per_week"] >= 4 and s["pf_is"] > 1.05 and s["pf_oos"] > 1.05 and s["pf_setra"] > 1.0
        rows.append(dict(kw=kw, **s))
    json.dump(rows, open(f"/tmp/p4_{part}.json", "w"), default=float)
    print("selesai", part, len(rows))
