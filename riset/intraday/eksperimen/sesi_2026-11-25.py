"""Sesi riset intraday Rabu 25 Nov 2026 (ATURAN_BERSAMA E + F): SATU skrip = saringan cepat 10 varian di periode pilih (<= 2021)
+ walk-forward penuh (replay penuh, daftar koin SESUAI MASANYA) untuk keluarga 2-3 teratas.

SKILL SNR tahap 2 sesi 3/3 (definisi baru terakhir, KURIKULUM program kilat 4): I-39 filter hanya untuk B-LONG
(B-short memburuk di I-35/I-36):
  1 L-PS-0.5  : lewati order B-long bila level PERIODE (high/low hari & minggu sebelumnya) ATAU SWING-D1 dalam ±0,5 ATR H1 dari limit
  2 L-PS-0.25 : idem ±0,25 ATR
  3 L-SW-0.5  : hanya SWING-D1 ±0,5 ATR, B-long saja
SUMBER EDGE BARU (I-38, cermin I-37 yang rugi kotor): modul F "FADE TEMBUSAN" mandiri. Tiap 00 UTC, koin peringkat 1-25:
limit JUAL di level atas + x ATR H1 dan limit BELI di level bawah - x ATR (hanya bila open masih di dalam level), berlaku 24 jam,
SL 1 ATR dari harga isi (taker), TP 1 ATR (maker), hold maks 12 jam. Entry maker. Dua sisi tersentuh di candle sama = rugi penuh.
Slot sendiri (CAP 3, PEND 3) -> dinilai sebagai juara + modul F (R dijumlah, risiko 1%).
  4 F-hari-cermin : level hari UTC sebelumnya, x 0,1, filter BTC = cermin I-37 (jual di high hanya bila BTC != turun, dst.)
  5 F-hari-semua  : idem tanpa filter BTC
  6 F-hari-0.5    : x 0,5 ATR (entry lebih dalam), tanpa filter BTC
  7 F-minggu-semua: level minggu ISO sebelumnya (belum tertembus minggu ini), x 0,1, tanpa filter BTC
MILESTONE T2 (monitor edge; dari saringan massal IM001, 0 penantang 24 Nov). Bobot risiko 0,5 bila PF trade yang sudah tutup
dalam N hari < 1,0 (min 20 trade). w = 0,5 tidak mengubah slot -> pasca-trade = replay penuh (tepat).
  8 M-bot-365   : seluruh bot, 365 hari (definisi T2 MILESTONE)
  9 M-modul-365 : per modul (A / B-long / B-short), 365 hari
 10 M-koin-90   : per koin, 90 hari
Pemakaian: python riset/intraday/eksperimen/sesi_2026-11-25.py <repo> <data> <out_dir>"""
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

# ------------------------------------------------------------------ modul F (FADE TEMBUSAN, I-38) — sumber edge baru
def sim_fade(D, i0, up, dn, r0, tpf, a, valid_bars, hold_bars, P):
    T, O, H, L, C = D["T"], D["O"], D["H"], D["L"], D["C"]; n = len(T); t_exp = int(T[i0]) + valid_bars * 900
    for j in range(i0, min(i0 + valid_bars, n)):
        hu = up is not None and H[j] >= up; hd = dn is not None and L[j] <= dn
        if hu and hd:                                    # dua sisi tersentuh di candle yang sama: rugi penuh (konservatif)
            pnl = -r0 - (P["MAKER"] + P["TAKER"]) / 100 * up
            return dict(filled=True, t_exp=t_exp, t_fill=int(T[j]), t_exit=int(T[j]) + 900, R=float(pnl / r0), why="SL2",
                        entry=float(up), exit=float(up + r0), d=-1), j + 1
        if hu or hd:
            d = -1 if hu else 1; lvl = up if hu else dn; fill = max(lvl, O[j]) if d == -1 else min(lvl, O[j]); j0 = j; break
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
    pnl = d * (px - fill) - (P["MAKER"] + cx) / 100 * fill - bi.funding_cost(D, int(T[j0]), int(T[j]), d) * fill
    return dict(filled=True, t_exp=t_exp, t_fill=int(T[j0]), t_exit=int(T[j]) + 900, R=float(pnl / r0), why=why,
                entry=float(fill), exit=float(px), d=d), j + 1

