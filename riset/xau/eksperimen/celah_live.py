"""Tambal-celah putaran 2 (10 Nov 2026): bedah sistem live (kombinasi #58 + hibrida + K6 + susulan) di 2005-2026.
Per tahun × komponen & arah; kondisi pasar per tahun (tren harian, gerak emas, ATR relatif, ADX); R per kondisi di tahun minus
vs tahun lain. Pemakaian: python celah_live.py <xau_2004.json> <ambigu.json>"""
import sys, json
import numpy as np
sys.argv = sys.argv[:3]
exec(open("simetris.py").read().split("KAND = {}")[0])
G = [x for x in BASE if m.wib(x["t0"]).year >= 2005]
for x, v in zip(G, m.net(G)): x["Rn"] = float(v)
k07 = {i: k for k, i in enumerate(i07)}; ma100 = sma(dC, 100); ma200 = sma(dC, 200)
MINUS = (2005, 2006, 2013, 2014, 2018, 2021)
for x in G:
    k = k07.get(x["ip"]); i = x["ip"]; x["y"] = m.wib(x["t0"]).year
    x["kd"] = f"{x['strat']}-{'B' if x['d'] == 1 else 'S'}"
    x["d1"] = "naik" if k is None or np.isnan(ma100[k]) or dC[k] > ma100[k] else "turun"
    x["searah"] = "searah D1" if (x["d"] == 1) == (x["d1"] == "naik") else "lawan D1"
    x["atr"] = A[i] / np.median(A[max(0, i - 500):i + 1]); x["adx"] = ADX[k - 1] if k else 0
kd = sorted({x["kd"] for x in G})
print("1) R per tahun × komponen-arah (B=BUY, S=SELL)")
print("      " + "".join(f"{k:>9}" for k in kd) + "    TOTAL")
for y in range(2005, 2027):
    r = [sum(x["Rn"] for x in G if x["y"] == y and x["kd"] == k) for k in kd]
    print(f"{y}{'*' if y in MINUS else ' '} " + "".join(f"{v:>+9.1f}" for v in r) + f"{sum(r):>+9.1f}")
print("\n2) Kondisi pasar per tahun: emas setahun · % hari tren D1 naik · ATR rel median · ADX median · jumlah ganti arah D1")
for y in range(2005, 2027):
    ks = [k for k, i in enumerate(i07) if m.wib(T[i]).year == y]
    up = [dC[k] > ma100[k] for k in ks if not np.isnan(ma100[k])]
    gn = sum(1 for a, b in zip(up, up[1:]) if a != b)
    t = [x for x in G if x["y"] == y]
    print(f"  {y}{'*' if y in MINUS else ' '}: emas {(dC[ks[-1]]/dC[ks[0]]-1)*100:+6.1f}% · naik {np.mean(up)*100:3.0f}% · ATR {np.median([x['atr'] for x in t]):.2f} · ADX {np.median([ADX[k] for k in ks]):4.1f} · ganti arah {gn:>2} · R {sum(x['Rn'] for x in t):+5.1f}")
def tab(nm, key, vals):
    print(f"\n{nm}: R/trade (n) tahun MINUS vs tahun lain")
    for v in vals:
        a = [x["Rn"] for x in G if x[key] == v and x["y"] in MINUS]; b = [x["Rn"] for x in G if x[key] == v and x["y"] not in MINUS]
        print(f"  {v:<10} minus {np.mean(a):+.3f} ({len(a)}, {sum(a):+.0f}R) · lain {np.mean(b):+.3f} ({len(b)}, {sum(b):+.0f}R)")
tab("3) Komponen-arah", "kd", kd)
tab("4) Searah/lawan tren harian", "searah", ["searah D1", "lawan D1"])
for x in G: x["atrk"] = "rendah" if x["atr"] < 0.9 else "normal" if x["atr"] < 1.2 else "tinggi"; x["adxk"] = "<20" if x["adx"] < 20 else "20-30" if x["adx"] < 30 else ">=30"
tab("5) Volatilitas", "atrk", ["rendah", "normal", "tinggi"])
tab("6) ADX harian", "adxk", ["<20", "20-30", ">=30"])
