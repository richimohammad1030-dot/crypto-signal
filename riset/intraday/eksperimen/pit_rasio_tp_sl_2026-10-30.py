"""Permintaan pemilik 30 Okt 11:40: uji rasio TP:SL 0,5 / 1 / 1,5 / 2 untuk bot intraday (modul A diperkuat + modul B).
Syarat: win rate tinggi + hasil R lumayan. PIT, IS 2020-2023 / OOS 2024-skrg, risiko 1%."""
from exp_run2 import *

def ordersA3(rr, sl=3.0, hold_h=4, off=0.5):
    out = []
    for c, D in M15.items():
        T, C, A, R2, R14, reg = D["T"], D["C"], D["A"], D["R2"], D["R14"], D["reg"]; nxt = 0
        for i in np.flatnonzero((reg == 1) & ((R2 < 5) | (R14 < 30)) & (A / C >= 0.015)):
            if i < max(nxt, 900) or i + 1 >= len(T) or T[i] < P0["START"]: continue
            t1 = int(T[i + 1])
            if c not in uni(t1) or uni(t1).index(c) >= 25 or not btc_up(t1): continue
            lim = C[i] - off * A[i]; r0 = sl * A[i]
            r, nxt = bi.sim(D, i + 1, 1, lim, r0, lim + rr * r0, 8, hold_h * 4, None, P0)
            out.append(dict(r, t=t1, c=c, m="A", d=1, vr=0.0))
    return out

def ordersB3(rr, sl=1.5, k=1.0, hold_h=24):
    out = []
    for c, D in M15.items():
        G = H1[c]; GA = G["A"]; nxt = 0; T = D["T"]
        for i in np.flatnonzero(T % 86400 == 0):
            if i < max(nxt, 900) or T[i] < P0["START"] or c not in uni(int(T[i])): continue
            kk = D["h1"].get(int(T[i]) - 3600)
            if kk is None or kk < 400: continue
            a = GA[kk]; vr = a / GA[kk - 336:kk].mean(); tr = int(G["reg"][kk])
            if vr < 1.1 or a / G["C"][kk] < 0.0134 or tr == 0 or int(G["btc"][kk]) != tr: continue
            if tr == -1 and (bi.funding_avg72(G, int(G["T"][kk])) or 0) <= 0: continue
            o = D["O"][i]; lim = o - tr * k * a; r0 = sl * a
            r, nxt = bi.sim(D, i, tr, lim, r0, lim + tr * rr * r0, 48, hold_h * 4, None, P0)
            out.append(dict(r, t=int(T[i]), c=c, m="B", d=tr, vr=float(vr)))
    return out

def win(t, a=None):
    x = [o["R"] for o in t if a is None or o["t"] >= a]
    return round(float(np.mean(np.array(x) > 0) * 100), 1) if x else 0

if __name__ == "__main__":
    RRS = [0.5, 1.0, 1.5, 2.0]
    _, J = portfolio(ordersA() + ordersB())
    f = lambda t: [(o["t_exit"], o["R"]) for o in t]
    print("== MODUL A diperkuat per rasio TP:SL (A saja) ==", flush=True)
    bestA = {}
    for rr in RRS:
        for sl, h in itertools.product([2.0, 3.0], [4, 8, 24]):
            o = ordersA3(rr, sl, h); s, t = portfolio(o)
            L, r, q = line(f"A TP {rr}x SL {sl}ATR hold {h}j", s, t); i = bi.stats(t, s, b=bi.IS_END)
            print(L, flush=True)
            sc = min(i.get("rasio", -9), q.get("rasio", -9))
            if rr not in bestA or sc > bestA[rr][0]: bestA[rr] = (sc, f"SL {sl} ATR hold {h}j", o)
    print("\n== MODUL B per rasio TP:SL (B saja) ==", flush=True)
    bestB = {}
    for rr in RRS:
        for sl, h in itertools.product([1.0, 1.5], [12, 24]):
            o = ordersB3(rr, sl, 1.0, h); s, t = portfolio(o)
            L, r, q = line(f"B TP {rr}x SL {sl}ATR hold {h}j", s, t); i = bi.stats(t, s, b=bi.IS_END)
            print(L, flush=True)
            sc = min(i.get("rasio", -9), q.get("rasio", -9))
            if rr not in bestB or sc > bestB[rr][0]: bestB[rr] = (sc, f"SL {sl} ATR hold {h}j", o)
    B0 = ordersB()
    print("\n== GABUNGAN per rasio (A & B rasio sama, varian terbaik di kedua periode), 3 posisi, risiko 1% ==", flush=True)
    combos = [(f"RR {rr}: A[{bestA[rr][1]}] + B[{bestB[rr][1]}]", bestA[rr][2] + bestB[rr][2]) for rr in RRS]
    combos += [(f"A RR {rr} [{bestA[rr][1]}] + B tetap (TP open)", bestA[rr][2] + B0) for rr in RRS]
    for nm, o in combos:
        s, t = portfolio(o); L, r, q = line(nm, s, t)
        c_all, d_all = eq(t); c_oos, d_oos = eq(t, bi.IS_END)
        p = sg.banding(f(J), f(t), mulai=bi.IS_END)["P_rasio_lebih_baik"]
        print(L, f"| win OOS {win(t, bi.IS_END)}% · 1%: CAGR {c_all}% DD {d_all}% · 2024+ CAGR {c_oos}% DD {d_oos}% · P>juara {p:.2f} · trade/bln {len(t)/((max(x['t_exit'] for x in t)-P0['START'])/2629800):.0f}", flush=True)
