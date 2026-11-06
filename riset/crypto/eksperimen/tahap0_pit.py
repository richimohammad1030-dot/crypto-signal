"""TAHAP 0 versi daftar koin SESUAI MASANYA (point-in-time, termasuk koin delisting) + biaya realistis.
Logika daftar & mesin sama dengan riset/pit.py (swing); biaya sama dengan tahap0_semua_tahun.py.
Butuh data riset/unduh_pit.py + koin tambahan. Argumen: <repo> <data_dir>."""
import json, os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tahap0_semua_tahun as t0
rp = t0.rp
REPO, DATA = t0.REPO, t0.DATA_DIR
sys.path.insert(0, REPO); sys.path.insert(0, os.path.join(REPO, "riset"))
import signal_bot as sb
import pit
rp.sb = sb
pit._load(DATA)
allc = sorted({c for m in pit._SNAP for c in pit.ranked(DATA, m)[:70]} | set(sb.COINS))
now = time.time() * 1000
for c in allc:
    p = f"{DATA}/klines/{c}.json"
    if not os.path.exists(p): continue
    rows = [r[:5] for r in json.load(open(p)) if r[5] < now]
    if len(rows) < sb.K + 1350: continue
    rp.DATA[c] = sb.prep(rows)
    f = json.load(open(f"{DATA}/funding/{c}.json")) if os.path.exists(f"{DATA}/funding/{c}.json") else []
    h = json.load(open(f"{DATA}/funding_hl/{c}.json")) if os.path.exists(f"{DATA}/funding_hl/{c}.json") else []
    rp.FUND[c] = ([x[0] for x in f], [x[1] for x in f]); rp.FUND_HL[c] = ([x[0] for x in h], [x[1] for x in h])
print("koin dengan data:", len(rp.DATA))
first = {c: int(d["T"][sb.K + 1300]) for c, d in rp.DATA.items()}
uni = pit.universe_fn(DATA, lambda c, t: c in first and first[c] <= t)


class PitEngine(sb.Engine):             # salinan riset/pit.py
    def run(self, data_, since_ts, univ=None):
        times = sorted({t for d in data_.values() for t in d["T"] if t > since_ts})
        idx = {c: {t: i for i, t in enumerate(d["T"])} for c, d in data_.items()}
        for t in times:
            U = univ(t)
            order = U + [c for c in data_ if c not in U]
            for coin in order:
                if t in idx[coin]:
                    i = idx[coin][t]
                    if i >= max(sb.K, 1300): self.step_fill_exit(coin, i, data_[coin])
            if (t // 3600) % 24 in sb.CHECK_HOURS_UTC:
                for coin in order:
                    if t not in idx[coin]: continue
                    i = idx[coin][t]
                    if i < max(sb.K, 1300): continue
                    cs = self.s["coins"].setdefault(coin, {"pend": None, "pos": None})
                    if coin not in U and not cs.get("pos"):
                        if cs.get("pend"): cs["pend"] = None
                        continue
                    allow = lambda c, old: self.slots_used() - (1 if self.s["coins"][c].get("pend") else 0) < sb.MAX_SLOTS
                    self.step_check(coin, i, data_[coin], allow)


cur, rows = {}, []
def notify(kind, coin, **k):
    if kind == "fill":
        cur[coin] = dict(coin=coin, d=k["d"], t_fill=k["t"], e=k["entry"], r0=k["r0"], sl0=k["sl"], t_part=None, px_part=None)
    elif kind == "partial":
        cur[coin].update(t_part=k["t"], px_part=k["px"])
    elif kind == "exit":
        x = cur.pop(coin); x.update(t_exit=k["t"], ex=k["exit"], why=k["why"], R=k["R"]); rows.append(x)


eng = PitEngine({"coins": {}, "last_ts": 0, "replay": True}, rp.funding_fn, notify)
eng.run(rp.DATA, 0, uni)
df = t0.add_costs(pd.DataFrame(rows))
df.to_csv(f"{DATA}/tahap0_pit_trades.csv", index=False)
cur_coins = set(sb.COINS)
print(f"trade {len(df)} · di luar daftar kini {(~df.coin.isin(cur_coins)).sum()}")
pd.set_option("display.width", 200)
for col in ["R_KOTOR", "R_REAL", "R_KONS"]:
    t = t0.year_table(df, col)
    print(f"\n== PIT {col} per tahun tutup ==\n{t.round(2).to_string()}")
    print(f"semua {df[col].sum():.1f}R · DD {t0.maxdd(df[col].values):.1f}R")
