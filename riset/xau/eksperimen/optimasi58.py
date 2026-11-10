"""Optimasi #58 (10 Nov 2026): sistem V2 = kombinasi (2-4 komponen sepakat, market, SL/TP) -> MR live -> K6 + susulan.
Semua kombinasi × SL 1,5/2/2,5/3 × TP 1/1,5/2/3/tanpa dinilai SEBAGAI SISTEM; dipilih HANYA di 2015-2021 (R/thn sistem).
Konfirmasi 2005-14, 2022-Jan25, Setra + tahun minus 2005-2026 + P vs bot live. Pemakaian: python optimasi58.py <xau_2004.json> <ambigu.json>"""
import sys, os, itertools
import numpy as np
sys.argv = sys.argv[:3]
exec(open("kombinasi.py").read().split("def per_idx")[0])
sys.path.insert(0, os.path.join(m.REPO, "riset")); import signifikansi as sg
GRID = list(itertools.product((1.5, 2.0, 2.5, 3.0), (1, 1.5, 2, 3, None)))
days = harian
LIVE = mm.baseline(D, A, F, ambigu=AMB)
for x, v in zip(LIVE, m.net(LIVE)): x["Rn"] = float(v)
lain = {}                                  # hasil hari non-kombinasi = persis bot live (MR / K6 / SUS) per ip
for x in LIVE: lain.setdefault(x["ip"], []).append(x)
V = np.array([[KOMP[k](i) for k in NAMA] for i in days], dtype=int)
Rc = np.full((len(days), 2, len(GRID)), np.nan); T1 = np.zeros((len(days), 2, len(GRID)))
for a, i in enumerate(days):
    j = i + 1; e = O[j]
    for b_, d in enumerate((1, -1)):
        for g, (sl, tp) in enumerate(GRID):
            dist = sl * A[i]
            if dist <= 0.5: continue
            ex, t1, why = sm._kelola(D, j, d, e, e - d * dist, e + d * tp * dist if tp else None)
            Rc[a, b_, g] = ((ex - e) * d - 0.40) / dist; T1[a, b_, g] = t1
tahun = np.array([m.wib(T[i]).year for i in days])
Rl = np.array([sum(x["Rn"] for x in lain.get(i, [])) for i in days])
PER = {"05-14": (2005, 2014), "15-21": (2015, 2021), "uji": None, "Setra": None, "05-26": (2005, 2026)}
tU0, tU1, tK0 = m.ts(m.UJI[0]), m.ts(m.UJI[1]), m.ts(m.KONF[0])
ti = np.array([T[i] for i in days])
mask = {"05-14": (tahun >= 2005) & (tahun <= 2014), "15-21": (tahun >= 2015) & (tahun <= 2021), "uji": (ti >= tU0) & (ti < tU1),
        "Setra": ti >= tK0, "05-26": tahun >= 2005}
yrs = {"05-14": 10.0, "15-21": 7.0, "uji": 3.08, "Setra": (T[-1] - tK0) / 86400 / 365.25, "05-26": (T[-1] - m.ts("2005-01-01")) / 86400 / 365.25}
def nilai(r):
    out = {k: r[mk].sum() / yrs[k] for k, mk in mask.items()}
    th = np.array([r[tahun == y].sum() for y in range(2005, 2027)])
    c = np.cumsum(r[tahun >= 2005]); dd = (np.maximum.accumulate(np.concatenate([[0], c]))[1:] - c).max()
    return out, th, dd
base, thb, ddb = nilai(Rl)
hasil = []
for k in (2, 3, 4):
    for kom in itertools.combinations(range(len(NAMA)), k):
        v = V[:, kom]; s = v[:, 0]; ok = (s != 0) & np.all(v == s[:, None], axis=1)
        if ok.sum() < 100: continue
        ar = (s == -1).astype(int)
        for g in range(len(GRID)):
            rc = Rc[np.arange(len(days)), ar, g]
            r = np.where(ok & ~np.isnan(rc), rc, Rl)
            o, th, dd = nilai(r)
            hasil.append((kom, g, o, th, dd, ok.sum()))
print(f"sistem dinilai: {len(hasil)}")
hasil.sort(key=lambda z: -z[2]["15-21"])
def baris(nm, o, th, dd):
    return (f"{nm:<30} " + " · ".join(f"{o[k]:+5.1f}" for k in PER) + f" | DD {dd:.0f}R minus {int((th < 0).sum())}/22 terburuk {th.min():+.0f}")
print("R/thn: 2005-14 · 2015-21(PILIH) · 2022-Jan25 · Setra · 2005-26")
print(baris("BOT LIVE", base, thb, ddb))
top = hasil[:300]
lol = lambda z: all(z[2][k] > base[k] for k in ("05-14", "uji", "Setra"))
print(f"porsi yang mengalahkan live di 2005-14 & uji & Setra: 30 teratas {np.mean([lol(z) for z in hasil[:30]])*100:.0f}% · 300 teratas {np.mean([lol(z) for z in top])*100:.0f}% · semua {np.mean([lol(z) for z in hasil])*100:.0f}%")
for z in hasil[:12]:
    print(baris("+".join(NAMA[c] for c in z[0]) + f" SL{GRID[z[1]][0]} TP{GRID[z[1]][1] or '-'}", z[2], z[3], z[4]) + ("  MENANG" if lol(z) else ""))
best = hasil[0]
print("\nTERPILIH (R/thn 2015-21 tertinggi):", "+".join(NAMA[c] for c in best[0]), GRID[best[1]])
print("per tahun: " + " ".join(f"{str(y)[2:]}:{v:+.0f}" for y, v in zip(range(2005, 2027), best[3])))
import pickle; pickle.dump(dict(kom=[NAMA[c] for c in best[0]], grid=GRID[best[1]]), open("/tmp/data/opt58.pkl", "wb"))
