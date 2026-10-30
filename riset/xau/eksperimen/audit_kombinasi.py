"""Audit XAU: kombinasi filter biaya (K1/K3) + lewati hari bila sisi lawan tren terisi duluan. SELEKSI di 2015-2021.
Pemakaian: python audit_kombinasi.py <xau_sambung.json>"""
import sys, itertools
import numpy as np
import audit_mesin as m
D = m.muat(sys.argv[1]); A = np.array(m.atr(list(D[2]), list(D[3]), list(D[4]), 14)); F = m.fitur(D, A)
F["ema100"] = m.ema(D[4], 100)
rows = []
for bm, rg, e in itertools.product((0.04, 0.05, 0.06), ((23, 3), (0, 4)), ("ema100", "ema200", "d_ema20", "d_ema50")):
    spec = {"biaya_maks": bm, "place_hr": rg[0], "range_n": rg[1], "tren_lawan_w": (e, 0.0)}
    s = m.stat(m.jalankan(spec, D, A, F), a=m.PILIH[0], b=m.PILIH[1]); rows.append((s["ratio"], spec, s))
rows.sort(key=lambda r: -r[0])
for r, spec, s in rows[:10]:
    print(m.baris(f"b{spec['biaya_maks']} r{spec['place_hr']},{spec['range_n']} {spec['tren_lawan_w'][0]}", s))
