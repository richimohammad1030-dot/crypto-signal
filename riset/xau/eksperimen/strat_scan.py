"""Pindai strategi alternatif XAU (31 Okt 2026) dalam jendela tetap 07:00-23:00 WIB. SELEKSI HANYA DI 2015-2021 dengan
kriteria pemilik (win >= 40%, PF > 1, >= 3 trade/minggu, kalah beruntun <= menang beruntun + 4, mayoritas tahun untung).
Literatur: pola jam emas (Donati & Jung, CBS), pembalikan overnight-intraday (Della Corte, Kosowski & Wang 2015),
momentum intraday (Gao, Han, Li & Zhou 2018; Baltussen dkk. 2021), RSI(2) (Connors), fade range Asia.
Pemakaian: python strat_scan.py <xau_sambung.json>  -> /tmp/data/strat_scan.json"""
import sys, json, itertools
import numpy as np
import audit_mesin as m
import strat_mesin as sm

D = m.muat(sys.argv[1]); T, O, H, L, C = D
A = np.array(m.atr(list(H), list(L), list(C), 14))
HR = ((T // 3600) % 24).astype(int)
E200 = m.ema(C, 200)
# RSI(2) close H1
dC = np.diff(C, prepend=C[0]); up = np.where(dC > 0, dC, 0); dn = np.where(dC < 0, -dC, 0)
au, ad = m.ema(up, 3), m.ema(dn, 3)          # Wilder n=2 ~ EMA alpha 1/2 -> span 3
RSI2 = 100 - 100 / (1 + au / np.maximum(ad, 1e-12))
# close 23:00 WIB hari sebelumnya
prev = np.full(len(T), -1); last = -1
for j in range(len(T)):
    prev[j] = last
    if HR[j] == sm.CLOSE: last = j
ON = np.array([(C[i] - C[prev[i]]) / A[i] if prev[i] >= 0 and A[i] > 0 else 0.0 for i in range(len(T))])   # gerak "malam" dalam ATR
rng = lambda i: (H[i - 2:i + 1].max(), L[i - 2:i + 1].min())
tren = lambda i: 1 if C[i] > E200[i] else -1


def arah_ke_order(fn, masuk, k):
    def r(i):
        d = fn(i)
        if not d: return None
        if masuk == "market": return [(d, "market", None)]
        return [(d, "limit", C[i] - d * k * A[i])]
    return r


ATURAN = {}
ATURAN["selalu SELL"] = lambda i: -1
ATURAN["selalu BUY"] = lambda i: 1
for th in (0.0, 0.5, 1.0):
    ATURAN[f"balik overnight >{th}ATR"] = lambda i, th=th: -int(np.sign(ON[i])) if abs(ON[i]) > th else 0
    ATURAN[f"momentum overnight >{th}ATR"] = lambda i, th=th: int(np.sign(ON[i])) if abs(ON[i]) > th else 0
ATURAN["tren EMA200"] = tren
ATURAN["pullback searah tren (overnight lawan tren)"] = lambda i: tren(i) if np.sign(ON[i]) == -tren(i) else 0
for lo_, hi_ in ((50, 50), (30, 70), (15, 85)):
    ATURAN[f"RSI2 fade {lo_}/{hi_}"] = lambda i, lo_=lo_, hi_=hi_: 1 if RSI2[i] < lo_ else (-1 if RSI2[i] > hi_ else 0)
ATURAN[f"RSI2 fade searah tren"] = lambda i: tren(i) if (tren(i) == 1 and RSI2[i] < 30) or (tren(i) == -1 and RSI2[i] > 70) else 0

RENCANA = {}
for nm, fn in ATURAN.items():
    RENCANA[(nm, "market")] = arah_ke_order(fn, "market", 0)
    for k in (0.25, 0.5):
        RENCANA[(nm, f"limit {k}ATR")] = arah_ke_order(fn, "limit", k)
for b in (0.0, 0.25, 0.5):
    RENCANA[(f"fade range Asia OCO", f"limit {b}ATR di luar range")] = \
        lambda i, b=b: [(1, "limit", rng(i)[1] - b * A[i]), (-1, "limit", rng(i)[0] + b * A[i])]
    RENCANA[(f"fade range searah tren", f"limit {b}ATR di luar range")] = \
        lambda i, b=b: [(1, "limit", rng(i)[1] - b * A[i])] if tren(i) == 1 else [(-1, "limit", rng(i)[0] + b * A[i])]

SL = [1.0, 1.5, 2.0, 3.0]
TP = [0.5, 0.75, 1.0, 1.5, 2.0, None]
res = {}
for (key, rc), sl, tp in itertools.product(RENCANA.items(), SL, TP):
    tr = sm.jalan(D, A, rc, sl=sl, tp=tp)
    res[(key, sl, tp)] = (sm.ringkas(tr, *m.PILIH), tr)
print(len(res), "varian")


def nb(k):
    key, sl, tp = k; out = []
    for s2 in (SL[j] for j in (SL.index(sl) - 1, SL.index(sl) + 1) if 0 <= j < len(SL)): out.append((key, s2, tp))
    for t2 in (TP[j] for j in (TP.index(tp) - 1, TP.index(tp) + 1) if 0 <= j < len(TP)): out.append((key, sl, t2))
    return out


rows = []
for k, (s, _) in res.items():
    nr = [res[j][0]["ratio"] for j in nb(k)]
    rows.append(dict(k=k, s=s, skor=min(s["ratio"], np.mean(nr)), lulus=sm.lulus(s), nb_lulus=sum(sm.lulus(res[j][0]) for j in nb(k))))
ok = sorted([r for r in rows if r["lulus"]], key=lambda r: -r["skor"])
print(f"Lulus kriteria pemilik di 2015-2021: {len(ok)} dari {len(rows)}")
for r in ok[:20]:
    s = r["s"]
    print(f"skor {r['skor']:+.2f} tetangga lulus {r['nb_lulus']} | {r['k']} | n={s['n']} /mg={s['per_mg']:.1f} win={s['wr']*100:.1f}% "
          f"rr={s['rr']:.2f} pf={s['pf']:.2f} R/thn={s['rthn']:+.1f} DD={s['dd']:.1f} W/L={s['wmax']}/{s['lmax']} thn+={s['thn_pos']}/{s['thn_n']}")
# juga: yang terbaik tanpa syarat (untuk melihat seberapa dekat)
print("\nTop 10 rasio R/DD tanpa syarat (2015-2021):")
for r in sorted(rows, key=lambda r: -r["s"]["ratio"])[:10]:
    s = r["s"]
    print(f"{r['k']} | n={s['n']} /mg={s['per_mg']:.1f} win={s['wr']*100:.1f}% pf={s['pf']:.2f} R/thn={s['rthn']:+.1f} DD={s['dd']:.1f} "
          f"W/L={s['wmax']}/{s['lmax']} thn+={s['thn_pos']}/{s['thn_n']} lulus={r['lulus']}")
json.dump([[list(map(str, r["k"])), float(r["skor"]), bool(r["lulus"])] for r in ok], open("/tmp/data/strat_lulus.json", "w"))
import pickle; pickle.dump({r["k"]: res[r["k"]][1] for r in ok[:40]}, open("/tmp/data/strat_top.pkl", "wb"))
