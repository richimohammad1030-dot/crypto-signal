"""Penyetelan bot multi-strategi XAU (maks 1 posisi/hari, keputusan 07:00 WIB, tutup 23:00) - 31 Okt 2026.
Baseline (ide #34): sinyal RSI2 (kuantil 35%, market, SL 3 ATR, tanpa TP) -> RSI2, selain itu K6 (SL 1,5 ATR, TP 4R).
Grid: RSI2 kuantil {0,30 0,35 0,40} x SL {2, 2,5, 3} x TP {2, 3, tanpa} · K6 SL {1,25 1,5} x TP {4, tanpa} ·
aturan {RSI2 dulu, RSI2 hanya searah tren EMA200 H1, RSI2 hanya lawan tren}.
Aturan main (ditetapkan sebelum melihat hasil): seleksi 2015-2021 dengan kriteria awal pemilik + skor tetangga; diterima hanya bila
PF > 1 di uji & Setra DAN P_rasio vs baseline >= 0,90 di uji. Pemakaian: python multi_setel.py <xau_sambung.json> <ambigu.json>"""
import sys, os, json, itertools
import numpy as np
import audit_mesin as m
import strat_mesin as sm
sys.path.insert(0, os.path.join(m.REPO, "riset")); import signifikansi as sg

D = m.muat(sys.argv[1]); T, O, H, L, C = D
A = np.array(m.atr(list(H), list(L), list(C), 14)); F = m.fitur(D, A); HR = ((T // 3600) % 24).astype(int)
AMB = {int(k): v for k, v in json.load(open(sys.argv[2])).items()}
E200 = np.array(m.ema(C, 200))


def rsi(n):
    d = np.diff(C, prepend=C[0]); up, dn = np.where(d > 0, d, 0), np.where(d < 0, -d, 0)
    a = 1 / n; au = np.zeros(len(C)); ad = np.zeros(len(C))
    for j in range(1, len(C)):
        au[j] = au[j - 1] + a * (up[j] - au[j - 1]); ad[j] = ad[j - 1] + a * (dn[j] - ad[j - 1])
    return 100 - 100 / (1 + au / np.maximum(ad, 1e-12))


R2 = rsi(2)
pl = [i for i in np.flatnonzero(HR == sm.PLACE) if 250 <= i and T[i] < m.ts("2022-01-01")]
Q, MSL, MTP = (0.30, 0.35, 0.40), (2.0, 2.5, 3.0), (2, 3, None)
KSL, KTP = (1.25, 1.5), (4, None)
ATURAN = ("RSI2 dulu", "RSI2 hanya searah tren", "RSI2 hanya lawan tren")
tren = lambda i: 1 if C[i] > E200[i] else -1

K6 = {(sl, tp): {x["ip"]: x for x in m.potong(m.jalankan({"tren_lawan_w": ("ema200", 0.0), "ambigu": AMB, "sl_atr": sl, "rr": tp}, D, A, F))}
      for sl in KSL for tp in KTP}
SIG, MR = {}, {}
for q in Q:
    lo_, hi_ = np.quantile(R2[pl], q), np.quantile(R2[pl], 1 - q)
    SIG[q] = {i: (1 if R2[i] <= lo_ else -1) for i in np.flatnonzero(HR == sm.PLACE) if R2[i] <= lo_ or R2[i] >= hi_}
    for sl, tp in itertools.product(MSL, MTP):
        tr = sm.jalan(D, A, lambda i, q=q: [(SIG[q][i], "market", None)] if i in SIG[q] else None, sl=sl, tp=tp)
        MR[(q, sl, tp)] = {x["ip"]: x for x in tr}


def rakit(q, msl, mtp, ksl, ktp, aturan):
    k6, mr, sig = K6[(ksl, ktp)], MR[(q, msl, mtp)], SIG[q]
    out = []
    for i in sorted(set(k6) | set(mr)):
        pakai_mr = i in sig and (aturan == "RSI2 dulu" or (aturan == "RSI2 hanya searah tren" and sig[i] == tren(i))
                                 or (aturan == "RSI2 hanya lawan tren" and sig[i] != tren(i)))
        x = (mr if pakai_mr else k6).get(i)
        if x: out.append(x)
    return sorted(out, key=lambda x: x["t1"])


def lulus(s):
    return (s["wr"] >= 0.40 and s["pf"] > 1.0 and s["per_mg"] >= 3.0 and s["lmax"] <= s["wmax"] + 4 and s["thn_pos"] > s["thn_n"] / 2)


GRID = list(itertools.product(Q, MSL, MTP, KSL, KTP, ATURAN))
res = {g: sm.ringkas(rakit(*g), *m.PILIH) for g in GRID}
DIM = (Q, MSL, MTP, KSL, KTP, ATURAN)


def tetangga(g):
    out = []
    for d, vals in enumerate(DIM[:5]):                      # aturan bukan dimensi berurutan
        j = vals.index(g[d])
        for k in (j - 1, j + 1):
            if 0 <= k < len(vals): out.append(g[:d] + (vals[k],) + g[d + 1:])
    return out


BASE = (0.35, 3.0, None, 1.5, 4, "RSI2 dulu")
rows = []
for g, s in res.items():
    nb = [res[t]["ratio"] for t in tetangga(g)]
    rows.append((min(s["ratio"], np.mean(nb)), g, s, sum(lulus(res[t]) for t in tetangga(g)), len(nb)))
ok = sorted([r for r in rows if lulus(r[2])], key=lambda r: -r[0])
print(f"{len(GRID)} kombinasi; lulus kriteria awal di 2015-2021: {len(ok)}")
bs = res[BASE]; print(f"BASELINE {BASE}: pilih rasio {bs['ratio']:.2f} skor {[r[0] for r in rows if r[1] == BASE][0]:.2f} lulus {lulus(bs)}")
per_aturan = {a: sum(1 for r in ok if r[1][5] == a) for a in ATURAN}; print("Lulus per aturan:", per_aturan)

Bt = rakit(*BASE); bl = [(int(x["t1"]), float(v)) for x, v in zip(Bt, m.net(Bt))]
J = m.potong(m.jalankan({"ambigu": AMB}, D, A, F)); jl = [(int(x["t1"]), float(v)) for x, v in zip(J, m.net(J))]
print("\nTop 10 menurut skor tetangga (2015-2021) + hasil uji & Setra:")
for sk, g, s, nl, nn in ok[:10]:
    tr = rakit(*g); line = []
    for pn, (a, b) in (("pilih", m.PILIH), ("uji", m.UJI), ("Setra", m.KONF)):
        x = sm.ringkas(tr, a, b); line.append(f"{pn} PF {x['pf']:.2f} R/thn {x['rthn']:+.1f} win {x['wr']*100:.0f}% W/L {x['wmax']}/{x['lmax']}")
    pl_ = [(int(x["t1"]), float(v)) for x, v in zip(tr, m.net(tr))]
    p_b = sg.banding(bl, pl_, int(m.ts(m.UJI[0])), int(m.ts(m.UJI[1])))["P_rasio_lebih_baik"]
    s12 = sm.ringkas(tr)
    print(f"skor {sk:+.2f} tetangga lulus {nl}/{nn} {'(BASELINE)' if g == BASE else ''}\n  {g}\n  " + " | ".join(line) +
          f"\n  12 thn: /mg {s12['per_mg']:.1f} win {s12['wr']*100:.0f}% RR {s12['rr']:.2f} PF {s12['pf']:.2f} W/L {s12['wmax']}/{s12['lmax']} "
          f"thn+ {s12['thn_pos']}/{s12['thn_n']} DD {s12['dd']:.0f}R | P_rasio uji vs baseline {p_b:.3f}")
