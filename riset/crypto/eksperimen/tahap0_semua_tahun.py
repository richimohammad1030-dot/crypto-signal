"""TAHAP 0 · Verifikasi "untung di semua tahun" dengan eksekusi realistis (6 Nov 2026).

Backtest swing lain di repo memakai R KOTOR (sama dengan perhitungan bot). Skrip ini menambah biaya per trade:
- Entry  : order STOP (breakout) -> taker + slippage. Gap sudah ditangani mesin (fill di max(entry, open)).
- TP 25% di 1R : limit -> maker, tanpa slippage.
- Keluar sisa  : SL (stop market) / cut-loss stagnan (market di close) -> taker + slippage.
- Funding      : setiap settlement selama posisi terbuka, rate aktual (arsip Binance; setelah arsip habis -> Hyperliquid
                 per jam). Long bayar bila rate > 0, short menerima. Nilai posisi = qty x harga close jam settlement.
Semua biaya dikonversi ke R: biaya_harga / r0 (qty = 1R / r0).
Skenario: REAL (taker 0,05% + slip 0,03%, maker 0,02%), KONS (taker 0,05% + slip 0,10%, maker 0,02%).
Tahun = tahun kalender TUTUP posisi (laba terealisasi); dicek juga dengan tahun buka.
Argumen: <repo> <data_dir> [out_csv]."""
import bisect, json, os, sys, time
import numpy as np, pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _replay as rp

REPO, DATA_DIR = sys.argv[1], sys.argv[2]
OUT = sys.argv[3] if len(sys.argv) > 3 else f"{DATA_DIR}/tahap0_trades.csv"
SKEN = {"REAL": dict(taker=0.0005, slip=0.0003, maker=0.0002),
        "KONS": dict(taker=0.0005, slip=0.0010, maker=0.0002)}


