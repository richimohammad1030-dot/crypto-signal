"""Riset putaran 6 — struktur 3 bot sesuai pemilik (20 Nov 2026), spread asli Exness Standard Cent (+0,2 pip cadangan):
  UTAMA   : sinyal 07:00 WIB (N3 breakout level minggu lalu, Selasa-Jumat), order berlaku sampai jam kadaluarsa.
  SUSULAN : pair yang order UTAMA-nya tidak terisi sampai kadaluarsa -> dicek di candle H1 yang close 09:00, 11:00, ..., 21:00 WIB
            (seperti susulan XAU) setelah kadaluarsa.
  BALAS   : setelah UTAMA/SUSULAN kena SL penuh (R <= -0,5) sebelum 21:00 WIB -> sinyal balas di candle berikutnya. Ukuran lot
            balas diatur agar TP-nya menutup sebagian loss (dipetakan di akhir).
Seleksi tiap bot: PF IS (2015-2022) > 1,05, PF OOS (2023-2026) > 1,05, PF Setra > 1,0.
Pemakaian: python forex_major/riset_putaran6.py [utama|susulan|balas]"""
import itertools, json, os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import backtest as B
from backtest import order, atr, rsi, ema, prev_daily
from riset_putaran2 import SPLIT, pf
import riset_putaran4 as R4
from riset_putaran5 import stat, line

ROOT = os.path.dirname(os.path.abspath(__file__)); ALL = R4.ALL
# spread asli Exness Standard Cent (screenshot pemilik 20 Nov 2026, sesi London) + 0,2 pip cadangan
B.SPREAD.update({"EURUSD": 1.0, "GBPUSD": 1.2, "USDJPY": 1.2, "AUDUSD": 1.1, "NZDUSD": 1.6, "USDCAD": 1.8, "USDCHF": 1.5})
SUS_OPEN_UTC = (1, 3, 5, 7, 9, 11, 13)          # candle H1 yang close 09:00, 11:00, ..., 21:00 WIB


def run_gen(data, gen):
    out = []
    for P in data:
        for d, lst in gen(P).items(): out += R4.simulate_be(P, lst, d) if lst and lst[0].get("be") else B.simulate_pair(P, lst, d)
    return out


# ---------------- UTAMA ----------------
def utama_gen(kw):
    exp = kw.get("exp", 16); base = {k: v for k, v in kw.items() if k != "exp"}
    def gen(P):
        out = R4.n3o(P, **base)
        for d, lst in out.items():
            for o in lst: o["t_off"] = d * 86400 + exp * 3600
        return out
    return gen

def utama(data, kw):
    B.MAX_DAY = 2; tr = B.portfolio(run_gen(data, utama_gen(kw))); B.MAX_DAY = 4
    return tr


# ---------------- SUSULAN ----------------
def susulan_gen(kw, filled, exp, has_order):
    """filled: set (pair, hari) yang UTAMA terisi. Aktif di pair-hari tanpa isi UTAMA, setelah jam kadaluarsa."""
    def gen(P):
        idx, D = prev_daily(P); A = atr(D); E = ema(D["c"], 50); H = P.h1; r2 = rsi(H["c"], 2); AH = atr(H, 14)
        pos = {int(t): i for i, t in enumerate(H["t"])}; out = {}
        for d, j in idx.items():
            if j < 60 or (P.name, d) in filled: continue
            if kw["scope"] == "ada_order" and (P.name, d) not in has_order: continue
            if kw["scope"] == "selasa_jumat" and (d + 3) % 7 == 0: continue
            t0 = d * 86400; trend = 1 if D["c"][j] > E[j] else -1
            for hh in SUS_OPEN_UTC:
                if (hh + 1) < exp: continue                       # keputusan setelah kadaluarsa UTAMA
                i = pos.get(t0 + hh * 3600)
                if i is None: continue
                side = 1 if r2[i] <= kw["lo"] else -1 if r2[i] >= 100 - kw["lo"] else 0
                if kw["kind"] == "rsi2_tren" and side != trend: side = 0
                if side:
                    px = H["c"][i]; sl = px - side * kw["sl"] * AH[i]
                    out[d] = [order(P.name, "SUS", side, "market", px, sl, px + side * kw["tp"] * abs(px - sl), t0 + (hh + 1) * 3600)]
                    break
                if kw["once"]: break
        return out
    return gen


