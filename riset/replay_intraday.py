"""Uji kesetaraan: mesin bot live (intraday_bot.Engine) diputar ulang di data historis lalu dibandingkan dengan
backtest_intraday.py trade per trade. Wajib dijalankan setiap kali mesin bot atau juara diubah.
Pemakaian: python riset/replay_intraday.py <repo_dir> <data_dir> [mulai_YYYY-MM-DD]"""
import calendar, collections, sys, time
REPO, DATA = sys.argv[1:3]
sys.path.insert(0, REPO); sys.path.insert(0, REPO + "/riset")
import numpy as np
import backtest_intraday as bi, intraday_bot as ib, signal_bot as sb

start = calendar.timegm(time.strptime(sys.argv[3], "%Y-%m-%d")) if len(sys.argv) > 3 else bi.PARAM["START"]
P = dict(bi.PARAM, START=start)
H1, M15 = bi.load(DATA, sb.COINS)
_, sent, ref = bi.run(REPO, DATA, {"START": start})

data = {}
for c, D in M15.items():
    D["ix"] = {int(t): k for k, t in enumerate(D["T"])}
    D["h1"] = ib.h1_info_fn(H1[c], H1["BTC"], lambda t1, D=D: float(D["O"][D["ix"][t1]]) if t1 in D["ix"] else None)
    data[c] = D
eng = ib.Engine({}, P, sb.COINS, lambda *a: None,
                funding_fn=lambda c, t: bi.funding_avg72(H1[c], t),
                cost_fn=lambda c, t0, t1, d: bi.funding_cost(M15[c], t0, t1, d), btc_fn=bi.btc_regime_fn(H1))
# candle sebelum START tidak menghasilkan order (backtest: T[i] >= START untuk sinyal)
times = sorted({int(t) for D in data.values() for t in D["T"] if t >= start})
t0 = time.time()
for k, t in enumerate(times):
    eng.step(t, data)
print(f"replay {len(times)} candle dalam {time.time() - t0:.0f} detik")
live = [dict(c=h[0], m=h[1], d=h[2], t_fill=h[3], t_exit=h[4], R=h[7], why=h[8]) for h in eng.s["hist"]]
key = lambda o: (o["c"], o["t_fill"])
A = {key(o): o for o in ref}; B = {key(o): o for o in live}
both = A.keys() & B.keys()
diffR = [abs(A[k]["R"] - B[k]["R"]) for k in both]
print(f"backtest {len(A)} trade · bot {len(B)} trade · sama {len(both)} · hanya backtest {len(A.keys() - B.keys())} · hanya bot {len(B.keys() - A.keys())}")
print(f"selisih R maks {max(diffR) if diffR else 0:.6f} · total R backtest {sum(o['R'] for o in ref):.2f} · bot {sum(o['R'] for o in live):.2f}")
for k in sorted(A.keys() ^ B.keys())[:10]:
    print("  beda:", k, "backtest" if k in A else "bot", (A.get(k) or B.get(k)).get("why"))
