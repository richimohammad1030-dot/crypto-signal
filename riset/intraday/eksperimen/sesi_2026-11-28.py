"""Sesi riset intraday Sabtu 28 Nov 2026 (REVIEW BULANAN + ATURAN_BERSAMA E/F/G/H). SATU skrip, replay penuh, daftar koin SESUAI MASANYA.

SKILL 2 STRUKTUR PASAR (I-41) — tahap 1 PAHAM (studi peristiwa H1) lalu tahap 2 (filter order juara, walk-forward):
  Pivot fraktal n=3 di H1 (aktif setelah 3 candle kanan close). NAIK = HH+HL dua swing terakhir, TURUN = LH+LL, selain itu ACAK.
  BOS = close melewati swing terakhir searah struktur; CHoCH = close melewati swing terakhir berlawanan struktur.
  Pembanding adil: candle non-peristiwa dengan struktur sama, arah candle sama, dan desil besar candle (|C-O|/ATR) sama.
  Hasil: return maju 4/12/24 jam (ATR, ditandai arah peristiwa) dan peluang +1 ATR sebelum -1 ATR dalam 24 jam
  (dua-duanya di candle sama = kalah). Bootstrap blok bulanan, 2020-22 DAN 2023-26, kedua arah.
  Tahap 2 varian (filter keep di generator order, replay penuh):
    S-B       : lewati B-long bila struktur H1 TURUN, B-short bila NAIK
    S-AB      : idem + lewati A (beli dip) bila struktur TURUN
    C24-B     : lewati order B bila ada CHoCH berlawanan arah order dalam 24 jam terakhir
    C24-AB    : idem untuk A juga
SKILL 1 SNR (T10: tidak boleh ditutup sebelum 31 Des -> CARA PAKAI BARU, I-43): jarak ke level sebagai BOBOT RISIKO (bukan filter),
  order B yang limitnya ≤ x ATR dari level PERIODE (high/low hari & minggu sebelumnya) diberi risiko 0,5 -> slot tidak berubah.
    W-0.25, W-0.5
SUMBER EDGE BARU (I-44) [lit] lead-lag BTC -> altcoin (Sifat, Mohamad & Shariff 2019 "Lead-lag
  relationship between Bitcoin and Ethereum", RIBAF 50): candle H1 BTC bergerak ≥ k ATR, koin peringkat 2-25 yang candle jam itu
  bergerak < 0,3 × k ATR searah dibeli/dijual MARKET di open 15m berikutnya (taker, slip termasuk), SL 1 ATR H1, TP 1 ATR (maker),
  hold maks 4 jam. Slot sendiri (CAP 3, PEND 3). Short hanya bila koin punya funding (futures).
    LL-1.5, LL-2.0, LL-2.0-long
Pemakaian: python riset/intraday/eksperimen/sesi_2026-11-28.py <repo> <data> <out_dir>"""
import bisect, calendar, collections, json, os, sys, time
REPO, DATA, OUT = sys.argv[1:4]
sys.path.insert(0, REPO); sys.path.insert(0, os.path.join(REPO, "riset"))
import numpy as np
import backtest_intraday as bi, pit, signal_bot as sb, signifikansi as sg

os.makedirs(OUT, exist_ok=True)
P0 = dict(bi.PARAM)
YEARS = list(range(2020, 2027))
ts = lambda y: calendar.timegm((y, 1, 1, 0, 0, 0))
yr_of = lambda t: time.gmtime(t).tm_year

pit._load(DATA)
ALL = sorted({c for m in pit._SNAP for c in pit.ranked(DATA, m)[:70]} | set(sb.COINS))
H1, M15 = bi.load(DATA, ALL)
first = {c: int(D["T"][900]) for c, D in M15.items() if len(D["T"]) > 900}
uni = pit.universe_fn(DATA, lambda c, t: c in first and c in H1 and first[c] <= t)
BTC = bi.btc_regime_fn(H1)
rank_fn = lambda c, t: uni(t).index(c) if c in uni(t) else 999
print(f"koin dimuat {len(M15)}", flush=True)

