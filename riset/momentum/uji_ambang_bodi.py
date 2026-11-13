import sys, runpy
sys.argv = ["x", sys.argv[1] if len(sys.argv) > 1 else "riset/data/m1"]
g = runpy.run_path("/home/claude/crypto-signal/riset/momentum/backtest_momentum.py", run_name="lib")
import pandas as pd
rows = []
for mb in [5.0, 6.5, 8.0, 10.0, 13.0]:
    sig = g["signals"](mb, False, False)
    for en in [0.236, 0.382]:
        st = g["stats"](g["run"](sig, en, 0.0, -1.0, 12))
        rows.append(dict(bodi=mb, entry=en, **st))
pd.set_option("display.width", 250)
print(pd.DataFrame(rows).round(2)[["bodi","entry","n","per_mgg","wr","pf","totR","ddR","kalah_beruntun","thn_plus","per_thn"]].to_string(index=False))
