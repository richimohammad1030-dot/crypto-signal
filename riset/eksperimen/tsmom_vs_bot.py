"""Bandingkan bot "Crypto Futures Trend" (juara) dengan TSMOM long-only (Han, Kang & Ryu 2024)
di DATA YANG SAMA: candle H1 spot Binance + funding futures Binance (fallback Hyperliquid) dari unduh_crypto.py.

Keduanya diubah menjadi return HARIAN (mark-to-market di close harian UTC) agar bisa dibandingkan:
- Bot  : replay Engine asli. Setiap trade memakai risiko RISK (default 0,67% ekuitas). Return harian =
         RISK x perubahan R posisi terbuka (close ke close), dikurangi fee masuk/keluar dan funding.
- TSMOM: keranjang equal-weight (rebalance harian). Sinyal = return 28 hari keranjang; long 1 hari ke depan
         jika persentilnya masuk sepertiga teratas dari return 28-harian historis yang tidak tumpang tindih
         (minimal 12 jendela). Selain itu flat. Fee atas turnover + funding yang dibayar posisi long.

Argumen: <repo_dir> <data_dir> <out_dir> [RISK=0.0067] [FEE=0.0006]
FEE = biaya per sisi per notional (taker 0,05% + slippage 0,01%)."""
import bisect, csv, json, math, os, sys, time
import numpy as np, pandas as pd

REPO, DATA, OUT = sys.argv[1:4]
RISK = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0067
FEE = float(sys.argv[5]) if len(sys.argv) > 5 else 0.0006
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, REPO)
import signal_bot as sb

NOW = time.time()
DAY = 86400

# ------------------------------------------------------------------ data
kl, fund_b, fund_h = {}, {}, {}
for c in sb.COINS:
    p = f"{DATA}/klines/{c}.json"
    if not os.path.exists(p):
        continue
    rows = [r for r in json.load(open(p)) if r[5] < NOW * 1000]
    if rows:
        kl[c] = rows
    f = f"{DATA}/funding/{c}.json"
    fund_b[c] = json.load(open(f)) if os.path.exists(f) else []
    h = f"{DATA}/funding_hl/{c}.json"
    fund_h[c] = json.load(open(h)) if os.path.exists(h) else []

# close harian UTC = close candle H1 terakhir di hari itu (hanya hari yang lengkap 24 candle)
closes = {}
for c, rows in kl.items():
    df = pd.DataFrame([r[:5] for r in rows], columns=["t", "o", "h", "l", "c"])
    df["day"] = df["t"] // DAY
    g = df.groupby("day").agg(c=("c", "last"), n=("c", "size"))
    closes[c] = g.loc[g["n"] == 24, "c"]
