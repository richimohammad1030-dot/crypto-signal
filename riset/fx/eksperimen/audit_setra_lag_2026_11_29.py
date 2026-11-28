"""Audit data live FX (29 Nov 2026) bagian 1: lag waktu feed Setra FX H1 vs Dukascopy H1 per pair & bulan (korelasi return H1 maksimum).
Pemakaian (dari root repo): python riset/fx/eksperimen/audit_setra_lag_2026_11_29.py"""
import sys,time,json,gzip
sys.path.insert(0,'.')
from fx_bot import fetch
import numpy as np
from collections import defaultdict
res={}
for p in ['EURUSD','GBPUSD','USDJPY','AUDUSD','USDCAD','USDCHF','NZDUSD']:
    s=fetch(p,400); S={r[0]:r[4] for r in s}
    d={r[0]:r[4] for f in ['2025','2026'] for r in json.load(gzip.open(f'forex_major/data/{p}_h1_{f}.json.gz'))}
    bym=defaultdict(list)
    for k in S: bym[time.strftime('%Y-%m',time.gmtime(k))].append(k)
    row={}
    for m,ks in sorted(bym.items()):
        best=None
        for h in range(-24,25):
            sh=h*3600; t=[k for k in ks if k+3600 in S and k+sh in d and k+3600+sh in d]
            if len(t)<50: continue
            c=np.corrcoef([S[k+3600]-S[k] for k in t],[d[k+3600+sh]-d[k+sh] for k in t])[0,1]
            if best is None or c>best[1]: best=(h,c,len(t))
        row[m]=f"{best[0]:+d}j r{best[1]:.2f}" if best else '-'
    res[p]=row; print(p,row,flush=True)
