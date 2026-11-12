"""Riset mingguan intraday 13 Nov 2026 · ARAH: naikkan EDGE PER TRADE. Replay penuh, daftar koin SESUAI MASANYA (uji utama),
WALK-FORWARD berlabuh 2 tahun (pilih <=2021 -> uji 2022-23 · pilih <=2023 -> uji 2024-25 · pilih <=2025 -> uji 2026).

I-28  B-long hanya bila Alligator H1 (SMMA 13/8/5 dari median H1, candle H1 terakhir yang sudah close sebelum 07:00 WIB) searah.
      Varian: off (juara) · L-ketat (B-long hanya bila Lips > Teeth > Jaw) · L-bukanlawan (lewati B-long bila Lips < Teeth < Jaw)
              · LS-ketat / LS-bukanlawan (sama, dicerminkan juga untuk B-short).
I-33  [lit] Momentum BTC jangka pendek untuk modul B: lewati order B bila return BTC 24 jam sebelum 07:00 WIB BERLAWANAN dengan arah
      order lebih dari x (x = 0 / 1 / 2 / 3 / 5 %; off = juara). Sumber: Wen, Bouri, Xu & Zhao (2022) "Intraday return predictability
      in the cryptocurrency markets: Momentum, reversal, or both", North American J. of Economics and Finance 62, 101733 &
      Gao, Han, Li & Zhou (2018) "Market intraday momentum", J. Financial Economics 129(2). Hipotesis: order B (limit 1 ATR melawan
      gerak pagi) lebih aman bila pasar (BTC) 24 jam terakhir bergerak searah order.
Filter dipasang DI DALAM generator order (salinan bi.orders), lalu portofolio PIT diputar ulang penuh (slot & pembatalan berubah).
Pemilihan per jendela: skor = jumlah tahun minus di data pilih (sedikit) lalu R/thn (besar); tetangga dilaporkan.
Pemakaian: python riset/intraday/eksperimen/wf_b_filter_2026-11-13.py <repo> <data> <out_dir>"""
import calendar, collections, csv, json, os, sys, time
REPO, DATA, OUT = sys.argv[1:4]
sys.path.insert(0, REPO); sys.path.insert(0, os.path.join(REPO, "riset"))
import numpy as np
import backtest_intraday as bi, pit, signal_bot as sb, signifikansi as sg

os.makedirs(OUT, exist_ok=True)
P0 = dict(bi.PARAM)
YEARS = list(range(2020, 2027))
ts = lambda y: calendar.timegm((y, 1, 1, 0, 0, 0))

# ------------------------------------------------------------------ data (sekali)
pit._load(DATA)
ALL = sorted({c for m in pit._SNAP for c in pit.ranked(DATA, m)[:70]} | set(sb.COINS))
H1, M15 = bi.load(DATA, ALL)
first = {c: int(D["T"][900]) for c, D in M15.items() if len(D["T"]) > 900}
uni = pit.universe_fn(DATA, lambda c, t: c in first and c in H1 and first[c] <= t)
BTC = bi.btc_regime_fn(H1)
rank_fn = lambda c, t: uni(t).index(c) if c in uni(t) else 999
print(f"koin dimuat {len(M15)}", flush=True)

# Alligator H1 per koin: 1 = Lips > Teeth > Jaw, -1 = kebalikannya, 0 = kusut
for c, G in H1.items():
    med = (G["H"] + G["L"]) / 2
    J, Te, Li = bi.wilder(med, 13), bi.wilder(med, 8), bi.wilder(med, 5)
    G["alg"] = np.where((Li > Te) & (Te > J), 1, np.where((Li < Te) & (Te < J), -1, 0))
BG = H1["BTC"]; BIX = {int(t): k for k, t in enumerate(BG["T"])}
def btc_ret24(t_close_k):
    k = BIX.get(t_close_k)
    if k is None or k < 24: return 0.0
    return float(BG["C"][k] / BG["C"][k - 24] - 1)

