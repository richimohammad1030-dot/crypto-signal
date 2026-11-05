"""Ide #38b (5 Nov 2026, koreksi pemilik): revenge DENGAN DIAGNOSA. Setelah posisi kena SL (< 23:00), bot menilai kenapa gagal
dari kondisi di candle keputusan (run bot berikutnya, close 09:00..21:00 WIB), lalu memilih aksi: sama (masuk lagi arah sama),
balik (arah sebaliknya), atau lewati. Lot sama. Masuk market, SL 3 ATR, tanpa TP (varian terbaik #38), tutup 23:00.
Diagnosa (ditetapkan sebelum melihat hasil): strategi yang gagal (MR/SUS = fade gagal, K6 = breakout gagal) ×
  tren   : close keputusan vs EMA200 searah posisi yang gagal?   (ya = gagal walau searah tren / tidak = melawan tren)
  cepat  : SL kena <= 2 jam setelah masuk?
  lanjut : harga di close keputusan masih di luar SL (gerak berlanjut) atau sudah kembali?
  rsi    : RSI(2) keputusan ekstrem (q35% jam keputusan) ke arah balik-arah / sama / netral
  vol    : range hari ini (07:00 s.d. keputusan) >= 2,5 ATR?
Langkah 1: tabel rata-rata R per sel di 3 periode (apakah diagnosa memprediksi?). Langkah 2: aturan dipilih di 2015-2021
(per strategi gagal x 1 fitur: aksi terbaik per sel bila rata-rata > 0, selain itu lewati), diuji 2022-Jan 2025 & Setra.
Pemakaian: python revenge_diag.py <xau_sambung.json> <ambigu.json>"""
import sys, os, json
import numpy as np
import audit_mesin as m, strat_mesin as sm, multi_mesin as mm
sys.path.insert(0, os.path.join(m.REPO, "riset")); import signifikansi as sg
D = m.muat(sys.argv[1]); T, O, H, L, C = D
A = np.array(m.atr(list(H), list(L), list(C), 14)); F = m.fitur(D, A)
AMB = {int(k): v for k, v in json.load(open(sys.argv[2])).items()}
HR = ((T // 3600) % 24).astype(int); R2 = mm.rsi(C, 2); E = np.array(m.gb.ema(list(C), 200)); KEP = set(m.gb.SUS_JAM_UTC)
BASE = mm.baseline(D, A, F, ambigu=AMB)
idx = {int(t): i for i, t in enumerate(T)}
BIAYA = 0.40
kasus = []
for x in BASE:
    if x["R"] > -0.999: continue
    j = idx[int(x["t1"])]
    if HR[j] == sm.CLOSE: continue
    q = j
    while q < len(T) and HR[q] not in KEP and HR[q] != sm.CLOSE: q += 1
    if q >= len(T) - 1 or HR[q] not in KEP: continue
    d0 = x["d"]; slp = x["e"] - d0 * x["r0"]
    k0 = q
    while HR[k0] != m.gb.PLACE_HOUR_UTC and k0 > q - 24: k0 -= 1
    rng = (H[k0 + 1:q + 1].max() - L[k0 + 1:q + 1].min()) / A[q]
    rs = "netral"
    if R2[q] <= m.gb.SUS_BUY: rs = "balik" if d0 == -1 else "sama"
    if R2[q] >= m.gb.SUS_SELL: rs = "balik" if d0 == 1 else "sama"
    f = dict(grup="FADE" if x["strat"] in ("MR", "SUS") else "K6",
             tren="searah" if (C[q] > E[q]) == (d0 == 1) else "lawan",
             cepat="cepat" if x["t1"] - x["t0"] <= 2 * 3600 else "lambat",
             lanjut="lanjut" if (slp - C[q]) * d0 > 0 else "kembali",
             rsi=rs, vol="lebar" if rng >= 2.5 else "sempit")
    out = {}
    for aksi, d in (("sama", d0), ("balik", -d0)):
        dist = 3.0 * A[q]; e = O[q + 1]
        ex, t1, why = sm._kelola(D, q + 1, d, e, e - d * dist, None)
        out[aksi] = dict(d=d, e=e, ex=ex, r0=dist, t0=T[q + 1], t1=t1, why=why, w=1.0, ip=x["ip"], i0=q + 1,
                         R=(ex - e) * d / dist, Rn=((ex - e) * d - BIAYA) / dist, strat="REV")
    kasus.append((x, f, out))
print(f"kasus SL yang bisa di-revenge: {len(kasus)}")
PER = (("pilih", m.PILIH), ("uji", m.UJI), ("Setra", m.KONF))
dalam = lambda t, a, b: (a is None or t >= m.ts(a)) and (b is None or t < m.ts(b))

print("\n=== Langkah 1: rata-rata R bersih revenge per sel (n) · pilih | uji | Setra")
for grup in ("FADE", "K6"):
    for fit in ("tren", "cepat", "lanjut", "rsi", "vol"):
        nilai = sorted({f[fit] for x, f, o in kasus if f["grup"] == grup})
        for v in nilai:
            row = []
            for aksi in ("sama", "balik"):
                cel = []
                for pn, (a, b) in PER:
                    r = [o[aksi]["Rn"] for x, f, o in kasus if f["grup"] == grup and f[fit] == v and dalam(x["t1"], a, b)]
                    cel.append(f"{np.mean(r) if r else 0:+.2f}({len(r)})")
                row.append(f"{aksi}: " + " | ".join(cel))
            print(f"{grup:<4} {fit:<6} {v:<7} " + "   ".join(row))

print("\n=== Langkah 2: aturan dipilih di 2015-2021, gabung dengan baseline live (R/thn), P uji vs baseline")
jl = [(int(x["t1"]), float(v)) for x, v in zip(BASE, m.net(BASE))]
P4 = PER + (("12t", (None, None)),)
s0 = {pn: sm.ringkas(BASE, a, b)["rthn"] for pn, (a, b) in P4}
print("BASELINE        " + " · ".join(f"{pn} {v:+.1f}" for pn, v in s0.items()))
for fit in ("tren", "cepat", "lanjut", "rsi", "vol"):
    aturan = {}
    for x, f, o in kasus:
        if dalam(x["t1"], *m.PILIH): aturan.setdefault((f["grup"], f[fit]), {"sama": [], "balik": []})
    for (g, v) in aturan:
        best, bv = None, 0.0
        for aksi in ("sama", "balik"):
            r = [o[aksi]["Rn"] for x, f, o in kasus if f["grup"] == g and f[fit] == v and dalam(x["t1"], *m.PILIH)]
            if len(r) >= 20 and np.mean(r) > bv: best, bv = aksi, np.mean(r)
        aturan[(g, v)] = best
    rv = [o[aturan.get((f["grup"], f[fit]))] for x, f, o in kasus if aturan.get((f["grup"], f[fit]))]
    G = sorted(BASE + rv, key=lambda z: z["t1"]); gl = [(int(x["t1"]), float(v)) for x, v in zip(G, m.net(G))]
    pr = sg.banding(jl, gl, int(m.ts(m.UJI[0])), int(m.ts(m.UJI[1])))["P_rasio_lebih_baik"]
    s = {pn: sm.ringkas(G, a, b) for pn, (a, b) in P4}; r = {pn: sm.ringkas(rv, a, b) for pn, (a, b) in P4}
    atur = ", ".join(f"{g}/{v}->{a}" for (g, v), a in sorted(aturan.items()) if a) or "tidak ada"
    print(f"{fit:<6} n{len(rv):>4} " + " · ".join(f"{pn} {s[pn]['rthn']:+.1f}" for pn, _ in P4)
          + " | rev PF " + "/".join(f"{r[pn]['pf']:.2f}" for pn, _ in P4) + f" | DD {s['12t']['dd']:.0f}R | P {pr:.2f} | {atur}")
