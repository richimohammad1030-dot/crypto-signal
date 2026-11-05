"""Ide #37 (5 Nov 2026, permintaan pemilik): SINYAL SUSULAN pada hari tanpa trade (K6 dilewati karena batas batal tersentuh).
Realistis sesuai jadwal bot (tiap 2 jam): keputusan di candle pertama yang close 09:00/11:00/.../21:00 WIB setelah batas batal
tersentuh; masuk mulai candle berikutnya; tutup 23:00 WIB; maks 1 posisi/hari (hari susulan = hari tanpa posisi).
Kandidat: S1 ikuti tembusan (arah lawan tren, market) · S2 fade tembusan palsu (searah tren, market, hanya bila close keputusan
kembali di dalam range) · S3 RSI2 mean reversion di jam keputusan · S4 breakout ulang searah tren (stop di high/low 3 candle
terakhir) · S5 straddle OCO range 3 candle terakhir. Seleksi 2015-2021; uji 2022-Jan 2025; Setra. Biaya 0,40 USD.
Pemakaian: python susulan.py <xau_sambung.json> <ambigu.json>"""
import sys, os, json, itertools
import numpy as np
import audit_mesin as m
import strat_mesin as sm
import multi_mesin as mm
sys.path.insert(0, os.path.join(m.REPO, "riset")); import signifikansi as sg

