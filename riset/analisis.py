"""Analisis bulanan (bagian angka Lapis 3) + pembuat patokan Lapis 2.

Masukan : hasil backtest crypto & XAU (CSV dari backtest_crypto.py / backtest_xau.py), state & jurnal bot.
Keluaran: baseline.json        - patokan rentang normal untuk cek kesehatan (dipakai bot)
          riset/laporan/angka-YYYY-MM.md  - laporan lengkap
          riset/laporan/angka-YYYY-MM.txt - ringkasan untuk Telegram (HTML)
Pemakaian: python analisis.py <repo_dir> <crypto_trades.csv> <xau_trades.csv> [YYYY-MM]
"""
import datetime as dt, json, os, sys, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")

REPO, CRYPTO_CSV, XAU_CSV = sys.argv[1:4]
sys.path.insert(0, REPO); sys.path.insert(0, os.path.join(REPO, "riset"))
import signal_bot as sb
WIB = dt.timezone(dt.timedelta(hours=7))
NOW = dt.datetime.now(WIB)
PERIODE = sys.argv[4] if len(sys.argv) > 4 else (NOW.replace(day=1) - dt.timedelta(days=1)).strftime("%Y-%m")
LIVE_START = {"crypto": dt.datetime(2026, 10, 24, tzinfo=WIB).timestamp(), "xau": dt.datetime(2026, 10, 18, tzinfo=WIB).timestamp()}
GRID = [5, 10, 15, 20, 30, 40, 50, 75, 100, 150, 200, 300, 500]
rng = np.random.default_rng(42)


def stats(R):
    R = np.asarray(R, float)
    if len(R) == 0:
        return dict(n=0)
    w, l = R[R > 0].sum(), -R[R < 0].sum()
    c = np.cumsum(R)
    dd = float((np.maximum.accumulate(np.concatenate([[0], c]))[1:] - c).max())
    s = best = 0
    for r in R:
        s = s + 1 if r <= 0 else 0; best = max(best, s)
    return dict(n=int(len(R)), wr=float((R > 0).mean() * 100), avgR=float(R.mean()), totR=float(R.sum()),
                pf=float(w / l) if l else None, maxdd=dd, streak=int(best))


def bands(R, sims=5000):
    """Rentang normal (hasil kumulatif, win rate, drawdown, loss beruntun) untuk N trade, dari simulasi ulang urutan trade."""
    R = np.asarray(R, float); out = {}
    for n in GRID:
        x = rng.choice(R, size=(sims, n), replace=True)
        c = np.cumsum(x, axis=1)
        peak = np.maximum.accumulate(np.concatenate([np.zeros((sims, 1)), c], axis=1), axis=1)[:, 1:]
        dd = (peak - c).max(axis=1)
        loss = (x <= 0).astype(int)
        streak = np.zeros(sims, int); cur = np.zeros(sims, int)
        for j in range(n):
            cur = (cur + 1) * loss[:, j]; streak = np.maximum(streak, cur)
        p = lambda a, q: [round(float(v), 3) for v in np.percentile(a, q)]
        out[str(n)] = dict(cum=p(c[:, -1], [1, 5, 50, 95, 99]), wr=p((x > 0).mean(axis=1) * 100, [5, 95]),
                           dd=p(dd, [95, 99]), streak=p(streak, [95, 99]))
    return out


# ------------------------------------------------------------------ data backtest
cr = pd.read_csv(CRYPTO_CSV).sort_values("t1").reset_index(drop=True)
cr["year"] = pd.to_datetime(cr.t0, unit="s").dt.year
pts = lambda x, ab: np.where(x < ab[0], 1, np.where(x > ab[1], -1, 0))
cr["score"] = pts(cr.slpct, sb.CONV_SL) + pts(cr.ext, sb.CONV_EXT) + pts(cr["rank"], sb.CONV_RANK) + cr.btc
cr["label"] = np.where(cr.score >= 2, "HIGH", np.where(cr.score <= -1, "LOW", "MEDIUM"))
xa = pd.read_csv(XAU_CSV).sort_values("t1").reset_index(drop=True)
xa["year"] = pd.to_datetime(xa.t0, unit="s").dt.year

base = {"dibuat": NOW.strftime("%Y-%m-%d %H:%M WIB"), "catatan": "R kotor (tanpa biaya), sama seperti perhitungan bot"}
for bot, d in (("crypto", cr), ("xau", xa)):
    s = stats(d.R)
    base[bot] = dict(sumber=f"backtest {pd.to_datetime(d.t0.min(), unit='s'):%Y-%m} s.d. {pd.to_datetime(d.t1.max(), unit='s'):%Y-%m}",
                     **{k: (round(v, 3) if isinstance(v, float) else v) for k, v in s.items()}, band=bands(d.R))
base["crypto"]["label"] = {lab: {k: (round(v, 3) if isinstance(v, float) else v) for k, v in stats(g.R).items()}
                           for lab, g in cr.groupby("label")}
json.dump(base, open(os.path.join(REPO, "baseline.json"), "w"), indent=1)

