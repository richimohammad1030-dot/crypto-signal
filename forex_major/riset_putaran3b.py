"""Putaran 3b: N3 dua arah (lolos, 2,9/mgg) + level lain dua arah (Donchian k-hari, OCO) untuk mengejar >= 4 trade/minggu di 4 pair."""
import itertools, os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import backtest as B
from backtest import order, atr, prev_daily
from riset_putaran3 import n3x, trades_of, score, fmt

def n5x(P, k=5, slm=0.4, tpm=0.8):
    """Donchian k-hari dua arah (OCO)."""
    idx, D = prev_daily(P); A = atr(D); out = {}
    for d, j in idx.items():
        if j < max(k + 1, 20): continue
        hi, lo = D["h"][j - k + 1:j + 1].max(), D["l"][j - k + 1:j + 1].min(); a = A[j]; t0 = d * 86400
        out[d] = [order(P.name, "N5", 1, "stop", hi, hi - slm * a, hi + tpm * a, t0, oco=("N5", d)),
                  order(P.name, "N5", -1, "stop", lo, lo + slm * a, lo - tpm * a, t0, oco=("N5", d))]
    return out

duka = [B.load(p) for p in B.PAIRS]
os.environ["FX_DATA"] = "data_setra/{pair}_1h.json.gz"; setra = [B.load(p) for p in B.PAIRS]
base = dict(ema_n=50, slm=0.4, tpm=0.8, trend=False)
t3, nd = trades_of(n3x, base, duka); s3, _ = trades_of(n3x, base, setra)
print("N3 dua arah sendiri:", fmt(score(t3, nd, s3)))
for k, slm, tpm in itertools.product([2, 3, 5, 10], [0.3, 0.4, 0.6], [0.6, 0.8, 1.2]):
    kw = dict(k=k, slm=slm, tpm=tpm); t5, _ = trades_of(n5x, kw, duka); s5, _ = trades_of(n5x, kw, setra)
    a = score(t5, nd, s5); c = score(t3 + t5, nd, s3 + s5)
    ok = c["per_week"] >= 4 and min(c["pf_is"], c["pf_oos"]) > 1.05 and c["pf_setra"] > 1.0
    print(("LOLOS " if ok else "gagal ") + f"N5 {kw}: sendiri PF IS {a['pf_is']:.2f}/OOS {a['pf_oos']:.2f} | gabung N3: " + fmt(c), flush=True)
