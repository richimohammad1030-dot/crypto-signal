"""Ide #58b (10 Nov 2026): integrasi kombinasi terbaik #58 (mandiri 07:00) ke sistem live. V1 = kombinasi MENGGANTI MR live
(hari kombinasi -> trade kombinasi, hari lain -> K6 + susulan); V2 = kombinasi DULU, lalu MR live, lalu K6 + susulan.
Bandingkan dengan bot live di 2004-2014 (data baru), 2015-21, 2022-Jan25, Setra + tahun minus 2005-2026.
Pemakaian: python kombinasi_integrasi.py <xau_2004.json> <ambigu.json>"""
import sys
import numpy as np
sys.argv = sys.argv[:3]
exec(open("kombinasi.py").read().split("def per_idx")[0])
LIVE = mm.baseline(D, A, F, ambigu=AMB); live_mr = {x["ip"]: x for x in mm.trades_mr(D, A, sig)}
P = (("2004-14", ("2005-01-01", "2015-01-01")), ("2015-21", ("2015-01-01", "2022-01-01")), ("22-Jan25", m.UJI), ("Setra", m.KONF), ("2005-26", ("2005-01-01", None)))
def lapor(nm, G):
    s = {pn: sm.ringkas(G, a, b) for pn, (a, b) in P}
    th = {}
    for x, v in zip(sorted(G, key=lambda z: z["t1"]), m.net(sorted(G, key=lambda z: z["t1"]))):
        y = m.wib(x["t0"]).year
        if y >= 2005: th[y] = th.get(y, 0) + v
    v = np.array(list(th.values()))
    print(f"{nm:<38} " + " · ".join(f"{s[pn]['rthn']:+5.1f}" for pn, _ in P) + f" | /mg {s['2005-26']['per_mg']:.1f} win {s['2005-26']['wr']*100:.0f}%"
          f" PF {s['2005-26']['pf']:.2f} DD {s['2005-26']['dd']:.0f}R | thn minus {int((v < 0).sum())}/{len(v)} terburuk {v.min():+.0f}")
    return th
print("R/thn: 2004-14(dr 2005) · 2015-21 · 2022-Jan25 · Setra · 2005-2026")
thL = lapor("BOT LIVE", LIVE)
KAND = [("ALG", "RSIf", "CLV"), ("ALG", "RSIf", "EMA", "CLV"), ("ALG", "MACD", "RSIf", "CLV"), ("MACD", "RSIf"), ("RSIf", "EMA", "CLV"), ("ALG", "MACD", "RSIf")]
for kom in KAND:
    for sl, tp in ((2.0, 2), (2.0, None), (3.0, None)):
        sigk = {}
        for i in harian:
            v = [KOMP[k](i) for k in kom]
            if v[0] != 0 and all(x == v[0] for x in v): sigk[i] = v[0]
        tr = {x["ip"]: x for x in jalan_idx(list(sigk), lambda i: [(sigk[i], "market", None)], sl, tp)}
        G1 = mm.baseline(D, A, F, ambigu=AMB, sig=sigk, mr=list(tr.values()))
        s2 = {**sig, **sigk}; mr2 = {**live_mr, **tr}
        G2 = mm.baseline(D, A, F, ambigu=AMB, sig=s2, mr=list(mr2.values()))
        lapor(f"V1 {'+'.join(kom)} SL{sl} TP{tp or '-'}", G1)
        th = lapor(f"V2 {'+'.join(kom)} SL{sl} TP{tp or '-'}", G2)
print("\nper tahun BOT LIVE: " + " ".join(f"{str(y)[2:]}:{v:+.0f}" for y, v in thL.items()))
