import sys, pickle, time
sys.path.insert(0,'/home/claude/cs/forex_major')
import numpy as np, backtest as B, fx_live as F
from backtest import atr, prev_daily
J,=pickle.load(open('/tmp/fxJ.pkl','rb'))
data={p:B.load(p) for p in F.PAIRS}
FE={}
for p,P in data.items():
    idx,D=prev_daily(P); A=atr(D); A100=atr(D,100); c=D["c"]
    for d,j in idx.items():
        if j<110: continue
        er=abs(c[j]-c[j-20])/np.sum(np.abs(np.diff(c[j-20:j+1])))
        er5=abs(c[j]-c[j-5])/np.sum(np.abs(np.diff(c[j-5:j+1])))
        rng5=(D["h"][j-4:j+1].max()-D["l"][j-4:j+1].min())/A[j]
        FE[(p,d)]=dict(er20=er,er5=er5,vol=A[j]/A100[j],rng5=rng5)
def tab(strat):
    tr=[t for t in J if t["strat"]==strat and (t["pair"],t["t"]//86400) in FE]
    for f in ("er20","er5","vol","rng5"):
        x=np.array([FE[(t["pair"],t["t"]//86400)][f] for t in tr]); R=np.array([t["R"] for t in tr]); y=np.array([time.gmtime(t["t"]).tm_year for t in tr])
        isx=y<=2022; q=np.quantile(x[isx],[0.2,0.4,0.6,0.8]); b=np.digitize(x,q)
        print(strat,f,"IS avgR/kuintil",[round(R[isx&(b==k)].mean(),3) for k in range(5)],"| OOS",[round(R[~isx&(b==k)].mean(),3) for k in range(5)],"| 2023",[round(R[(y==2023)&(b==k)].sum(),1) for k in range(5)])
tab("SUS"); tab("N3")
sys.path.insert(0,'/home/claude/cs/riset/fx/eksperimen'); sys.path.insert(0,'/home/claude/cs/riset'); sys.path.insert(0,'/home/claude/cs/riset/massal')
import skill_snr_fx_t2 as T2, skill_snr_fx_t2b as T2b
dl=list(data.values()); T2.T_END=max(int(P.t[-1]) for P in dl)
ZP={P.name:T2.zona_pair(P) for P in dl}
tr=[t for t in J if t["strat"]=="SUS" and (t["pair"],t["t"]//86400) in FE]
x=np.array([FE[(t["pair"],t["t"]//86400)]["rng5"] for t in tr]); y=np.array([time.gmtime(t["t"]).tm_year for t in tr])
q80=float(np.quantile(x[y<=2022],0.8)); print("ambang rng5 q80 IS =",round(q80,2),"ATR")
def rw(tr,w,strats=("SUS",)):
    out=[]
    for t in tr:
        f=FE.get((t["pair"],t["t"]//86400))
        k=w if (t["strat"] in strats and f and f["rng5"]>q80) else 1.0
        if k>0: out.append(dict(t,R=t["R"]*k))
    return out
V={"RNG SUS 0x":rw(J,0.0),"RNG SUS 0,5x":rw(J,0.5),"RNG semua 0,5x":rw(J,0.5,("SUS","N3","B3"))}
S1=T2.bobot(J,ZP,("SUPDEM",),0.5,1.25,dl)
V["SNR+bulat1,25 + RNG SUS 0x"]=rw(S1,0.0); V["SNR+bulat1,25 + RNG SUS 0,5x"]=rw(S1,0.5)
S2=T2.bobot(J,ZP,("SUPDEM",),0.5,1.5,dl); V["SNR+bulat1,5 + RNG SUS 0,5x"]=rw(S2,0.5); V["SNR+bulat1,5 + RNG SUS 0x"]=rw(S2,0.0)
T2.baris("JUARA",J)
for k,X in V.items():
    T2.baris(k,X)
    for lbl,m in (("penuh",T2.T_IS0),("OOS",T2.T_OOS)):
        r=T2b.sig(J,X,m); print(f"     P_rasio {lbl} {r['P_rasio_lebih_baik']:.2f} P_R {r['P_R_lebih_baik']:.2f} R/thn {r['penantang']['R_thn']} DD {r['penantang']['DD']}")
pickle.dump((FE,q80),open('/tmp/fxfe.pkl','wb'))
