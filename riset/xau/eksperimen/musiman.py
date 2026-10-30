"""Musiman kalender: R bersih per bulan kalender (juara & K6, urutan M1 2022-skrg), 2015-2021 vs 2022-skrg.
Jika musiman nyata, peringkat bulan di kedua periode harus mirip (korelasi Spearman tinggi).
Pemakaian: python musiman.py <xau_sambung.json> <ambigu_sisi.json>"""
import sys, json
import numpy as np
from scipy.stats import spearmanr
import audit_mesin as m
D = m.muat(sys.argv[1]); A = np.array(m.atr(list(D[2]), list(D[3]), list(D[4]), 14)); F = m.fitur(D, A)
AMB = {int(k): v for k, v in json.load(open(sys.argv[2])).items()}
for nm, sp in (("juara", {}), ("K6", {"tren_lawan_w": ("ema200", 0.0)})):
    tr = m.potong(m.jalankan(dict(sp, ambigu=AMB), D, A, F)); r = m.net(tr)
    a, b = np.zeros(12), np.zeros(12)
    for x, v in zip(tr, r):
        w = m.wib(x["t0"]); (a if w.year < 2022 else b)[w.month - 1] += v
    rho, p = spearmanr(a, b)
    print(f"{nm}: R per bulan 2015-21 :", " ".join(f"{v:+5.0f}" for v in a))
    print(f"{nm}: R per bulan 2022-skrg:", " ".join(f"{v:+5.0f}" for v in b))
    print(f"   korelasi peringkat bulan antar periode: {rho:+.2f} (p={p:.2f})")
    yrs = sorted({m.wib(x['t0']).year for x in tr}); pos = np.zeros(12); cnt = np.zeros(12)
    for y in yrs:
        for mo in range(12):
            s = sum(v for x, v in zip(tr, r) if m.wib(x['t0']).year == y and m.wib(x['t0']).month == mo + 1)
            if any(m.wib(x['t0']).year == y and m.wib(x['t0']).month == mo + 1 for x in tr): cnt[mo] += 1; pos[mo] += s > 0
    print("   % tahun positif per bulan:", " ".join(f"{p_/c*100:3.0f}" for p_, c in zip(pos, cnt)))
