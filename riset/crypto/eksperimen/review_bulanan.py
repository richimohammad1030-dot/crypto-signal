"""Review bulanan crypto (PROSEDUR langkah 4): statistik juara, live vs backtest, label, data ML.
Argumen: <repo> <data_dir>. Menulis <data_dir>/trades_scored.pkl untuk riset/ml_walkforward.py."""
import datetime as dt, json, os, sys
import numpy as np, pandas as pd
from _common import setup
rp, champ, data_dir = setup()
sb = rp.sb
repo = sys.argv[1]
sys.path.insert(0, repo)
import kesehatan
WIB = dt.timezone(dt.timedelta(hours=7))
LS = kesehatan.LIVE_START["crypto"]

bt = pd.read_csv(f"{data_dir}/trades_crypto.csv").sort_values("t1").reset_index(drop=True)
bt["year"] = pd.to_datetime(bt.t0, unit="s").dt.year
pts = lambda x, ab: np.where(x < ab[0], 1, np.where(x > ab[1], -1, 0))
bt["score"] = pts(bt.slpct, sb.CONV_SL) + pts(bt.ext, sb.CONV_EXT) + pts(bt["rank"], sb.CONV_RANK) + bt.btc
bt["label"] = np.where(bt.score >= 2, "HIGH", np.where(bt.score <= -1, "LOW", "MEDIUM"))
bt.to_pickle(f"{data_dir}/trades_scored.pkl")

def row(g):
    s = rp.stats(g)
    return pd.Series(dict(n=s["n"], totR=round(s["tot"], 1), avgR=round(s["avg"], 3), wr=round(s["wr"], 1), dd=round(s["dd"], 1),
                          rasio=round(s["rasio"], 1)))
print("== Per tahun"); print(bt.groupby("year").apply(row, include_groups=False).to_string())
print("== Per label"); print(bt.groupby("label").apply(row, include_groups=False).to_string())
print("== Label per tahun (avgR)"); print(bt.pivot_table(index="year", columns="label", values="R", aggfunc="mean").round(3).to_string())
print("== Label per tahun (n)"); print(bt.pivot_table(index="year", columns="label", values="R", aggfunc="count").to_string())
bt["arah"] = np.where(bt.d == 1, "BUY", "SELL")
bt["per"] = np.where(bt.year >= 2024, "2024-skrg", "2020-2023")
print("== Arah x periode"); print(bt.groupby(["per", "arah"]).apply(row, include_groups=False).to_string())
print("== Arah x label x periode (avgR)"); print(bt.pivot_table(index=["per", "arah"], columns="label", values="R", aggfunc="mean").round(3).to_string())
rec = bt[bt.year >= 2025].groupby("label").R.mean()
allm = bt.groupby("label").R.mean()
print("HIGH>MED>LOW semua:", allm.HIGH > allm.MEDIUM > allm.LOW, "· 2025-2026:", rec.round(3).to_dict(), rec.HIGH > rec.MEDIUM > rec.LOW)
y26 = bt[bt.year == 2026].groupby("label").R.mean()
print("2026 saja:", y26.round(3).to_dict())

# ---- risiko 1/2 untuk SEMUA LOW (tinjau ulang ide #2 di mesin v2; slot tidak berubah)
m = champ.merge(bt[["coin", "t0", "label"]], on=["coin", "t0"], how="left")
half = m.copy(); half.loc[half.label == "LOW", "R"] *= 0.5
print("== Tinjau ulang #2 (LOW risiko 1/2, mesin v2)"); print(rp.HEADER); print(rp.fmt_compare("LOW risiko 1/2", rp.compare(champ, half)))
c = rp.compare(champ, half); print({y: (round(a["rasio"], 1), round(b["rasio"], 1)) for y, (a, b) in c["yr"].items()})

# ---- live vs backtest
st = json.load(open(os.path.join(repo, "state.json")))
live = pd.DataFrame(st.get("hist", []), columns=["coin", "d", "t0", "t1", "e", "ex", "R"])
lv = live[live.t1 >= LS].sort_values("t1")
bts = champ[champ.t1 >= LS].sort_values("t1")
print("== Live sejak", dt.datetime.fromtimestamp(LS, WIB))
f = lambda t: dt.datetime.fromtimestamp(t, WIB).strftime("%d %b %H:%M")
print("LIVE:"); [print(" ", r.coin, int(r.d), f(r.t0), "->", f(r.t1), r.e, r.ex, r.R) for r in lv.itertuples()]
print("BACKTEST:"); [print(" ", r.coin, int(r.d), f(r.t0), "->", f(r.t1), round(r.e, 6), round(r.ex, 6), r.R) for r in bts.itertuples()]
print("live total", round(lv.R.sum(), 3), len(lv), "· backtest total", round(bts.R.sum(), 3), len(bts))

# posisi/order terbuka: replay ulang untuk state akhir
cls = rp.make_engine_cls(); S = {"coins": {}, "last_ts": 0, "replay": True}
e = cls(S, rp.funding_fn, lambda *a, **k: None); e.run(rp.DATA, 0)
print("last candle backtest:", f(S["last_ts"]), "· live last_ts:", f(st.get("last_ts", 0)))
ob = {c: (v.get("pos"), v.get("pend")) for c, v in S["coins"].items() if v.get("pos") or v.get("pend")}
ol = {c: (v.get("pos"), v.get("pend")) for c, v in st["coins"].items() if v.get("pos") or v.get("pend")}
for c in sorted(set(ob) | set(ol), key=lambda c: sb.COINS.index(c)):
    def s(x):
        p, q = x
        return (f"POS {p[0]:+d} e={p[1]:.6g} sl={p[2]:.6g} t0={f(p[3])}" if p else "") + (f"PEND {q[0]:+d} e={q[1]:.6g} sl={q[2]:.6g}" if q else "")
    print(f"  {c:7s} BT: {s(ob[c]) if c in ob else '-':60s} LIVE: {s(ol[c]) if c in ol else '-'}")
