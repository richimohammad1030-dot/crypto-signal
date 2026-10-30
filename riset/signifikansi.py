"""Uji signifikansi PENANTANG vs JUARA (dipakai riset crypto, XAU, intraday).
Bootstrap blok per bulan atas hasil harian kedua versi pada hari yang sama (berpasangan), 5.000 kali:
- P(penantang lebih baik) untuk total R dan rasio total R / drawdown (seri dihitung setengah).
- Interval 90% selisih total R per tahun.
Aturan pakai (lihat PROSEDUR): kandidat LOLOS hanya jika P(lebih baik) >= 0,90 untuk rasio R/DD.
Masukan: dua CSV trade. Kolom waktu tutup dideteksi otomatis (t1 / t_exit), kolom hasil: R.
Pemakaian: python riset/signifikansi.py <juara.csv> <penantang.csv> [mulai YYYY-MM-DD] [akhir YYYY-MM-DD]
Sebagai modul: signifikansi.banding(list_juara, list_penantang) dengan list (t_tutup_detik, R)."""
import calendar, csv, sys, time
import numpy as np

def _load(p):
    rows = list(csv.DictReader(open(p)))
    k = next(c for c in ("t_exit", "t1") if c in rows[0])
    return [(int(float(r[k])), float(r["R"])) for r in rows]

def _daily(tr, d0, nd):
    a = np.zeros(nd)
    for t, R in tr:
        j = t // 86400 - d0
        if 0 <= j < nd: a[j] += R
    return a

def _dd(c):
    return float((np.maximum.accumulate(np.concatenate([[0], c]))[1:] - c).max())

def banding(juara, penantang, mulai=None, akhir=None, sims=5000, seed=7):
    t0 = mulai or min(t for t, _ in juara + penantang); t1 = akhir or max(t for t, _ in juara + penantang) + 1
    d0, nd = t0 // 86400, (t1 - 1) // 86400 - t0 // 86400 + 1
    A, B = _daily([x for x in juara if t0 <= x[0] < t1], d0, nd), _daily([x for x in penantang if t0 <= x[0] < t1], d0, nd)
    yrs = nd / 365.25
    mon = (np.arange(nd) + d0) * 86400
    mkey = np.array([time.gmtime(int(t)).tm_year * 12 + time.gmtime(int(t)).tm_mon for t in mon])
    blocks = [np.flatnonzero(mkey == k) for k in np.unique(mkey)]
    rng = np.random.default_rng(seed)
    dR, dRat, = [], []
    for _ in range(sims):
        idx = np.concatenate([blocks[i] for i in rng.integers(0, len(blocks), len(blocks))])
        a, b = A[idx], B[idx]
        ca, cb = np.cumsum(a), np.cumsum(b)
        dR.append((b.sum() - a.sum()) / yrs)
        dRat.append(b.sum() / max(_dd(cb), 1) - a.sum() / max(_dd(ca), 1))
    dR, dRat = np.array(dR), np.array(dRat)
    return dict(hari=nd, bulan=len(blocks),
                juara=dict(R_thn=round(float(A.sum() / yrs), 2), DD=round(_dd(np.cumsum(A)), 2), rasio=round(float(A.sum() / max(_dd(np.cumsum(A)), 1)), 2)),
                penantang=dict(R_thn=round(float(B.sum() / yrs), 2), DD=round(_dd(np.cumsum(B)), 2), rasio=round(float(B.sum() / max(_dd(np.cumsum(B)), 1)), 2)),
                P_R_lebih_baik=round(float((dR > 0).mean() + 0.5 * (dR == 0).mean()), 3),
                P_rasio_lebih_baik=round(float((dRat > 0).mean() + 0.5 * (dRat == 0).mean()), 3),
                selisih_R_thn_90=[round(float(x), 2) for x in np.percentile(dR, [5, 95])])

if __name__ == "__main__":
    a, b = _load(sys.argv[1]), _load(sys.argv[2])
    ts = lambda s: calendar.timegm(time.strptime(s, "%Y-%m-%d"))
    r = banding(a, b, ts(sys.argv[3]) if len(sys.argv) > 3 else None, ts(sys.argv[4]) if len(sys.argv) > 4 else None)
    for k, v in r.items(): print(f"{k:<20} {v}")
    print("KEPUTUSAN:", "signifikan (>= 0,90)" if r["P_rasio_lebih_baik"] >= 0.90 else "BELUM signifikan (< 0,90)")
