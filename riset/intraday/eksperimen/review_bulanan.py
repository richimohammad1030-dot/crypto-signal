"""Review bulanan intraday (PROSEDUR.md langkah 4): statistik juara per tahun, per modul, per cara keluar,
kesehatan edge 6 bulan terakhir, dan perbandingan jurnal live vs backtest.
Pemakaian: python3 review_bulanan.py <trades_intraday.csv> <repo_dir>"""
import collections, csv, glob, json, sys, time
import numpy as np
rows = list(csv.DictReader(open(sys.argv[1])))
for r in rows:
    for k in ("t", "t_fill", "t_exit", "d"): r[k] = int(float(r[k]))
    r["R"] = float(r["R"])
def st(v):
    R = np.array([x["R"] for x in v]) if v else np.array([0.0])
    return dict(n=len(v), win=round(float((R > 0).mean() * 100), 1) if v else 0, avgR=round(float(R.mean()), 4) if v else 0, totR=round(float(R.sum()), 1) if v else 0)
def by(fn):
    g = collections.defaultdict(list)
    for r in rows: g[fn(r)].append(r)
    return {k: st(v) for k, v in sorted(g.items())}
yr = lambda r: time.gmtime(r["t"]).tm_year
mod = lambda r: "A" if r["m"] == "A" else ("B-long" if r["d"] == 1 else "B-short")
print("PER TAHUN", json.dumps(by(yr)))
print("PER MODUL", json.dumps(by(mod)))
print("PER KELUAR", json.dumps(by(lambda r: r["why"])))
g = collections.defaultdict(list)
for r in rows: g[(mod(r), yr(r))].append(r)
for k in sorted(g): print("  ", k, st(g[k]))
last = max(r["t"] for r in rows)
six = last - 183 * 86400
r24 = [r for r in rows if r["t"] >= 1704067200]; r6 = [r for r in rows if r["t"] >= six]
print("2024-skrg", st(r24)); print("6 bln terakhir (mulai", time.strftime("%Y-%m-%d", time.gmtime(six)), ")", st(r6))
g6 = collections.defaultdict(list)
for r in r6: g6[mod(r)].append(r)
print("6 bln per modul", {k: st(v) for k, v in sorted(g6.items())})
gm = collections.defaultdict(list)
for r in r6: gm[time.strftime("%Y-%m", time.gmtime(r["t"]))].append(r)
print("6 bln per bulan", {k: st(v) for k, v in sorted(gm.items())})
# live vs backtest
live = []
for p in sorted(glob.glob(f"{sys.argv[2]}/jurnal/intraday-*.json")): live += json.load(open(p))
bt = {(r["c"], r["t_fill"]): r for r in rows}
t_live0 = min((x["t0"] for x in live), default=None)
print("LIVE", len(live), "trade")
for x in live:
    b = bt.get((x["sym"].replace("USDT", ""), x["t0"]))
    print("  ", x["waktu_tutup_wib"], x["sym"], x["modul"], "live R", x["R"], x["alasan"], "| backtest", (round(b["R"], 3), b["why"], b["t_exit"] == x["t1"]) if b else "TIDAK ADA")
if t_live0:
    seen = {(x["sym"].replace("USDT", ""), x["t0"]) for x in live}
    extra = [r for r in rows if r["t_fill"] >= 1793120400 and (r["c"], r["t_fill"]) not in seen]   # 27 Okt 2026 00:00 WIB
    print("Trade backtest sejak 27 Okt tanpa padanan live:", [(r["c"], r["m"], time.strftime("%m-%d %H:%M", time.gmtime(r["t_fill"] + 25200)), round(r["R"], 3), r["why"]) for r in extra])
