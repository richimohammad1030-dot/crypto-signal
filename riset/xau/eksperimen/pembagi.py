"""Ide #41 (5 Nov 2026, pemilik): sistem yang strateginya saling menutup celah = PEMBAGI TUGAS. Setiap hari (keputusan 07:00)
masuk satu SEL kondisi; tiap sel diberi strategi terbaik di 2015-2021: MR (fade RSI2), K6 (+susulan bila K6 dilewati), atau kosong.
Kompleksitas naik: L1 sel RSI2 (7 kelompok) · L2 RSI2 x tren EMA200 · L3 RSI2 x tren x ATR relatif (3) · L4 L3 x hari (5).
Sel dengan < 30 hari di 2015-2021 memakai pilihan bot sekarang. Diuji 2022-Jan 2025 & Setra; P vs baseline.
Pemakaian: python pembagi.py <xau_sambung.json> <ambigu.json>"""
import sys, os, json, itertools
import numpy as np
import audit_mesin as m, strat_mesin as sm, multi_mesin as mm
sys.path.insert(0, os.path.join(m.REPO, "riset")); import signifikansi as sg
D = m.muat(sys.argv[1]); T, O, H, L, C = D
A = np.array(m.atr(list(H), list(L), list(C), 14)); F = m.fitur(D, A)
AMB = {int(k): v for k, v in json.load(open(sys.argv[2])).items()}
HR = ((T // 3600) % 24).astype(int); R2 = mm.rsi(C, 2); E = np.array(m.gb.ema(list(C), 200))
BASE = mm.baseline(D, A, F, ambigu=AMB)
for x, r in zip(BASE, m.net(BASE)): x["Rn"] = float(r)
# hasil tiap opsi per hari
semua = {int(i): (1 if R2[i] <= 50 else -1) for i in np.flatnonzero(HR == sm.PLACE) if R2[i] <= m.gb.MR_BUY or R2[i] >= m.gb.MR_SELL}
mr = {x["ip"]: [x] for x in mm.trades_mr(D, A, semua)}
k6 = {}
for x in mm.baseline(D, A, F, ambigu=AMB, sig={}): k6.setdefault(x["ip"], []).append(x)
for d in (mr, k6):
    for v in d.values():
        for x, r in zip(v, m.net(v)): x["Rn"] = float(r)
hari = [int(i) for i in np.flatnonzero(HR == sm.PLACE) if 250 <= i < len(T) - 1]
def rsi_k(r):
    for b, nm in ((10, "b<10"), (25, "b10-25"), (m.gb.MR_BUY, "b25-44"), (m.gb.MR_SELL, "netral"), (85, "s71-85"), (95, "s85-95")):
        if r < b: return nm
    return "s>95"
def atr_k(i):
    v = A[i] / np.median(A[max(0, i - 500):i + 1]); return "atr<0,9" if v < 0.9 else "atr0,9-1,2" if v < 1.2 else "atr>1,2"
WD = lambda i: (int(T[i]) // 86400 + 3) % 7
FIT = {"L1 RSI": lambda i: (rsi_k(R2[i]),),
       "L2 RSI x tren": lambda i: (rsi_k(R2[i]), C[i] > E[i]),
       "L3 RSI x tren x ATR": lambda i: (rsi_k(R2[i]), C[i] > E[i], atr_k(i)),
       "L4 L3 x hari": lambda i: (rsi_k(R2[i]), C[i] > E[i], atr_k(i), WD(i))}
def opsi_hari(i, o):
    return mr.get(i, []) if o == "MR" else k6.get(i, []) if o == "K6" else []
def default(i): return "MR" if i in semua else "K6"
pl = lambda i: T[i] < m.ts("2022-01-01")
jl = [(int(x["t1"]), float(x["Rn"])) for x in BASE]
P4 = (("2015-21", m.PILIH), ("2022-Jan25", m.UJI), ("Setra", m.KONF), ("12t", (None, None)))
def lapor(nm, G, extra=""):
    G = sorted(G, key=lambda z: z["t1"]); gl = [(int(x["t1"]), float(x["Rn"])) for x in G]
    pu = sg.banding(jl, gl, int(m.ts(m.UJI[0])), int(m.ts(m.UJI[1])))["P_rasio_lebih_baik"]
    pk = sg.banding(jl, gl, int(m.ts(m.KONF[0])), int(T[-1]))["P_rasio_lebih_baik"]
    s = {pn: sm.ringkas(G, a, b) for pn, (a, b) in P4}
    print(f"{nm:<22} " + " · ".join(f"{s[pn]['rthn']:+5.1f}" for pn, _ in P4) + f" | /mg {s['12t']['per_mg']:.1f} PF {s['12t']['pf']:.2f} DD {s['12t']['dd']:.0f}R"
          f" | P uji {pu:.2f} Setra {pk:.2f} {extra}")
print("R/thn: 2015-21 (dipakai memilih) · 2022-Jan25 · Setra · 12 thn")
lapor("BASELINE live", BASE)
for nm, f in FIT.items():
    sel = {}
    for i in hari:
        if pl(i): sel.setdefault(f(i), []).append(i)
    pilih = {}
    for k, ii in sel.items():
        if len(ii) < 30: continue
        opsi = ["K6", ""] + (["MR"] if any(j in semua for j in ii) else [])
        pilih[k] = max(opsi, key=lambda o: sum(x["Rn"] for j in ii for x in opsi_hari(j, o)))
    G = [x for i in hari for x in opsi_hari(i, pilih.get(f(i), default(i)))]
    beda = sum(1 for k, ii in sel.items() if k in pilih and pilih[k] != default(ii[0]))
    lapor(nm, G, f"| sel {len(sel)} (aktif {len(pilih)}, diubah {beda})")
