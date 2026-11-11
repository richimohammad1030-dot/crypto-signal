"""VONIS APA ADANYA di data KONFIRMASI Nov 2017 - Nov 2019 (11 Nov 2026; padanan "Langkah 1" XAU 2004-2014).
Bot live v2 tanpa perubahan parameter, daftar koin SESUAI MASANYA (snapshot CMC bulanan, logika riset/pit.py), mesin asli.
Funding futures belum ada sebelum Sep 2019 → aturan bot (SELL hanya bila funding > 0) = tanpa SELL. Varian B: funding tidak
diketahui dianggap > 0 (SELL diizinkan) untuk melihat sisi SELL. Biaya REAL; funding long sebelum ada arsip = proksi 0,01%/8 jam.
Data dari eksperimen/unduh_lama.py (BCC=Bitconnect & VEN=VET duplikat dibuang). Periode konfirmasi = trade tutup < 1 Des 2019.
DATA INI BOLEH DIPAKAI SEKALI PER IDE SEBAGAI KONFIRMASI, DILARANG UNTUK MEMILIH PARAMETER.
Pemakaian: python tahap0_lama.py <repo> <data_lama>"""
import json, os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tahap0_semua_tahun as t0
rp = t0.rp; REPO, DATA = t0.REPO, t0.DATA_DIR
sys.path.insert(0, REPO); sys.path.insert(0, os.path.join(REPO, "riset"))
import signal_bot as sb, pit
rp.sb = sb
pit._load(DATA)
AKHIR = pd.Timestamp("2019-12-01").timestamp()
now = time.time() * 1000
for fn in os.listdir(f"{DATA}/klines"):
    c = fn[:-5]
    rows = [r[:5] for r in json.load(open(f"{DATA}/klines/{fn}")) if r[5] < now]
    if len(rows) < sb.K + 1350: continue
    rp.DATA[c] = sb.prep(rows)
    f = json.load(open(f"{DATA}/funding/{c}.json")) if os.path.exists(f"{DATA}/funding/{c}.json") else []
    h = json.load(open(f"{DATA}/funding_hl/{c}.json")) if os.path.exists(f"{DATA}/funding_hl/{c}.json") else []
    rp.FUND[c] = ([x[0] for x in f], [x[1] for x in f]); rp.FUND_HL[c] = ([x[0] for x in h], [x[1] for x in h])
first = {c: int(d["T"][sb.K + 1300]) for c, d in rp.DATA.items()}
uni = pit.universe_fn(DATA, lambda c, t: c in first and first[c] <= t)


class PitEngine(sb.Engine):             # salinan riset/pit.py, berhenti di AKHIR
    def run(self, data_, since_ts, univ=None):
        times = sorted({t for d in data_.values() for t in d["T"] if since_ts < t < AKHIR + 120 * 86400})
        idx = {c: {t: i for i, t in enumerate(d["T"])} for c, d in data_.items()}
        for t in times:
            U = univ(t); order = U + [c for c in data_ if c not in U]
            for coin in order:
                if t in idx[coin]:
                    i = idx[coin][t]
                    if i >= max(sb.K, 1300): self.step_fill_exit(coin, i, data_[coin])
            if (t // 3600) % 24 in sb.CHECK_HOURS_UTC:
                for coin in order:
                    if t not in idx[coin]: continue
                    i = idx[coin][t]
                    if i < max(sb.K, 1300): continue
                    cs = self.s["coins"].setdefault(coin, {"pend": None, "pos": None})
                    if coin not in U and not cs.get("pos"):
                        if cs.get("pend"): cs["pend"] = None
                        continue
                    allow = lambda c, old: self.slots_used() - (1 if self.s["coins"][c].get("pend") else 0) < sb.MAX_SLOTS
                    self.step_check(coin, i, data_[coin], allow)


def jalan(fund_fn, univ, coins=None):
    cur, rows = {}, []
    def notify(kind, coin, **k):
        if kind == "fill":
            cur[coin] = dict(coin=coin, d=k["d"], t_fill=k["t"], e=k["entry"], r0=k["r0"], sl0=k["sl"], t_part=None, px_part=None)
        elif kind == "partial": cur[coin].update(t_part=k["t"], px_part=k["px"])
        elif kind == "exit":
            x = cur.pop(coin); x.update(t_exit=k["t"], ex=k["exit"], why=k["why"], R=k["R"]); rows.append(x)
    eng = PitEngine({"coins": {}, "last_ts": 0, "replay": True}, fund_fn, notify)
    eng.run({c: rp.DATA[c] for c in (coins or rp.DATA)}, 0, univ)
    df = t0.add_costs(pd.DataFrame(rows))
    # proksi funding long sebelum arsip ada: 0,01% per 8 jam (posisi long bayar)
    f0 = {c: (rp.FUND[c][0][0] if rp.FUND[c][0] else 1e18) for c in df.coin.unique()}
    hold8 = (np.minimum(df.t_exit, df.coin.map(f0)) - df.t_fill).clip(lower=0) / 28800
    prox = df.d * 0.0001 * hold8 * df.e / df.r0
    for k in ("REAL", "KONS"): df[f"R_{k}"] -= prox
    return df[df.t_exit < AKHIR]


fund_b = lambda c, t: (lambda f: 1e-4 if f is None else f)(rp.funding_fn(c, t))
fixed = lambda t: [c for c in sb.COINS if c in rp.DATA]
VAR = {"A: aturan bot (tanpa SELL sblm funding ada), sesuai masanya": (rp.funding_fn, uni, None),
       "B: SELL diizinkan bila funding tak diketahui, sesuai masanya": (fund_b, uni, None),
       "C: aturan bot, daftar bot SEKARANG (bias koin selamat)": (rp.funding_fn, fixed, [c for c in sb.COINS if c in rp.DATA])}
pd.set_option("display.width", 200)
for nm, (ff, un, coins) in VAR.items():
    df = jalan(ff, un, coins)
    df.to_csv(f"{DATA}/lama_{nm[0]}.csv", index=False)
    print(f"\n######## {nm}: trade {len(df)} · koin {df.coin.nunique()} · bersih {df.R_REAL.sum():+.1f}R (kotor {df.R_KOTOR.sum():+.1f}, KONS {df.R_KONS.sum():+.1f}) · "
          f"DD {t0.maxdd(df.R_REAL.values):.1f}R · R/trade {df.R_REAL.mean():+.3f} · win {(df.R_REAL > 0).mean() * 100:.0f}%")
    t = t0.year_table(df, "R_REAL")
    print(t.round(2).to_string())
    df["arah"] = np.where(df.d == 1, "BUY", "SELL")
    print(df.groupby(["year", "arah"]).R_REAL.agg(["count", "sum", "mean"]).round(2).to_string())
    s = df.groupby("coin").R_REAL.sum().sort_values()
    print("koin terburuk:", s.head(5).round(1).to_dict(), "· terbaik:", s.tail(5).round(1).to_dict())
    m = df.groupby(pd.to_datetime(df.t_exit, unit="s").dt.to_period("Q")).R_REAL.sum()
    print("per kuartal:", {str(k): round(v, 1) for k, v in m.items()})
