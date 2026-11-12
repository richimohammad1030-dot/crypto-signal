"""LANGKAH 1 pembagian data (pemilik 6 Nov 2026; dijalankan sekali Jumat 13 Nov 2026): uji APA ADANYA (tanpa ubah parameter)
bot live (#58 kombinasi + hibrida MA100), hibrida MA100 tanpa kombinasi (versi 6 Nov), hibrida MA200, #40 (tanpa hibrida),
MR SELL 71,22 (versi sebelum #40), dan penambal #50 (zona netral 1% di sekitar MA200) di 2005-2014 = data yang tidak dipakai
merancang (2004 = pemanasan indikator). Setelah ini 2004-2014 dianggap SUDAH DILIHAT.
Pemakaian: python langkah1_2004.py <xau_2004.json> <ambigu.json>"""
import sys
import numpy as np
sys.argv = sys.argv[:3]
exec(open("simetris.py").read().split("KAND = {}")[0])
ma200 = sma(dC, 200)
def aturan(r, rezim):
    if rezim == "naik": return 1 if r <= m.gb.MR_BUY else -1 if r >= m.gb.MR_SELL else 0
    if rezim == "turun": return -1 if r >= 70 else 1 if r <= 15 else 0
    if rezim == "netral_ketat": return 1 if r <= 15 else -1 if r >= 85 else 0
    return 0
def zona(X, mode):
    out = {}
    for k, i in enumerate(i07):
        if np.isnan(ma200[k]): rz = "naik"
        elif abs(dC[k] / ma200[k] - 1) * 100 < X: rz = mode
        else: rz = "naik" if dC[k] > ma200[k] else "turun"
        d = aturan(r07[k], rz)
        if d: out[i] = d
    return out
VAR = {
    "BOT LIVE (kombinasi + hibrida MA100)": BASE,
    "Hibrida MA100 tanpa kombinasi (6 Nov)": sistem(mm.sinyal_hibrida(D)),
    "Hibrida MA200 (#42b)": sistem(mm.sinyal_hibrida(D, 200)),
    "#40 tanpa hibrida": sistem(mm.sinyal_mr(D)),
    "MR SELL 71,22 (sblm #40)": sistem(mm.sinyal_mr(D, mr_sell=71.22)),
    "#50 zona 1% -> ketat": sistem(zona(1, "netral_ketat")),
    "#50 zona 1% -> K6 saja": sistem(zona(1, "netral_k6")),
}
def nilai(G, y0, y1):
    G = sorted([x for x in G if y0 <= m.wib(x["t0"]).year <= y1], key=lambda z: z["t1"]); r = m.net(G)
    th = {y: 0.0 for y in range(y0, y1 + 1)}
    for x, v in zip(G, r): th[m.wib(x["t0"]).year] += v
    c = np.cumsum(r); dd = (np.maximum.accumulate(np.concatenate([[0], c]))[1:] - c).max() if len(c) else 0
    pf = r[r > 0].sum() / -r[r < 0].sum() if (r < 0).any() else np.inf
    v = np.array(list(th.values()))
    return dict(th=th, rthn=v.mean(), minus=int((v < 0).sum()), worst=v.min(), dd=dd, pf=pf, n=len(G), win=(r > 0).mean() * 100,
                avg=r.mean(), sd=v.std())
print("2005-2014 (data belum dilihat), bersih biaya 0,40 USD, R per tahun:")
print(f"{'varian':<40} " + " ".join(f"{y % 100:>4}" for y in range(2005, 2015)) + " | R/thn minus terburuk  PF  DD  R/trade")
for nm, G in VAR.items():
    a = nilai(G, 2005, 2014)
    print(f"{nm:<40} " + " ".join(f"{v:+4.0f}" for v in a["th"].values()) +
          f" | {a['rthn']:+5.1f} {a['minus']:>3}/10 {a['worst']:+5.0f} {a['pf']:.2f} {a['dd']:3.0f} {a['avg']:+.3f}")
print("\nPembanding (sudah dilihat): 2015-2026 dan 2005-2026")
for nm, G in VAR.items():
    b = nilai(G, 2015, 2026); c = nilai(G, 2005, 2026)
    print(f"{nm:<40} 15-26 {b['rthn']:+5.1f} ({b['minus']}/12 minus, terburuk {b['worst']:+.0f}) · 05-26 {c['rthn']:+5.1f} "
          f"({c['minus']}/22 minus, terburuk {c['worst']:+.0f}, DD {c['dd']:.0f}R, PF {c['pf']:.2f}, {c['avg']:+.3f}R/trade, sd thn {c['sd']:.1f}, /mg {c['n']/22/52:.1f})")
