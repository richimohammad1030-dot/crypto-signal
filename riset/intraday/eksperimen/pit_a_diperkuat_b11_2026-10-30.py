"""Permintaan pemilik 30 Okt 11:05: intraday 1:1 (bukan scalping), modul A peringkat 1-25 diperkuat + modul B 1:1. Risiko 1%.
PIT, IS 2020-2023 / OOS 2024-skrg."""
import bisect
from exp_pit import *

BTCH = H1["BTC"]; BIX = {int(t): k for k, t in enumerate(BTCH["T"])}
def btc_up(t):   # tren BTC dari candle H1 terakhir yang sudah close sebelum t
    k = BIX.get(t // 3600 * 3600 - 3600)
    return k is not None and int(BTCH["reg"][k]) == 1

def ordersA2(exitm="rsi", sl=3.0, hold_h=2, off=0.25, vmin=0.015, btc=False, dip="std"):
    out = []
    for c, D in M15.items():
        T, C, A, R2, R14, reg = D["T"], D["C"], D["A"], D["R2"], D["R14"], D["reg"]; nxt = 0
        sig = (R2 < 2) if dip == "dalam" else ((R2 < 5) | (R14 < 30))
        for i in np.flatnonzero((reg == 1) & sig & (A / C >= vmin)):
            if i < max(nxt, 900) or i + 1 >= len(T) or T[i] < P0["START"]: continue
            t1 = int(T[i + 1])
            if c not in uni(t1) or uni(t1).index(c) >= 25: continue
            if btc and not btc_up(t1): continue
            lim = C[i] - off * A[i]; r0 = sl * A[i]
            if exitm == "rsi":
                r, nxt = bi.sim(D, i + 1, 1, lim, r0, None, 8, hold_h * 4, 70, P0)
            else:
                r, nxt = bi.sim(D, i + 1, 1, lim, r0, lim + r0, 8, hold_h * 4, None, P0)
            out.append(dict(r, t=t1, c=c, m="A", d=1, vr=0.0))
    return out

def eq(t, a=None):
    x = [o for o in t if a is None or o["t"] >= a]
    if not x: return 0, 0
    e = pk = 100.0; mdd = 0
    for o in x: e *= 1 + o["R"] / 100; pk = max(pk, e); mdd = max(mdd, 1 - e / pk)
    yrs = (max(o["t_exit"] for o in x) - min(o["t"] for o in x)) / 31557600
    return round(((e / 100) ** (1 / yrs) - 1) * 100), round(mdd * 100)

if __name__ == "__main__":
    B11 = {nm: ordersB(sl=sl, k=1.0, tp_mode="rr", hold_h=h) for nm, sl, h in (("B 1:1 SL1.5 h24", 1.5, 24), ("B 1:1 SL1.0 h24", 1.0, 24), ("B 1:1 SL1.5 h12", 1.5, 12))}
    B0 = ordersB()
    print("== MODUL A diperkuat (A saja, peringkat 1-25, PIT) ==", flush=True)
    rows = []
    exits = [("rsi", 3.0, 2, 0.25)] + [("rr", sl, h, 0.5) for sl in (2.0, 3.0) for h in (4, 8, 24)]
    for (em, sl, h, off), btc, vmin, dip in itertools.product(exits, [False, True], [0.015, 0.02], ["std", "dalam"]):
        oa = ordersA2(em, sl, h, off, vmin, btc, dip)
        s, t = portfolio(oa)
        nm = f"A {'1:1 SL'+str(sl)+' h'+str(h) if em=='rr' else 'RSI h2'} btc={'Y' if btc else 'N'} atr>={vmin*100:.1f}% dip={dip}"
        L, r, q = line(nm, s, t); i = bi.stats(t, s, b=bi.IS_END)
        rows.append(dict(nm=nm, cfg=(em, sl, h, off, vmin, btc, dip), IS=i.get("rasio", -9), OOS=q.get("rasio", -9), ords=oa)); print(L, flush=True)
    print("\nTOP A menurut IS:"); [print(" ", r["nm"], "IS", r["IS"], "OOS", r["OOS"]) for r in sorted(rows, key=lambda r: -r["IS"])[:6]]
    print("TOP A menurut min(IS,OOS) (tahan di kedua periode):"); [print(" ", r["nm"], "IS", r["IS"], "OOS", r["OOS"]) for r in sorted(rows, key=lambda r: -min(r["IS"], r["OOS"]))[:6]]
    base = [r for r in rows if r["cfg"] == ("rsi", 3.0, 2, 0.25, 0.015, False, "std")][0]
    pick_is = max(rows, key=lambda r: r["IS"]); pick_rob = max(rows, key=lambda r: min(r["IS"], r["OOS"]))
    print("\n== GABUNGAN A (peringkat 1-25) + B, 3 posisi, risiko 1% ==", flush=True)
    _, J = portfolio(ordersA() + B0)
    f = lambda t: [(o["t_exit"], o["R"]) for o in t]
    cands = [("JUARA SEKARANG (A+B)", ordersA() + B0, {}), ("A 1-25 + B (kemarin)", base["ords"] + B0, {})]
    for bn, bo in B11.items():
        cands += [(f"A 1-25 (sekarang) + {bn}", base["ords"] + bo, {}),
                  (f"A diperkuat[IS] + {bn}", pick_is["ords"] + bo, {}),
                  (f"A diperkuat[tahan] + {bn}", pick_rob["ords"] + bo, {})]
    cands += [(f"A diperkuat[tahan] + B (TP open)", pick_rob["ords"] + B0, {})]
    print("A diperkuat[IS]   =", pick_is["nm"]); print("A diperkuat[tahan]=", pick_rob["nm"])
    for nm, o, kw in cands:
        s, t = portfolio(o, **kw); L, r, q = line(nm, s, t)
        c_all, d_all = eq(t); c_oos, d_oos = eq(t, bi.IS_END)
        p = sg.banding(f(J), f(t), mulai=bi.IS_END)["P_rasio_lebih_baik"]
        print(L, f"| 1%: CAGR {c_all}% DD {d_all}% · 2024+ CAGR {c_oos}% DD {d_oos}% · P>juara {p:.2f} · trade/bln {len(t)/((max(x['t_exit'] for x in t)-P0['START'])/2629800):.0f}", flush=True)
