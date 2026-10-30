"""Matriks rasio TP:SL modul A x modul B (boleh berbeda). PIT, risiko 1%, statistik lengkap."""
import datetime as dt
from exp_run3 import *

def full(s, t, a=None):
    x = sorted([o for o in t if a is None or o["t"] >= a], key=lambda o: o["t_exit"])
    R = np.array([o["R"] for o in x]); W, L = R[R > 0], R[R <= 0]
    e = pk = 100.0; mdd = 0
    for r in R: e *= 1 + r / 100; pk = max(pk, e); mdd = max(mdd, 1 - e / pk)
    yrs = (x[-1]["t_exit"] - x[0]["t"]) / 31557600
    w = l = bw = bl = 0
    for r in R: w, l = (w + 1, 0) if r > 0 else (0, l + 1); bw, bl = max(bw, w), max(bl, l)
    mon = collections.defaultdict(float)
    for o in x: mon[dt.datetime.fromtimestamp(o["t_exit"], dt.timezone.utc).strftime("%Y-%m")] += o["R"]
    mv = np.array(list(mon.values()))
    c = np.cumsum(R); ddR = float((np.maximum.accumulate(np.concatenate([[0], c]))[1:] - c).max())
    per = {m: np.array([o["R"] for o in x if o["m"] == m]) for m in "AB"}
    return dict(n=len(R), bln=round(len(R) / yrs / 12), win=round(float((R > 0).mean() * 100), 1), avgW=round(float(W.mean()), 3),
                avgL=round(float(L.mean()), 3), rr=round(float(W.mean() / -L.mean()), 2), exp=round(float(R.mean()), 3),
                pf=round(float(W.sum() / -L.sum()), 2), Rthn=round(float(R.sum() / yrs), 1), ddR=round(ddR, 1), rasio=round(float(R.sum() / yrs) / max(ddR, 1), 2),
                cagr=round(((e / 100) ** (1 / yrs) - 1) * 100), dd=round(mdd * 100, 1), bw=bw, bl=bl,
                blnpos=round(float((mv > 0).mean() * 100)), blnmin=round(float(mv.min()), 1),
                winA=round(float((per["A"] > 0).mean() * 100), 1) if len(per["A"]) else 0, winB=round(float((per["B"] > 0).mean() * 100), 1) if len(per["B"]) else 0)

if __name__ == "__main__":
    _, J = portfolio(ordersA() + ordersB())
    f = lambda t: [(o["t_exit"], o["R"]) for o in t]
    A = {0.5: ordersA3(0.5, 3.0, 24), 1.0: ordersA3(1.0, 3.0, 4), 1.5: ordersA3(1.5, 3.0, 4), 2.0: ordersA3(2.0, 3.0, 4)}
    Bs = {0.5: ordersB3(0.5, 1.5, 1.0, 24), 0.67: ordersB(), 1.0: ordersB3(1.0, 1.5, 1.0, 24), 1.5: ordersB3(1.5, 1.5, 1.0, 24), 2.0: ordersB3(2.0, 1.5, 1.0, 24)}
    rows = []
    for ra, rb in itertools.product(A, Bs):
        s, t = portfolio(A[ra] + Bs[rb])
        i, q, al = full(s, t, None), full(s, t, bi.IS_END), None
        isr = bi.stats(t, s, b=bi.IS_END)["rasio"]
        p = sg.banding(f(J), f(t), mulai=bi.IS_END)["P_rasio_lebih_baik"]
        yr = collections.defaultdict(float)
        for o in t: yr[time.gmtime(o["t"]).tm_year] += o["R"]
        rows.append(dict(ra=ra, rb=rb, all=i, oos=q, isr=isr, p=p, yr=dict(yr)))
        print(f"A {ra}:1 + B {rb}:1 | IS rasio {isr:5.2f} | OOS rasio {q['rasio']:5.2f} win {q['win']}% (A {q['winA']} / B {q['winB']}) rr {q['rr']} exp {q['exp']:+.3f}R "
              f"PF {q['pf']} CAGR {q['cagr']}% DD {q['dd']}% | semua CAGR {i['cagr']}% DD {i['dd']}% | P {p:.2f}", flush=True)
    json.dump(rows, open("exp_run4.json", "w"), indent=1, default=float)
