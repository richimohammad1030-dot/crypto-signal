"""TAMBAL-CELAH putaran 1 (6 Nov 2026) · celah: 2025 (pasar berombak) -> filter "pasar tanpa arah" per koin.
#52 [lit] Efficiency Ratio Kaufman (P. Kaufman, "Smarter Trading" 1995 / "Trading Systems and Methods"):
     ER = |C_t - C_{t-20h}| / jumlah |perubahan harian| 20 hari. Order baru hanya jika ER >= ambang.
#53 [lit] ADX Wilder (J. W. Wilder, "New Concepts in Technical Trading Systems" 1978): ADX(14) harian >= ambang.
Keduanya gerbang order baru (replay penuh, slot ikut berubah), BUY & SELL. Hanya data candle yang sudah tutup.
R bersih skenario REAL (tahap0_semua_tahun.py). Metrik utama: tahun minus (biasa & tanpa 2% terbaik per tahun), tahun terburuk.
Pemilihan ambang: periode 2020-2023 saja (rasio R/DD dan tahun terburuk), 2024-2026 = uji. Argumen: <repo> <data_dir>."""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tahap0_semua_tahun as t0
rp = t0.rp
rp.load(t0.REPO, t0.DATA_DIR)

ER, ADX = {}, {}
for c, D in rp.DATA.items():
    C = np.asarray(D["C"], float); H = np.asarray(D["H"], float); L = np.asarray(D["L"], float); n = len(C)
    # Efficiency Ratio 20 hari dari close per 24 jam yang berakhir di candle i
    er = np.full(n, np.nan)
    if n > 481:
        num = np.abs(C[480:] - C[:-480])
        step = np.abs(C[24:] - C[:-24])                      # perubahan 24 jam di setiap candle
        den = np.zeros(n - 480)
        for k in range(20):                                  # jumlah 20 perubahan harian berurutan
            den += step[480 - 24 * (k + 1):n - 24 * (k + 1)]   # step[j] = |C[j+24] - C[j]|
        er[480:] = num / np.where(den > 0, den, np.nan)
    ER[c] = er
    # ADX(14) harian dihitung di setiap candle (jendela 24 jam bergulir, smoothing Wilder per fase jam)
    hs = pd.Series(H).rolling(24).max().values; ls = pd.Series(L).rolling(24).min().values
    adx = np.full(n, np.nan)
    for p in range(24):
        ix = np.arange(p + 24, n, 24)
        if len(ix) < 40: continue
        h, l, cprev = hs[ix], ls[ix], C[ix - 24]
        hp, lp = hs[ix - 24], ls[ix - 24]
        up, dn = h - hp, lp - l
        pdm = np.where((up > dn) & (up > 0), up, 0.0); mdm = np.where((dn > up) & (dn > 0), dn, 0.0)
        tr = np.maximum(h, cprev) - np.minimum(l, cprev)
        sm = lambda x: pd.Series(x).ewm(alpha=1 / 14, adjust=False).mean().values
        atr = sm(tr)
        pdi, mdi = 100 * sm(pdm) / atr, 100 * sm(mdm) / atr
        dx = 100 * np.abs(pdi - mdi) / np.where(pdi + mdi > 0, pdi + mdi, np.nan)
        a = sm(np.nan_to_num(dx)).copy(); a[:28] = np.nan
        adx[ix] = a
    ADX[c] = adx


def gate_of(arr, th):
    return lambda coin, i, D, d, en, sl, t: not (arr[coin][i] < th)     # NaN (data kurang) -> izinkan


VAR = {"Juara": None}
for th in (0.15, 0.20, 0.25, 0.30, 0.35):
    VAR[f"#52 ER>={th:.2f}"] = gate_of(ER, th)
for th in (15, 20, 25, 30):
    VAR[f"#53 ADX>={th}"] = gate_of(ADX, th)

res = {}
for k, g in VAR.items():
    df = t0.add_costs(t0.run_replay(g)[0])
    df.to_csv(f"{t0.DATA_DIR}/tambal1_{k.split()[0].strip('#')}_{k.split()[-1].replace('>=', '')}.csv", index=False)
    old, new = df[df.year.between(2020, 2023)], df[df.year >= 2024]
    s = t0.ringkas_tahun(df)
    s["rasio_lama"] = old.R_REAL.sum() / t0.maxdd(old.R_REAL.values)
    s["rasio_baru"] = new.R_REAL.sum() / t0.maxdd(new.R_REAL.values)
    s["worst_lama"] = min(v for y, v in s["per"].items() if y <= 2023)
    res[k] = s
    print(f"{k:<14} n {s['n']:4d} tot {s['tot']:6.1f} DD {s['dd']:5.1f} · rasio lama {s['rasio_lama']:5.1f} baru {s['rasio_baru']:5.1f}"
          f" · minus {s['minus']} / tanpa2 {s['minus2']} · terburuk {s['worst']:+.1f} / tanpa2 {s['worst2']:+.1f}", flush=True)
    print("   per tahun:", s["per"], "\n   tanpa2   :", s["per2"], flush=True)
pd.to_pickle(res, f"{t0.DATA_DIR}/tambal1_res.pkl")
