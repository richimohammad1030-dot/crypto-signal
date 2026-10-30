"""Patokan cek kesehatan bot INTRADAY (Lapis 2): rentang normal dari backtest juara, ditulis ke baseline.json["intraday"].
Memakai R BERSIH (fee, slippage, funding) karena bot intraday mencatat R bersih di state["hist"][7].
Periode patokan: 2024-sekarang (periode uji, ekspektasi paling jujur; 2020-2023 dipakai untuk memilih juara).
Pemakaian: python riset/baseline_intraday.py <repo_dir> <data_dir>"""
import datetime as dt, json, os, sys
import numpy as np
REPO, DATA = sys.argv[1:3]
sys.path.insert(0, REPO); sys.path.insert(0, os.path.join(REPO, "riset"))
import backtest_intraday as bi
GRID = [5, 10, 15, 20, 30, 40, 50, 75, 100, 150, 200, 300, 500]
rng = np.random.default_rng(42)

def bands(R, sims=5000):
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

P, sent, taken = bi.run(REPO, DATA)
tr = [o for o in taken if o["t"] >= bi.IS_END]
R = np.array([o["R"] for o in tr])
c = np.cumsum(R); dd = float((np.maximum.accumulate(np.concatenate([[0], c]))[1:] - c).max())
s = st = 0
for r in R: s = s + 1 if r <= 0 else 0; st = max(st, s)
p = os.path.join(REPO, "baseline.json")
base = json.load(open(p)) if os.path.exists(p) else {}
base["intraday"] = dict(sumber=f"backtest juara intraday 2024-01 s.d. {dt.datetime.fromtimestamp(max(o['t_exit'] for o in tr), dt.timezone.utc):%Y-%m} · R bersih",
                        n=int(len(R)), wr=round(float((R > 0).mean() * 100), 3), avgR=round(float(R.mean()), 4),
                        totR=round(float(R.sum()), 3), pf=round(float(R[R > 0].sum() / -R[R <= 0].sum()), 3),
                        maxdd=round(dd, 3), streak=int(st), band=bands(R))
json.dump(base, open(p, "w"), indent=1)
print("baseline intraday:", {k: v for k, v in base["intraday"].items() if k != "band"})
