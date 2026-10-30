"""Pemilih rezim HARIAN (31 Okt 2026): tiap 07:00 hitung efficiency ratio (ER) close harian N hari terakhir (data s.d. hari itu).
ER >= ambang (median 2015-2021) -> pakai K6 (breakout searah tren); ER < ambang -> pakai RSI2 fade (limit/market mean reversion).
Ambang & N dipilih HANYA di 2015-2021. Pemakaian: python rezim_harian.py <xau_sambung.json> <ambigu.json>"""
import sys, json, pickle
import numpy as np
import audit_mesin as m
import strat_mesin as sm
import harian_mesin as hm
D = m.muat(sys.argv[1]); A = np.array(m.atr(list(D[2]), list(D[3]), list(D[4]), 14)); F = m.fitur(D, A)
AMB = {int(k): v for k, v in json.load(open(sys.argv[2])).items()}
idx, dh, dl, dc, datr = hm.harian(D)
K6 = m.potong(m.jalankan({"tren_lawan_w": ("ema200", 0.0), "ambigu": AMB}, D, A, F))
MR = pickle.load(open("/tmp/data/mr_top.pkl", "rb"))[("RSI2", 0.35, "tanpa", "market", 3.0, None)][0]
kk = {x["ip"]: x for x in K6}; mm = {x["ip"]: x for x in MR}
pos = {i: j for j, i in enumerate(idx)}
for N in (5, 10, 20, 40):
    er = np.full(len(idx), np.nan)
    for j in range(N, len(idx)):
        c = dc[j - N:j + 1]; er[j] = abs(c[-1] - c[0]) / max(np.sum(np.abs(np.diff(c))), 1e-9)
    thr = np.nanmedian([er[j] for j, i in enumerate(idx) if D[0][i] < m.ts("2022-01-01")])
    for nm, pilih in (("K6 bila tren, RSI2 bila sideways", lambda e: "K6" if e >= thr else "MR"),
                      ("kebalikan (uji kontrol)", lambda e: "MR" if e >= thr else "K6")):
        tr = []
        for j, i in enumerate(idx):
            if np.isnan(er[j]): continue
            x = (kk if pilih(er[j]) == "K6" else mm).get(i)
            if x: tr.append(x)
        tr.sort(key=lambda x: x["t1"]); out = []
        for pn, (a, b) in (("pilih", m.PILIH), ("uji", m.UJI), ("Setra", m.KONF)):
            s = sm.ringkas(tr, a, b)
            out.append(f"{pn} /mg {s['per_mg']:.1f} win {s['wr']*100:.0f}% rr {s['rr']:.2f} pf {s['pf']:.2f} R/thn {s['rthn']:+.1f} W/L {s['wmax']}/{s['lmax']}")
        print(f"N={N:>2} {nm:<32} | " + " | ".join(out))
for nm, tr in (("K6 saja", K6), ("RSI2 saja", MR)):
    print(f"{nm:<38} | " + " | ".join(f"{pn} pf {sm.ringkas(tr, a, b)['pf']:.2f} R/thn {sm.ringkas(tr, a, b)['rthn']:+.1f}"
                                     for pn, (a, b) in (("pilih", m.PILIH), ("uji", m.UJI), ("Setra", m.KONF))))
