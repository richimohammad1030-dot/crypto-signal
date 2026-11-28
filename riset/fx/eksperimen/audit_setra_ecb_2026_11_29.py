"""Audit data live FX (29 Nov 2026) bagian 2: jangkar independen kurs acuan ECB EURUSD (frankfurter.dev, 14:15 CET) vs Dukascopy & Setra.
Pemakaian (dari root repo): python riset/fx/eksperimen/audit_setra_ecb_2026_11_29.py"""
import sys,time,json,gzip,urllib.request,calendar
sys.path.insert(0,'.')
from fx_bot import fetch
import numpy as np
ecb={}
for a,b in [("2026-01-02","2026-06-30"),("2026-07-01","2026-11-27")]:
    j=json.load(urllib.request.urlopen(f"https://api.frankfurter.dev/v1/{a}..{b}?from=EUR&to=USD"))
    ecb.update({k:v["USD"] for k,v in j["rates"].items()})
S={r[0]:r for r in fetch('EURUSD',400)}
D={r[0]:r for r in json.load(gzip.open('forex_major/data/EURUSD_h1_2026.json.gz'))}
def at(src,ts):  # harga di ts: open candle jam itu + 15 menit ~ pakai open candle berikut-nya rata2
    k=ts//3600*3600
    return src[k][1]+(src[k][4]-src[k][1])*0.25 if k in src else None
for nama,src,lag in [("Dukascopy",D,0),("Setra (jam sama)",S,0),("Setra +15 jam",S,15*3600),("Setra +18 jam",S,18*3600)]:
    e=[]
    for day,v in ecb.items():
        t=calendar.timegm(time.strptime(day,"%Y-%m-%d"))
        dst=time.localtime(t)  # perkiraan CET/CEST: Mar-akhir s/d Okt-akhir musim panas
        m=int(day[5:7]); summer = 4<=m<=10 or (m==3 and int(day[8:])>=29)
        ts=t+(12 if summer else 13)*3600+900+lag
        x=at(src,ts)
        if x: e.append(abs(x-v)/1e-4)
    print(f"{nama}: n={len(e)} selisih median {np.median(e):.1f} pip · rata {np.mean(e):.1f}")
