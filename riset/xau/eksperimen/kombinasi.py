"""Ide #58 (10 Nov 2026, pemilik): KOMBINASI 2-4 indikator/strategi klasik jadi satu strategi buatan sendiri. Tiap komponen memberi
suara arah (+1/-1/0) di candle keputusan; trade hanya bila SEMUA komponen kombinasi sepakat (market di open berikutnya,
SL 1/2 ATR × TP 0,5/1/2R/tanpa, tutup 23:00). Komponen (16): ALG alligator, ST supertrend, ICH ichimoku, SAR, MACD, HA heikin-ashi
2 warna, TPOi (ikut keluar value area), TPOf (fade value area), BBf (bollinger fade), STf (stochastic fade), SOUP (turtle soup),
PDS (PDH/PDL soup), RSIf (RSI2 30/70 fade), EMA (EMA200 H1), D1 (SMA100 harian), CLV (close di separuh range 24 jam).
Konteks: PENGISI hari K6 batal tanpa S3; MANDIRI jam 07:00. Pilih 2015-21 (n pilih >= 30); konfirmasi 2004-14, 2022-Jan25,
Setra. UJI PEMBANDING: porsi lolos-konfirmasi di 100 teratas vs di semua kombinasi (n cukup). Pemakaian: python kombinasi.py <xau_2004.json> <ambigu.json>"""
import sys, itertools
import numpy as np
sys.argv = sys.argv[:3]
exec(open("pustaka.py").read().split("PER = ((")[0])
E200 = np.array(m.gb.ema(list(C), 200))
i07 = np.flatnonzero(HR == sm.PLACE); c07 = C[i07]; cs = np.cumsum(np.insert(c07, 0, 0)); d1b = np.zeros(N)
last = 1
for k, i in enumerate(i07):
    last = 1 if k < 99 or c07[k] > (cs[k + 1] - cs[k - 99]) / 100 else -1
    d1b[i:] = last
def tpo_s(i, ikut):
    poc, val, vah = tpo(i); s = 1 if C[i] > vah else -1 if C[i] < val else 0
    return s if ikut else -s
KOMP = {
 "ALG": lambda i: 1 if LIPS[i] > TEETH[i] > JAW[i] else -1 if LIPS[i] < TEETH[i] < JAW[i] else 0,
 "ST": lambda i: int(ST[i]), "ICH": lambda i: 1 if C[i] > max(SPA[i], SPB[i]) else -1 if C[i] < min(SPA[i], SPB[i]) else 0,
 "SAR": lambda i: int(PS[i]), "MACD": lambda i: 1 if MACDH[i] > 0 else -1,
 "HA": lambda i: int(HAD[i]) if HAD[i] == HAD[i - 1] else 0,
 "TPOi": lambda i: tpo_s(i, True), "TPOf": lambda i: tpo_s(i, False),
 "BBf": lambda i: 1 if C[i] < SMA20[i] - 2 * SD20[i] else -1 if C[i] > SMA20[i] + 2 * SD20[i] else 0,
 "STf": lambda i: 1 if KS[i] < 20 else -1 if KS[i] > 80 else 0,
 "SOUP": lambda i: 1 if L[i] < LL20[i - 1] and C[i] > LL20[i - 1] else -1 if H[i] > HH20[i - 1] and C[i] < HH20[i - 1] else 0,
 "PDS": lambda i: (lambda r: r[0][0] if r else 0)(_pd(i)),
 "RSIf": lambda i: 1 if R2[i] <= 30 else -1 if R2[i] >= 70 else 0,
 "EMA": lambda i: 1 if C[i] > E200[i] else -1, "D1": lambda i: int(d1b[i]),
 "CLV": lambda i: 1 if C[i] >= (H[i - 23:i + 1].max() + L[i - 23:i + 1].min()) / 2 else -1}