def gen_F(P, jenis, x=0.1, btc="semua", tpf=1.0, sl=1.0, rank_max=25, valid_jam=24, hold_jam=12):
    out = []
    for c, D in M15.items():
        T = D["T"]; G = H1[c]; GA = G["A"]; nxt = 0
        for i in np.flatnonzero(T % 86400 == 0):
            if i < max(nxt, 900) or T[i] < P["START"]: continue
            t = int(T[i]); k = D["h1"].get(t - 3600)
            if k is None or k < 400 or rank_fn(c, t) >= rank_max: continue
            a = float(GA[k]); o = float(D["O"][i]); b = BTC(t)
            hi, lo = periode(c, t, jenis)
            if jenis == "minggu" and hi is not None:
                ws = ((t // 86400 + 3) // 7 * 7 - 3) * 86400; a0 = np.searchsorted(G["T"], ws); a1 = k + 1
                if a1 > a0:
                    if G["H"][a0:a1].max() >= hi: hi = None
                    if lo is not None and G["L"][a0:a1].min() <= lo: lo = None
            okU = okD = True
            if btc == "cermin": okU, okD = b != -1, b != 1
            up = hi + x * a if (hi is not None and o < hi and okU) else None
            dn = lo - x * a if (lo is not None and o > lo and okD) else None
            if up is None and dn is None: continue
            r, nxt = sim_fade(D, i, up, dn, sl * a, tpf, a, valid_jam * 4, hold_jam * 4, P)
            d = r.pop("d"); out.append(dict(r, t=t, c=c, m="F", d=d, vr=0.0))
    return out

# ------------------------------------------------------------------ monitor edge (T2), pasca-trade, w 0,5 (slot tidak berubah)
import bisect
def monitor(trades, hari, kunci, amb=1.0, w=0.5, mn=20):
    key = {"bot": lambda o: 0, "modul": lambda o: o["m"] + str(o["d"]) if o["m"] == "B" else o["m"], "koin": lambda o: o["c"]}[kunci]
    g = collections.defaultdict(list)
    for o in trades: g[key(o)].append(o)
    out, turun = [], 0
    for v in g.values():
        tt = sorted(v, key=lambda o: o["t_exit"]); t1 = [o["t_exit"] for o in tt]
        pos = np.cumsum([max(o["R"], 0) for o in tt]); neg = np.cumsum([max(-o["R"], 0) for o in tt])
        for o in v:
            j = bisect.bisect_left(t1, o["t"]); i = bisect.bisect_left(t1, o["t"] - hari * 86400); k = 1.0
            if j - i >= mn:
                p = pos[j - 1] - (pos[i - 1] if i else 0); q = neg[j - 1] - (neg[i - 1] if i else 0)
                if q > 0 and p / q < amb: k = w
            turun += k < 1; out.append(dict(o, R=o["R"] * k))
    return sorted(out, key=lambda o: o["t_exit"]), turun

# ------------------------------------------------------------------ varian
ALLOW = lambda *a: True
def snr_long(per, sw, w):
    def f(c, t, d, ref, lim, sl, atr):
        if d != 1: return True
        lv = (list(periode(c, t)) if per else []) + (list(swing(c, t)) if sw else [])
        return not any(abs(x - lim) <= w * atr for x in lv)
    return f
def per_tahun(t):
    yr = collections.defaultdict(float)
    for o in t: yr[time.gmtime(o["t"]).tm_year] += o["R"]
    return {y: round(yr.get(y, 0.0), 1) for y in YEARS}
def grp(t):
    g = collections.defaultdict(list)
    for o in t: g["A" if o["m"] == "A" else (o["m"] if o["m"] == "F" else ("B-long" if o["d"] == 1 else "B-short"))].append(o["R"])
    return {k: (len(v), round(sum(v), 1), round(float(np.mean(v)), 3)) for k, v in sorted(g.items())}

A0 = gen_A(P0, ALLOW); B0 = gen_B(P0, ALLOW); print(f"order A {len(A0)} · B {len(B0)}", flush=True)
BASE = portfolio(A0 + B0, P0)
RES = {"off": BASE}; MOD = {}; INFO = {}
FAM = {"SNR-BLONG (I-39)": ["L-PS-0.5", "L-PS-0.25", "L-SW-0.5"],
       "FADE (I-38)": ["F-hari-cermin", "F-hari-semua", "F-hari-0.5", "F-minggu-semua"],
       "MONITOR T2": ["M-bot-365", "M-modul-365", "M-koin-90"]}
for nm, (pe, sw, w) in {"L-PS-0.5": (1, 1, 0.5), "L-PS-0.25": (1, 1, 0.25), "L-SW-0.5": (0, 1, 0.5)}.items():
    RES[nm] = portfolio(A0 + gen_B(P0, snr_long(pe, sw, w)), P0)
for nm, kw in {"F-hari-cermin": dict(jenis="hari", btc="cermin"), "F-hari-semua": dict(jenis="hari"),
               "F-hari-0.5": dict(jenis="hari", x=0.5), "F-minggu-semua": dict(jenis="minggu")}.items():
    s, t = portfolio(gen_F(P0, **kw), P0); MOD[nm] = (s, t)
    RES[nm] = (BASE[0] + s, sorted(BASE[1] + t, key=lambda o: o["t_exit"]))
for nm, (h, k) in {"M-bot-365": (365, "bot"), "M-modul-365": (365, "modul"), "M-koin-90": (90, "koin")}.items():
    t, n = monitor(BASE[1], h, k); RES[nm] = (BASE[0], t); INFO[nm] = n

# ------------------------------------------------------------------ SARINGAN (periode pilih <= 2021)
E21 = ts(2022)
def skor(t, y0, y1):
    pt = per_tahun(t); yrs = [pt[y] for y in range(y0, y1 + 1)]
    return (-sum(v <= 0 for v in yrs), sum(yrs) / len(yrs))
print("\n######## SARINGAN Mar 2020 - Des 2021 (sistem lengkap; modul F = juara + F slot sendiri)")
sar = {}
for nm, (s, t) in RES.items():
    S = bi.stats(t, s, b=E21); mi = sum(per_tahun(t)[y] <= 0 for y in (2020, 2021))
    sar[nm] = (-mi, S["rasio"])
    extra = ""
    if nm in MOD:
        M = bi.stats(MOD[nm][1], MOD[nm][0], b=E21)
        extra = f" | modul F sendiri n {M.get('n')} fill {M.get('fill')} win {M.get('win')} R/tr {M.get('avgR')} R {M.get('totR')} DD {M.get('maxDD')}"
    if nm in INFO: extra = f" | trade diperkecil (semua periode) {INFO[nm]}"
    print(f"  {nm:<16} n {S['n']} R/tr {S['avgR']:+.4f} R {S['totR']:+.1f} DD {S['maxDD']} rasio {S['rasio']} minus {mi} grup {grp([o for o in t if o['t'] < E21])}{extra}", flush=True)
urut = sorted((v for v in sar if v != "off"), key=lambda v: sar[v], reverse=True)
print("  urutan saringan: " + " > ".join(f"{v} ({sar[v][1]})" for v in urut) + f" · juara rasio {sar['off'][1]}")
top = list(FAM)                      # 3 keluarga: skill SNR sesi terakhir (wajib), edge baru (E.4), T2 (celah milestone)
print(f"  KE UJI PENUH: {top} (wajib: skill sesi 3/3, sumber edge baru, celah T2)")

# ------------------------------------------------------------------ WALK-FORWARD per keluarga
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
        print(f"  {jn}: " + " · ".join(f"{nm} ({-s[0]} minus, {s[1]:+.1f}R/thn, rasio {r})" for s, r, nm in sk) + f" -> PILIH {pilih}")
        tc, tj = seg(RES[pilih][1], b0, b1), seg(BASE[1], b0, b1); uji_c += tc; uji_j += tj
        for y in range(b0, b1 + 1):
            yc = [o["R"] for o in tc if time.gmtime(o["t"]).tm_year == y]; yj = [o["R"] for o in tj if time.gmtime(o["t"]).tm_year == y]
            rows.append((y, pilih, len(yc), sum(yc), len(yj), sum(yj)))
    for y, pl, nc, rc, nj, rj in rows:
        print(f"  {y}  {pl:<16} {nc:4d} {rc:+6.1f} {rc / max(nc, 1):+.3f} | juara {nj:4d} {rj:+6.1f} {rj / max(nj, 1):+.3f}")
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
            M = bi.stats(MOD[nm][1], MOD[nm][0]); m = f" | F sendiri n {M['n']} win {M['win']} R/tr {M['avgR']} DD {M['maxDD']} th {per_tahun(MOD[nm][1])}"
            jr = collections.defaultdict(float); tr_ = collections.defaultdict(float)
            for o in BASE[1]: jr[time.strftime("%Y-%m", time.gmtime(o["t_exit"]))] += o["R"]
            for o in MOD[nm][1]: tr_[time.strftime("%Y-%m", time.gmtime(o["t_exit"]))] += o["R"]
            ks = sorted(set(jr) | set(tr_)); m += f" korelasi bulanan vs juara {np.corrcoef([jr[k] for k in ks], [tr_[k] for k in ks])[0, 1]:+.2f}"
        print(f"    {nm:<16} n {S['n']} R/tr {S['avgR']:+.4f} DD {S['maxDD']} kalah-beruntun {S['kalah_beruntun']} th {per_tahun(t)} grup {grp(t)}{x}{m}", flush=True)
    lap[fam] = dict(rows=rows, sig=sig)
json.dump(lap, open(f"{OUT}/sesi_2026-11-25.json", "w"), indent=1, default=str)
