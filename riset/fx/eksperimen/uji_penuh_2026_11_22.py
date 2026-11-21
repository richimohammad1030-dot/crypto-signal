"""Uji penuh FX MAJOR · 22 Nov 2026: 3 teratas saringan (ide 13, 14, 15). Ide 13 'BALAS tembus ulang ekstrem':
Setelah UTAMA/SUSULAN kena SL penuh sebelum 20:00 WIB: stop order SEARAH di ekstrem hari itu (high hari itu untuk BUY yang kalah,
low untuk SELL) yang terbentuk sampai candle SL selesai; SL 0,3 ATR D1, TP 0,6 ATR, berlaku s/d 23:00 WIB. Lot normal (bukan martingale).
Uji: IS 2015-22, OOS 2023-26, Setra, per tahun, gabungan 3 bot, signifikansi (riset/signifikansi.py), kepekaan, M5 (4 pair).
Pemakaian: python riset/fx/eksperimen/uji_penuh_2026_11_22.py"""
import os, sys, time, itertools
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(REPO, "riset"))
import numpy as np
import saringan_2026_11_22 as S
from saringan_2026_11_22 import B, F, order, ystat, fmt, juara, run, gen_after, SPLIT
import signifikansi as SG


def mk_rebreak(sl=0.3, tp=0.6, buf=0.0):
    def b(P, t, a, i, i0, d, t_on):
        H = P.h1; s = t["side"]
        ext = (H["h"][i0:i + 1].max() if s > 0 else H["l"][i0:i + 1].min()) + s * buf * a
        return order(P.name, "BALr", s, "stop", ext, ext - s * sl * a, ext + s * tp * a, t_on)
    return b


def load(pat, pairs=F.PAIRS):
    if pat: os.environ["FX_DATA"] = pat
    else: os.environ.pop("FX_DATA", None)
    return [x for x in (B.load(p) for p in pairs) if x is not None]


def ujung(data):
    return min(int(P.t[0]) for P in data) + 120 * 86400, max(int(P.t[-1]) for P in data) + 1


def blok(nama, J, X, lo, hi):
    sj, sx, sg = ystat(J, lo, hi), ystat(X, lo, hi), ystat(J + X, lo, hi)
    print(f"\n### {nama} ({time.strftime('%Y-%m', time.gmtime(lo))} .. {time.strftime('%Y-%m', time.gmtime(hi - 1))})")
    print("juara    :", fmt(sj)); print("BALAS    :", fmt(sx)); print("gabung   :", fmt(sg))
    return sj, sx, sg


def harian(tr, lo, hi):
    out = {}
    for t in tr:
        if lo <= t["t"] < hi: out[t["t_exit"] // 86400] = out.get(t["t_exit"] // 86400, 0) + t["R"]
    return out


IDE = {   # 3 teratas saringan IS menurut rasio R/DD gabungan (5,01 · 5,00 · 4,87 vs juara 4,75)
    "13 BALAS tembus ulang ekstrem (searah 0,3/0,6)": ("sl", lambda data: mk_rebreak()),
    "14 Pasang ulang setelah BE (stop di entry)": ("be", lambda data: S.b_rearm),
    "15 BALAS breakout palsu (balik 0,3/0,45)": ("sl", lambda data: S.mk_palsu({P.name: P for P in data})),
}


def arus(data, b3, ide):
    kind, mk = IDE[ide]
    return run(data, gen_after(b3[0] + b3[1], kind, mk(data)))


if __name__ == "__main__":
    t0 = time.time()
    duka = load(None); lo, hi = ujung(duka); lo = max(lo, 1420070400)
    setra = load("data_setra/{pair}_1h.json.gz"); l2, h2 = ujung(setra)
    p4 = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]
    h1_4 = load(None, p4); m5_4 = load("data_m5/{pair}_m5_*.json.gz", p4)
    b3 = juara(duka); J = sum(b3, []); b3s = juara(setra); Js = sum(b3s, [])
    b34, b3m = juara(h1_4), juara(m5_4)
    sj = ystat(J, lo, hi); tj = [(t["t_exit"], t["R"]) for t in J]
    for ide in IDE:
        X = arus(duka, b3, ide)
        print(f"\n## Uji penuh ide {ide}")
        blok("IS Dukascopy", J, X, lo, SPLIT); blok("OOS Dukascopy", J, X, SPLIT, hi); _, sx, sg = blok("Seluruh Dukascopy", J, X, lo, hi)
        print("Per tahun (R) juara | ide | gabung: " + " · ".join(f"{y} {sj['years'].get(y, 0):+.1f}|{sx['years'].get(y, 0):+.1f}|{sg['years'][y]:+.1f}" for y in sorted(sg["years"])))
        hj, hx = harian(J, lo, hi), harian(X, lo, hi); ks = sorted(set(hj) | set(hx))
        print(f"Korelasi R harian ide vs juara: {np.corrcoef([hj.get(k, 0) for k in ks], [hx.get(k, 0) for k in ks])[0, 1]:+.2f}")
        print("Per pair:", {p: round(float(sum(t['R'] for t in X if t['pair'] == p)), 1) for p in F.PAIRS})
        tg = [(t["t_exit"], t["R"]) for t in J + X]
        for lab, a_, b_ in (("IS", lo, SPLIT), ("OOS 2023-26", SPLIT, hi), ("Seluruh", lo, hi)):
            r = SG.banding(tj, tg, a_, b_)
            print(f"Signifikansi {lab}: P_rasio {r['P_rasio_lebih_baik']:.3f} · P_R {r['P_R_lebih_baik']:.3f} · R/thn {r['juara']['R_thn']} -> {r['penantang']['R_thn']} · "
                  f"rasio {r['juara']['rasio']} -> {r['penantang']['rasio']} · selisih R/thn 90% {r['selisih_R_thn_90']}")
        blok("Setra (sekali)", Js, arus(setra, b3s, ide), l2, h2)
        l3 = max(ujung(h1_4)[0], 1590969600)
        for lab, dd, bb in (("H1 4 pair", h1_4, b34), ("M5 4 pair", m5_4, b3m)):
            blok(lab, sum(bb, []), arus(dd, bb, ide), l3, ujung(dd)[1])
        if ide.startswith("13"):
            print("Kepekaan (IS | OOS PF):")
            for sl, tp, buf in [(0.2, 0.4, 0), (0.3, 0.45, 0), (0.3, 0.9, 0), (0.4, 0.6, 0), (0.4, 0.8, 0), (0.3, 0.6, 0.05)]:
                Y = run(duka, gen_after(b3[0] + b3[1], "sl", mk_rebreak(sl, tp, buf))); a_, b_ = ystat(Y, lo, SPLIT), ystat(Y, SPLIT, hi)
                print(f"  SL {sl} TP {tp} buf {buf}: IS PF {a_['pf']:.2f} {a_['avg']:+.3f}R n {a_['n']} | OOS PF {b_['pf']:.2f} {b_['avg']:+.3f}R n {b_['n']}")
    print(f"\nselesai {time.time() - t0:.0f}s")
