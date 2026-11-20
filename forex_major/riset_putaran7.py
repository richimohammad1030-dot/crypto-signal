"""Riset putaran 7: optimasi BERSAMA UTAMA + SUSULAN (threshold pemilik: >= 4 trade/mgg, tanpa tahun minus, > 10%/th,
WR >= 35-40%, PF > 1) + pencarian BOT-3 tindak lanjut (setelah TP / BE / SL dari UTAMA & SUSULAN).
Pemakaian: python forex_major/riset_putaran7.py gabung <bagian> <jml_bagian> | bot3"""
import itertools, json, os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import backtest as B
from backtest import order, atr, prev_daily
from riset_putaran2 import pf
import riset_putaran6 as P6          # memasang spread asli Exness
from riset_putaran5 import stat, line

ALL = P6.ALL; SUS_OPEN_UTC = P6.SUS_OPEN_UTC


def sus_gen(kw, filled, exp):
    """SUSULAN pasang ulang level minggu lalu setelah UTAMA kadaluarsa (pair-hari tanpa isi UTAMA). kw: sl, tp, senin, at."""
    def gen(P):
        idx, D = prev_daily(P); A = atr(D); H = P.h1; pos = {int(t): i for i, t in enumerate(H["t"])}; out = {}
        wk = (D["t"] // 86400 + 3) // 7
        for d, j in idx.items():
            if j < 110 or (P.name, d) in filled: continue
            if (d + 3) % 7 == 0 and not kw["senin"]: continue
            first = 0 if ((d + 3) % 7 == 0 and kw.get("um") == "mon") else exp   # Senin & UTAMA libur Senin -> susulan sejak pagi
            hh = next((h for h in SUS_OPEN_UTC if h + 1 >= max(first, kw["at"])), None)
            if hh is None: continue
            t0 = d * 86400; i = pos.get(t0 + hh * 3600); i0 = pos.get(t0)
            m = wk == ((d + 3) // 7 - 1)
            if i is None or i0 is None or not m.any(): continue
            ph, pl = D["h"][m].max(), D["l"][m].min(); a = A[j]; t_on = t0 + (hh + 1) * 3600
            hi, lo = H["h"][i0:i + 1].max(), H["l"][i0:i + 1].min(); lst = []
            if D["h"][j] < ph and hi < ph: lst.append(order(P.name, "SUS", 1, "stop", ph, ph - kw["sl"] * a, ph + kw["tp"] * a, t_on, oco=("SUS", d)))
            if D["l"][j] > pl and lo > pl: lst.append(order(P.name, "SUS", -1, "stop", pl, pl + kw["sl"] * a, pl - kw["tp"] * a, t_on, oco=("SUS", d)))
            if lst: out[d] = lst
        return out
    return gen


def build(data, UK, SK):
    m = P6.utama(data, UK); f = {(t["pair"], t["t"] // 86400) for t in m}
    s = P6.run_gen(data, sus_gen(dict(SK, um=UK["dow"]), f, UK["exp"]))
    return sorted(m + s, key=lambda x: x["t"])


def yearly_pct(tr, risk):
    yrs = {}
    for t in tr: y = time.gmtime(t["t"]).tm_year; yrs[y] = yrs.get(y, 0) + t["R"]
    full = [v for y, v in yrs.items() if y < 2026]
    return float(np.mean(full)) * risk * 100 if full else 0


def bot3_gen(kw, base):
    """Tindak lanjut: pemicu = keluar trade UTAMA/SUSULAN dengan hasil kw['on'] (tp / be / sl) sebelum 20:00 WIB."""
    trig = {}
    for t in base:
        r = t["R"]; kind = "tp" if t["why"] == "tp" and r > 0.3 else "sl" if r <= -0.5 else "be" if -0.5 < r <= 0.05 else None
        if kind == kw["on"] and (t["t_exit"] % 86400) < 13 * 3600: trig.setdefault((t["pair"], t["t_exit"] // 86400), t)
    def gen(P):
        idx, D = prev_daily(P); A = atr(D); H = P.h1; pos = {int(x): i for i, x in enumerate(H["t"])}; out = {}
        for (pair, d), t in trig.items():
            if pair != P.name or d not in idx: continue
            a = A[idx[d]]; t_on = (t["t_exit"] // 3600 + 1) * 3600; i = pos.get(t_on - 3600)
            if i is None: continue
            side = t["side"] if kw["dir"] == "searah" else -t["side"]
            if kw["entry"] == "market":
                px = H["c"][i]; o = order(P.name, "B3", side, "market", px, px - side * kw["sl"] * a, px + side * kw["tp"] * a, t_on)
            else:   # limit di level asal breakout (entry trade pemicu)
                px = t["entry"]; o = order(P.name, "B3", side, "limit", px, px - side * kw["sl"] * a, px + side * kw["tp"] * a, t_on, t_off=t_on + 5 * 3600)
            out.setdefault(d, []).append(o)
        return out
    return gen


if __name__ == "__main__":
    duka = [B.load(p) for p in ALL]; nd = (max(int(P.days[-1]) for P in duka) - min(int(P.days[0]) for P in duka))
    os.environ["FX_DATA"] = "data_setra/{pair}_1h.json.gz"; setra = [B.load(p) for p in ALL]
    if sys.argv[1] == "gabung":
        part, nparts = int(sys.argv[2]), int(sys.argv[3]); rows = []
        U = [dict(exp=e, slm=a, tpm=b, be=c, dow=w) for e in (7, 10) for (a, b, c) in ((0.4, 0.4, 0.5), (0.4, 0.8, 0.0), (0.3, 0.6, 0.5), (0.5, 0.5, 0.3)) for w in ("mon", "none")]
        S = [dict(sl=a, tp=b, senin=s, at=at) for a in (0.3, 0.6) for b in (0.8, 1.2, 1.6) for s in (True, False) for at in (0,)]
        for k, (u, s_) in enumerate(itertools.product(U, S)):
            if k % nparts != part: continue
            UK = dict(dist=9.0, vol="none", **u)
            tr = build(duka, UK, s_); ts = build(setra, UK, s_); st = stat(tr, nd)
            rows.append(dict(u=u, s=s_, pf=st["pf"], pf_is=st["pf_is"], pf_oos=st["pf_oos"], pf_setra=pf(ts)[0], R=st["R"], dd=st["dd"],
                             wr=st["wr"], pw=st["pw"], pos=st["pos"], ny=st["ny"], worst=st["worst"], nw=st["nw"], years=st["years"]))
        json.dump(rows, open(f"/tmp/p7_{part}.json", "w"), default=float); print("selesai", part, len(rows))
    else:
        UK = json.loads(os.environ["UK"]); SK = json.loads(os.environ["SK"])
        bd = build(duka, UK, SK); bs = build(setra, UK, SK); sb = stat(bd, nd)
        print("UTAMA+SUSULAN:", line(sb), flush=True); rows = []
        grid = dict(on=["tp", "be", "sl"], dir=["searah", "balik"], entry=["market", "limit"], sl=[0.2, 0.4, 0.6], tp=[0.3, 0.6, 1.0])
        for vals in itertools.product(*grid.values()):
            kw = dict(zip(grid, vals))
            a = P6.run_gen(duka, bot3_gen(kw, bd)); b = P6.run_gen(setra, bot3_gen(kw, bs))
            if not a: continue
            s = stat(sorted(a, key=lambda x: x["t"]), nd); ps = pf(b)[0]
            ok = s["pf_is"] > 1.05 and s["pf_oos"] > 1.05 and ps > 1.0
            tot = stat(sorted(bd + a, key=lambda x: x["t"]), nd)
            rows.append((ok, min(s["pf_is"], s["pf_oos"]), kw, ps, s, tot))
        rows.sort(key=lambda r: (r[0], r[1]), reverse=True)
        print("BOT-3 lolos:", sum(r[0] for r in rows), "dari", len(rows))
        for r in rows[:10]:
            print(("LOLOS " if r[0] else "gagal ") + f"{r[2]} Setra {r[3]:.2f} | " + line(r[4]) + "\n     GABUNG 3 BOT: " + line(r[5]), flush=True)
