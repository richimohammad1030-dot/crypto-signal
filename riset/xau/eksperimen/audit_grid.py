"""Audit XAU tahap 2a: grid kombinasi kecil, SELEKSI HANYA DI 2015-2021.
Skor = min(rasio R/DD varian, rata-rata rasio tetangganya) agar tidak memilih puncak tunggal.
Syarat: >= 100 trade di periode pilih, positif tanpa 2% trade terbaik.
Pemakaian: python audit_grid.py <xau_panjang.json>  -> /tmp/data/grid_pilih.json"""
import sys, json, itertools
import numpy as np
import audit_mesin as m

D = m.muat(sys.argv[1])
A = np.array(m.atr(list(D[2]), list(D[3]), list(D[4]), m.gb.ATR_N))
F = m.fitur(D, A)
FILT = [None, ("vol", 0.0030), ("vol", 0.0035), ("vol", 0.0040), ("biaya", 0.04), ("biaya", 0.05), ("biaya", 0.06)]
SL = [1.5, 2.0, 2.5]
TP = [4, None]
RG = [(23, 3), (23, 1), (0, 4)]


def spec_of(f, sl, tp, rg):
    s = {"sl_atr": sl, "rr": tp, "place_hr": rg[0], "range_n": rg[1]}
    if f and f[0] == "vol": s["vol"] = ("atr_rel", f[1])
    if f and f[0] == "biaya": s["biaya_maks"] = f[1]
    return s


res = {}
for f, sl, tp, rg in itertools.product(FILT, SL, TP, RG):
    s = m.stat(m.jalankan(spec_of(f, sl, tp, rg), D, A, F), a=m.PILIH[0], b=m.PILIH[1])
    res[(FILT.index(f), SL.index(sl), TP.index(tp), RG.index(rg))] = s


def tetangga(k):
    out = []
    for d, size in enumerate((len(FILT), len(SL), len(TP), len(RG))):
        for st in (-1, 1):
            j = list(k); j[d] += st
            if not 0 <= j[d] < size:
                continue
            if d == 0 and (k[0] == 0 or j[0] == 0 or FILT[k[0]][0] != FILT[j[0]][0]):
                continue          # tetangga filter hanya ambang sejenis
            out.append(tuple(j))
    return out


rows = []
for k, s in res.items():
    nb = [res[j]["ratio"] for j in tetangga(k)]
    skor = min(s["ratio"], np.mean(nb)) if nb else s["ratio"]
    rows.append((skor, k, s, nb))
rows.sort(key=lambda r: -r[0])
print("Juara (pilih):", m.baris("juara", res[(0, 0, 0, 0)]))
print("\nTOP 15 menurut skor (periode pilih 2015-2021)")
for skor, k, s, nb in rows[:15]:
    f, sl, tp, rg = FILT[k[0]], SL[k[1]], TP[k[2]], RG[k[3]]
    ok = s["n"] >= 100 and s["tanpa2"] > 0
    print(f"skor={skor:+.2f} {'OK ' if ok else 'x  '} filter={f} SL={sl} TP={tp} range={rg} | {m.baris('', s)} | tetangga {np.round(nb, 2)}")
json.dump([dict(skor=float(r[0]), spec=spec_of(FILT[r[1][0]], SL[r[1][1]], TP[r[1][2]], RG[r[1][3]]),
                n=r[2]["n"], ratio=r[2]["ratio"], tanpa2=r[2]["tanpa2"]) for r in rows],
          open("/tmp/data/grid_pilih.json", "w"))
