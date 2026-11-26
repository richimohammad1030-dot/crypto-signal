"""Analisis penyebab SL + KALAH BERUNTUN (T7) juara crypto swing · 27 Nov 2026 (ATURAN_BERSAMA G a-b, milestone T7).
Input: CSV trade juara dari tahap0_semua_tahun.py (daftar tetap, R_REAL). Urutan = waktu TUTUP (sama dengan inti.nilai).
Pertanyaan: runtun kalah panjang (>= 11) itu terbuat dari apa? (a) SL penuh vs rugi kecil (stagnan / trailing di bawah impas),
(b) banyak posisi tutup bersamaan (klaster hari pembalikan pasar) vs tersebar, (c) arah & BTC.
Pemakaian: python runtun_sl.py <csv>"""
import sys
import numpy as np, pandas as pd

df = pd.read_csv(sys.argv[1]).sort_values("t_exit").reset_index(drop=True)
df = df[df.year >= 2020].reset_index(drop=True)
r = df.R_REAL.values
kalah = r < 0
df["jenis"] = np.where(df.why.str.contains("stagnan"), "stagnan",
                       np.where(df.R_REAL <= -0.9, "SL penuh", np.where(df.R_REAL < 0, "rugi kecil (trail/SL < 0,9R)", "menang")))
print("== Komposisi trade 2020-skrg (R_REAL)")
print(df.groupby("jenis").R_REAL.agg(["count", "mean", "sum"]).round(3).to_string())
print(f"Kalah dengan part TP1 sudah terisi: {int(((df.R_REAL < 0) & df.px_part.notna()).sum())}")

# runtun
runs, cur = [], []
for k, v in enumerate(r):
    if v < 0: cur.append(k)
    else:
        if cur: runs.append(cur)
        cur = []
if cur: runs.append(cur)
L = np.array([len(x) for x in runs])
print(f"\n== Runtun kalah: total {len(runs)} · maks {L.max()} · >=11: {(L >= 11).sum()} · >=15: {(L >= 15).sum()}")
print("distribusi panjang:", {int(k): int(v) for k, v in zip(*np.unique(L, return_counts=True))})
print("\n== Runtun >= 11 (rincian)")
for x in [x for x in runs if len(x) >= 11]:
    g = df.loc[x]
    hari = pd.to_datetime(g.t_exit, unit="s").dt.floor("D")
    jam = (g.t_exit.max() - g.t_exit.min()) / 3600
    print(f"  {pd.to_datetime(g.t_exit.min(), unit='s'):%Y-%m-%d} n {len(g):2d} · {jam:5.0f} jam · hari unik {hari.nunique():2d} · "
          f"klaster terbesar/hari {hari.value_counts().max():2d} · BUY {int((g.d == 1).sum()):2d} SELL {int((g.d == -1).sum()):2d} · "
          f"SL penuh {int((g.jenis == 'SL penuh').sum()):2d} stagnan {int((g.jenis == 'stagnan').sum()):2d} kecil {int(g.jenis.str.startswith('rugi').sum()):2d} · "
          f"jumlah {g.R_REAL.sum():+.1f}R")

# klaster: berapa trade yang tutup rugi di hari yang sama dengan >= 3 trade rugi lain
hari = pd.to_datetime(df.t_exit, unit="s").dt.floor("D")
df["n_rugi_hari"] = df.assign(h=hari, k=kalah).groupby("h").k.transform("sum")
print("\n== Kalah per ukuran klaster harian (jumlah trade rugi tutup di hari yang sama)")
kk = df[kalah]
print(pd.cut(kk.n_rugi_hari, [0, 1, 2, 4, 7, 100], labels=["1", "2", "3-4", "5-7", "8+"]).value_counts().sort_index().to_string())

# runtun bila trade yang tutup di hari yang sama dihitung SATU (rata-rata R hari itu) → apakah T7 masalah klaster?
g = df.assign(h=hari).groupby("h").R_REAL.sum()
best = cur2 = 0
for v in g.values:
    cur2 = cur2 + 1 if v < 0 else 0; best = max(best, cur2)
print(f"\nRuntun 'hari rugi' beruntun maks (per hari tutup, jumlah R): {best}")

# rugi kecil: berapa runtun >= 11 yang tidak akan >= 11 bila rugi > -0,25R dihitung impas (tidak memutus, tidak menambah)
def runtun_maks(v, batas):
    best = cur = 0
    for x in v:
        if x < batas: cur += 1; best = max(best, cur)
        elif x > 0: cur = 0
    return best
for b in (0, -0.1, -0.25, -0.5):
    print(f"runtun maks bila hanya R < {b} = kalah (R di [{b},0] tidak menambah & tidak memutus): {runtun_maks(r, b)}")
# BTC searah / lawan untuk SL penuh (kolom btc dari backtest_crypto bila ada)
for y in sorted(df.year.unique()):
    s = df[df.year == y]
    print(f"{y}: SL penuh {int((s.jenis == 'SL penuh').sum())}/{len(s)} ({(s.jenis == 'SL penuh').mean() * 100:.0f}%) · rugi kecil "
          f"{int(s.jenis.str.startswith('rugi').sum())} · stagnan {int((s.jenis == 'stagnan').sum())} · runtun maks {runtun_maks(s.R_REAL.values, 0)}")
