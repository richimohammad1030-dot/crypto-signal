"""Bedah celah juara (program TAMBAL-CELAH, 6 Nov 2026). Memakai CSV dari tahap0_semua_tahun.py (R bersih skenario REAL).
Tabel: per tahun x arah, x label conviction, x alasan keluar, x rezim BTC, x volatilitas BTC; koin penopang / perusak
per tahun; bulan terburuk; tahun tanpa 2% trade terbaik. Argumen: <repo> <data_dir> [csv]."""
import bisect, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _replay as rp

REPO, DATA_DIR = sys.argv[1], sys.argv[2]
CSV = sys.argv[3] if len(sys.argv) > 3 else f"{DATA_DIR}/tahap0_trades.csv"
rp.load(REPO, DATA_DIR)
sb = rp.sb
df = pd.read_csv(CSV)
df = df[df.year >= 2020].copy()
COL = "R_REAL"

B = rp.DATA["BTC"]; BT = np.asarray(B["T"], float); BC = np.asarray(B["C"], float)
lr = np.diff(np.log(BC), prepend=np.log(BC[0]))
vol30 = pd.Series(lr).rolling(720, min_periods=600).std().values * np.sqrt(24 * 365) * 100


def at(t):
    return bisect.bisect_right(BT, t) - 2      # candle BTC terakhir yang sudah tutup


lab, breg, bvol, bret = [], [], [], []
for x in df.itertuples():
    tc = (int(x.t_fill) // 14400) * 14400 - 3600          # perkiraan candle cek terakhir sebelum fill
    lab.append(sb.conviction(rp.DATA, x.coin, tc, x.d, x.e, x.sl0) or "NA")
    j = at(x.t_fill)
    breg.append(rp.REG["BTC"][j] * x.d)
    bvol.append(vol30[j])
    bret.append((BC[j] / BC[j - 24 * 90] - 1) * 100 * x.d if j >= 2160 else np.nan)
df["label"], df["btc"], df["bvol"], df["bret90"] = lab, breg, bvol, bret
df["arah"] = np.where(df.d == 1, "BUY", "SELL")
df["keluar"] = np.where(df.why.str.contains("stagnan"), "stagnan", np.where(df.R_KOTOR > 0, "trail untung", "SL/rugi"))
df["mon"] = pd.to_datetime(df.t_exit, unit="s").dt.to_period("M")
pd.set_option("display.width", 220)


def piv(col, name):
    t = df.pivot_table(index="year", columns=col, values=COL, aggfunc=["count", "sum", "mean"]).round(2)
    print(f"\n== per tahun x {name} (R bersih REAL) ==\n{t.to_string()}")


piv("arah", "arah"); piv("label", "label"); piv("keluar", "alasan keluar"); piv("btc", "rezim BTC searah(+1)/lawan(-1)")
df["vq"] = pd.cut(df.bvol, [0, 40, 55, 75, 500], labels=["<40", "40-55", "55-75", ">75"])
piv("vq", "vol BTC 30h tahunan %")
df["mq"] = pd.cut(df.bret90, [-999, -20, 0, 20, 50, 9999], labels=["<-20", "-20..0", "0..20", "20..50", ">50"])
piv("mq", "return BTC 90h searah posisi %")

print("\n== koin per tahun: 3 penopang & 3 perusak (R bersih) ==")
for y, g in df.groupby("year"):
    s = g.groupby("coin")[COL].sum().sort_values()
    tot = g[COL].sum()
    print(f"{y} total {tot:+.1f} · penopang: " + ", ".join(f"{c} {v:+.1f}" for c, v in s[::-1][:3].items()) +
          " · perusak: " + ", ".join(f"{c} {v:+.1f}" for c, v in s[:3].items()) +
          f" · tanpa koin terbaik {tot - s.iloc[-1]:+.1f}")
s = df.groupby("coin")[COL].agg(["count", "sum", "mean"]).sort_values("sum")
print("\n== koin seluruh periode (terburuk / terbaik) ==\n", s.head(8).round(2).to_string(), "\n", s.tail(8).round(2).to_string())

m = df.groupby("mon")[COL].sum()
print("\n== 12 bulan terburuk ==\n", m.sort_values().head(12).round(1).to_string())
print("\n== bulanan 2025 ==\n", m[m.index.year == 2025].round(1).to_string())
print("\n== bulanan 2026 ==\n", m[m.index.year == 2026].round(1).to_string())

print("\n== 2% trade terbaik per tahun (berapa R yang ditopang) ==")
for y, g in df.groupby("year"):
    k = max(1, int(round(len(g) * 0.02)))
    top = g.nlargest(k, COL)
    print(f"{y}: {k} trade = {top[COL].sum():+.1f}R dari {g[COL].sum():+.1f}R · " +
          ", ".join(f"{r.coin}{'+' if r.d == 1 else '-'} {r.R_REAL:+.1f}" for r in top.itertuples()))
df.to_csv(f"{DATA_DIR}/celah_trades.csv", index=False)
