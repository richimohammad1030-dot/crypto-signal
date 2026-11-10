"""Ide #59 (10 Nov 2026, pemilik): cara keluar trade KOMBINASI (#58): tanpa TP (live) vs TP keras 2-10R vs trailing SL
(jarak k×ATR dari harga terbaik, aktif segera / setelah +1R, + breakeven) dengan/tanpa TP 10R. SL awal 1,5 ATR, tutup 23:00.
Trailing diperbarui di close tiap candle H1 (berlaku candle berikutnya; konservatif). Pilih 2015-21; konfirmasi 2005-14,
2022-Jan25, Setra. Pemakaian: python kombo_keluar.py <xau_2004.json>"""
import sys, itertools
import numpy as np
import audit_mesin as m, strat_mesin as sm, multi_mesin as mm
D = m.muat(sys.argv[1]); T, O, H, L, C = D; N = len(T)
A = np.array(m.atr(list(H), list(L), list(C), 14)); HR = ((T // 3600) % 24).astype(int)
sig = {i: d for i, d in mm.sinyal_kombo(D).items() if i >= 2500}
def kelola(i, d, tp, trail, aktif, be):
    j = i + 1; e = O[j]; r0 = 1.5 * A[i]; sl = e - d * r0; best = e; mfe = 0.0
    tpp = e + d * tp * r0 if tp else None
    for q in range(j, min(j + 30, N)):
        if (d == 1 and L[q] <= sl) or (d == -1 and H[q] >= sl): return (sl - e) * d, mfe
        if q > j and tpp is not None and ((d == 1 and H[q] >= tpp) or (d == -1 and L[q] <= tpp)): return (tpp - e) * d, mfe
        mfe = max(mfe, ((H[q] if d == 1 else L[q]) - e) * d / r0)
        if HR[q] == sm.CLOSE: return (C[q] - e) * d, mfe
        best = max(best, H[q]) if d == 1 else min(best, L[q])
        untung = (best - e) * d / r0
        if be and untung >= 1: sl = max(sl, e) if d == 1 else min(sl, e)
        if trail and untung >= aktif:
            ns = best - d * trail * A[i]
            sl = max(sl, ns) if d == 1 else min(sl, ns)
    return (C[min(j + 29, N - 1)] - e) * d, mfe
PER = (("2005-14", "2005-01-01", "2015-01-01"), ("pilih15-21", "2015-01-01", "2022-01-01"), ("22-Jan25", *m.UJI), ("Setra", m.KONF[0], None))
VAR = [("LIVE tanpa TP", None, 0, 0, False)] + [(f"TP keras {tp}R", tp, 0, 0, False) for tp in (2, 3, 5, 10)]
for tr, ak, be, tp in itertools.product((1.0, 1.5, 2.0, 3.0), (0, 1), (False, True), (None, 10)):
    VAR.append((f"trail {tr}ATR {'stl +1R' if ak else 'segera'}{' +BE' if be else ''}{' TP10' if tp else ''}", tp, tr, ak, be))
VAR += [("breakeven saja di +1R", None, 0, 0, True)]
res = {}
mfes = []
for nm, tp, tr, ak, be in VAR:
    R = []
    for i, d in sig.items():
        g, mfe = kelola(i, d, tp, tr, ak, be); R.append((T[i], (g - 0.40) / (1.5 * A[i])))
        if nm.startswith("LIVE"): mfes.append(mfe)
    res[nm] = R
mf = np.array(mfes)
print(f"trade kombinasi 2005-2026: {len(sig)} · gerak menguntungkan maksimal intraday (MFE) dalam R: median {np.median(mf):.2f}, "
      f"p75 {np.percentile(mf,75):.2f}, p90 {np.percentile(mf,90):.2f}, maks {mf.max():.1f} · capai >=3R {np.mean(mf>=3)*100:.1f}%, >=5R {np.mean(mf>=5)*100:.1f}%, >=10R {np.mean(mf>=10)*100:.2f}%")
def ring(R):
    out = []
    for pn, a, b in PER:
        r = np.array([v for t, v in R if t >= m.ts(a) and (b is None or t < m.ts(b))]); y = ((m.ts(b) if b else T[-1]) - m.ts(a)) / 86400 / 365.25
        w, l = r[r > 0], -r[r <= 0]
        out.append((r.sum() / y, np.mean(r > 0), (w.mean() / l.mean()) if len(w) and len(l) else 0, w.sum() / l.sum()))
    return out
print("R/thn trade kombinasi saja · win · RR · PF per periode (2005-14 | PILIH 2015-21 | 2022-Jan25 | Setra)")
urut = sorted(VAR, key=lambda v: -ring(res[v[0]])[1][0])
for v in [VAR[0]] + [x for x in urut if x[0] != VAR[0][0]][:14] + [x for x in VAR if x[0].startswith("TP keras")]:
    o = ring(res[v[0]])
    print(f"{v[0]:<34} " + " | ".join(f"{a:+5.1f} {b*100:3.0f}% RR{c:4.2f} PF{d:4.2f}" for a, b, c, d in o))
