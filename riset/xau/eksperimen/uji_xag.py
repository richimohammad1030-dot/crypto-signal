"""Validasi silang di PERAK (XAG/USD Dukascopy BID): apakah aturan bot XAU & ide #40 (MR SELL hanya RSI2 >= 85 -> sisanya K6)
juga bekerja di pasar mirip yang TIDAK dipakai saat merancang. Harga perak dikali SKALA (= 80, ±rasio emas/perak) agar ambang
mesin dalam USD (SL > 0,5 USD) setara; biaya disetarakan: spread perak ±0,025 USD/oz x 80 = 2,0 USD (sensitivitas 1,0 / 3,0).
Urutan candle ambigu: asumsi bot (BUY duluan). Pemakaian: python uji_xag.py <dir_bulanan_xag>"""
import sys, os, json, glob
import numpy as np
import audit_mesin as m, strat_mesin as sm, multi_mesin as mm
SKALA = 80.0
rows = []
for f in sorted(glob.glob(os.path.join(sys.argv[1], "*.json"))): rows += json.load(open(f))
rows = [[r[0]] + [v * SKALA for v in r[1:]] for r in rows if not (r[1] == r[2] == r[3] == r[4])]
rows = list({r[0]: r for r in rows}.values()); rows.sort()
tmp = "/tmp/_xag_skala.json"; json.dump(rows, open(tmp, "w"))
D = m.muat(tmp); T, O, H, L, C = D
A = np.array(m.atr(list(H), list(L), list(C), 14)); F = m.fitur(D, A)
print(f"XAG {len(rows)} candle, {m.wib(T[0]):%b %Y} - {m.wib(T[-1]):%b %Y}")
P4 = (("2015-21", m.PILIH), ("2022-Jan25", m.UJI), ("Feb25-skrg", m.KONF), ("12t", (None, None)))
VAR = {"BOT LIVE (MR SELL >= 85)": mm.baseline(D, A, F), "MR SELL 71,22 (sblm #40)": mm.baseline(D, A, F, sig=mm.sinyal_mr(D, mr_sell=71.22)),
       "MR + K6 saja (tanpa susulan)": mm.baseline(D, A, F, sus=False)}
for X in (80, 85, 90): VAR[f"ide #40 X{X}"] = mm.baseline(D, A, F, sig=mm.sinyal_mr(D, mr_sell=X))
sig = mm.sinyal_mr(D)
for st in ("MR", "K6", "SUS"): VAR[f"  {st} saja dlm bot live"] = [x for x in VAR["BOT LIVE (MR SELL >= 85)"] if x["strat"] == st]
VAR["  MR SELL RSI 71-85 (versi lama)"] = [x for x in VAR["MR SELL 71,22 (sblm #40)"] if x["strat"] == "MR" and x["d"] == -1
                                           and mm.rsi(C, 2)[x["ip"]] < 85]
for biaya in (2.0, 1.0, 3.0):
    print(f"\n=== biaya {biaya} USD (skala) · R/thn per periode | 12 thn: trade/mg, win, PF, DD")
    for nm, tr in VAR.items():
        s = {pn: sm.ringkas(tr, a, b, biaya=biaya) for pn, (a, b) in P4}
        print(f"{nm:<32} " + " · ".join(f"{s[pn]['rthn']:+6.1f}" for pn, _ in P4) +
              f" | /mg {s['12t']['per_mg']:.1f} win {s['12t']['wr']*100:.0f}% PF {s['12t']['pf']:.2f} DD {s['12t']['dd']:.0f}R")
