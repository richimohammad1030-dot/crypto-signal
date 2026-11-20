"""Sesi riset intraday 21 Nov 2026 (PERCEPATAN, ATURAN_BERSAMA E): SATU skrip = saringan cepat 10 varian di periode pilih
(<= 2021) + walk-forward penuh (replay penuh, daftar koin SESUAI MASANYA) untuk keluarga varian 2-3 teratas.

SKILL SNR tahap 2 putaran 2 (KURIKULUM program kilat): level SWING-D1 (pivot fraktal n=3 di D1 UTC dari H1 koin itu; aktif setelah
3 candle kanan close; berlaku 30 hari) — tahap 1: lebih sering DITEMBUS dari acak.
  1 SW-dekat0.25-B : lewati order B bila level SWING-D1 dalam ±0,25 ATR H1 dari harga limit
  2 SW-dekat0.5-B  : idem ±0,5 ATR
  3 SW-lewat-B     : lewati order B bila ada level SWING-D1 di antara open 07:00 dan harga limit (isi = harus tembus level)
SUMBER EDGE BARU (bukan tambalan; momentum/tembus, beda dengan juara yang beli dip/limit melawan gerak): modul T "TEMBUS"
mandiri dari skill SNR tahap 1b (tembusan level PERIODE lebih sering lanjut +1 ATR dari acak). Tiap 00 UTC (07 WIB), koin
peringkat 1-25 (sesuai masanya): order stop OCO beli di level atas + 0,1 ATR H1 / jual di level bawah - 0,1 ATR (hanya bila open
masih di dalam level; arah yang berlawanan dengan tren BTC H1 tidak dipasang), berlaku 24 jam, SL 1 ATR H1 dari harga isi,
TP f × ATR (limit maker), hold maks 12 jam. Entry taker. Dua sisi tersentuh di candle yang sama = dianggap rugi (konservatif).
Slot sendiri (CAP 3, PEND 3) → dinilai sebagai juara + modul T (R dijumlah; risiko 1% per trade, sama dengan juara).
  4 T-hari-1.0     : level = high/low hari UTC sebelumnya, TP 1,0 ATR
  5 T-hari-1.5     : idem TP 1,5 ATR
  6 T-minggu-1.0   : level = high/low minggu ISO sebelumnya (hanya bila belum tertembus minggu ini), TP 1,0 ATR
  7 T-minggu-1.5   : idem TP 1,5 ATR
  8 T-swing-1.0    : level = SWING-D1 aktif terdekat di atas & di bawah open, TP 1,0 ATR
IDE ANTRI (ide.md):
  9 I-04 rem harian: berhenti kirim order baru setelah 2 SL di hari UTC yang sama
 10 I-06 B-short tanpa syarat funding > 0
Saringan: periode pilih Mar 2020 - Des 2021 saja; skor = (tahun minus, rasio R/thn ÷ DD) sistem lengkap. 2-3 teratas
(minimal 1 sumber edge baru) → walk-forward berlabuh 2 tahun per keluarga + signifikansi (P_rasio ≥ 0,90 = lulus;
0,50-0,70 arah konsisten = kandidat). Data konfirmasi 2018-2019 hanya bila lulus walk-forward.
Pemakaian: python riset/intraday/eksperimen/saringan_2026-11-21.py <repo> <data> <out_dir>"""
import calendar, collections, json, os, sys, time
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

