"""PUTARAN RISET 11 Nov 2026 · ARAH: naikkan EDGE PER TRADE / turunkan variansi tahunan.
PUSTAKA indikator klasik (pola riset/xau/eksperimen/pustaka.py & kombinasi.py) sebagai KOMPONEN SUARA di H1 koin saat sinyal juara:
  tren  : ALG alligator (SMMA 13/8/5), ST supertrend(10,3), ICH (close vs awan 9/26/52 tanpa geser), SAR parabolic, MACD hist,
          HA heikin-ashi 2 warna sama, EMA (EMA200 H1), D1 (close harian vs SMA100), BTC (rezim BTC H1), CLV (close vs tengah range 24 jam)
  balik : RSIf (RSI2 <= 30 / >= 70 fade), BBf (bollinger 20/2 fade), STf (stochastic 14 < 20 / > 80 fade), SOUP (turtle soup 20 jam),
          DON (close dekat low/high donchian 20 → fade), VOLx (ATR H1 relatif 14 hari > 1,3 → +arah sinyal, sumber edge B)
Trade juara dipertahankan bila SEMUA komponen kombinasi (1-4) memberi suara SEARAH trade (suara == arah). Lingkup filter: semua trade,
hanya A, hanya B-long, hanya B-short. INI SARINGAN AWAL (filter pasca-trade, tanpa replay slot) -> kandidat wajib replay penuh.
WALK-FORWARD BERLABUH per 2 tahun: pilih <=2021 → uji 2022-23 · pilih <=2023 → uji 2024-25 · pilih <=2025 → uji 2026.
Skor pemilihan: R/trade tertinggi dengan syarat (di data pilih) tidak ada tahun minus, R total >= 80% juara, n >= 30%.
UJI PEMBANDING: porsi 'mengalahkan juara di periode uji (R/trade naik DAN R total >= 80%)' di 20/100 teratas vs semua kombinasi.
Pemakaian: python riset/intraday/eksperimen/kombinasi_2026-11-11.py <repo> <data> <trades.csv>"""
import bisect, calendar, collections, csv, itertools, json, os, sys, time
REPO, DATA, CSV = sys.argv[1:4]
sys.path.insert(0, REPO); sys.path.insert(0, os.path.join(REPO, "riset"))
import numpy as np
import backtest_intraday as bi

tr = [dict(r, t=int(r["t"]), d=int(r["d"]), R=float(r["R"])) for r in csv.DictReader(open(CSV))]
for o in tr: o["g"] = "A" if o["m"] == "A" else ("Bl" if o["d"] == 1 else "Bs"); o["y"] = time.gmtime(o["t"]).tm_year

