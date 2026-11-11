"""EVALUASI bot crypto swing live (v2) seluruh data (pemilik, 11 Nov 2026). R bersih skenario REAL (tahap0_semua_tahun.py).
Isi: per periode / tahun / koin / arah: trade, trade/thn, win, RR (rata menang / rata kalah), PF, R/trade, R/thn, DD,
beruntun menang/kalah, % bulan positif; tahun minus; DD terdalam & lama pulih; porsi biaya terhadap edge; peluang tahun minus
dari rata & simpangan R tahunan (cara log XAU 10 Nov) dan dari R/trade (iid); ekuitas majemuk pada risiko 1%.
Pemakaian: python evaluasi_live.py <tahap0_trades.csv> [tahap0_pit_trades.csv]"""
import sys, math
import numpy as np, pandas as pd

df = pd.read_csv(sys.argv[1]); df = df[df.year >= 2020].sort_values("t_exit").reset_index(drop=True)
PIT = pd.read_csv(sys.argv[2]) if len(sys.argv) > 2 else None
C = "R_REAL"
T_END = df.t_exit.max(); T0 = pd.Timestamp("2020-01-01").timestamp()
Phi = lambda x: 0.5 * (1 + math.erf(x / math.sqrt(2)))


def streak(R, win=True):
    best = cur = 0
    for r in R:
        cur = cur + 1 if ((r > 0) == win) else 0
        best = max(best, cur)
    return best


def stat(g, yrs=None):
    g = g.sort_values("t_exit"); R = g[C].values
    if not len(R): return {}
    w, l = R[R > 0], R[R <= 0]
    c = np.cumsum(R); dd = float((np.maximum.accumulate(np.concatenate([[0], c]))[1:] - c).max())
    if yrs is None: yrs = max((g.t_exit.max() - g.t_fill.min()) / 31557600, 1e-9)
    mon = g.groupby(pd.to_datetime(g.t_exit, unit="s").dt.to_period("M"))[C].sum()
    return dict(n=len(R), n_thn=len(R) / yrs, win=len(w) / len(R) * 100, avg_w=w.mean() if len(w) else 0,
                avg_l=l.mean() if len(l) else 0, RR=(w.mean() / -l.mean()) if len(w) and len(l) and l.mean() < 0 else np.nan,
                PF=w.sum() / -l.sum() if l.sum() < 0 else np.inf, R_trade=R.mean(), R_thn=R.sum() / yrs, tot=R.sum(), DD=dd,
                maks_kalah=streak(R, False), maks_menang=streak(R, True), bulan_plus=(mon > 0).mean() * 100,
                kotor_trade=g.R_KOTOR.mean(), biaya_trade=(g.R_KOTOR - g[C]).mean())


def tabel(rows, title):
    t = pd.DataFrame(rows).T
    cols = ["n", "n_thn", "win", "RR", "PF", "R_trade", "R_thn", "tot", "DD", "maks_kalah", "maks_menang", "bulan_plus"]
    print(f"\n== {title} ==\n" + t[[c for c in cols if c in t]].astype(float).round(2).to_string())
    return t


yrs_all = (T_END - T0) / 31557600
per = {"2020-2023": (df[df.year <= 2023], 4.0), "2024-skrg": (df[df.year >= 2024], (T_END - pd.Timestamp("2024-01-01").timestamp()) / 31557600),
       "Semua": (df, yrs_all)}
tabel({k: stat(g, y) for k, (g, y) in per.items()}, "PER PERIODE (R bersih REAL)")
ty = tabel({y: stat(g, 1.0 if y < 2026 else (T_END - pd.Timestamp('2026-01-01').timestamp()) / 31557600) for y, g in df.groupby("year")},
           "PER TAHUN (tahun tutup; 2026 = s.d. data terakhir, R_thn disetahunkan)")
print("tahun minus:", [y for y, g in df.groupby("year") if g[C].sum() < 0] or "tidak ada")
df["arah"] = np.where(df.d == 1, "BUY", "SELL")
tabel({a: stat(g, yrs_all) for a, g in df.groupby("arah")}, "PER ARAH")
tabel({(y, a): stat(g, 1.0) for (y, a), g in df.groupby(["year", "arah"])}, "PER TAHUN x ARAH")
kc = {k: stat(g, yrs_all) for k, g in df.groupby("coin")}
kt = pd.DataFrame(kc).T.sort_values("tot")
print(f"\n== PER KOIN ({len(kt)} koin; positif {(kt.tot > 0).sum()}) — 10 terburuk & 10 terbaik ==")
cols = ["n", "win", "RR", "PF", "R_trade", "tot"]
print(kt[cols].astype(float).head(10).round(2).to_string()); print(kt[cols].astype(float).tail(10).round(2).to_string())

