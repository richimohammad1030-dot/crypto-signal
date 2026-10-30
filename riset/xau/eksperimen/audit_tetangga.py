"""Audit XAU: uji tetangga K6 (lewati hari bila sisi lawan tren terisi duluan). Semua periode + signifikansi UJI.
Pemakaian: python audit_tetangga.py <xau_sambung.json>"""
import sys, os
import numpy as np
import audit_mesin as m
sys.path.insert(0, os.path.join(m.REPO, "riset")); import signifikansi as sg
D = m.muat(sys.argv[1]); A = np.array(m.atr(list(D[2]), list(D[3]), list(D[4]), 14)); F = m.fitur(D, A)
for k in (100, 150, 300, 400):
    F[f"ema{k}"] = m.ema(D[4], k)
J = m.potong(m.replay(D, A=A)); jl = [(int(x["t1"]), float(v)) for x, v in zip(J, m.net(J))]
P = (("pilih", m.PILIH), ("UJI", m.UJI), ("KONF", m.KONF))
print(f"{'varian':<22}" + "".join(f"| {p:<5} R/thn  rasio  " for p, _ in P) + "| P_rasio UJI | slip0,2 UJI R/thn")
def show(nm, spec):
    tr = m.potong(m.jalankan(spec, D, A, F)) if spec else J
    row = f"{nm:<22}"
    for p, (a, b) in P:
        s = m.stat(tr, a=a, b=b); row += f"| {s['rthn']:+6.1f} {s['ratio']:+6.2f} n{s['n']:>4} "
    pl = [(int(x["t1"]), float(v)) for x, v in zip(tr, m.net(tr))]
    r = sg.banding(jl, pl, int(m.ts(m.UJI[0])), int(m.ts(m.UJI[1])))
    print(row + f"| {r['P_rasio_lebih_baik']:.3f}     | {m.stat(tr, slip=0.2, a=m.UJI[0], b=m.UJI[1])['rthn']:+.1f}")
show("juara", None)
for e in ("ema50", "ema100", "ema150", "ema200", "ema300", "ema400", "d_ema20", "d_ema50", "d_ema200"):
    for w in (0.0, 0.5):
        show(f"{e} lawan w{w}", {"tren_lawan_w": (e, w)})