# ================================================================== STRUKTUR H1 per koin
EV_NAMA = {2: "BOS-naik", -2: "BOS-turun", 1: "CHoCH-naik", -1: "CHoCH-turun"}
ST = {}
for c, G in H1.items():
    H, L, C = G["H"], G["L"], G["C"]; n = len(C); m = 3
    ph = np.zeros(n, bool); pl = np.zeros(n, bool)
    win = np.lib.stride_tricks.sliding_window_view
    if n > 2 * m + 1:
        ph[m:n - m] = H[m:n - m] >= win(H, 2 * m + 1).max(axis=1)
        pl[m:n - m] = L[m:n - m] <= win(L, 2 * m + 1).min(axis=1)
    state = np.zeros(n, np.int8); ev = np.zeros(n, np.int8)
    sh = [np.nan, np.nan]; sl = [np.nan, np.nan]; s = 0
    for k in range(n):
        i = k - m                                         # pivot di i dikonfirmasi saat candle k close
        if i >= m:
            if ph[i]: sh = [sh[1], H[i]]
            if pl[i]: sl = [sl[1], L[i]]
            if sh[0] == sh[0] and sl[0] == sl[0]:
                s = 1 if (sh[1] > sh[0] and sl[1] > sl[0]) else (-1 if (sh[1] < sh[0] and sl[1] < sl[0]) else 0)
        if k > 0 and sh[1] == sh[1] and sl[1] == sl[1]:
            up = C[k] > sh[1] >= C[k - 1]; dn = C[k] < sl[1] <= C[k - 1]
            if s == 1: ev[k] = 2 if up else (-1 if dn else 0)
            elif s == -1: ev[k] = -2 if dn else (1 if up else 0)
        state[k] = s
    ST[c] = (state, ev)
print("struktur H1 selesai", flush=True)

def struk(c, t):
    """struktur & peristiwa dari candle H1 yang SUDAH close sebelum t."""
    G = H1[c]; k = bisect.bisect_right(G["T"], t - 3600) - 1
    return k

