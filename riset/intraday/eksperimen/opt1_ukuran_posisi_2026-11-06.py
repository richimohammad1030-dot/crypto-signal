"""PROGRAM OPTIMASI putaran 1 (6 Nov 2026) · jalur UKURAN POSISI. Trade juara v3 TIDAK berubah (slot, order, isi sama),
hanya bobot risiko per trade -> boleh dihitung dari CSV trade (tahap0) tanpa replay ulang.
Bobot dinormalisasi agar rata-rata bobot 2020-2023 = 1 (risiko rata-rata sama dengan juara 1%).
Ide:
  I-08  risiko berbeda per modul (A-long / B-long / B-short), dipilih di 2020-2023.
  I-24  [lit] volatility-managed (Moreira & Muir 2017, J. Finance 72(4)): bobot = (median 365 hari σ30 BTC / σ30 BTC saat ini),
        dibatasi [lo, hi]. Kritik: Cederburg, O'Doherty, Wang & Yan (2020, JFE 138(1)) -> wajib uji di luar sampel.
  I-25  [lit] bobot menurut dispersi return 24 jam antar koin 25 besar (Jegadeesh, Luo, Subrahmanyam & Titman 2025, RFS:
        reversal lebih besar saat noise trading lebih volatil): bobot = (dispersi / median 365 hari)^k, dibatasi [lo, hi].
Semua indikator kausal (hanya data sebelum waktu sinyal).
Pemakaian: python riset/intraday/eksperimen/opt1_ukuran_posisi_2026-11-06.py <repo> <data> <dir_tahap0>"""
import bisect, collections, csv, json, os, sys, time
REPO, DATA, DIR = sys.argv[1:4]
sys.path.insert(0, REPO); sys.path.insert(0, os.path.join(REPO, "riset"))
import numpy as np
import backtest_intraday as bi, pit, signifikansi as sg

IS_END = bi.IS_END
def load(nm):
    return [dict(r, t=int(r["t"]), t_exit=int(r["t_exit"]), d=int(r["d"]), R=float(r["R"])) for r in csv.DictReader(open(f"{DIR}/{nm}"))]
SETS = {k: load(f"trades_{k}.csv") for k in ("pit_std", "pit_stres", "tetap_std")}
for v in SETS.values():
    for o in v: o["g"] = "A" if o["m"] == "A" else ("Bl" if o["d"] == 1 else "Bs")

# ------------------------------------------------------------------ indikator kausal
pit._load(DATA)
def h1(c):
    r = bi.jload(f"{DATA}/klines/{c}.json"); a = np.array([x[:5] for x in r], float)
    return a[:, 0].astype(np.int64), a[:, 4]
BT, BC = h1("BTC")
lr = np.diff(np.log(BC), prepend=np.log(BC[0])); cs, cs2 = np.cumsum(lr), np.cumsum(lr ** 2)
def sig30(k):
    a = max(1, k - 720); n = k - a
    m = (cs[k] - cs[a]) / n; return np.sqrt(max((cs2[k] - cs2[a]) / n - m * m, 1e-12)) * np.sqrt(8766)
def kidx(t): return bisect.bisect_right(BT, t - 3600) - 1           # candle H1 terakhir yang sudah close
CT = {}
def ret24(c, t):
    if c not in CT:
        try: CT[c] = h1(c)
        except Exception: CT[c] = (np.array([], np.int64), np.array([]))
    T, C = CT[c]; k = bisect.bisect_right(T, t - 3600) - 1
    return C[k] / C[k - 24] - 1 if k >= 24 and T[k] > t - 3 * 3600 else None
def disp(t):
    u = pit.ranked(DATA, time.strftime("%Y-%m", time.gmtime(t)))[:25]
    r = [x for x in (ret24(c, t) for c in u) if x is not None]
    return float(np.std(r)) if len(r) >= 8 else np.nan
