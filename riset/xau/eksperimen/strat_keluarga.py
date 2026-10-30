"""Ringkasan per keluarga strategi (dari strat_scan): varian terbaik menurut rasio R/DD di 2015-2021, lalu hasilnya di uji & Setra.
Pemakaian: python strat_keluarga.py <xau_sambung.json>"""
import sys, itertools
import numpy as np
src = open(__file__.replace("strat_keluarga.py", "strat_scan.py")).read().split("SL = [1.0")[0]
exec(src)
SL = [1.0, 1.5, 2.0, 3.0]; TP = [0.5, 0.75, 1.0, 1.5, 2.0, None]
best = {}
for (key, rc) in RENCANA.items():
    fam = key[0].split(" >")[0].split(" 50/50")[0].split(" 30/70")[0].split(" 15/85")[0]
    for sl, tp in itertools.product(SL, TP):
        tr = sm.jalan(D, A, rc, sl=sl, tp=tp); s = sm.ringkas(tr, *m.PILIH)
        if s["per_mg"] < 3: continue
        if fam not in best or s["ratio"] > best[fam][0]["ratio"]: best[fam] = (s, tr, (key, sl, tp))
for fam, (s, tr, k) in sorted(best.items(), key=lambda x: -x[1][0]["ratio"]):
    print(f"\n{fam}  terbaik (>= 3 trade/mg di 2015-21): {k}")
    for pn, (a, b) in (("pilih", m.PILIH), ("uji", m.UJI), ("Setra", m.KONF)):
        x = sm.ringkas(tr, a, b)
        print(f"   {pn:<5} /mg {x['per_mg']:.1f} win {x['wr']*100:.0f}% rr {x['rr']:.2f} pf {x['pf']:.2f} R/thn {x['rthn']:+.1f} DD {x['dd']:.0f} "
              f"W/L {x['wmax']}/{x['lmax']} thn+ {x['thn_pos']}/{x['thn_n']}")
