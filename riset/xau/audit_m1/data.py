"""Muat M1 Dukascopy (BID) 2020-2026, rakit H1, sambung dengan H1 repo (2004-2019) untuk pemanasan indikator."""
import glob, gzip, csv, json, numpy as np, datetime as dt
import os
M1DIR = os.environ.get("M1DIR", "riset/data/m1")   # data M1 ada di branch claude/data-xau-m1
REPO = os.environ.get("REPO", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

def load_m1():
    rows = []
    for p in sorted(glob.glob(f"{M1DIR}/xau_m1_*.csv.gz")):
        for r in csv.reader(gzip.open(p, "rt")):
            rows.append((int(r[0]), int(r[1]) / 1000, int(r[2]) / 1000, int(r[3]) / 1000, int(r[4]) / 1000))
    a = np.array(sorted(set(rows)), dtype=float)
    return a[:, 0].astype(np.int64), a[:, 1], a[:, 2], a[:, 3], a[:, 4]

def to_h1(T, O, H, L, C):
    b = T // 3600 * 3600
    idx = np.flatnonzero(np.r_[True, b[1:] != b[:-1]])
    end = np.r_[idx[1:], len(T)]
    return (b[idx].astype(float), O[idx], np.maximum.reduceat(H, idx), np.minimum.reduceat(L, idx), C[end - 1], idx, end)

def load_repo_h1():
    out = []
    for p in ["riset/data/xau_dukascopy_h1_2004_2014.json.gz", "riset/data/xau_dukascopy_h1.json.gz"]:
        out += json.load(gzip.open(f"{REPO}/{p}", "rt"))
    return np.array(out, dtype=float)


import collections
def month_shifts():
    """Geser waktu per bulan (detik) agar M1 cocok dengan H1 Dukascopy repo (waktu UTC benar). Bulan tanpa H1 repo (2026-10+): -3600 utk Okt (DST AS), 0 utk Nov."""
    T, O, H, L, C = load_m1()
    t, o, h, l, c, i0, i1 = to_h1(T, O, H, L, C)
    R = load_repo_h1(); d = {int(x[0]): x for x in R}
    months = collections.defaultdict(list)
    for k in range(len(t)): months[dt.datetime.fromtimestamp(t[k], dt.timezone.utc).strftime("%Y-%m")].append(k)
    sh = {}
    for ym, ks in sorted(months.items()):
        best = None
        for s_ in (-3600, 0, 3600):
            e = [abs(d[int(t[k]) + s_][4] - c[k]) for k in ks if int(t[k]) + s_ in d]
            if len(e) > 50:
                m = float(np.median(e))
                if best is None or m < best[1]: best = (s_, m)
        sh[ym] = best[0] if best else (-3600 if ym == "2026-10" else 0)
    return sh

def load_m1_fixed():
    T, O, H, L, C = load_m1()
    sh = month_shifts()
    ym = np.array([dt.datetime.fromtimestamp(x, dt.timezone.utc).strftime("%Y-%m") for x in T])
    T = T.copy()
    for k, v in sh.items(): T[ym == k] += v
    # catatan: s_ = -3600 berarti repo_t = M1_t - 3600 -> T_baru = T + s_
    return T, O, H, L, C
