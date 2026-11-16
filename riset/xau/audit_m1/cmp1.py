from m1sim import *
import datetime as dt, collections
base = mm.baseline(D, A, F)                       # mesin H1 repo (ambigu BUY = asumsi bot)
res, sk = run()                                    # M1 eksak, bid-only, flat 0,40 (apel-ke-apel dengan repo)
def ym(t): return dt.datetime.fromtimestamp(int(t)+3600, dt.timezone.utc).strftime("%Y-%m")
ok_ip = {x["ip"] for x in res} | set()
days_ok = set(int(i) for i in np.flatnonzero(HR == gb.PLACE_HOUR_UTC)) - set(int(s) for s in sk)
H1t = [x for x in base if x["ip"] in days_ok and T[x["ip"]] >= M1_START]
def yr(t): return dt.datetime.fromtimestamp(int(t)+3600, dt.timezone.utc).year
def summ(trs, key):
    out = collections.defaultdict(float); n = collections.defaultdict(int)
    for x in trs: out[yr(x["t0"])] += key(x); n[yr(x["t0"])] += 1
    return out, n
h_net = lambda x: (x["R"] - 0.40/x["r0"]) * x.get("w", 1.0)
m_net = lambda x: x["net"]
hy, hn = summ(H1t, h_net); my, mn = summ(res, m_net)
print("Tahun   H1: n  netR   |  M1: n  netR   | selisih")
th=tm=0
for y in sorted(set(hy)|set(my)):
    print(y, f"{hn[y]:4d} {hy[y]:+7.1f} | {mn[y]:4d} {my[y]:+7.1f} | {my[y]-hy[y]:+6.1f}"); th+=hy[y]; tm+=my[y]
print("TOTAL", f"H1 {th:+.1f} ({len(H1t)} trade)  M1 {tm:+.1f} ({len(res)} trade)")
for st in ("KOMBO","MR","K6","SUS"):
    h=[x for x in H1t if x["strat"]==st]; r=[x for x in res if x["strat"]==st]
    print(f"{st:6s} H1 n={len(h):4d} net={sum(h_net(x) for x in h):+7.1f} | M1 n={len(r):4d} net={sum(m_net(x) for x in r):+7.1f}")
# kecocokan trade
hm = {(x["ip"],x["strat"]):x for x in H1t}; mt = {(x["ip"],x["strat"]):x for x in res}
common = set(hm)&set(mt)
print("trade sama (ip,strat):", len(common), "dari H1", len(hm), "M1", len(mt))
dsign = sum(1 for k in common if hm[k]["d"]!=mt[k]["d"]); print("arah beda di trade sama:", dsign)
import statistics
dr=[mt[k]["net"]-h_net(hm[k]) for k in common]
print("selisih net per trade sama: mean %.4f  sd %.3f  |>0.3R|: %d"%(statistics.mean(dr), statistics.pstdev(dr), sum(abs(v)>0.3 for v in dr)))
for st in ("KOMBO","MR","K6","SUS"):
    ks=[k for k in common if k[1]==st]; 
    print(st, "mean selisih %.4f n=%d"%(statistics.mean(mt[k]['net']-h_net(hm[k]) for k in ks), len(ks)))
only_h=[hm[k] for k in hm if k not in mt]; only_m=[mt[k] for k in mt if k not in hm]
print("hanya di H1:", len(only_h), "net", round(sum(h_net(x) for x in only_h),1), "| hanya di M1:", len(only_m), "net", round(sum(m_net(x) for x in only_m),1))
print("  hanya H1 per strat:", collections.Counter(x["strat"] for x in only_h), " hanya M1:", collections.Counter(x["strat"] for x in only_m))
