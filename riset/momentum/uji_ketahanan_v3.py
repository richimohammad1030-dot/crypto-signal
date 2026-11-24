import sys, runpy, numpy as np, pandas as pd
sp = sys.argv[1]; sys.argv = ["x", "/home/claude/crypto-signal/riset/data/m1", sp]
v = runpy.run_path("/home/claude/crypto-signal/riset/momentum/backtest_v3.py", run_name="lib")
g, hw, C, ema, ATR = v["g"], v["hour_wib"], v["C"], v["ema50"], v["ATR"]
def sig(mb=4.0, h0=7, h1=14, ext=2.0, wick="W1"):
    b = v["base"](mb, wick); b = np.where((hw >= h0) & (hw < h1), b, 0)
    e = (np.roll(C, 1) - np.roll(ema, 1)) / ATR
    b[(b == 1) & (e > ext)] = 0; b[(b == -1) & (e < -ext)] = 0
    return b
def row(nm, s, slv=3.0, rr=1.5):
    st = g["stats"](g["run"](s, 1, 0.0, 1, slv, 1, rr, 12))
    print(f"{sp:>5} {nm:28s} n={st['n']:4d} WR={st['wr']:.0f}% PF={st['pf']:.2f} tot={st['totR']:+.0f}R DD={st['ddR']:.0f}R streak={st['kalah_beruntun']} | {st['per_thn']}")
row("KANDIDAT $4 07-14 ext2 3ATR 1.5R", sig())
if sp == "0.3":
    for h1 in [12, 16]: row(f"jam 07-{h1}", sig(h1=h1))
    for ex in [1.5, 2.5, 99]: row(f"ambang pucuk {ex}", sig(ext=ex))
    for mb in [3.0, 5.0]: row(f"bodi ${mb}", sig(mb=mb))
    row("ekor lama W0", sig(wick="W0"))
    for slv, rr in [(2.0, 1.5), (3.0, 1.0), (3.0, 2.0), (4.0, 1.5)]: row(f"SL {slv}ATR TP {rr}R", sig(), slv, rr)