# ---------------- BALAS ----------------
def balas_gen(kw, losers):
    trig = {}
    for t in losers:
        if t["R"] <= -0.5 and t["why"] == "sl" and (t["t_exit"] % 86400) < 14 * 3600:
            trig.setdefault((t["pair"], t["t_exit"] // 86400), t)
    def gen(P):
        idx, D = prev_daily(P); A = atr(D); H = P.h1; AH = atr(H, 14); pos = {int(x): i for i, x in enumerate(H["t"])}; out = {}
        for (pair, d), t in trig.items():
            if pair != P.name or d not in idx: continue
            t_on = (t["t_exit"] // 3600 + 1) * 3600; i = pos.get(t_on - 3600)
            if i is None: continue
            a = AH[i] if kw["atr"] == "h1" else A[idx[d]]
            side = -t["side"] if kw["dir"] == "balik" else t["side"]
            if kw["entry"] == "market":
                px = H["c"][i]; o = order(P.name, "BAL", side, "market", px, px - side * kw["sl"] * a, px + side * kw["tp"] * a, t_on)
            else:                                    # limit di harga entry trade yang kalah (retest level)
                px = t["entry"]; o = order(P.name, "BAL", side, "limit", px, px - side * kw["sl"] * a, px + side * kw["tp"] * a, t_on, t_off=t_on + 4 * 3600)
            out.setdefault(d, []).append(o)
        return out
    return gen


def check(tr, ts, nd):
    s = stat(sorted(tr, key=lambda x: x["t"]), nd) if tr else dict(n=0); ps = pf(ts)[0] if ts else 0
    ok = bool(s["n"]) and s["pf_is"] > 1.05 and s["pf_oos"] > 1.05 and ps > 1.0
    return s, ps, ok


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "utama"
    if what == "susulan2": pass
    duka = [B.load(p) for p in ALL]; nd = (max(int(P.days[-1]) for P in duka) - min(int(P.days[0]) for P in duka))
    os.environ["FX_DATA"] = "data_setra/{pair}_1h.json.gz"; setra = [B.load(p) for p in ALL]
    MAIN = dict(dist=9.0, vol="none", dow="mon", slm=0.4, tpm=0.4, be=0.5)
    if what == "utama":
        for exp, (slm, tpm, be) in itertools.product([7, 10, 13, 16], [(0.4, 0.4, 0.5), (0.4, 1.2, 0.5), (0.4, 0.8, 0.0), (0.6, 0.8, 0.3)]):
            kw = dict(MAIN, slm=slm, tpm=tpm, be=be, exp=exp)
            s, ps, ok = check(utama(duka, kw), utama(setra, kw), nd)
            print(("LOLOS " if ok else "gagal ") + f"UTAMA kadaluarsa {exp + 7:02d}:00 WIB SL {slm} TP {tpm} BE {be}: Setra {ps:.2f} | " + line(s), flush=True)
    else:
        UK = json.loads(os.environ.get("UTAMA_KW", json.dumps(dict(MAIN, exp=16))))
        exp = UK["exp"]; res = {}
        for lab, data in (("d", duka), ("s", setra)):
            m = utama(data, UK); g = utama_gen(UK)
            has = {(P.name, d) for P in data for d in g(P)}
            res[lab] = (m, {(t["pair"], t["t"] // 86400) for t in m}, has)
        if what == "susulan":
            grid = dict(kind=["rsi2", "rsi2_tren"], lo=[10, 25], sl=[1.5, 3.0], tp=[0.5, 1.0], once=[True, False], scope=["semua", "ada_order", "selasa_jumat"])
            keys = list(grid)
            for vals in itertools.product(*[grid[k] for k in keys]):
                kw = dict(zip(keys, vals))
                a = run_gen(duka, susulan_gen(kw, res["d"][1], exp, res["d"][2])); b = run_gen(setra, susulan_gen(kw, res["s"][1], exp, res["s"][2]))
                s, ps, ok = check(a, b, nd)
                print(("LOLOS " if ok else "gagal ") + f"SUSULAN {kw}: Setra {ps:.2f} | " + (line(s) if s["n"] else "0 trade"), flush=True)
        if what == "balas":
            SK = json.loads(os.environ.get("SUS_KW", "null"))
            for lab, data in (("d", duka), ("s", setra)):
                los = list(res[lab][0])
                if SK: los += run_gen(data, susulan_gen(SK, res[lab][1], exp, res[lab][2]))
                res[lab] = res[lab] + (los,)
            grid = dict(dir=["balik", "searah"], entry=["market", "retest"], atr=["h1", "d1"], sl=[0.5, 1.0, 2.0], tp=[0.5, 1.0])
            keys = list(grid)
            for vals in itertools.product(*[grid[k] for k in keys]):
                kw = dict(zip(keys, vals))
                if kw["atr"] == "d1": kw = dict(kw, sl=kw["sl"] * 0.3, tp=kw["tp"] * 0.3)
                a = run_gen(duka, balas_gen(kw, res["d"][3])); b = run_gen(setra, balas_gen(kw, res["s"][3]))
                s, ps, ok = check(a, b, nd)
                print(("LOLOS " if ok else "gagal ") + f"BALAS {kw}: Setra {ps:.2f} | " + (line(s) if s["n"] else "0 trade"), flush=True)


# ---------------- SUSULAN v2: pasang ulang level breakout mingguan setelah UTAMA kadaluarsa ----------------
def susulan_rearm_gen(kw, filled, exp):
    """Pair-hari yang UTAMA tidak terisi: di jam keputusan pertama setelah kadaluarsa (close 09:00..21:00 WIB), pasang ulang
    stop order di level minggu lalu (OCO) dengan SL/TP sendiri; berlaku sampai 23:00 WIB. Hanya bila harga belum menembus level."""
    def gen(P):
        idx, D = prev_daily(P); A = atr(D); H = P.h1; pos = {int(t): i for i, t in enumerate(H["t"])}; out = {}
        wk = (D["t"] // 86400 + 3) // 7
        for d, j in idx.items():
            if j < 110 or (P.name, d) in filled or (d + 3) % 7 == 0: continue
            hh = next((h for h in SUS_OPEN_UTC if h + 1 >= exp), None)
            if hh is None: continue
            t0 = d * 86400; i = pos.get(t0 + hh * 3600)
            if i is None: continue
            m = wk == ((d + 3) // 7 - 1)
            if not m.any(): continue
            ph, pl = D["h"][m].max(), D["l"][m].min(); a = A[j]; t_on = t0 + (hh + 1) * 3600
            i0 = pos.get(t0)
            if i0 is None: continue
            hi_today, lo_today = H["h"][i0:i + 1].max(), H["l"][i0:i + 1].min(); lst = []
            if D["h"][j] < ph and hi_today < ph: lst.append(order(P.name, "SUS", 1, "stop", ph, ph - kw["sl"] * a, ph + kw["tp"] * a, t_on, oco=("SUS", d)))
            if D["l"][j] > pl and lo_today > pl: lst.append(order(P.name, "SUS", -1, "stop", pl, pl + kw["sl"] * a, pl - kw["tp"] * a, t_on, oco=("SUS", d)))
            if lst: out[d] = lst
        return out
    return gen


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "susulan2":
    for exp in (7, 10):
        UK = dict(MAIN, slm=0.4, tpm=0.8 if exp == 10 else 0.4, be=0.0 if exp == 10 else 0.5, exp=exp)
        md = utama(duka, UK); ms = utama(setra, UK)
        fd = {(t["pair"], t["t"] // 86400) for t in md}; fs = {(t["pair"], t["t"] // 86400) for t in ms}
        print(f"\nUTAMA kadaluarsa {exp + 7}:00 WIB {UK}: " + line(stat(md, nd)), flush=True)
        for sl, tp in itertools.product([0.3, 0.4, 0.6], [0.4, 0.8, 1.2]):
            kw = dict(sl=sl, tp=tp)
            a = run_gen(duka, susulan_rearm_gen(kw, fd, exp)); b = run_gen(setra, susulan_rearm_gen(kw, fs, exp))
            s, ps, ok = check(a, b, nd)
            tot = stat(sorted(md + a, key=lambda x: x["t"]), nd)
            print(("LOLOS " if ok else "gagal ") + f"SUSULAN pasang-ulang {kw}: Setra {ps:.2f} | " + (line(s) if s["n"] else "0") + "\n      GABUNG: " + line(tot), flush=True)
