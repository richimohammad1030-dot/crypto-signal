"""Optimasi ide #37 S3 (sinyal susulan RSI2 pada hari K6 dilewati) - 5 Nov 2026, permintaan pemilik.
Dinilai sebagai GABUNGAN dengan baseline (MR + K6), maks 1 posisi/hari. SELEKSI hanya 2015-2021: kriteria pemilik pada gabungan
+ skor tetangga (kuantil, SL, TP). Grid: kuantil RSI2 {25..50%} x SL {1..3 ATR} x TP {1, 1,5, 2, 3R, tanpa} x masuk {market,
limit 0,25 ATR} x batas jam {09:00 saja, s.d. 13:00, s.d. 21:00 WIB} x filter arah {tanpa, searah tren, lawan tren}.
Pemakaian: python susulan_opt.py <xau_sambung.json> <ambigu.json>"""
import sys, itertools
import numpy as np
exec(open(__file__.replace("susulan_opt.py", "susulan.py")).read().split("pl_q = ")[0])   # data, BASE, hari, jalan_di

pl_q = [q for ip, q, *_ in hari if T[q] < m.ts("2022-01-01")]
QS, SLS, TPS = (0.25, 0.30, 0.35, 0.40, 0.45, 0.50), (1.0, 1.5, 2.0, 2.5, 3.0), (1, 1.5, 2, 3, None)
MASUK, BATAS, FILT = ("market", "limit"), (1, 5, 13), ("tanpa", "searah tren", "lawan tren")
AMBANG = {q: (np.quantile(R2[pl_q], q), np.quantile(R2[pl_q], 1 - q)) for q in QS}


def rencana(q_, masuk, batas, filt):
    lo_, hi_ = AMBANG[q_]; out = []
    for ip, q, tr, hi, lo in hari:
        if HR[q] > batas: continue
        d = 1 if R2[q] <= lo_ else (-1 if R2[q] >= hi_ else 0)
        if d and filt == "searah tren" and d != tr: d = 0
        if d and filt == "lawan tren" and d == tr: d = 0
        if not d: continue
        out.append((ip, q, [(d, "market", None)] if masuk == "market" else [(d, "limit", C[q] - d * 0.25 * A[q])]))
    return out


def lulus(s):
    return s["wr"] >= 0.40 and s["pf"] > 1.0 and s["per_mg"] >= 3.0 and s["lmax"] <= s["wmax"] + 4 and s["thn_pos"] > s["thn_n"] / 2


SUS, GAB = {}, {}
for q_, ms, bt, fl in itertools.product(QS, MASUK, BATAS, FILT):
    rc = rencana(q_, ms, bt, fl)
    for sl, tp in itertools.product(SLS, TPS):
        tr = jalan_di(rc, sl, tp); k = (q_, sl, tp, ms, bt, fl)
        SUS[k] = tr; GAB[k] = sm.ringkas(sorted(BASE + tr, key=lambda x: x["t1"]), *m.PILIH)
print(len(GAB), "kombinasi")
B0 = sm.ringkas(BASE, *m.PILIH)
print(f"BASELINE pilih: R/thn {B0['rthn']:+.1f} rasio {B0['ratio']:.2f} PF {B0['pf']:.2f}")


def tetangga(k):
    q_, sl, tp, ms, bt, fl = k; o = []
    for vals, idx in ((QS, 0), (SLS, 1), (TPS, 2)):
        j = vals.index(k[idx])
        for jj in (j - 1, j + 1):
            if 0 <= jj < len(vals): o.append(k[:idx] + (vals[jj],) + k[idx + 1:])
    return o


rows = []
for k, s in GAB.items():
    if not lulus(s) or len(m.potong(SUS[k], *m.PILIH)) < 60: continue
    nb = [GAB[j]["ratio"] for j in tetangga(k)]
    rows.append((min(s["ratio"], np.mean(nb)), k, s, sum(lulus(GAB[j]) for j in tetangga(k)), len(nb)))
rows.sort(key=lambda r: -r[0])
print(f"Lulus kriteria pemilik (gabungan, pilih) & >= 60 trade susulan: {len(rows)}")
jl = [(int(x["t1"]), float(v)) for x, v in zip(BASE, m.net(BASE))]
DEF = (0.35, 3.0, 1, "market", 13, "tanpa")
print("\nTOP 10 menurut skor tetangga (pilih), lalu hasil uji & Setra:")
for sk, k, s, nl, nn in rows[:10]:
    tr = SUS[k]; G = sorted(BASE + tr, key=lambda x: x["t1"]); gl = [(int(x["t1"]), float(v)) for x, v in zip(G, m.net(G))]
    p = sg.banding(jl, gl, int(m.ts(m.UJI[0])), int(m.ts(m.UJI[1])))["P_rasio_lebih_baik"]
    line = []
    for pn, (a, b) in (("pilih", m.PILIH), ("uji", m.UJI), ("Setra", m.KONF)):
        g = sm.ringkas(G, a, b); x = sm.ringkas(tr, a, b)
        line.append(f"{pn}: gab {g['rthn']:+.1f} sus PF {x['pf']:.2f} n{x['n']}")
    print(f"skor {sk:+.2f} tet {nl}/{nn} {k}{'  (versi awal)' if k == DEF else ''}\n   " + " | ".join(line) + f" | P uji {p:.2f}")
import pickle; pickle.dump({"rows": [(r[0], r[1]) for r in rows[:30]], "sus": {r[1]: SUS[r[1]] for r in rows[:30]}, "def": SUS.get(DEF)},
                          open("/tmp/data/susulan_opt.pkl", "wb"))
