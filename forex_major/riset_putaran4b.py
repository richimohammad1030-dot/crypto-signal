"""Putaran 4b: hari Senin breakout level minggu lalu cenderung palsu (N3 skip Senin lebih baik). Uji Senin = FADE level minggu lalu
(limit order lawan arah di level + off*ATR), digabung N3 tanpa Senin, di 7 pair."""
import itertools, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import backtest as B
from backtest import order, atr, prev_daily
from riset_putaran2 import pf
from riset_putaran3 import score, fmt
from riset_putaran4 import ALL, run as run_n3

def monfade(P, off=0.2, slm=0.4, tpm=0.6):
    idx, D = prev_daily(P); A = atr(D); out = {}; wk = (D["t"] // 86400 + 3) // 7
    for d, j in idx.items():
        if j < 110 or (d + 3) % 7 != 0: continue
        m = wk == ((d + 3) // 7 - 1)
        if not m.any(): continue
        ph, pl = D["h"][m].max(), D["l"][m].min(); a = A[j]; t0 = d * 86400
        s_ = ph + off * a; b_ = pl - off * a
        out[d] = [order(P.name, "MF", -1, "limit", s_, s_ + slm * a, s_ - tpm * a, t0, oco=("MF", d)),
                  order(P.name, "MF", 1, "limit", b_, b_ - slm * a, b_ + tpm * a, t0, oco=("MF", d))]
    return out

def run_mf(kw, data):
    tr = []
    for P in data:
        for d, l in monfade(P, **kw).items(): tr += B.simulate_pair(P, l, d)
    return tr

duka = [B.load(p) for p in ALL]
os.environ["FX_DATA"] = "data_setra/{pair}_1h.json.gz"; setra = [B.load(p) for p in ALL]
base = dict(dist=9.0, vol="none", dow="mon", slm=0.4, tpm=1.2, be=0.5)
t3, nd = run_n3(base, duka); s3, _ = run_n3(base, setra)
print("N3 tanpa Senin:", fmt(score(t3, nd, s3)))
for off, slm, tpm in itertools.product([0.0, 0.1, 0.2, 0.3], [0.3, 0.5], [0.4, 0.6, 1.0]):
    kw = dict(off=off, slm=slm, tpm=tpm); a = run_mf(kw, duka); b = run_mf(kw, setra)
    sa = score(a, nd, b); c = score(t3 + a, nd, s3 + b)
    ok = c["per_week"] >= 4 and min(c["pf_is"], c["pf_oos"]) > 1.05 and c["pf_setra"] > 1.0
    print(("LOLOS " if ok else "gagal ") + f"{kw} | Senin fade sendiri IS {sa['pf_is']:.2f} OOS {sa['pf_oos']:.2f} Setra {sa['pf_setra']:.2f} {sa['per_week']:.1f}/mgg | gabung: " + fmt(c), flush=True)