def smma(x, n): return bi.wilder(x, n)
def ind(c):
    rows = bi.jload(f"{DATA}/klines/{c}.json")
    a = np.array([x[:5] for x in rows], float); T = a[:, 0].astype(np.int64); O, H, L, C = a[:, 1], a[:, 2], a[:, 3], a[:, 4]
    med = (H + L) / 2; J, Te, Li = smma(med, 13), smma(med, 8), smma(med, 5)
    tr_ = np.maximum(H - L, np.maximum(abs(H - np.roll(C, 1)), abs(L - np.roll(C, 1)))); tr_[0] = H[0] - L[0]; A = bi.wilder(tr_, 10)
    up, dn = med + 3 * A, med - 3 * A; st = np.ones(len(C)); fu, fd = up.copy(), dn.copy()
    for i in range(1, len(C)):
        fu[i] = up[i] if (up[i] < fu[i - 1] or C[i - 1] > fu[i - 1]) else fu[i - 1]
        fd[i] = dn[i] if (dn[i] > fd[i - 1] or C[i - 1] < fd[i - 1]) else fd[i - 1]
        st[i] = 1 if C[i] > fu[i - 1] else -1 if C[i] < fd[i - 1] else st[i - 1]
    def mid(n): return (np.array([H[max(0, i - n + 1):i + 1].max() for i in range(len(H))]) + np.array([L[max(0, i - n + 1):i + 1].min() for i in range(len(L))])) / 2
    m9, m26, m52 = mid(9), mid(26), mid(52); spa, spb = (m9 + m26) / 2, m52
    # parabolic SAR
    sar = np.zeros(len(C)); dirn = np.ones(len(C)); af, ep = 0.02, H[0]; sar[0] = L[0]
    for i in range(1, len(C)):
        s = sar[i - 1] + af * (ep - sar[i - 1]); d = dirn[i - 1]
        if d == 1:
            s = min(s, L[i - 1]);
            if L[i] < s: d, s, ep, af = -1, ep, L[i], 0.02
            elif H[i] > ep: ep, af = H[i], min(af + 0.02, 0.2)
        else:
            s = max(s, H[i - 1])
            if H[i] > s: d, s, ep, af = 1, ep, H[i], 0.02
            elif L[i] < ep: ep, af = L[i], min(af + 0.02, 0.2)
        sar[i], dirn[i] = s, d
    macd = bi.ema(C, 12) - bi.ema(C, 26); mh = macd - bi.ema(macd, 9)
    hc = (O + H + L + C) / 4; ho = np.empty_like(hc); ho[0] = O[0]
    for i in range(1, len(C)): ho[i] = (ho[i - 1] + hc[i - 1]) / 2
    had = np.sign(hc - ho)
    e200 = bi.ema(C, 200); r2 = bi.rsi(C, 2)
    s20 = np.convolve(C, np.ones(20) / 20, "full")[:len(C)]; sd20 = np.array([C[max(0, i - 19):i + 1].std() for i in range(len(C))])
    hh20 = np.array([H[max(0, i - 19):i + 1].max() for i in range(len(H))]); ll20 = np.array([L[max(0, i - 19):i + 1].min() for i in range(len(L))])
    hh14 = np.array([H[max(0, i - 13):i + 1].max() for i in range(len(H))]); ll14 = np.array([L[max(0, i - 13):i + 1].min() for i in range(len(L))])
    k14 = (C - ll14) / np.maximum(hh14 - ll14, 1e-12) * 100
    h24 = np.array([H[max(0, i - 23):i + 1].max() for i in range(len(H))]); l24 = np.array([L[max(0, i - 23):i + 1].min() for i in range(len(L))])
    A14 = bi.wilder(tr_, 14); vrel = A14 / np.array([A14[max(0, i - 336):i + 1].mean() for i in range(len(A14))])
    # D1 SMA100 dari close 00:00 UTC
    dcl = {};
    for t, c in zip(T, C):
        if (t + 3600) % 86400 == 0: dcl[(t + 3600) // 86400] = c
    dk = sorted(dcl); dv = np.array([dcl[k] for k in dk]); dsma = np.array([dv[max(0, i - 99):i + 1].mean() if i >= 99 else np.nan for i in range(len(dv))])
    return dict(T=T, C=C, H=H, L=L, J=J, Te=Te, Li=Li, st=st, spa=spa, spb=spb, sar=sar, dirn=dirn, mh=mh, had=had, e200=e200, r2=r2,
                s20=s20, sd20=sd20, hh20=hh20, ll20=ll20, k14=k14, h24=h24, l24=l24, vrel=vrel, dk=np.array(dk), dv=dv, dsma=dsma)

KOMP = ["ALG", "ST", "ICH", "SAR", "MACD", "HA", "EMA", "D1", "BTC", "CLV", "RSIf", "BBf", "STf", "SOUP", "DON", "VOLx"]
def suara(X, i, t, d, btc):
    C, H, L = X["C"], X["H"], X["L"]
    kd = bisect.bisect_right(X["dk"], t // 86400) - 1
    d1 = 0 if kd < 0 or np.isnan(X["dsma"][kd]) else (1 if X["dv"][kd] > X["dsma"][kd] else -1)
    return [1 if X["Li"][i] > X["Te"][i] > X["J"][i] else -1 if X["Li"][i] < X["Te"][i] < X["J"][i] else 0,
            int(X["st"][i]), 1 if C[i] > max(X["spa"][i], X["spb"][i]) else -1 if C[i] < min(X["spa"][i], X["spb"][i]) else 0,
            int(X["dirn"][i]), 1 if X["mh"][i] > 0 else -1, int(X["had"][i]) if X["had"][i] == X["had"][i - 1] else 0,
            1 if C[i] > X["e200"][i] else -1, d1, btc,
            1 if C[i] >= (X["h24"][i] + X["l24"][i]) / 2 else -1,
            1 if X["r2"][i] <= 30 else -1 if X["r2"][i] >= 70 else 0,
            1 if C[i] < X["s20"][i] - 2 * X["sd20"][i] else -1 if C[i] > X["s20"][i] + 2 * X["sd20"][i] else 0,
            1 if X["k14"][i] < 20 else -1 if X["k14"][i] > 80 else 0,
            1 if L[i] < X["ll20"][i - 1] and C[i] > X["ll20"][i - 1] else -1 if H[i] > X["hh20"][i - 1] and C[i] < X["hh20"][i - 1] else 0,
            1 if C[i] <= X["ll20"][i] + 0.1 * (X["hh20"][i] - X["ll20"][i]) else -1 if C[i] >= X["hh20"][i] - 0.1 * (X["hh20"][i] - X["ll20"][i]) else 0,
            d if X["vrel"][i] > 1.3 else 0]

H1b = bi.load(DATA, ["BTC"])[0] if False else None
cache = {}; btcX = ind("BTC"); bix = {int(t): k for k, t in enumerate(btcX["T"])}
BREG = None
V = np.zeros((len(tr), len(KOMP)), dtype=int)
for n, o in enumerate(tr):
    c = o["c"]
    if c not in cache:
        try: cache[c] = ind(c)
        except Exception: cache[c] = None
    X = cache[c]
    if X is None: continue
    i = bisect.bisect_right(X["T"], o["t"] - 3600) - 1           # candle H1 terakhir yang sudah close
    if i < 300: continue
    kb = bisect.bisect_right(btcX["T"], o["t"] - 3600) - 1
    bC, bE = btcX["C"][kb], btcX["e200"][kb]; e100 = None
    btc = 1 if bC > bE else -1
    V[n] = suara(X, i, o["t"], o["d"], btc)
print(f"{len(tr)} trade, {len(cache)} koin, suara terisi {np.mean(np.any(V != 0, axis=1)) * 100:.0f}%", flush=True)
Rv = np.array([o["R"] for o in tr]); D = np.array([o["d"] for o in tr]); Y = np.array([o["y"] for o in tr]); G = np.array([o["g"] for o in tr])
AG = (V == D[:, None])                                            # komponen setuju dengan arah trade
JEN = (("pilih<=2021", 2020, 2021, 2022, 2023), ("pilih<=2023", 2020, 2023, 2024, 2025), ("pilih<=2025", 2020, 2025, 2026, 2026))
LINGKUP = {"semua": np.ones(len(tr), bool), "A": G == "A", "B-long": G == "Bl", "B-short": G == "Bs"}

def nilai(keep, y0, y1):
    sel = (Y >= y0) & (Y <= y1); k = keep & sel
    yrs = [Rv[k & (Y == y)].sum() for y in range(y0, y1 + 1)]
    return dict(n=int(k.sum()), n0=int(sel.sum()), R=float(Rv[k].sum()), R0=float(Rv[sel].sum()), avg=float(Rv[k].mean()) if k.any() else 0.0,
                avg0=float(Rv[sel].mean()), minus=sum(v <= 0 for v in yrs), tahun=[round(v, 1) for v in yrs])

semua = []
for lk, mask in LINGKUP.items():
    for k in (1, 2, 3, 4):
        for kom in itertools.combinations(range(len(KOMP)), k):
            ok = np.all(AG[:, kom], axis=1)
            keep = ~mask | ok                                       # filter hanya di lingkup
            semua.append((lk, "+".join(KOMP[c] for c in kom), keep))
print(f"kombinasi dinilai: {len(semua)}", flush=True)
ringkas = {}
uji_all = collections.defaultdict(list)
for jn, a0, a1, b0, b1 in JEN:
    sc = []
    for lk, nm, keep in semua:
        p = nilai(keep, a0, a1)
        if p["minus"] == 0 and p["R"] >= 0.8 * p["R0"] and p["n"] >= 0.3 * p["n0"]:
            sc.append((p["avg"], lk, nm, keep, p))
    sc.sort(key=lambda z: -z[0])
    lol = lambda keep: (lambda u: u["avg"] > u["avg0"] and u["R"] >= 0.8 * u["R0"])(nilai(keep, b0, b1))
    base = np.mean([lol(z[3]) for z in sc]) if sc else 0
    print(f"\n### {jn} → uji {b0}-{b1}: lolos syarat pilih {len(sc)} · porsi menang di uji: 20 teratas "
          f"{np.mean([lol(z[3]) for z in sc[:20]]) * 100:.0f}% · 100 teratas {np.mean([lol(z[3]) for z in sc[:100]]) * 100:.0f}% · semua {base * 100:.0f}%")
    for z in sc[:8]:
        u = nilai(z[3], b0, b1); p = z[4]
        print(f"  {z[1]:<8} {z[2]:<22} pilih R/tr {p['avg']:+.3f} (juara {p['avg0']:+.3f}) n {p['n']}/{p['n0']} · UJI R/tr {u['avg']:+.3f} vs {u['avg0']:+.3f}, "
              f"R {u['R']:+.1f} vs {u['R0']:+.1f}, n {u['n']}/{u['n0']}")
    if sc:
        best = sc[0]; ringkas[jn] = (best[1], best[2]); uji_all["terpilih"].append(nilai(best[3], b0, b1))
# gabungan walk-forward: tahun 2022-2026 semuanya hasil uji dari aturan yang dipilih sebelumnya
print("\n### Gabungan walk-forward (aturan terpilih tiap jendela; tahun 2022-2026 semua hasil uji)")
tot = dict(n=0, n0=0, R=0.0, R0=0.0); per = []
for (jn, a0, a1, b0, b1), u in zip(JEN, uji_all["terpilih"]):
    tot = {k: tot[k] + u[k] for k in tot}; per += list(zip(range(b0, b1 + 1), u["tahun"]))
    print(f"  {jn}: {ringkas[jn]} → uji {b0}-{b1} R {u['R']:+.1f} vs juara {u['R0']:+.1f} · R/tr {u['avg']:+.3f} vs {u['avg0']:+.3f} · per tahun {u['tahun']}")
print(f"  total 2022-2026: R {tot['R']:+.1f} vs {tot['R0']:+.1f} · R/tr {tot['R'] / max(tot['n'], 1):+.3f} vs {tot['R0'] / tot['n0']:+.3f} · n {tot['n']}/{tot['n0']}")
# komponen tunggal (pustaka) di seluruh data: R/trade saat setuju vs tidak
print("\n### Pustaka: tiap komponen, R/trade saat SETUJU vs TIDAK (semua trade; per lingkup)")
for lk, mask in LINGKUP.items():
    row = []
    for c, nm in enumerate(KOMP):
        a = mask & AG[:, c]; b = mask & ~AG[:, c]
        if a.sum() >= 30 and b.sum() >= 30:
            yr_ok = sum(Rv[a & (Y == y)].mean() > Rv[b & (Y == y)].mean() for y in range(2020, 2027) if (a & (Y == y)).sum() >= 5 and (b & (Y == y)).sum() >= 5)
            row.append(f"{nm} {Rv[a].mean():+.3f}/{Rv[b].mean():+.3f} ({a.sum()}, {yr_ok}/7)")
    print(f"  {lk}: " + " · ".join(row))
