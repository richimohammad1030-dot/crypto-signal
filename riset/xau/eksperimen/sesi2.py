"""Ide #39 (5 Nov 2026, pemilik): SESI TAMBAHAN 23:00-07:00 WIB di samping sesi wajib 07:00-23:00 (aturan sesi 1 tidak diubah).
Sinyal di close candle 23:00 WIB, masuk market open 23:00, tutup di close candle 07:00 WIB (sebelum sinyal sesi 1).
Malam Jumat dilewati (tanpa menahan posisi akhir pekan). Biaya 0,40 USD + SWAP menginap (long dibebankan; sensitivitas
0 / 0,3 / 0,6 USD per oz per malam; short dianggap 0). Varian: long selalu / long bila tren naik (EMA200 H1) / long bila tren
naik D1 (close > EMA 50 hari dari close 23:00) / MR RSI2 dua arah / long MR (RSI2 rendah) × SL 1,5/2/3 ATR × TP 1R/2R/tanpa.
Pilih 2015-2021, uji 2022-Jan 2025, Setra. Gabung dengan baseline live (sesi 1 tidak berubah, posisi tidak tumpang tindih).
Pemakaian: python sesi2.py <xau_sambung.json> <ambigu.json>"""
import sys, os, json, itertools
import numpy as np
import audit_mesin as m, strat_mesin as sm, multi_mesin as mm
sys.path.insert(0, os.path.join(m.REPO, "riset")); import signifikansi as sg
D = m.muat(sys.argv[1]); T, O, H, L, C = D
A = np.array(m.atr(list(H), list(L), list(C), 14)); F = m.fitur(D, A)
AMB = {int(k): v for k, v in json.load(open(sys.argv[2])).items()}
HR = ((T // 3600) % 24).astype(int); R2 = mm.rsi(C, 2); E = np.array(m.gb.ema(list(C), 200))
BASE = mm.baseline(D, A, F, ambigu=AMB)
# EMA 50 hari dari close 23:00 WIB
i23 = np.flatnonzero(HR == 15); ed = np.array(m.gb.ema(list(C[i23]), 50)); ED = {int(i): ed[k] for k, i in enumerate(i23)}
pl = [i for i in i23 if T[i] < m.ts("2022-01-01")]
q_lo, q_hi = np.quantile(R2[pl], 0.35), np.quantile(R2[pl], 0.65)
print(f"ambang RSI2 23:00 (kuantil 35/65% 2015-21): {q_lo:.2f} / {q_hi:.2f}")
WD = lambda t: (int(t) // 86400 + 3) % 7      # 0 = Senin (UTC)
ARAH = {"long selalu": lambda i: 1,
        "long tren H1": lambda i: 1 if C[i] > E[i] else 0,
        "long tren D1": lambda i: 1 if C[i] > ED[int(i)] else 0,
        "MR RSI2 2 arah": lambda i: 1 if R2[i] <= q_lo else -1 if R2[i] >= q_hi else 0,
        "long MR RSI2": lambda i: 1 if R2[i] <= q_lo else 0}


def jalan(fn, sl, tp, swap):
    out = []
    for i in i23:
        if i < 250 or i + 1 >= len(T) or WD(T[i]) == 4 or T[i + 1] - T[i] != 3600: continue
        d = fn(i)
        if not d: continue
        k = next((j for j in range(i + 1, min(i + 12, len(T))) if HR[j] == 23), None)
        if k is None: continue
        dist = sl * A[i]; e = O[i + 1]; slp = e - d * dist; tpp = e + d * tp * dist if tp else None
        ex, t1 = C[k], T[k]
        for j in range(i + 1, k + 1):
            if (d == 1 and L[j] <= slp) or (d == -1 and H[j] >= slp): ex, t1 = slp, T[j]; break
            if j > i + 1 and tpp is not None and ((d == 1 and H[j] >= tpp) or (d == -1 and L[j] <= tpp)): ex, t1 = tpp, T[j]; break
        # swap: dibebankan bila posisi long melewati rollover (21-22 UTC); ditaruh sebagai pengurang harga keluar
        if d == 1 and t1 >= T[i] + 7 * 3600: ex = ex - swap
        out.append(dict(d=d, e=e, ex=ex, r0=dist, t0=T[i + 1], t1=t1, why="S2", w=1.0, ip=i, i0=i + 1, R=(ex - e) * d / dist, strat="S2"))
    return out


jl = [(int(x["t1"]), float(v)) for x, v in zip(BASE, m.net(BASE))]
P4 = (("pilih", m.PILIH), ("uji", m.UJI), ("Setra", m.KONF), ("12t", (None, None)))
s0 = {pn: sm.ringkas(BASE, a, b) for pn, (a, b) in P4}
print("BASELINE sesi 1 saja R/thn: " + " · ".join(f"{pn} {s0[pn]['rthn']:+.1f}" for pn, _ in P4) + f" | DD {s0['12t']['dd']:.0f}R")
for swap in (0.0, 0.3, 0.6):
    print(f"\n=== swap long {swap} USD/oz/malam ===   (sesi 2 sendiri: n, win, PF per periode | GABUNG R/thn per periode, DD, P uji)")
    for (nm, fn), sl, tp in itertools.product(ARAH.items(), (1.5, 2.0, 3.0), (1, 2, None)):
        s2 = jalan(fn, sl, tp, swap)
        if not s2: continue
        r = {pn: sm.ringkas(s2, a, b) for pn, (a, b) in P4}
        G = sorted(BASE + s2, key=lambda z: z["t1"]); gl = [(int(x["t1"]), float(v)) for x, v in zip(G, m.net(G))]
        g = {pn: sm.ringkas(G, a, b) for pn, (a, b) in P4}
        pr = sg.banding(jl, gl, int(m.ts(m.UJI[0])), int(m.ts(m.UJI[1])))["P_rasio_lebih_baik"]
        print(f"{nm:<15} SL{sl} TP{tp or '-':<4} n{r['12t']['n']:>5} win {r['12t']['wr']*100:3.0f}% PF " +
              "/".join(f"{r[pn]['pf']:.2f}" for pn, _ in P4) + " | gab " + " · ".join(f"{g[pn]['rthn']:+5.1f}" for pn, _ in P4) +
              f" DD {g['12t']['dd']:3.0f}R P {pr:.2f}")
