"""Lanjutan uji_xag.py (6 Nov 2026): di perak, apakah MASALAH-nya hari RSI2 71,22-85 (MR SELL lemah) atau PENGGANTI-nya (K6)?
A2 = ide #40 tetapi hari RSI 71,22-85 tanpa trade (bukan K6/susulan). Pemakaian: python uji_xag_a2.py <dir_bulanan_xag>"""
import sys
sys.argv = sys.argv[:2]
exec(open("uji_xag.py").read().split("for biaya in")[0])
R2 = mm.rsi(C, 2)
X85 = VAR["ide #40 X85"]
A2 = [x for x in X85 if not (x["strat"] != "MR" and 71.22 <= R2[x["ip"]] < 85)]
GANTI = [x for x in X85 if x["strat"] != "MR" and 71.22 <= R2[x["ip"]] < 85]
V2 = {"MR SELL 71,22 (sblm #40)": VAR["MR SELL 71,22 (sblm #40)"], "ide #40 X85 (hari 71-85 -> K6)": X85,
      "A2: hari 71-85 tanpa trade": A2, "  K6/SUS pengganti hari 71-85": GANTI,
      "  MR SELL RSI 71-85 (versi lama)": VAR["  MR SELL RSI 71-85 (versi lama)"]}
for biaya in (2.0, 1.0, 3.0):
    print(f"\n=== biaya {biaya} USD (skala) · R/thn 2015-21 · 2022-Jan25 · Feb25-skrg · 12t")
    for nm, tr in V2.items():
        s = {pn: sm.ringkas(tr, a, b, biaya=biaya) for pn, (a, b) in P4}
        print(f"{nm:<34} " + " · ".join(f"{s[pn]['rthn']:+6.1f}" for pn, _ in P4) + f" | n {s['12t']['n']}")
