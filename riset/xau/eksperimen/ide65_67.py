"""Putaran riset 20 Nov 2026 (ARAH UTAMA: naikkan edge per trade), WALK-FORWARD BERLABUH 2004-2026.
#65 (antri) KOMBO BUY risiko lebih besar: bobot KOMBO BUY w in {1; 1,25; 1,5; 2}, komponen lain 1. R dinormalkan rata bobot
    di tiap jendela (anggaran risiko sama dengan sistem dasar). Dipilih per jendela di 2005..Y.
#67 (baru) KOMBO SUSULAN: komponen ber-edge paling stabil (#58 KOMBO, +0,17..+0,31R/trade BUY) dipakai juga di jam keputusan
    susulan (candle close 09:00..21:00 WIB) pada hari K6 dilewati. Konstanta KOMBO tetap (tanpa parameter baru):
    Alligator 13/8/5 + histogram MACD 12/26/9 + RSI(2) <=30/>=70 sepakat, market open berikutnya, SL 1,5 ATR, tanpa TP, tutup 23:00.
      A  ganti S3: di jam keputusan pertama hanya KOMBO (tidak sepakat -> tanpa trade)
      B  KOMBO dulu, selain itu S3 (jam keputusan pertama)
      C  B + bila jam pertama tanpa sinyal, pindai jam keputusan berikutnya (s.d. 21:00) hanya untuk KOMBO
    Varian dipilih per jendela walk-forward dari {dasar, A, B, C}.
Uji: pilih <=2010 -> uji 2011-12, ... <=2024 -> uji 2025-26 (semua tahun 2011-2026 hasil uji). P = signifikansi.banding rasio
R/DD vs sistem live 2011-2026, juga 2005-2026 & Setra Feb 2025-skrg (informasi; Setra & 2004-14 sudah pernah dilihat).
Pemakaian (dari folder eksperimen): python ide65_67.py <xau_2004.json> <ambigu_m1_2022_2026.json>"""
import sys
import numpy as np
sys.argv = sys.argv[:3]
exec(open("simetris.py").read().split("KAND = {}")[0])
gb = m.gb
WIN = [(Y, Y + 1, Y + 2) for Y in range(2010, 2025, 2)]

def siap(G):
    G = sorted([x for x in G if m.wib(x["t0"]).year >= 2005], key=lambda z: z["t1"])
    for x, v in zip(G, m.net(G)):
        x["Rn"] = float(v); x["y"] = m.wib(x["t0"]).year; x["k"] = f"{x['strat']}-{'BUY' if x['d'] == 1 else 'SELL'}"
    return G

def tahunan(G, w, y0, y1):
    th = {y: 0.0 for y in range(y0, y1 + 1)}
    for x, ww in zip(G, w):
        if y0 <= x["y"] <= y1: th[x["y"]] += x["Rn"] * ww
    return th

def skor(G, w, y0, y1):
    sel = [ww for x, ww in zip(G, w) if y0 <= x["y"] <= y1]; mw = np.mean(sel) if sel else 1
    v = np.array(list(tahunan(G, w, y0, y1).values())) / max(mw, 1e-9)
    return (-(v < 0).sum(), round(v.mean(), 6))

