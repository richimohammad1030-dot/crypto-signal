"""Riset mingguan intraday 20 Nov 2026 · ARAH: naikkan EDGE PER TRADE. Replay penuh, daftar koin SESUAI MASANYA (uji utama),
WALK-FORWARD berlabuh 2 tahun (pilih <=2021 -> uji 2022-23 · pilih <=2023 -> uji 2024-25 · pilih <=2025 -> uji 2026).

I-30  Skill SNR tahap 2 (BISA MEMAKAI): level PERIODE (high & low hari sebelumnya 00-00 UTC = 07-07 WIB, high & low minggu
      ISO sebelumnya; dihitung dari H1 koin itu, hanya data yang sudah lengkap saat order dikirim) lebih sering DITEMBUS dan
      tembusannya lebih sering LANJUT +1 ATR (tahap 1 & 1b). Order limit juara MELAWAN gerak (A beli dip, B limit 1 ATR berlawanan
      gerak pagi) → order yang hanya terisi setelah harga menembus level PERIODE diduga lebih sering kena SL. Filter (order
      dilewati, tidak memblok koin):
        lewat   : ada level di antara harga acuan (A: close sinyal 15m · B: open 07:00) dan harga limit (isi = harus tembus level)
        antara  : ada level di antara harga limit dan SL (setelah isi, SL = harus tembus level; "SL di balik level" gagal)
        dekat w : ada level dalam ±w ATR dari harga limit (w 0,25 / 0,5 / 1,0; ATR = ATR order: A 15m, B H1)
      masing-masing untuk modul A, B, atau A+B. 15 varian + off.
I-34  [lit] Efek hari dalam seminggu / akhir pekan: likuiditas & volume akhir pekan lebih tipis → gerak pagi akhir pekan lebih
      sering berlanjut/acak. Varian: lewati B Sabtu / Minggu / Sab+Min / Senin (hari order 07:00 WIB), A Sab+Min, A+B Sab+Min.
      Sumber: Caporale & Plastun (2019) "The day of the week effect in the cryptocurrency market", Finance Research Letters 31,
      258-269 · Aharon & Qadan (2019) "Bitcoin and the day-of-the-week effect", Finance Research Letters 31, 415-424.
Pemilihan per jendela: skor = jumlah tahun minus di data pilih (sedikit) lalu R/thn (besar). Tetangga dilaporkan.
Pemakaian: python riset/intraday/eksperimen/wf_snr_akhirpekan_2026-11-20.py <repo> <data> <out_dir>"""
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

# Level PERIODE per koin dari H1: hari UTC sebelumnya & minggu ISO sebelumnya (Senin 00 UTC)
LV = {}
for c, G in H1.items():
    T = G["T"]; d = T // 86400; w = (d + 3) // 7
    dh, dl, wh, wl = {}, {}, {}, {}
    for key, hi, lo in ((d, dh, dl), (w, wh, wl)):
        u, inv = np.unique(key, return_inverse=True)
        mx = np.full(len(u), -np.inf); mn = np.full(len(u), np.inf)
        np.maximum.at(mx, inv, G["H"]); np.minimum.at(mn, inv, G["L"])
        cnt = np.bincount(inv)
        for k, kk in enumerate(u):
            if cnt[k] >= (20 if key is d else 140): hi[int(kk)], lo[int(kk)] = float(mx[k]), float(mn[k])
    LV[c] = (dh, dl, wh, wl)
def levels(c, t):
    dh, dl, wh, wl = LV[c]; d = t // 86400; w = (d + 3) // 7
    return [x for x in (dh.get(d - 1), dl.get(d - 1), wh.get(w - 1), wl.get(w - 1)) if x is not None]
def antara(lv, a, b):
    lo, hi = min(a, b), max(a, b)
    return any(lo < x < hi for x in lv)

