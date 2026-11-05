"""Ide #40b (5 Nov 2026): penutup celah dengan sumber edge BERBEDA. Hari RSI2 07:00 di antara 71,22 dan X (jenuh beli ringan,
yang SELL-nya lemah) diberi: K6 (ide #40) / MOMENTUM = BUY market (jenuh beli ringan = momentum naik; SL 3 ATR, TP 2R/tanpa) /
momentum hanya bila tren naik (lainnya K6). Tetangga X = 80/85/90. Pemakaian: python celah_momentum.py <sambung.json> <ambigu.json>"""
import sys, os, json
import numpy as np
import audit_mesin as m, strat_mesin as sm, multi_mesin as mm
sys.path.insert(0, os.path.join(m.REPO, "riset")); import signifikansi as sg
D = m.muat(sys.argv[1]); T, O, H, L, C = D
A = np.array(m.atr(list(H), list(L), list(C), 14)); F = m.fitur(D, A)
AMB = {int(k): v for k, v in json.load(open(sys.argv[2])).items()}
E = np.array(m.gb.ema(list(C), 200))
BASE = mm.baseline(D, A, F, ambigu=AMB)
jl = [(int(x["t1"]), float(v)) for x, v in zip(BASE, m.net(BASE))]
P4 = (("2015-21", m.PILIH), ("2022-Jan25", m.UJI), ("Setra", m.KONF), ("12t", (None, None)))
def lapor(nm, G):
    G = sorted(G, key=lambda z: z["t1"]); gl = [(int(x["t1"]), float(v)) for x, v in zip(G, m.net(G))]
    pu = sg.banding(jl, gl, int(m.ts(m.UJI[0])), int(m.ts(m.UJI[1])))["P_rasio_lebih_baik"]
    pk = sg.banding(jl, gl, int(m.ts(m.KONF[0])), int(T[-1]))["P_rasio_lebih_baik"]
    s = {pn: sm.ringkas(G, a, b) for pn, (a, b) in P4}
    print(f"{nm:<36} " + " · ".join(f"{s[pn]['rthn']:+5.1f}" for pn, _ in P4) + f" | /mg {s['12t']['per_mg']:.1f} PF {s['12t']['pf']:.2f}"
          f" DD {s['12t']['dd']:.0f}R W/L {s['12t']['wmax']}/{s['12t']['lmax']} | P uji {pu:.2f} Setra {pk:.2f}")
print("R/thn: 2015-21 · 2022-Jan25 · Setra · 12 thn"); lapor("BASELINE live", BASE)
sig0 = mm.sinyal_mr(D)
for X in (80, 85, 90):
    sig = mm.sinyal_mr(D, mr_sell=X); sel = set(sig0) - set(sig)
    ide40 = mm.baseline(D, A, F, ambigu=AMB, sig=sig); lapor(f"X{X} ide #40: sel -> K6", ide40)
    for tp in (2, None):
        mo = sm.jalan(D, A, lambda i: [(1, "market", None)] if i in sel else None, sl=3.0, tp=tp)
        for x in mo: x["strat"] = "MOM"
        lapor(f"X{X} sel -> BUY momentum TP{tp or '-'}", [x for x in ide40 if x["ip"] not in sel] + mo)
        mo2 = [x for x in mo if C[x["ip"]] > E[x["ip"]]]; ip2 = {x["ip"] for x in mo2}
        lapor(f"X{X} sel -> momentum bila tren naik TP{tp or '-'}", [x for x in ide40 if x["ip"] not in ip2] + mo2)
