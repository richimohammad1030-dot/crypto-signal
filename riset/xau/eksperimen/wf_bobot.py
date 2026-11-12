"""Putaran riset 13 Nov 2026 (ARAH UTAMA: naikkan edge per trade / turunkan variansi tahunan), WALK-FORWARD BERLABUH 2004-2026.
#64 (baru) bobot risiko per KOMPONEN sebanding edge masa lalu: komponen = strategi x arah (KOMBO, MR, K6, SUS x BUY/SELL).
    Tiap jendela: rata R bersih/trade komponen di 2005..Y -> bobot via peta tetap. Peta dipilih per jendela dari 3 kandidat
    (skor = tahun minus paling sedikit di 2005..Y, lalu R/thn dinormalkan rata bobot):
      P1 tangga: avg<0 -> 0 · 0..0,05 -> 0,5 · 0,05..0,12 -> 1 · >0,12 -> 1,5
      P2 lunak : avg<0 -> 0,5 · selain itu 1 · >0,12 -> 1,5
      P3 buang : avg<0 -> 0 · selain itu 1
#45 (antri) ukuran posisi target-volatilitas: w = clip(median ATR_rel 250 hari terakhir / ATR_rel sekarang, lo, hi);
    kandidat (lo,hi) (0,5;1,5) (0,75;1,25) (0,5;2) dan kebalikannya (w = ATR_rel/median, pemenang saat volatil).
Uji: pilih <=2010 -> uji 2011-12, ... <=2024 -> uji 2025-26. Hasil per tahun 2011-2026 SEMUA hasil uji; R dinormalkan
dengan rata bobot (anggaran risiko sama dgn sistem dasar); P = signifikansi.banding rasio R/DD vs sistem live (skala-bebas).
Pemakaian: python wf_bobot.py <xau_2004.json> <ambigu.json>"""
import sys
import numpy as np
sys.argv = sys.argv[:3]
exec(open("simetris.py").read().split("KAND = {}")[0])
G0 = sorted([x for x in BASE if m.wib(x["t0"]).year >= 2005], key=lambda z: z["t1"])
for x, v in zip(G0, m.net(G0)): x["Rn"] = float(v); x["y"] = m.wib(x["t0"]).year; x["k"] = f"{x['strat']}-{'BUY' if x['d'] == 1 else 'SELL'}"
AR = A / C
def medlag(i, n=250 * 24):
    return np.median(AR[max(0, i - n):i + 1])
for x in G0: x["vr"] = AR[x["ip"]] / medlag(x["ip"])
WIN = [(Y, Y + 1, Y + 2) for Y in range(2010, 2025, 2)]
def tahunan(G, w, y0, y1):
    th = {y: 0.0 for y in range(y0, y1 + 1)}
    for x, ww in zip(G, w):
        if y0 <= x["y"] <= y1: th[x["y"]] += x["Rn"] * ww
    return th
def skor(G, w, y0, y1):
    sel = [ww for x, ww in zip(G, w) if y0 <= x["y"] <= y1]; mw = np.mean(sel) if sel else 1
    v = np.array(list(tahunan(G, w, y0, y1).values())) / max(mw, 1e-9)
    return (-(v < 0).sum(), v.mean())
PETA = {"P1": lambda a: 0 if a < 0 else 0.5 if a < 0.05 else 1 if a < 0.12 else 1.5,
        "P2": lambda a: 0.5 if a < 0 else 1.5 if a > 0.12 else 1,
        "P3": lambda a: 0 if a < 0 else 1}
def bobot60(nm, Y):
    av = {}
    for x in G0:
        if x["y"] <= Y: av.setdefault(x["k"], []).append(x["Rn"])
    av = {k: np.mean(v) for k, v in av.items()}
    return [PETA[nm](av.get(x["k"], 0.0)) for x in G0], av
VOL = {f"{'inv' if inv else 'vt'} {lo}-{hi}": (lambda x, lo=lo, hi=hi, inv=inv: float(np.clip(x["vr"] if inv else 1 / x["vr"], lo, hi)))
       for lo, hi in ((0.5, 1.5), (0.75, 1.25), (0.5, 2.0)) for inv in (False, True)}
def wf(keluarga):
    """Walk-forward: tiap jendela pilih kandidat terbaik di 2005..Y, terapkan di Y+1..Y+2. Kembalikan bobot hasil uji."""
    W = {}; pilih = []
    for Y, a, b in WIN:
        best = None
        for nm in keluarga:
            w = bobot60(nm, Y)[0] if nm in PETA else [VOL[nm](x) for x in G0]
            s = skor(G0, w, 2005, Y)
            if best is None or s > best[0]: best = (s, nm, w)
        pilih.append((Y, best[1]))
        sel = [ww for x, ww in zip(G0, best[2]) if a <= x["y"] <= b]; mw = np.mean(sel)
        for j, x in enumerate(G0):
            if a <= x["y"] <= b: W[j] = best[2][j] / mw
    return W, pilih
def lapor(nm, W):
    idx = sorted(W); G = [G0[j] for j in idx]; w = [W[j] for j in idx]
    th = tahunan(G, w, 2011, 2026); v = np.array(list(th.values()))
    r = np.array([x["Rn"] * ww for x, ww in zip(G, w)]); c = np.cumsum(r)
    dd = (np.maximum.accumulate(np.concatenate([[0], c]))[1:] - c).max()
    jl = [(int(x["t1"]), x["Rn"]) for x in G0 if 2011 <= x["y"]]
    gl = [(int(x["t1"]), x["Rn"] * ww) for x, ww in zip(G, w) if ww > 0]
    P = sg.banding(jl, gl, int(m.ts("2011-01-01")), int(m.ts("2027-01-01")))
    aktif = sum(1 for ww in w if ww > 0)
    print(f"{nm:<26} " + " ".join(f"{y % 100}:{v_:+.0f}" for y, v_ in th.items()))
    print(f"{'':<26} R/thn {v.mean():+5.1f} · minus {(v < 0).sum()}/16 · terburuk {v.min():+.0f} · sd {v.std():.1f} · DD {dd:.0f}R · "
          f"R/trade aktif {r.sum() / max(aktif, 1):+.3f} · trade aktif {aktif / 16 / 52:.1f}/mg · P rasio {P['P_rasio_lebih_baik']:.2f} (R/DD {P['penantang']['rasio']} vs {P['juara']['rasio']})")
DASAR = {j: 1.0 for j, x in enumerate(G0) if x["y"] >= 2011}
print("Uji walk-forward 2011-2026 (semua tahun hasil uji), R bersih per tahun:")
lapor("SISTEM LIVE (bobot 1)", DASAR)
W, p = wf(list(PETA)); lapor("#64 bobot komponen (WF)", W); print("   pilihan:", p)
for nm in PETA:
    W, _ = wf([nm]); lapor(f"  #64 {nm} saja", W)
W, p = wf(list(VOL)); lapor("#45 target-vol (WF)", W); print("   pilihan:", p)
for nm in VOL:
    W, _ = wf([nm]); lapor(f"  #45 {nm}", W)
# edge komponen per periode (informasi)
print("\nEdge komponen (R bersih/trade, n) 2005-14 · 2015-21 · 2022-26:")
for k in sorted({x["k"] for x in G0}):
    s = []
    for a, b in ((2005, 2014), (2015, 2021), (2022, 2026)):
        r = [x["Rn"] for x in G0 if x["k"] == k and a <= x["y"] <= b]; s.append(f"{np.mean(r):+.3f} ({len(r)})" if r else "-")
    print(f"  {k:<11} " + " · ".join(s))
