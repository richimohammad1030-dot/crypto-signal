"""Audit XAU langkah 2: diagnosa juara di data panjang. Pemakaian: python audit_diagnosa.py <xau.json> [setra.json]"""
import sys
import numpy as np
import audit_mesin as m

D = m.muat(sys.argv[1])
A = np.array(m.atr(list(D[2]), list(D[3]), list(D[4]), m.gb.ATR_N))
F = m.fitur(D, A)
tr = m.replay(D, A=A)
T, O, H, L, C = D
print("Data", m.wib(T[0]).date(), "-", m.wib(T[-1]).date(), "candle", len(T), "trade", len(tr))


def grup(nama, kunci, data=tr):
    g = {}
    for x in data:
        k = kunci(x)
        if k is not None:
            g.setdefault(k, []).append(x)
    print(f"\n== {nama}")
    for k in sorted(g):
        s = m.stat(g[k]); r_gross = np.mean([x["R"] for x in g[k]])
        print(f"{str(k):<16} n={s['n']:>4} win={s['wr']*100:4.1f}% kotor={r_gross:+.3f} bersih={s['avg']:+.3f} "
              f"tot={s['tot']:+7.1f} DD={s['dd']:5.1f} biaya/R={np.mean([0.4/x['r0'] for x in g[k]]):.3f} "
              f"r0/harga={np.mean([x['r0']/x['e'] for x in g[k]])*100:.2f}%")


w = lambda x: m.wib(x["t0"])
grup("Per tahun", lambda x: w(x).year)
grup("Per kuartal", lambda x: f"{w(x).year}Q{(w(x).month-1)//3+1}")
grup("Arah", lambda x: "BUY" if x["d"] == 1 else "SELL")
grup("Cara keluar", lambda x: x["why"])
grup("Hari (WIB, hari order)", lambda x: m.wib(T[x["ip"]] + 3600).strftime("%w-%a"))
grup("Jam terisi (WIB)", lambda x: m.wib(x["t0"]).hour)


def q(arr, x, qs):
    v = arr[x["ip"]]
    if np.isnan(v):
        return None
    return int(np.searchsorted(qs, v))


for key in ("atr_rel", "atr_vs1y", "pct1y", "d_atr_rel"):
    vals = np.array([F[key][x["ip"]] for x in tr]); vals = vals[~np.isnan(vals)]
    qs = np.quantile(vals, [0.2, 0.4, 0.6, 0.8])
    print(f"\n[{key}] batas kuintil:", np.round(qs, 5))
    grup(f"Kuintil {key} (0 = terendah)", lambda x, k=key, qq=qs: q(F[k], x, qq))

# ambang absolut ATR relatif (H1, persen harga)
grup("ATR H1 / harga (%)", lambda x: f"{min(int(F['atr_rel'][x['ip']]*1000)/10, 0.4):.1f}+")
for n in (50, 200):
    grup(f"Tren H1 EMA{n}: posisi searah?", lambda x, n=n: "searah" if (C[x["ip"]] > F[f"ema{n}"][x["ip"]]) == (x["d"] == 1) else "lawan")
for n in (20, 50, 200):
    grup(f"Tren D1 EMA{n}: posisi searah?", lambda x, n=n: None if np.isnan(F[f"d_ema{n}"][x["ip"]]) else
         ("searah" if (C[x["ip"]] > F[f"d_ema{n}"][x["ip"]]) == (x["d"] == 1) else "lawan"))
grup("Tren D1 EMA50 (pasar)", lambda x: None if np.isnan(F["d_ema50"][x["ip"]]) else
     ("naik" if C[x["ip"]] > F["d_ema50"][x["ip"]] else "turun"))
grup("Lebar range / ATR", lambda x: f"{min(int((max(H[x['ip']-2:x['ip']+1])-min(L[x['ip']-2:x['ip']+1]))/x['a']*2)/2, 3):.1f}")

# dampak biaya
r = np.array([x["R"] for x in tr]); c = np.array([0.4 / x["r0"] for x in tr])
print(f"\n== Biaya: kotor {r.sum():+.1f}R ({r.mean():+.3f}/trade), biaya {c.sum():.1f}R ({c.mean():.3f}/trade), "
      f"bersih {(r-c).sum():+.1f}R. Slip +0,20 USD: {(r - 0.6/np.array([x['r0'] for x in tr])).sum():+.1f}R")
for y in sorted({w(x).year for x in tr}):
    s = [x for x in tr if w(x).year == y]
    print(f"{y}: kotor {np.sum([x['R'] for x in s]):+6.1f} biaya {np.sum([0.4/x['r0'] for x in s]):5.1f} "
          f"r0 rata {np.mean([x['r0'] for x in s]):5.2f} USD harga {np.mean([x['e'] for x in s]):6.0f}")

# hari terburuk & beruntun
rn = m.net(tr)
o = np.argsort(rn)[:10]
print("\n== 10 trade terburuk (bersih)")
for j in o:
    x = tr[j]; print(m.wib(x["t0"]).strftime("%Y-%m-%d %H:%M"), "BUY " if x["d"] == 1 else "SELL", f"{rn[j]:+.2f}R", x["why"],
                     f"r0={x['r0']:.2f}", f"gap entry={abs(x['e'] - (max(H[x['ip']-2:x['ip']+1]) if x['d']==1 else min(L[x['ip']-2:x['ip']+1]))):.2f}")
s = m.stat(tr)
print("\nKalah beruntun maks", s["lmax"], "· menang beruntun maks", s["wmax"])
eq = np.cumsum(rn); pk = np.maximum.accumulate(eq); j = int(np.argmax(pk - eq)); i0 = int(np.argmax(eq[:j + 1]))
print(f"DD terdalam {pk[j]-eq[j]:.1f}R: puncak {m.wib(tr[i0]['t0']).date()} -> lembah {m.wib(tr[j]['t0']).date()}")
print("\nSemua:", m.baris("juara", s))
for nm, (a, b) in (("2015-2021", m.PILIH), ("2022-Jan25", m.UJI), ("Feb25-skrg", m.KONF)):
    print(m.baris(nm, m.stat(tr, a=a, b=b)))
