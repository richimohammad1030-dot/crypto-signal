"""Riset mingguan intraday 6 Nov 2026 (replay penuh, daftar koin sesuai masanya = uji utama; daftar tetap = pembanding).
I-22  Modul A cermin SHORT saat BTC H1 turun: koin tren turun 15m, RSI2 > 95 atau RSI14 > 70, ATR >= 1,5%, peringkat 1-25,
      funding 72 jam > 0, LIMIT short 0,5 ATR di atas close, SL 3 ATR, TP 2x SL, tutup paksa 4 jam (ditambahkan ke juara v3).
I-23  [lit] Modul A hanya untuk dip IDIOSINKRATIS: lewati sinyal jika BTC 15m sendiri sedang dip (RSI2 BTC 15m di candle sinyal
      < ambang). Da, Liu & Schaumburg (2014) "A Closer Look at the Short-Term Return Reversal", Management Science 60(3):
      reversal jangka pendek terutama berasal dari komponen return idiosinkratis, bukan pergerakan pasar.
Pemakaian: python riset/intraday/eksperimen/pit_2026-11-06.py <repo> <data> <out_dir>"""
import collections, csv, json, os, sys, time
REPO, DATA, OUT = sys.argv[1:4]
sys.path.insert(0, REPO); sys.path.insert(0, os.path.join(REPO, "riset"))
import numpy as np
import backtest_intraday as bi, pit, signal_bot as sb, signifikansi as sg

P0 = dict(bi.PARAM)
YEARS = list(range(2020, 2027))

# ------------------------------------------------------------------ data (sekali)
pit._load(DATA)
ALL = sorted({c for m in pit._SNAP for c in pit.ranked(DATA, m)[:70]} | set(sb.COINS))
H1, M15 = bi.load(DATA, ALL)
first = {c: int(D["T"][900]) for c, D in M15.items() if len(D["T"]) > 900}
uni = pit.universe_fn(DATA, lambda c, t: c in first and c in H1 and first[c] <= t)
BTC = bi.btc_regime_fn(H1)
B15 = M15["BTC"]; B15ix = {int(t): k for k, t in enumerate(B15["T"])}
FIX = {c: i for i, c in enumerate(sb.COINS)}

def btc_r2(t_sig):
    k = B15ix.get(t_sig)
    return float(B15["R2"][k]) if k is not None else 50.0

