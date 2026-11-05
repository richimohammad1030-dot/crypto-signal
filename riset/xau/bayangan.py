"""Catatan BAYANGAN bot XAU (31 Okt 2026): putar ulang semua strategi menu pada data Setra sejak LIVE_START XAU dan bandingkan
dengan catatan live (gold_state.json hist). Dipakai riset Jumat (uji maju) untuk menilai bobot/penggantian strategi.
Menu: BASELINE (live, MR+K6+susulan sejak 6 Nov 2026), Tanpa susulan (MR+K6), MR saja, K6 saja, juara lama (OCO 2 sisi), PENANTANG (RSI2 kuantil 30% SL 2,5 TP 2R + K6 SL 1,25 tanpa TP).
Pemakaian: python riset/xau/bayangan.py <repo> <xau_setra.json> <xau_dukascopy.json>"""
import sys, os, json
import numpy as np
REPO, SETRA, DUKA = sys.argv[1:4]
sys.path.insert(0, REPO); sys.path.insert(0, os.path.join(REPO, "riset", "xau", "eksperimen"))
import audit_mesin as m, multi_mesin as mm, kesehatan
D = m.sambung(m.muat(DUKA), m.muat(SETRA))          # Dukascopy hanya untuk pemanasan indikator
A = np.array(m.atr(list(D[2]), list(D[3]), list(D[4]), 14)); F = m.fitur(D, A)
mulai = kesehatan.LIVE_START["xau"]
sig30 = mm.sinyal_mr(D, mr_buy=38.49, mr_sell=74.72)   # kuantil 30%/70% 2015-2021 (multi_setel.py)
MENU = {
    "BASELINE (live)": mm.baseline(D, A, F),
    "Tanpa susulan": mm.baseline(D, A, F, sus=False),
    "MR SELL lama 71,22 (sblm #40)": mm.baseline(D, A, F, sig=mm.sinyal_mr(D, mr_sell=71.22)),
    "Connors MA200 (#42)": mm.baseline(D, A, F, sig=mm.sinyal_connors(D, 200)),
    "Connors MA100 (#42)": mm.baseline(D, A, F, sig=mm.sinyal_connors(D, 100)),
    "Hibrida MA100 (#42b)": mm.baseline(D, A, F, sig=mm.sinyal_hibrida(D, 100)),
    "Hibrida MA200 (#42b)": mm.baseline(D, A, F, sig=mm.sinyal_hibrida(D, 200)),
    "MR saja": mm.trades_mr(D, A),
    "K6 saja": mm.trades_k6(D, A, F),
    "Juara lama (OCO)": m.potong(m.replay(D, A=A)),
    "PENANTANG": mm.baseline(D, A, F, sig=sig30, mr=mm.trades_mr(D, A, sig30, sl=2.5, tp=2), k6=mm.trades_k6(D, A, F, sl=1.25, tp=None)),
}
print(f"Sejak {m.wib(mulai):%d %b %Y} (biaya 0,40 USD/trade):")
for nm, tr in MENU.items():
    tr = [x for x in tr if x["t0"] >= mulai]; r = m.net(tr)
    print(f"  {nm:<18} trade {len(tr):>3} · win {np.mean(r > 0)*100 if len(r) else 0:4.0f}% · total {r.sum() if len(r) else 0:+6.2f}R")
hist = [h for h in json.load(open(os.path.join(REPO, "gold_state.json"))).get("hist", []) if h[2] >= mulai]
print(f"  {'LIVE (catatan bot)':<18} trade {len(hist):>3} · total kotor {sum(h[6] for h in hist):+6.2f}R")
