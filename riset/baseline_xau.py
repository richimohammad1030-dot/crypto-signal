"""Patokan cek kesehatan bot XAU (Lapis 2) untuk versi MULTI-STRATEGI (MR RSI2 + K6), ditulis ke baseline.json["xau"].
R KOTOR (bot mencatat R kotor). Periode 2022 - sekarang (Dukascopy s.d. Jan 2025 + Setra sesudahnya), urutan candle ambigu dari
M1 Dukascopy (riset/xau/eksperimen/ambigu_m1_2022_2026.json) agar ekspektasi tidak optimis. analisis.py tidak menimpa patokan ini.
Pemakaian: python riset/baseline_xau.py <repo> <xau_setra.json> <xau_dukascopy.json>"""
import datetime as dt, json, os, sys
import numpy as np
REPO, SETRA, DUKA = sys.argv[1:4]
sys.path.insert(0, os.path.join(REPO, "riset")); sys.path.insert(0, os.path.join(REPO, "riset", "xau", "eksperimen"))
import audit_mesin as m
GRID = [5, 10, 15, 20, 30, 40, 50, 75, 100, 150, 200, 300, 500]
rng = np.random.default_rng(42)


def bands(R, sims=5000):
    """Rentang normal per jumlah trade (salinan riset/baseline_intraday.bands)."""
    R = np.asarray(R, float); out = {}
    for n in GRID:
        x = rng.choice(R, size=(sims, n), replace=True); c = np.cumsum(x, axis=1)
        peak = np.maximum.accumulate(np.concatenate([np.zeros((sims, 1)), c], axis=1), axis=1)[:, 1:]
        loss = (x <= 0).astype(int); streak = np.zeros(sims, int); cur = np.zeros(sims, int)
        for j in range(n): cur = (cur + 1) * loss[:, j]; streak = np.maximum(streak, cur)
        p = lambda a, q: [round(float(v), 3) for v in np.percentile(a, q)]
        out[str(n)] = dict(cum=p(c[:, -1], [1, 5, 50, 95, 99]), wr=p((x > 0).mean(axis=1) * 100, [5, 95]),
                           dd=p((peak - c).max(axis=1), [95, 99]), streak=p(streak, [95, 99]))
    return out

D = m.sambung(m.muat(DUKA), m.muat(SETRA))
A = np.array(m.atr(list(D[2]), list(D[3]), list(D[4]), 14)); F = m.fitur(D, A)
AMB = {int(k): v for k, v in json.load(open(os.path.join(REPO, "riset", "xau", "eksperimen", "ambigu_m1_2022_2026.json"))).items()}
import multi_mesin as mm
tr = m.potong(mm.baseline(D, A, F, ambigu=AMB), "2022-01-01")
R = np.array([x["R"] for x in tr])
c = np.cumsum(R); dd = float((np.maximum.accumulate(np.concatenate([[0], c]))[1:] - c).max())
s = st = 0
for r in R: s = s + 1 if r <= 0 else 0; st = max(st, s)
win, los = R[R > 0], R[R <= 0]
base = json.load(open(os.path.join(REPO, "baseline.json")))
base["xau"] = dict(sumber=f"riset multi-strategi (MR+K6) {m.wib(tr[0]['t0']):%Y-%m} s.d. {m.wib(tr[-1]['t1']):%Y-%m} (Dukascopy+Setra, urutan M1)",
                   pembuat="riset/baseline_xau.py", n=len(R), wr=round(float((R > 0).mean() * 100), 3), avgR=round(float(R.mean()), 3),
                   totR=round(float(R.sum()), 3), pf=round(float(win.sum() / -los.sum()), 3), maxdd=round(dd, 3), streak=int(st), band=bands(R))
json.dump(base, open(os.path.join(REPO, "baseline.json"), "w"), indent=1)
print({k: v for k, v in base["xau"].items() if k != "band"})
