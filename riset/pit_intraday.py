"""Uji bias koin selamat untuk INTRADAY: juara dengan daftar koin tetap (signal_bot.COINS) vs daftar koin SESUAI MASANYA
(riset/pit.py; termasuk koin yang sudah delisting). Mesin & model eksekusi sama dengan riset/backtest_intraday.py:
sinyal hanya untuk koin yang masuk 50 besar pada bulan itu, prioritas order = peringkat bulan itu.
Pemakaian: python riset/pit_intraday.py <repo> <data> ['{"PARAM": nilai}']   (argumen ke-3 opsional: parameter penantang)"""
import collections, json, os, sys, time
REPO, DATA = sys.argv[1:3]
OVER = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
sys.path.insert(0, REPO); sys.path.insert(0, os.path.join(REPO, "riset"))
import numpy as np
import backtest_intraday as bi, pit, signal_bot as sb

def run_pit(P):
    pit._load(DATA)
    coins = sorted({c for m in pit._SNAP for c in pit.ranked(DATA, m)[:70]} | set(sb.COINS))
    H1, M15 = bi.load(DATA, coins)
    first = {c: int(D["T"][900]) for c, D in M15.items() if len(D["T"]) > 900}
    uni = pit.universe_fn(DATA, lambda c, t: c in first and c in H1 and first[c] <= t)
    ords = [o for o in bi.orders(H1, M15, P) if o["c"] in uni(o["t"])]
    # portofolio dengan prioritas peringkat bulan berjalan
    rank_of = lambda o: uni(o["t"]).index(o["c"])
    ev = sorted(ords, key=lambda o: (o["t"], rank_of(o)))
    pend, pos, sent, taken = [], [], [], []
    def settle(now):
        nonlocal pend, pos
        while True:
            cand = [(o["t_fill"], rank_of(o), k) for k, (_, o) in enumerate(pend) if o["filled"] and o["t_fill"] < now]
            if not cand: break
            tf, _, k = min(cand); o = pend[k][1]
            pos = [(e, c) for e, c in pos if e > tf]
            pend = [p for p in pend if p[1] is not o and p[0] > tf]
            if len(pos) < P["CAP"]:
                pos.append((o["t_exit"], o["c"])); taken.append(o)
                if len(pos) >= P["CAP"]: pend = []
        pend = [p for p in pend if p[0] > now]; pos = [(e, c) for e, c in pos if e > now]
    for o in ev:
        settle(o["t"])
        if o["c"] in {c for _, c in pos} | {x["c"] for _, x in pend} or len(pend) >= P["PEND"] or len(pos) >= P["CAP"]: continue
        sent.append(o); pend.append(((o["t_fill"] + 1) if o["filled"] else o["t_exp"], o))
    settle(2_000_000_000)
    return sent, sorted(taken, key=lambda o: o["t_exit"])

if __name__ == "__main__":
    P = dict(bi.PARAM, **OVER)
    _, s0, t0 = bi.run(REPO, DATA, OVER)
    s1, t1 = run_pit(P)
    print("INTRADAY · parameter:", OVER or "juara")
    for nm, s, t in (("tetap", s0, t0), ("sesuai masanya", s1, t1)):
        for lab, a, b in (("semua", None, None), ("2020-23", None, bi.IS_END), ("2024-", bi.IS_END, None)):
            st = bi.stats(t, s, a, b)
            print(f"  {nm:<15} {lab:<8} n={st['n']:5d} win {st['win']}% avg {st['avgR']:+.4f}R R/thn {st['totR_thn']:+6.1f} DD {st['maxDD']:5.1f}R rasio {st['rasio']:5.2f} fill {st['fill']}%")
        yr = collections.defaultdict(float)
        for o in t: yr[time.gmtime(o["t"]).tm_year] += o["R"]
        print(f"  {'':<15} per tahun " + " ".join(f"{y}:{v:+.0f}" for y, v in sorted(yr.items())))
    cur = set(sb.COINS); mati = [o["R"] for o in t1 if o["c"] not in cur]
    if mati: print(f"  trade di koin yang TIDAK ada di daftar sekarang: {len(mati)} · {sum(mati):+.1f}R · avg {np.mean(mati):+.3f}R")
