"""PEMBANDING SAJA (melanggar aturan pemilik 'tutup 23:00', bukan kandidat): swing emas multi-hari gaya bot crypto
(breakout 20 hari stop order, SL 8 ATR harian, trailing low/high 3 hari, cut-loss stagnan umur >= 2 hari & R < -0,2,
TP 25% di +1R), bar harian 24 jam berakhir 07:00 WIB, biaya 0,40 USD. Juga: kandidat tren harian teratas di periode uji (info).
Pemakaian: python swing_pembanding.py <xau_sambung.json>"""
import sys
import numpy as np
import audit_mesin as m
import harian_mesin as hm
D = m.muat(sys.argv[1]); T = D[0]
idx, dh, dl, dc, datr = hm.harian(D)
do = np.r_[dc[0], dc[:-1]]                         # open hari = close hari sebelumnya (pendekatan)
tr, pos = [], None
for j in range(21, len(idx)):
    t = T[idx[j]]
    if pos:
        d = pos["d"]
        if (d == 1 and dl[j] <= pos["sl"]) or (d == -1 and dh[j] >= pos["sl"]):
            ex = pos["sl"]; why = "SL"
        else:
            ex = None
            if not pos["tp"] and ((d == 1 and dh[j] >= pos["e"] + pos["r0"]) or (d == -1 and dl[j] <= pos["e"] - pos["r0"])):
                pos["tp"] = True
            Rn = (dc[j] - pos["e"]) * d / pos["r0"]
            if j - pos["j0"] >= 2 and Rn < -0.2: ex = dc[j]; why = "stagnan"
            else:
                pos["sl"] = max(pos["sl"], dl[j - 2:j + 1].min()) if d == 1 else min(pos["sl"], dh[j - 2:j + 1].max())
        if ex is not None:
            R = (ex - pos["e"]) * d / pos["r0"]; R = 0.25 * 1 + 0.75 * R if pos["tp"] else R
            tr.append(dict(d=d, e=pos["e"], r0=pos["r0"], t0=pos["t0"], t1=t, R=R, w=1.0, why=why)); pos = None
        continue
    hi20, lo20, a = dh[j - 20:j].max(), dl[j - 20:j].min(), datr[j - 1]
    if np.isnan(a): continue
    for d, lvl in ((1, hi20), (-1, lo20)):
        if (d == 1 and dh[j] >= lvl) or (d == -1 and dl[j] <= lvl):
            e = max(lvl, do[j]) if d == 1 else min(lvl, do[j]); r0 = 8 * a
            pos = dict(d=d, e=e, sl=e - d * r0, r0=r0, t0=t, j0=j, tp=False); break
for nm, (a, b) in (("pilih 2015-21", m.PILIH), ("uji 2022-Jan25", m.UJI), ("Setra-era", m.KONF), ("semua", (None, None))):
    print(m.baris(f"swing emas (pembanding) {nm}", m.stat(tr, a=a, b=b)))
print("per tahun:", m.stat(tr)["thn"])
A = np.array(m.atr(list(D[2]), list(D[3]), list(D[4]), 14))
t2 = hm.simulasi(D, A, hm.arah_harian(dh, dl, dc, "mom", 60), idx, masuk="market", sl=3.0, rr=4)
for nm, (a, b) in (("pilih", m.PILIH), ("uji", m.UJI), ("Setra-era", m.KONF)):
    print(m.baris(f"tren harian terbaik (mom60 market SL3 TP4) {nm}", m.stat(t2, a=a, b=b)))
