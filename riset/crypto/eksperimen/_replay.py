"""Replay penuh memakai class Engine asli dari signal_bot.py, dengan gerbang tambahan untuk order baru.
Gerbang dipanggil saat engine akan membuat/mengganti order pending: gate(coin, i, D, d, entry, sl, t) -> bool.
Jika gerbang menolak, order tidak dibuat (order lama dibatalkan) dan slot tetap kosong untuk koin lain,
persis seperti bot live bila aturan itu dipasang.
Pemakaian modul: load(repo, data_dir) lalu replay(gate) -> DataFrame trade (coin, d, t0, t1, R)."""
import bisect, json, os, sys, time
import numpy as np, pandas as pd

sb = None
DATA, FUND, FUND_HL, IDX, REG = {}, {}, {}, {}, {}


def load(repo, data_dir):
    global sb
    sys.path.insert(0, repo)
    import signal_bot as _sb
    sb = _sb
    for c in sb.COINS:
        p = f"{data_dir}/klines/{c}.json"
        rows = json.load(open(p)) if os.path.exists(p) else []
        rows = [r[:5] for r in rows if r[5] < time.time() * 1000]
        if len(rows) < sb.K + 1350:
            continue
        D = sb.prep(rows)
        DATA[c] = D
        IDX[c] = {t: i for i, t in enumerate(D["T"])}
        REG[c] = [sb._regime(D, i) for i in range(len(D["T"]))]
        f = f"{data_dir}/funding/{c}.json"
        f = json.load(open(f)) if os.path.exists(f) else []
        FUND[c] = ([x[0] for x in f], [x[1] for x in f])
        h = f"{data_dir}/funding_hl/{c}.json"
        h = json.load(open(h)) if os.path.exists(h) else []
        FUND_HL[c] = ([x[0] for x in h], [x[1] for x in h])
    return DATA


def funding_fn(coin, t):
    """Sama persis dengan riset/backtest_crypto.py."""
    ts, rs = FUND.get(coin, ([], []))
    a, b = bisect.bisect_right(ts, t - 72 * 3600), bisect.bisect_right(ts, t)
    if b - a >= 6:
        return sum(rs[a:b]) / (b - a)
    ts, rs = FUND_HL.get(coin, ([], []))
    a, b = bisect.bisect_right(ts, t - 72 * 3600), bisect.bisect_right(ts, t)
    return sum(rs[a:b]) / (b - a) if b - a >= 24 else None


def btc_regime(t):
    j = IDX["BTC"].get(t)
    if j is None:
        B = DATA["BTC"]; j = bisect.bisect_right(B["T"], t) - 1
    return REG["BTC"][j] if j >= 0 else 0


def make_engine_cls():
    class GatedEngine(sb.Engine):
        gate = None

        def step_check(self, coin, i, D, allow_new):
            cs = self.s["coins"].setdefault(coin, {"pend": None, "pos": None})
            if cs.get("pos") is not None or self.gate is None:
                return super().step_check(coin, i, D, allow_new)
            C, H, L, A, EF, ES, T = D["C"], D["H"], D["L"], D["A"], D["EF"], D["ES"], D["T"][i]
            if C[i] > ES[i] and EF[i] > ES[i]:
                d = 1; en = max(H[i - sb.K + 1:i + 1])
            elif C[i] < ES[i] and EF[i] < ES[i]:
                d = -1; en = min(L[i - sb.K + 1:i + 1])
            else:
                return super().step_check(coin, i, D, allow_new)
            sl = en - d * sb.SL_ATR * A[i]
            ok = self.gate(coin, i, D, d, en, sl, T)
            return super().step_check(coin, i, D, (lambda c, old: allow_new(c, old) and ok))
    return GatedEngine


def replay(gate=None):
    cls = make_engine_cls()
    state = {"coins": {}, "last_ts": 0, "replay": True}
    eng = cls(state, funding_fn, lambda *a, **k: None)
    eng.gate = gate
    eng.run(DATA, 0)
    h = state.get("hist", [])
    df = pd.DataFrame(h, columns=["coin", "d", "t0", "t1", "e", "ex", "R"])
    df["year"] = pd.to_datetime(df.t0, unit="s").dt.year
    return df.sort_values("t1").reset_index(drop=True), eng.open_count()


# ------------------------------------------------------------------ statistik
def maxdd(R):
    c = np.cumsum(np.asarray(R, float))
    return float((np.maximum.accumulate(np.concatenate([[0], c]))[1:] - c).max()) if len(c) else 0.0


def stats(df):
    df = df.sort_values("t1")
    R = df.R.values
    if len(R) == 0:
        return dict(n=0, tot=0.0, avg=0.0, wr=0.0, dd=0.0, rasio=0.0, tahan=0.0)
    dd = maxdd(R)
    k = max(1, int(round(len(R) * 0.02)))
    tahan = float(np.sort(R)[:-k].sum())
    return dict(n=len(R), tot=float(R.sum()), avg=float(R.mean()), wr=float((R > 0).mean() * 100), dd=dd,
                rasio=float(R.sum() / dd) if dd > 0 else float("inf"), tahan=tahan)


def periods(df):
    return {"2020-2023": df[(df.year >= 2020) & (df.year <= 2023)], "2024-skrg": df[df.year >= 2024], "Semua": df}


def compare(champ, var, years=range(2021, 2027)):
    """Ringkasan keputusan sesuai PROSEDUR: Δ rasio lama/baru, tahun tidak lebih buruk, ketahanan."""
    pc, pv = periods(champ), periods(var)
    out = {}
    for k in pc:
        out[k] = (stats(pc[k]), stats(pv[k]))
    yr = {}
    for y in years:
        yr[y] = (stats(champ[champ.year == y]), stats(var[var.year == y]))
    not_worse = sum(1 for y, (a, b) in yr.items() if b["rasio"] >= a["rasio"] - 1e-9)
    d_old = out["2020-2023"][1]["rasio"] / out["2020-2023"][0]["rasio"] - 1
    d_new = out["2024-skrg"][1]["rasio"] / out["2024-skrg"][0]["rasio"] - 1
    tahan_ok = all(out[k][1]["tahan"] >= out[k][0]["tahan"] - 1e-9 for k in ("2020-2023", "2024-skrg"))
    lolos = d_old >= 0.10 and d_new >= 0.10 and not_worse >= 4 and tahan_ok
    return dict(per=out, yr=yr, d_old=d_old, d_new=d_new, not_worse=not_worse, tahan_ok=tahan_ok, lolos=lolos)


def fmt_compare(name, c):
    o, n = c["per"]["2020-2023"], c["per"]["2024-skrg"]
    a = c["per"]["Semua"][1]
    return (f"| {name} | {a['n']} | {a['tot']:.1f} | {a['avg']:+.3f} | {a['wr']:.1f}% | {a['dd']:.1f} | "
            f"{o[1]['rasio']:.1f} | {n[1]['rasio']:.1f} | {c['d_old']*100:+.0f}% | {c['d_new']*100:+.0f}% | "
            f"{c['not_worse']}/6 | {o[1]['tahan']:.1f} / {n[1]['tahan']:.1f} | {'LOLOS' if c['lolos'] else 'GAGAL'} |")


HEADER = ("| Varian | Trade | Total R | R/trade | Win | DD | Rasio lama | Rasio baru | Δ lama | Δ baru | "
          "Tahun ≥ juara | Tanpa top 2% (lama / baru) | Keputusan |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|")
