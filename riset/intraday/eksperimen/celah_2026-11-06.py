"""Bedah celah juara intraday v3 (6 Nov 2026): kondisi pasar saat trade, per tahun.
Masukan: CSV trade dari tahap0_semua_tahun_2026-11-06.py (default PIT standar) + data H1 BTC & funding.
Kondisi (semua dihitung dari data yang SUDAH ada sebelum waktu sinyal, tanpa mengintip):
  btc_vol   : volatilitas realisasi BTC 30 hari (std return H1 tahunan) → tersil dari seluruh periode
  btc_ret30 : return BTC 30 hari (naik > +10%, datar, turun < -10%)
  btc_jarak : jarak close BTC ke EMA200 H1 (dalam %, tersil)
  fund      : funding rata-rata 72 jam koin (≤0, 0-0,01%, >0,01%)
  rank      : peringkat koin saat itu (1-10, 11-25, 26-50) [PIT]
  hari      : hari kerja vs akhir pekan (WIB)
  dispersi  : sebaran return 24 jam antar koin 25 besar (tinggi = pasar terpecah)
Pemakaian: python riset/intraday/eksperimen/celah_2026-11-06.py <repo> <data> <trades.csv> <out.txt>"""
import bisect, collections, csv, json, os, sys, time
REPO, DATA, CSV, OUT = sys.argv[1:5]
sys.path.insert(0, REPO); sys.path.insert(0, os.path.join(REPO, "riset"))
import numpy as np
import backtest_intraday as bi, pit

tr = [dict(r, t=int(r["t"]), t_fill=int(r["t_fill"]), t_exit=int(r["t_exit"]), d=int(r["d"]), R=float(r["R"])) for r in csv.DictReader(open(CSV))]
pit._load(DATA)
coins = sorted({o["c"] for o in tr} | {"BTC"})
H1 = {}
for c in coins:
    rows = bi.jload(f"{DATA}/klines/{c}.json")
    if rows: H1[c] = np.array([x[:5] for x in rows], float)
B = H1["BTC"]; BT = B[:, 0].astype(np.int64); BC = B[:, 4]
lr = np.diff(np.log(BC), prepend=np.log(BC[0]))
vol = np.array([lr[max(0, i - 720):i].std() * np.sqrt(8766) if i > 50 else np.nan for i in range(len(BC))])
e200 = bi.ema(BC, 200)
def bk(t):  # indeks candle H1 BTC terakhir yang sudah close sebelum t
    return max(0, bisect.bisect_right(BT, t - 3600) - 1)
VQ = np.nanpercentile(vol[BT >= bi.PARAM["START"]], [33.3, 66.7])
JQ = np.nanpercentile(((BC - e200) / e200 * 100)[BT >= bi.PARAM["START"]], [33.3, 66.7])
FB = {c: bi.jload(f"{DATA}/funding/{c}.json") for c in coins}
FBT = {c: [x[0] for x in v] for c, v in FB.items()}
def fund72(c, t):
    ts = FBT.get(c) or []; a, b = bisect.bisect_right(ts, t - 72 * 3600), bisect.bisect_right(ts, t)
    return float(np.mean([x[1] for x in FB[c][a:b]])) if b - a >= 6 else None
# dispersi: std return 24 jam antar koin top-25 bulan itu
CT = {c: (H1[c][:, 0].astype(np.int64), H1[c][:, 4]) for c in H1}
def ret24(c, t):
    T, C = CT[c]; k = bisect.bisect_right(T, t - 3600) - 1
    return C[k] / C[k - 24] - 1 if k >= 24 and T[k] > t - 3 * 3600 else None
_dcache = {}
def disp(t):
    key = t // 3600
    if key not in _dcache:
        u = pit.ranked(DATA, time.strftime("%Y-%m", time.gmtime(t)))[:25]
        r = [x for x in (ret24(c, t) for c in u if c in CT) if x is not None]
        _dcache[key] = float(np.std(r)) if len(r) >= 8 else np.nan
    return _dcache[key]

