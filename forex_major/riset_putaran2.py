"""Riset putaran 2 bot FX MAJOR: setel S8, S2, S6 + 3 ide baru (N1, N2, N3), dengan validasi anti-overfitting.
Aturan seleksi (ditetapkan SEBELUM melihat hasil):
  - In-sample (IS) = Dukascopy H1 2015-2022, out-of-sample (OOS) = Dukascopy H1 2023-2026, cek tambahan = Setra H1 2025-2026
  - Lolos bila PF IS > 1,05 DAN PF OOS > 1,05 DAN PF Setra > 1,0 DAN minimal 1 trade/minggu
  - Peringkat: PF OOS (data yang tidak dipakai menyetel)
Pemakaian: python forex_major/riset_putaran2.py"""
import itertools, json, os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import backtest as B
from backtest import order, atr, ema, rsi, sma, std, prev_daily

SPLIT = 1672531200          # 1 Jan 2023 UTC


# ---------- S8: candle 1 jam pertama London ----------
def s8(P, body=0.6, rng=0.25, entry="limit", tp=1.5, trend="none"):
    idx, D = prev_daily(P); A = atr(D); E = ema(D["c"], 50); H = P.h1; pos = {int(t): i for i, t in enumerate(H["t"])}; out = {}
    for d, j in idx.items():
        if j < 60: continue
        i = pos.get(d * 86400 + 7 * 3600)
        if i is None: continue
        o, h, l, c = H["o"][i], H["h"][i], H["l"][i], H["c"][i]; r = h - l
        if r < rng * A[j] or abs(c - o) < body * r: continue
        side = 1 if c > o else -1
        if trend == "with" and side != (1 if D["c"][j] > E[j] else -1): continue
        if trend == "against" and side == (1 if D["c"][j] > E[j] else -1): continue
        sl = l if side > 0 else h; t1 = d * 86400 + 8 * 3600
        if entry == "market":
            out[d] = [order(P.name, "S8", side, "market", c, sl, c + side * tp * abs(c - sl), t1)]
        else:                                   # limit di 50% badan candle
            px = (o + c) / 2
            out[d] = [order(P.name, "S8", side, "limit", px, sl, px + side * tp * abs(px - sl), t1, t_off=t1 + 3 * 3600)]
    return out


# ---------- S2: adaptasi XAU ----------
def s2(P, lv=10, mr_sl=0.6, mr_tp=0.6, bo_sl=0.5, bo_tp=1.0, mode="both"):
    idx, D = prev_daily(P); A = atr(D); R2 = rsi(D["c"], 2); H = P.h1; E = ema(H["c"], 200); out = {}
    for d, j in idx.items():
        if j < 30: continue
        t0 = d * 86400; a = A[j]; hi = np.searchsorted(H["t"], t0) - 1
        if hi < 200: continue
        ext = R2[j] < lv or R2[j] > 100 - lv
        if ext and mode in ("both", "mr"):
            side = 1 if R2[j] < lv else -1; px = D["c"][j]
            out[d] = [order(P.name, "S2", side, "limit", px, px - side * mr_sl * a, px + side * mr_tp * a, t0)]
        elif not ext and mode in ("both", "bo"):
            side = 1 if H["c"][hi] > E[hi] else -1; lvl = D["h"][j] if side > 0 else D["l"][j]
            out[d] = [order(P.name, "S2", side, "stop", lvl, lvl - side * bo_sl * a, lvl + side * bo_tp * a, t0)]
    return out


