import sys, pickle, time
sys.path.insert(0,'/home/claude/cs/riset/fx/eksperimen'); sys.path.insert(0,'/home/claude/cs/riset'); sys.path.insert(0,'/home/claude/cs/riset/massal'); sys.path.insert(0,'/home/claude/cs/forex_major')
import numpy as np, backtest as B, fx_live as F
import skill_snr_fx_t2 as T2, skill_snr_fx_t2b as T2b
J,=pickle.load(open('/tmp/fxJ.pkl','rb')); FE,q80=pickle.load(open('/tmp/fxfe.pkl','rb'))
dl=[B.load(p) for p in F.PAIRS]; T2.T_END=max(int(P.t[-1]) for P in dl)
ZP={P.name:T2.zona_pair(P) for P in dl}
yr=lambda t: time.gmtime(t["t"]).tm_year
sus=[t for t in J if t["strat"]=="SUS" and (t["pair"],t["t"]//86400) in FE]
def wf_thr(Y,q=0.8,mode="exp"):
    past=[FE[(t["pair"],t["t"]//86400)]["rng5"] for t in sus if yr(t)<Y and (mode=="exp" or yr(t)>=Y-4)]
    return float(np.quantile(past,q)) if len(past)>100 else None
def rwf(tr,w,q=0.8,mode="exp",start=2017):
    th={Y:wf_thr(Y,q,mode) for Y in range(2015,2027)}; out=[]
    for t in tr:
        f=FE.get((t["pair"],t["t"]//86400)); Y=yr(t); k=1.0
        if t["strat"]=="SUS" and f and Y>=start and th[Y] is not None and f["rng5"]>th[Y]: k=w
        if k>0: out.append(dict(t,R=t["R"]*k))
    return out, th
J17=[t for t in J if yr(t)>=2017]
S1=T2.bobot(J,ZP,("SUPDEM",),0.5,1.25,dl)
print("ambang WF ekspansi:",{k:round(v,2) for k,v in rwf(J,0)[1].items() if v})
T2.baris("JUARA",J)
for nm,base in (("",J),("SNR+bulat1,25 ",S1)):
  for q in (0.8,0.9):
    for w in (0.0,0.5):
      for mode in ("exp","4th"):
        X,_=rwf(base,w,q,mode); nmx=f"{nm}WF rng5 q{q} {mode} SUS {w}x"
        T2.baris(nmx,X)
        r=T2b.sig(J,X,1483228800); print(f"     P_rasio 2017+ {r['P_rasio_lebih_baik']:.2f} P_R {r['P_R_lebih_baik']:.2f}")
print("=== cek SNR di atas RNG + stres")
from collections import defaultdict
RNG,_=rwf(J,0.0); SR,_=rwf(S1,0.0); RNG9,_=rwf(J,0.0,0.9); SR9,_=rwf(S1,0.0,0.9)
for a,b,nm in ((RNG,SR,"SNR di atas RNG q0.8"),(RNG9,SR9,"SNR di atas RNG q0.9")):
    for m in (1433116800,T2.T_OOS):
        r=T2b.sig(a,b,m); print(nm,"mulai",time.gmtime(m).tm_year,f"P_rasio {r['P_rasio_lebih_baik']:.2f} P_R {r['P_R_lebih_baik']:.2f}")
def yrs(tr):
    d=defaultdict(float)
    for t in tr: d[yr(t)]+=t["R"]
    return {k:round(v,1) for k,v in sorted(d.items())}
for nm,X in (("JUARA",J),("RNG q0.8",RNG),("SNR+RNG q0.8",SR),("RNG q0.9",RNG9),("SNR+RNG q0.9",SR9)):
    st=[dict(t,R=t["R"]-0.05*(abs(t["R"])>0)) for t in X]
    print(nm,"tahun:",yrs(X)); T2.baris(nm+" STRES -0,05R/trade",st)
pickle.dump(dict(J=J,RNG=RNG,SR=SR,RNG9=RNG9,SR9=SR9),open('/tmp/fx_kand.pkl','wb'))
