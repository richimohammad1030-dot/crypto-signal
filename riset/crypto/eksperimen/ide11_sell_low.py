"""Ide #11 · Sinyal SELL LOW conviction dilewati (BUY LOW tetap), replay penuh.
Label dihitung saat order dibuat dengan sb.conviction (sama dengan bot).
Varian tambahan: SELL LOW risiko setengah (slot tidak berubah, jadi cukup skala R dari replay juara)."""
import pandas as pd
from _common import setup
rp, champ, data_dir = setup()
sb = rp.sb
skip = rp.replay(lambda c, i, D, d, en, sl, t: d == 1 or sb.conviction(rp.DATA, c, t, d, en, sl) != "LOW")[0]

# label per trade juara dari CSV backtest_crypto.py (fitur saat order dibuat)
bt = pd.read_csv(f"{data_dir}/trades_crypto.csv")
import numpy as np
pts = lambda x, ab: np.where(x < ab[0], 1, np.where(x > ab[1], -1, 0))
bt["score"] = pts(bt.slpct, sb.CONV_SL) + pts(bt.ext, sb.CONV_EXT) + pts(bt["rank"], sb.CONV_RANK) + bt.btc
bt["label"] = np.where(bt.score >= 2, "HIGH", np.where(bt.score <= -1, "LOW", "MEDIUM"))
m = champ.merge(bt[["coin", "t0", "label"]], on=["coin", "t0"], how="left")
print("trade juara tanpa label:", int(m.label.isna().sum()))
half = m.copy()
mask = (half.d == -1) & (half.label == "LOW")
half.loc[mask, "R"] = half.loc[mask, "R"] * 0.5
print(rp.HEADER)
print(rp.fmt_compare("Juara", rp.compare(champ, champ)))
for k, v in {"SELL LOW dilewati (replay)": skip, "SELL LOW risiko 1/2": half}.items():
    print(rp.fmt_compare(k, rp.compare(champ, v)))
for k, v in {"SELL LOW dilewati (replay)": skip, "SELL LOW risiko 1/2": half}.items():
    c = rp.compare(champ, v)
    print(k, "rasio per tahun:", {y: (round(a["rasio"], 1), round(b["rasio"], 1)) for y, (a, b) in c["yr"].items()})
g = m.assign(per=np.where(m.year >= 2024, "2024-skrg", "2020-2023")).groupby(["per", "d", "label"]).R.agg(["count", "mean", "sum"]).round(3)
print(g)
