import sys, time, pickle
sys.path.insert(0,'/home/claude/cs/riset'); sys.path.insert(0,'/home/claude/cs/riset/massal')
import numpy as np, signifikansi as SG
tr,F=pickle.load(open('/tmp/xau_tr.pkl','rb'))
yr=lambda x: time.gmtime(x["t0"]).tm_year
def q_wf(strats,f,q,Y):   # ambang bergulir: hanya trade tahun < Y
    v=[F[i][f] for i,x in enumerate(tr) if x["strat"] in strats and F[i] and yr(x)<Y]
    return np.quantile(v,q) if len(v)>150 else None
def var(rules):
    th={}; out=[]
    for i,x in enumerate(tr):
        k=1.0; Y=yr(x)
        for strats,f,q,w in rules:
            if x["strat"] not in strats: continue
            if f is None: k*=w; continue
            key=(strats,f,q,Y)
            if key not in th: th[key]=q_wf(strats,f,q,Y)
            if F[i] and th[key] is not None and F[i][f]>th[key]: k*=w
        if k>0: out.append(dict(x,r=x["r"]*k))
    return out
def stat(t,lo,hi,risk=0.5):
    t=sorted([x for x in t if lo<=yr(x)<=hi],key=lambda x:x["t1"]); R=np.array([x["r"] for x in t]); eq=np.cumsum(R)
    dd=(np.maximum.accumulate(np.insert(eq,0,0))[1:]-eq).max(); ys={}
    for x in t: ys[yr(x)]=ys.get(yr(x),0)+x["r"]
    m=c=0
    for x in t: c=c+1 if x["r"]<0 else 0; m=max(m,c)
    ny=hi-lo+1 if hi<2026 else (2026-lo)+0.9; pos=R[R>0].sum(); neg=-R[R<0].sum()
    return dict(pf=pos/neg,wr=(R>0).mean(),pct=R.sum()/ny*risk,dd=dd*risk,neg=sorted(y for y,v in ys.items() if v<0),run=m,pw=len(R)/(ny*52.2),rasio=R.sum()/ny/dd)
def show(nm,t):
    a=stat(t,2005,2021); b=stat(t,2022,2026)
    f=lambda s:f"PF {s['pf']:.2f} WR {s['wr']:.0%} {s['pct']:+.1f}%/th DD {s['dd']:.1f}% rasio {s['rasio']:.2f} runtun {s['run']} {s['pw']:.1f}/mg th- {s['neg']}"
    print(f"{nm:<34} IS {f(a)}\n{'':<34} OOS {f(b)}")
J=tr
H={"H1 tanpa SUS":[(("SUS",),None,0,0.0)],
   "H1b SUS 0,5x":[(("SUS",),None,0,0.5)],
   "H2 MR/KOMBO 0,5x er20>q60":[(("MR","KOMBO"),"er20",0.6,0.5)],
   "H2b MR/KOMBO 0x er20>q80":[(("MR","KOMBO"),"er20",0.8,0.0)],
   "H3 K6 0,5x er20>q80":[(("K6",),"er20",0.8,0.5)],
   "H1+H2":[(("SUS",),None,0,0.0),(("MR","KOMBO"),"er20",0.6,0.5)],
   "H1+H2+H3":[(("SUS",),None,0,0.0),(("MR","KOMBO"),"er20",0.6,0.5),(("K6",),"er20",0.8,0.5)],
   "H1b+H2":[(("SUS",),None,0,0.5),(("MR","KOMBO"),"er20",0.6,0.5)]}
show("JUARA",J); V={}
for nm,r in H.items():
    V[nm]=var(r); show(nm,V[nm])
    for lbl,m in (("2005+",1104537600),("OOS 2022+",1640995200)):
        s=SG.banding([(int(x["t1"]),x["r"]) for x in J],[(int(x["t1"]),x["r"]) for x in V[nm]],mulai=m)
        print(f"{'':<34} P_rasio {lbl} {s['P_rasio_lebih_baik']:.2f} P_R {s['P_R_lebih_baik']:.2f}")
pickle.dump(V,open('/tmp/xau_V.pkl','wb'))
