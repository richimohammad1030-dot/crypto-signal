"""Daftar koin POINT-IN-TIME (sesuai masanya) untuk mengukur bias koin selamat (survivorship bias).
Aturan sama dengan daftar bot: 50 koin teratas CoinMarketCap tanpa stablecoin/token emas/token bungkus, yang punya pair
USDT spot di Binance, dari snapshot CMC tanggal 1 tiap bulan. Koin yang sudah delisting/ambruk (LUNA, FTT, dst.) ikut.
Data: <data>/pit/cmc_snapshots.json & binance_spot_usdt.json (riset/unduh_pit.py), candle dari unduh_crypto/unduh_intraday.

Uji swing   : python riset/pit.py swing <repo> <data>      -> juara dengan daftar tetap vs daftar sesuai masanya
Modul       : universe(month) -> list koin urut peringkat; month_of(t) -> 'YYYY-MM'."""
import json, os, sys, time

ALIAS = {"MIOTA": "IOTA", "RNDR": "RENDER", "BCHABC": "BCH", "BCHSV": "BSV"}
BAD_TAGS = {"stablecoin", "tokenized-gold", "wrapped-tokens", "liquid-staking-derivatives", "tokenized-stock",
            "asset-backed-stablecoin", "fiat-stablecoin", "algorithmic-stablecoin", "usd-stablecoin", "eur-stablecoin",
            "liquid-staking-tokens", "restaking", "tokenized-commodities"}
BAD_SYM = {"WBTC", "WETH", "STETH", "WSTETH", "WEETH", "CBBTC", "RETH", "WBETH", "BETH", "BTCB", "BSC-USD", "USDE", "SUSDE", "BUIDL",
           "USD1", "PAXG", "XAUT", "FDUSD", "TUSD", "USDP", "BUSD", "DAI", "USDD", "PYUSD", "FRAX", "LUSD", "EURC", "USDC", "USDT", "USDS",
           "SUSDS", "RLUSD", "USDTB", "USDF", "USDG", "USYC", "BFUSD", "USD0", "EURT", "GUSD", "HUSD", "PAX", "WTRX", "WBNB", "JITOSOL",
           "MSOL", "BNSOL", "LBTC", "SOLVBTC", "CLBTC", "FBTC", "EZETH", "RSETH", "METH", "OUSG", "USTB"}
_SNAP = _BN = None
TOP = 50

def _load(data):
    global _SNAP, _BN
    if _SNAP is None:
        _SNAP = json.load(open(f"{data}/pit/cmc_snapshots.json"))
        _BN = set(json.load(open(f"{data}/pit/binance_spot_usdt.json")))

def month_of(t):
    return time.strftime("%Y-%m", time.gmtime(t))

def ranked(data, month):
    """Semua koin yang lolos aturan di bulan itu, urut peringkat CMC (belum dibatasi 50 / ketersediaan data)."""
    _load(data)
    out = []
    for r in _SNAP.get(month, []):
        s = ALIAS.get(r["sym"], r["sym"])
        if s in BAD_SYM or BAD_TAGS & set(r["tags"]) or s not in _BN or s in out: continue
        out.append(s)
    return out

def universe_fn(data, has_data):
    """has_data(coin, t) -> bool. Return fungsi uni(t) -> list 50 koin (urut peringkat) yang punya data di awal bulan."""
    cache = {}
    def uni(t):
        m = month_of(t)
        if m not in cache:
            t0 = time.mktime(time.strptime(m + "-01", "%Y-%m-%d")) - time.timezone
            cache[m] = [c for c in ranked(data, m) if has_data(c, t0)][:TOP]
        return cache[m]
    return uni


