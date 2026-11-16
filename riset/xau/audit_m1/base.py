import sys, os, numpy as np
from data import REPO
sys.path.insert(0, REPO); sys.path.insert(0, REPO + "/riset/xau/eksperimen")
import audit_mesin as m, multi_mesin as mm, strat_mesin as sm
from data import *
gb = m.gb

def build_D():
    R = load_repo_h1()
    T, O, H, L, C = load_m1_fixed()
    o_ = np.argsort(T, kind="stable"); T, O, H, L, C = T[o_], O[o_], H[o_], L[o_], C[o_]
    t, o, h, l, c, i0, i1 = to_h1(T, O, H, L, C)
    last = R[-1, 0]
    ex = t > last
    full = np.vstack([R, np.c_[t[ex], o[ex], h[ex], l[ex], c[ex]]])
    return [full[:, k] for k in range(5)]

if __name__ == "__main__":
    D = build_D()
    print(len(D[0]), D[0][0], D[0][-1])
    A = np.array(m.atr(list(D[2]), list(D[3]), list(D[4]), 14)); F = m.fitur(D, A)
    amb = None
    import json
    ambf = REPO + "/riset/xau/eksperimen/ambigu_m1_2022_2026.json"
    base = mm.baseline(D, A, F)           # ambigu="buy" = asumsi bot
    P = (("2005-14", ("2005-01-01","2015-01-01")),("2015-21",("2015-01-01","2022-01-01")),("2022-Jan25",m.UJI),("Feb25-skrg",m.KONF),("2005-26",("2005-01-01",None)))
    for nm,(a,b) in P:
        s = sm.ringkas(base, a, b)
        print(nm, f"n={s['n']} R/thn={s['rthn']:+.1f} win={s['wr']*100:.0f}% PF={s['pf']:.2f} DD={s['dd']:.0f}R", s['thn'] if nm=="2005-26" else "")
