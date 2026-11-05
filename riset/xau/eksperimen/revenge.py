"""Ide #38 (5 Nov 2026, pertanyaan pemilik): aturan "revenge" setelah kena SL - posisi ke-2 di hari yang sama, LOT/RISIKO SAMA
(bukan martingale). Realistis jadwal bot: SL diketahui di run berikutnya; keputusan di candle pertama yang close 09:00..21:00 WIB
pada/setelah candle SL, masuk market di open berikutnya, tutup 23:00 WIB. Varian: arah sama / berbalik × syarat (tanpa / RSI2
ekstrem searah) × SL 1,5/3 ATR × TP 1R/2R/tanpa. Seleksi 2015-2021 atas GABUNGAN (baseline live + revenge); uji 2022-Jan 2025; Setra.
Pemakaian: python revenge.py <xau_sambung.json> <ambigu.json>"""
import sys, os, json, itertools
import numpy as np
import audit_mesin as m, strat_mesin as sm, multi_mesin as mm
sys.path.insert(0, os.path.join(m.REPO, "riset")); import signifikansi as sg
D = m.muat(sys.argv[1]); T, O, H, L, C = D
A = np.array(m.atr(list(H), list(L), list(C), 14)); F = m.fitur(D, A)
AMB = {int(k): v for k, v in json.load(open(sys.argv[2])).items()}
HR = ((T // 3600) % 24).astype(int); R2 = mm.rsi(C, 2); KEP = set(m.gb.SUS_JAM_UTC)
BASE = mm.baseline(D, A, F, ambigu=AMB)
idx = {int(t): i for i, t in enumerate(T)}
sl_hari = []
for x in BASE:
    if x["R"] > -0.999: continue
    j = idx[int(x["t1"])]
    if HR[j] == sm.CLOSE: continue
    q = j
    while q < len(T) and HR[q] not in KEP and HR[q] != sm.CLOSE: q += 1
    if q >= len(T) - 1 or HR[q] not in KEP: continue
    sl_hari.append((x, q))
print(f"trade baseline {len(BASE)}, kena SL {sum(1 for x in BASE if x['R'] <= -0.999)}, bisa revenge (keputusan <=21:00): {len(sl_hari)}")


def jalan(arah, syarat, sl, tp):
    out = []
    for x, q in sl_hari:
        d = x["d"] if arah == "sama" else -x["d"]
        if syarat == "rsi" and not ((d == 1 and R2[q] <= m.gb.SUS_BUY) or (d == -1 and R2[q] >= m.gb.SUS_SELL)): continue
        dist = sl * A[q]
        if dist <= 0.5: continue
        j = q + 1; e = O[j]
        ex, t1, why = sm._kelola(D, j, d, e, e - d * dist, e + d * tp * dist if tp else None)
        out.append(dict(d=d, e=e, ex=ex, r0=dist, t0=T[j], t1=t1, why=why, w=1.0, ip=x["ip"], i0=j, R=(ex - e) * d / dist, strat="REV"))
    return out


jl = [(int(x["t1"]), float(v)) for x, v in zip(BASE, m.net(BASE))]
P = (("pilih", m.PILIH), ("uji", m.UJI), ("Setra", m.KONF), ("12t", (None, None)))
print("\nGABUNGAN vs baseline live (R/thn) | revenge saja PF per periode | P uji")
s0 = {pn: sm.ringkas(BASE, a, b) for pn, (a, b) in P}
print("BASELINE           " + " · ".join(f"{pn} {s0[pn]['rthn']:+.1f}" for pn, _ in P) + f" | DD {s0['12t']['dd']:.0f}R W/L {s0['12t']['wmax']}/{s0['12t']['lmax']}")
for arah, syarat, sl, tp in itertools.product(("sama", "balik"), ("tanpa", "rsi"), (1.5, 3.0), (1, 2, None)):
    rv = jalan(arah, syarat, sl, tp); G = sorted(BASE + rv, key=lambda z: z["t1"])
    gl = [(int(x["t1"]), float(v)) for x, v in zip(G, m.net(G))]
    pr = sg.banding(jl, gl, int(m.ts(m.UJI[0])), int(m.ts(m.UJI[1])))["P_rasio_lebih_baik"]
    s = {pn: sm.ringkas(G, a, b) for pn, (a, b) in P}; r = {pn: sm.ringkas(rv, a, b) for pn, (a, b) in P}
    print(f"{arah:<5} {syarat:<5} SL{sl} TP{tp or '-':<4} n{len(rv):>4} " + " · ".join(f"{pn} {s[pn]['rthn']:+.1f}" for pn, _ in P)
          + f" | rev PF " + "/".join(f"{r[pn]['pf']:.2f}" for pn, _ in P) + f" | DD {s['12t']['dd']:.0f}R W/L {s['12t']['wmax']}/{s['12t']['lmax']} | P {pr:.2f}")
