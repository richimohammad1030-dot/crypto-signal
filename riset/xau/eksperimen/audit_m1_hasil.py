"""Audit XAU: hasil setelah urutan candle ambigu dipastikan dengan M1 Dukascopy (audit_m1.py).
Hari ambigu yang belum punya data M1 tetap memakai asumsi bot (BUY). Pemakaian: python audit_m1_hasil.py <xau_sambung.json>"""
import sys, os, json
import numpy as np
import audit_mesin as m
sys.path.insert(0, os.path.join(m.REPO, "riset")); import signifikansi as sg
D = m.muat(sys.argv[1]); A = np.array(m.atr(list(D[2]), list(D[3]), list(D[4]), 14)); F = m.fitur(D, A)
SISI = "/tmp/data/ambigu_sisi.json" if os.path.exists("/tmp/data/ambigu_sisi.json") else \
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "ambigu_m1_2022_2026.json")
amb = {int(k): v for k, v in json.load(open(SISI)).items()}
v = list(amb.values()); print(f"Hari ambigu terselesaikan: {len(amb)} (BUY duluan {v.count(1)}, SELL duluan {v.count(-1)}, tetap ambigu {v.count(0)})")
for pn, (a, b) in (("uji", m.UJI), ("konf", m.KONF)):
    ks = [k for k in amb if (a is None or k >= m.ts(a)) and (b is None or k < m.ts(b))]
    print(f"  {pn}: {len(ks)} hari, BUY {sum(amb[k]==1 for k in ks)}, SELL {sum(amb[k]==-1 for k in ks)}, ambigu {sum(amb[k]==0 for k in ks)}")
K = {"juara": {}, "K6": {"tren_lawan_w": ("ema200", 0.0)}, "K6b": {"tren_lawan_w": ("ema200", 0.5)}}
res = {}
for nm, sp in K.items():
    for mode in ("buy", "m1"):
        tr = m.potong(m.jalankan(dict(sp, ambigu="buy" if mode == "buy" else amb), D, A, F)); res[(nm, mode)] = tr
        out = []
        for pn, (a, b) in (("uji", m.UJI), ("konf", m.KONF)):
            s = m.stat(tr, a=a, b=b); out.append(f"{pn} {s['rthn']:+6.1f}R/thn exp {s['avg']:+.3f} DD {s['dd']:5.1f} rasio {s['ratio']:+.2f}")
        print(f"{nm:<6} {mode:<4}", " | ".join(out))
print("\nSignifikansi vs juara (keduanya urutan M1):")
J = res[("juara", "m1")]; jl = [(int(x["t1"]), float(r)) for x, r in zip(J, m.net(J))]
for nm in ("K6", "K6b"):
    P = res[(nm, "m1")]; pl = [(int(x["t1"]), float(r)) for x, r in zip(P, m.net(P))]
    for pn, (a, b) in (("uji", m.UJI), ("konf", m.KONF)):
        r = sg.banding(jl, pl, int(m.ts(a)), int(m.ts(b)) if b else None)
        print(f"  {nm} {pn}: P_rasio {r['P_rasio_lebih_baik']:.3f} juara {r['juara']} penantang {r['penantang']}")
json.dump({f"{k[0]}|{k[1]}": [[int(x["t0"]), int(x["t1"]), x["d"], float(r)] for x, r in zip(v_, m.net(v_))] for k, v_ in res.items()},
          open("/tmp/data/m1_trades.json", "w"))
