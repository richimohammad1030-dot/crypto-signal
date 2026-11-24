import sys, runpy, numpy as np, pandas as pd
sys.argv = ["x", "/home/claude/crypto-signal/riset/data/m1", "0.3"]
v = runpy.run_path("/home/claude/crypto-signal/riset/momentum/backtest_v3.py", run_name="lib")
g, hw, C, ema, ATR, T5 = v["g"], v["hour_wib"], v["C"], v["ema50"], v["ATR"], v["T5"]
d26 = pd.to_datetime(T5, unit="s").year == 2026; hari26 = len(np.unique(T5[d26 & (hw >= 7)] // 86400))
e = (np.roll(C, 1) - np.roll(ema, 1)) / ATR
for mb in [3.0, 4.0]:
  for nm, m in [("Asia 07-14", (hw >= 7) & (hw < 14)), ("Asia 07-16", (hw >= 7) & (hw < 16)), ("Asia+NY", ((hw >= 7) & (hw < 14)) | (hw >= 20)), ("semua 07-24", hw >= 7)]:
    s = np.where(m, v["base"](mb, "W1"), 0); s[(s == 1) & (e > 2)] = 0; s[(s == -1) & (e < -2)] = 0
    df = g["run"](s, 1, 0, 1, 3.0, 1, 1.5, 12); st = g["stats"](df); d = df[df.t >= 1767225600]; s26 = g["stats"](d)
    print(f"bodi ${mb:g} {nm:11s} | trade/hari 2026={len(d)/hari26:.1f} PF2026={s26['pf']:.2f} WR2026={s26['wr']:.0f}% | 7 thn: PF={st['pf']:.2f} tot={st['totR']:+.0f}R DD={st['ddR']:.0f}R | {st['per_thn']}")