for o in tr:
    k = bk(o["t"]); v = vol[k]; j = (BC[k] - e200[k]) / e200[k] * 100
    o["btc_vol"] = "rendah" if v < VQ[0] else "sedang" if v < VQ[1] else "tinggi"
    r30 = BC[k] / BC[max(0, k - 720)] - 1
    o["btc_ret30"] = "naik>10%" if r30 > 0.10 else "turun<-10%" if r30 < -0.10 else "datar"
    o["btc_jarak"] = "dekat/bawah" if j < JQ[0] else "sedang" if j < JQ[1] else "jauh atas"
    f = fund72(o["c"], o["t"])
    o["fund"] = "n/a" if f is None else "<=0" if f <= 0 else "0-0,01%" if f <= 0.0001 else ">0,01%"
    u = pit.ranked(DATA, time.strftime("%Y-%m", time.gmtime(o["t"])))
    rk = u.index(o["c"]) if o["c"] in u else 999
    o["rank"] = "1-10" if rk < 10 else "11-25" if rk < 25 else "26-50" if rk < 50 else ">50"
    o["hari"] = "akhir pekan" if time.gmtime(o["t"] + 7 * 3600).tm_wday >= 5 else "hari kerja"
    o["grup"] = "A-long" if o["m"] == "A" else ("B-long" if o["d"] == 1 else "B-short")
DQ = np.nanpercentile([disp(o["t"]) for o in tr], [33.3, 66.7])
for o in tr:
    x = disp(o["t"]); o["dispersi"] = "n/a" if np.isnan(x) else "rendah" if x < DQ[0] else "sedang" if x < DQ[1] else "tinggi"

f = open(OUT, "w")
def pr(*a): print(*a); print(*a, file=f)
YRS = sorted({time.gmtime(o["t"]).tm_year for o in tr})
pr(f"Bedah celah · {CSV} · {len(tr)} trade · tersil vol BTC {VQ.round(2)} · jarak EMA200 {JQ.round(1)}% · dispersi {DQ.round(3)}")
for kond in ("grup", "btc_vol", "btc_ret30", "btc_jarak", "fund", "rank", "hari", "dispersi"):
    pr(f"\n-- {kond} × tahun (R / n / avg) --")
    for g in sorted({o[kond] for o in tr}):
        cells = []
        for y in YRS:
            t = [o["R"] for o in tr if o[kond] == g and time.gmtime(o["t"]).tm_year == y]
            cells.append(f"{sum(t):+6.1f}/{len(t):<3}" if t else f"{'-':>10}")
        a = [o["R"] for o in tr if o[kond] == g]
        pr(f"{g:<12} " + " ".join(cells) + f" | {sum(a):+7.1f}/{len(a)} avg {np.mean(a):+.3f}")
    pr(f"{'':<12} " + " ".join(f"{y:>10}" for y in YRS))
# grup × kondisi untuk dua tahun terlemah
yr = collections.defaultdict(float)
for o in tr: yr[time.gmtime(o["t"]).tm_year] += o["R"]
lemah = sorted(yr, key=lambda y: yr[y])[:2]
for y in lemah:
    pr(f"\n== tahun lemah {y} ({yr[y]:+.1f}R): grup × kondisi ==")
    T = [o for o in tr if time.gmtime(o["t"]).tm_year == y]
    for kond in ("btc_vol", "btc_ret30", "btc_jarak", "fund", "rank", "hari", "dispersi"):
        line = []
        for g in sorted({o[kond] for o in T}):
            for gg in ("A-long", "B-long", "B-short"):
                a = [o["R"] for o in T if o[kond] == g and o["grup"] == gg]
                if a: line.append(f"{gg}|{g} {sum(a):+.1f}/{len(a)}")
        pr(f"{kond:<10} " + " · ".join(line))
    mon = collections.defaultdict(lambda: collections.defaultdict(float))
    for o in T: mon[time.strftime("%m", time.gmtime(o["t"]))][o["grup"]] += o["R"]
    pr("bulan: " + " · ".join(f"{m}: " + "/".join(f"{mon[m][g]:+.1f}" for g in ("A-long", "B-long", "B-short")) for m in sorted(mon)) + "  (A/B-long/B-short)")
json.dump([{k: o[k] for k in ("t", "c", "grup", "R", "btc_vol", "btc_ret30", "btc_jarak", "fund", "rank", "hari", "dispersi")} for o in tr],
          open(OUT.replace(".txt", ".json"), "w"))