# ------------------------------------------------------------------ generator order (salinan orders() + variasi)
def gen(P, pitmode, ashort=None, idio=None):
    """ashort: dict parameter modul A-short (None = mati). idio: ambang RSI2 BTC 15m (None = mati)."""
    if pitmode:
        rank_fn = lambda c, t: uni(t).index(c) if c in uni(t) else 999
        coins = list(M15)
    else:
        rank_fn = lambda c, t: FIX.get(c, 999)
        coins = [c for c in sb.COINS if c in M15]
    out = []
    for c in coins:
        D = M15[c]; G = H1[c]
        T, C, A, R2, R14, reg = D["T"], D["C"], D["A"], D["R2"], D["R14"], D["reg"]
        nxt = 0
        for i in np.flatnonzero((reg == 1) & ((R2 < 5) | (R14 < 30)) & (A / C >= P["A_VMIN"])):
            if i < max(nxt, 900) or i + 1 >= len(T) or T[i] < P["START"]: continue
            t1 = int(T[i + 1])
            if rank_fn(c, t1) >= P["A_RANK_MAX"] or (P["A_BTC"] and BTC(t1) != 1): continue
            if idio is not None and c != "BTC" and btc_r2(int(T[i])) < idio: continue
            lim, r0 = C[i] - P["A_OFF"] * A[i], P["A_SL"] * A[i]
            r, nxt = bi.sim(D, i + 1, 1, lim, r0, lim + P["A_TP_R"] * r0, P["A_VALID_MIN"] // 15, P["A_HOLD_JAM"] * 4, None, P)
            out.append(dict(r, t=t1, c=c, m="A", d=1, vr=0.0))
        if ashort:
            S = ashort; nxt = 0
            for i in np.flatnonzero((reg == -1) & ((R2 > S["r2"]) | (R14 > S["r14"])) & (A / C >= S["vmin"])):
                if i < max(nxt, 900) or i + 1 >= len(T) or T[i] < P["START"]: continue
                t1 = int(T[i + 1])
                if rank_fn(c, t1) >= S["rank"] or BTC(t1) != -1: continue
                if S["fund"] and (bi.funding_avg72(G, t1 // 3600 * 3600 - 3600) or 0) <= 0: continue
                lim, r0 = C[i] + S["off"] * A[i], S["sl"] * A[i]
                r, nxt = bi.sim(D, i + 1, -1, lim, r0, lim - S["tp"] * r0, 8, S["hold"] * 4, None, P)
                out.append(dict(r, t=t1, c=c, m="As", d=-1, vr=0.0))
        GA = G["A"]; nxt = 0
        for i in np.flatnonzero(T % 86400 == 0):
            if i < max(nxt, 900) or T[i] < P["START"]: continue
            k = D["h1"].get(int(T[i]) - 3600)
            if k is None or k < 400: continue
            a = GA[k]; vr = a / GA[k - 336:k].mean(); tr = int(G["reg"][k])
            if vr < P["B_VR"] or a / G["C"][k] < P["B_ATRP"] or tr == 0: continue
            if P["B_BTC"] and int(G["btc"][k]) != tr: continue
            if tr == -1 and (not P["B_SHORT"] or (bi.funding_avg72(G, int(G["T"][k])) or 0) <= 0): continue
            o = D["O"][i]; lim = o - tr * P["B_K"] * a
            r, nxt = bi.sim(D, i, tr, lim, P["B_SL"] * a, lim + tr * P["B_TPF"] * P["B_K"] * a, P["B_VALID_JAM"] * 4, P["B_HOLD_JAM"] * 4, None, P)
            out.append(dict(r, t=int(T[i]), c=c, m="B", d=tr, vr=float(vr)))
    if pitmode: out = [o for o in out if o["c"] in uni(o["t"])]
    return out

# ------------------------------------------------------------------ portofolio (sama dengan pit_intraday.run_pit / bi.portfolio)
def portfolio(ords, pitmode, cap=3, pend_max=3):
    rank_of = (lambda o: uni(o["t"]).index(o["c"])) if pitmode else (lambda o: FIX[o["c"]])
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
            if len(pos) < cap:
                pos.append((o["t_exit"], o["c"])); taken.append(o)
                if len(pos) >= cap: pend = []
        pend = [p for p in pend if p[0] > now]; pos = [(e, c) for e, c in pos if e > now]
    for o in ev:
        settle(o["t"])
        if o["c"] in {c for _, c in pos} | {x["c"] for _, x in pend} or len(pend) >= pend_max or len(pos) >= cap: continue
        sent.append(o); pend.append(((o["t_fill"] + 1) if o["filled"] else o["t_exp"], o))
    settle(2_000_000_000)
    return sent, sorted(taken, key=lambda o: o["t_exit"])

def ringkas(s, t):
    out = dict(semua=bi.stats(t, s), lama=bi.stats(t, s, b=bi.IS_END), baru=bi.stats(t, s, a=bi.IS_END))
    yr = collections.defaultdict(float)
    for o in t: yr[time.gmtime(o["t"]).tm_year] += o["R"]
    out["tahun"] = {y: round(yr.get(y, 0.0), 1) for y in YEARS}
    mod = collections.defaultdict(list)
    for o in t:
        if o["t"] >= bi.IS_END: mod[o["m"] + ("+" if o["d"] == 1 else "-")].append(o["R"])
    out["modul_baru"] = {k: (len(v), round(sum(v), 1)) for k, v in sorted(mod.items())}
    return out

def keputusan(b, a):
    r_l = a["lama"]["rasio"] / b["lama"]["rasio"] - 1; r_b = a["baru"]["rasio"] / b["baru"]["rasio"] - 1
    th = sum(a["tahun"][y] >= b["tahun"][y] for y in YEARS); t2 = a["semua"]["tanpa_top2"] >= b["semua"]["tanpa_top2"]
    return dict(lolos=bool(r_l >= 0.10 and r_b >= 0.10 and th >= 5 and t2), dL=round(r_l * 100, 1), dB=round(r_b * 100, 1), thn=th, top2=bool(t2))

RES = {}
def uji(nama, pitmode, base=None, **kw):
    s, t = portfolio(gen(P0, pitmode, **kw), pitmode)
    r = ringkas(s, t)
    if base is not None:
        r["kep"] = keputusan(base[0], r)
        r["P"] = sg.banding([(o["t_exit"], o["R"]) for o in base[1]], [(o["t_exit"], o["R"]) for o in t], mulai=bi.IS_END)["P_rasio_lebih_baik"]
    L, B, S = r["lama"], r["baru"], r["semua"]
    line = (f"{nama:<34} n={S['n']:5d} fill={S['fill']:5}% win={S['win']:4}% R/tr={S['avgR']:+.4f} R/thn={S['totR_thn']:+6.1f} DD={S['maxDD']:5.1f} "
            f"| L n={L['n']} avg {L['avgR']:+.3f} DD {L['maxDD']} rasio {L['rasio']:5.2f} | B n={B['n']} avg {B['avgR']:+.3f} R/thn {B['totR_thn']:+.1f} DD {B['maxDD']} rasio {B['rasio']:5.2f} "
            f"| top2 {S['tanpa_top2']} | " + " ".join(f"{y % 100}:{v:+.0f}" for y, v in r["tahun"].items()) + f" | modul24+ {r['modul_baru']}")
    if base is not None:
        k = r["kep"]; line += f" -> dL {k['dL']:+}% dB {k['dB']:+}% thn {k['thn']}/7 top2 {k['top2']} P {r['P']:.2f} {'LOLOS' if k['lolos'] else 'gagal'}"
    print(line, flush=True)
    RES[nama] = r
    return s, t, r

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for pitmode, lab in ((True, "PIT"), (False, "TETAP")):
        print(f"\n===== {lab} =====", flush=True)
        s0, t0, r0 = uji(f"{lab} juara v3", pitmode)
        with open(f"{OUT}/juara_{lab}.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["t", "t_fill", "t_exit", "c", "m", "d", "R", "why"], extrasaction="ignore"); w.writeheader(); w.writerows(t0)
        base = (r0, t0)
        BASE_S = dict(r2=95, r14=70, vmin=0.015, rank=25, fund=True, off=0.5, sl=3.0, tp=2.0, hold=4)
        print("-- I-22 A-short cermin --", flush=True)
        varian = [("I22 dasar", {})]
        if pitmode:
            varian += [("I22 tanpa funding", dict(fund=False)), ("I22 RSI 97/75", dict(r2=97, r14=75)), ("I22 RSI 90/65", dict(r2=90, r14=65)),
                       ("I22 limit 0,25", dict(off=0.25)), ("I22 limit 0,75", dict(off=0.75)), ("I22 hold 3j", dict(hold=3)), ("I22 hold 6j", dict(hold=6)),
                       ("I22 SL 2 ATR", dict(sl=2.0)), ("I22 TP 1x", dict(tp=1.0)), ("I22 peringkat 1-50", dict(rank=50))]
        for nm, ov in varian:
            uji(f"{lab} {nm}", pitmode, base, ashort=dict(BASE_S, **ov))
        print("-- I-23 dip idiosinkratis (RSI2 BTC 15m >= ambang) --", flush=True)
        for th in ((5, 10, 20, 30, 50) if pitmode else (10, 20, 30)):
            uji(f"{lab} I23 BTC RSI2>={th}", pitmode, base, idio=th)
    json.dump(RES, open(f"{OUT}/hasil.json", "w"), indent=1)
