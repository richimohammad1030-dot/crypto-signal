import sys, time, pickle
sys.path.insert(0,'/home/claude/cs/riset/massal')
import numpy as np, xau as X
t0=time.time(); D,A,Fz=X.muat(None); M=X.Mesin(D,A,Fz); tr=X.ke_inti(M.trades())
print("trade",len(tr),f"{time.time()-t0:.0f}s"); T,O,H,L,C=D
# D1 (hari UTC) dari H1
day=(T//86400).astype(int); ud,st=np.unique(day,return_index=True); en=np.append(st[1:],len(T))
dh=np.maximum.reduceat(H,st); dl=np.minimum.reduceat(L,st); dc=C[en-1]
tr_=np.maximum(dh[1:]-dl[1:],np.maximum(abs(dh[1:]-dc[:-1]),abs(dl[1:]-dc[:-1]))); tr_=np.insert(tr_,0,dh[0]-dl[0])
def sma(x,n): c=np.cumsum(np.insert(x,0,0)); o=np.full(len(x),np.nan); o[n-1:]=(c[n:]-c[:-n])/n; return o
a14=sma(tr_,14); a100=sma(tr_,100); pos={d:k for k,d in enumerate(ud)}
def fe(t):
    k=pos.get(int(t//86400))
    if k is None or k<110: return None
    j=k-1   # hari sebelumnya yang sudah close
    er=lambda n: abs(dc[j]-dc[j-n])/np.sum(np.abs(np.diff(dc[j-n:j+1])))
    return dict(er20=er(20),er5=er(5),vol=a14[j]/a100[j],rng5=(dh[j-4:j+1].max()-dl[j-4:j+1].min())/a14[j],
                mom20=(dc[j]-dc[j-20])/a14[j])
F={i:fe(x["t0"]) for i,x in enumerate(tr)}
pickle.dump((tr,F),open('/tmp/xau_tr.pkl','wb'))
yr=np.array([time.gmtime(x["t0"]).tm_year for x in tr]); R=np.array([x["r"] for x in tr]); S=np.array([x["strat"] for x in tr])
print("strat:",{s:(int((S==s).sum()),round(R[S==s].sum(),1)) for s in np.unique(S)})
IS=yr<=2021
for s in np.unique(S):
    for f in ("er20","er5","vol","rng5","mom20"):
        msk=(S==s)&np.array([F[i] is not None for i in range(len(tr))])
        x=np.array([F[i][f] if F[i] else np.nan for i in range(len(tr))])
        if (msk&IS).sum()<100: continue
        q=np.nanquantile(x[msk&IS],[0.2,0.4,0.6,0.8]); b=np.digitize(x,q)
        print(s,f,"IS avgR",[round(R[msk&IS&(b==k)].mean(),3) for k in range(5)], "n",(msk&IS).sum())
