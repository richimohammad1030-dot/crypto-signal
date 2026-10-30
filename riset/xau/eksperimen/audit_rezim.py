"""Audit XAU: edge kotor vs volatilitas relatif (ATR H1/harga) dan absolut (r0 USD), dipisah per periode audit.
Pemakaian: python audit_rezim.py <xau_sambung.json>"""
import sys
import numpy as np
import audit_mesin as m
D = m.muat(sys.argv[1]); A = np.array(m.atr(list(D[2]), list(D[3]), list(D[4]), 14)); F = m.fitur(D, A)
tr = m.replay(D, A=A)
P = (("2015-2021", m.PILIH), ("2022-Jan25", m.UJI), ("Feb25-skrg", m.KONF))
def tab(nama, f, edges, fmt):
    print(f"\n== {nama}")
    for pn, (a, b) in P:
        s = m.potong(tr, a, b); out = []
        for lo, hi in zip(edges[:-1], edges[1:]):
            g = [x for x in s if lo <= f(x) < hi]
            if g:
                kot = np.mean([x["R"] for x in g]); net = np.mean(m.net(g))
                out.append(f"{fmt(lo)}: n={len(g):>4} kotor {kot:+.3f} bersih {net:+.3f}")
        print(f"  {pn}: " + " | ".join(out))
tab("ATR H1 / harga", lambda x: F["atr_rel"][x["ip"]], [0, .002, .0025, .003, .0035, .0045, 1], lambda v: f">={v*100:.2f}%")
tab("r0 (USD, jarak SL)", lambda x: x["r0"], [0, 4, 6, 8, 12, 20, 1e9], lambda v: f">={v:g}$")
tab("Tren pasar D1 EMA50 (harga di atas = naik)", lambda x: 1 if D[4][x["ip"]] > F["d_ema50"][x["ip"]] else 0, [0, 1, 2], lambda v: "naik" if v else "turun")
tab("Posisi searah H1 EMA200", lambda x: 1 if (D[4][x["ip"]] > F["ema200"][x["ip"]]) == (x["d"] == 1) else 0, [0, 1, 2], lambda v: "searah" if v else "lawan")
