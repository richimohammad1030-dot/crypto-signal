"""Uji 'logika swing/tren harian dalam jendela 07:00-23:00' (31 Okt 2026). SELEKSI HANYA DI 2015-2021.
Skor = min(rasio, rata-rata rasio tetangga SL/TP/n). Syarat >= 300 trade di periode pilih & positif tanpa 2% terbaik.
Top 6 diuji di 2022 - Jan 2025 dan dikonfirmasi di Setra (data sambung), plus signifikansi vs juara (urutan M1).
Pemakaian: python harian_scan.py <xau_sambung.json> [ambigu_sisi.json]"""
import sys, os, json, itertools
import numpy as np
import audit_mesin as m
import harian_mesin as hm
sys.path.insert(0, os.path.join(m.REPO, "riset")); import signifikansi as sg

D = m.muat(sys.argv[1]); A = np.array(m.atr(list(D[2]), list(D[3]), list(D[4]), 14))
idx, dh, dl, dc, datr = hm.harian(D)
ARAH = {("donchian", n): hm.arah_harian(dh, dl, dc, "donchian", n) for n in (10, 20, 55)}
ARAH.update({("ema", n): hm.arah_harian(dh, dl, dc, "ema", n) for n in (20, 50, 100, 200)})
ARAH.update({("mom", n): hm.arah_harian(dh, dl, dc, "mom", n) for n in (20, 60, 120)})
ARAH[("selalu", "long")] = np.ones(len(idx))
MASUK = [("market", 0), ("limit", 0.25), ("limit", 0.5), ("limit", 1.0), ("stop", 0)]
SL = [1.0, 1.5, 2.0, 3.0]
TP = [None, 1, 2, 4]

res = {}
for (ak, mk, sl, tp) in itertools.product(ARAH, MASUK, SL, TP):
    tr = hm.simulasi(D, A, ARAH[ak], idx, masuk=mk[0], k=mk[1], sl=sl, rr=tp)
    res[(ak, mk, sl, tp)] = (m.stat(tr, a=m.PILIH[0], b=m.PILIH[1]), tr)


def tetangga(key):
    ak, mk, sl, tp = key; out = []
    for s2 in (SL[i] for i in (SL.index(sl) - 1, SL.index(sl) + 1) if 0 <= i < len(SL)): out.append((ak, mk, s2, tp))
    for t2 in (TP[i] for i in (TP.index(tp) - 1, TP.index(tp) + 1) if 0 <= i < len(TP)): out.append((ak, mk, sl, t2))
    ns = sorted(n for (j, n) in ARAH if j == ak[0])
    if ak[0] in ("donchian", "ema", "mom"):
        p = ns.index(ak[1])
        for q in (p - 1, p + 1):
            if 0 <= q < len(ns): out.append(((ak[0], ns[q]), mk, sl, tp))
    return out


rows = []
for key, (s, _) in res.items():
    nb = [res[k][0]["ratio"] for k in tetangga(key)]
    rows.append((min(s["ratio"], np.mean(nb)) if nb else s["ratio"], key, s))
rows.sort(key=lambda r: -r[0])
ok = [r for r in rows if r[2]["n"] >= 300 and r[2]["tanpa2"] > 0]
print(f"{len(res)} varian. Lolos syarat dasar di periode pilih: {len(ok)}")
print("Pembanding 'selalu long' terbaik (pilih):", max((r for r in rows if r[1][0][0] == "selalu"), key=lambda r: r[0])[1:])
print("\nTOP 12 (periode pilih 2015-2021):")
for sk, key, s in ok[:12]:
    print(f"skor {sk:+.2f} {key} | {m.baris('', s)}")

# kandidat: top 6 dengan arah berbeda-beda (hindari 6 varian yang sama)
cand, seen = [], set()
for sk, key, s in ok:
    if (key[0], key[1][0]) in seen: continue
    seen.add((key[0], key[1][0])); cand.append(key)
    if len(cand) == 6: break

AMB = {int(k): v for k, v in json.load(open(sys.argv[2])).items()} if len(sys.argv) > 2 else "buy"
J = m.potong(m.replay(D, A=A, ambigu=AMB)); jl = [(int(x["t1"]), float(v)) for x, v in zip(J, m.net(J))]
print("\n=== Kandidat di periode UJI (2022-Jan 2025) dan KONF (Setra), juara dengan urutan M1")
for nm, (a, b) in (("UJI", m.UJI), ("KONF", m.KONF)):
    print(m.baris(f"juara {nm}", m.stat(J, a=a, b=b)))
for key in cand:
    tr = res[key][1]; pl = [(int(x["t1"]), float(v)) for x, v in zip(tr, m.net(tr))]
    print(f"\n{key}")
    for nm, (a, b) in (("pilih", m.PILIH), ("UJI", m.UJI), ("KONF", m.KONF)):
        s = m.stat(tr, a=a, b=b); x = m.stat(tr, a=a, b=b, slip=0.2)
        r = sg.banding(jl, pl, int(m.ts(a)) if a else None, int(m.ts(b)) if b else None)
        print(f"  {m.baris(nm, s)} | slip0,2 {x['rthn']:+.1f}R/thn | P_rasio {r['P_rasio_lebih_baik']:.3f}")
    print("  per tahun:", " · ".join(f"{y} {v:+.0f}" for y, v in m.stat(tr)["thn"].items()))
json.dump([[str(k) for k in cand]], open("/tmp/data/harian_kandidat.json", "w"))
