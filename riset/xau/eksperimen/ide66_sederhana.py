"""Ide #66 (13 Nov 2026, dari LANGKAH 1): struktur sederhana = KOMBINASI #58 (prioritas, SL 1,5 ATR) + MR TANPA hibrida dengan
ambang lama (BUY <= 43,76 / SELL >= 71,22 atau >= 85) + K6 + susulan. Pemicu: di 2005-2014 (data belum dilihat) versi MR SELL 71,22
paling tahan (3/10 tahun minus, terburuk -8, DD 24R) walau R/thn lebih kecil. CATATAN: dipicu setelah melihat 2005-2014 ->
2004-2014 tidak lagi bersih untuk ide ini; tanpa parameter baru (tidak ada pemilihan), jadi dilaporkan apa adanya per tahun.
Pemakaian: python ide66_sederhana.py <xau_2004.json> <ambigu.json>"""
import sys
import numpy as np
sys.argv = sys.argv[:3]
exec(open("simetris.py").read().split("KAND = {}")[0])
sk = mm.sinyal_kombo(D)
def sistem_k(sig_mr):
    sh = {i: d for i, d in sig_mr.items() if i not in sk}
    mr = [dict(x, strat0="KOMBO") for x in mm.trades_mr(D, A, sk, sl=m.gb.KOMBO_SL_ATR)] + [dict(x, strat0="MR") for x in mm.trades_mr(D, A, sh)]
    return mm.baseline(D, A, F, ambigu=AMB, sig={**sig_mr, **sk}, mr=mr)
VAR = {"BOT LIVE": BASE, "KOMBO + MR 43,76/71,22 (tanpa hibrida)": sistem_k(mm.sinyal_mr(D, mr_sell=71.22)),
       "KOMBO + MR 43,76/85 (tanpa hibrida)": sistem_k(mm.sinyal_mr(D))}
jl = [(int(x["t1"]), float(v)) for x, v in zip(BASE, m.net(BASE))]
for nm, G in VAR.items():
    G = sorted([x for x in G if m.wib(x["t0"]).year >= 2005], key=lambda z: z["t1"]); r = m.net(G)
    th = {y: 0.0 for y in range(2005, 2027)}
    for x, v in zip(G, r): th[m.wib(x["t0"]).year] += v
    v = np.array(list(th.values())); c = np.cumsum(r); dd = (np.maximum.accumulate(np.concatenate([[0], c]))[1:] - c).max()
    gl = [(int(x["t1"]), float(q)) for x, q in zip(G, r)]
    P = {p: sg.banding(jl, gl, int(m.ts(a)), int(m.ts(b)))["P_rasio_lebih_baik"] for p, (a, b) in
         {"05-14": ("2005-01-01", "2015-01-01"), "11-26": ("2011-01-01", "2027-01-01"), "Setra": ("2025-02-01", "2027-01-01")}.items()}
    print(f"{nm:<40} " + " ".join(f"{y % 100}:{q:+.0f}" for y, q in th.items()))
    print(f"{'':<40} 05-26 R/thn {v.mean():+5.1f} · minus {(v < 0).sum()}/22 · terburuk {v.min():+.0f} · sd {v.std():.1f} · DD {dd:.0f}R · "
          f"R/trade {r.mean():+.3f} · P rasio vs live " + " ".join(f"{k} {q:.2f}" for k, q in P.items()))
