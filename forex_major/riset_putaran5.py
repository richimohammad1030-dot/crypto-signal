"""Riset putaran 5: 3 bot yang SALING MENUTUP CELAH (prinsip pemilik, 20 Nov 2026), bukan 3 varian satu mesin.
  UTAMA  : N3 breakout level minggu lalu (Selasa-Jumat), SL 0,4 / TP 0,4 ATR, BE +0,5R, maks 2/hari.
  PENGISI: aktif di hari UTAMA belum entry sampai jam keputusan (termasuk Senin, hari libur UTAMA).
  BALAS  : setelah posisi UTAMA kena SL penuh, masuk BERLAWANAN arah di pair yang sama (breakout gagal -> berbalik).
Seleksi tiap bot: PF IS (2015-2022) > 1,05, OOS (2023-2026) > 1,05, Setra > 1,0. Lalu sistem gabungan (maks 4/hari total).
Pemakaian: python forex_major/riset_putaran5.py"""
import itertools, json, os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import backtest as B
from backtest import order, atr, rsi, prev_daily
from riset_putaran2 import SPLIT, pf
import riset_putaran4 as R4

ROOT = os.path.dirname(os.path.abspath(__file__)); ALL = R4.ALL
MAIN = dict(dist=9.0, vol="none", dow="mon", slm=0.4, tpm=0.4, be=0.5)


def main_trades(data):
    B.MAX_DAY = 2
    tr, nd = R4.run(MAIN, data); tr = B.portfolio(tr); B.MAX_DAY = 4
    return tr, nd


def sim(data, gen):
    """gen(P) -> {hari: [order]}; simulasi tanpa batas portofolio (diterapkan belakangan)."""
    out = []
    for P in data:
        for d, lst in gen(P).items(): out += B.simulate_pair(P, lst, d)
    return out


