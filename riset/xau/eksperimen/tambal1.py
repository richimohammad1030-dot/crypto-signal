"""Putaran 1 tambal-celah (6 Nov 2026): celah = rezim mendatar/berganti di sekitar MA200 (2018, 2021). Penambal (literatur:
pita netral/histeresis MA; arah tren dari kemiringan MA, mis. Faber 2007 & trend-following klasik):
  Z  zona netral |harga-MA200| < X% (X 1/2/3): di zona -> aturan ketat dua arah (BUY <= 15, SELL >= 85) atau tanpa MR (K6 saja)
  S  arah tren = kemiringan MA200 (MA hari ini vs L hari lalu, L 10/20/40) menggantikan posisi harga vs MA
  ZS gabungan: tren = kemiringan; zona netral bila kemiringan & posisi harga tidak sepakat
Selain hari MR -> K6 + susulan (tetap). Catatan: 2015 sebagian tanpa MA200 (data mulai 2015) = efek data awal.
Pemakaian: python tambal1.py <sambung.json> <ambigu.json>"""
import sys, itertools
import numpy as np
sys.argv = sys.argv[:3]
exec(open("simetris.py").read().split("KAND = {}")[0])
ma200 = sma(dC, 200)
def aturan(k, i, rezim):
    r = r07[k]
    if rezim == "naik":
        return 1 if r <= m.gb.MR_BUY else -1 if r >= m.gb.MR_SELL else 0
    if rezim == "turun":
        return -1 if r >= 70 else 1 if r <= 15 else 0
    if rezim == "netral_ketat":
        return 1 if r <= 15 else -1 if r >= 85 else 0
    return 0                                   # "netral_k6": tanpa MR
def sinyal(fn):
    out = {}
    for k, i in enumerate(i07):
        d = aturan(k, i, fn(k))
        if d: out[i] = d
    return out
def rez_posisi(k):
    return "naik" if np.isnan(ma200[k]) or dC[k] > ma200[k] else "turun"
VAR = {"DASAR hibrida MA200": rez_posisi}
for X, mode in itertools.product((1, 2, 3), ("netral_ketat", "netral_k6")):
    VAR[f"Z zona {X}% -> {mode}"] = (lambda k, X=X, mode=mode: rez_posisi(k) if np.isnan(ma200[k]) or abs(dC[k] / ma200[k] - 1) * 100 >= X else mode)
for Lb in (10, 20, 40):
    VAR[f"S kemiringan {Lb}h"] = (lambda k, Lb=Lb: "naik" if k < Lb or np.isnan(ma200[k - Lb]) or ma200[k] >= ma200[k - Lb] else "turun")
    for mode in ("netral_ketat", "netral_k6"):
        def f(k, Lb=Lb, mode=mode):
            if k < Lb or np.isnan(ma200[k - Lb]): return "naik"
            a = "naik" if ma200[k] >= ma200[k - Lb] else "turun"
            return a if a == rez_posisi(k) else mode
        VAR[f"ZS kemiringan {Lb}h + tidak sepakat -> {mode[7:]}"] = f
print("R/thn: 2015-21 · 2022-Jan25 · Setra · 12t | ... | P uji vs bot live")
baris("BOT LIVE (hibrida MA100)", ukur(BASE))
for nm, fn in VAR.items():
    u = ukur(sistem(sinyal(fn))); baris(nm, u)
    print("      " + " ".join(f"{str(y)[2:]}:{v:+.0f}" for y, v in u["th"].items()))