def hl_sejak(coin, start_s):
    """Funding Hyperliquid per jam sejak start_s (sumber bot live)."""
    import urllib.request
    out, start = [], int(start_s) * 1000
    for _ in range(20):
        body = json.dumps({"type": "fundingHistory", "coin": rp.sb.HL_NAME.get(coin, coin), "startTime": start}).encode()
        try:
            req = urllib.request.Request("https://api.hyperliquid.xyz/info", data=body, headers={"Content-Type": "application/json"})
            d = json.load(urllib.request.urlopen(req, timeout=60))
        except Exception:
            time.sleep(3); continue
        if not d: break
        out += [[x["time"] // 1000, float(x["fundingRate"])] for x in d]
        if len(d) < 500: break
        start = d[-1]["time"] + 1
    time.sleep(0.4)
    return out


def lengkapi_hl(sejak):
    """Lengkapi rp.FUND_HL (di memori) sejak waktu `sejak` agar replay periode live memakai sumber funding bot."""
    for c in rp.DATA:
        ts, rs = rp.FUND_HL.get(c, ([], []))
        if not ts or ts[0] > sejak:
            h = hl_sejak(c, sejak)
            if h:
                m = dict(zip(ts, rs)); m.update({tt: r for tt, r in h})
                k = sorted(m); rp.FUND_HL[c] = (k, [m[tt] for tt in k])


def funding_hl_dulu(coin, t):
    """Sumber funding seperti bot LIVE: Hyperliquid (rata 72 jam, >= 24 titik) bila ada, selain itu arsip Binance.
    Dipakai untuk cek kesehatan live = replay (11 Nov 2026: replay Binance-dulu beda tanda funding di POL/ALGO)."""
    ts, rs = rp.FUND_HL.get(coin, ([], []))
    a, b = bisect.bisect_right(ts, t - 72 * 3600), bisect.bisect_right(ts, t)
    if b - a >= 24:
        return sum(rs[a:b]) / (b - a)
    ts, rs = rp.FUND.get(coin, ([], []))
    a, b = bisect.bisect_right(ts, t - 72 * 3600), bisect.bisect_right(ts, t)
    return sum(rs[a:b]) / (b - a) if b - a >= 6 else None


def run_replay(gate=None, fund_fn=None):
    """Replay mesin asli dengan notifier yang mencatat detail fill / TP sebagian / keluar.
    gate(coin, i, D, d, entry, sl, t) -> bool (opsional, replay penuh: slot ikut berubah, lihat _replay.py)."""
    sb = rp.sb
    cur, rows = {}, []

    def notify(kind, coin, **k):
        if kind == "fill":
            cur[coin] = dict(coin=coin, d=k["d"], t_fill=k["t"], e=k["entry"], r0=k["r0"], sl0=k["sl"],
                             t_part=None, px_part=None)
        elif kind == "partial":
            cur[coin].update(t_part=k["t"], px_part=k["px"])
        elif kind == "exit":
            x = cur.pop(coin)
            x.update(t_exit=k["t"], ex=k["exit"], why=k["why"], R=k["R"])
            rows.append(x)

    state = {"coins": {}, "last_ts": 0, "replay": True}
    if gate is None:
        eng = sb.Engine(state, fund_fn or rp.funding_fn, notify)
    else:
        eng = rp.make_engine_cls()(state, fund_fn or rp.funding_fn, notify)
        eng.gate = gate
    eng.run(rp.DATA, 0)
    return pd.DataFrame(rows), eng.open_count()


def funding_series(coin):
    """Gabung arsip Binance (8 jam / 4 jam) lalu Hyperliquid (per jam) setelah arsip habis."""
    ts, rs = rp.FUND.get(coin, ([], []))
    hts, hrs = rp.FUND_HL.get(coin, ([], []))
    last = ts[-1] if ts else -1
    T = list(ts) + [t for t in hts if t > last]
    R = list(rs) + [r for t, r in zip(hts, hrs) if t > last]
    return np.asarray(T, float), np.asarray(R, float)


def add_costs(df):
    FS = {c: funding_series(c) for c in df.coin.unique()}
    fund_R, notional = [], []
    for x in df.itertuples():
        D = rp.DATA[x.coin]; T = D["T"]; C = D["C"]
        ft, fr = FS[x.coin]
        a, b = bisect.bisect_right(ft, x.t_fill), bisect.bisect_right(ft, x.t_exit)
        f = 0.0
        for j in range(a, b):
            ts = ft[j]
            k = bisect.bisect_right(T, ts) - 1
            px = C[k] if k >= 0 else x.e
            frac = (1 - rp.sb.TP1_FRAC) if (x.t_part is not None and not pd.isna(x.t_part) and ts >= x.t_part) else 1.0
            f += frac * fr[j] * x.d * px / x.r0       # positif = biaya
        fund_R.append(f)
        notional.append(x.e / x.r0)                  # nilai posisi per 1R saat entry
    df = df.assign(fund_R=fund_R, lev_R=notional)
    has_part = df.px_part.notna()
    for k, s in SKEN.items():
        ent = (s["taker"] + s["slip"]) * df.e / df.r0
        fr = rp.sb.TP1_FRAC                                    # porsi TP sebagian (0,25 di bot v2)
        part = np.where(has_part, fr * s["maker"] * df.px_part.fillna(0) / df.r0, 0.0)
        rest = np.where(has_part, 1 - fr, 1.0) * (s["taker"] + s["slip"]) * df.ex / df.r0
        df[f"fee_{k}"] = ent + part + rest
        df[f"R_{k}"] = df.R - df[f"fee_{k}"] - df.fund_R
    df["R_KOTOR"] = df.R
    df["year"] = pd.to_datetime(df.t_exit, unit="s").dt.year
    df["year_open"] = pd.to_datetime(df.t_fill, unit="s").dt.year
    return df.sort_values("t_exit").reset_index(drop=True)


def maxdd(R):
    c = np.cumsum(np.asarray(R, float))
    return float((np.maximum.accumulate(np.concatenate([[0], c]))[1:] - c).max()) if len(c) else 0.0


def drop_top(R, frac=0.02):
    R = np.sort(np.asarray(R, float))
    k = max(1, int(round(len(R) * frac)))
    return R[:-k]


def ystats(g, col):
    R = g.sort_values("t_exit")[col].values
    w, l = R[R > 0].sum(), -R[R < 0].sum()
    return dict(n=len(R), R=R.sum(), avg=R.mean(), win=(R > 0).mean() * 100, pf=w / l if l else np.inf,
                dd=maxdd(R), tanpa2=drop_top(R).sum())


def year_table(df, col, ycol="year"):
    rows = {y: ystats(g, col) for y, g in df.groupby(ycol)}
    # versi tanpa 2% trade terbaik SECARA GLOBAL (trade terbaik bisa menumpuk di satu tahun)
    k = max(1, int(round(len(df) * 0.02)))
    top = df[col].nlargest(k).index
    g2 = df.drop(top).groupby(ycol)[col].sum()
    for y in rows:
        rows[y]["tanpa2g"] = float(g2.get(y, 0.0))
    t = pd.DataFrame(rows).T
    return t


MIN_R_TAHUN = 1.0      # syarat pemilik (6 Nov 2026): setiap tahun kalender R bersih REAL >= +1R


def p_minus(df, col="R_REAL", y0=2020, n_boot=20000, seed=1):
    """Peluang tahun minus (bootstrap trade tahun itu). Informasi risiko, bukan syarat lulus."""
    rng = np.random.default_rng(seed)
    out = {}
    for y, g in df[df.year >= y0].groupby("year"):
        R = g[col].values
        out[y] = float((rng.choice(R, (n_boot, len(R))).sum(1) < 0).mean() * 100)
    return out


def lulus(df, col="R_REAL", y0=2020):
    t = df[df.year >= y0].groupby("year")[col].sum()
    return bool((t >= MIN_R_TAHUN).all()), float(t.min()), int(t.idxmin())


def ringkas_tahun(df, col="R_REAL", y0=2020):
    """Metrik program TAMBAL-CELAH: tahun minus (biasa & tanpa 2% terbaik per tahun), tahun terburuk, total, DD."""
    t = year_table(df[df.year >= y0], col)
    return dict(n=len(df), tot=float(df[col].sum()), dd=maxdd(df.sort_values("t_exit")[col].values),
                minus=int((t.R < 0).sum()), minus2=int((t.tanpa2 < 0).sum()),
                worst=float(t.R.min()), worst2=float(t.tanpa2.min()),
                per=t.R.round(1).to_dict(), per2=t.tanpa2.round(1).to_dict())


if __name__ == "__main__":
    t0 = time.time()
    rp.load(REPO, DATA_DIR)
    df, still_open = run_replay()
    df = add_costs(df)
    df.to_csv(OUT, index=False)
    print(f"trade: {len(df)} · masih terbuka: {still_open} · {time.time()-t0:.0f} dtk · simpan {OUT}")
    print(f"biaya rata-rata/trade (R): fee REAL {df.fee_REAL.mean():.3f} · fee KONS {df.fee_KONS.mean():.3f} · "
          f"funding {df.fund_R.mean():+.3f} (long {df[df.d==1].fund_R.mean():+.3f}, short {df[df.d==-1].fund_R.mean():+.3f})"
          f" · nilai posisi per 1R median {df.lev_R.median():.1f}x")
    pd.set_option("display.width", 200)
    for col in ["R_KOTOR", "R_REAL", "R_KONS"]:
        t = year_table(df, col)
        print(f"\n== {col} per tahun tutup ==")
        print(t.round(2).to_string())
        avg = t.loc[[y for y in t.index if 2020 <= y <= 2025], "R"].mean()
        print(f"semua: {df[col].sum():.1f}R · DD {maxdd(df[col].values):.1f}R · rata2 tahunan penuh 2020-2025 {avg:.1f}R")
    ok, worst, wy = lulus(df)
    print(f"\nSYARAT (tiap tahun R bersih REAL >= +{MIN_R_TAHUN:.0f}R): {'LULUS' if ok else 'TIDAK LULUS'} · terburuk {wy} {worst:+.1f}R")
    print("peluang tahun minus (bootstrap, %):", {y: round(v, 1) for y, v in p_minus(df).items()})
    t = year_table(df, "R_REAL", "year_open")
    print("\n== R_REAL per tahun BUKA ==\n", t[["n", "R", "tanpa2", "tanpa2g"]].round(1).to_string())
