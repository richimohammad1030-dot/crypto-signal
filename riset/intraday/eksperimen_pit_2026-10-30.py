"""Eksplorasi intraday dengan daftar koin SESUAI MASANYA: modul A/B, batas peringkat, SL/TP tetap 1:1, durasi hold.
Semua dipilih di 2020-2023 (PIT), diuji di 2024-skrg (PIT) + signifikansi vs juara."""
import collections, itertools, json, os, sys, time, pickle
REPO, DATA = "/home/claude/crypto-signal", "/home/claude/data"
sys.path.insert(0, REPO); sys.path.insert(0, REPO + "/riset")
import numpy as np
import backtest_intraday as bi, pit, signal_bot as sb, signifikansi as sg
S = "/tmp/claude-0/-home-claude/563667fa-fea2-5514-8f49-dd552a9116a1/scratchpad"

pit._load(DATA)
coins = sorted({c for m in pit._SNAP for c in pit.ranked(DATA, m)[:70]} | set(sb.COINS))
H1, M15 = bi.load(DATA, coins)
first = {c: int(D["T"][900]) for c, D in M15.items() if len(D["T"]) > 900}
uni = pit.universe_fn(DATA, lambda c, t: c in first and c in H1 and first[c] <= t)
rank = lambda o: uni(o["t"]).index(o["c"]) if o["c"] in uni(o["t"]) else 999
P0 = dict(bi.PARAM)

def ordersA(sl=3.0, off=0.25, valid_min=120, hold_h=2, mode="rsi", tp_r=1.0, vmin=0.015):
    out = []
    for c, D in M15.items():
        T, C, A, R2, R14, reg = D["T"], D["C"], D["A"], D["R2"], D["R14"], D["reg"]; nxt = 0
        for i in np.flatnonzero((reg == 1) & ((R2 < 5) | (R14 < 30)) & (A / C >= vmin)):
            if i < max(nxt, 900) or i + 1 >= len(T) or T[i] < P0["START"]: continue
            if c not in uni(int(T[i + 1])): continue
            lim = C[i] - off * A[i]; r0 = sl * A[i]
            tp = lim + tp_r * r0 if mode == "rr" else None
            r, nxt = bi.sim(D, i + 1, 1, lim, r0, tp, valid_min // 15, hold_h * 4, (70 if mode == "rsi" else None), P0)
            out.append(dict(r, t=int(T[i + 1]), c=c, m="A", d=1, vr=0.0))
    return out

def ordersB(sl=1.5, k=1.0, tp_mode="open", valid_h=12, hold_h=24, short=True):
    out = []
    for c, D in M15.items():
        G = H1[c]; GA = G["A"]; nxt = 0; T = D["T"]
        for i in np.flatnonzero(T % 86400 == 0):
            if i < max(nxt, 900) or T[i] < P0["START"] or c not in uni(int(T[i])): continue
            kk = D["h1"].get(int(T[i]) - 3600)
            if kk is None or kk < 400: continue
            a = GA[kk]; vr = a / GA[kk - 336:kk].mean(); tr = int(G["reg"][kk])
            if vr < 1.1 or a / G["C"][kk] < 0.0134 or tr == 0 or int(G["btc"][kk]) != tr: continue
            if tr == -1 and (not short or (bi.funding_avg72(G, int(G["T"][kk])) or 0) <= 0): continue
            o = D["O"][i]; lim = o - tr * k * a; r0 = sl * a
            tp = lim + tr * k * a if tp_mode == "open" else lim + tr * r0          # 'rr' = TP sejauh SL (1:1)
            r, nxt = bi.sim(D, i, tr, lim, r0, tp, valid_h * 4, hold_h * 4, None, P0)
            out.append(dict(r, t=int(T[i]), c=c, m="B", d=tr, vr=float(vr)))
    return out

def portfolio(ords, cap=3, pend_max=3, rmax=50, rmaxA=None):
    ords = [o for o in ords if rank(o) < (rmaxA if (o["m"] == "A" and rmaxA) else rmax)]
    ev = sorted(ords, key=lambda o: (o["t"], rank(o)))
    pend, pos, sent, taken = [], [], [], []
    def settle(now):
        nonlocal pend, pos
        while True:
            cand = [(o["t_fill"], rank(o), j) for j, (_, o) in enumerate(pend) if o["filled"] and o["t_fill"] < now]
            if not cand: break
            tf, _, j = min(cand); o = pend[j][1]
            pos = [(e, c) for e, c in pos if e > tf]; pend = [p for p in pend if p[1] is not o and p[0] > tf]
            if len(pos) < cap:
                pos.append((o["t_exit"], o["c"])); taken.append(o)
                if len(pos) >= cap: pend = []
        pend = [p for p in pend if p[0] > now]; pos = [(e, c) for e, c in pos if e > now]
    for o in ev:
        settle(o["t"])
        if o["c"] in {c for _, c in pos} | {x["c"] for _, x in pend} or len(pend) >= pend_max or len(pos) >= cap: continue
        sent.append(o); pend.append(((o["t_fill"] + 1) if o["filled"] else o["t_exp"], o))
    settle(2_000_000_000)
    return sent, sorted(taken, key=lambda o: o["t_exit"])

def line(nm, s, t):
    i, q = bi.stats(t, s, b=bi.IS_END), bi.stats(t, s, a=bi.IS_END)
    yr = collections.defaultdict(float)
    for o in t: yr[time.gmtime(o["t"]).tm_year] += o["R"]
    hold = np.median([(o["t_exit"] - o["t_fill"]) / 3600 for o in t]) if t else 0
    return (f"{nm:<46} IS {i.get('avgR', 0):+.3f} rasio {i.get('rasio', 0):5.2f} | OOS n={q.get('n', 0):4d} avg {q.get('avgR', 0):+.3f} R/thn {q.get('totR_thn', 0):+5.1f} "
            f"DD {q.get('maxDD', 0):4.1f} rasio {q.get('rasio', 0):5.2f} win {q.get('win', 0)}% fill {q.get('fill', 0)}% hold {hold:.1f}j | "
            + " ".join(f"{y % 100}:{v:+.0f}" for y, v in sorted(yr.items()) if y >= 2024)), i.get("rasio", -9), q
