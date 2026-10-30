"""Pindai mean reversion XAU jam 07:00 WIB (tutup 23:00) - lanjutan strat_scan (31 Okt 2026). SELEKSI HANYA 2015-2021.
Indikator (H1, close 07:00): RSI(2), RSI(3), RSI(5), jarak close dari EMA20 H1 dalam ATR. Ambang dibuat dari kuantil 2015-2021
agar frekuensi bisa diatur (hanya varian >= 3 trade/minggu di periode pilih yang dinilai). Arah: fade (beli saat oversold).
Opsi filter tren EMA200 H1 (hanya fade searah tren / tanpa filter). Pemakaian: python mr_scan.py <xau_sambung.json>"""
import sys, json, itertools, pickle
import numpy as np
import audit_mesin as m
import strat_mesin as sm

D = m.muat(sys.argv[1]); T, O, H, L, C = D
A = np.array(m.atr(list(H), list(L), list(C), 14)); HR = ((T // 3600) % 24).astype(int)
E200 = np.array(m.ema(C, 200)); E20 = np.array(m.ema(C, 20))


def rsi(n):
    d = np.diff(C, prepend=C[0]); up, dn = np.where(d > 0, d, 0), np.where(d < 0, -d, 0)
    a = 1 / n; au = np.zeros(len(C)); ad = np.zeros(len(C))
    for j in range(1, len(C)):
        au[j] = au[j - 1] + a * (up[j] - au[j - 1]); ad[j] = ad[j - 1] + a * (dn[j] - ad[j - 1])
    return 100 - 100 / (1 + au / np.maximum(ad, 1e-12))


IND = {"RSI2": rsi(2), "RSI3": rsi(3), "RSI5": rsi(5), "Z-EMA20": -(C - E20) / np.maximum(A, 1e-9) * 25 + 50}
# Z-EMA20 dipetakan ke skala mirip RSI (rendah = jauh di bawah EMA = oversold)
pl = [i for i in np.flatnonzero(HR == sm.PLACE) if 250 <= i and T[i] < m.ts("2022-01-01")]
res = {}
for ind, X in IND.items():
    v = X[pl]
    for q in (0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50):     # bagian hari di tiap ekor -> frekuensi ±2q
        lo_, hi_ = np.quantile(v, q), np.quantile(v, 1 - q)
        for filt in ("tanpa", "searah tren"):
            def arah(i, X=X, lo_=lo_, hi_=hi_, filt=filt):
                d = 1 if X[i] <= lo_ else (-1 if X[i] >= hi_ else 0)
                if d and filt == "searah tren" and d != (1 if C[i] > E200[i] else -1): return 0
                return d
            for masuk, k in (("market", 0), ("limit", 0.25)):
                rc = (lambda i, arah=arah: [(arah(i), "market", None)] if arah(i) else None) if masuk == "market" else \
                     (lambda i, arah=arah, k=k: [(arah(i), "limit", C[i] - arah(i) * k * A[i])] if arah(i) else None)
                for sl, tp in itertools.product((2.0, 2.5, 3.0, 4.0), (1.0, 1.5, 2.0, None)):
                    tr = sm.jalan(D, A, rc, sl=sl, tp=tp)
                    key = (ind, q, filt, masuk, sl, tp)
                    res[key] = (sm.ringkas(tr, *m.PILIH), tr, (round(float(lo_), 2), round(float(hi_), 2)))
print(len(res), "varian")
SLs, TPs = (2.0, 2.5, 3.0, 4.0), (1.0, 1.5, 2.0, None)


def nb(k):
    ind, q, f, ms, sl, tp = k; out = []
    for s2 in SLs:
        if abs(SLs.index(s2) - SLs.index(sl)) == 1: out.append((ind, q, f, ms, s2, tp))
    for t2 in TPs:
        if abs(TPs.index(t2) - TPs.index(tp)) == 1: out.append((ind, q, f, ms, sl, t2))
    for q2 in (q - 0.05, q + 0.05):
        q2 = round(q2, 2)
        if (ind, q2, f, ms, sl, tp) in res: out.append((ind, q2, f, ms, sl, tp))
    return out


rows = []
for k, (s, tr, th) in res.items():
    nbs = nb(k)
    rows.append(dict(k=k, s=s, th=th, lulus=sm.lulus(s), skor=min(s["ratio"], np.mean([res[j][0]["ratio"] for j in nbs])),
                     nb_lulus=sum(sm.lulus(res[j][0]) for j in nbs), nb_n=len(nbs)))
ok = sorted([r for r in rows if r["lulus"]], key=lambda r: -r["skor"])
print(f"Lulus kriteria pemilik di 2015-2021: {len(ok)}")
for r in ok[:25]:
    s = r["s"]
    print(f"skor {r['skor']:+.2f} tetangga lulus {r['nb_lulus']}/{r['nb_n']} | {r['k']} ambang {r['th']} | /mg={s['per_mg']:.1f} "
          f"win={s['wr']*100:.1f}% rr={s['rr']:.2f} pf={s['pf']:.2f} R/thn={s['rthn']:+.1f} DD={s['dd']:.1f} W/L={s['wmax']}/{s['lmax']} "
          f"thn+={s['thn_pos']}/{s['thn_n']} tanpa2%={s['tanpa2']:+.0f}")
pickle.dump({r["k"]: (res[r["k"]][1], r["th"]) for r in ok[:30]}, open("/tmp/data/mr_top.pkl", "wb"))