# ---------------- PENGISI ----------------
def pengisi(kind, kw, busy):
    """busy: set (pair, hari) & set hari yang UTAMA sudah entry sebelum jam keputusan -> pengisi tidak aktif."""
    def gen(P):
        idx, D = prev_daily(P); A = atr(D); H = P.h1; R2 = rsi(D["c"], 2); out = {}
        pos = {int(t): i for i, t in enumerate(H["t"])}
        for d, j in idx.items():
            if j < 30 or d in busy: continue
            t0 = d * 86400; a = A[j]
            if kind == "asia_fade":          # range Asia 00-07 UTC, limit lawan arah di luar range, TP ke tengah range
                i0, i1 = pos.get(t0), pos.get(t0 + 6 * 3600)
                if i0 is None or i1 is None: continue
                hi, lo = H["h"][i0:i1 + 1].max(), H["l"][i0:i1 + 1].min(); mid = (hi + lo) / 2; off = kw["off"] * a
                if hi - lo > kw["maxr"] * a: continue
                s_, b_ = hi + off, lo - off
                out[d] = [order(P.name, "PG", -1, "limit", s_, s_ + kw["slm"] * a, mid, t0 + 7 * 3600, oco=("PG", d), t_off=t0 + 12 * 3600),
                          order(P.name, "PG", 1, "limit", b_, b_ - kw["slm"] * a, mid, t0 + 7 * 3600, oco=("PG", d), t_off=t0 + 12 * 3600)]
            elif kind == "london_mom":       # candle 1 jam pertama London kuat -> limit 50% badan searah
                i = pos.get(t0 + 7 * 3600)
                if i is None: continue
                o, h, l, c = H["o"][i], H["h"][i], H["l"][i], H["c"][i]; r = h - l
                if r < kw["rng"] * a or abs(c - o) < 0.6 * r: continue
                side = 1 if c > o else -1; px = (o + c) / 2; sl = l if side > 0 else h
                out[d] = [order(P.name, "PG", side, "limit", px, sl, px + side * kw["tp"] * abs(px - sl), t0 + 8 * 3600, t_off=t0 + 11 * 3600)]
            elif kind == "rsi2":             # RSI2 harian ekstrem -> mean reversion, limit di close kemarin, mulai 07 UTC
                if not (R2[j] < kw["lv"] or R2[j] > 100 - kw["lv"]): continue
                side = 1 if R2[j] < kw["lv"] else -1; px = D["c"][j]
                out[d] = [order(P.name, "PG", side, "limit", px, px - side * kw["slm"] * a, px + side * kw["tpm"] * a, t0 + 7 * 3600)]
            elif kind == "week_mid":         # posisi di range minggu lalu jam 07 UTC: dekat tepi -> balik ke tengah
                wk = (D["t"] // 86400 + 3) // 7; m = wk == ((d + 3) // 7 - 1); i = pos.get(t0 + 7 * 3600)
                if not m.any() or i is None: continue
                ph, pl = D["h"][m].max(), D["l"][m].min(); px = H["o"][i]; z = (px - pl) / max(ph - pl, 1e-9)
                if kw["edge"] < z < 1 - kw["edge"] or z > 1 or z < 0: continue
                side = -1 if z >= 1 - kw["edge"] else 1
                out[d] = [order(P.name, "PG", side, "market", px, px - side * kw["slm"] * a, px + side * kw["tpm"] * a, t0 + 7 * 3600)]
        return out
    return gen


PENGISI = {
    "asia_fade": dict(off=[0.0, 0.1], slm=[0.3, 0.5], maxr=[0.5, 0.8]),
    "london_mom": dict(rng=[0.15, 0.25, 0.35], tp=[1.0, 1.5]),
    "rsi2": dict(lv=[5, 10, 15], slm=[0.5, 0.8], tpm=[0.3, 0.5]),
    "week_mid": dict(edge=[0.15, 0.25], slm=[0.4, 0.6], tpm=[0.3, 0.5]),
}


# ---------------- BALAS ----------------
def balas(kw, main):
    """Setelah UTAMA kena SL penuh (R <= -0,5) sebelum 14 UTC -> market berlawanan di candle berikutnya."""
    trig = {}
    for t in main:
        if t["R"] <= -0.5 and t["why"] == "sl" and (t["t_exit"] % 86400) < 14 * 3600:
            trig.setdefault((t["pair"], t["t_exit"] // 86400), t)
    def gen(P):
        idx, D = prev_daily(P); A = atr(D); out = {}
        for (pair, d), t in trig.items():
            if pair != P.name or d not in idx: continue
            a = A[idx[d]]; side = -t["side"]; ref = t["sl"]; t_on = (t["t_exit"] // 3600 + 1) * 3600
            if kw["entry"] == "market":
                o = order(P.name, "BL", side, "market", ref, ref - side * kw["slm"] * a, ref + side * kw["tpm"] * a, t_on)
            else:                            # retest: limit di level breakout (entry UTAMA) arah balik
                px = t["entry"]; o = order(P.name, "BL", side, "limit", px, px - side * kw["slm"] * a, px + side * kw["tpm"] * a, t_on, t_off=t_on + 4 * 3600)
            out.setdefault(d, []).append(o)
        return out
    return gen


BALAS = dict(entry=["market", "retest"], slm=[0.3, 0.5, 0.8], tpm=[0.3, 0.5, 0.8, 1.2])


def system(main, extra, cap=4):
    """Gabung: UTAMA sudah difilter; tambahan masuk bila total hari itu < cap dan bot itu belum di pair tsb hari itu."""
    out = list(main); cnt = {}; used = set()
    for t in main: cnt[t["t"] // 86400] = cnt.get(t["t"] // 86400, 0) + 1
    for t in sorted(extra, key=lambda x: x["t"]):
        d = t["t"] // 86400; k = (t["strat"], t["pair"], d)
        if cnt.get(d, 0) >= cap or k in used: continue
        cnt[d] = cnt.get(d, 0) + 1; used.add(k); out.append(t)
    return sorted(out, key=lambda x: x["t"])


def stat(tr, nd):
    if not tr: return dict(n=0)
    R = np.array([t["R"] for t in tr]); eq = np.cumsum(R); dd = float((np.maximum.accumulate(np.insert(eq, 0, 0))[1:] - eq).max())
    yrs = {}
    for t in tr: y = time.gmtime(t["t"]).tm_year; yrs[y] = yrs.get(y, 0) + t["R"]
    nw = cur = 0
    for r in R: cur = 0 if r > 0 else cur + 1; nw = max(nw, cur)
    IS = [t for t in tr if t["t"] < SPLIT]; OOS = [t for t in tr if t["t"] >= SPLIT]
    days = len({t["t"] // 86400 for t in tr})
    return dict(n=len(R), pf=pf(tr)[0], pf_is=pf(IS)[0], pf_oos=pf(OOS)[0], R=float(R.sum()), dd=dd, nw=nw, wr=float(np.mean(R > 0)),
                pw=len(R) / (nd / 7), pos=sum(v > 0 for v in yrs.values()), ny=len(yrs), worst=min(yrs.values()),
                years={y: round(v, 1) for y, v in sorted(yrs.items())}, days_pct=days / (nd * 5 / 7))


def line(s):
    return (f"PF {s['pf']:.2f} (IS {s['pf_is']:.2f} / OOS {s['pf_oos']:.2f}) | {s['R']:+.0f}R | DD {s['dd']:.0f}R | WR {s['wr']:.0%} | "
            f"{s['pw']:.1f}/mgg | hari ada trade {s['days_pct']:.0%} | th+ {s['pos']}/{s['ny']} terburuk {s['worst']:+.0f}R | tanpa-menang beruntun {s['nw']}")


if __name__ == "__main__":
    duka = [B.load(p) for p in ALL]
    os.environ["FX_DATA"] = "data_setra/{pair}_1h.json.gz"; setra = [B.load(p) for p in ALL]
    res = {}
    for lab, data in (("duka", duka), ("setra", setra)):
        m, nd = main_trades(data)
        busy = {t["t"] // 86400 for t in m if (t["t"] % 86400) < 7 * 3600}   # hari UTAMA sudah entry sebelum 14:00 WIB
        res[lab] = (m, nd, busy)
    m, nd, busy = res["duka"]; sm = stat(m, nd)
    print("UTAMA:", line(sm), flush=True)

    best = {}
    for kind, g in PENGISI.items():
        keys = list(g)
        for vals in itertools.product(*[g[k] for k in keys]):
            kw = dict(zip(keys, vals))
            a = sim(duka, pengisi(kind, kw, res["duka"][2])); b = sim(setra, pengisi(kind, kw, res["setra"][2]))
            s = stat(sorted(a, key=lambda x: x["t"]), nd); ps = pf(b)[0]
            ok = s["n"] and s["pf_is"] > 1.05 and s["pf_oos"] > 1.05 and ps > 1.0
            if ok: best.setdefault("PENGISI", []).append((min(s["pf_is"], s["pf_oos"]), kind, kw, ps, s, a, b))
            print(("  LOLOS " if ok else "  gagal ") + f"PENGISI {kind} {kw}: Setra {ps:.2f} | " + (line(s) if s["n"] else "0 trade"), flush=True)
    keys = list(BALAS)
    for vals in itertools.product(*[BALAS[k] for k in keys]):
        kw = dict(zip(keys, vals))
        a = sim(duka, balas(kw, res["duka"][0])); b = sim(setra, balas(kw, res["setra"][0]))
        s = stat(sorted(a, key=lambda x: x["t"]), nd); ps = pf(b)[0]
        ok = s["n"] and s["pf_is"] > 1.05 and s["pf_oos"] > 1.05 and ps > 1.0
        if ok: best.setdefault("BALAS", []).append((min(s["pf_is"], s["pf_oos"]), "balas", kw, ps, s, a, b))
        print(("  LOLOS " if ok else "  gagal ") + f"BALAS {kw}: Setra {ps:.2f} | " + (line(s) if s["n"] else "0 trade"), flush=True)

    print("\n=== SISTEM GABUNGAN (maks 4/hari) ===", flush=True)
    pg = sorted(best.get("PENGISI", []), key=lambda r: r[0], reverse=True)[:1]
    bl = sorted(best.get("BALAS", []), key=lambda r: r[0], reverse=True)[:1]
    for name, parts in (("UTAMA+PENGISI", pg), ("UTAMA+BALAS", bl), ("UTAMA+PENGISI+BALAS", pg + bl)):
        if len(parts) < (2 if name.count("+") == 2 else 1): continue
        ex = [t for p in parts for t in p[5]]
        print(name, [(p[1], p[2]) for p in parts], "\n  ", line(stat(system(m, ex), nd)), flush=True)
    json.dump({k: [(r[1], r[2], r[3], {x: y for x, y in r[4].items() if x != "years"}) for r in v] for k, v in best.items()},
              open(f"{ROOT}/hasil_putaran5.json", "w"), indent=1, default=float)
