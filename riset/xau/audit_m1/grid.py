from m1sim import *
import datetime as dt, collections
def yr(t): return dt.datetime.fromtimestamp(int(t)+3600, dt.timezone.utc).year
cfgs = [
 ("A repo: bid-only + flat $0,40",            dict(S=0.0, flat=0.40)),
 ("B spread $0,20 + gap",                      dict(S=0.20, gap=True, flat=0.0)),
 ("C spread $0,30 + gap",                      dict(S=0.30, gap=True, flat=0.0)),
 ("D spread $0,30 + slip SL $0,20 + telat 5m", dict(S=0.30, gap=True, slip_sl=0.20, delay=5, flat=0.0)),
 ("E spread $0,50 + slip SL $0,30 + telat 10m",dict(S=0.50, gap=True, slip_sl=0.30, delay=10, flat=0.0)),
]
tabs = {}
for nm, kw in cfgs:
    res, sk = run(**kw)
    by = collections.defaultdict(float); st = collections.defaultdict(float)
    for x in res: by[yr(x["t0"])] += x["net"]; st[x["strat"]] += x["net"]
    tot = sum(by.values()); yrs = 6.83   # 1 Jan 2020 - 6 Nov 2026 tanpa 2 bulan data kosong (~6,67)
    r = np.array([x["net"] for x in sorted(res, key=lambda z: z["t1"])]); eq = np.cumsum(r); dd = float(np.max(np.maximum.accumulate(np.r_[0, eq])[1:] - eq))
    win = (r > 0).mean(); pf = r[r > 0].sum() / -r[r < 0].sum()
    print(f"{nm:<45} n={len(r)} total={tot:+7.1f}R  ~{tot/6.67:+5.1f}R/thn  win={win*100:.0f}% PF={pf:.2f} DD={dd:.0f}R | " + " ".join(f"{y}:{by[y]:+.0f}" for y in sorted(by)))
    print("   per strat:", {k: round(v,1) for k,v in st.items()})
