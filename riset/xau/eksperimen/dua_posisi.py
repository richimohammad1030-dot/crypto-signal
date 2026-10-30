"""Risiko 2 posisi dalam 1 hari (portofolio K6 + RSI2) vs aturan maks 1 posisi/hari. R bersih, bobot risiko per strategi.
Pemakaian: python dua_posisi.py <xau_sambung.json> <ambigu.json>"""
import sys, json, pickle
import numpy as np
import audit_mesin as m
import strat_mesin as sm
D = m.muat(sys.argv[1]); A = np.array(m.atr(list(D[2]), list(D[3]), list(D[4]), 14)); F = m.fitur(D, A)
AMB = {int(k): v for k, v in json.load(open(sys.argv[2])).items()}
K6 = m.potong(m.jalankan({"tren_lawan_w": ("ema200", 0.0), "ambigu": AMB}, D, A, F))
MR = pickle.load(open("/tmp/data/mr_top.pkl", "rb"))[("RSI2", 0.35, "tanpa", "market", 3.0, None)][0]
hari = lambda x: m.wib(D[0][x["ip"]] + 3600).date()
k = {hari(x): x for x in K6}; r = {hari(x): x for x in MR}
both = sorted(set(k) & set(r)); semua = sorted(set(k) | set(r))
nk, nr = dict(zip([hari(x) for x in K6], m.net(K6))), dict(zip([hari(x) for x in MR], m.net(MR)))
searah = sum(k[d]["d"] == r[d]["d"] for d in both)
sl2 = sum(nk[d] < -0.9 and nr[d] < -0.9 for d in both)
print(f"Hari dengan trade: {len(semua)} | hari 2 posisi: {len(both)} ({len(both)/len(semua)*100:.0f}%) | searah {searah}, berlawanan {len(both)-searah}")
print(f"Hari 2 posisi & KEDUANYA kena SL: {sl2} ({sl2/len(semua)*100:.1f}% dari hari trade, ±{sl2/11.8:.0f} kali/tahun)")
print(f"Korelasi R K6 vs RSI2 di hari yang sama: {np.corrcoef([nk[d] for d in both],[nr[d] for d in both])[0,1]:+.2f}")
def evalu(nm, harian, w_ket):
    v = np.array(list(harian.values())); eq = np.cumsum(v); dd = (np.maximum.accumulate(np.concatenate([[0], eq]))[1:] - eq).max()
    e = np.cumprod(1 + 0.01 * v); ddp = (1 - e / np.maximum.accumulate(e)).max() * 100
    s = st = 0
    for x in v: s = s + 1 if x < 0 else 0; st = max(st, s)
    print(f"{nm:<44} rugi/hari terburuk {v.min():+.2f}% | hari rugi ≤ -1%: {np.sum(v <= -0.99)} | hari rugi beruntun {st} | "
          f"total {v.sum():+.0f}% | DD {dd:.1f}% (majemuk {ddp:.1f}%) {w_ket}")
# R per hari dalam "% modal" (1R = 1% x bobot)
for w in (0.5, 1.0):
    h = {}
    for d in semua: h[d] = w * nk.get(d, 0) + w * nr.get(d, 0)
    evalu(f"K6 {w}% + RSI2 {w}% (boleh 2 posisi)", h, "")
# maks 1 posisi per hari: prioritas K6, RSI2 hanya bila K6 tidak trade hari itu
for w in (0.5, 1.0):
    h = {d: w * (nk[d] if d in nk else nr[d]) for d in semua}
    tr = [k[d] if d in k else r[d] for d in semua]
    evalu(f"maks 1 posisi/hari (K6 dulu, lalu RSI2) {w}%", h, "")
    s = sm.ringkas(sorted(tr, key=lambda x: x["t1"]))
    print(f"   -> {s['per_mg']:.1f} trade/mg, win {s['wr']*100:.0f}%, RR {s['rr']:.2f}, PF {s['pf']:.2f}, W/L {s['wmax']}/{s['lmax']}, thn+ {s['thn_pos']}/{s['thn_n']} | "
          + " ".join(f"{pn} PF {sm.ringkas(tr, a, b)['pf']:.2f}" for pn, (a, b) in (("2015-21", m.PILIH), ("2022-25", m.UJI), ("Setra", m.KONF))))
evalu("K6 saja 1%", {d: nk[d] for d in nk}, "")
evalu("Juara lama saja 1% (pembanding)", {hari(x): v for x, v in zip(*(lambda t: (t, m.net(t)))(m.potong(m.jalankan({'ambigu': AMB}, D, A, F))))}, "")
