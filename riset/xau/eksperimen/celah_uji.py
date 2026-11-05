"""Uji kandidat celah dari statistik_live.py (5 Nov 2026). Kandidat ditemukan dengan melihat SEMUA periode -> rawan kebetulan
(±57 segmen, ±7 diharapkan 'lemah 3/3' secara acak). Diuji sebagai aturan + tetangga + P uji vs baseline live.
A) MR SELL hanya bila RSI2 >= X (X 75/80/85/90); hari RSI 71,22..X -> K6 (A1) atau tanpa trade (A2)
B) K6 hanya saat tren naik (tren turun: tanpa K6 & tanpa susulan)
C) Gabungan A1(85) + B.  Pemakaian: python celah_uji.py <xau_sambung.json> <ambigu.json>"""
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
    pr = sg.banding(jl, gl, int(m.ts(m.UJI[0])), int(m.ts(m.UJI[1])))["P_rasio_lebih_baik"]
    pk = sg.banding(jl, gl, int(m.ts(m.KONF[0])), int(T[-1]))["P_rasio_lebih_baik"]
    s = {pn: sm.ringkas(G, a, b) for pn, (a, b) in P4}
    print(f"{nm:<34} " + " · ".join(f"{s[pn]['rthn']:+5.1f}" for pn, _ in P4) + f" | /mg {s['12t']['per_mg']:.1f} win {s['12t']['wr']*100:.0f}% PF {s['12t']['pf']:.2f}"
          f" DD {s['12t']['dd']:.0f}R W/L {s['12t']['wmax']}/{s['12t']['lmax']} | P uji {pr:.2f} P Setra {pk:.2f}")
print(f"{'R/thn: 2015-21 · 2022-Jan25 · Setra · 12t':<34}")
lapor("BASELINE live", BASE)
sig0 = mm.sinyal_mr(D)
for X in (75, 80, 85, 90):
    sig = mm.sinyal_mr(D, mr_sell=X)
    lapor(f"A1 MR SELL >= {X}, sisanya K6", mm.baseline(D, A, F, ambigu=AMB, sig=sig))
    hapus = set(sig0) - set(sig)
    lapor(f"A2 MR SELL >= {X}, sisanya kosong", [x for x in mm.baseline(D, A, F, ambigu=AMB, sig=sig) if x["ip"] not in hapus])
naik = lambda i: C[i] > E[i]
lapor("B  K6+susulan hanya tren naik", [x for x in BASE if x["strat"] == "MR" or naik(x["ip"])])
sig = mm.sinyal_mr(D, mr_sell=85)
lapor("C  A1(85) + B", [x for x in mm.baseline(D, A, F, ambigu=AMB, sig=sig) if x["strat"] == "MR" or naik(x["ip"])])