NAMA = list(KOMP)
GRID = list(itertools.product((1.0, 2.0), (0.5, 1, 2, None)))
PER = (("2004-14", ("2004-01-01", "2015-01-01")), ("pilih", m.PILIH), ("22-Jan25", m.UJI), ("Setra", m.KONF))
def per_idx(t):
    for k, (pn, (a, b)) in enumerate(PER):
        if (a is None or t >= m.ts(a)) and (b is None or t < m.ts(b)) and (k != 1 or t >= m.ts("2015-01-01")): return k
    return -1
def siapkan(idx):
    V = np.array([[KOMP[k](i) for k in NAMA] for i in idx], dtype=int)           # suara tiap komponen
    P = np.array([per_idx(T[i]) for i in idx]); thn = np.array([(T[min(i + 1, N - 1)] - 0) for i in idx])
    R = np.zeros((len(idx), 2, len(GRID)))                                       # R bersih per arah (+1, -1) & setelan
    for a, i in enumerate(idx):
        j = i + 1; e = O[j]
        for b_, d in enumerate((1, -1)):
            for g, (sl, tp) in enumerate(GRID):
                dist = sl * A[i]
                ex, t1, why = sm._kelola(D, j, d, e, e - d * dist, e + d * tp * dist if tp else None)
                R[a, b_, g] = ((ex - e) * d - 0.40) / dist
    return V, P, R
YRS = np.array([11.0, 7.0, 3.08, (T[-1] - m.ts(m.KONF[0])) / 86400 / 365.25])
def jalan(nm, idx):
    V, P, R = siapkan(idx); hasil = []
    for k in (2, 3, 4):
        for kom in itertools.combinations(range(len(NAMA)), k):
            v = V[:, kom]; s = v[:, 0]
            sepakat = (s != 0) & np.all(v == s[:, None], axis=1)
            if sepakat.sum() < 40: continue
            rows = np.flatnonzero(sepakat); arah = (s[rows] == -1).astype(int)
            for g in range(len(GRID)):
                r = R[rows, arah, g]; p = P[rows]
                tot = np.array([r[p == q].sum() for q in range(4)]); n = np.array([(p == q).sum() for q in range(4)])
                if n[1] < 30: continue
                hasil.append(("+".join(NAMA[c] for c in kom), GRID[g], tot / YRS, n, np.mean(r > 0), r))
    print(f"\n######## {nm}: {len(idx)} hari, kombinasi dinilai {len(hasil)}")
    hasil.sort(key=lambda z: -z[2][1])
    lol = lambda z: z[2][0] > 0 and z[2][2] > 0 and z[2][3] > 0
    base = np.mean([lol(z) for z in hasil])
    for top in (20, 100, 500):
        print(f"  porsi lolos konfirmasi (2004-14 & 2022-Jan25 & Setra positif): {top} teratas {np.mean([lol(z) for z in hasil[:top]])*100:.0f}%  vs  semua {base*100:.0f}%")
    print("  15 teratas di 2015-21 (R/thn 2004-14 · pilih · 22-Jan25 · Setra | n pilih | win):")
    for z in hasil[:15]:
        print(f"    {z[0]:<20} SL{z[1][0]} TP{z[1][1] or '-':<4} " + " · ".join(f"{v:+6.1f}" for v in z[2]) + f" | n{z[3][1]:>4} win {z[4]*100:.0f}%" + ("  LOLOS" if lol(z) else ""))
    ok = [z for z in hasil if lol(z) and z[2][1] > 0]
    ok.sort(key=lambda z: -min(z[2]))
    print("  terbaik menurut periode TERBURUK (untung di keempat periode):")
    for z in ok[:8]:
        print(f"    {z[0]:<20} SL{z[1][0]} TP{z[1][1] or '-':<4} " + " · ".join(f"{v:+6.1f}" for v in z[2]) + f" | n total {z[3].sum()} win {z[4]*100:.0f}%")
jalan("PENGISI hari batal", isi)
jalan("MANDIRI jam 07:00", harian)
