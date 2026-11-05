"""Ide #42 (5 Nov 2026, pemilik: "baik di setiap tahun, tidak condong BUY"). Sumber: Connors & Alvarez (2008) RSI(2) + filter
MA 200 hari dan versi cermin short; RSI adaptif berbasis persentil bergulir (TradingView: Adaptive RSI/BOSWaves, RSI Median
Deviation); saklar rezim ADX harian dengan histeresis 20/30 (Top Gun Fast 1, MQL5; Unger: tren & MR saling menyeimbangkan).
Keluarga (MR jam 07:00; hari tanpa MR -> K6 + susulan seperti bot live; tutup 23:00):
  C  Connors cermin: tren D1 naik (close 07:00 > MA n hari) -> BUY RSI<=b, SELL hanya RSI>=s_kuat; tren turun -> cermin
     (SELL RSI>=100-b, BUY hanya RSI<=100-s_kuat). n 50/100/200, b 30/43,76, s_kuat 85/90/95(=tanpa SELL lawan tren efektif)
  P  ambang persentil bergulir RSI2 07:00 (jendela 60/120/250 hari, q 25/35/45) -> BUY <= persentil q, SELL >= persentil 1-q
  X  saklar ADX(14) harian: ADX <= lo -> MR (ambang live), ADX >= hi -> K6 saja; histeresis (lo,hi) (15,25)/(20,30)/(25,35)
Metrik "tiap tahun": tahun positif, tahun terburuk, simpangan R tahunan, porsi R dari SELL. Pilih 2015-2021 (skor = R/thn
pilih x tahun positif pilih), uji 2022-Jan 2025 & Setra. Pemakaian: python simetris.py <sambung.json> <ambigu.json>"""
import sys, os, json, itertools
import numpy as np
import audit_mesin as m, strat_mesin as sm, multi_mesin as mm
sys.path.insert(0, os.path.join(m.REPO, "riset")); import signifikansi as sg
D = m.muat(sys.argv[1]); T, O, H, L, C = D
A = np.array(m.atr(list(H), list(L), list(C), 14)); F = m.fitur(D, A)
AMB = {int(k): v for k, v in json.load(open(sys.argv[2])).items()}
HR = ((T // 3600) % 24).astype(int); R2 = mm.rsi(C, 2)
i07 = [int(i) for i in np.flatnonzero(HR == sm.PLACE)]
# bar harian berakhir di close 07:00 WIB
dO, dH, dL, dC = [], [], [], []
prev = None
for i in i07:
    a = prev + 1 if prev is not None else max(0, i - 23)
    dO.append(O[a]); dH.append(H[a:i + 1].max()); dL.append(L[a:i + 1].min()); dC.append(C[i]); prev = i
dO, dH, dL, dC = map(np.array, (dO, dH, dL, dC))
def sma(x, n): c = np.cumsum(np.insert(x, 0, 0)); out = np.full(len(x), np.nan); out[n - 1:] = (c[n:] - c[:-n]) / n; return out
def adx(h, l, c, n=14):
    tr = np.maximum(h[1:] - l[1:], np.maximum(abs(h[1:] - c[:-1]), abs(l[1:] - c[:-1])))
    up, dn = h[1:] - h[:-1], l[:-1] - l[1:]
    pdm = np.where((up > dn) & (up > 0), up, 0); ndm = np.where((dn > up) & (dn > 0), dn, 0)
    def w(x):
        o = np.zeros(len(x)); o[0] = x[0]
        for k in range(1, len(x)): o[k] = o[k - 1] + (x[k] - o[k - 1]) / n
        return o
    atr_, p, q = w(tr), w(pdm), w(ndm); pdi, ndi = 100 * p / atr_, 100 * q / atr_
    dx = 100 * abs(pdi - ndi) / np.maximum(pdi + ndi, 1e-9); return np.concatenate([[0], w(dx)])
ADX = adx(dH, dL, dC)
r07 = np.array([R2[i] for i in i07])
BASE = mm.baseline(D, A, F, ambigu=AMB)
jl = [(int(x["t1"]), float(v)) for x, v in zip(BASE, m.net(BASE))]
K6ALL = mm.baseline(D, A, F, ambigu=AMB, sig={})     # cache tidak dipakai mm, cukup untuk referensi

def ukur(G):
    G = sorted(G, key=lambda z: z["t1"]); r = m.net(G)
    th = {}; sel = 0.0; tot = 0.0
    for x, v in zip(G, r):
        th.setdefault(m.wib(x["t0"]).year, 0.0); th[m.wib(x["t0"]).year] += v
        tot += v; sel += v if x["d"] == -1 else 0
    s = {pn: sm.ringkas(G, a, b) for pn, (a, b) in (("p", m.PILIH), ("u", m.UJI), ("k", m.KONF), ("t", (None, None)))}
    pil = [v for y, v in th.items() if y <= 2021]
    return dict(G=G, th=th, s=s, sell=sel, tot=tot, skor=s["p"]["rthn"] * sum(v > 0 for v in pil) / len(pil))
def baris(nm, u):
    s, th = u["s"], u["th"]; gl = [(int(x["t1"]), float(v)) for x, v in zip(u["G"], m.net(u["G"]))]
    pu = sg.banding(jl, gl, int(m.ts(m.UJI[0])), int(m.ts(m.UJI[1])))["P_rasio_lebih_baik"]
    v = np.array(list(th.values()))
    print(f"{nm:<44} {s['p']['rthn']:+5.1f} · {s['u']['rthn']:+5.1f} · {s['k']['rthn']:+5.1f} · {s['t']['rthn']:+5.1f} | /mg {s['t']['per_mg']:.1f}"
          f" DD {s['t']['dd']:.0f}R | thn+ {int((v > 0).sum())}/12 terburuk {v.min():+.0f} sd {v.std():.1f} | SELL {u['sell']:+.0f}R dr {u['tot']:+.0f} | P {pu:.2f}")
def sistem(sig): return mm.baseline(D, A, F, ambigu=AMB, sig=sig)

KAND = {}
for n, b, sk in itertools.product((50, 100, 200), (30.0, 43.76), (85.0, 90.0, 95.0)):
    ma = sma(dC, n); sig = {}
    for k, i in enumerate(i07):
        if np.isnan(ma[k]): continue
        r = r07[k]
        if dC[k] > ma[k]:
            if r <= b: sig[i] = 1
            elif r >= sk: sig[i] = -1
        else:
            if r >= 100 - b: sig[i] = -1
            elif r <= 100 - sk: sig[i] = 1
    KAND[f"C MA{n} b{b:g} kuat{sk:g}"] = sig
for w, q in itertools.product((60, 120, 250), (0.25, 0.35, 0.45)):
    sig = {}
    for k, i in enumerate(i07):
        if k < w: continue
        h = r07[k - w:k]; lo, hi = np.quantile(h, q), np.quantile(h, 1 - q)
        if r07[k] <= lo: sig[i] = 1
        elif r07[k] >= hi: sig[i] = -1
    KAND[f"P jendela{w} q{q:g}"] = sig
live = mm.sinyal_mr(D)
for lo, hi in ((15, 25), (20, 30), (25, 35)):
    st = "MR"; sig = {}
    for k, i in enumerate(i07):
        a_ = ADX[k - 1] if k else 0          # ADX hari sebelumnya (tanpa intip)
        if a_ >= hi: st = "TREN"
        elif a_ <= lo: st = "MR"
        if st == "MR" and i in live: sig[i] = live[i]
    KAND[f"X ADX {lo}/{hi}"] = sig
print("R/thn: 2015-21 · 2022-Jan25 · Setra · 12t | ... | P uji vs bot live")
baris("BOT LIVE (MR SELL>=85)", ukur(BASE))
baris("bot 71,22 (sebelum #40)", ukur(sistem(mm.sinyal_mr(D, mr_sell=71.22))))
U = {nm: ukur(sistem(sig)) for nm, sig in KAND.items()}
for fam in ("C", "P", "X"):
    print(f"\n--- keluarga {fam} (urut skor pilih; 5 teratas)")
    for nm in sorted([k for k in U if k.startswith(fam)], key=lambda k: -U[k]["skor"])[:5]: baris(nm, U[nm])
best = max(U, key=lambda k: U[k]["skor"])
print(f"\nTERPILIH (skor pilih tertinggi semua keluarga): {best}")
print("per tahun:  " + " · ".join(f"{y} {v:+.0f}" for y, v in U[best]["th"].items()))
print("bot live:   " + " · ".join(f"{y} {v:+.0f}" for y, v in ukur(BASE)["th"].items()))