# DD terdalam & lama pulih (kurva R kumulatif menurut waktu tutup)
c = df[C].cumsum().values; t = df.t_exit.values
peak = np.maximum.accumulate(np.concatenate([[0], c]))[1:]; dd = peak - c
i_tr = int(dd.argmax()); i_pk = int(np.flatnonzero(c[:i_tr + 1] >= peak[i_tr] - 1e-9)[0]) if (c[:i_tr + 1] >= peak[i_tr] - 1e-9).any() else 0
rec = np.flatnonzero(c[i_tr:] >= peak[i_tr] - 1e-9)
d = lambda s: pd.to_datetime(s, unit="s").strftime("%d %b %Y")
print(f"\n== DRAWDOWN ==\nDD terdalam {dd[i_tr]:.1f}R: puncak {d(t[i_pk])} → dasar {d(t[i_tr])} ({(t[i_tr]-t[i_pk])/86400:.0f} hari) → "
      + (f"pulih {d(t[i_tr + rec[0]])} ({(t[i_tr + rec[0]] - t[i_tr]) / 86400:.0f} hari dari dasar, {(t[i_tr + rec[0]] - t[i_pk]) / 86400:.0f} hari total)" if len(rec) else "BELUM pulih"))
uw, start, best = 0, None, (0, None, None)
for k in range(len(c)):
    if c[k] >= peak[k] - 1e-9: start = t[k]
    elif start is not None and t[k] - start > best[0]: best = (t[k] - start, start, t[k])
print(f"periode di bawah puncak terlama: {best[0]/86400:.0f} hari ({d(best[1])} → {d(best[2])})")
top5 = []
k = 0
while k < len(c):
    if dd[k] > 0:
        j = k
        while j < len(c) and dd[j] > 0: j += 1
        top5.append((dd[k:j].max(), t[k], t[j] if j < len(c) else None)); k = j
    else: k += 1
print("5 DD terbesar:", "; ".join(f"{x:.1f}R {d(a)}→{d(b) if b else 'belum'}" for x, a, b in sorted(top5, key=lambda z: -z[0])[:5]))

# biaya vs edge
g, n = df.R_KOTOR.mean(), df[C].mean()
print(f"\n== BIAYA ==\nR kotor/trade {g:+.3f} · biaya {g - n:.3f} (fee {(df.fee_REAL).mean():.3f} + funding {df.fund_R.mean():+.3f}) · "
      f"bersih {n:+.3f} → biaya = {(g - n) / g * 100:.0f}% edge kotor. KONS: bersih {df.R_KONS.mean():+.3f} ({(g - df.R_KONS.mean()) / g * 100:.0f}%).")
for y, gg in df.groupby("year"):
    print(f"  {y}: kotor {gg.R_KOTOR.mean():+.3f} biaya {(gg.R_KOTOR - gg[C]).mean():.3f} → {(gg.R_KOTOR - gg[C]).sum() / max(gg.R_KOTOR.sum(), 1e-9) * 100:.0f}% edge tahun itu")

# peluang tahun minus
full = df[(df.year >= 2020) & (df.year <= 2025)].groupby("year")[C].sum()
m_, s_ = full.mean(), full.std(ddof=1)
nt = df[(df.year <= 2025)].groupby("year").size().mean(); mr, sr = df[C].mean(), df[C].std(ddof=1)
print(f"\n== PELUANG TAHUN MINUS ==\nR tahunan 2020-2025: rata {m_:+.1f}R, simpangan {s_:.1f}R → P(minus) = Φ(-{m_:.1f}/{s_:.1f}) = {Phi(-m_ / s_) * 100:.1f}%"
      f" ≈ {Phi(-m_ / s_) * 10:.2f} dari 10 tahun")
print(f"R/trade {mr:+.3f} × {nt:.0f} trade/thn, sd/trade {sr:.2f} (iid): rata {mr * nt:+.1f}, sd {sr * math.sqrt(nt):.1f} → P = {Phi(-mr * nt / (sr * math.sqrt(nt))) * 100:.2f}%")
print(f"Agar P(minus) ≤ 5% dgn simpangan tahunan sekarang butuh rata ≥ {1.645 * s_:.0f}R/thn (sekarang {m_:.0f}).")
if PIT is not None:
    PIT = PIT[PIT.year >= 2020]
    fp = PIT[PIT.year <= 2025].groupby("year")[C].sum()
    print(f"Daftar sesuai masanya: rata {fp.mean():+.1f}, sd {fp.std(ddof=1):.1f} → P(minus) {Phi(-fp.mean() / fp.std(ddof=1)) * 100:.1f}%")

# ekuitas majemuk 1%
eq = np.cumprod(1 + 0.01 * df[C].values); pk = np.maximum.accumulate(eq)
print(f"\n== EKUITAS (risiko 1%/trade, majemuk saat tutup; posisi paralel diabaikan) ==\nCAGR {(eq[-1] ** (1 / yrs_all) - 1) * 100:.0f}% · MaxDD {((pk - eq) / pk).max() * 100:.1f}%")