# ------------------------------------------------------------------ data live (catatan bot)
def live(bot):
    f = os.path.join(REPO, "state.json" if bot == "crypto" else "gold_state.json")
    h = json.load(open(f)).get("hist", []) if os.path.exists(f) else []
    return pd.DataFrame(h, columns=["sym", "d", "t0", "t1", "e", "ex", "R"]) if h else pd.DataFrame(columns=["sym", "d", "t0", "t1", "e", "ex", "R"])

# ------------------------------------------------------------------ uji ML walk-forward
ml_txt, ml_table = "Uji ML dilewati.", ""
try:
    import ml_walkforward as mw
    if "slope" in cr and "breadth" in cr:
        _, agg = mw.walkforward(cr)
        best = agg.index[0]
        lab = agg.loc["Label 4 faktor (sekarang)"]
        ml_best = agg[~agg.index.str.startswith("Label")].iloc[0]
        menang = ml_best.selisih > lab.selisih and ml_best.tahun_high_menang >= lab.tahun_high_menang
        ml_txt = (f"Label sekarang: selisih HIGH-LOW {lab.selisih:+.2f}R ({int(lab.tahun_high_menang)}/{int(lab.tahun_uji)} tahun). "
                  f"ML terbaik ({ml_best.name}): {ml_best.selisih:+.2f}R ({int(ml_best.tahun_high_menang)}/{int(ml_best.tahun_uji)} tahun). "
                  + ("ML LEBIH BAIK - kandidat penantang, perlu review." if menang else "ML belum lebih baik dari label sekarang."))
        ml_table = "```\n" + agg.round(2).to_string() + "\n```"
except Exception as e:
    ml_txt = f"Uji ML gagal: {e}"; ml_table = ""

# ------------------------------------------------------------------ laporan
os.makedirs(os.path.join(REPO, "riset", "laporan"), exist_ok=True)
md = [f"# Laporan angka bulanan · {PERIODE}", f"Dibuat otomatis {NOW:%Y-%m-%d %H:%M} WIB.", ""]
tg = [f"<b>LAPORAN ANGKA BULANAN</b>", f"Periode {PERIODE}", "────────────────────"]
for bot, d in (("crypto", cr), ("xau", xa)):
    nama = "CRYPTO" if bot == "crypto" else "XAU"
    s = base[bot]
    lv = live(bot); lv_s = stats(lv.R) if len(lv) else dict(n=0)
    bt_same = d[d.t0 >= LIVE_START[bot]]; bt_s = stats(bt_same.R) if len(bt_same) else dict(n=0)
    yr = d.groupby("year").R.agg(["count", "mean", "sum"]).round(2)
    md += [f"## {nama}", f"Backtest {s['sumber']}: {s['n']} trade · win rate {s['wr']:.1f}% · rata-rata {s['avgR']:+.2f}R · "
           f"profit factor {s['pf']:.2f} · drawdown terburuk {s['maxdd']:.1f}R · loss beruntun terpanjang {s['streak']}", "",
           "Per tahun (jumlah trade, rata-rata R, total R):", "```", yr.to_string(), "```", ""]
    md += [f"Live sejak {dt.datetime.fromtimestamp(LIVE_START[bot], WIB):%d %b %Y}: {lv_s['n']} trade"
           + (f" · total {lv_s['totR']:+.2f}R · win rate {lv_s['wr']:.0f}%" if lv_s["n"] else ""),
           f"Backtest periode yang sama: {bt_s['n']} trade" + (f" · total {bt_s['totR']:+.2f}R" if bt_s["n"] else ""), ""]
    tg += ["", f"<b>{nama}</b>", "────────────────────",
           f"Live: {lv_s['n']} trade" + (f" · {lv_s['totR']:+.2f}R" if lv_s["n"] else ""),
           f"Backtest periode sama: {bt_s['n']} trade" + (f" · {bt_s['totR']:+.2f}R" if bt_s["n"] else ""),
           f"Backtest total: {s['n']} trade · {s['avgR']:+.2f}R/trade · DD terburuk {s['maxdd']:.1f}R"]
    if bot == "crypto":
        lab = cr.groupby("label").R.agg(["count", "mean"])
        recent = cr[cr.year >= NOW.year - 1].groupby("label").R.mean()
        ok = lab.loc["HIGH", "mean"] > lab.loc["MEDIUM", "mean"] > lab.loc["LOW", "mean"]
        ok_recent = recent.get("HIGH", 0) > recent.get("LOW", 0)
        md += ["Label conviction (seluruh backtest):", "```", lab.round(2).to_string(), "```",
               f"Urutan HIGH > MEDIUM > LOW: {'ya' if ok else 'TIDAK'} · HIGH > LOW di {NOW.year - 1}-{NOW.year}: {'ya' if ok_recent else 'TIDAK'}", "",
               "Uji ML walk-forward:", ml_txt, "", ml_table, ""]
        tg += [f"Label conviction: {'masih valid' if ok and ok_recent else 'PERLU DICEK'}", f"ML: {ml_txt.split('. ')[-1]}"]
open(os.path.join(REPO, "riset", "laporan", f"angka-{PERIODE}.md"), "w").write("\n".join(md) + "\n")
tg += ["", "Laporan lengkap: riset/laporan/angka-" + PERIODE + ".md"]
open(os.path.join(REPO, "riset", "laporan", f"angka-{PERIODE}.txt"), "w").write("\n".join(tg))
print("\n".join(tg))
