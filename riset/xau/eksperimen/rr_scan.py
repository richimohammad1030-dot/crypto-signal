"""Kriteria longgar pemilik (31 Okt 2026): win >= 35%, RR tercapai >= 1,5, PF > 1,05, >= 3 trade/minggu,
kalah beruntun maks <= 2 x menang beruntun maks, mayoritas tahun untung. Jendela tetap 07:00-23:00 WIB.
Pindai exit K6 (SL x TP), RSI(2) fade (kuantil x filter x SL x TP), dan portofolio K6 + RSI2 (bobot RSI2 1 atau 0,5).
SELEKSI di 2015-2021; uji 2022 - Jan 2025; konfirmasi Setra. K6 memakai urutan M1 2022-skrg.
Pemakaian: python rr_scan.py <xau_sambung.json> <ambigu.json>"""
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


def lulus(s):
    return (s["n"] > 0 and s["wr"] >= 0.35 and s["rr"] >= 1.5 and s["pf"] > 1.05 and s["per_mg"] >= 3.0
            and s["lmax"] <= 2 * s["wmax"] and s["thn_pos"] > s["thn_n"] / 2)


# --- K6 dengan exit berbeda
K6 = {}
for sl, tp in itertools.product((1.0, 1.25, 1.5, 2.0), (2, 3, 4, 6, None)):
    K6[(sl, tp)] = m.potong(m.jalankan({"tren_lawan_w": ("ema200", 0.0), "ambigu": AMB, "sl_atr": sl, "rr": tp}, D, A, F))
# --- RSI2 fade dengan exit berbeda
MR = {}
for q, filt, sl, tp in itertools.product((0.30, 0.35, 0.40), ("tanpa", "searah tren"), (1.5, 2.0, 2.5, 3.0), (1.5, 2, 3, None)):
    lo_, hi_ = np.quantile(R2[pl], q), np.quantile(R2[pl], 1 - q)
    def rc(i, lo_=lo_, hi_=hi_, filt=filt):
        d = 1 if R2[i] <= lo_ else (-1 if R2[i] >= hi_ else 0)
        if d and filt == "searah tren" and d != (1 if C[i] > E200[i] else -1): d = 0
        return [(d, "market", None)] if d else None
    MR[(q, filt, sl, tp)] = sm.jalan(D, A, rc, sl=sl, tp=tp)

KAND = {}
for k, tr in K6.items(): KAND[("K6", k)] = tr
for k, tr in MR.items(): KAND[("RSI2", k)] = tr
for (k1, t1), (k2, t2) in itertools.product(K6.items(), MR.items()):
    for w in (1.0, 0.5):
        KAND[("K6+RSI2", k1, k2, w)] = sorted(t1 + [dict(x, w=w) for x in t2], key=lambda x: x["t1"])
print(len(KAND), "kandidat")

res = {k: sm.ringkas(tr, *m.PILIH) for k, tr in KAND.items()}
ok = [k for k, s in res.items() if lulus(s)]
print("Lulus kriteria longgar di 2015-2021:", len(ok), "| per jenis:", {j: sum(1 for k in ok if k[0] == j) for j in ("K6", "RSI2", "K6+RSI2")})
# dekat-lulus per jenis (untuk melihat syarat mana yang gagal)
for j in ("K6", "RSI2", "K6+RSI2"):
    ks = sorted([k for k in res if k[0] == j], key=lambda k: -res[k]["ratio"])[:3]
    for k in ks:
        s = res[k]
        gagal = [n for n, c in (("win", s["wr"] >= .35), ("RR", s["rr"] >= 1.5), ("PF", s["pf"] > 1.05), ("frek", s["per_mg"] >= 3),
                                ("beruntun", s["lmax"] <= 2 * s["wmax"]), ("tahun", s["thn_pos"] > s["thn_n"] / 2)) if not c]
        print(f"  [{j}] terbaik rasio {k[1:]}: /mg {s['per_mg']:.1f} win {s['wr']*100:.0f}% rr {s['rr']:.2f} pf {s['pf']:.2f} "
              f"R/thn {s['rthn']:+.1f} DD {s['dd']:.0f} W/L {s['wmax']}/{s['lmax']} thn+ {s['thn_pos']}/{s['thn_n']} gagal: {gagal}")

ok.sort(key=lambda k: -res[k]["ratio"])
J = m.potong(m.jalankan({"ambigu": AMB}, D, A, F)); jl = [(int(x["t1"]), float(v)) for x, v in zip(J, m.net(J))]
print("\n=== Lulus di 2015-2021 (urut rasio R/DD), hasil di uji & Setra")
seen = 0
for k in ok[:12]:
    tr = KAND[k]; print(f"\n{k}")
    for pn, (a, b) in (("pilih", m.PILIH), ("uji", m.UJI), ("Setra", m.KONF), ("12 thn", (None, None))):
        s = sm.ringkas(tr, a, b)
        print(f"   {pn:<6} /mg {s['per_mg']:.1f} win {s['wr']*100:.0f}% rr {s['rr']:.2f} pf {s['pf']:.2f} exp {s['avg']:+.3f} R/thn {s['rthn']:+.1f} "
              f"DD {s['dd']:.0f}R ({s['ddpct']:.0f}%) W/L {s['wmax']}/{s['lmax']} thn+ {s['thn_pos']}/{s['thn_n']} {'LULUS' if lulus(s) else '-'}")
    pl_ = [(int(x["t1"]), float(v)) for x, v in zip(m.potong(tr), m.net(m.potong(tr)))]
    r = sg.banding(jl, pl_, int(m.ts(m.UJI[0])), int(m.ts(m.UJI[1])))
    print(f"   P_rasio uji vs juara {r['P_rasio_lebih_baik']:.3f} | slip+0,2 uji R/thn {sm.ringkas(tr, *m.UJI, slip=0.2)['rthn']:+.1f} | per tahun:",
          " ".join(f"{y}:{v:+.0f}" for y, v in m.stat(tr)["thn"].items()))
