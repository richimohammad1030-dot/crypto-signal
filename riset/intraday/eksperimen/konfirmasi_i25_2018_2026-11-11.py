"""KONFIRMASI SEKALI I-25 (bobot dispersi, status uji-maju sejak 6 Nov 2026) di periode yang belum dipakai merancang: Mar 2018 - Feb 2020.
Trade = vonis juara v3 apa adanya (PIT, biaya juara). Bobot = clip(dispersi 24 jam 25 koin teratas sesuai masanya / median 365 hari, 0,5, 2),
dinormalisasi dengan rata-rata bobot trade PIT 2020-2023 (CSV evaluasi 11 Nov) → sama dengan definisi riset 6 Nov.
Pemakaian: python riset/intraday/eksperimen/konfirmasi_i25_2018_2026-11-11.py <repo> <data18> <trades_pit_2020+.csv>"""
import bisect, calendar, collections, csv, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
CSV = sys.argv[3]; sys.argv = sys.argv[:3] + ["/tmp"]
import importlib.util
spec = importlib.util.spec_from_file_location("t0", os.path.join(HERE, "tahap0_semua_tahun_2026-11-06.py"))
M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)
import numpy as np
pit, DATA = M.pit, M.DATA
START, AKHIR = calendar.timegm((2018, 3, 1, 0, 0, 0)), calendar.timegm((2020, 3, 1, 0, 0, 0))
CT = {}
def h1(c):
    if c not in CT:
        r = M.bi.jload(f"{DATA}/klines/{c}.json"); a = np.array([x[:5] for x in r], float) if r else np.zeros((0, 5))
        CT[c] = (a[:, 0].astype(np.int64), a[:, 4])
    return CT[c]
def ret24(c, t):
    T, C = h1(c); k = bisect.bisect_right(T, t - 3600) - 1
    return C[k] / C[k - 24] - 1 if k >= 24 and T[k] > t - 3 * 3600 else None
def disp(t):
    u = pit.ranked(DATA, time.strftime("%Y-%m", time.gmtime(t)))[:25]
    r = [x for x in (ret24(c, t) for c in u) if x is not None]
    return float(np.std(r)) if len(r) >= 8 else np.nan
days = np.arange(calendar.timegm((2017, 9, 1, 0, 0, 0)), calendar.timegm((2026, 11, 12, 0, 0, 0)), 86400)
DS = np.array([disp(int(d)) for d in days])
def w(t):
    j = bisect.bisect_right(days, t); a = DS[max(0, j - 365):j]; a = a[~np.isnan(a)]; x = disp(t)
    return float(np.clip(x / np.median(a), 0.5, 2.0)) if len(a) >= 60 and x == x else 1.0
ref = [int(r["t"]) for r in csv.DictReader(open(CSV)) if int(r["t"]) < calendar.timegm((2024, 1, 1, 0, 0, 0))]
norm = np.mean([w(t) for t in ref]); print(f"normalisasi (rata-rata bobot 2020-2023) {norm:.3f}")
for st in (False, True):
    s, tr = M.jalankan(True, st, {"START": START}); tr = [o for o in tr if o["t"] < AKHIR]
    yr = collections.defaultdict(lambda: [0.0, 0.0, 0])
    for o in tr:
        y = time.gmtime(o["t"]).tm_year; ww = w(o["t"]) / norm; yr[y][0] += o["R"]; yr[y][1] += o["R"] * ww; yr[y][2] += 1
    def dd(vals):
        eq = np.cumsum(vals); return float((np.maximum.accumulate(np.concatenate([[0], eq]))[1:] - eq).max())
    o2 = sorted(tr, key=lambda o: o["t_exit"])
    print(("STRES " if st else "STANDAR ") + " · ".join(f"{y}: juara {v[0]:+.1f} vs I-25 {v[1]:+.1f} (n {v[2]})" for y, v in sorted(yr.items())) +
          f" · total {sum(v[0] for v in yr.values()):+.1f} vs {sum(v[1] for v in yr.values()):+.1f} · DD {dd([o['R'] for o in o2]):.1f} vs {dd([o['R'] * w(o['t']) / norm for o in o2]):.1f}R")
