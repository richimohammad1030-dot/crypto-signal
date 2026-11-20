"""Riset putaran 3 bot FX MAJOR: target minimal 4 trade/minggu (pemilik, 20 Nov 2026).
Keluarga baru: N3x (breakout mingguan, variasi tren), N4 (breakout high/low kemarin searah tren), N5 (Donchian k-hari searah tren),
N6 (turtle soup level mingguan). Seleksi per varian sama dengan putaran 2 (IS 2015-2022, OOS 2023-2026, Setra), tanpa syarat
trade/minggu; lalu kombinasi varian terbaik tiap keluarga dicari yang >= 4 trade/minggu dengan PF terendah (IS/OOS/Setra) tertinggi.
Terakhir: validasi kombinasi terpilih di M5 Dukascopy 2020-2026 vs H1 periode sama.
Pemakaian: python forex_major/riset_putaran3.py"""
import itertools, json, os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import backtest as B
from backtest import order, atr, ema, prev_daily
from riset_putaran2 import SPLIT, pf, n3

ROOT = os.path.dirname(os.path.abspath(__file__))


def n3x(P, ema_n=50, slm=0.4, tpm=1.2, trend=True):
    """Breakout high/low minggu lalu. trend=True: hanya searah EMA harian; False: OCO dua arah."""
    idx, D = prev_daily(P); A = atr(D); E = ema(D["c"], ema_n); out = {}; wk = (D["t"] // 86400 + 3) // 7
    for d, j in idx.items():
        if j < max(60, ema_n): continue
        m = wk == ((d + 3) // 7 - 1)
        if not m.any(): continue
        ph, pl = D["h"][m].max(), D["l"][m].min(); a = A[j]; t0 = d * 86400
        if trend:
            side = 1 if D["c"][j] > E[j] else -1; lvl = ph if side > 0 else pl
            if (side > 0 and D["h"][j] >= ph) or (side < 0 and D["l"][j] <= pl): continue
            out[d] = [order(P.name, "N3", side, "stop", lvl, lvl - side * slm * a, lvl + side * tpm * a, t0)]
        else:
            lst = []
            if D["h"][j] < ph: lst.append(order(P.name, "N3", 1, "stop", ph, ph - slm * a, ph + tpm * a, t0, oco=("N3", d)))
            if D["l"][j] > pl: lst.append(order(P.name, "N3", -1, "stop", pl, pl + slm * a, pl - tpm * a, t0, oco=("N3", d)))
            if lst: out[d] = lst
    return out


def n4(P, ema_n=50, slm=0.4, tpm=1.0):
    """Breakout high/low kemarin searah tren EMA harian (stop order jam 07:00 WIB)."""
    idx, D = prev_daily(P); A = atr(D); E = ema(D["c"], ema_n); out = {}
    for d, j in idx.items():
        if j < max(30, ema_n): continue
        side = 1 if D["c"][j] > E[j] else -1; lvl = D["h"][j] if side > 0 else D["l"][j]; a = A[j]
        out[d] = [order(P.name, "N4", side, "stop", lvl, lvl - side * slm * a, lvl + side * tpm * a, d * 86400)]
    return out


def n5(P, k=10, ema_n=50, slm=0.4, tpm=1.2):
    """Donchian k-hari searah tren EMA harian."""
    idx, D = prev_daily(P); A = atr(D); E = ema(D["c"], ema_n); out = {}
    for d, j in idx.items():
        if j < max(k + 1, ema_n): continue
        side = 1 if D["c"][j] > E[j] else -1
        lvl = D["h"][j - k + 1:j + 1].max() if side > 0 else D["l"][j - k + 1:j + 1].min(); a = A[j]
        out[d] = [order(P.name, "N5", side, "stop", lvl, lvl - side * slm * a, lvl + side * tpm * a, d * 86400)]
    return out


def n6(P, slm=0.15, tpm=1.0):
    """Turtle soup level mingguan: tembus high/low minggu lalu > 0,1 ATR lalu candle H1 tutup kembali di dalam -> stop balik di level."""
    idx, D = prev_daily(P); A = atr(D); H = P.h1; out = {}; wk = (D["t"] // 86400 + 3) // 7
    for d, j in idx.items():
        if j < 20: continue
        m = wk == ((d + 3) // 7 - 1)
        if not m.any(): continue
        ph, pl = D["h"][m].max(), D["l"][m].min(); a = A[j]; t0 = d * 86400
        i0, i1 = np.searchsorted(H["t"], t0), np.searchsorted(H["t"], t0 + 13 * 3600)
        for i in range(i0, min(i1, len(H["t"]))):
            if H["h"][i] > ph + 0.1 * a and H["c"][i] < ph:
                ext = H["h"][i0:i + 1].max(); sl = ext + slm * a
                out[d] = [order(P.name, "N6", -1, "stop", ph, sl, ph - tpm * a, H["t"][i] + 3600, t_off=H["t"][i] + 4 * 3600)]; break
            if H["l"][i] < pl - 0.1 * a and H["c"][i] > pl:
                ext = H["l"][i0:i + 1].min(); sl = ext - slm * a
                out[d] = [order(P.name, "N6", 1, "stop", pl, sl, pl + tpm * a, H["t"][i] + 3600, t_off=H["t"][i] + 4 * 3600)]; break
    return out


GRID = {
    "N3": (n3x, dict(ema_n=[20, 50, 100], slm=[0.3, 0.4, 0.5], tpm=[0.8, 1.2, 1.6], trend=[True, False])),
    "N4": (n4, dict(ema_n=[20, 50, 100], slm=[0.3, 0.4, 0.6], tpm=[0.6, 1.0, 1.4])),
    "N5": (n5, dict(k=[3, 5, 10, 20], ema_n=[20, 50, 100], slm=[0.3, 0.4, 0.6], tpm=[0.8, 1.2, 1.6])),
    "N6": (n6, dict(slm=[0.1, 0.2], tpm=[0.6, 1.0, 1.4])),
}


def trades_of(fn, kw, data):
    tr = []; days = set()
    for P in data:
        days |= set(int(x) for x in P.days)
        for d, lst in fn(P, **kw).items(): tr += B.simulate_pair(P, lst, d)
    return tr, (max(days) - min(days)) if days else 1


def score(tr, nd, ts):
    tr = B.portfolio(tr); ts = B.portfolio(ts)
    IS = [t for t in tr if t["t"] < SPLIT]; OOS = [t for t in tr if t["t"] >= SPLIT]
    yrs = {}
    for t in tr: y = time.gmtime(t["t"]).tm_year; yrs[y] = yrs.get(y, 0) + t["R"]
    return dict(pf_is=pf(IS)[0], r_is=pf(IS)[1], pf_oos=pf(OOS)[0], r_oos=pf(OOS)[1], pf_setra=pf(ts)[0], r_setra=pf(ts)[1],
                per_week=len(tr) / (nd / 7), wr=float(np.mean([t["R"] > 0 for t in tr])) if tr else 0,
                pos_years=sum(v > 0 for v in yrs.values()), n_years=len(yrs), years={y: round(v, 1) for y, v in sorted(yrs.items())},
                totR=sum(t["R"] for t in tr))


def fmt(s):
    return (f"PF IS {s['pf_is']:.2f} ({s['r_is']:+.0f}R) | OOS {s['pf_oos']:.2f} ({s['r_oos']:+.0f}R) | Setra {s['pf_setra']:.2f} ({s['r_setra']:+.0f}R)"
            f" | WR {s['wr']:.0%} | {s['per_week']:.1f}/mgg | tahun+ {s['pos_years']}/{s['n_years']}")


if __name__ == "__main__":
    duka = [B.load(p) for p in B.PAIRS]
    os.environ["FX_DATA"] = "data_setra/{pair}_1h.json.gz"; setra = [B.load(p) for p in B.PAIRS]
    best = {}; allrows = []
    for n, (fn, g) in GRID.items():
        keys = list(g); rows = []
        for vals in itertools.product(*[g[k] for k in keys]):
            kw = dict(zip(keys, vals)); tr, nd = trades_of(fn, kw, duka); ts, _ = trades_of(fn, kw, setra)
            s = score(tr, nd, ts); s["lolos"] = s["pf_is"] > 1.05 and s["pf_oos"] > 1.05 and s["pf_setra"] > 1.0
            rows.append((kw, s, tr, ts, nd)); allrows.append(dict(strat=n, kw=kw, **{k: v for k, v in s.items() if k != "years"}))
        ok = [r for r in rows if r[1]["lolos"]]
        print(f"\n{n}: {len(ok)} lolos dari {len(rows)}", flush=True)
        for kw, s, *_ in sorted(ok, key=lambda r: min(r[1]["pf_is"], r[1]["pf_oos"]), reverse=True)[:3]: print("  ", fmt(s), kw, flush=True)
        # wakil keluarga: varian lolos dengan PF terendah (IS/OOS) tertinggi -> lebih tahan
        top = sorted(ok, key=lambda r: min(r[1]["pf_is"], r[1]["pf_oos"]), reverse=True)[:3]
        if top: best[n] = top
    json.dump(allrows, open(f"{ROOT}/hasil_putaran3.json", "w"), indent=1, default=float)

    print("\n=== KOMBINASI (target >= 4 trade/minggu) ===", flush=True)
    cands = []
    fams = list(best)
    for r in range(1, len(fams) + 1):
        for combo in itertools.combinations(fams, r):
            for pick in itertools.product(*[range(len(best[f])) for f in combo]):
                tr = []; ts = []; nd = 1
                for f, p in zip(combo, pick):
                    kw, s, t1, t2, nd = best[f][p]; tr += t1; ts += t2
                s = score(tr, nd, ts); s["combo"] = [(f, best[f][p][0]) for f, p in zip(combo, pick)]
                cands.append(s)
    good = [c for c in cands if c["per_week"] >= 4 and c["pf_is"] > 1.05 and c["pf_oos"] > 1.05 and c["pf_setra"] > 1.0]
    good.sort(key=lambda c: (min(c["pf_is"], c["pf_oos"]), c["pos_years"]), reverse=True)
    print(f"{len(good)} kombinasi memenuhi >= 4/mgg dan lolos semua uji", flush=True)
    for c in good[:5]: print("  ", fmt(c), c["combo"], "\n     tahun:", c["years"], flush=True)
    json.dump([dict(c, combo=[(f, kw) for f, kw in c["combo"]]) for c in good[:20]], open(f"{ROOT}/hasil_kombinasi3.json", "w"), indent=1, default=float)

    if good:
        print("\n=== VALIDASI M5 (Dukascopy 2020-2026) kombinasi terbaik ===", flush=True)
        os.environ["FX_DATA"] = "data_m5/{pair}_m5_*.json.gz"; m5 = [B.load(p) for p in B.PAIRS]
        lo = min(int(P.t[0]) for P in m5)
        os.environ["FX_DATA"] = "data/{pair}_h1_*.json.gz"
        for label, data in (("H1", duka), ("M5", m5)):
            tr = []; nd = 1
            for f, kw in good[0]["combo"]:
                t, nd = trades_of(GRID[f][0], kw, data); tr += [x for x in t if x["t"] >= lo]
            tr = B.portfolio(tr); nd = (time.time() - lo) / 86400; m = B.metrics(tr, nd)
            print(f"  {label}: n={m['n']} WR={m['wr']:.0%} PF={m['pf']:.2f} totR={m['totR']:.1f} DD={m['ddR']:.1f}R "
                  f"{m['per_week']:.1f}/mgg tahun+ {m['pos_years']}/{m['n_years']} {m['years']}", flush=True)