def ringkas(nm, G, w, y0=2011, y1=2026, base=None):
    """G/w = trade & bobot (sudah ternormalisasi). Cetak tabel per tahun + metrik + P vs live."""
    th = tahunan(G, w, y0, y1); v = np.array(list(th.values()))
    sel = [(x, ww) for x, ww in zip(G, w) if y0 <= x["y"] <= y1 and ww > 0]
    r = np.array([x["Rn"] * ww for x, ww in sel]); c = np.cumsum(r)
    dd = (np.maximum.accumulate(np.concatenate([[0], c]))[1:] - c).max() if len(c) else 0
    base = base or LIVE
    jl = [(int(x["t1"]), x["Rn"]) for x in base if y0 <= x["y"] <= y1]
    gl = [(int(x["t1"]), x["Rn"] * ww) for x, ww in sel]
    t0, t1 = int(m.ts(f"{y0}-01-01")), int(m.ts(f"{y1 + 1}-01-01"))
    P = sg.banding(jl, gl, t0, t1)
    gs = [(t, v_) for t, v_ in gl if t >= m.ts("2025-02-01")]; js = [(t, v_) for t, v_ in jl if t >= m.ts("2025-02-01")]
    Ps = sg.banding(js, gs, int(m.ts("2025-02-01")), t1) if y1 >= 2026 else None
    print(f"{nm:<30} " + " ".join(f"{y % 100}:{x_:+.0f}" for y, x_ in th.items()))
    print(f"{'':<30} R/thn {v.mean():+5.1f} · minus {(v < 0).sum()}/{len(v)} · terburuk {v.min():+.0f} · sd {v.std():.1f} · DD {dd:.0f}R · "
          f"R/trade {r.sum() / max(len(r), 1):+.3f} · {len(r) / len(v) / 52:.1f}/mg · P {P['P_rasio_lebih_baik']:.2f} "
          f"(R/DD {P['penantang']['rasio']} vs {P['juara']['rasio']})" + (f" · Setra P {Ps['P_rasio_lebih_baik']:.2f} "
          f"({Ps['penantang']['R_thn']:+.1f} vs {Ps['juara']['R_thn']:+.1f} R/thn)" if Ps else ""))
    return dict(rthn=v.mean(), minus=int((v < 0).sum()), terburuk=v.min(), sd=v.std(), dd=dd, P=P['P_rasio_lebih_baik'],
                Ps=Ps['P_rasio_lebih_baik'] if Ps else None, th=th)

LIVE = siap(BASE)
print(f"Data {m.wib(T[0]):%Y-%m-%d} s.d. {m.wib(T[-1]):%Y-%m-%d %H:%M} WIB · trade live 2005-2026: {len(LIVE)}")

# ---------------- #65 KOMBO BUY bobot ----------------
print("\n=== #65 KOMBO BUY risiko lebih besar (uji walk-forward 2011-2026) ===")
ringkas("SISTEM LIVE", LIVE, [1.0] * len(LIVE))
KAND65 = (1.0, 1.25, 1.5, 2.0)
def bobot65(wk): return [wk if x["k"] == "KOMBO-BUY" else 1.0 for x in LIVE]
for wk in KAND65[1:]:
    w = bobot65(wk); mw = np.mean([ww for x, ww in zip(LIVE, w) if x["y"] >= 2011])
    ringkas(f"  tetap KOMBO BUY x{wk}", LIVE, [ww / mw for ww in w])
W = {}; pil = []
for Y, a, b in WIN:
    best = max(((skor(LIVE, bobot65(wk), 2005, Y), wk) for wk in KAND65))
    pil.append((Y, best[1])); w = bobot65(best[1]); mw = np.mean([ww for x, ww in zip(LIVE, w) if a <= x["y"] <= b])
    for j, x in enumerate(LIVE):
        if a <= x["y"] <= b: W[j] = w[j] / mw
idx = sorted(W)
ringkas("#65 WF", [LIVE[j] for j in idx], [W[j] for j in idx]); print("   pilihan:", pil)

# ---------------- #67 KOMBO susulan ----------------
mp = (H + L) / 2
s13, s8, s5 = mm._smma(mp, 13), mm._smma(mp, 8), mm._smma(mp, 5)
e_ = lambda x, n: np.array(gb.ema(list(x), n))
mac = e_(C, 12) - e_(C, 26); MH = mac - e_(mac, 9)
def kombo_at(i):
    if i < 8: return 0
    jaw, teeth, lips = s13[i - 8], s8[i - 5], s5[i - 3]
    alg = 1 if lips > teeth > jaw else -1 if lips < teeth < jaw else 0
    mc = 1 if MH[i] > 0 else -1
    rs = 1 if R2[i] <= gb.KOMBO_RSI_BUY else -1 if R2[i] >= gb.KOMBO_RSI_SELL else 0
    return alg if (alg != 0 and alg == mc == rs) else 0

