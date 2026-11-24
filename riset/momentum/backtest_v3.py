"""Momentum Candle v3: aturan baru dari video Rizky Aditama (24 Nov 2026), simulasi tanpa bias (mesin backtest_v2.py).
A. Ekor : W0 = lama (ekor searah <= 10%) | W1 = video (total ekor < 30%, ekor sisi asal < ekor sisi tujuan)
B. Sesi : semua 07-24 WIB | Asia 07-14 | London 14-20 | NY 20-24 WIB
C. Lokasi: tanpa | lepas konsolidasi (close tembus range 24/48 candle M5) | tidak di pucuk (jarak ke EMA50 <= 2 ATR)
           | tidak menabrak hambatan (high/low hari sebelumnya tidak berada dalam 1x panjang candle di depan)
D. Manajemen: limit Fibo 23,6% atau market; SL lebar (Fibo 100/150%, 2-3 ATR); TP ujung ekor / 1R / 1,5R / $5. Umur maks 1 jam.
Pemilihan pakai 2020-2024 (in-sample), lalu dicek di 2025-2026 (out-of-sample).
Pemakaian: python backtest_v3.py <folder_m1> [spread]"""
import itertools, runpy, sys
import numpy as np, pandas as pd

g = runpy.run_path(__file__.replace("backtest_v3.py", "backtest_v2.py"), run_name="lib")
T5, O, H, L, C, rng, body, ATR = (g[k] for k in ["T5", "O", "H", "L", "C", "rng", "body", "ATR"])
hour_wib = ((T5 % 86400) // 3600 + 7) % 24

def sesi(nm):
    return {"semua": (hour_wib >= 7), "asia": (hour_wib >= 7) & (hour_wib < 14),
            "london": (hour_wib >= 14) & (hour_wib < 20), "ny": (hour_wib >= 20)}[nm]

ema50 = pd.Series(C).ewm(span=50, adjust=False).mean().to_numpy()
day = (T5 // 86400).astype(np.int64)
dH = pd.Series(H).groupby(day).max(); dL = pd.Series(L).groupby(day).min()
PDH = pd.Series(day - 1).map(dH).to_numpy(); PDL = pd.Series(day - 1).map(dL).to_numpy()

def base(min_body, wick):
    prevH = pd.Series(H).rolling(5).max().shift(1).to_numpy(); prevL = pd.Series(L).rolling(5).min().shift(1).to_numpy()
    up_w = H - np.maximum(O, C); lo_w = np.minimum(O, C) - L
    ok = (rng > 0) & (body >= 0.70 * rng) & (body >= min_body)
    if wick == "W0":
        bull = ok & (C > O) & (up_w <= 0.10 * rng) & (C > prevH)
        bear = ok & (C < O) & (lo_w <= 0.10 * rng) & (C < prevL)
    else:   # W1: ekor sisi asal lebih pendek dari ekor sisi tujuan
        bull = ok & (C > O) & (lo_w < up_w) & (C > prevH)
        bear = ok & (C < O) & (up_w < lo_w) & (C < prevL)
    return np.where(bull, 1, np.where(bear, -1, 0)).astype(np.int64)

def lokasi(sig, nm):
    d = sig.copy()
    if nm.startswith("lepas"):
        n = int(nm[5:])
        rh = pd.Series(H).rolling(n).max().shift(1).to_numpy(); rl = pd.Series(L).rolling(n).min().shift(1).to_numpy()
        d[(d == 1) & ~(C > rh)] = 0; d[(d == -1) & ~(C < rl)] = 0
    elif nm == "bukan_pucuk":
        ext = (np.roll(C, 1) - np.roll(ema50, 1)) / ATR
        d[(d == 1) & (ext > 2)] = 0; d[(d == -1) & (ext < -2)] = 0
    elif nm == "bebas_hambatan":
        d[(d == 1) & (PDH > C) & (PDH < C + rng)] = 0
        d[(d == -1) & (PDL < C) & (PDL > C - rng)] = 0
    return d

# (nama, market, entry_fib, sl_mode, sl_v, tp_mode, tp_v)  tp_mode 0 = fibo, 1 = kelipatan R, 2 = dolar tetap
MGMT = []
for sl in [(0, 1.0, "fibo100"), (0, 1.5, "fibo150"), (1, 3.0, "3ATR")]:
    for tp in [(0, 0.0, "ujung ekor"), (1, 1.0, "1R"), (2, 5.0, "$5")]:
        MGMT.append((f"limit23.6 SL {sl[2]} TP {tp[2]}", 0, 0.236, sl[0], sl[1], tp[0], tp[1]))
for sl in [(0, 1.0, "fibo100"), (1, 2.0, "2ATR"), (1, 3.0, "3ATR")]:
    for tp in [(1, 1.0, "1R"), (1, 1.5, "1.5R"), (2, 5.0, "$5")]:
        MGMT.append((f"market SL {sl[2]} TP {tp[2]}", 1, 0.0, sl[0], sl[1], tp[0], tp[1]))

if __name__ == "__main__":
    rows = []
    for mb, wk in itertools.product([3.0, 4.0, 5.0], ["W0", "W1"]):
        b = base(mb, wk)
        for ss, lk in itertools.product(["semua", "asia", "london", "ny"], ["tanpa", "lepas24", "lepas48", "bukan_pucuk", "bebas_hambatan"]):
            sig = lokasi(np.where(sesi(ss), b, 0), lk)
            for nm, mk, ef, slm, slv, tpm, tpv in MGMT:
                st = g["stats"](g["run"](sig, mk, ef, slm, slv, tpm, tpv, 12))
                if st: rows.append(dict(bodi=mb, ekor=wk, sesi=ss, lokasi=lk, manajemen=nm, **st))
    res = pd.DataFrame(rows)
    res["pf_is"] = np.nan
    res.to_csv("hasil_v3.csv", index=False)
    print(f"Kombinasi: {len(res)} | PF>1: {(res.pf > 1).sum()} | IS>0 & OOS>0: {((res.is_R > 0) & (res.oos_R > 0)).sum()}")
