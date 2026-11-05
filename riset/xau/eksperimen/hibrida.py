"""Ide #42b (5 Nov 2026, pemilik): integrasi bot live + Connors cermin. Tren D1 (close 07:00 vs SMA n hari) NAIK -> aturan MR
live persis (BUY <= 43,76, SELL >= 85); TURUN -> cermin (SELL >= 100-b, BUY hanya <= 100-kuat). Hari tanpa MR -> K6 + susulan.
n 100/200, b 30/43,76, kuat 85/90/95. Pemakaian: python hibrida.py <sambung.json> <ambigu.json>"""
import sys, itertools
sys.argv = sys.argv[:3]
exec(open("simetris.py").read().split("KAND = {}")[0])
def hib(n, b, kuat):
    ma = sma(dC, n); sig = {}
    for k, i in enumerate(i07):
        r = r07[k]
        if np.isnan(ma[k]) or dC[k] > ma[k]:
            if r <= m.gb.MR_BUY: sig[i] = 1
            elif r >= m.gb.MR_SELL: sig[i] = -1
        else:
            if r >= 100 - b: sig[i] = -1
            elif r <= 100 - kuat: sig[i] = 1
    return sig
print("R/thn: 2015-21 · 2022-Jan25 · Setra · 12t | ... | P uji vs bot live")
baris("BOT LIVE", ukur(BASE))
baris("Connors MA200 b30 kuat85 (#42)", ukur(sistem(mm.sinyal_connors(D, 200))))
U = {}
for n, b, kuat in itertools.product((100, 200), (30.0, 43.76), (85.0, 90.0, 95.0)):
    U[(n, b, kuat)] = ukur(sistem(hib(n, b, kuat)))
    baris(f"HIBRIDA MA{n} turun: SELL>={100-b:g} BUY<={100-kuat:g}", U[(n, b, kuat)])
best = max(U, key=lambda k: U[k]["skor"]); u = U[best]
gl = [(int(x["t1"]), float(v)) for x, v in zip(u["G"], m.net(u["G"]))]
print(f"\nTERPILIH di 2015-21: {best} · P Setra {sg.banding(jl, gl, int(m.ts(m.KONF[0])), int(T[-1]))['P_rasio_lebih_baik']:.2f}")
print("hibrida: " + " · ".join(f"{y} {v:+.0f}" for y, v in u["th"].items()))
print("live:    " + " · ".join(f"{y} {v:+.0f}" for y, v in ukur(BASE)["th"].items()))