JAM = set(gb.SUS_JAM_UTC); SIG = mm.sinyal_live(D)
def susulan(var):
    out = []
    for x in m.jalankan({"tren_lawan_w": ("ema200", 0.0), "ambigu": AMB}, D, A, F):
        if x["w"] != 0 or x["ip"] in SIG: continue
        q = x["i0"]
        while q < len(T) and HR[q] not in JAM and HR[q] != sm.CLOSE: q += 1
        if q >= len(T) - 1 or HR[q] not in JAM: continue
        d, sl, tp, st = 0, None, None, None
        k = kombo_at(q) if var in "ABC" else 0
        if k: d, sl, tp, st = k, gb.KOMBO_SL_ATR, None, "SUSK"
        elif var in "BC" or var == "0":
            if R2[q] <= gb.SUS_BUY or R2[q] >= gb.SUS_SELL:
                d = 1 if R2[q] <= gb.SUS_BUY else -1; sl, tp, st = gb.SUS_SL_ATR, gb.SUS_TP_R, "SUS"
        if not d and var == "C":
            q2 = q + 1
            while q2 < len(T) - 1 and HR[q2] != sm.CLOSE:
                if HR[q2] in JAM:
                    k = kombo_at(q2)
                    if k: d, sl, tp, st, q = k, gb.KOMBO_SL_ATR, None, "SUSK", q2; break
                q2 += 1
        if not d: continue
        dist = sl * A[q]
        if dist <= 0.5: continue
        j = q + 1; e = O[j]
        ex, t1, why = sm._kelola(D, j, d, e, e - d * dist, e + d * tp * dist if tp else None)
        out.append(dict(d=d, e=e, ex=ex, r0=dist, t0=T[j], t1=t1, why=why, w=1.0, ip=x["ip"], i0=j, R=(ex - e) * d / dist, strat=st))
    return out

pagi = [x for x in BASE if x["strat"] not in ("SUS",)]
SIS = {"0": LIVE}
for v in "ABC":
    SIS[v] = siap([dict(x) for x in pagi] + susulan(v))
print("\n=== #67 KOMBO susulan: tetap, 2005-2026 (informasi) & uji 2011-2026 ===")
NAMA = {"0": "dasar (S3 live)", "A": "A KOMBO ganti S3", "B": "B KOMBO lalu S3", "C": "C B + pindai jam"}
for v, G in SIS.items():
    ringkas(f"{NAMA[v]} 05-26", G, [1.0] * len(G), 2005, 2026)
    sk = [x for x in G if x["strat"] in ("SUS", "SUSK")]
    for s in ("SUS", "SUSK"):
        for dd_ in (1, -1):
            r = [x["Rn"] for x in sk if x["strat"] == s and x["d"] == dd_]
            if r: print(f"      {s}-{'BUY' if dd_ == 1 else 'SELL'}: n {len(r)} · R/trade {np.mean(r):+.3f} · win {np.mean(np.array(r) > 0) * 100:.0f}%"
                        f" · 05-14 {np.mean([x['Rn'] for x in sk if x['strat'] == s and x['d'] == dd_ and x['y'] <= 2014] or [0]):+.3f}"
                        f" · 15-21 {np.mean([x['Rn'] for x in sk if x['strat'] == s and x['d'] == dd_ and 2015 <= x['y'] <= 2021] or [0]):+.3f}"
                        f" · 22-26 {np.mean([x['Rn'] for x in sk if x['strat'] == s and x['d'] == dd_ and x['y'] >= 2022] or [0]):+.3f}")
# walk-forward pilih varian
sel = []; pil = []
for Y, a, b in WIN:
    best = max(((skor(G, [1.0] * len(G), 2005, Y), v) for v, G in SIS.items()))
    pil.append((Y, best[1])); sel += [x for x in SIS[best[1]] if a <= x["y"] <= b]
ringkas("#67 WF (pilih varian)", sel, [1.0] * len(sel)); print("   pilihan:", pil)
for v in "ABC":
    G = [x for x in SIS[v] if x["y"] >= 2011]; ringkas(f"  {NAMA[v]} 11-26", G, [1.0] * len(G))