D = m.muat(sys.argv[1]); T, O, H, L, C = D
A = np.array(m.atr(list(H), list(L), list(C), 14)); F = m.fitur(D, A)
AMB = {int(k): v for k, v in json.load(open(sys.argv[2])).items()}
HR = ((T // 3600) % 24).astype(int)
R2 = mm.rsi(C, 2)
KEPUTUSAN = {1, 3, 5, 7, 9, 11, 13}          # jam UTC open candle yang close 09:00, 11:00, ..., 21:00 WIB

sig = mm.sinyal_mr(D)
k6_all = m.jalankan({"tren_lawan_w": ("ema200", 0.0), "ambigu": AMB}, D, A, F)
BASE = mm.baseline(D, A, F, ambigu=AMB)
hari = []                                       # (ip, i_keputusan, arah_tren, hi, lo)
for x in k6_all:
    if x["w"] != 0 or x["ip"] in sig: continue
    q = x["i0"]
    while q < len(T) and HR[q] not in KEPUTUSAN and HR[q] != sm.CLOSE: q += 1
    if q >= len(T) - 1 or HR[q] not in KEPUTUSAN: continue
    ip = x["ip"]; tren = -x["d"]                 # trade w=0 adalah sisi LAWAN tren
    hari.append((ip, q, tren, H[ip - 2:ip + 1].max(), L[ip - 2:ip + 1].min()))
print(f"hari susulan (K6 dilewati, keputusan sebelum 23:00): {len(hari)}")


def jalan_di(rencana, sl, tp):
    """rencana: list (ip, q, orders). Order dievaluasi mulai candle q+1 s.d. tutup 23:00; >1 terisi di candle sama -> terburuk."""
    out = []
    for ip, q, orders in rencana:
        if not orders: continue
        dist = sl * A[q]
        if dist <= 0.5: continue
        hasil = None
        for j in range(q + 1, min(q + 20, len(T))):
            kand = []
            for d, jenis, lvl in orders:
                if jenis == "market":
                    if j == q + 1: kand.append((d, O[j]))
                elif jenis == "stop":
                    if (d == 1 and H[j] >= lvl) or (d == -1 and L[j] <= lvl):
                        kand.append((d, max(lvl, O[j]) if d == 1 else min(lvl, O[j])))
                else:
                    if (d == 1 and L[j] <= lvl) or (d == -1 and H[j] >= lvl):
                        kand.append((d, min(lvl, O[j]) if d == 1 else max(lvl, O[j])))
            if kand:
                ops = []
                for d, e in kand:
                    ex, t1, why = sm._kelola(D, j, d, e, e - d * dist, e + d * tp * dist if tp else None)
                    ops.append(dict(d=d, e=e, ex=ex, r0=dist, t0=T[j], t1=t1, why=why, w=1.0, ip=ip, i0=j, R=(ex - e) * d / dist,
                                    strat="SUSULAN"))
                hasil = min(ops, key=lambda z: z["R"]); break
            if HR[j] == sm.CLOSE: break
        if hasil: out.append(hasil)
    return out


pl_q = [q for ip, q, *_ in hari if T[q] < m.ts("2022-01-01")]
KAND = {}
for k in KAND: pass
KAND["S1 ikuti tembusan"] = lambda: [(ip, q, [(-tr, "market", None)]) for ip, q, tr, hi, lo in hari]
KAND["S2 fade tembusan palsu"] = lambda: [(ip, q, [(tr, "market", None)] if lo < C[q] < hi else []) for ip, q, tr, hi, lo in hari]
for qq in (0.35, 0.5):
    lo_, hi_ = np.quantile(R2[pl_q], qq), np.quantile(R2[pl_q], 1 - qq)
    KAND[f"S3 RSI2 kuantil {int(qq*100)}%"] = (lambda lo_=lo_, hi_=hi_: [(ip, q, [(1 if R2[q] <= lo_ else -1, "market", None)])
                                              if (R2[q] <= lo_ or R2[q] >= hi_) else (ip, q, []) for ip, q, tr, hi, lo in hari])
KAND["S4 breakout ulang searah tren"] = lambda: [(ip, q, [(tr, "stop", H[q - 2:q + 1].max() if tr == 1 else L[q - 2:q + 1].min())])
                                                 for ip, q, tr, hi, lo in hari]
KAND["S5 straddle OCO range baru"] = lambda: [(ip, q, [(1, "stop", H[q - 2:q + 1].max()), (-1, "stop", L[q - 2:q + 1].min())])
                                              for ip, q, tr, hi, lo in hari]
SL, TP = (1.0, 1.5, 2.0, 3.0), (1, 2, 4, None)
res = {}
for (nm, fn), sl, tp in itertools.product(KAND.items(), SL, TP):
    tr = jalan_di(fn(), sl, tp)
    res[(nm, sl, tp)] = (sm.ringkas(tr, *m.PILIH), tr)


def nb(k):
    nm, sl, tp = k; o = []
    for s2 in SL:
        if abs(SL.index(s2) - SL.index(sl)) == 1: o.append((nm, s2, tp))
    for t2 in TP:
        if abs(TP.index(t2) - TP.index(tp)) == 1: o.append((nm, sl, t2))
    return o


print("\n=== Susulan saja, periode pilih 2015-2021 (terbaik per kandidat menurut skor tetangga)")
best = {}
for k, (s, tr) in res.items():
    sk = min(s["ratio"], np.mean([res[j][0]["ratio"] for j in nb(k)])) if s["n"] >= 30 else -9
    if k[0] not in best or sk > best[k[0]][0]: best[k[0]] = (sk, k)
jl = [(int(x["t1"]), float(v)) for x, v in zip(BASE, m.net(BASE))]
for nm, (sk, k) in sorted(best.items(), key=lambda z: -z[1][0]):
    tr = res[k][1]
    print(f"\n{k}  skor {sk:+.2f}")
    for pn, (a, b) in (("pilih", m.PILIH), ("uji", m.UJI), ("Setra", m.KONF), ("12 thn", (None, None))):
        s = sm.ringkas(tr, a, b)
        print(f"   susulan {pn:<6} n {s['n']:>3} win {s['wr']*100:3.0f}% RR {s['rr']:.2f} PF {s['pf']:.2f} exp {s['avg']:+.3f} R/thn {s['rthn']:+5.1f}")
    G = sorted(BASE + tr, key=lambda x: x["t1"]); gl = [(int(x["t1"]), float(v)) for x, v in zip(G, m.net(G))]
    for pn, (a, b) in (("pilih", m.PILIH), ("uji", m.UJI), ("Setra", m.KONF), ("12 thn", (None, None))):
        s = sm.ringkas(G, a, b); s0 = sm.ringkas(BASE, a, b)
        print(f"   GABUNG {pn:<6} /mg {s['per_mg']:.1f} win {s['wr']*100:.0f}% PF {s['pf']:.2f} R/thn {s['rthn']:+5.1f} (baseline {s0['rthn']:+5.1f}) "
              f"DD {s['dd']:.0f}R W/L {s['wmax']}/{s['lmax']} thn+ {s['thn_pos']}/{s['thn_n']}")
    r = sg.banding(jl, gl, int(m.ts(m.UJI[0])), int(m.ts(m.UJI[1])))
    print(f"   P_rasio gabung vs baseline (uji): {r['P_rasio_lebih_baik']:.3f}")
