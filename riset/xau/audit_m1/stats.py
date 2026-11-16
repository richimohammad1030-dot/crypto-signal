import numpy as np, datetime as dt, collections
from base import *
D = build_D(); T,O,H,L,C = D
A = np.array(m.atr(list(H), list(L), list(C), 14)); F = m.fitur(D, A)
base = [x for x in mm.baseline(D, A, F) if x.get("w",1)>0]
def wib(t): return dt.datetime.fromtimestamp(int(t)+7*3600, dt.timezone.utc)
per = {"2005-14":(2005,2014),"2015-21":(2015,2021),"2022-26":(2022,2026),"2005-26":(2005,2026)}
def sel(a,b): return [x for x in base if a<=wib(x["t0"]).year<=b]
def netR(trs,cost): return np.array([(x["R"]-cost/x["r0"]) for x in trs])
print("=== Sensitivitas biaya flat (USD/trade) -> R/tahun, tahun minus ===")
for nm,(a,b) in per.items():
    trs=sel(a,b); yrs=b-a+1
    row=[]
    for c in (0.0,0.2,0.4,0.8,1.2):
        r=netR(trs,c); byy=collections.defaultdict(float)
        for x,v in zip(trs,r): byy[wib(x["t0"]).year]+=v
        row.append(f"c={c}: {r.sum()/yrs:+.1f}R/thn ({sum(v<0 for v in byy.values())}/{len(byy)} minus)")
    print(nm, " | ".join(row))
print("\n=== Per komponen, R bersih/trade @0,40 ===")
for nm,(a,b) in per.items():
    trs=sel(a,b); s=[]
    for st in ("KOMBO","MR","K6","SUS"):
        xs=[x for x in trs if x["strat"]==st]
        if xs: r=netR(xs,0.40); s.append(f"{st} n={len(xs)} {r.mean():+.3f} (t={r.mean()/(r.std(ddof=1)/np.sqrt(len(r))):+.1f})")
    print(nm," | ".join(s))
print("\n=== Bootstrap blok bulanan (5000x): R/tahun @0,40 ===")
rng=np.random.default_rng(1)
for nm,(a,b) in per.items():
    trs=sel(a,b); r=netR(trs,0.40); yrs=b-a+1
    mon=collections.defaultdict(float)
    for x,v in zip(trs,r): w=wib(x["t0"]); mon[(w.year,w.month)]+=v
    arr=np.array(list(mon.values())); n=len(arr)
    bs=np.array([arr[rng.integers(0,n,n)].sum()/yrs for _ in range(5000)])
    print(f"{nm}: {arr.sum()/yrs:+.1f}R/thn  CI95 [{np.percentile(bs,2.5):+.1f}, {np.percentile(bs,97.5):+.1f}]  P(>0)={np.mean(bs>0):.3f}  bulan+={np.mean(arr>0)*100:.0f}%")
print("\n=== Jumlah tahun minus & drawdown @0,5% risiko ===")
for nm,(a,b) in per.items():
    trs=sorted(sel(a,b),key=lambda x:x["t1"]); r=netR(trs,0.40)
    e=np.cumprod(1+0.005*r); pk=np.maximum.accumulate(np.r_[1,e])[1:]; print(nm,f"DD maks {np.max(1-e/pk)*100:.1f}% CAGR {(e[-1]**(1/(b-a+1))-1)*100:+.1f}%")
