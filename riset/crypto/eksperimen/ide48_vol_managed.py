"""Ide #48 [lit] · Risiko dikelola volatilitas pasar (Moreira & Muir 2017, "Volatility-Managed Portfolios", J. Finance 72(4)).
Hipotesis: saat volatilitas BTC 30 hari tinggi dibanding biasanya, hasil per risiko (R) strategi tidak naik sebanding,
sedangkan risiko gabungan (banyak posisi berkorelasi) naik. Mengecilkan risiko per trade saat volatilitas tinggi
(dan membesarkan saat tenang) memperbaiki rasio R/DD.
Hanya ukuran risiko yang berubah, slot/urutan tidak berubah -> cukup skala R trade replay juara (bukan filter).
Volatilitas diukur dari candle H1 BTC SEBELUM jam fill (tanpa melihat masa depan); patokan = median 365 hari terakhir.
Bobot dinormalkan ke rata-rata 1 agar total R sebanding (rasio R/DD tidak terpengaruh normalisasi).
Argumen: <repo> <data_dir>."""
import bisect
import numpy as np, pandas as pd
from _common import setup
rp, champ, data_dir = setup()

B = rp.DATA["BTC"]
T = np.asarray(B["T"], float); C = np.asarray(B["C"], float)
lr = np.diff(np.log(C), prepend=np.log(C[0]))
s = pd.Series(lr)
vol30 = s.rolling(720, min_periods=600).std().values            # vol 30 hari (H1)
ref = pd.Series(vol30).rolling(8760, min_periods=2000).median().values   # median 365 hari


def vol_at(t):
    j = bisect.bisect_right(T, t) - 2           # candle terakhir yang sudah TUTUP sebelum jam t
    return (vol30[j], ref[j]) if j >= 0 else (np.nan, np.nan)


v = np.array([vol_at(t) for t in champ.t0])
champ = champ.assign(vol=v[:, 0], ref=v[:, 1])
champ["rel"] = champ.vol / champ.ref
print("trade tanpa data vol (bobot 1):", int(champ.rel.isna().sum()))

# hubungan vol relatif vs hasil (diagnostik)
champ["kv"] = pd.qcut(champ.rel, 4, labels=["Q1 tenang", "Q2", "Q3", "Q4 bergejolak"])
champ["per"] = np.where(champ.year >= 2024, "2024-skrg", "2020-2023")
print(champ.groupby(["per", "kv"], observed=True).R.agg(["count", "mean", "sum"]).round(3).to_string())


def weighted(w):
    w = np.where(np.isnan(w), 1.0, w)
    w = w / w.mean()
    return champ.assign(R=champ.R * w)


rel = champ.rel.values
VAR = {
    "A: 1/vol, batas 0,5-1,5": np.clip(1 / rel, 0.5, 1.5),
    "B: 1/vol², batas 0,5-1,5": np.clip(1 / rel ** 2, 0.5, 1.5),
    "C: vol > 1,25x median -> 0,5": np.where(rel > 1.25, 0.5, 1.0),
    "D: 1/vol, batas 0,25-2": np.clip(1 / rel, 0.25, 2.0),
}
print(rp.HEADER)
print(rp.fmt_compare("Juara", rp.compare(champ, champ)))
res = {}
for k, w in VAR.items():
    var = weighted(w)
    c = rp.compare(champ, var); res[k] = (c, var)
    print(rp.fmt_compare(k, c))
for k, (c, var) in res.items():
    print(k, "rasio per tahun:", {y: (round(a["rasio"], 1), round(b["rasio"], 1)) for y, (a, b) in c["yr"].items()})
best = max(res, key=lambda k: min(res[k][0]["d_old"], res[k][0]["d_new"]))
res[best][1].to_csv(f"{data_dir}/ide48_best.csv", index=False)
champ.to_csv(f"{data_dir}/champ_replay.csv", index=False)
print("varian terbaik (min Δ lama/baru):", best)
