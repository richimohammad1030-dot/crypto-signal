"""Mitigasi SL (ATURAN_BERSAMA G a-b), sesi 29 Nov 2026: kategori SEMUA SL juara di backtest Dukascopy H1 2015-2026
(kategori sama dengan riset/fx/harian_fx.py) + pola jam isi / jarak SL / rezim, dibanding trade menang pada kondisi sama.
Pemakaian: python riset/fx/eksperimen/sebab_sl_backtest_2026_11_29.py"""
import os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(REPO, "riset", "xau", "eksperimen")); sys.path.insert(0, os.path.join(REPO, "forex_major"))
import numpy as np
import skill_snr_fx_t2 as T2
import backtest as B, fx_live as F
from collections import Counter, defaultdict

data = [B.load(p) for p in F.PAIRS]; Pm = {P.name: P for P in data}
J = T2.juara_snr(data, {P.name: None for P in data})
kat = defaultdict(list); menang = []
for t in J:
    H = Pm[t["pair"]].h1; i0 = int(np.searchsorted(H["t"], t["t"])); i1 = int(np.searchsorted(H["t"], t["t_exit"]))
    r0 = abs(t["entry"] - t["sl"]); s = t["side"]
    if r0 <= 0: continue
    mfe = max(((H["h"][i] - t["entry"]) if s > 0 else (t["entry"] - H["l"][i])) for i in range(i0, min(i1 + 1, len(H["t"])))) / r0
    jam = (time.gmtime(t["t"]).tm_hour + 7) % 24
    if t["R"] <= -0.5:
        end = int(np.searchsorted(H["t"], t["t"] // 86400 * 86400 + 16 * 3600))
        tp_lalu = any((H["h"][i] >= t["tp"]) if s > 0 else (H["l"][i] <= t["tp"]) for i in range(i1 + 1, end))
        cepat = (t["t_exit"] - t["t"]) <= 2 * 3600
        k = ("SL lalu TP tercapai" if tp_lalu else "Breakout palsu (<=2 jam, MFE<0,3R)" if cepat and mfe < 0.3 else
             "Sempat untung >=0,5R lalu berbalik" if mfe >= 0.5 else "Berbalik perlahan")
        kat[k].append(dict(t, mfe=mfe, jam=jam))
    elif t["R"] > 0.05: menang.append(dict(t, mfe=mfe, jam=jam))
n = sum(len(v) for v in kat.values())
print(f"Juara Dukascopy 2015-2026: {len(J)} trade · SL penuh {n} · menang {len(menang)}")
for k, v in sorted(kat.items(), key=lambda kv: -len(kv[1])):
    st = Counter(x["strat"] for x in v)
    print(f"- {k}: {len(v)} ({len(v) / n:.0%}) per bot {dict(st)} · jam isi median {np.median([x['jam'] for x in v]):.0f} WIB")
print("\nPer jam isi (WIB) UTAMA+SUSULAN: SL vs menang")
semua_sl = [x for v in kat.values() for x in v]
for lo, hi in ((7, 10), (10, 13), (13, 16), (16, 19), (19, 23)):
    a = [x for x in semua_sl if lo <= x["jam"] < hi and x["strat"] in ("N3", "SUS")]
    b = [x for x in menang if lo <= x["jam"] < hi and x["strat"] in ("N3", "SUS")]
    Rs = [x["R"] for x in J if x["strat"] in ("N3", "SUS") and lo <= (time.gmtime(x["t"]).tm_hour + 7) % 24 < hi]
    print(f"  {lo:02d}-{hi:02d}: SL {len(a)} · menang {len(b)} · semua {len(Rs)} trade R/trade {np.mean(Rs) if Rs else 0:+.3f}")
print("\nSempat untung >=0,5R lalu berbalik: MFE median", round(float(np.median([x['mfe'] for x in kat['Sempat untung >=0,5R lalu berbalik']] or [0])), 2),
      "· menang MFE median", round(float(np.median([x['mfe'] for x in menang])), 2))