# Level PERIODE (hari UTC & minggu ISO sebelumnya) dan SWING-D1 (fraktal n=3, aktif 30 hari) per koin, dari H1
LV, SW = {}, {}
for c, G in H1.items():
    T = G["T"]; d = T // 86400; w = (d + 3) // 7; tab = []
    for key, need in ((d, 20), (w, 140)):
        hi, lo = {}, {}
        u, inv = np.unique(key, return_inverse=True); cnt = np.bincount(inv)
        mx = np.full(len(u), -np.inf); mn = np.full(len(u), np.inf); np.maximum.at(mx, inv, G["H"]); np.minimum.at(mn, inv, G["L"])
        for k, kk in enumerate(u):
            if cnt[k] >= need: hi[int(kk)], lo[int(kk)] = float(mx[k]), float(mn[k])
        tab += [hi, lo]
    LV[c] = tab
    u, inv = np.unique(d, return_inverse=True); cnt = np.bincount(inv)
    mx = np.full(len(u), -np.inf); mn = np.full(len(u), np.inf); np.maximum.at(mx, inv, G["H"]); np.minimum.at(mn, inv, G["L"])
    ok = cnt >= 20; u, mx, mn = u[ok], mx[ok], mn[ok]; n = 3; px, on = [], []
    for i in range(n, len(u) - n):
        t_on = int(u[i + n]) * 86400 + 86400
        if mx[i] == mx[i - n:i + n + 1].max(): px.append(mx[i]); on.append(t_on)
        if mn[i] == mn[i - n:i + n + 1].min(): px.append(mn[i]); on.append(t_on)
    SW[c] = (np.array(px, float), np.array(on, np.int64))
def periode(c, t, jenis="semua"):
    dh, dl, wh, wl = LV[c]; d = t // 86400; w = (d + 3) // 7
    if jenis == "hari": return dh.get(d - 1), dl.get(d - 1)
    if jenis == "minggu": return wh.get(w - 1), wl.get(w - 1)
    return [x for x in (dh.get(d - 1), dl.get(d - 1), wh.get(w - 1), wl.get(w - 1)) if x is not None]
def swing(c, t):
    px, on = SW[c]; m = (on <= t) & (on + 30 * 86400 > t); return px[m]
def antara(lv, a, b):
    lo, hi = min(a, b), max(a, b); return any(lo < x < hi for x in lv)

# ------------------------------------------------------------------ generator juara (salinan bi.orders + filter keep)
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

def gen_B(P, keep, nofund=False):
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
            if tr == -1 and (not P["B_SHORT"] or (not nofund and (bi.funding_avg72(G, int(G["T"][k])) or 0) <= 0)): continue
            o = D["O"][i]; lim = o - tr * P["B_K"] * a
            if not keep(c, int(T[i]), tr, float(o), float(lim), float(lim - tr * P["B_SL"] * a), float(a)): continue
            r, nxt = bi.sim(D, i, tr, lim, P["B_SL"] * a, lim + tr * P["B_TPF"] * P["B_K"] * a, P["B_VALID_JAM"] * 4, P["B_HOLD_JAM"] * 4, None, P)
            out.append(dict(r, t=int(T[i]), c=c, m="B", d=tr, vr=float(vr)))
    return out

# ------------------------------------------------------------------ modul T (TEMBUS) — sumber edge baru
def sim_oco(D, i0, up, dn, r0, tpf, a, valid_bars, hold_bars, P):
    T, O, H, L, C = D["T"], D["O"], D["H"], D["L"], D["C"]; n = len(T); t_exp = int(T[i0]) + valid_bars * 900
    for j in range(i0, min(i0 + valid_bars, n)):
        hu = up is not None and H[j] >= up; hd = dn is not None and L[j] <= dn
        if hu and hd:                                    # dua sisi tersentuh di candle yang sama: rugi penuh (konservatif)
            fill = up; px = up - r0; d = 1; j0 = j; why = "SL2"
            pnl = -r0 - 2 * P["TAKER"] / 100 * fill
            return dict(filled=True, t_exp=t_exp, t_fill=int(T[j]), t_exit=int(T[j]) + 900, R=float(pnl / r0), why=why, entry=fill, exit=px, d=d), j + 1
        if hu or hd:
            d = 1 if hu else -1; lvl = up if hu else dn; fill = max(lvl, O[j]) if d == 1 else min(lvl, O[j]); j0 = j; break
    else:
        return dict(filled=False, t_exp=t_exp, d=1), min(i0 + valid_bars, n)
    sl, tp = fill - d * r0, fill + d * tpf * a
    for j in range(j0, min(j0 + hold_bars, n)):
        if (d == 1 and L[j] <= sl) or (d == -1 and H[j] >= sl):
            px = sl if j == j0 else (min(sl, O[j]) if d == 1 else max(sl, O[j])); cx, why = P["TAKER"], "SL"; break
        if (d == 1 and H[j] >= tp) or (d == -1 and L[j] <= tp):
            if j == j0 and d * (C[j] - tp) < 0: continue
            px, cx, why = tp, P["MAKER"], "TP"; break
    else:
        j = min(j0 + hold_bars, n) - 1; px, cx, why = C[j], P["TAKER"], "WAKTU"
    pnl = d * (px - fill) - (P["TAKER"] + cx) / 100 * fill - bi.funding_cost(D, int(T[j0]), int(T[j]), d) * fill
    return dict(filled=True, t_exp=t_exp, t_fill=int(T[j0]), t_exit=int(T[j]) + 900, R=float(pnl / r0), why=why,
                entry=float(fill), exit=float(px), d=d), j + 1

