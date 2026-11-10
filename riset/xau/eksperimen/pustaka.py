"""Ide #54 (10 Nov 2026, pemilik: keluar dari RSI/EMA). PUSTAKA STRATEGI KLASIK dalam jendela tetap pemilik (keputusan lalu
masuk, tutup 23:00 WIB), diuji di 2 konteks: (1) PENGISI hari K6 batal tanpa S3; (2) MANDIRI tiap hari jam 07:00.
Strategi: inside bar (OCO induk), turtle soup (tembus 20-bar gagal -> fade), fraktal Bill Williams (OCO di fraktal terakhir),
alligator (SMMA 13/8/5 tergeser), fibonacci (limit di 61,8% swing 24 bar searah swing), profil waktu TPO/POC (proksi volume
profile; kembali ke POC atau tolak value area), donchian 20 (OCO), NR7 (OCO), bollinger (tembus pita -> fade) & squeeze
breakout, supertrend 10/3, pivot klasik harian (fade R1/S1 limit), PDH/PDL soup, heikin-ashi 2 warna, MACD histogram,
ichimoku (posisi vs awan), parabolic SAR, stochastic 14/3. SL 1/2 ATR × TP 0,5/1/2R/tanpa (8 per strategi).
Pilih 2015-2021; konfirmasi 2004-2014, 2022-Jan 2025, Setra. Biaya 0,40 USD. Pemakaian: python pustaka.py <xau_2004.json> <ambigu.json>"""
import sys, json, itertools
import numpy as np
import audit_mesin as m, strat_mesin as sm, multi_mesin as mm
D = m.muat(sys.argv[1]); T, O, H, L, C = D; N = len(T)
A = np.array(m.atr(list(H), list(L), list(C), 14)); F = m.fitur(D, A)
AMB = {int(k): v for k, v in json.load(open(sys.argv[2])).items()}
HR = ((T // 3600) % 24).astype(int); R2 = mm.rsi(C, 2); KEP = set(m.gb.SUS_JAM_UTC)
def smma(x, n):
    o = np.empty(len(x)); o[0] = x[0]
    for i in range(1, len(x)): o[i] = (o[i - 1] * (n - 1) + x[i]) / n
    return o
def emaa(x, n): return np.array(m.gb.ema(list(x), n))
def shift(x, k): return np.concatenate([np.full(k, np.nan), x[:-k]])
MP = (H + L) / 2
JAW, TEETH, LIPS = shift(smma(MP, 13), 8), shift(smma(MP, 8), 5), shift(smma(MP, 5), 3)
MACDH = (emaa(C, 12) - emaa(C, 26)); MACDH = MACDH - emaa(MACDH, 9)
def roll(f, x, n):
    o = np.full(len(x), np.nan)
    for i in range(n - 1, len(x)): o[i] = f(x[i - n + 1:i + 1])
    return o
SMA20 = roll(np.mean, C, 20); SD20 = roll(np.std, C, 20); BW = (4 * SD20) / SMA20; BWQ = roll(lambda v: np.mean(v[:-1] >= v[-1]), BW, 120)
HH20, LL20 = roll(np.max, H, 20), roll(np.min, L, 20); RNG = H - L; NR7 = roll(lambda v: float(v[-1] == v.min()), RNG, 7)
LO14, HI14 = roll(np.min, L, 14), roll(np.max, H, 14); K = 100 * (C - LO14) / np.maximum(HI14 - LO14, 1e-9); KS = roll(np.mean, K, 3)
TEN = (roll(np.max, H, 9) + roll(np.min, L, 9)) / 2; KIJ = (roll(np.max, H, 26) + roll(np.min, L, 26)) / 2
SPA = shift((TEN + KIJ) / 2, 26); SPB = shift((roll(np.max, H, 52) + roll(np.min, L, 52)) / 2, 26)
# supertrend 10/3
ST = np.zeros(N); up = dn = 0.0; tr = 1
for i in range(1, N):
    m_ = (H[i] + L[i]) / 2; u, d_ = m_ - 3 * A[i], m_ + 3 * A[i]
    up = max(u, up) if C[i - 1] > up else u; dn = min(d_, dn) if C[i - 1] < dn else d_
    tr = 1 if C[i] > dn else -1 if C[i] < up else tr; ST[i] = tr
# parabolic SAR
PS = np.zeros(N); bull, af, ep, sar = True, 0.02, H[0], L[0]
for i in range(1, N):
    sar = sar + af * (ep - sar)
    if bull:
        if L[i] < sar: bull, sar, ep, af = False, ep, L[i], 0.02
        elif H[i] > ep: ep, af = H[i], min(af + 0.02, 0.2)
    else:
        if H[i] > sar: bull, sar, ep, af = True, ep, H[i], 0.02
        elif L[i] < ep: ep, af = L[i], min(af + 0.02, 0.2)
    PS[i] = 1 if bull else -1
# heikin ashi
HAC = (O + H + L + C) / 4; HAO = np.empty(N); HAO[0] = O[0]
for i in range(1, N): HAO[i] = (HAO[i - 1] + HAC[i - 1]) / 2
HAD = np.sign(HAC - HAO)
# hari sebelumnya (blok 24 jam berakhir di candle i)
def fraktal(i):
    up = dn = None
    for k in range(i - 2, max(i - 60, 2), -1):
        if up is None and H[k] > max(H[k - 2:k]) and H[k] > max(H[k + 1:k + 3]): up = H[k]
        if dn is None and L[k] < min(L[k - 2:k]) and L[k] < min(L[k + 1:k + 3]): dn = L[k]
        if up is not None and dn is not None: break
    return up, dn
def tpo(i):
    h, l = H[i - 23:i + 1], L[i - 23:i + 1]; b = max(A[i] * 0.25, 0.01); lo = l.min()
    nb = int((h.max() - lo) / b) + 1; cnt = np.zeros(nb)
    for a_, z in zip(l, h): cnt[int((a_ - lo) / b):int((z - lo) / b) + 1] += 1
    poc = int(np.argmax(cnt)); tot = cnt.sum(); s = cnt[poc]; a_, z = poc, poc
    while s < 0.7 * tot:
        na = cnt[a_ - 1] if a_ > 0 else -1; nz = cnt[z + 1] if z < nb - 1 else -1
        if nz >= na: z += 1; s += cnt[z]
        else: a_ -= 1; s += cnt[a_]
    return lo + (poc + 0.5) * b, lo + a_ * b, lo + (z + 1) * b
S = {}
S["inside bar OCO"] = lambda i: [(1, "stop", H[i - 1]), (-1, "stop", L[i - 1])] if H[i] <= H[i - 1] and L[i] >= L[i - 1] else None
S["turtle soup 20"] = lambda i: ([(1, "market", None)] if L[i] < LL20[i - 1] and C[i] > LL20[i - 1] else
                                 [(-1, "market", None)] if H[i] > HH20[i - 1] and C[i] < HH20[i - 1] else None)
def _fr(i):
    u, d = fraktal(i)
    return [(1, "stop", u), (-1, "stop", d)] if u is not None and d is not None and d < C[i] < u else None
S["fraktal breakout OCO"] = _fr
S["alligator searah"] = lambda i: ([(1, "market", None)] if LIPS[i] > TEETH[i] > JAW[i] else [(-1, "market", None)] if LIPS[i] < TEETH[i] < JAW[i] else None)
def _fib(i):
    h, l = H[i - 23:i + 1], L[i - 23:i + 1]; ih, il = int(np.argmax(h)), int(np.argmin(l)); a_, z = l.min(), h.max()
    return [(1, "limit", z - 0.618 * (z - a_))] if ih > il else [(-1, "limit", a_ + 0.618 * (z - a_))]
S["fibonacci 61,8 searah swing"] = _fib
def _tpo_r(i):
    poc, val, vah = tpo(i)
    return [(-1, "market", None)] if C[i] > vah else [(1, "market", None)] if C[i] < val else None
def _tpo_b(i):
    poc, val, vah = tpo(i)
    return [(1, "market", None)] if C[i] > vah else [(-1, "market", None)] if C[i] < val else None
def _tpo_lim(i):
    poc, val, vah = tpo(i)
    return [(1, "limit", val), (-1, "limit", vah)]
S["TPO tolak value area (fade)"] = _tpo_r
S["TPO terima di luar VA (ikut)"] = _tpo_b
S["TPO limit di tepi VA (OCO)"] = _tpo_lim
S["donchian 20 OCO"] = lambda i: [(1, "stop", HH20[i]), (-1, "stop", LL20[i])]
S["NR7 OCO"] = lambda i: [(1, "stop", H[i]), (-1, "stop", L[i])] if NR7[i] == 1 else None
S["bollinger fade"] = lambda i: ([(1, "market", None)] if C[i] < SMA20[i] - 2 * SD20[i] else [(-1, "market", None)] if C[i] > SMA20[i] + 2 * SD20[i] else None)
S["bollinger squeeze OCO"] = lambda i: [(1, "stop", SMA20[i] + 2 * SD20[i]), (-1, "stop", SMA20[i] - 2 * SD20[i])] if BWQ[i] >= 0.9 else None
S["supertrend searah"] = lambda i: [(int(ST[i]), "market", None)]
def _piv(i):
    h, l, c = H[i - 23:i + 1].max(), L[i - 23:i + 1].min(), C[i]; p = (h + l + c) / 3
    return [(-1, "limit", 2 * p - l), (1, "limit", 2 * p - h)]
S["pivot fade R1/S1 (OCO limit)"] = _piv
def _pd(i):
    ph, pl = H[i - 47:i - 23].max(), L[i - 47:i - 23].min()
    return ([(1, "market", None)] if L[i - 23:i + 1].min() < pl and C[i] > pl else
            [(-1, "market", None)] if H[i - 23:i + 1].max() > ph and C[i] < ph else None)
S["PDH/PDL soup"] = _pd
S["heikin-ashi 2 warna"] = lambda i: [(int(HAD[i]), "market", None)] if HAD[i] == HAD[i - 1] != 0 else None
S["MACD histogram"] = lambda i: [(1 if MACDH[i] > 0 else -1, "market", None)]
S["ichimoku vs awan"] = lambda i: ([(1, "market", None)] if C[i] > max(SPA[i], SPB[i]) else [(-1, "market", None)] if C[i] < min(SPA[i], SPB[i]) else None)
S["parabolic SAR"] = lambda i: [(int(PS[i]), "market", None)]
S["stochastic 20/80 fade"] = lambda i: ([(1, "market", None)] if KS[i] < 20 else [(-1, "market", None)] if KS[i] > 80 else None)

def jalan_idx(idx, rencana, sl, tp):
    out = []
    for i in idx:
        try: orders = rencana(i)
        except Exception: orders = None
        if not orders or any(o[2] is not None and not np.isfinite(o[2]) for o in orders): continue
        dist = sl * A[i]
        if dist <= 0.5: continue
        for j in range(i + 1, min(i + 20, N)):
            kand = []
            for d, jn, lvl in orders:
                if jn == "market":
                    if j == i + 1: kand.append((d, O[j]))
                elif jn == "limit":
                    if (d == 1 and L[j] <= lvl) or (d == -1 and H[j] >= lvl): kand.append((d, min(lvl, O[j]) if d == 1 else max(lvl, O[j])))
                elif (d == 1 and H[j] >= lvl) or (d == -1 and L[j] <= lvl): kand.append((d, max(lvl, O[j]) if d == 1 else min(lvl, O[j])))
            if kand:
                ops = []
                for d, e in kand:
                    ex, t1, why = sm._kelola(D, j, d, e, e - d * dist, e + d * tp * dist if tp else None)
                    ops.append(dict(d=d, e=e, ex=ex, r0=dist, t0=T[j], t1=t1, why=why, w=1.0, ip=i, i0=j, R=(ex - e) * d / dist))
                out.append(min(ops, key=lambda z: z["R"])); break
            if HR[j] == sm.CLOSE: break
    return out
# konteks
sig = mm.sinyal_live(D); ekstrem = lambda q: R2[q] <= m.gb.SUS_BUY or R2[q] >= m.gb.SUS_SELL
isi = []
for x in m.jalankan({"tren_lawan_w": ("ema200", 0.0), "ambigu": AMB}, D, A, F):
    if x["w"] != 0 or x["ip"] in sig or x["ip"] < 2500: continue
    q = x["i0"]
    while q < N and HR[q] not in KEP and HR[q] != sm.CLOSE: q += 1
    if q < N - 1 and HR[q] in KEP and not ekstrem(q): isi.append(q)
harian = [int(i) for i in np.flatnonzero(HR == sm.PLACE) if 2500 <= i < N - 1]
PER = (("2004-14", ("2004-01-01", "2015-01-01")), ("pilih15-21", m.PILIH), ("22-Jan25", m.UJI), ("Setra", m.KONF))
GRID = list(itertools.product((1.0, 2.0), (0.5, 1, 2, None)))
for nm_k, idx, hari in (("PENGISI hari batal", isi, len(isi)), ("MANDIRI tiap hari 07:00", harian, len(harian))):
    print(f"\n######## {nm_k} ({hari} hari) — R/thn per periode (2004-14 · pilih 15-21 · 22-Jan25 · Setra) & win/RR 12+ thn")
    lolos = 0
    for snm, fn in S.items():
        best = None
        for sl, tp in GRID:
            tr = jalan_idx(idx, fn, sl, tp)
            if len(tr) < 20: continue
            s = {pn: sm.ringkas(tr, a, b) for pn, (a, b) in PER}
            if best is None or s["pilih15-21"]["rthn"] > best[2]["pilih15-21"]["rthn"]: best = (sl, tp, s, tr)
        if not best: print(f"  {snm:<30} sinyal terlalu jarang"); continue
        sl, tp, s, tr = best; ok = all(s[pn]["rthn"] > 0 for pn, _ in PER); lolos += ok
        sa = sm.ringkas(tr)
        print(f"  {snm:<30} SL{sl} TP{tp or '-':<4} cakupan {len(tr)/hari*100:3.0f}% | " + " · ".join(f"{s[pn]['rthn']:+6.1f}" for pn, _ in PER)
              + f" | win {sa['wr']*100:.0f}% RR {sa['rr']:.2f} PF {sa['pf']:.2f}" + ("  <<< UNTUNG DI SEMUA PERIODE" if ok else ""))
    print(f"  -> lolos semua periode: {lolos}/{len(S)}")