# ------------------------------------------------------------------ generator
def gen_A(P):
    out = []
    for c, D in M15.items():
        T, C, A, R2, R14, reg = D["T"], D["C"], D["A"], D["R2"], D["R14"], D["reg"]; nxt = 0
        for i in np.flatnonzero((reg == 1) & ((R2 < 5) | (R14 < 30)) & (A / C >= P["A_VMIN"])):
            if i < max(nxt, 900) or i + 1 >= len(T) or T[i] < P["START"]: continue
            t1 = int(T[i + 1])
            if rank_fn(c, t1) >= P["A_RANK_MAX"] or (P["A_BTC"] and BTC(t1) != 1): continue
            lim, r0 = C[i] - P["A_OFF"] * A[i], P["A_SL"] * A[i]
            r, nxt = bi.sim(D, i + 1, 1, lim, r0, lim + P["A_TP_R"] * r0, P["A_VALID_MIN"] // 15, P["A_HOLD_JAM"] * 4, None, P)
            out.append(dict(r, t=t1, c=c, m="A", d=1, vr=0.0))
    return out

def gen_B(P, keep):
    """keep(c, G, k, tr) -> bool : filter tambahan SEBELUM order dikirim (order yang dilewati tidak memblok koin)."""
    out = []
    for c, D in M15.items():
        T = D["T"]; G = H1[c]; GA = G["A"]; nxt = 0
        for i in np.flatnonzero(T % 86400 == 0):
            if i < max(nxt, 900) or T[i] < P["START"]: continue
            k = D["h1"].get(int(T[i]) - 3600)
            if k is None or k < 400: continue
            a = GA[k]; vr = a / GA[k - 336:k].mean(); tr = int(G["reg"][k])
            if vr < P["B_VR"] or a / G["C"][k] < P["B_ATRP"] or tr == 0: continue
            if P["B_BTC"] and int(G["btc"][k]) != tr: continue
            if tr == -1 and (not P["B_SHORT"] or (bi.funding_avg72(G, int(G["T"][k])) or 0) <= 0): continue
            if not keep(c, G, k, tr): continue
            o = D["O"][i]; lim = o - tr * P["B_K"] * a
            r, nxt = bi.sim(D, i, tr, lim, P["B_SL"] * a, lim + tr * P["B_TPF"] * P["B_K"] * a, P["B_VALID_JAM"] * 4, P["B_HOLD_JAM"] * 4, None, P)
            out.append(dict(r, t=int(T[i]), c=c, m="B", d=tr, vr=float(vr)))
    return out

def portfolio(ords, P):
    rank_of = lambda o: uni(o["t"]).index(o["c"])
    ords = [o for o in ords if o["c"] in uni(o["t"])]
    ev = sorted(ords, key=lambda o: (o["t"], rank_of(o)))
    pend, pos, sent, taken = [], [], [], []
    def settle(now):
        nonlocal pend, pos
        while True:
            cand = [(o["t_fill"], rank_of(o), k) for k, (_, o) in enumerate(pend) if o["filled"] and o["t_fill"] < now]
            if not cand: break
            tf, _, k = min(cand); o = pend[k][1]
            pos = [(e, c) for e, c in pos if e > tf]
            pend = [p for p in pend if p[1] is not o and p[0] > tf]
            if len(pos) < P["CAP"]:
                pos.append((o["t_exit"], o["c"])); taken.append(o)
                if len(pos) >= P["CAP"]: pend = []
        pend = [p for p in pend if p[0] > now]; pos = [(e, c) for e, c in pos if e > now]
    for o in ev:
        settle(o["t"])
        if o["c"] in {c for _, c in pos} | {x["c"] for _, x in pend} or len(pend) >= P["PEND"] or len(pos) >= P["CAP"]: continue
        sent.append(o); pend.append(((o["t_fill"] + 1) if o["filled"] else o["t_exp"], o))
    settle(2_000_000_000)
    return sent, sorted(taken, key=lambda o: o["t_exit"])

# ------------------------------------------------------------------ varian
def alg_keep(mode, both):
    def f(c, G, k, tr):
        if tr == -1 and not both: return True
        s = int(G["alg"][k])
        return (s == tr) if mode == "ketat" else (s != -tr)
    return f
def mom_keep(x):
    return lambda c, G, k, tr: tr * btc_ret24(int(G["T"][k])) >= -x
VAR = {"I-28": {"off": None, "L-ketat": alg_keep("ketat", False), "L-bukanlawan": alg_keep("bukan", False),
                "LS-ketat": alg_keep("ketat", True), "LS-bukanlawan": alg_keep("bukan", True)},
       "I-33": {"off": None, "x=0%": mom_keep(0.0), "x=1%": mom_keep(0.01), "x=2%": mom_keep(0.02), "x=3%": mom_keep(0.03), "x=5%": mom_keep(0.05)}}

A_ORD = gen_A(P0); print(f"order A: {len(A_ORD)}", flush=True)
RES = {}
def jalan(nm, keep):
    b = gen_B(P0, keep or (lambda *a: True))
    s, t = portfolio(A_ORD + b, P0)
    return s, t

def per_tahun(t):
    yr = collections.defaultdict(float)
    for o in t: yr[time.gmtime(o["t"]).tm_year] += o["R"]
    return {y: round(yr.get(y, 0.0), 1) for y in YEARS}
def grp(t):
    g = collections.defaultdict(list)
    for o in t: g["A" if o["m"] == "A" else ("B-long" if o["d"] == 1 else "B-short")].append(o["R"])
    return {k: (len(v), round(sum(v), 1), round(float(np.mean(v)), 3)) for k, v in sorted(g.items())}

BASE = None
for ide, vs in VAR.items():
    for nm, keep in vs.items():
        if nm == "off" and BASE is not None: RES[(ide, nm)] = BASE; continue
        s, t = jalan(nm, keep)
        RES[(ide, nm)] = (s, t)
        if nm == "off": BASE = (s, t)
        S = bi.stats(t, s)
        print(f"{ide} {nm:<14} n={S['n']} R/tr {S['avgR']:+.4f} R {S['totR']:+.1f} DD {S['maxDD']} tahun {per_tahun(t)} grup {grp(t)}", flush=True)

# ------------------------------------------------------------------ walk-forward
JEN = (("pilih<=2021", 2020, 2021, 2022, 2023), ("pilih<=2023", 2020, 2023, 2024, 2025), ("pilih<=2025", 2020, 2025, 2026, 2026))
def seg(t, y0, y1): return [o for o in t if y0 <= time.gmtime(o["t"]).tm_year <= y1]
def skor(t, y0, y1):
    pt = per_tahun(t); yrs = [pt[y] for y in range(y0, y1 + 1)]
    return (-sum(v <= 0 for v in yrs), sum(yrs) / len(yrs))
lap = {}
for ide, vs in VAR.items():
    print(f"\n######## {ide} walk-forward", flush=True)
    uji_c, uji_j = [], []; rows = []
    for jn, a0, a1, b0, b1 in JEN:
        sk = sorted(((skor(RES[(ide, nm)][1], a0, a1), nm) for nm in vs), reverse=True)
        pilih = sk[0][1]
        print(f"  {jn}: skor " + " · ".join(f"{nm} ({-s[0]} minus, {s[1]:+.1f}R/thn)" for s, nm in sk) + f" -> PILIH {pilih}")
        tc, tj = seg(RES[(ide, pilih)][1], b0, b1), seg(BASE[1], b0, b1)
        uji_c += tc; uji_j += tj
        for y in range(b0, b1 + 1):
            rc = sum(o["R"] for o in tc if time.gmtime(o["t"]).tm_year == y); rj = sum(o["R"] for o in tj if time.gmtime(o["t"]).tm_year == y)
            nc = sum(1 for o in tc if time.gmtime(o["t"]).tm_year == y); nj = sum(1 for o in tj if time.gmtime(o["t"]).tm_year == y)
            rows.append((y, pilih, nc, rc, nj, rj))
    print("  tahun  aturan          n     R      R/tr   | juara n     R      R/tr")
    for y, pl, nc, rc, nj, rj in rows:
        print(f"  {y}  {pl:<14} {nc:4d} {rc:+6.1f} {rc / max(nc, 1):+.3f} | {nj:4d} {rc * 0 + rj:+6.1f} {rj / max(nj, 1):+.3f}")
    sc, sj = bi.stats(uji_c), bi.stats(uji_j)
    sig = sg.banding([(o["t_exit"], o["R"]) for o in uji_j], [(o["t_exit"], o["R"]) for o in uji_c], ts(2022), None)
    minus_c = sum(r[3] <= 0 for r in rows); minus_j = sum(r[5] <= 0 for r in rows)
    print(f"  GABUNGAN UJI 2022-2026: penantang n {sc['n']} R {sc['totR']:+.1f} R/tr {sc['avgR']:+.4f} DD {sc['maxDD']} tanpa2% {sc['tanpa_top2']} minus {minus_c}"
          f" | juara n {sj['n']} R {sj['totR']:+.1f} R/tr {sj['avgR']:+.4f} DD {sj['maxDD']} tanpa2% {sj['tanpa_top2']} minus {minus_j}")
    print(f"  signifikansi (2022-skrg): {sig}")
    lap[ide] = dict(rows=rows, pen=sc, jua=sj, sig=sig)
    # kriteria lama (pembanding): seluruh varian, rasio 2020-23 / 2024-skrg
    print("  pembanding kriteria lama (semua varian, seluruh periode):")
    for nm in vs:
        s, t = RES[(ide, nm)]
        L, B, S = bi.stats(t, s, b=bi.IS_END), bi.stats(t, s, a=bi.IS_END), bi.stats(t, s)
        print(f"    {nm:<14} n {S['n']} fill {S['fill']} R/tr {S['avgR']:+.4f} R/thn {S['totR_thn']} DD {S['maxDD']} rasio L {L['rasio']} B {B['rasio']} tanpa2% {S['tanpa_top2']}")
    best = max((nm for nm in vs if nm != "off"), key=lambda nm: skor(RES[(ide, nm)][1], 2020, 2023))
    with open(f"{OUT}/{ide}_{best}.csv".replace("%", "p").replace("=", ""), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["t", "t_fill", "t_exit", "c", "m", "d", "R", "why"], extrasaction="ignore"); w.writeheader(); w.writerows(RES[(ide, best)][1])
with open(f"{OUT}/juara_pit.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["t", "t_fill", "t_exit", "c", "m", "d", "R", "why"], extrasaction="ignore"); w.writeheader(); w.writerows(BASE[1])
json.dump({k: dict(rows=v["rows"], sig=v["sig"]) for k, v in lap.items()}, open(f"{OUT}/wf.json", "w"), indent=1, default=str)