# ---------- S6: squeeze H1 ----------
def s6(P, kc=1.5, slm=1.0, tpm=2.0, h1=13):
    H = P.h1; c = H["c"]; m = sma(c, 20); sd = std(c, 20); A = atr(H, 20); em = ema(c, 20)
    sq = ((m + 2 * sd) < (em + kc * A)) & ((m - 2 * sd) > (em - kc * A)); out = {}
    for i in range(25, len(c)):
        t_end = H["t"][i] + 3600; hr = (t_end % 86400) // 3600
        if not (7 <= hr <= h1) or not sq[i - 5:i].any(): continue
        side = 1 if c[i] > m[i] + 2 * sd[i] else -1 if c[i] < m[i] - 2 * sd[i] else 0
        if not side: continue
        d = t_end // 86400
        if d in out: continue
        out[d] = [order(P.name, "S6", side, "stop", c[i], c[i] - side * slm * A[i], c[i] + side * tpm * A[i], t_end, t_off=t_end + 3600)]
    return out


# ---------- N1: fade gerakan London saat NY buka ----------
def n1(P, k=0.7, tp="half"):
    """Jam 13 UTC (20 WIB): bila harga sudah bergerak > k*ATR dari buka London, lawan arah (overshoot). SL ekstrem hari ini."""
    idx, D = prev_daily(P); A = atr(D); H = P.h1; pos = {int(t): i for i, t in enumerate(H["t"])}; out = {}
    for d, j in idx.items():
        if j < 20: continue
        i0, i1 = pos.get(d * 86400 + 7 * 3600), pos.get(d * 86400 + 12 * 3600)
        if i0 is None or i1 is None: continue
        op, now = H["o"][i0], H["c"][i1]; mv = now - op
        if abs(mv) < k * A[j]: continue
        side = -1 if mv > 0 else 1
        ext = H["h"][i0:i1 + 1].max() if side < 0 else H["l"][i0:i1 + 1].min()
        sl = ext - side * 0.1 * A[j]; risk = abs(now - sl)
        tgt = now + side * (abs(mv) * 0.5 if tp == "half" else float(tp) * risk)
        out[d] = [order(P.name, "N1", side, "market", now, sl, tgt, d * 86400 + 13 * 3600)]
    return out


# ---------- N2: momentum hari kemarin ----------
def n2(P, pct=0.2, slm=0.5, tpm=0.75):
    """Kemarin tutup di 20% teratas/terbawah range -> lanjut arah saat London buka (07 UTC), SL slm*ATR, TP tpm*ATR."""
    idx, D = prev_daily(P); A = atr(D); out = {}
    for d, j in idx.items():
        if j < 20: continue
        r = D["h"][j] - D["l"][j]
        if r <= 0 or r < 0.7 * A[j]: continue
        pos = (D["c"][j] - D["l"][j]) / r
        side = 1 if pos > 1 - pct else -1 if pos < pct else 0
        if not side: continue
        a = A[j]; t1 = d * 86400 + 7 * 3600; ref = D["c"][j]
        out[d] = [order(P.name, "N2", side, "market", ref, ref - side * slm * a, ref + side * tpm * a, t1)]
    return out