def gen_T(P, jenis, tpf, sl=1.0, rank_max=25, valid_jam=24, hold_jam=12):
    out = []
    for c, D in M15.items():
        T = D["T"]; G = H1[c]; GA = G["A"]; nxt = 0
        for i in np.flatnonzero(T % 86400 == 0):
            if i < max(nxt, 900) or T[i] < P["START"]: continue
            t = int(T[i]); k = D["h1"].get(t - 3600)
            if k is None or k < 400 or rank_fn(c, t) >= rank_max: continue
            a = float(GA[k]); o = float(D["O"][i]); b = BTC(t)
            if jenis == "swing":
                lv = swing(c, t); ab = lv[lv > o]; be = lv[lv < o]
                hi = float(ab.min()) if len(ab) else None; lo = float(be.max()) if len(be) else None
            else:
                hi, lo = periode(c, t, jenis)
                if jenis == "minggu" and hi is not None:          # belum tertembus minggu ini
                    ws = ((t // 86400 + 3) // 7 * 7 - 3) * 86400; a0 = np.searchsorted(G["T"], ws); a1 = k + 1
                    if a1 > a0:
                        if G["H"][a0:a1].max() >= hi: hi = None
                        if lo is not None and G["L"][a0:a1].min() <= lo: lo = None
            up = hi + 0.1 * a if (hi is not None and o < hi and b != -1) else None
            dn = lo - 0.1 * a if (lo is not None and o > lo and b != 1) else None
            if up is None and dn is None: continue
            r, nxt = sim_oco(D, i, up, dn, sl * a, tpf, a, valid_jam * 4, hold_jam * 4, P)
            d = r.pop("d"); out.append(dict(r, t=t, c=c, m="T", d=d, vr=0.0))
    return out

def portfolio(ords, P, rem=0):
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
        if rem and sum(1 for x in taken[-12:] if x["why"] == "SL" and x["t_exit"] <= o["t"] and x["t_exit"] // 86400 == o["t"] // 86400) >= rem:
            continue
        sent.append(o); pend.append(((o["t_fill"] + 1) if o["filled"] else o["t_exp"], o))
    settle(2_000_000_000)
    return sent, sorted(taken, key=lambda o: o["t_exit"])

# ------------------------------------------------------------------ varian
ALLOW = lambda *a: True
def snr_sw(kind, w=0.0):
    def f(c, t, d, ref, lim, sl, atr):
        lv = swing(c, t)
        if kind == "lewat": return not antara(lv, ref, lim)
        return not np.any(np.abs(lv - lim) <= w * atr)
    return f
def per_tahun(t):
    yr = collections.defaultdict(float)
    for o in t: yr[time.gmtime(o["t"]).tm_year] += o["R"]
    return {y: round(yr.get(y, 0.0), 1) for y in YEARS}
def grp(t):
    g = collections.defaultdict(list)
    for o in t: g["A" if o["m"] == "A" else ("T" if o["m"] == "T" else ("B-long" if o["d"] == 1 else "B-short"))].append(o["R"])
    return {k: (len(v), round(sum(v), 1), round(float(np.mean(v)), 3)) for k, v in sorted(g.items())}

A0 = gen_A(P0, ALLOW); B0 = gen_B(P0, ALLOW); print(f"order A {len(A0)} · B {len(B0)}", flush=True)
BASE = portfolio(A0 + B0, P0)
RES = {"off": BASE}; MOD = {}
FAM = {"SNR-SWING": ["SW-dekat0.25-B", "SW-dekat0.5-B", "SW-lewat-B"],
       "TEMBUS": ["T-hari-1.0", "T-hari-1.5", "T-minggu-1.0", "T-minggu-1.5", "T-swing-1.0"],
       "I-04": ["I-04-rem2"], "I-06": ["I-06-tanpafunding"]}
for nm, f in (("SW-dekat0.25-B", snr_sw("dekat", 0.25)), ("SW-dekat0.5-B", snr_sw("dekat", 0.5)), ("SW-lewat-B", snr_sw("lewat"))):
    RES[nm] = portfolio(A0 + gen_B(P0, f), P0)
for nm, (j, tpf) in {"T-hari-1.0": ("hari", 1.0), "T-hari-1.5": ("hari", 1.5), "T-minggu-1.0": ("minggu", 1.0),
                     "T-minggu-1.5": ("minggu", 1.5), "T-swing-1.0": ("swing", 1.0)}.items():
    s, t = portfolio(gen_T(P0, j, tpf), P0); MOD[nm] = (s, t)
    RES[nm] = (BASE[0] + s, sorted(BASE[1] + t, key=lambda o: o["t_exit"]))
RES["I-04-rem2"] = portfolio(A0 + B0, P0, rem=2)
RES["I-06-tanpafunding"] = portfolio(A0 + gen_B(P0, ALLOW, nofund=True), P0)

# ------------------------------------------------------------------ SARINGAN (periode pilih <= 2021)
E21 = ts(2022)
def skor(t, y0, y1):
    pt = per_tahun(t); yrs = [pt[y] for y in range(y0, y1 + 1)]
    return (-sum(v <= 0 for v in yrs), sum(yrs) / len(yrs))
print("\n######## SARINGAN Mar 2020 - Des 2021 (sistem lengkap; modul T = juara + T slot sendiri)")
sar = {}
for nm, (s, t) in RES.items():
    S = bi.stats(t, s, b=E21); mi = sum(per_tahun(t)[y] <= 0 for y in (2020, 2021))
    sar[nm] = (-mi, S["rasio"])
    extra = ""
    if nm in MOD:
        M = bi.stats(MOD[nm][1], MOD[nm][0], b=E21)
        extra = f" | modul T sendiri n {M.get('n')} fill {M.get('fill')} win {M.get('win')} R/tr {M.get('avgR')} R {M.get('totR')} DD {M.get('maxDD')} th {per_tahun([o for o in MOD[nm][1] if o['t'] < E21])}"
    print(f"  {nm:<18} n {S['n']} R/tr {S['avgR']:+.4f} R {S['totR']:+.1f} DD {S['maxDD']} rasio {S['rasio']} minus {mi} grup {grp([o for o in t if o['t'] < E21])}{extra}", flush=True)
urut = sorted((v for v in sar if v != "off"), key=lambda v: sar[v], reverse=True)
print("  urutan saringan: " + " > ".join(f"{v} ({sar[v][1]})" for v in urut) + f" · juara rasio {sar['off'][1]}")
fam_of = {v: f for f, vs in FAM.items() for v in vs}
top = []
for v in urut:
    if sar[v] <= sar["off"]: continue                       # tidak lebih baik dari juara di periode pilih = gugur
    if fam_of[v] not in top: top.append(fam_of[v])
    if len(top) == 3: break
if "TEMBUS" not in top:                                    # E.4: minimal 1 sumber edge baru ke uji penuh
    top = top[:2] + ["TEMBUS"]
print(f"  KE UJI PENUH: {top}")

# ------------------------------------------------------------------ WALK-FORWARD per keluarga (off ikut kandidat pilihan)
JEN = (("pilih<=2021", 2020, 2021, 2022, 2023), ("pilih<=2023", 2020, 2023, 2024, 2025), ("pilih<=2025", 2020, 2025, 2026, 2026))
def seg(t, y0, y1): return [o for o in t if y0 <= time.gmtime(o["t"]).tm_year <= y1]
lap = {"saringan": {v: sar[v] for v in sar}, "uji_penuh": top}
for fam in top:
    vs = ["off"] + FAM[fam]
    print(f"\n######## {fam} walk-forward", flush=True)
    uji_c, uji_j, rows = [], [], []
    for jn, a0, a1, b0, b1 in JEN:
        sk = sorted(((skor(RES[nm][1], a0, a1), bi.stats(seg(RES[nm][1], a0, a1))["rasio"], nm) for nm in vs), reverse=True)
        pilih = sk[0][2]
        print(f"  {jn}: " + " · ".join(f"{nm} ({-s[0]} minus, {s[1]:+.1f}R/thn)" for s, _, nm in sk) + f" -> PILIH {pilih}")
        tc, tj = seg(RES[pilih][1], b0, b1), seg(BASE[1], b0, b1); uji_c += tc; uji_j += tj
        for y in range(b0, b1 + 1):
            yc = [o["R"] for o in tc if time.gmtime(o["t"]).tm_year == y]; yj = [o["R"] for o in tj if time.gmtime(o["t"]).tm_year == y]
            rows.append((y, pilih, len(yc), sum(yc), len(yj), sum(yj)))
    for y, pl, nc, rc, nj, rj in rows:
        print(f"  {y}  {pl:<18} {nc:4d} {rc:+6.1f} {rc / max(nc, 1):+.3f} | juara {nj:4d} {rj:+6.1f} {rj / max(nj, 1):+.3f}")
    sc = bi.stats(sorted(uji_c, key=lambda o: o["t_exit"])); sj = bi.stats(sorted(uji_j, key=lambda o: o["t_exit"]))
    sig = sg.banding([(o["t_exit"], o["R"]) for o in uji_j], [(o["t_exit"], o["R"]) for o in uji_c], ts(2022), None)
    print(f"  GABUNGAN UJI 2022-2026: penantang n {sc['n']} R {sc['totR']:+.1f} R/tr {sc['avgR']:+.4f} DD {sc['maxDD']} tanpa2% {sc['tanpa_top2']}"
          f" | juara n {sj['n']} R {sj['totR']:+.1f} R/tr {sj['avgR']:+.4f} DD {sj['maxDD']} tanpa2% {sj['tanpa_top2']}")
    print(f"  signifikansi (2022-skrg): {sig}")
    print("  semua varian keluarga, seluruh periode (pembanding, tetap):")
    for nm in vs:
        s, t = RES[nm]; S = bi.stats(t, s)
        g = sg.banding([(o["t_exit"], o["R"]) for o in BASE[1]], [(o["t_exit"], o["R"]) for o in t], ts(2022), None) if nm != "off" else None
        x = f" | pasca-hoc 2022+ P_rasio {g['P_rasio_lebih_baik']} DD {g['penantang']['DD']} vs {g['juara']['DD']}" if g else ""
        m = ""
        if nm in MOD:
            M = bi.stats(MOD[nm][1], MOD[nm][0]); m = f" | T sendiri n {M['n']} R/tr {M['avgR']} DD {M['maxDD']} th {per_tahun(MOD[nm][1])}"
            jr = collections.defaultdict(float); tr_ = collections.defaultdict(float)
            for o in BASE[1]: jr[time.strftime("%Y-%m", time.gmtime(o["t_exit"]))] += o["R"]
            for o in MOD[nm][1]: tr_[time.strftime("%Y-%m", time.gmtime(o["t_exit"]))] += o["R"]
            ks = sorted(set(jr) | set(tr_)); m += f" korelasi bulanan vs juara {np.corrcoef([jr[k] for k in ks], [tr_[k] for k in ks])[0, 1]:+.2f}"
        print(f"    {nm:<18} n {S['n']} R/tr {S['avgR']:+.4f} DD {S['maxDD']} th {per_tahun(t)} grup {grp(t)}{x}{m}", flush=True)
    lap[fam] = dict(rows=rows, sig=sig)
json.dump(lap, open(f"{OUT}/saringan_2026-11-21.json", "w"), indent=1, default=str)
