"""Tambal-celah putaran 2 (10 Nov 2026): penambal untuk sistem live di 2005-2026 (celah utama K6 di tahun minus, SUS-BUY rugi).
P-a K6 hanya bila tren H1 (EMA200) searah tren harian (close 07:00 vs SMA n hari, n 50/100/200); hari lain tanpa K6/susulan.
P-b K6 dilewati bila ATR relatif < x (0,8/0,85/0,9). P-c tanpa susulan BUY / tanpa susulan. P-d gabungan.
Valid bila memperbaiki tahun minus & total di KEDUA paruh (2005-2015, 2016-2026) dan tetangga ikut baik.
Pemakaian: python tambal2.py <xau_2004.json> <ambigu.json>"""
import sys, itertools
import numpy as np
sys.argv = sys.argv[:3]
exec(open("simetris.py").read().split("KAND = {}")[0])
G0 = [x for x in BASE if m.wib(x["t0"]).year >= 2005]
for x, v in zip(G0, m.net(G0)): x["Rn"] = float(v)
E200 = np.array(m.gb.ema(list(C), 200))
k07 = {i: k for k, i in enumerate(i07)}
MA = {n: sma(dC, n) for n in (50, 100, 200)}
def d1(i, n):
    k = k07.get(i); ma = MA[n][k] if k is not None else np.nan
    return 1 if np.isnan(ma) or dC[k] > ma else -1
atr_rel = lambda i: A[i] / np.median(A[max(0, i - 500):i + 1])
def nilai(G):
    th = {y: 0.0 for y in range(2005, 2027)}
    for x in G: th[m.wib(x["t0"]).year] += x["Rn"]
    v = np.array(list(th.values())); a, b = v[:11], v[11:]
    c = np.cumsum([x["Rn"] for x in sorted(G, key=lambda z: z["t1"])]); dd = (np.maximum.accumulate(np.concatenate([[0], c]))[1:] - c).max()
    return dict(th=v, tot=v.mean(), minus=int((v < 0).sum()), worst=v.min(), a=(a.mean(), int((a < 0).sum())), b=(b.mean(), int((b < 0).sum())), dd=dd, n=len(G))
def baris(nm, r, ref=None):
    ok = ""
    if ref: ok = "  ✓ KEDUA PARUH" if r["a"][0] >= ref["a"][0] and r["b"][0] >= ref["b"][0] and r["a"][1] <= ref["a"][1] and r["b"][1] <= ref["b"][1] and r["minus"] < ref["minus"] else ""
    print(f"{nm:<40} R/thn {r['tot']:+5.1f} · minus {r['minus']}/22 · terburuk {r['worst']:+4.0f} · DD {r['dd']:.0f}R · "
          f"2005-15 {r['a'][0]:+5.1f} ({r['a'][1]} minus) · 2016-26 {r['b'][0]:+5.1f} ({r['b'][1]} minus) · /mg {r['n']/22/52:.1f}{ok}")
ref = nilai(G0); baris("SISTEM LIVE", ref)
def k6_hari(x): return x["strat"] in ("K6", "SUS")
def tren_h1(i): return 1 if C[i] > E200[i] else -1
V = {}
for n in (50, 100, 200):
    V[f"a) K6 bila H1 searah D1 SMA{n}"] = [x for x in G0 if not k6_hari(x) or tren_h1(x["ip"]) == d1(x["ip"], n)]
for t in (0.8, 0.85, 0.9):
    V[f"b) K6 lewati ATR rel < {t}"] = [x for x in G0 if not k6_hari(x) or atr_rel(x["ip"]) >= t]
V["c1) tanpa susulan BUY"] = [x for x in G0 if not (x["strat"] == "SUS" and x["d"] == 1)]
V["c2) tanpa susulan"] = [x for x in G0 if x["strat"] != "SUS"]
for n, t in itertools.product((50, 100, 200), (0.8, 0.85, 0.9)):
    V[f"d) a SMA{n} + b {t} + c1"] = [x for x in G0 if (not k6_hari(x) or (tren_h1(x["ip"]) == d1(x["ip"], n) and atr_rel(x["ip"]) >= t))
                                       and not (x["strat"] == "SUS" and x["d"] == 1)]
R = {}
for nm, G in V.items():
    R[nm] = nilai(G); baris(nm, R[nm], ref)
best = min(R, key=lambda k: (R[k]["minus"], -R[k]["worst"], -R[k]["tot"]))
print(f"\nTERBAIK (tahun minus paling sedikit): {best}")
print("per tahun: " + " ".join(f"{str(y)[2:]}:{v:+.0f}" for y, v in zip(range(2005, 2027), R[best]["th"])))
print("live:      " + " ".join(f"{str(y)[2:]}:{v:+.0f}" for y, v in zip(range(2005, 2027), ref["th"])))
