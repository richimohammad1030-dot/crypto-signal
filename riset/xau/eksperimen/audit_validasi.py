"""Audit XAU langkah 1: kesetaraan Dukascopy (BID) vs Setra pada periode tumpang tindih.
Pemakaian: python audit_validasi.py <setra.json> <dukascopy.json>"""
import sys
import numpy as np
import audit_mesin as m

S, Dk = m.muat(sys.argv[1]), m.muat(sys.argv[2])
t0 = S[0][0]
# candle
ks, kd = {int(t): j for j, t in enumerate(S[0])}, {int(t): j for j, t in enumerate(Dk[0])}
com = sorted(set(ks) & set(kd))
only_s = [t for t in ks if t not in kd]; only_d = [t for t in kd if t >= t0 and t <= S[0][-1] and t not in ks]
print(f"Candle Setra {len(ks)}, Dukascopy di periode sama {sum(1 for t in kd if t0 <= t <= S[0][-1])}, sama waktu {len(com)}, "
      f"hanya Setra {len(only_s)}, hanya Dukascopy {len(only_d)}")
dc = np.array([S[4][ks[t]] - Dk[4][kd[t]] for t in com])
rs = np.array([S[2][ks[t]] - S[3][ks[t]] for t in com]); rd = np.array([Dk[2][kd[t]] - Dk[3][kd[t]] for t in com])
print(f"Selisih close Setra-Duka: rata {dc.mean():+.3f}, median abs {np.median(abs(dc)):.3f}, p95 abs {np.percentile(abs(dc), 95):.3f} USD")
print(f"Rentang candle: Setra rata {rs.mean():.3f}, Duka {rd.mean():.3f} (rasio {rs.mean()/rd.mean():.3f}), korelasi {np.corrcoef(rs, rd)[0,1]:.3f}")
hrs_s = sorted({(t // 3600) % 24 for t in only_s}); print("Jam UTC candle hanya-Setra:", hrs_s[:24])

# trade juara
ts_ = m.replay(S); td = [x for x in m.replay(Dk) if x["t0"] >= S[0][250]]
ts_ = [x for x in ts_ if x["t0"] >= td[0]["t0"]] if td else ts_
ms = {int(S[0][x["ip"]]): x for x in ts_}
md = {int(Dk[0][x["ip"]]): x for x in td}
both = sorted(set(ms) & set(md))
same_side = sum(1 for k in both if ms[k]["d"] == md[k]["d"])
same_res = sum(1 for k in both if ms[k]["d"] == md[k]["d"] and np.sign(ms[k]["R"]) == np.sign(md[k]["R"]))
same_why = sum(1 for k in both if ms[k]["why"] == md[k]["why"])
rA = np.array([ms[k]["R"] for k in both]); rB = np.array([md[k]["R"] for k in both])
print(f"\nTrade (periode sama sejak {m.wib(td[0]['t0']).date()}): Setra {len(ts_)}, Duka {len(td)}, hari order sama {len(both)}")
print(f"  arah sama {same_side}/{len(both)} ({same_side/len(both)*100:.1f}%), arah+tanda hasil sama {same_res} "
      f"({same_res/len(both)*100:.1f}%), cara keluar sama {same_why} ({same_why/len(both)*100:.1f}%), korelasi R {np.corrcoef(rA, rB)[0,1]:.3f}")
print("  " + m.baris("Setra", m.stat(ts_)))
print("  " + m.baris("Dukascopy", m.stat(td)))
for y in (2025, 2026):
    a, b = f"{y}-01-01", f"{y+1}-01-01"
    print(f"  {y}: Setra {m.stat(ts_, a=a, b=b)['tot']:+.1f}R  Duka {m.stat(td, a=a, b=b)['tot']:+.1f}R")
