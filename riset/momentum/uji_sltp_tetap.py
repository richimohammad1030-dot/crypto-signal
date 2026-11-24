import sys, runpy, itertools, numpy as np, pandas as pd
sys.argv = ["x", "/home/claude/crypto-signal/riset/data/m1", "0.3"]
v = runpy.run_path("/home/claude/crypto-signal/riset/momentum/backtest_v3.py", run_name="lib")
g, hw, C, ema, ATR, T5 = v["g"], v["hour_wib"], v["C"], v["ema50"], v["ATR"], v["T5"]
d26 = pd.to_datetime(T5, unit="s").year == 2026; hari26 = len(np.unique((T5[d26 & (hw >= 7)] // 86400)))
def per_hari26(df): return (df.t >= 1767225600).sum() / hari26
# frekuensi kandidat di 2026
b = v["base"](4.0, "W1"); s = np.where((hw >= 7) & (hw < 14), b, 0)
e = (np.roll(C, 1) - np.roll(ema, 1)) / ATR; s[(s == 1) & (e > 2)] = 0; s[(s == -1) & (e < -2)] = 0
print("kandidat: candle momentum mentah 2026/hari =", round((s[d26] != 0).sum() / hari26, 2), "| trade 2026/hari =", round(per_hari26(g["run"](s, 1, 0, 1, 3.0, 1, 1.5, 12)), 2))
rows = []
for mb, wk, ss in itertools.product([2.0, 3.0, 4.0], ["W0", "W1"], ["semua", "asia+ny", "asia"]):
    bb = v["base"](mb, wk)
    m = {"semua": hw >= 7, "asia+ny": ((hw >= 7) & (hw < 14)) | (hw >= 20), "asia": (hw >= 7) & (hw < 14)}[ss]
    sg = np.where(m, bb, 0)
    for usd in [1.0, 2.0, 3.0, 5.0, 10.0]:
        df = g["run"](sg, 1, 0.0, 2, usd, 2, usd, 12)
        st = g["stats"](df)
        if st: rows.append(dict(bodi=mb, ekor=wk, sesi=ss, sl_tp=f"${usd:g} (={usd*100:.0f} pip)", trade_hari_2026=per_hari26(df), **st))
r = pd.DataFrame(rows).sort_values("pf", ascending=False); r.to_csv("hasil_11.csv", index=False)
pd.set_option("display.width", 250)
c = ["bodi","ekor","sesi","sl_tp","trade_hari_2026","per_hari","wr","pf","totR","ddR","kalah_beruntun","per_thn"]
print("kombinasi", len(r), "PF>1:", (r.pf > 1).sum())
print(r.head(12)[c].round(2).to_string(index=False))
print(r.groupby("sl_tp").pf.median().round(3).to_string())
print(r[r.trade_hari_2026 >= 3].head(6)[c].round(2).to_string(index=False))