# ---------- N3: breakout high/low minggu lalu searah tren ----------
def n3(P, slm=0.5, tpm=1.0):
    idx, D = prev_daily(P); A = atr(D); E = ema(D["c"], 50); out = {}
    wk = (D["t"] // 86400 + 3) // 7                    # minggu dimulai Senin
    for d, j in idx.items():
        if j < 60: continue
        w = (d + 3) // 7; m = wk == (w - 1)
        if not m.any(): continue
        ph, pl = D["h"][m].max(), D["l"][m].min(); a = A[j]
        side = 1 if D["c"][j] > E[j] else -1; lvl = ph if side > 0 else pl
        if (side > 0 and D["h"][j] >= ph) or (side < 0 and D["l"][j] <= pl): continue   # sudah tembus minggu ini
        out[d] = [order(P.name, "N3", side, "stop", lvl, lvl - side * slm * a, lvl + side * tpm * a, d * 86400)]
    return out


GRID = {
    "S8": (s8, dict(body=[0.5, 0.6, 0.7], rng=[0.15, 0.25, 0.35], entry=["market", "limit"], tp=[1.0, 1.5, 2.0], trend=["none", "with", "against"])),
    "S2": (s2, dict(lv=[5, 10, 15], mr_sl=[0.6, 1.0], mr_tp=[0.6, 1.0], bo_sl=[0.5, 0.75], bo_tp=[1.0, 1.5], mode=["both", "mr", "bo"])),
    "S6": (s6, dict(kc=[1.5, 2.0], slm=[1.0, 1.5], tpm=[1.5, 2.0, 3.0], h1=[13, 16])),
    "N1": (n1, dict(k=[0.5, 0.7, 0.9], tp=["half", "1", "1.5"])),
    "N2": (n2, dict(pct=[0.15, 0.25], slm=[0.4, 0.6], tpm=[0.5, 0.75, 1.0])),
    "N3": (n3, dict(slm=[0.4, 0.6], tpm=[0.8, 1.2, 1.6])),
}


def evaluate(fn, kw, data):
    trades = []; days = set()
    for P in data:
        days |= set(int(x) for x in P.days)
        for d, lst in fn(P, **kw).items(): trades += B.simulate_pair(P, lst, d)
    tr = B.portfolio(trades); nd = (max(days) - min(days)) if days else 1
    return tr, nd


def pf(tr):
    R = np.array([t["R"] for t in tr]) if tr else np.array([0.0])
    g, l = R[R > 0].sum(), -R[R < 0].sum()
    return (g / l if l > 0 else 9.9), float(R.sum()), len(tr)


if __name__ == "__main__":
    duka = [B.load(p) for p in B.PAIRS]
    os.environ["FX_DATA"] = "data_setra/{pair}_1h.json.gz"; setra = [B.load(p) for p in B.PAIRS]
    names = sys.argv[1:] or list(GRID); rows = []
    for n in names:
        fn, g = GRID[n]; keys = list(g)
        for vals in itertools.product(*[g[k] for k in keys]):
            kw = dict(zip(keys, vals))
            tr, nd = evaluate(fn, kw, duka)
            IS = [t for t in tr if t["t"] < SPLIT]; OOS = [t for t in tr if t["t"] >= SPLIT]
            ts, _ = evaluate(fn, kw, setra)
            pi, ri, ni = pf(IS); po, ro, no = pf(OOS); ps, rs, ns = pf(ts)
            yrs = {}
            for t in tr: y = time.gmtime(t["t"]).tm_year; yrs[y] = yrs.get(y, 0) + t["R"]
            row = dict(strat=n, kw=kw, pf_is=round(pi, 3), r_is=round(ri, 1), pf_oos=round(po, 3), r_oos=round(ro, 1),
                       pf_setra=round(ps, 3), r_setra=round(rs, 1), per_week=round(len(tr) / (nd / 7), 2),
                       wr=round(float(np.mean([t["R"] > 0 for t in tr])), 3) if tr else 0,
                       pos_years=sum(v > 0 for v in yrs.values()), n_years=len(yrs))
            row["lolos"] = pi > 1.05 and po > 1.05 and ps > 1.0 and row["per_week"] >= 1
            rows.append(row)
        best = sorted([r for r in rows if r["strat"] == n], key=lambda r: (r["lolos"], r["pf_oos"]), reverse=True)[:3]
        print(f"\n{n}: {sum(r['lolos'] for r in rows if r['strat'] == n)} varian lolos dari {len([r for r in rows if r['strat'] == n])}", flush=True)
        for r in best:
            print(f"  {'LOLOS' if r['lolos'] else 'gagal'} PF IS {r['pf_is']} ({r['r_is']}R) | OOS {r['pf_oos']} ({r['r_oos']}R) | Setra {r['pf_setra']} ({r['r_setra']}R) "
                  f"| WR {r['wr']:.0%} | {r['per_week']}/mgg | tahun+ {r['pos_years']}/{r['n_years']} | {r['kw']}", flush=True)
    json.dump(rows, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "hasil_putaran2.json"), "w"), indent=1, default=float)
