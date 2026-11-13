"""Backtest strategi Momentum Candle XAUUSD (M5, simulasi jalur harga pakai M1).
Pip baku XAU: 1 pip = $0,01 (Dupoin). Spread 30 pip = $0,30 (data Dukascopy = BID; ASK = BID + spread).
Jam aktif 07:00-24:00 WIB (00:00-17:00 UTC). Semua posisi/order ditutup paksa 24:00 WIB. Tanpa layering, 1 posisi pada satu waktu.
Hasil dalam R (risiko 1% per trade).
Pemakaian: python backtest_momentum.py <folder_m1>  (berisi xau_m1_<tahun>.csv.gz)"""
import glob, gzip, itertools, sys
import numpy as np, pandas as pd

SPREAD = 0.30
FOLDER = sys.argv[1]

# ---------- data ----------
fr = []
for p in sorted(glob.glob(f"{FOLDER}/xau_m1_*.csv.gz")):
    fr.append(pd.read_csv(gzip.open(p, "rt"), header=None, names=["t", "o", "h", "l", "c"]))
m1 = pd.concat(fr).drop_duplicates("t").sort_values("t").reset_index(drop=True)
for k in "ohlc": m1[k] = m1[k] / 1000.0
T1, O1, H1, L1, C1 = (m1[k].to_numpy().astype(np.float64) for k in "tohlc")
m1["b5"] = m1.t // 300 * 300
m5 = m1.groupby("b5").agg(o=("o", "first"), h=("h", "max"), l=("l", "min"), c=("c", "last"), i0=("t", "size")).reset_index()
m5["i_end"] = m1.reset_index().groupby("b5")["index"].max().values      # indeks M1 terakhir dalam candle M5
T5 = m5.b5.to_numpy().astype(np.float64); O, H, L, C = (m5[k].to_numpy() for k in "ohlc"); IEND = m5.i_end.to_numpy()
rng = H - L; body = np.abs(C - O)
tr = np.maximum(H[1:], C[:-1]) - np.minimum(L[1:], C[:-1]); tr = np.r_[rng[0], tr]
ATR = pd.Series(tr).rolling(14).mean().shift(1).to_numpy()                # ATR candle sebelumnya
hour_utc = (T5 % 86400) // 3600
in_sess = hour_utc < 17                                                    # 07:00-24:00 WIB
day_end = ((T5 // 86400) * 86400 + 17 * 3600).astype(np.float64)                                # 24:00 WIB = 17:00 UTC
print(f"Data M1: {len(m1):,} candle | M5: {len(m5):,} | {pd.to_datetime(T5[0], unit='s').date()} s.d. {pd.to_datetime(T5[-1], unit='s').date()}")

def signals(min_body, use_atr, accum):
    """Kandidat momentum: bodi ≥ 70% range, ekor searah ≤ 10% range, close tembus high/low 5 candle sebelumnya."""
    prevH = pd.Series(H).rolling(5).max().shift(1).to_numpy(); prevL = pd.Series(L).rolling(5).min().shift(1).to_numpy()
    ok = (rng > 0) & (body >= 0.70 * rng) & in_sess
    ok &= (body >= min_body * ATR) if use_atr else (body >= min_body)
    if accum:   # 3 candle sebelumnya kecil (bodi masing-masing ≤ 40% bodi momentum)
        sm = pd.Series(body).rolling(3).max().shift(1).to_numpy(); ok &= sm <= 0.4 * body
    bull = ok & (C > O) & ((H - C) <= 0.10 * rng) & (C > prevH)
    bear = ok & (C < O) & ((C - L) <= 0.10 * rng) & (C < prevL)
    return np.where(bull, 1, np.where(bear, -1, 0))

def lvl(i, d, f):
    """Level Fibonacci ditarik dari pangkal ke ujung candle momentum: 0 = ujung (high utk buy), 1 = pangkal. f negatif = ekstensi."""
    return H[i] - f * rng[i] if d == 1 else L[i] + f * rng[i]

from numba import njit

@njit(cache=True)
def _run(sig, T5, H, L, rng, IEND, day_end, T1, O1, H1, L1, mode_close, ef, tp_f, cancel_f, max_bars, spread):
    n = 0; outt = np.zeros(len(sig)); outd = np.zeros(len(sig)); outr = np.zeros(len(sig)); busy = -1
    for i in range(len(sig)):
        d = sig[i]
        if d == 0 or i <= busy or i + 1 >= len(T5): continue
        def_lv = H[i] if d == 1 else L[i]
        sl = def_lv - d * 0.745 * rng[i]; tp = def_lv - d * tp_f * rng[i]; cx = def_lv - d * cancel_f * rng[i]
        j = IEND[i] + 1
        end_t = day_end[i] if max_bars <= 0 else min(day_end[i], T5[i] + 300 + max_bars * 300)
        if end_t <= T5[i] + 300 or j >= len(T1): continue
        t_in = -1; e = 0.0
        if mode_close:
            e = O1[j] + spread if d == 1 else O1[j]; t_in = j
        else:
            lim = def_lv - d * ef * rng[i]
            while j < len(T1) and T1[j] < day_end[i]:
                if d == 1:
                    if L1[j] + spread <= lim:
                        t_in = j; e = min(lim, O1[j] + spread); break
                    if H1[j] >= cx: break
                else:
                    if H1[j] >= lim:
                        t_in = j; e = max(lim, O1[j]); break
                    if L1[j] + spread <= cx: break
                j += 1
            if t_in < 0: continue
        risk = (e - sl) * d
        if risk <= 0 or (tp - e) * d <= 0: continue
        k = t_in; res = 1e9
        while k < len(T1):
            if T1[k] >= end_t:
                px = O1[k] if d == 1 else O1[k] + spread
                res = (px - e) * d / risk; break
            if d == 1:
                hb = H1[k]; lb = L1[k]
            else:
                hb = H1[k] + spread; lb = L1[k] + spread
            if (d == 1 and lb <= sl) or (d == -1 and hb >= sl):
                res = -1.0; break
            if (d == 1 and hb >= tp) or (d == -1 and lb <= tp):
                res = (tp - e) * d / risk; break
            k += 1
        if res == 1e9: continue
        kk = min(k, len(T1) - 1)
        busy = np.searchsorted(T5, T1[kk], 'right') - 1
        outt[n] = T5[i]; outd[n] = d; outr[n] = res; n += 1
    return outt[:n], outd[:n], outr[:n]

def run(sig, entry, tp_f, cancel_f, max_bars):
    """entry: 'close' (market saat candle close) atau fibo limit (0.236/0.382/0.5). SL fibo 0.745.
    tp_f: fibo TP (0 = ujung ekor, -0.27, ...). cancel_f: limit batal bila harga menyentuh fibo ini dulu.
    max_bars: umur posisi (candle M5), None = sampai 24:00 WIB. SL & TP di bar M1 yang sama = SL."""
    mc = entry == "close"
    t, d, r = _run(sig.astype(np.int64), T5, H, L, rng, IEND.astype(np.int64), day_end, T1, O1, H1, L1,
                   mc, 0.0 if mc else float(entry), float(tp_f), float(cancel_f), int(max_bars or 0), SPREAD)
    return pd.DataFrame(dict(t=t, d=d, r=r))

def stats(df):
    if len(df) < 20: return None
    r = df.r.to_numpy(); w = r > 0; eq = np.cumsum(r); dd = (np.maximum.accumulate(eq) - eq).max()
    yrs = df.groupby(pd.to_datetime(df.t, unit="s").dt.year).r.sum()
    weeks = (df.t.max() - df.t.min()) / 604800
    s = "".join("W" if x else "L" for x in w); mls = max(len(x) for x in s.split("W")); mws = max(len(x) for x in s.split("L"))
    return dict(n=len(r), per_mgg=len(r) / max(weeks, 1), wr=w.mean() * 100,
                pf=r[w].sum() / max(-r[~w].sum(), 1e-9), avgR=r.mean(), totR=r.sum(), ddR=dd,
                kalah_beruntun=mls, menang_beruntun=mws, thn_plus=f"{(yrs > 0).sum()}/{len(yrs)}",
                per_thn=" ".join(f"{y % 100}:{v:+.0f}" for y, v in yrs.items()))

if __name__ == "__main__":
    grid = dict(
        filt=[("$0,65", 0.65, False), ("$6,50", 6.50, False), ("2xATR", 2.0, True), ("3xATR", 3.0, True)],
        accum=[False, True],
        entry=["close", 0.236, 0.382, 0.5],
        tp=[0.0, -0.27, -0.618, -1.0],
        cancel=[-0.27, -0.5, -1.0],
        hold=[12, None],
    )
    rows = []
    for (nm, mb, ua), ac in itertools.product(grid["filt"], grid["accum"]):
        sig = signals(mb, ua, ac)
        for en, tp, cx, hd in itertools.product(grid["entry"], grid["tp"], grid["cancel"], grid["hold"]):
            if en == "close" and (tp == 0.0 or cx != -0.27): continue   # entry close: TP ujung ekor = 0 jarak; batal tidak relevan
            if en != "close" and cx >= tp: continue                      # batal harus lebih jauh dari TP
            st = stats(run(sig, en, tp, cx, hd))
            if st: rows.append(dict(filter=nm, akumulasi=ac, entry=en, tp=tp, batal=cx, hold="1j" if hd else "24WIB", **st))
    res = pd.DataFrame(rows).sort_values("totR", ascending=False)
    res.to_csv("hasil_grid.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    print(res.head(25).round(2).to_string(index=False))
