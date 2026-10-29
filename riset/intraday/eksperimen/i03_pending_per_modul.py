"""I-03: batas order menunggu per modul (total tetap PEND=3). Salinan portfolio() juara dengan batas tambahan
per modul; replay penuh (slot, pembatalan, urutan isi ikut berubah). Pemakaian: python3 i03_pending_per_modul.py /tmp/data"""
import json, sys
from _umum import bi, sb, orders_mod, ringkas, keputusan, baris

def portfolio_mod(ords, coins, cap, pend_max, lim):
    rank = {c: i for i, c in enumerate(coins)}
    ev = sorted(ords, key=lambda o: (o["t"], rank[o["c"]]))
    pend, pos, sent, taken = [], [], [], []
    def settle(now):
        nonlocal pend, pos
        while True:
            cand = [(o["t_fill"], rank[o["c"]], k) for k, (_, o) in enumerate(pend) if o["filled"] and o["t_fill"] < now]
            if not cand: break
            tf, _, k = min(cand); o = pend[k][1]
            pos = [(e, c) for e, c in pos if e > tf]
            pend = [p for p in pend if p[1] is not o and (p[0] > tf)]
            if len(pos) < cap:
                pos.append((o["t_exit"], o["c"])); taken.append(o)
                if len(pos) >= cap: pend = []
        pend = [p for p in pend if p[0] > now]
        pos = [(e, c) for e, c in pos if e > now]
    for o in ev:
        settle(o["t"])
        if o["c"] in {c for _, c in pos} | {x["c"] for _, x in pend} or len(pend) >= pend_max or len(pos) >= cap: continue
        if sum(x["m"] == o["m"] for _, x in pend) >= lim.get(o["m"], 99): continue     # <- aturan baru
        sent.append(o)
        pend.append(((o["t_fill"] + 1) if o["filled"] else o["t_exp"], o))
    settle(2_000_000_000)
    return sent, sorted(taken, key=lambda o: o["t_exit"])

D = sys.argv[1]
ords = orders_mod(D, {}, "A") + orders_mod(D, {}, "B")
var = {"juara": {}, "A<=1": {"A": 1}, "A<=2": {"A": 2}, "B<=1": {"B": 1}, "B<=2": {"B": 2},
       "A<=1,B<=2": {"A": 1, "B": 2}, "A<=2,B<=1": {"A": 2, "B": 1}}
res = {k: ringkas(*portfolio_mod(ords, sb.COINS, bi.PARAM["CAP"], bi.PARAM["PEND"], v)) for k, v in var.items()}
base = res["juara"]
# cek: salinan tanpa batas == juara asli
s0, t0 = bi.portfolio(ords, sb.COINS, bi.PARAM["CAP"], bi.PARAM["PEND"])
assert bi.stats(t0, s0) == base["semua"], "salinan portfolio tidak sama dengan juara"
for k, s in res.items():
    print(baris(k + (" *" if k == "juara" else ""), s, None if k == "juara" else keputusan(base, s)))
json.dump(res, open(sys.argv[2] if len(sys.argv) > 2 else "/tmp/i03.json", "w"))
