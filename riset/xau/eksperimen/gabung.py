"""HIPOTESIS (ide lahir setelah melihat periode uji -> bukan bukti): portofolio K6 (tren) + RSI(2) fade (mean reversion,
q 0,35, SL 3 ATR, tanpa TP), masing-masing risiko penuh atau 1/2. Pemakaian: python gabung.py <xau_sambung.json> <ambigu.json>"""
import sys, json, pickle
import numpy as np
import audit_mesin as m
import strat_mesin as sm
D = m.muat(sys.argv[1]); A = np.array(m.atr(list(D[2]), list(D[3]), list(D[4]), 14)); F = m.fitur(D, A)
AMB = {int(k): v for k, v in json.load(open(sys.argv[2])).items()}
K6 = m.potong(m.jalankan({"ambigu": AMB, "tren_lawan_w": ("ema200", 0.0)}, D, A, F))
MR = pickle.load(open("/tmp/data/mr_top.pkl", "rb"))[("RSI2", 0.35, "tanpa", "market", 3.0, None)][0]
for w in (1.0, 0.5):
    G = sorted([dict(x, w=w) for x in K6] + [dict(x, w=w) for x in MR], key=lambda x: x["t1"])
    print(f"\n### K6 + RSI2 fade, tiap strategi risiko {w:g}x (maks 2 posisi bersamaan)")
    for pn, (a, b) in (("2015-2021", m.PILIH), ("2022-Jan25", m.UJI), ("Setra", m.KONF), ("2015-skrg", (None, None))):
        s = sm.ringkas(G, a, b)
        print(f"  {pn:<10} /mg {s['per_mg']:.1f} win {s['wr']*100:.0f}% rr {s['rr']:.2f} pf {s['pf']:.2f} R/thn {s['rthn']:+.1f} DD {s['dd']:.0f}R "
              f"({s['ddpct']:.0f}% ekuitas, risiko 1%) W/L {s['wmax']}/{s['lmax']} thn+ {s['thn_pos']}/{s['thn_n']} {'LULUS' if sm.lulus(s) else ''}")
    print("  per tahun:", " ".join(f"{y}:{v:+.0f}" for y, v in m.stat(G)["thn"].items()))
