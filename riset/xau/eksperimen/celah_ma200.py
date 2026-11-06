"""Putaran 1 tambal-celah (6 Nov 2026, pemilik): bedah celah sistem dasar hibrida MA200 (#42b). Per tahun x komponen
(MR naik/turun, K6, SUS), per kondisi pasar (volatilitas ATR relatif, kekuatan tren ADX harian, jarak harga ke MA200, arah
tren berubah-ubah), dan bulan-bulan rugi terbesar. Pemakaian: python celah_ma200.py <sambung.json> <ambigu.json>"""
import sys, json
import numpy as np
sys.argv = sys.argv[:3]
exec(open("simetris.py").read().split("KAND = {}")[0])
G = mm.baseline(D, A, F, ambigu=AMB, sig=mm.sinyal_hibrida(D, 200))
for x, v in zip(G, m.net(G)): x["Rn"] = float(v)
k07 = {i: k for k, i in enumerate(i07)}
ma200 = sma(dC, 200)
def fitur(x):
    k = k07.get(x["ip"]); i = x["ip"]
    if k is None: return None
    atr_rel = A[i] / np.median(A[max(0, i - 500):i + 1])
    jarak = (dC[k] - ma200[k]) / ma200[k] * 100 if not np.isnan(ma200[k]) else np.nan
    seb = [dC[j] > ma200[j] for j in range(max(0, k - 20), k + 1) if not np.isnan(ma200[j])]
    silang = sum(1 for a, b in zip(seb, seb[1:]) if a != b)
    return dict(tahun=m.wib(x["t0"]).year, komp=x["strat"] + ("" if x["strat"] != "MR" else ("-naik" if np.isnan(ma200[k]) or dC[k] > ma200[k] else "-turun")),
                atr=atr_rel, adx=ADX[k - 1] if k else 0, jarak=jarak, silang=silang, arah="BUY" if x["d"] == 1 else "SELL")
for x in G: x["f"] = fitur(x)
G = [x for x in G if x["f"]]
th = sorted({x["f"]["tahun"] for x in G})
print("1) R bersih per tahun x komponen")
komp = sorted({x["f"]["komp"] for x in G})
print("      " + "".join(f"{k:>10}" for k in komp) + "     TOTAL")
for y in th:
    r = [sum(x["Rn"] for x in G if x["f"]["tahun"] == y and x["f"]["komp"] == k) for k in komp]
    print(f"{y}  " + "".join(f"{v:>+10.1f}" for v in r) + f"{sum(r):>+10.1f}")
def tabel(nm, key, batas):
    print(f"\n{nm}: rata R/trade (n) di tahun LEMAH (2015,2018,2021,2023) vs tahun lain")
    for lo, hi in batas:
        f = lambda x: lo <= x["f"][key] < hi
        a = [x["Rn"] for x in G if f(x) and x["f"]["tahun"] in (2015, 2018, 2021, 2023)]
        b = [x["Rn"] for x in G if f(x) and x["f"]["tahun"] not in (2015, 2018, 2021, 2023)]
        print(f"  {key} {lo}-{hi}: lemah {np.mean(a) if a else 0:+.3f} ({len(a)}) · lain {np.mean(b) if b else 0:+.3f} ({len(b)}) · total {sum(a)+sum(b):+.0f}R")
tabel("2) Volatilitas", "atr", ((0, 0.8), (0.8, 1.0), (1.0, 1.25), (1.25, 9)))
tabel("3) Kekuatan tren ADX harian", "adx", ((0, 15), (15, 20), (20, 25), (25, 30), (30, 99)))
tabel("4) Jarak harga ke MA200 (%)", "jarak", ((-99, -5), (-5, -2), (-2, 0), (0, 2), (2, 5), (5, 10), (10, 99)))
tabel("5) Berapa kali harga menyeberang MA200 dalam 20 hari", "silang", ((0, 1), (1, 2), (2, 4), (4, 99)))
print("\n6) Kondisi pasar per tahun: ATR rel median · ADX median · % hari di atas MA200 · gerak emas setahun")
for y in th:
    t = [x for x in G if x["f"]["tahun"] == y]
    ks = [k for k, i in enumerate(i07) if m.wib(T[i]).year == y]
    up = np.mean([dC[k] > ma200[k] for k in ks if not np.isnan(ma200[k])]) * 100 if ks else 0
    print(f"  {y}: ATR {np.median([x['f']['atr'] for x in t]):.2f} · ADX {np.median([ADX[k] for k in ks]):4.1f} · di atas MA200 {up:3.0f}% · emas {(dC[ks[-1]]/dC[ks[0]]-1)*100:+5.1f}% · R {sum(x['Rn'] for x in t):+.0f}")
print("\n7) 8 bulan terburuk")
bl = {}
for x in G: bl.setdefault(m.wib(x["t0"]).strftime("%Y-%m"), []).append(x)
for b, t in sorted(bl.items(), key=lambda z: sum(x["Rn"] for x in z[1]))[:8]:
    kk = {}
    for x in t: kk[x["f"]["komp"]] = kk.get(x["f"]["komp"], 0) + x["Rn"]
    print(f"  {b}: {sum(x['Rn'] for x in t):+5.1f}R · " + " ".join(f"{k} {v:+.1f}" for k, v in kk.items()) + f" · ADX med {np.median([x['f']['adx'] for x in t]):.0f} · ATR {np.median([x['f']['atr'] for x in t]):.2f}")
