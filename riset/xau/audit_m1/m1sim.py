"""Simulasi ulang bot XAU live per menit (M1 BID Dukascopy) memakai sinyal & parameter yang SAMA dengan mesin H1 repo.
Parameter realisme: spread (USD, ask=bid+spread), delay_min (menit keterlambatan entry), slip_sl (USD slippage tambahan saat SL),
gap (True = order stop/SL terisi di harga open bila harga loncat melewati level), flat (biaya flat USD/trade ala repo)."""
import numpy as np
from base import *

D = build_D(); T, O, Hh, Ll, Cc = D
A = np.array(m.atr(list(Hh), list(Ll), list(Cc), 14)); F = m.fitur(D, A)
SIG = mm.sinyal_live(D); KOMBO = mm.sinyal_kombo(D)
t1, o1, h1, l1, c1 = load_m1_fixed()
_o = np.argsort(t1, kind="stable"); t1, o1, h1, l1, c1 = t1[_o], o1[_o], h1[_o], l1[_o], c1[_o]
t1 = t1.astype(np.int64)
M1_START, M1_END = t1[0], t1[-1]
HR = ((T // 3600) % 24).astype(int)
RSI2 = mm.rsi(Cc, 2)
GAP_MONTHS = {"2023-06", "2023-07"}

def manage(a, b, d, e, slp, tpp, S, gap, slip_sl):
    """Kelola posisi di menit a..b-1 (indeks M1), entry e (sudah termasuk spread). Return (exit, t_exit, why).
    Long: keluar di bid, SL/TP dipicu bid. Short: dipicu & keluar di ask = bid + S. SL dicek sebelum TP dalam 1 menit."""
    for k in range(a, b):
        if d == 1:
            lo, hi, op = l1[k], h1[k], o1[k]
            if lo <= slp: return (min(slp, op) if gap else slp) - slip_sl, t1[k], "SL"
            if tpp is not None and hi >= tpp: return (max(tpp, op) if gap else tpp), t1[k], "TP"
        else:
            lo, hi, op = l1[k] + S, h1[k] + S, o1[k] + S
            if hi >= slp: return (max(slp, op) if gap else slp) + slip_sl, t1[k], "SL"
            if tpp is not None and lo <= tpp: return (min(tpp, op) if gap else tpp), t1[k], "TP"
    return (c1[b - 1] if d == 1 else c1[b - 1] + S), t1[b - 1], "TUTUP"

def day(i, S=0.0, delay=0, gap=False, slip_sl=0.0, ambigu_k6="m1"):
    """Hasil hari bursa dengan candle penempatan i. Return list trade (dict) atau []"""
    out = []
    ts0 = int(T[i]) + 3600; te = int(T[i]) + 17 * 3600          # 07:00 WIB .. 23:00 WIB
    ym = __import__("datetime").datetime.fromtimestamp(ts0, __import__("datetime").timezone.utc).strftime("%Y-%m")
    if ym in GAP_MONTHS or ts0 < M1_START or te > M1_END: return None
    a0 = int(np.searchsorted(t1, ts0)); b0 = int(np.searchsorted(t1, te))
    if b0 - a0 < 0.80 * 960: return None
    act = int(np.searchsorted(t1, ts0 + 60 * delay))               # menit aktif order (setelah keterlambatan)
    if i in SIG:
        d = SIG[i]; sl_atr = gb.KOMBO_SL_ATR if i in KOMBO else gb.MR_SL_ATR; dist = sl_atr * A[i]
        if dist <= 0.5: return []
        e0 = o1[a0]                                                 # harga acuan sinyal (open 07:00)
        e = (o1[act] + S) if d == 1 else o1[act]
        slp = e0 - d * dist if d == 1 else e0 + d * -dist           # SL absolut dari harga acuan
        slp = e0 - dist if d == 1 else e0 + dist
        ex, tx, why = manage(act, b0, d, e, slp, None, S, gap, slip_sl)
        r0 = dist
        return [dict(ip=i, strat="KOMBO" if i in KOMBO else "MR", d=d, e=e, ex=ex, r0=r0, t0=t1[act], t1=tx, why=why, R=(ex - e) * d / r0)]
    # ---- K6 ----
    ema = F["ema200"][i]
    if np.isnan(ema) or i < 250: return []
    hi_, lo_ = Hh[i - 2:i + 1].max(), Ll[i - 2:i + 1].min(); dist = gb.SL_ATR * A[i]
    if dist <= 0.5: return []
    eb, es = hi_, lo_; up = Cc[i] > ema
    fill = None
    for k in range(act, b0):
        bh = h1[k] + S >= eb; sh = l1[k] <= es
        if bh and sh:
            d_ = (-1 if up else 1) if ambigu_k6 == "m1" else 1      # sama menit: anggap sisi lawan tren (dilewati) dulu = konservatif utk strategi
        elif bh: d_ = 1
        elif sh: d_ = -1
        else: continue
        fill = (k, d_); break
    if fill is None: return []
    k, d_ = fill
    if d_ == 1:
        e = max(eb, o1[k] + S) if gap else eb + 0.0
        e = max(eb, o1[k] + S) if gap else max(eb, o1[k] + S)
        slp, tpp = eb - dist, eb + gb.RR * dist
    else:
        e = min(es, o1[k]); slp, tpp = es + dist, es - gb.RR * dist
    trend_side = (d_ == 1) == up
    if trend_side:
        r0 = abs(e - slp)
        # menit terisi: hanya SL yang dicek (konservatif, sama dengan mesin H1)
        ex, tx, why = manage(k, b0, d_, e, slp, tpp, S, gap, slip_sl)
        return [dict(ip=i, strat="K6", d=d_, e=e, ex=ex, r0=r0, t0=t1[k], t1=tx, why=why, R=(ex - e) * d_ / r0)]
    # ---- hari K6 dilewati -> SUSULAN (ide #37) ----
    q = int(np.searchsorted(T, (t1[k] // 3600) * 3600))
    if q >= len(T) or int(T[q]) != int(t1[k] // 3600 * 3600): return []
    jam = set(gb.SUS_JAM_UTC)
    while q < len(T) and HR[q] not in jam and HR[q] != sm.CLOSE: q += 1
    if q >= len(T) - 1 or HR[q] not in jam: return []
    r = RSI2[q]
    if not (r <= gb.SUS_BUY or r >= gb.SUS_SELL): return []
    d2 = 1 if r <= gb.SUS_BUY else -1; dist2 = gb.SUS_SL_ATR * A[q]
    if dist2 <= 0.5: return []
    ts2 = int(T[q + 1]); a2 = int(np.searchsorted(t1, ts2 + 60 * delay)); 
    if a2 >= b0: return []
    e0 = o1[int(np.searchsorted(t1, ts2))]
    e = (o1[a2] + S) if d2 == 1 else o1[a2]
    slp = e0 - dist2 if d2 == 1 else e0 + dist2
    tpp = e0 + gb.SUS_TP_R * dist2 if d2 == 1 else e0 - gb.SUS_TP_R * dist2
    ex, tx, why = manage(a2, b0, d2, e, slp, tpp, S, gap, slip_sl)
    return [dict(ip=i, strat="SUS", d=d2, e=e, ex=ex, r0=dist2, t0=t1[a2], t1=tx, why=why, R=(ex - e) * d2 / dist2)]

def run(S=0.0, delay=0, gap=False, slip_sl=0.0, flat=0.40, ambigu_k6="m1"):
    res = []; skipped = []
    for i in np.flatnonzero(HR == gb.PLACE_HOUR_UTC):
        if i < 250 or i + 1 >= len(T): continue
        r = day(i, S, delay, gap, slip_sl, ambigu_k6)
        if r is None: skipped.append(i); continue
        res += r
    for x in res: x["net"] = x["R"] - flat / x["r0"]
    return res, skipped