C = pd.DataFrame(closes).sort_index()
last_full_day = int(NOW // DAY) - 1
C = C[C.index <= last_full_day]
R = C.pct_change(fill_method=None)            # return harian per koin (NaN sebelum listing)

def daily_funding(c):
    """Total funding per hari UTC (jumlah rate yang diselesaikan di hari itu). Arsip Binance;
    Hyperliquid (per jam) hanya untuk hari setelah arsip Binance terakhir."""
    s = {}
    b = fund_b.get(c, [])
    for t, r in b:
        s[t // DAY] = s.get(t // DAY, 0.0) + r
    last_b = b[-1][0] // DAY if b else -1
    for t, r in fund_h.get(c, []):
        if t // DAY > last_b:
            s[t // DAY] = s.get(t // DAY, 0.0) + r
    return pd.Series(s, dtype=float)
F = pd.DataFrame({c: daily_funding(c) for c in C.columns}).reindex(C.index).fillna(0.0)

# ------------------------------------------------------------------ bot (replay Engine asli)
data = {}
for c in sb.COINS:
    if c not in kl:
        continue
    rows = [r[:5] for r in kl[c]]
    if len(rows) < sb.K + 1350:
        continue
    data[c] = sb.prep(rows)

def funding_fn(coin, t):            # sama dengan backtest_crypto.py
    ts = [x[0] for x in fund_b.get(coin, [])]; rs = [x[1] for x in fund_b.get(coin, [])]
    a, b = bisect.bisect_right(ts, t - 72 * 3600), bisect.bisect_right(ts, t)
    if b - a >= 6:
        return sum(rs[a:b]) / (b - a)
    ts = [x[0] for x in fund_h.get(coin, [])]; rs = [x[1] for x in fund_h.get(coin, [])]
    a, b = bisect.bisect_right(ts, t - 72 * 3600), bisect.bisect_right(ts, t)
    return sum(rs[a:b]) / (b - a) if b - a >= 24 else None

state = {"coins": {}, "last_ts": 0, "replay": True}
eng = sb.Engine(state, funding_fn, lambda *a, **k: None)
eng.run(data, 0)
hist = state["hist"]                                      # [coin, d, t0, t1, entry, exit, R]
open_pos = [(c, s["pos"]) for c, s in state["coins"].items() if s.get("pos")]
print(f"bot: {len(hist)} trade selesai, {len(open_pos)} masih terbuka, total R kotor {sum(h[6] for h in hist):.1f}")

days = C.index
dpos = {d: i for i, d in enumerate(days)}
bot_gross = np.zeros(len(days)); bot_fee = np.zeros(len(days)); bot_fund = np.zeros(len(days))
bot_expo = np.zeros(len(days))     # notional terbuka / ekuitas (perkiraan)
trade_rows = []

def fund_events(coin):
    """Event funding (t_s, rate): arsip Binance, lalu Hyperliquid per jam setelah arsip terakhir."""
    b = fund_b.get(coin, [])
    last_b = b[-1][0] if b else -1
    return [tuple(x) for x in b] + [tuple(x) for x in fund_h.get(coin, []) if x[0] > last_b]
FE = {c: fund_events(c) for c in C.columns}
FE_T = {c: [x[0] for x in v] for c, v in FE.items()}

def add_trade(coin, d, t0, t1, e, ex, r0):
    """ΔR harian (mark-to-market close harian) untuk satu trade; t1=None = masih terbuka."""
    if not r0 or coin not in C:
        return
    lev = e / r0                                          # notional per 1R = entry / jarak SL
    d0, d1 = t0 // DAY, (t1 // DAY if t1 else days[-1])
    # funding persis: setiap settlement di antara masuk dan keluar
    a = bisect.bisect_right(FE_T[coin], t0)
    b = bisect.bisect_right(FE_T[coin], t1 if t1 else (days[-1] + 1) * DAY - 1)
    for ts, rate in FE[coin][a:b]:
        if ts // DAY in dpos:
            bot_fund[dpos[ts // DAY]] -= RISK * d * rate * lev
    prevR = 0.0
    for day in range(d0, d1 + 1):
        if day not in dpos:
            continue
        k = dpos[day]
        if t1 and day == d1:
            nowR = (ex - e) * d / r0
        else:
            px = C.at[day, coin]
            if not np.isfinite(px):
                continue
            nowR = (px - e) * d / r0
        bot_gross[k] += RISK * (nowR - prevR)
        bot_expo[k] += RISK * lev
        prevR = nowR
    if d0 in dpos:
        bot_fee[dpos[d0]] -= RISK * FEE * lev
    if t1 and d1 in dpos:
        bot_fee[dpos[d1]] -= RISK * FEE * lev
    trade_rows.append([coin, d, t0, t1, e, ex, r0])

for coin, d, t0, t1, e, ex, Rr in hist:
    r0 = (ex - e) * d / Rr if abs(Rr) > 1e-9 else None
    if r0 is None or r0 <= 0:
        continue
    add_trade(coin, d, t0, t1, e, ex, r0)
for coin, pos in open_pos:
    d, e, sl, t0 = pos[:4]
    r0 = pos[4] if len(pos) > 4 else abs(e - sl)
    add_trade(coin, d, t0, None, e, None, r0)

bot = pd.DataFrame({"gross": bot_gross, "fee": bot_fee, "fund": bot_fund}, index=days)
bot["net"] = bot["gross"] + bot["fee"] + bot["fund"]

# ------------------------------------------------------------------ TSMOM
def tsmom(members, label, J=28, H=1, thr=2 / 3, minwin=12, fee=FEE):
    rr = R[members]
    w_avail = rr.notna().astype(float)
    w = w_avail.div(w_avail.sum(axis=1), axis=0)          # EW di antara koin yang sudah ada
    w_prev = w.shift(1)
    basket = (w_prev * rr.fillna(0)).sum(axis=1)           # rebalance harian ke EW
    basket[w_prev.sum(axis=1) == 0] = np.nan
    idx = (1 + basket.fillna(0)).cumprod().values
    kstart = dpos[basket.first_valid_index()] - 1          # indeks level awal keranjang
    sig = pd.Series(0.0, index=days); elig = pd.Series(False, index=days)
    for k in range(len(days)):
        nwin = (k - kstart) // J - 1                       # jendela 28 hari historis yang tidak tumpang tindih
        if nwin < minwin:
            continue
        cur = idx[k] / idx[k - J] - 1
        past = np.array([idx[k - J * m] / idx[k - J * (m + 1)] - 1 for m in range(1, nwin + 1)])
        pct = np.mean(past < cur)                          # persentil return 28 hari sekarang
        sig.iloc[k] = 1.0 if pct >= thr else 0.0
        elig.iloc[k] = True
    pos = sig.shift(H).fillna(0)                           # sinyal close hari t -> posisi hari t+1
    gross = pos * basket.fillna(0)
    # turnover: masuk/keluar keranjang + rebalance drift ke EW saat posisi long
    drift = (w_prev * (1 + rr.fillna(0))).div((1 + basket.fillna(0)), axis=0)
    reb = (w - drift).abs().sum(axis=1).fillna(0)
    turn = (pos - pos.shift(1).fillna(0)).abs() + pos * pos.shift(-1).fillna(0) * reb
    feec = -fee * turn
    fundc = -pos * (w_prev * F[members]).sum(axis=1)
    out = pd.DataFrame({"gross": gross, "fee": feec, "fund": fundc, "pos": pos, "basket": basket,
                        "elig": elig.shift(1).fillna(False)})
    out["net"] = out["gross"] + out["fee"] + out["fund"]
    out.attrs["label"] = label
    return out

top10 = [c for c in sb.COINS if c in C.columns][:10]
allc = [c for c in sb.COINS if c in C.columns]
variants = {
    "TSMOM BTC": tsmom(["BTC"], "TSMOM BTC"),
    "TSMOM Top-10 EW": tsmom(top10, "TSMOM Top-10 EW"),
    "TSMOM Semua koin EW": tsmom(allc, "TSMOM Semua koin EW"),
}

# ------------------------------------------------------------------ metrik
def metrics(r):
    r = r.dropna()
    if len(r) < 30:
        return {}
    eq = (1 + r).cumprod()
    yrs = len(r) / 365
    cagr = eq.iloc[-1] ** (1 / yrs) - 1
    dd = (eq / eq.cummax() - 1).min()
    sh = r.mean() / r.std() * math.sqrt(365) if r.std() > 0 else 0
    down = r[r < 0].std()
    so = r.mean() / down * math.sqrt(365) if down > 0 else 0
    return {"CAGR %": cagr * 100, "MaxDD %": dd * 100, "Sharpe": sh, "Sortino": so,
            "Calmar": cagr / abs(dd) if dd < 0 else float("nan"), "Total %": (eq.iloc[-1] - 1) * 100}

first_ts = max(v["elig"].idxmax() for v in variants.values())   # hari pertama semua TSMOM bisa aktif
common = days[days >= first_ts]
periods = {"Semua (" + pd.to_datetime(common[0] * DAY, unit="s").strftime("%Y-%m-%d") + " s.d. " +
           pd.to_datetime(common[-1] * DAY, unit="s").strftime("%Y-%m-%d") + ")": common,
           "2020-2023": common[common < 19723], "2024-skrg": common[common >= 19723]}
series = {"Bot (juara)": bot}
series.update(variants)
for nm, src in (("Buy&hold BTC", "TSMOM BTC"), ("Buy&hold Top-10 EW", "TSMOM Top-10 EW")):
    b = variants[src]["basket"].fillna(0)
    series[nm] = pd.DataFrame({"gross": b, "fee": 0.0, "fund": 0.0, "net": b})

rows = []
for pname, rng in periods.items():
    for name, df in series.items():
        for kind in ("gross", "net"):
            m = metrics(df.loc[rng, kind] if kind == "gross" else df.loc[rng, "net"])
            rows.append({"Periode": pname, "Strategi": name, "Basis": kind, **{k: round(v, 2) for k, v in m.items()}})
summary = pd.DataFrame(rows)
summary.to_csv(f"{OUT}/ringkasan.csv", index=False)

# per tahun (net)
yr = pd.to_datetime(common * DAY, unit="s").year
peryear = []
for name, df in series.items():
    r = df.loc[common, "net"]
    for y in sorted(set(yr)):
        rr = r[yr == y]
        eq = (1 + rr).cumprod()
        peryear.append({"Strategi": name, "Tahun": y, "Return %": round((eq.iloc[-1] - 1) * 100, 1),
                        "MaxDD %": round(((eq / eq.cummax()) - 1).min() * 100, 1)})
pd.DataFrame(peryear).to_csv(f"{OUT}/per_tahun.csv", index=False)

# kurva ekuitas + korelasi
eqs = pd.DataFrame({name: (1 + df.loc[common, "net"]).cumprod() for name, df in series.items()})
eqs.index = pd.to_datetime(common * DAY, unit="s").strftime("%Y-%m-%d")
eqs.to_csv(f"{OUT}/ekuitas_net.csv")
corr = pd.DataFrame({name: df.loc[common, "net"] for name, df in series.items()}).corr().round(2)
corr.to_csv(f"{OUT}/korelasi.csv")

# info tambahan
info = {"risk_per_trade": RISK, "fee_per_sisi": FEE, "top10": top10, "jumlah_koin_semua": len(allc),
        "hari_long_pct": {k: round(v.loc[common, "pos"].mean() * 100, 1) for k, v in variants.items()},
        "jumlah_masuk": {k: int((v.loc[common, "pos"].diff() == 1).sum()) for k, v in variants.items()},
        "bot_eksposur_notional": {"rata2": round(float(bot_expo[dpos[common[0]]:].mean()), 2),
                                  "maks": round(float(bot_expo[dpos[common[0]]:].max()), 2)},
        "hari_long_per_tahun": {k: v.loc[common, "pos"].groupby(pd.to_datetime(common * DAY, unit="s").year).mean().round(2).to_dict() for k, v in variants.items()},
        "bot_komponen_pct_per_tahun": {k: round(bot.loc[common, k].sum() / (len(common) / 365) * 100, 2) for k in ("gross", "fee", "fund")},
        "tsmom_top10_komponen_pct_per_tahun": {k: round(variants["TSMOM Top-10 EW"].loc[common, k].sum() / (len(common) / 365) * 100, 2) for k in ("gross", "fee", "fund")}}
json.dump(info, open(f"{OUT}/info.json", "w"), indent=1)

pd.set_option("display.width", 200); pd.set_option("display.max_rows", 200)
print(summary.to_string(index=False))
print(pd.DataFrame(peryear).pivot(index="Tahun", columns="Strategi", values="Return %").to_string())
print(corr.to_string())
print(json.dumps(info, indent=1))
