"""Audit XAU ide baru: filter kurva ekuitas. Trade hanya jika jumlah R bersih N trade bayangan terakhir (strategi dasar
tanpa filter, trade yang SUDAH tutup sebelum order 07:00) > 0. Hari independen (1 trade/hari), jadi filter = saring pasca-replay.
SELEKSI N di 2015-2021. Pemakaian: python audit_ekuitas.py <xau_sambung.json>"""
import sys, os
import numpy as np
import audit_mesin as m
sys.path.insert(0, os.path.join(m.REPO, "riset")); import signifikansi as sg
D = m.muat(sys.argv[1]); A = np.array(m.atr(list(D[2]), list(D[3]), list(D[4]), 14)); F = m.fitur(D, A)
J = m.potong(m.replay(D, A=A)); jl = [(int(x["t1"]), float(v)) for x, v in zip(J, m.net(J))]
def saring(base, N):
    r = m.net(base); t1 = np.array([x["t1"] for x in base]); out = []
    for x in base:
        tp = D[0][x["ip"]]; j = np.searchsorted(t1, tp, side="left")    # trade tutup sebelum order dipasang
        if j >= N and r[j - N:j].sum() > 0: out.append(x)
    return out
P = (("pilih", m.PILIH), ("UJI", m.UJI), ("KONF", m.KONF))
for nm, base in (("juara", J), ("K6 ema200 w0", m.potong(m.jalankan({"tren_lawan_w": ("ema200", 0.0)}, D, A, F)))):
    for N in (0, 20, 40, 60, 100, 150):
        tr = base if N == 0 else saring(base, N); row = f"{nm} N={N:<4}"
        for p, (a, b) in P:
            s = m.stat(tr, a=a, b=b); row += f"| {p} {s['rthn']:+6.1f}R/thn rasio {s['ratio']:+5.2f} n{s['n']:>4} "
        pl = [(int(x["t1"]), float(v)) for x, v in zip(tr, m.net(tr))]
        print(row + f"| P UJI {sg.banding(jl, pl, int(m.ts(m.UJI[0])), int(m.ts(m.UJI[1])))['P_rasio_lebih_baik']:.3f}")
