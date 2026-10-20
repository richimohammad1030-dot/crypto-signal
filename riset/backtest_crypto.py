"""Replay strategi Crypto Futures Trend memakai class Engine asli dari signal_bot.py.
Mencatat fitur pasar saat order (yang akhirnya terisi) dibuat, lalu hasil R saat posisi ditutup.
Argumen: <repo_dir> <data_dir> <out_csv>"""
import bisect, csv, json, os, sys, time
REPO, DATA, OUT = sys.argv[1:4]
sys.path.insert(0, REPO)
import signal_bot as sb

COINS = sb.COINS
data, fund, fund_hl, idx, reg = {}, {}, {}, {}, {}
for c in COINS:
    p = f"{DATA}/klines/{c}.json"
    rows = json.load(open(p)) if os.path.exists(p) else []
    rows = [r[:5] for r in rows if r[5] < time.time() * 1000]
    if len(rows) < sb.K + 1350:
        print("lewati (data kurang):", c); continue
    D = sb.prep(rows)
    data[c] = D
    idx[c] = {t: i for i, t in enumerate(D["T"])}
    reg[c] = [1 if (D["C"][i] > D["ES"][i] and D["EF"][i] > D["ES"][i]) else
              -1 if (D["C"][i] < D["ES"][i] and D["EF"][i] < D["ES"][i]) else 0 for i in range(len(D["T"]))]
    f = json.load(open(f"{DATA}/funding/{c}.json")) if os.path.exists(f"{DATA}/funding/{c}.json") else []
    fund[c] = ([x[0] for x in f], [x[1] for x in f])
    h = json.load(open(f"{DATA}/funding_hl/{c}.json")) if os.path.exists(f"{DATA}/funding_hl/{c}.json") else []
    fund_hl[c] = ([x[0] for x in h], [x[1] for x in h])
print("koin dengan data:", len(data))

def funding_fn(coin, t):
    """Rata-rata funding 72 jam terakhir. Arsip Binance (proxy), atau Hyperliquid (sumber bot live) untuk
    periode yang belum ada di arsip Binance. Filter short hanya memakai tandanya (> 0). None jika data kurang."""
    ts, rs = fund.get(coin, ([], []))
    a, b = bisect.bisect_right(ts, t - 72 * 3600), bisect.bisect_right(ts, t)
    if b - a >= 6:
        return sum(rs[a:b]) / (b - a)
    ts, rs = fund_hl.get(coin, ([], []))
    a, b = bisect.bisect_right(ts, t - 72 * 3600), bisect.bisect_right(ts, t)
    return sum(rs[a:b]) / (b - a) if b - a >= 24 else None

breadth_cache = {}
def breadth(t, d):
    if (t, d) not in breadth_cache:
        n = s = 0
        for c in data:
            i = idx[c].get(t)
            if i is not None and i >= 1300:
                n += 1; s += reg[c][i] == d
        breadth_cache[(t, d)] = s / n if n else 0.0
    return breadth_cache[(t, d)]

last_order, open_feat, trades = {}, {}, []
eng = None

def notify(kind, coin, **k):
    if kind == "order":
        D, i, d = data[coin], idx[coin][k["t"]], k["d"]
        C, A, EF, ES = D["C"][i], D["A"][i], D["EF"][i], D["ES"][i]
        bi = idx["BTC"].get(k["t"])
        last_order[coin] = dict(
            t_order=k["t"], d=d, rank=COINS.index(coin),
            trend=d * (EF - ES) / A,                        # jarak EMA100-EMA200 dalam ATR
            ext=d * (C - ES) / A,                           # jarak harga dari EMA200 dalam ATR
            dist=abs(k["entry"] - C) / A,                   # jarak entry dari harga dalam ATR
            slpct=abs(k["entry"] - k["sl"]) / k["entry"] * 100,
            mom20=d * (C / D["C"][i - 480] - 1) * 100,      # return 20 hari searah posisi
            slope=d * (ES - D["ES"][i - 120]) / A,          # kemiringan EMA200 5 hari
            btc=reg["BTC"][bi] * d if bi is not None else 0,   # 1 = BTC searah, -1 = berlawanan
            breadth=breadth(k["t"], d),                     # porsi koin lain yang trend-nya searah
            fund=(funding_fn(coin, k["t"]) or 0) * 1e4 if d == -1 else None)
    elif kind == "fill":
        f = dict(last_order.get(coin, {}))
        f["open_at_fill"] = eng.open_count() - 1
        f["wait_h"] = (k["t"] - f.get("t_order", k["t"])) / 3600
        open_feat[coin] = f
    elif kind == "exit":
        f = open_feat.pop(coin, {})
        trades.append(dict(coin=coin, t0=k["t0"], t1=k["t"], R=k["R"], **f))

state = {"coins": {}, "last_ts": 0, "replay": True}
eng = sb.Engine(state, funding_fn, notify)
t0 = time.time()
eng.run(data, 0)
print(f"selesai dalam {time.time() - t0:.0f} detik · trade selesai: {len(trades)} · masih terbuka: {eng.open_count()}")
keys = sorted({k for t in trades for k in t})
with open(OUT, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); w.writerows(trades)