# seri harian (00:00 UTC) untuk median 365 hari ke belakang
days = np.arange(BT[0] // 86400 * 86400 + 86400 * 40, BT[-1], 86400)
VOLD = np.array([sig30(kidx(int(d))) for d in days])
DISD = np.array([disp(int(d)) for d in days])
def rel(series, t, x):
    j = bisect.bisect_right(days, t); a = series[max(0, j - 365):j]; a = a[~np.isnan(a)]
    return x / np.median(a) if len(a) >= 60 and x == x else 1.0
CACHE = {}
for v in SETS.values():
    for o in v:
        key = o["t"]
        if key not in CACHE:
            CACHE[key] = (rel(VOLD, key, sig30(kidx(key))), rel(DISD, key, disp(key)))
        o["vrel"], o["drel"] = CACHE[key]

# ------------------------------------------------------------------ evaluasi
YEARS = list(range(2020, 2027))
def evaluasi(tr, wf):
    w = np.array([wf(o) for o in tr]); isw = np.array([o["t"] < IS_END for o in tr])
    w = w / w[isw].mean()
    X = [dict(o, R=o["R"] * wi) for o, wi in zip(tr, w)]
    s = dict(semua=bi.stats(X), lama=bi.stats(X, b=IS_END), baru=bi.stats(X, a=IS_END))
    yr = collections.defaultdict(list)
    for o in X: yr[time.gmtime(o["t"]).tm_year].append(o["R"])
    s["tahun"] = {y: round(sum(yr[y]), 1) for y in YEARS}
    s["tahun_t2"] = {y: round(float(np.sort(yr[y])[::-1][max(1, len(yr[y]) // 50):].sum()), 1) for y in YEARS}
    eq, pk, dd, e24 = 1.0, 1.0, 0.0, None
    for o in sorted(X, key=lambda o: o["t_exit"]):
        if e24 is None and o["t"] >= IS_END: e24 = eq
        eq *= 1 + 0.01 * o["R"]; pk = max(pk, eq); dd = max(dd, 1 - eq / pk)
    yrs = (X[-1]["t_exit"] - X[0]["t"]) / 31557600; yrs24 = (X[-1]["t_exit"] - IS_END) / 31557600
    s["cagr"], s["cagr24"], s["ddp"] = round((eq ** (1 / yrs) - 1) * 100, 1), round(((eq / e24) ** (1 / yrs24) - 1) * 100, 1), round(dd * 100, 1)
    s["wmin"], s["wmax"] = round(float(w.min()), 2), round(float(w.max()), 2)
    return s, X

BASE = {k: evaluasi(v, lambda o: 1.0) for k, v in SETS.items()}
HASIL = {}
def uji(nama, wf, cetak=True):
    r = {}
    for k, tr in SETS.items():
        s, X = evaluasi(tr, wf)
        b, bX = BASE[k]
        if k == "pit_std":
            s["P"] = sg.banding([(o["t_exit"], o["R"]) for o in bX], [(o["t_exit"], o["R"]) for o in X], mulai=IS_END)["P_rasio_lebih_baik"]
            s["dL"] = round((s["lama"]["rasio"] / b["lama"]["rasio"] - 1) * 100, 1); s["dB"] = round((s["baru"]["rasio"] / b["baru"]["rasio"] - 1) * 100, 1)
            s["dDD"] = round((s["semua"]["maxDD"] / b["semua"]["maxDD"] - 1) * 100, 1)
        r[k] = s
    p, st, tt = r["pit_std"], r["pit_stres"], r["tetap_std"]
    minus = [y for y in YEARS if p["tahun"][y] <= 0]; minus2 = [y for y in YEARS if p["tahun_t2"][y] <= 0]
    worst, worst_st = min(p["tahun"].values()), min(st["tahun"].values())
    ok = (not minus and not minus2 and p["dL"] >= 10 and p["dB"] >= 10 and p["dDD"] <= 25 and p["P"] >= 0.90
          and worst_st >= min(BASE["pit_stres"][0]["tahun"].values()))
    r["lolos"] = ok
    if cetak:
        print(f"{nama:<30} rasio L {p['lama']['rasio']:5.2f} ({p['dL']:+5.1f}%) B {p['baru']['rasio']:5.2f} ({p['dB']:+5.1f}%) DD {p['semua']['maxDD']:5.1f}R ({p['dDD']:+5.1f}%) "
              f"DD% {p['ddp']:5.1f} CAGR {p['cagr']:5.1f}/{p['cagr24']:5.1f} P {p['P']:.2f} | thn " + " ".join(f"{p['tahun'][y]:+.0f}" for y in YEARS) +
              f" | -2% " + " ".join(f"{p['tahun_t2'][y]:+.0f}" for y in YEARS) + f" | stres terburuk {worst_st:+.1f} | tetap rasio B {tt['baru']['rasio']:.2f}"
              f" | w {p['wmin']}-{p['wmax']} {'LOLOS' if ok else 'gagal'}", flush=True)
    HASIL[nama] = r
    return r

if __name__ == "__main__":
    b = BASE["pit_std"][0]
    print(f"JUARA  rasio L {b['lama']['rasio']} B {b['baru']['rasio']} DD {b['semua']['maxDD']} DD% {b['ddp']} CAGR {b['cagr']}/{b['cagr24']} "
          f"thn {b['tahun']} | stres terburuk {min(BASE['pit_stres'][0]['tahun'].values())} | tetap rasio B {BASE['tetap_std'][0]['baru']['rasio']}")
    print("\n-- I-08 risiko per modul (A / B-long / B-short); pemilihan di 2020-2023 --")
    grid = {}
    for a in (0.5, 0.75, 1.0, 1.25, 1.5):
        for bl in (0.75, 1.0, 1.25):
            for bs in (0.5, 0.75, 1.0, 1.25):
                W = dict(A=a, Bl=bl, Bs=bs)
                grid[(a, bl, bs)] = uji(f"I08 A{a} Bl{bl} Bs{bs}", lambda o, W=W: W[o["g"]], cetak=False)
    top = sorted(grid, key=lambda k: -grid[k]["pit_std"]["lama"]["rasio"])[:6]
    print("6 terbaik menurut 2020-2023 (rasio L), dicetak penuh:")
    for k in top: uji(f"I08 A{k[0]} Bl{k[1]} Bs{k[2]}", lambda o, W=dict(A=k[0], Bl=k[1], Bs=k[2]): W[o["g"]])
    print("tetangga dasar:")
    for k in ((1.0, 1.0, 0.75), (1.0, 1.0, 0.5), (1.25, 1.0, 1.0), (1.5, 1.0, 1.0), (0.75, 1.0, 1.0)):
        uji(f"I08 A{k[0]} Bl{k[1]} Bs{k[2]}", lambda o, W=dict(A=k[0], Bl=k[1], Bs=k[2]): W[o["g"]])
    print("\n-- I-24 [lit] volatility-managed (σ30 BTC relatif median 365 hari) --")
    for lo, hi in ((0.5, 1.5), (0.67, 1.5), (0.5, 2.0), (0.75, 1.33)):
        uji(f"I24 1/vrel [{lo},{hi}]", lambda o, lo=lo, hi=hi: float(np.clip(1 / o["vrel"], lo, hi)))
    for p_ in (0.5, 2.0):
        uji(f"I24 (1/vrel)^{p_} [0.5,2]", lambda o, p_=p_: float(np.clip((1 / o["vrel"]) ** p_, 0.5, 2.0)))
    print("\n-- I-25 [lit] dispersi relatif (drel^k) --")
    for k in (0.5, 1.0, 1.5):
        for lo, hi in ((0.5, 1.5), (0.5, 2.0)):
            uji(f"I25 drel^{k} [{lo},{hi}]", lambda o, k=k, lo=lo, hi=hi: float(np.clip(o["drel"] ** k, lo, hi)))
    uji("I25 drel^1 hanya B [0.5,2]", lambda o: float(np.clip(o["drel"], 0.5, 2.0)) if o["g"] != "A" else 1.0)
    json.dump({k: {kk: (vv if kk == "lolos" else {x: vv[x] for x in ("tahun", "tahun_t2", "cagr", "cagr24", "ddp", "P", "dL", "dB", "dDD") if x in vv})
                   for kk, vv in v.items()} for k, v in HASIL.items()}, open(f"{DIR}/opt1.json", "w"), indent=1, default=str)