# ---------------------------------------------------------------------------------------------- uji swing
def swing(repo, data):
    sys.path.insert(0, repo); sys.path.insert(0, os.path.join(repo, "riset"))
    import bisect
    import signal_bot as sb
    _load(data)
    allc = sorted({c for m in _SNAP for c in ranked(data, m)[:70]} | set(sb.COINS))
    D, fund, fund_hl = {}, {}, {}
    now = time.time() * 1000
    for c in allc:
        p = f"{data}/klines/{c}.json"
        if not os.path.exists(p): continue
        rows = [r[:5] for r in json.load(open(p)) if r[5] < now]
        if len(rows) < sb.K + 1350: continue
        D[c] = sb.prep(rows)
        f = json.load(open(f"{data}/funding/{c}.json")) if os.path.exists(f"{data}/funding/{c}.json") else []
        h = json.load(open(f"{data}/funding_hl/{c}.json")) if os.path.exists(f"{data}/funding_hl/{c}.json") else []
        fund[c] = ([x[0] for x in f], [x[1] for x in f]); fund_hl[c] = ([x[0] for x in h], [x[1] for x in h])
    def funding_fn(coin, t):
        for (ts, rs), need in ((fund.get(coin, ([], [])), 6), (fund_hl.get(coin, ([], [])), 24)):
            a, b = bisect.bisect_right(ts, t - 72 * 3600), bisect.bisect_right(ts, t)
            if b - a >= need: return sum(rs[a:b]) / (b - a)
        return None
    first = {c: int(d["T"][sb.K + 1300]) for c, d in D.items()}       # koin baru dianggap "ada" setelah pemanasan indikator
    uni = universe_fn(data, lambda c, t: c in first and first[c] <= t)

    class PitEngine(sb.Engine):
        def run(self, data_, since_ts, univ=None):
            times = sorted({t for d in data_.values() for t in d["T"] if t > since_ts})
            idx = {c: {t: i for i, t in enumerate(d["T"])} for c, d in data_.items()}
            for t in times:
                U = univ(t) if univ else [c for c in sb.COINS if c in data_]
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
                            if cs.get("pend"): cs["pend"] = None          # keluar dari 50 besar: order dibatalkan
                            continue
                        allow = lambda c, old: self.slots_used() - (1 if self.s["coins"][c].get("pend") else 0) < sb.MAX_SLOTS
                        self.step_check(coin, i, data_[coin], allow)
            self.s["last_ts"] = times[-1]

    def run(univ, coins):
        tr = []
        def notify(kind, coin, **k):
            if kind == "exit": tr.append(dict(c=coin, d=k["d"], t0=k["t0"], t1=k["t"], R=k["R"]))
        eng = PitEngine({"coins": {}, "last_ts": 0, "replay": True}, funding_fn, notify)
        eng.run({c: D[c] for c in coins if c in D}, 0, univ)
        return tr
    tetap = run(None, sb.COINS)
    pit = run(uni, list(D))
    return tetap, pit, uni, D

def ringkas(tr, a=None, b=None):
    import numpy as np
    x = [o for o in tr if (a is None or o["t0"] >= a) and (b is None or o["t0"] < b)]
    if not x: return "n=0"
    R = np.array([o["R"] for o in sorted(x, key=lambda o: o["t1"])]); c = np.cumsum(R)
    dd = float((np.maximum.accumulate(np.concatenate([[0], c]))[1:] - c).max())
    yrs = ((b or max(o["t1"] for o in x)) - (a or min(o["t0"] for o in x))) / 31557600
    return f"n={len(R):4d} win {(R > 0).mean() * 100:4.1f}% avg {R.mean():+.3f}R R/thn {R.sum() / yrs:+6.1f} DD {dd:5.1f}R rasio {R.sum() / yrs / max(dd, 1):5.2f}"

if __name__ == "__main__" and sys.argv[1] == "swing":
    import collections
    tetap, pit, uni, D = swing(sys.argv[2], sys.argv[3])
    IS = 1704067200
    print("SWING · daftar TETAP (koin hari ini) vs SESUAI MASANYA (point-in-time)")
    for nm, tr in (("tetap", tetap), ("sesuai masanya", pit)):
        print(f"  {nm:<15} semua   {ringkas(tr)}")
        print(f"  {'':<15} 2020-23 {ringkas(tr, b=IS)}")
        print(f"  {'':<15} 2024-   {ringkas(tr, a=IS)}")
        yr = collections.defaultdict(float)
        for o in tr: yr[time.gmtime(o["t0"]).tm_year] += o["R"]
        print(f"  {'':<15} per tahun " + " ".join(f"{y}:{v:+.0f}" for y, v in sorted(yr.items())))
    cur = set(__import__("signal_bot").COINS)
    mati = [o for o in pit if o["c"] not in cur]
    import numpy as np
    print(f"  trade di koin yang TIDAK ada di daftar sekarang: {len(mati)} · {sum(o['R'] for o in mati):+.1f}R · avg {np.mean([o['R'] for o in mati]):+.3f}R")
    by = collections.defaultdict(float)
    for o in mati: by[o["c"]] += o["R"]
    print("  koin tersebut terburuk:", ", ".join(f"{c} {v:+.1f}" for c, v in sorted(by.items(), key=lambda z: z[1])[:8]))
    print("  koin tersebut terbaik :", ", ".join(f"{c} {v:+.1f}" for c, v in sorted(by.items(), key=lambda z: -z[1])[:8]))
    import csv
    for nm, tr in (("tetap", tetap), ("pit", pit)):
        with open(f"/tmp/claude-0/-home-claude/563667fa-fea2-5514-8f49-dd552a9116a1/scratchpad/swing_{nm}.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["c", "d", "t0", "t1", "R"]); w.writeheader(); w.writerows(tr)
