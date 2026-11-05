"""Ide #46 (6 Nov 2026, ide baru) [lit] Connors & Alvarez (2008/2009, "Short Term Trading Strategies That Work"; "High
Probability ETF Trading"): posisi mean reversion RSI(2) ditutup saat harga SUDAH berbalik (close > SMA5, atau RSI(2) naik melewati
ambang), bukan ditahan sampai jam tutup. Bot live: MR tanpa TP, ditutup 23:00 WIB. Logika keluar baru (bukan geser parameter):
  E-RSI X : BUY ditutup di close candle H1 pertama dengan RSI(2) >= X (SELL: <= 100-X), X 50/60/70/80/90
  E-SMA n : BUY ditutup di close candle H1 pertama dengan close > SMA n H1 (SELL: close < SMA n), n 5/10
SL 3 ATR & tutup 23:00 tetap; K6 & susulan tidak berubah. Pilih 2015-2021, uji 2022-Jan 2025, konfirmasi Setra.
Pemakaian: python ide46_mr_keluar.py <sambung.json> <ambigu.json>"""
import sys, os, json
import numpy as np
import audit_mesin as m, strat_mesin as sm, multi_mesin as mm
sys.path.insert(0, os.path.join(m.REPO, "riset")); import signifikansi as sg

D = m.muat(sys.argv[1]); T, O, H, L, C = D
A = np.array(m.atr(list(H), list(L), list(C), 14)); F = m.fitur(D, A)
AMB = {int(k): v for k, v in json.load(open(sys.argv[2])).items()}
R2 = mm.rsi(C, 2); HR = ((T // 3600) % 24).astype(int)
SIG = mm.sinyal_live(D)


def sma(n):
    c = np.cumsum(np.insert(C, 0, 0)); o = np.full(len(C), np.nan); o[n - 1:] = (c[n:] - c[:-n]) / n; return o


def mr_keluar(cek):
    """Trade MR bot live dengan aturan keluar tambahan cek(q, d) -> True = tutup di close candle q."""
    out = []
    for i, d in SIG.items():
        if i < 250 or i + 1 >= len(T): continue
        dist = m.gb.MR_SL_ATR * A[i]
        if dist <= 0.5: continue
        q0 = i + 1; e = O[q0]; slp = e - d * dist; hasil = None
        for q in range(q0, min(q0 + 30, len(T))):
            if (d == 1 and L[q] <= slp) or (d == -1 and H[q] >= slp): hasil = (slp, T[q], "SL"); break
            if HR[q] == sm.CLOSE: hasil = (C[q], T[q], "TUTUP"); break
            if cek(q, d): hasil = (C[q], T[q], "KELUAR"); break
        if hasil is None: q = min(q0 + 29, len(T) - 1); hasil = (C[q], T[q], "TUTUP")
        ex, t1, why = hasil
        out.append(dict(d=d, e=e, ex=ex, r0=dist, t0=T[q0], t1=t1, why=why, w=1.0, ip=i, i0=q0, R=(ex - e) * d / dist))
    return out


def sistem(mr): return mm.baseline(D, A, F, ambigu=AMB, mr=mr)


BASE = mm.baseline(D, A, F, ambigu=AMB)
jl = [(int(x["t1"]), float(v)) for x, v in zip(BASE, m.net(BASE))]
P4 = (("p", m.PILIH), ("u", m.UJI), ("k", m.KONF), ("t", (None, None)))


def ukur(nm, G, cetak=True):
    s = {pn: sm.ringkas(G, a, b) for pn, (a, b) in P4}
    gl = [(int(x["t1"]), float(v)) for x, v in zip(G, m.net(G))]
    pu = sg.banding(jl, gl, int(m.ts(m.UJI[0])), int(m.ts(m.UJI[1])))["P_rasio_lebih_baik"]
    pk = sg.banding(jl, gl, int(m.ts(m.KONF[0])), int(T[-1]) + 1)["P_rasio_lebih_baik"]
    mrx = [x for x in G if x.get("strat") == "MR"]; rr = m.net(mrx)
    s2 = sm.ringkas(G, slip=0.20)
    t = s["t"]; th = t["thn"]
    if cetak:
        print(f"{nm:<20} {s['p']['rthn']:+5.1f} · {s['u']['rthn']:+5.1f} · {s['k']['rthn']:+5.1f} · {t['rthn']:+5.1f} | "
              f"/mg {t['per_mg']:.1f} win {t['wr']*100:.0f}% RR {t['rr']:.2f} PF {t['pf']:.2f} DD {t['dd']:.0f}R/{t['ddpct']:.1f}% "
              f"W/L {t['wmax']}/{t['lmax']} thn+ {t['thn_pos']}/{t['thn_n']} tanpa2% {t['tanpa2']:+.0f} slip {s2['rthn']:+.1f} | "
              f"MR n {len(rr)} win {np.mean(rr > 0)*100:.0f}% {rr.sum():+.0f}R | P uji {pu:.2f} P Setra {pk:.2f} | "
              f"lulus pilih {sm.lulus(s['p'])}")
    return dict(s=s, pu=pu, pk=pk, th=th)


print("R/thn bersih: 2015-21 · 2022-Jan25 · Setra · 12t | 12 thn ... | MR | signifikansi vs BASELINE (live)")
U = {"BASELINE (live)": ukur("BASELINE (live)", BASE)}
for X in (50, 60, 70, 80, 90):
    U[f"E-RSI {X}"] = ukur(f"E-RSI {X}", sistem(mr_keluar(lambda q, d, X=X: R2[q] >= X if d == 1 else R2[q] <= 100 - X)))
for n in (5, 10):
    S = sma(n)
    U[f"E-SMA {n}"] = ukur(f"E-SMA {n}", sistem(mr_keluar(lambda q, d, S=S: (C[q] > S[q]) if d == 1 else (C[q] < S[q]))))
kand = {k: v for k, v in U.items() if k != "BASELINE (live)"}
best = max(kand, key=lambda k: kand[k]["s"]["p"]["rthn"])
print(f"\nTERPILIH di 2015-21 (R/thn tertinggi): {best}")
for k in ("BASELINE (live)", best):
    print(f"  {k:<18} " + " · ".join(f"{y} {v:+.0f}" for y, v in U[k]["th"].items()))
