"""Backtest Momentum Candle v2 (tanpa bias urutan harga). Dua keluarga strategi:
  Opsi 1 PULLBACK  : limit di fibo entry, SL di fibo, TP di ekstensi fibo (RR > 1).
  Opsi 2 BREAKOUT  : market di open candle berikutnya, SL = fibo candle / kelipatan ATR, TP = kelipatan R.
Aturan simulasi (konservatif):
  - Data BID; ASK = BID + spread. Buy masuk di ASK, keluar di BID. Sell sebaliknya.
  - Di bar M1 tempat limit terisi, TP TIDAK dihitung (urutan harga tak diketahui), SL dihitung.
  - SL & TP di bar M1 yang sama = SL.
  - Limit batal bila TP tersentuh sebelum terisi, atau saat 24:00 WIB.
Pemakaian: python backtest_v2.py <folder_m1> [spread]"""
import glob, gzip, itertools, sys
import numpy as np, pandas as pd
from numba import njit

FOLDER = sys.argv[1]; SPREAD = float(sys.argv[2]) if len(sys.argv) > 2 else 0.30

fr = [pd.read_csv(gzip.open(p, "rt"), header=None, names=["t", "o", "h", "l", "c"]) for p in sorted(glob.glob(f"{FOLDER}/xau_m1_*.csv.gz"))]
m1 = pd.concat(fr).drop_duplicates("t").sort_values("t").reset_index(drop=True)
for k in "ohlc": m1[k] = m1[k] / 1000.0
T1, O1, H1, L1 = (m1[k].to_numpy().astype(np.float64) for k in "tohl")
m1["b5"] = m1.t // 300 * 300
g5 = m1.reset_index().groupby("b5")
m5 = g5.agg(o=("o", "first"), h=("h", "max"), l=("l", "min"), c=("c", "last"), iend=("index", "max")).reset_index()
T5 = m5.b5.to_numpy().astype(np.float64); O, H, L, C = (m5[k].to_numpy() for k in "ohlc"); IEND = m5.iend.to_numpy().astype(np.int64)
rng = H - L; body = np.abs(C - O)
tr = np.r_[rng[0], np.maximum(H[1:], C[:-1]) - np.minimum(L[1:], C[:-1])]
ATR = pd.Series(tr).rolling(14).mean().to_numpy()                 # ATR termasuk candle sinyal (diketahui saat close)
in_sess = ((T5 % 86400) // 3600) < 17                              # 07:00-24:00 WIB
DAYEND = ((T5 // 86400) * 86400 + 17 * 3600).astype(np.float64)
print(f"M1 {len(m1):,} | M5 {len(m5):,} | {pd.to_datetime(T5[0], unit='s').date()} - {pd.to_datetime(T5[-1], unit='s').date()} | spread ${SPREAD}")

def signals(min_body):
    prevH = pd.Series(H).rolling(5).max().shift(1).to_numpy(); prevL = pd.Series(L).rolling(5).min().shift(1).to_numpy()
    ok = (rng > 0) & (body >= 0.70 * rng) & in_sess & (body >= min_body)
    bull = ok & (C > O) & ((H - C) <= 0.10 * rng) & (C > prevH)
    bear = ok & (C < O) & ((C - L) <= 0.10 * rng) & (C < prevL)
    return np.where(bull, 1, np.where(bear, -1, 0)).astype(np.int64)

@njit
def sim(sig, T5, H, L, rng, ATR, IEND, DAYEND, T1, O1, H1, L1, spread,
        market, ef, sl_mode, sl_v, tp_mode, tp_v, max_bars):
    """market=1: masuk di open bar M1 setelah candle close. market=0: limit di fibo ef.
    sl_mode 0: SL di fibo sl_v candle; 1: SL = sl_v x ATR dari harga entry.
    tp_mode 0: TP di fibo tp_v (negatif = ekstensi); 1: TP = tp_v x jarak risiko; 2: TP = tp_v dolar."""
    n = 0; ot = np.zeros(len(sig)); od = np.zeros(len(sig)); orr = np.zeros(len(sig)); busy = -1
    for i in range(len(sig)):
        d = sig[i]
        if d == 0 or i <= busy or i + 1 >= len(T5): continue
        tip = H[i] if d == 1 else L[i]
        j = IEND[i] + 1
        if j >= len(T1) or T1[j] >= DAYEND[i]: continue
        end_t = DAYEND[i] if max_bars <= 0 else min(DAYEND[i], T5[i] + 300 + max_bars * 300)
        # level awal (untuk limit, SL/TP fibo sudah tetap)
        t_in = -1; e = 0.0
        if market == 1:
            e = O1[j] + spread if d == 1 else O1[j]; t_in = j
        else:
            lim = tip - d * ef * rng[i]
            tp_pre = tip - d * tp_v * rng[i] if tp_mode == 0 else 1e18 * d
            while j < len(T1) and T1[j] < end_t:          # limit hanya berlaku selama umur maksimal
                if d == 1:
                    if L1[j] + spread <= lim:
                        t_in = j; e = min(lim, O1[j] + spread); break
                    if H1[j] >= tp_pre: break
                else:
                    if H1[j] >= lim:
                        t_in = j; e = max(lim, O1[j]); break
                    if L1[j] + spread <= tp_pre: break
                j += 1
            if t_in < 0: continue
        if sl_mode == 0: sl = tip - d * sl_v * rng[i]
        elif sl_mode == 1: sl = e - d * sl_v * ATR[i]
        else: sl = e - d * sl_v                    # sl_mode 2: SL dolar tetap
        risk = (e - sl) * d
        if risk <= 0: continue
        if tp_mode == 0: tp = tip - d * tp_v * rng[i]
        elif tp_mode == 1: tp = e + d * tp_v * risk
        else: tp = e + d * tp_v                    # tp_mode 2: TP dolar tetap
        if (tp - e) * d <= 0: continue
        k = t_in; res = 1e9
        while k < len(T1):
            if T1[k] >= end_t:
                px = O1[k] if d == 1 else O1[k] + spread
                res = (px - e) * d / risk; break
            hb = H1[k] if d == 1 else H1[k] + spread
            lb = L1[k] if d == 1 else L1[k] + spread
            if (d == 1 and lb <= sl) or (d == -1 and hb >= sl):
                res = -1.0; break
            if (d == 1 and hb >= tp) or (d == -1 and lb <= tp):
                if market == 1 or k != t_in:
                    res = (tp - e) * d / risk; break
            k += 1
        if res == 1e9: continue
        busy = np.searchsorted(T5, T1[min(k, len(T1) - 1)], 'right') - 1
        ot[n] = T5[i]; od[n] = d; orr[n] = res; n += 1
    return ot[:n], od[:n], orr[:n]

def run(sig, market, ef, sl_mode, sl_v, tp_mode, tp_v, max_bars):
    t, d, r = sim(sig, T5, H, L, rng, ATR, IEND, DAYEND, T1, O1, H1, L1, SPREAD,
                  market, ef, sl_mode, sl_v, tp_mode, tp_v, max_bars)
    return pd.DataFrame(dict(t=t, d=d, r=r))

DAYS = pd.Series(T5[in_sess] // 86400).nunique()
def stats(df):
    if len(df) < 30: return None
    r = df.r.to_numpy(); w = r > 0; eq = np.cumsum(r)
    yrs = df.groupby(pd.to_datetime(df.t, unit="s").dt.year).r.sum()
    s = "".join("W" if x else "L" for x in w)
    return dict(n=len(r), per_hari=len(r) / DAYS, wr=w.mean() * 100, avg_win=r[w].mean() if w.any() else 0,
                pf=r[w].sum() / max(-r[~w].sum(), 1e-9), totR=r.sum(), ddR=(np.maximum.accumulate(eq) - eq).max(),
                kalah_beruntun=max(len(x) for x in s.split("W")), thn_plus=int((yrs > 0).sum()), thn=len(yrs),
                is_R=yrs[yrs.index <= 2024].sum(), oos_R=yrs[yrs.index >= 2025].sum(),
                per_thn=" ".join(f"{y % 100}:{v:+.0f}" for y, v in yrs.items()))

if __name__ == "__main__":
    rows = []
    for mb in [3.0, 4.0, 5.0, 6.5]:
        sig = signals(mb)
        # ---- Opsi 1: pullback, RR besar ----
        for ef, slf, tpf, hold in itertools.product([0.236, 0.382, 0.5], [0.618, 0.745, 1.0], [-0.27, -0.618, -1.0], [12, 0]):
            if slf <= ef: continue
            st = stats(run(sig, 0, ef, 0, slf, 0, tpf, hold))
            if st: rows.append(dict(opsi="1 pullback", bodi=mb, entry=f"fibo {ef}", sl=f"fibo {slf}", tp=f"fibo {tpf}", hold="1j" if hold else "24WIB", **st))
        # ---- Opsi 2: breakout searah, market ----
        for (slm, slv), rr, hold in itertools.product([(0, 0.5), (0, 1.0), (1, 1.0), (1, 1.5), (1, 2.0)], [1.0, 1.5, 2.0, 3.0], [12, 48, 0]):
            st = stats(run(sig, 1, 0.0, slm, slv, 1, rr, hold))
            if st: rows.append(dict(opsi="2 breakout", bodi=mb, entry="market", sl=(f"fibo {slv}" if slm == 0 else f"{slv}xATR"),
                                    tp=f"{rr}R", hold={12: "1j", 48: "4j", 0: "24WIB"}[hold], **st))
    res = pd.DataFrame(rows).sort_values("pf", ascending=False)
    res.to_csv("hasil_v2.csv", index=False)
    pd.set_option("display.width", 260); pd.set_option("display.max_columns", 30)
    cols = ["opsi", "bodi", "entry", "sl", "tp", "hold", "n", "per_hari", "wr", "pf", "totR", "ddR", "kalah_beruntun", "thn_plus", "is_R", "oos_R", "per_thn"]
    print(f"Total kombinasi: {len(res)} | PF>1: {(res.pf > 1).sum()} | PF>1 & semua periode (IS & OOS) positif: {((res.pf > 1) & (res.is_R > 0) & (res.oos_R > 0)).sum()}")
    for o in ["1 pullback", "2 breakout"]:
        print(f"\n=== Opsi {o} (top 10 PF) ===")
        print(res[res.opsi == o].head(10)[cols].round(2).to_string(index=False))
