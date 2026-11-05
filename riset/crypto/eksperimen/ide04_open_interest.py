"""Ide #4 · Open interest (OI) Binance futures: breakout dengan OI naik vs turun.
Hipotesis: breakout 20 hari yang disertai OI naik (posisi baru masuk searah) lebih kuat daripada breakout dengan OI turun
(hanya penutupan posisi lawan / short squeeze), sehingga menolak order saat OI turun memperbaiki rasio R/DD.
Data: arsip harian `metrics` data.binance.vision (riset/crypto/eksperimen/unduh_oi.py) -> OI per jam, umumnya mulai Des 2021
(BTC Sep 2020). Bila OI tidak tersedia (sebelum arsip ada / koin tanpa futures) gerbang MENGIZINKAN (sama dengan juara).
Karena itu periode lama dinilai juga pada 2022-2023 saja (periode yang punya data OI).
Gerbang dicek setiap candle saat order dibuat/diperbarui (replay penuh, slot ikut berubah).
Argumen: <repo> <data_dir>."""
import bisect, json, os
import numpy as np, pandas as pd
from _common import setup
rp, champ, data_dir = setup()

OI = {}
for c in rp.DATA:
    p = f"{data_dir}/oi/{c}.json"
    if os.path.exists(p):
        r = json.load(open(p))
        if r:
            OI[c] = (np.array([x[0] for x in r], float), np.array([x[1] for x in r], float))
print("koin dengan data OI:", len(OI), "dari", len(rp.DATA))


def oi_chg(coin, t, hrs):
    """Perubahan OI (fraksi) selama `hrs` jam sampai candle jam t (nilai jam t = 5 menit terakhir sebelum candle tutup)."""
    if coin not in OI:
        return np.nan
    ts, v = OI[coin]
    j = bisect.bisect_right(ts, t) - 1
    if j < 0 or t - ts[j] > 3 * 3600:
        return np.nan
    k = bisect.bisect_right(ts, t - hrs * 3600) - 1
    if k < 0 or (t - hrs * 3600) - ts[k] > 6 * 3600 or v[k] <= 0:
        return np.nan
    return v[j] / v[k] - 1


# ---------------- diagnostik pada trade juara (jam sebelum fill)
champ = champ.copy()
for h in (24, 72, 168):
    champ[f"oi{h}"] = [oi_chg(c, t - 3600, h) for c, t in zip(champ.coin, champ.t0)]
champ["per"] = np.where(champ.year >= 2024, "2024-skrg", np.where(champ.year >= 2022, "2022-2023", "2020-2021"))
champ["arah"] = np.where(champ.d == 1, "BUY", "SELL")
print("trade juara dengan OI 7 hari:", int(champ.oi168.notna().sum()), "/", len(champ))
for h in (72, 168):
    g = champ.dropna(subset=[f"oi{h}"]).copy()
    g["kel"] = np.where(g[f"oi{h}"] > 0, "OI naik", "OI turun")
    print(f"== OI {h} jam: naik vs turun")
    print(g.groupby(["per", "arah", "kel"]).R.agg(["count", "mean", "sum"]).round(3).to_string())
    g["q"] = g.groupby("arah")[f"oi{h}"].transform(lambda x: pd.qcut(x, 4, labels=False))
    print(f"== OI {h} jam: kuartil per arah (0 = paling turun)")
    print(g.groupby(["per", "arah", "q"]).R.agg(["count", "mean"]).round(3).unstack("q").to_string())
    print(g.groupby("arah")[f"oi{h}"].quantile([.25, .5, .75]).round(3).to_string())


# ---------------- replay penuh dengan gerbang
def gate_maker(rule, hrs=168):
    def g(coin, i, D, d, en, sl, t):
        x = oi_chg(coin, t, hrs)
        if np.isnan(x):
            return True
        return rule(d, x)
    return g

VAR = {
    "A: OI 7 hari naik (BUY & SELL)": gate_maker(lambda d, x: x > 0),
    "B: OI 7 hari naik (BUY saja)": gate_maker(lambda d, x: d == -1 or x > 0),
    "C: tolak OI 7 hari < -10%": gate_maker(lambda d, x: x > -0.10),
    "D: OI 3 hari naik (BUY & SELL)": gate_maker(lambda d, x: x > 0, 72),
}
res = {}
for k, g in VAR.items():
    res[k] = rp.replay(g)[0]


def sub(df):
    return df[df.year >= 2022]


print(rp.HEADER)
print(rp.fmt_compare("Juara", rp.compare(champ, champ)))
for k, v in res.items():
    print(rp.fmt_compare(k, rp.compare(champ, v)))
print("== Hanya 2022-skrg (periode yang punya data OI): 'lama' = 2022-2023")
for k, v in res.items():
    a, b = sub(champ), sub(v)
    sa, sb_ = rp.stats(a[a.year <= 2023]), rp.stats(b[b.year <= 2023])
    print(f"{k}: 2022-2023 rasio {sa['rasio']:.1f} -> {sb_['rasio']:.1f} ({(sb_['rasio']/sa['rasio']-1)*100:+.0f}%), "
          f"R {sa['tot']:.1f} -> {sb_['tot']:.1f}, DD {sa['dd']:.1f} -> {sb_['dd']:.1f}, tanpa top2% {sa['tahan']:.1f} -> {sb_['tahan']:.1f}")
for k, v in res.items():
    c = rp.compare(champ, v)
    print(k, "rasio per tahun:", {y: (round(a["rasio"], 1), round(b["rasio"], 1)) for y, (a, b) in c["yr"].items()},
          "trade:", {y: (a["n"], b["n"]) for y, (a, b) in c["yr"].items()})
best = max(res, key=lambda k: rp.compare(champ, res[k])["d_new"])
res[best].to_csv(f"{data_dir}/ide04_best.csv", index=False)
champ.to_csv(f"{data_dir}/champ_replay.csv", index=False)
print("varian terbaik (Δ baru):", best)
