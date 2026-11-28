"""SKILL SNR FX · TAHAP 2 putaran 3 (sesi 29 Nov 2026): penilaian penantang saringan massal F012 (JARAK zona pantul di
arah TP sebagai bobot risiko). Penantang teratas: SUPDEM+SWING, zona < 1,5R dari entry -> risiko × 0,5, selain itu × 1.
Uji (ATURAN G): (1) signifikansi vs juara penuh & OOS; (2) WALK-FORWARD: tiap tahun Y >= 2017 pilih varian F012 terbaik
(rasio R/DD) dari tahun < Y saja, pakai di tahun Y; (3) tetangga parameter; (4) uji stres +0,05R; (5) validasi M5 (4 pair
2020-2026, simulasi di candle M5). Pemakaian: python riset/fx/eksperimen/skill_snr_fx_t2d.py"""
import os, sys, time, itertools
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(REPO, "riset"))
import numpy as np
import skill_snr_fx_t2 as T2
import skill_snr_fx_t2c as T2C
import backtest as B, fx_live as F
import signifikansi as SG

GRID = list(itertools.product((("SUPDEM",), ("SUPDEM", "SWING")), (0.75, 1.0, 1.5), (0.25, 0.5, 0.75), (1.0, 1.25, 1.5)))
TOP = (("SUPDEM", "SWING"), 1.5, 0.5, 1.0)


def jarak(raw, ZP, cats, d, wa, wb):
    out = []
    for t in raw:
        w = 1.0
        if t["strat"] in ("N3", "SUS") and abs(t["tp"] - t["entry"]) > 0:
            o = dict(side=t["side"], price=t["entry"], sl=t["sl"], tp=t["tp"], t_on=t["t"]); r0 = abs(t["entry"] - t["sl"])
            z = T2.di_jalur(ZP[t["pair"]], o, cats, 1, 0.15, 1.0)
            if z is not None and abs(z - t["entry"]) < d * r0: w = wa
            elif z is None: w = wb
        out.append(dict(t, R=t["R"] * w))
    return out


def yr(t): return time.gmtime(t["t_exit"]).tm_year


def rasio(tr):
    R = np.array([t["R"] for t in sorted(tr, key=lambda x: x["t_exit"])])
    if len(R) < 30: return -9
    eq = np.cumsum(R); dd = (np.maximum.accumulate(np.insert(eq, 0, 0))[1:] - eq).max()
    return R.sum() / max(dd, 1e-9)


def sig(J, X, m):
    r = SG.banding([(t["t_exit"], t["R"]) for t in J], [(t["t_exit"], t["R"]) for t in X], mulai=m)
    return f"P_rasio {r['P_rasio_lebih_baik']:.3f} · P_R {r['P_R_lebih_baik']:.3f} · R/thn {r['juara']['R_thn']}→{r['penantang']['R_thn']} · DD {r['juara']['DD']}→{r['penantang']['DD']}"


def baris(nm, X, END):
    a = T2C.stat(X, T2.T_IS0, T2.T_OOS); b = T2C.stat(X, T2.T_OOS, END); s = T2C.stat(X, T2.T_OOS, END, 0.05)
    print(f"{nm:<44} IS PF {a['pf']:.2f} R {a['R']:+.0f} DD {a['dd']:.1f} th- {a['neg']} | OOS PF {b['pf']:.2f} R {b['R']:+.0f} "
          f"DD {b['dd']:.1f} th- {b['neg']} | stres OOS PF {s['pf']:.2f}")


if __name__ == "__main__":
    t0 = time.time()
    data = [B.load(p) for p in F.PAIRS]; END = max(int(P.t[-1]) for P in data) + 1
    ZP = {P.name: T2.zona_pair(P) for P in data}
    J = T2.juara_snr(data, ZP)
    X = jarak(J, ZP, *TOP)
    print("== H1 Dukascopy 2015-2026 ==")
    baris("JUARA", J, END); baris("F012 teratas (SUPDEM+SWING <1,5R w0,5)", X, END)
    print("signifikansi penuh:", sig(J, X, T2.T_IS0)); print("signifikansi OOS  :", sig(J, X, T2.T_OOS))
    print("\nTetangga (zona < d R, w):")
    for d, wa in itertools.product((1.0, 1.5, 2.0), (0.25, 0.5, 0.75)):
        baris(f"  SUPDEM+SWING <{d}R w{wa}", jarak(J, ZP, ("SUPDEM", "SWING"), d, wa, 1.0), END)
    print("\nWalk-forward (pilih varian terbaik dari tahun sebelumnya, 54 varian):")
    V = {g: jarak(J, ZP, *g) for g in GRID}
    wf = [t for t in J if yr(t) < 2017]; pilih = {}
    for Y in range(2017, time.gmtime(END).tm_year + 1):
        g = max(GRID, key=lambda g: rasio([t for t in V[g] if yr(t) < Y]))
        pilih[Y] = g; wf += [t for t in V[g] if yr(t) == Y]
    print("  pilihan per tahun:", {Y: f"{'+'.join(g[0])}<{g[1]}R w{g[2]} b{g[3]}" for Y, g in pilih.items()})
    baris("WF F012", wf, END)
    print("  signifikansi WF 2017+:", sig(J, wf, 1483228800)); print("  signifikansi WF OOS  :", sig(J, wf, T2.T_OOS))
    yj = {}; yw = {}
    for t in J: yj[yr(t)] = yj.get(yr(t), 0) + t["R"]
    for t in wf: yw[yr(t)] = yw.get(yr(t), 0) + t["R"]
    print("  R per tahun juara vs WF:", {Y: (round(yj[Y], 1), round(yw.get(Y, 0), 1)) for Y in sorted(yj)})
    print("\nPenyebab SL juara yang dikenai bobot 0,5 (mitigasi vs pemenang ikut terpotong):")
    for k, lbl in ((lambda t: t["R"] <= -0.5, "SL"), (lambda t: t["R"] > 0.05, "menang")):
        a = [(t, x) for t, x in zip(J, X) if t["strat"] in ("N3", "SUS") and k(t)]
        print(f"  {lbl}: {sum(1 for t, x in a if abs(x['R'] - t['R']) > 1e-9)}/{len(a)} dikurangi")
    print("\n== Validasi M5 (Dukascopy M5 2020-2026) ==")
    os.environ["FX_DATA"] = "data_m5/{pair}_m5_*.json.gz"
    dm = [P for P in (B.load(p) for p in F.PAIRS) if P is not None]
    print("  pair M5:", [P.name for P in dm])
    ZM = {P.name: T2.zona_pair(P) for P in dm}
    JM = T2.juara_snr(dm, ZM); XM = jarak(JM, ZM, *TOP)
    Jh = [t for t in J if t["pair"] in ZM and t["t_exit"] >= 1577836800]; Xh = jarak(Jh, ZP, *TOP)
    for nm, tr in (("JUARA H1 (pair sama, 2020+)", Jh), ("F012 H1", Xh), ("JUARA M5", JM), ("F012 M5", XM)):
        s = T2C.stat(tr, 1577836800, END); print(f"  {nm:<30} n{s['n']} PF {s['pf']:.2f} R {s['R']:+.0f} DD {s['dd']:.1f} rasio {s['rasio']:.2f} th- {s['neg']}")
    print(f"waktu {time.time() - t0:.0f} dtk")
