"""Ide #53 (10 Nov 2026, pemilik: riset bebas & kreatif). PENGISI hari K6 batal yang tidak dapat susulan S3 (RSI2 tidak ekstrem
di jam keputusan). Aturan: JIKA kondisi(fitur) MAKA arah A SELAIN ITU arah B (100% hari tetap dapat sinyal), masuk market di
open candle berikutnya, SL k ATR, TP r R (boleh < 1), tutup 23:00.
Arah: IKUT (arah tembusan batas batal) · FADE (arah tren EMA200 = kebalikan tembusan) · MR50 (RSI2<50 BUY) · MOM (arah candle
keputusan) · D1 (tren harian SMA100) · CLV (close di separuh atas range hari ini -> BUY).
Fitur kondisi (dibelah di median 2015-2021): RSI2, RSI14, jarak ke EMA200 H1 (ATR), tembusan sudah sejauh apa dari batas batal
(ATR), range hari s.d. keputusan (ATR), ATR relatif, jam keputusan, hari, tubuh candle keputusan (ATR), arah tembusan searah D1?
Pilih 2015-2021; KONFIRMASI 2004-2014 (belum pernah dilihat) & 2022-2026. Pemakaian: python pengisi_bebas.py <xau_2004.json> <ambigu.json>"""
import sys, json, itertools
import numpy as np
import audit_mesin as m, strat_mesin as sm, multi_mesin as mm
D = m.muat(sys.argv[1]); T, O, H, L, C = D
A = np.array(m.atr(list(H), list(L), list(C), 14)); F = m.fitur(D, A)
AMB = {int(k): v for k, v in json.load(open(sys.argv[2])).items()}
HR = ((T // 3600) % 24).astype(int); R2 = mm.rsi(C, 2); R14 = mm.rsi(C, 14); E = np.array(m.gb.ema(list(C), 200))
KEP = set(m.gb.SUS_JAM_UTC); sig = mm.sinyal_live(D)
i07 = np.flatnonzero(HR == sm.PLACE); c07 = C[i07]; cs = np.cumsum(np.insert(c07, 0, 0))
d1 = {int(i): (1 if k < 99 or c07[k] > (cs[k + 1] - cs[k - 99]) / 100 else -1) for k, i in enumerate(i07)}
ekstrem = lambda q: R2[q] <= m.gb.SUS_BUY or R2[q] >= m.gb.SUS_SELL
hari = []
for x in m.jalankan({"tren_lawan_w": ("ema200", 0.0), "ambigu": AMB}, D, A, F):
    if x["w"] != 0 or x["ip"] in sig or x["ip"] < 2500: continue          # 2500 candle pemanasan (EMA200, SMA100 hari)
    q = x["i0"]
    while q < len(T) and HR[q] not in KEP and HR[q] != sm.CLOSE: q += 1
    if q >= len(T) - 1 or HR[q] not in KEP or ekstrem(q): continue
    ip, tb = x["ip"], x["d"]                                              # tb = arah tembusan (sisi lawan tren yang tersentuh)
    lvl = x["e"]; a = A[q]; hi, lo = H[ip + 1:q + 1].max(), L[ip + 1:q + 1].min()
    f = dict(rsi2=R2[q], rsi14=R14[q], jarak_ema=(C[q] - E[q]) / a, lanjut=(C[q] - lvl) * tb / a, range=(hi - lo) / a,
             atr=a / np.median(A[max(0, q - 500):q + 1]), jam=HR[q], hari=(int(T[q]) // 86400 + 3) % 7, tubuh=(C[q] - O[q]) / a,
             searah_d1=float(tb == d1.get(ip, 1)))
    arah = dict(IKUT=tb, FADE=-tb, MR50=1 if R2[q] < 50 else -1, MOM=1 if C[q] >= O[q] else -1, D1=d1.get(ip, 1),
                CLV=1 if C[q] >= (hi + lo) / 2 else -1)
    hari.append(dict(ip=ip, q=q, t=T[q], f=f, arah=arah))
print(f"hari pengisi (2004-2026): {len(hari)}")
PER = {"2004-14": ("2004-01-01", "2015-01-01"), "pilih 15-21": ("2015-01-01", "2022-01-01"), "22-Jan25": m.UJI, "Setra": m.KONF}
def per(t):
    for k, (a, b) in PER.items():
        if t >= m.ts(a) and (b is None or t < m.ts(b)): return k
# hasil tiap (hari, arah, SL, TP) dihitung sekali
SLs, TPs = (1.0, 1.5, 2.0, 3.0), (0.3, 0.5, 0.75, 1.0, 1.5, 2.0, None)
cache = {}
for h in hari:
    q = h["q"]; j = q + 1; e = O[j]
    for d in (1, -1):
        for sl, tp in itertools.product(SLs, TPs):
            dist = sl * A[q]
            ex, t1, why = sm._kelola(D, j, d, e, e - d * dist, e + d * tp * dist if tp else None)
            cache[(h["q"], d, sl, tp)] = ((ex - e) * d - 0.40) / dist
med = {k: np.median([h["f"][k] for h in hari if per(h["t"]) == "pilih 15-21"]) for k in hari[0]["f"]}
ARAH = list(hari[0]["arah"])
def nilai(rule, sl, tp):
    fit, A_, B_ = rule; out = {k: [] for k in PER}
    for h in hari:
        d = h["arah"][A_] if (fit is None or h["f"][fit] > med[fit]) else h["arah"][B_]
        out[per(h["t"])].append(cache[(h["q"], d, sl, tp)])
    return out
rules = [(None, a, a) for a in ARAH] + [(f, a, b) for f in med for a in ARAH for b in ARAH if a != b]
res = []
for r, sl, tp in itertools.product(rules, SLs, TPs):
    o = nilai(r, sl, tp)
    s = {k: (np.mean(v) if v else 0, np.mean(np.array(v) > 0) if v else 0, len(v)) for k, v in o.items()}
    res.append((r, sl, tp, s))
print(f"kombinasi diuji: {len(res)}")
pil = sorted(res, key=lambda z: -z[3]["pilih 15-21"][0])
def fmt(z):
    r, sl, tp, s = z; nm = (f"{r[0]}>{med[r[0]]:.2f}? {r[1]}:{r[2]}" if r[0] else f"selalu {r[1]}") + f" SL{sl} TP{tp or '-'}"
    return f"{nm:<44} " + " | ".join(f"{k} {v[0]:+.3f}R win {v[1]*100:.0f}% n{v[2]}" for k, v in s.items())
print("\n=== 15 teratas di 2015-2021 (R bersih rata/trade), lalu konfirmasi:")
for z in pil[:15]: print(fmt(z))
top = pil[:200]
ok = [z for z in top if z[3]["2004-14"][0] > 0 and z[3]["22-Jan25"][0] > 0 and z[3]["Setra"][0] > 0]
print(f"\nDari 200 teratas pilih: positif di 2004-14 {sum(z[3]['2004-14'][0] > 0 for z in top)}, di 2022-Jan25 "
      f"{sum(z[3]['22-Jan25'][0] > 0 for z in top)}, di Setra {sum(z[3]['Setra'][0] > 0 for z in top)}, ketiganya {len(ok)}")
for z in ok[:10]: print("  LOLOS: " + fmt(z))
print("\nSemua kombinasi: porsi positif per periode:", {k: f"{np.mean([z[3][k][0] > 0 for z in res])*100:.0f}%" for k in PER})
