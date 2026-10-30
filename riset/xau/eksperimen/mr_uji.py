"""Uji kandidat mean reversion (dipilih di 2015-2021 oleh mr_scan.py) di 2022 - Jan 2025 dan Setra, + signifikansi vs juara & K6.
Pemakaian: python mr_uji.py <xau_sambung.json> <ambigu_sisi.json>"""
import sys, os, json, pickle
import numpy as np
import audit_mesin as m
import strat_mesin as sm
sys.path.insert(0, os.path.join(m.REPO, "riset")); import signifikansi as sg
D = m.muat(sys.argv[1]); A = np.array(m.atr(list(D[2]), list(D[3]), list(D[4]), 14)); F = m.fitur(D, A)
AMB = {int(k): v for k, v in json.load(open(sys.argv[2])).items()}
top = pickle.load(open("/tmp/data/mr_top.pkl", "rb"))
L = lambda tr: [(int(x["t1"]), float(v)) for x, v in zip(tr, m.net(tr))]
J = m.potong(m.jalankan({"ambigu": AMB}, D, A, F)); K6 = m.potong(m.jalankan({"ambigu": AMB, "tren_lawan_w": ("ema200", 0.0)}, D, A, F))
P = (("pilih", m.PILIH), ("uji", m.UJI), ("Setra", m.KONF), ("semua", (None, None)))
def baris(nm, tr):
    out = []
    for pn, (a, b) in P:
        s = sm.ringkas(tr, a, b)
        out.append(f"{pn}: /mg {s['per_mg']:.1f} win {s['wr']*100:.0f}% pf {s['pf']:.2f} R/thn {s['rthn']:+.1f} DD {s['dd']:.0f} W/L {s['wmax']}/{s['lmax']} "
                   f"thn+ {s['thn_pos']}/{s['thn_n']} {'LULUS' if sm.lulus(s) else '-'}")
    print(f"\n{nm}\n  " + "\n  ".join(out))
    s = sm.ringkas(tr, *m.UJI, slip=0.2); print(f"  slip+0,2 uji R/thn {s['rthn']:+.1f} pf {s['pf']:.2f}")
    for ref, rl in (("juara", L(J)), ("K6", L(K6))):
        r = sg.banding(rl, L(tr), int(m.ts(m.UJI[0])), int(m.ts(m.UJI[1])))
        print(f"  P_rasio uji vs {ref}: {r['P_rasio_lebih_baik']:.3f}", end="")
    print("  per tahun:", " ".join(f"{y}:{v:+.0f}" for y, v in m.stat(tr)["thn"].items()))
baris("JUARA", J); baris("K6", K6)
for k in list(top)[:8]:
    baris(f"{k} ambang {top[k][1]}", top[k][0])