# ================================================================== TAHAP 1: studi peristiwa
# versi cepat tahap 1: rata-rata sel pembanding dihitung sekali per (koin, periode, state, sgn, dec)
def tahap1_cepat():
    out = collections.defaultdict(list)                   # (jenis, periode) -> list (bulan, ex4, ex12, ex24, exhit)
    for c, G in H1.items():
        if c not in first: continue
        T, O, H, L, C, A = G["T"], G["O"], G["H"], G["L"], G["C"], G["A"]; n = len(C); state, ev = ST[c]
        if n < 1000: continue
        K = np.arange(400, n - 25); K = K[T[K] >= max(P0["START"], first[c])]
        if len(K) < 500: continue
        a = A[K]; fw = np.stack([(C[K + h] - C[K]) / a for h in (4, 12, 24)], 1)
        hitL = np.zeros(len(K)); hitS = np.zeros(len(K)); dL = np.zeros(len(K), bool); dS = np.zeros(len(K), bool)
        for h in range(1, 25):
            uu = H[K + h] - C[K] >= a; dd_ = C[K] - L[K + h] >= a
            hitL[~dL & uu & ~dd_] = 1; dL |= uu | dd_
            hitS[~dS & dd_ & ~uu] = 1; dS |= uu | dd_
        body = (C[K] - O[K]) / a; sgn = np.sign(body).astype(int); dec = np.minimum((np.abs(body) * 4).astype(int), 7)
        st = state[K].astype(int); e = ev[K].astype(int)
        yy = (T[K] // 31557600 + 1970).astype(int)          # tahun kira-kira (cukup untuk pembagian periode)
        mon = (T[K] // (30.44 * 86400)).astype(int)
        cellkey = (st + 1) * 100 + (sgn + 1) * 10 + dec
        for jn, (y0, y1) in (("2020-22", (2020, 2022)), ("2023-26", (2023, 2026))):
            per = (yy >= y0) & (yy <= y1)
            base = per & (e == 0)
            for code in (2, -2, 1, -1):
                d = 1 if code > 0 else -1
                isE = np.flatnonzero(per & (e == code))
                if not len(isE): continue
                val = np.column_stack([fw * d, hitL if d == 1 else hitS])
                for ck in np.unique(cellkey[isE]):
                    bm = base & (cellkey == ck)
                    if bm.sum() < 30: continue
                    mu = val[bm].mean(0); ee = isE[cellkey[isE] == ck]
                    for j in ee: out[(code, jn)].append((int(mon[j]), *(val[j] - mu), *val[j]))
    return out

def boot(rows, col, sims=2000, seed=3):
    g = collections.defaultdict(list)
    for r in rows: g[r[0]].append(r[col])
    ks = list(g); s = np.array([sum(g[k]) for k in ks]); nn = np.array([len(g[k]) for k in ks]); rng = np.random.default_rng(seed)
    ix = rng.integers(0, len(ks), (sims, len(ks))); m = s[ix].sum(1) / np.maximum(nn[ix].sum(1), 1)
    return float((m > 0).mean())

print("\n######## SKILL 2 STRUKTUR · TAHAP 1 PAHAM (excess vs pembanding sel sama; P = peluang excess > 0, bootstrap blok bulanan)")
T1 = tahap1_cepat(); hasil1 = {}
for code in (2, -2, 1, -1):
    for jn in ("2020-22", "2023-26"):
        r = T1.get((code, jn), [])
        if not r: continue
        R = np.array(r)
        ex = {nm: (round(float(R[:, i].mean()), 4), round(boot(r, i), 3)) for i, nm in ((1, "r4"), (2, "r12"), (3, "r24"), (4, "hit"))}
        hasil1[(code, jn)] = ex
        print(f"  {EV_NAMA[code]:<12} {jn} n {len(r):6d} | hit mentah {R[:, 8].mean():.3f} | excess (rata, P>0): " +
              " · ".join(f"{k} {v[0]:+.4f} P {v[1]:.3f}" for k, v in ex.items()), flush=True)
def lulus(kodes, k):
    ps = [hasil1[(c, j)][k][1] for c in kodes for j in ("2020-22", "2023-26") if (c, j) in hasil1]
    return len(ps) == 4 and (min(ps) >= 0.90 or max(ps) <= 0.10)
VON = {}
for nm, kodes in (("BOS", (2, -2)), ("CHoCH", (1, -1))):
    VON[nm] = {k: lulus(kodes, k) for k in ("r4", "r12", "r24", "hit")}
    print(f"  VONIS {nm}: " + " · ".join(f"{k} {'LULUS' if v else 'tidak'}" for k, v in VON[nm].items()))

# ================================================================== generator juara (salinan bi.orders + filter keep)
def gen_A(P, keep):
    out = []
    for c, D in M15.items():
        T, C, A, R2, R14, reg = D["T"], D["C"], D["A"], D["R2"], D["R14"], D["reg"]; nxt = 0
        for i in np.flatnonzero((reg == 1) & ((R2 < 5) | (R14 < 30)) & (A / C >= P["A_VMIN"])):
            if i < max(nxt, 900) or i + 1 >= len(T) or T[i] < P["START"]: continue
            t1 = int(T[i + 1])
            if rank_fn(c, t1) >= P["A_RANK_MAX"] or (P["A_BTC"] and BTC(t1) != 1): continue
            lim, r0 = C[i] - P["A_OFF"] * A[i], P["A_SL"] * A[i]
            if not keep(c, t1, 1, "A", float(lim), float(A[i])): continue
            r, nxt = bi.sim(D, i + 1, 1, lim, r0, lim + P["A_TP_R"] * r0, P["A_VALID_MIN"] // 15, P["A_HOLD_JAM"] * 4, None, P)
            out.append(dict(r, t=t1, c=c, m="A", d=1, lim=float(lim), atr=float(A[i])))
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
            if not keep(c, int(T[i]), tr, "B", float(lim), float(a)): continue
            r, nxt = bi.sim(D, i, tr, lim, P["B_SL"] * a, lim + tr * P["B_TPF"] * P["B_K"] * a, P["B_VALID_JAM"] * 4, P["B_HOLD_JAM"] * 4, None, P)
            out.append(dict(r, t=int(T[i]), c=c, m="B", d=tr, lim=float(lim), atr=float(a)))
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

# ------------------------------------------------------------------ filter STRUKTUR (tahap 2)
def f_struk(mode, modul):
    def f(c, t, d, m, lim, atr):
        if m not in modul: return True
        k = struk(c, t)
        if k < 50: return True
        state, ev = ST[c]
        if mode == "S": return not (int(state[k]) == -d)
        lo = max(0, k - 23); e = ev[lo:k + 1]
        return not np.any(e == -d)                        # CHoCH berlawanan arah order (-1 utk long, +1 utk short)
    return f
ALLOW = lambda *a: True

# ------------------------------------------------------------------ level PERIODE (SNR bobot risiko)
LV = {}
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
def periode(c, t):
    dh, dl, wh, wl = LV[c]; d = t // 86400; w = (d + 3) // 7
    return [x for x in (dh.get(d - 1), dl.get(d - 1), wh.get(w - 1), wl.get(w - 1)) if x is not None]
def snr_w(trades, x):
    out, n = [], 0
    for o in trades:
        k = 1.0
        if o["m"] == "B" and any(abs(v - o["lim"]) <= x * o["atr"] for v in periode(o["c"], o["t"])): k = 0.5; n += 1
        out.append(dict(o, R=o["R"] * k))
    return out, n

# ------------------------------------------------------------------ modul LL (lead-lag BTC -> altcoin), market entry
def sim_mkt(D, i0, d, r0, tp_a, hold_bars, P):
    T, O, H, L, C = D["T"], D["O"], D["H"], D["L"], D["C"]; n = len(T)
    fill = float(O[i0]); sl, tp = fill - d * r0, fill + d * tp_a
    for j in range(i0, min(i0 + hold_bars, n)):
        if (d == 1 and L[j] <= sl) or (d == -1 and H[j] >= sl):
            px = sl if j == i0 else (min(sl, O[j]) if d == 1 else max(sl, O[j])); cx, why = P["TAKER"], "SL"; break
        if (d == 1 and H[j] >= tp) or (d == -1 and L[j] <= tp):
            if j == i0 and d * (C[j] - tp) < 0: continue    # di candle isi: SL dulu (dicek di atas), TP hanya bila close lewat
            px, cx, why = tp, P["MAKER"], "TP"; break
    else:
        j = min(i0 + hold_bars, n) - 1; px, cx, why = C[j], P["TAKER"], "WAKTU"
    pnl = d * (px - fill) - (P["TAKER"] + cx) / 100 * fill - bi.funding_cost(D, int(T[i0]), int(T[j]), d) * fill
    return dict(filled=True, t_exp=int(T[i0]) + 900, t_fill=int(T[i0]), t_exit=int(T[j]) + 900, R=float(pnl / r0), why=why,
                entry=fill, exit=float(px)), j + 1

def gen_LL(P, k=1.5, lag=0.3, short=True, hold_jam=4, rank_max=25):
    B = H1["BTC"]; bix = {int(t): j for j, t in enumerate(B["T"])}
    out = []
    for c, D in M15.items():
        if c == "BTC" or c not in first: continue
        G = H1[c]; GT = G["T"]; nxt = 0
        cand = []
        for kk in range(400, len(GT) - 1):
            t = int(GT[kk]) + 3600                         # candle H1 kk sudah close di t
            if t < max(P["START"], first[c]): continue
            jb = bix.get(int(GT[kk]))
            if jb is None or jb < 20: continue
            rb = (B["C"][jb] - B["O"][jb]) / B["A"][jb - 1]
            if abs(rb) < k: continue
            d = 1 if rb > 0 else -1
            if d == -1 and (not short or not G["fb"][0]): continue
            ra = (G["C"][kk] - G["O"][kk]) / G["A"][kk - 1] * d
            if ra >= lag * k: continue
            cand.append((t, d, float(G["A"][kk])))
        T = D["T"]
        for t, d, a in cand:
            i = int(np.searchsorted(T, t))
            if i >= len(T) or T[i] != t or i < nxt: continue
            if rank_fn(c, t) >= rank_max or rank_fn(c, t) == 0: continue
            r, nxt = sim_mkt(D, i, d, a, a, hold_jam * 4, P)
            out.append(dict(r, t=t, c=c, m="L", d=d))
    return out

# ================================================================== varian
def per_tahun(t):
    yr = collections.defaultdict(float)
    for o in t: yr[yr_of(o["t"])] += o["R"]
    return {y: round(yr.get(y, 0.0), 1) for y in YEARS}
def grp(t):
    g = collections.defaultdict(list)
    for o in t: g["A" if o["m"] == "A" else (o["m"] if o["m"] == "L" else ("B-long" if o["d"] == 1 else "B-short"))].append(o["R"])
    return {k: (len(v), round(sum(v), 1), round(float(np.mean(v)), 3)) for k, v in sorted(g.items())}

A0 = gen_A(P0, ALLOW); B0 = gen_B(P0, ALLOW); print(f"order A {len(A0)} · B {len(B0)}", flush=True)
BASE = portfolio(A0 + B0, P0)
RES = {"off": BASE}; MOD = {}; INFO = {}
FAM = {"STRUKTUR (I-41)": ["S-B", "S-AB", "C24-B", "C24-AB"],
       "SNR-BOBOT (I-43)": ["W-0.25", "W-0.5"],
       "LEAD-LAG (I-44)": ["LL-1.5", "LL-2.0", "LL-2.0-long"]}
for nm, (mode, modul) in {"S-B": ("S", "B"), "S-AB": ("S", "AB"), "C24-B": ("C", "B"), "C24-AB": ("C", "AB")}.items():
    f = f_struk(mode, modul); RES[nm] = portfolio(gen_A(P0, f) + gen_B(P0, f), P0); print(f"  {nm} selesai", flush=True)
for nm, x in {"W-0.25": 0.25, "W-0.5": 0.5}.items():
    t, n = snr_w(BASE[1], x); RES[nm] = (BASE[0], t); INFO[nm] = n
for nm, kw in {"LL-1.5": dict(k=1.5), "LL-2.0": dict(k=2.0), "LL-2.0-long": dict(k=2.0, short=False)}.items():
    s, t = portfolio(gen_LL(P0, **kw), P0); MOD[nm] = (s, t)
    RES[nm] = (BASE[0] + s, sorted(BASE[1] + t, key=lambda o: o["t_exit"])); print(f"  {nm} selesai ({len(t)} trade)", flush=True)

# ------------------------------------------------------------------ dampak pada SL juara (KURIKULUM: SL dicegah vs pemenang hilang)
print("\n######## DAMPAK FILTER STRUKTUR pada trade juara (pasca-trade, indikatif; keputusan dari replay penuh)")
for nm, (mode, modul) in {"S-B": ("S", "B"), "S-AB": ("S", "AB"), "C24-B": ("C", "B"), "C24-AB": ("C", "AB")}.items():
    f = f_struk(mode, modul); buang = [o for o in BASE[1] if not f(o["c"], o["t"], o["d"], o["m"], o["lim"], o["atr"])]
    sl = [o for o in buang if o["why"] == "SL"]; win = [o for o in buang if o["R"] > 0]
    print(f"  {nm:<7} trade terbuang {len(buang)} (R {sum(o['R'] for o in buang):+.1f}) · SL dicegah {len(sl)} dari {sum(o['why'] == 'SL' for o in BASE[1])}"
          f" · pemenang hilang {len(win)} · R/tr terbuang {np.mean([o['R'] for o in buang]) if buang else 0:+.3f}")

# ------------------------------------------------------------------ SARINGAN (periode pilih <= 2021)
E21 = ts(2022)
def skor(t, y0, y1):
    pt = per_tahun(t); yrs = [pt[y] for y in range(y0, y1 + 1)]
    return (-sum(v <= 0 for v in yrs), sum(yrs) / len(yrs))
print("\n######## SARINGAN Mar 2020 - Des 2021 (sistem lengkap; modul L = juara + L slot sendiri)")
sar = {}
for nm, (s, t) in RES.items():
    S = bi.stats(t, s, b=E21); mi = sum(per_tahun(t)[y] <= 0 for y in (2020, 2021))
    sar[nm] = (-mi, S["rasio"]); extra = ""
    if nm in MOD:
        M = bi.stats(MOD[nm][1], MOD[nm][0], b=E21)
        extra = f" | modul L sendiri n {M.get('n')} win {M.get('win')} R/tr {M.get('avgR')} R {M.get('totR')} DD {M.get('maxDD')}"
    if nm in INFO: extra = f" | trade diperkecil (semua periode) {INFO[nm]}"
    print(f"  {nm:<12} n {S['n']} R/tr {S['avgR']:+.4f} R {S['totR']:+.1f} DD {S['maxDD']} rasio {S['rasio']} minus {mi} grup {grp([o for o in t if o['t'] < E21])}{extra}", flush=True)
urut = sorted((v for v in sar if v != "off"), key=lambda v: sar[v], reverse=True)
print("  urutan saringan: " + " > ".join(f"{v} ({sar[v][1]})" for v in urut) + f" · juara rasio {sar['off'][1]}")

# ------------------------------------------------------------------ WALK-FORWARD per keluarga + STRES 0,03R/trade
JEN = (("pilih<=2021", 2020, 2021, 2022, 2023), ("pilih<=2023", 2020, 2023, 2024, 2025), ("pilih<=2025", 2020, 2025, 2026, 2026))
def seg(t, y0, y1): return [o for o in t if y0 <= yr_of(o["t"]) <= y1]
lap = {"tahap1": {f"{EV_NAMA[k[0]]} {k[1]}": v for k, v in hasil1.items()}, "vonis_tahap1": VON, "saringan": sar}
for fam in FAM:
    vs = ["off"] + FAM[fam]
    print(f"\n######## {fam} walk-forward", flush=True)
    uji_c, uji_j, rows = [], [], []
    for jn, a0, a1, b0, b1 in JEN:
        sk = sorted(((skor(RES[nm][1], a0, a1), bi.stats(seg(RES[nm][1], a0, a1))["rasio"], nm) for nm in vs), reverse=True)
        pilih = sk[0][2]
        print(f"  {jn}: " + " · ".join(f"{nm} ({-s[0]} minus, {s[1]:+.1f}R/thn, rasio {r})" for s, r, nm in sk) + f" -> PILIH {pilih}")
        tc, tj = seg(RES[pilih][1], b0, b1), seg(BASE[1], b0, b1); uji_c += tc; uji_j += tj
        for y in range(b0, b1 + 1):
            yc = [o["R"] for o in tc if yr_of(o["t"]) == y]; yj = [o["R"] for o in tj if yr_of(o["t"]) == y]
            rows.append((y, pilih, len(yc), sum(yc), len(yj), sum(yj)))
    for y, pl, nc, rc, nj, rj in rows:
        print(f"  {y}  {pl:<12} {nc:4d} {rc:+6.1f} {rc / max(nc, 1):+.3f} | juara {nj:4d} {rj:+6.1f} {rj / max(nj, 1):+.3f}")
    sc = bi.stats(sorted(uji_c, key=lambda o: o["t_exit"])); sj = bi.stats(sorted(uji_j, key=lambda o: o["t_exit"]))
    sig = sg.banding([(o["t_exit"], o["R"]) for o in uji_j], [(o["t_exit"], o["R"]) for o in uji_c], ts(2022), None)
    sgs = sg.banding([(o["t_exit"], o["R"] - 0.03) for o in uji_j], [(o["t_exit"], o["R"] - 0.03) for o in uji_c], ts(2022), None)
    print(f"  GABUNGAN UJI 2022-2026: penantang n {sc['n']} R {sc['totR']:+.1f} R/tr {sc['avgR']:+.4f} PF {sc['pf']} DD {sc['maxDD']} tanpa2% {sc['tanpa_top2']}"
          f" | juara n {sj['n']} R {sj['totR']:+.1f} R/tr {sj['avgR']:+.4f} PF {sj['pf']} DD {sj['maxDD']} tanpa2% {sj['tanpa_top2']}")
    print(f"  signifikansi (2022-skrg): {sig}")
    print(f"  STRES -0,03R/trade: P_rasio {sgs['P_rasio_lebih_baik']} · penantang {sgs['penantang']} · juara {sgs['juara']}")
    print("  semua varian keluarga, seluruh periode (pembanding, tetap):")
    for nm in vs:
        s, t = RES[nm]; S = bi.stats(t, s)
        g = sg.banding([(o["t_exit"], o["R"]) for o in BASE[1]], [(o["t_exit"], o["R"]) for o in t], ts(2022), None) if nm != "off" else None
        x = f" | pasca-hoc 2022+ P_rasio {g['P_rasio_lebih_baik']} DD {g['penantang']['DD']} vs {g['juara']['DD']}" if g else ""
        m = ""
        if nm in MOD:
            M = bi.stats(MOD[nm][1], MOD[nm][0]); m = f" | L sendiri n {M['n']} win {M['win']} R/tr {M['avgR']} DD {M['maxDD']} th {per_tahun(MOD[nm][1])}"
        print(f"    {nm:<12} n {S['n']} R/tr {S['avgR']:+.4f} PF {S['pf']} DD {S['maxDD']} kalah-beruntun {S['kalah_beruntun']} th {per_tahun(t)} grup {grp(t)}{x}{m}", flush=True)
    lap[fam] = dict(rows=rows, sig=sig, stres=sgs["P_rasio_lebih_baik"])

# ------------------------------------------------------------------ penyebab SL backtest juara (ATURAN G a): per modul × struktur
print("\n######## PENYEBAB SL BACKTEST JUARA (PIT, semua periode): porsi SL per modul × struktur H1 saat order")
g = collections.defaultdict(lambda: [0, 0, 0.0])
for o in BASE[1]:
    k = struk(o["c"], o["t"]); s = int(ST[o["c"]][0][k]) if k >= 0 else 0
    key = ("A" if o["m"] == "A" else ("B-long" if o["d"] == 1 else "B-short"), {1: "searah", -1: "lawan", 0: "acak"}[s * o["d"]])
    g[key][0] += 1; g[key][1] += o["why"] == "SL"; g[key][2] += o["R"]
for k in sorted(g):
    n, nsl, R = g[k]; print(f"  {k[0]:<8} struktur {k[1]:<7} n {n:4d} SL {nsl:4d} ({nsl / n * 100:4.1f}%) R/tr {R / n:+.3f}")
why = collections.Counter(o["why"] for o in BASE[1]); print("  cara keluar juara:", dict(why))
json.dump(lap, open(f"{OUT}/sesi_2026-11-28.json", "w"), indent=1, default=str)
# simpan trade juara PIT untuk review bulanan & konfirmasi
import csv
with open(f"{OUT}/trades_pit.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["c", "m", "d", "t", "t_fill", "t_exit", "R", "why"])
    for o in BASE[1]: w.writerow([o["c"], o["m"], o["d"], o["t"], o["t_fill"], o["t_exit"], round(o["R"], 5), o["why"]])
print("SELESAI")