# ------------------------------------------------------------------ generator (salinan bi.orders + filter keep)
def gen_A(P, keep):
    out = []
    for c, D in M15.items():
        T, C, A, R2, R14, reg = D["T"], D["C"], D["A"], D["R2"], D["R14"], D["reg"]; nxt = 0
        for i in np.flatnonzero((reg == 1) & ((R2 < 5) | (R14 < 30)) & (A / C >= P["A_VMIN"])):
            if i < max(nxt, 900) or i + 1 >= len(T) or T[i] < P["START"]: continue
            t1 = int(T[i + 1])
            if rank_fn(c, t1) >= P["A_RANK_MAX"] or (P["A_BTC"] and BTC(t1) != 1): continue
            lim, r0 = C[i] - P["A_OFF"] * A[i], P["A_SL"] * A[i]
            if not keep(c, t1, 1, float(C[i]), float(lim), float(lim - r0), float(A[i])): continue
            r, nxt = bi.sim(D, i + 1, 1, lim, r0, lim + P["A_TP_R"] * r0, P["A_VALID_MIN"] // 15, P["A_HOLD_JAM"] * 4, None, P)
            out.append(dict(r, t=t1, c=c, m="A", d=1, vr=0.0))
    return out

def gen_B(P, keep):
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
            o = D["O"][i]; lim = o - tr * P["B_K"] * a
            if not keep(c, int(T[i]), tr, float(o), float(lim), float(lim - tr * P["B_SL"] * a), float(a)): continue
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

# ------------------------------------------------------------------ varian: (keep_A, keep_B); None = tanpa filter
ALLOW = lambda *a: True
def snr(kind, w=0.0):
    def f(c, t, d, ref, lim, sl, atr):
        lv = levels(c, t)
        if kind == "lewat": return not antara(lv, ref, lim)
        if kind == "antara": return not antara(lv, lim, sl)
        return not any(abs(x - lim) <= w * atr for x in lv)
    return f
def hari(skip):                      # tm_wday: 0 Senin .. 5 Sabtu, 6 Minggu (hari UTC; order B 00 UTC = 07 WIB hari yang sama)
    return lambda c, t, *a: time.gmtime(t + 7 * 3600).tm_wday not in skip
VAR = {"I-30": {"off": (None, None)}, "I-34": {"off": (None, None)}}
for nm, f in (("lewat", snr("lewat")), ("antara", snr("antara")), ("dekat0.25", snr("dekat", 0.25)),
              ("dekat0.5", snr("dekat", 0.5)), ("dekat1.0", snr("dekat", 1.0))):
    VAR["I-30"][f"{nm}-A"] = (f, None); VAR["I-30"][f"{nm}-B"] = (None, f); VAR["I-30"][f"{nm}-AB"] = (f, f)
VAR["I-34"].update({"B-tanpaSab": (None, hari({5})), "B-tanpaMin": (None, hari({6})), "B-tanpaSabMin": (None, hari({5, 6})),
                    "B-tanpaSen": (None, hari({0})), "A-tanpaSabMin": (hari({5, 6}), None), "AB-tanpaSabMin": (hari({5, 6}), hari({5, 6}))})

A0 = gen_A(P0, ALLOW); B0 = gen_B(P0, ALLOW); print(f"order A {len(A0)} · B {len(B0)}", flush=True)
RES = {}
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
    for nm, (ka, kb) in vs.items():
        if nm == "off" and BASE is not None: RES[(ide, nm)] = BASE; continue
        a = A0 if ka is None else gen_A(P0, ka); b = B0 if kb is None else gen_B(P0, kb)
        s, t = portfolio(a + b, P0)
        RES[(ide, nm)] = (s, t)
        if nm == "off": BASE = (s, t)
        S = bi.stats(t, s)
        print(f"{ide} {nm:<15} order A {len(a)} B {len(b)} n={S['n']} R/tr {S['avgR']:+.4f} R {S['totR']:+.1f} DD {S['maxDD']} "
              f"tahun {per_tahun(t)} grup {grp(t)}", flush=True)

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
        print(f"  {jn}: skor " + " · ".join(f"{nm} ({-s[0]} minus, {s[1]:+.1f}R/thn)" for s, nm in sk[:8]) + f" -> PILIH {pilih}")
        tc, tj = seg(RES[(ide, pilih)][1], b0, b1), seg(BASE[1], b0, b1)
        uji_c += tc; uji_j += tj
        for y in range(b0, b1 + 1):
            yc = [o["R"] for o in tc if time.gmtime(o["t"]).tm_year == y]; yj = [o["R"] for o in tj if time.gmtime(o["t"]).tm_year == y]
            rows.append((y, pilih, len(yc), sum(yc), len(yj), sum(yj)))
    print("  tahun  aturan           n     R      R/tr   | juara n     R      R/tr")
    for y, pl, nc, rc, nj, rj in rows:
        print(f"  {y}  {pl:<15} {nc:4d} {rc:+6.1f} {rc / max(nc, 1):+.3f} | {nj:4d} {rj:+6.1f} {rj / max(nj, 1):+.3f}")
    sc, sj = bi.stats(sorted(uji_c, key=lambda o: o["t_exit"])), bi.stats(sorted(uji_j, key=lambda o: o["t_exit"]))
    sig = sg.banding([(o["t_exit"], o["R"]) for o in uji_j], [(o["t_exit"], o["R"]) for o in uji_c], ts(2022), None)
    minus_c = sum(r[3] <= 0 for r in rows); minus_j = sum(r[5] <= 0 for r in rows)
    print(f"  GABUNGAN UJI 2022-2026: penantang n {sc['n']} R {sc['totR']:+.1f} R/tr {sc['avgR']:+.4f} DD {sc['maxDD']} tanpa2% {sc['tanpa_top2']} minus {minus_c}"
          f" | juara n {sj['n']} R {sj['totR']:+.1f} R/tr {sj['avgR']:+.4f} DD {sj['maxDD']} tanpa2% {sj['tanpa_top2']} minus {minus_j}")
    print(f"  signifikansi (2022-skrg): {sig}")
    lap[ide] = dict(rows=rows, sig=sig)
    print("  pembanding kriteria lama (semua varian, seluruh periode):")
    for nm in vs:
        s, t = RES[(ide, nm)]
        L, B, S = bi.stats(t, s, b=bi.IS_END), bi.stats(t, s, a=bi.IS_END), bi.stats(t, s)
        print(f"    {nm:<15} n {S['n']} fill {S['fill']} R/tr {S['avgR']:+.4f} R/thn {S['totR_thn']} DD {S['maxDD']} rasio L {L['rasio']} B {B['rasio']} tanpa2% {S['tanpa_top2']} grup {grp(t)}")
# Informasi PASCA-HOC (bukan dasar keputusan; varian dipilih setelah melihat seluruh data): tiap varian TETAP vs juara di 2022-skrg
print("\n######## info pasca-hoc: varian tetap vs juara, 2022-skrg (P bootstrap bulan)")
for ide, vs in VAR.items():
    for nm in vs:
        if nm == "off": continue
        t = RES[(ide, nm)][1]
        g = sg.banding([(o["t_exit"], o["R"]) for o in BASE[1]], [(o["t_exit"], o["R"]) for o in t], ts(2022), None)
        print(f"  {ide} {nm:<15} R/thn {g['penantang']['R_thn']:+.1f} vs {g['juara']['R_thn']:+.1f} DD {g['penantang']['DD']} vs {g['juara']['DD']}"
              f" P_R {g['P_R_lebih_baik']} P_rasio {g['P_rasio_lebih_baik']}", flush=True)
with open(f"{OUT}/juara_pit.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["t", "t_fill", "t_exit", "c", "m", "d", "R", "why"], extrasaction="ignore"); w.writeheader(); w.writerows(BASE[1])
json.dump(lap, open(f"{OUT}/wf.json", "w"), indent=1, default=str)
