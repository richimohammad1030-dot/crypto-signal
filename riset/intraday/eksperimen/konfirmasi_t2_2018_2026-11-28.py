"""KONFIRMASI SEKALI monitor edge T2 (terpasang live 25 Nov 2026: risiko 50% bila PF trade tutup 365 hari < 1,0, min 20 trade)
di periode yang belum dipakai merancang: Mar 2018 - Feb 2020 (+ seluruh 2018-2026 sebagai gambaran).
Trade = juara v3 apa adanya (PIT, biaya juara; juga STRES taker 0,12%). Monitor pasca-trade = tepat (bobot 0,5 tidak mengubah slot).
Pemakaian: python riset/intraday/eksperimen/konfirmasi_t2_2018_2026-11-28.py <repo> <data18>"""
import bisect, calendar, collections, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.argv = sys.argv[:3] + ["/tmp"]
import importlib.util
spec = importlib.util.spec_from_file_location("t0", os.path.join(HERE, "tahap0_semua_tahun_2026-11-06.py"))
M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)
import numpy as np
START, AKHIR = calendar.timegm((2018, 3, 1, 0, 0, 0)), calendar.timegm((2020, 3, 1, 0, 0, 0))

def monitor(tr, hari=365, amb=1.0, w=0.5, mn=20):
    tt = sorted(tr, key=lambda o: o["t_exit"]); t1 = [o["t_exit"] for o in tt]
    pos = np.cumsum([max(o["R"], 0) for o in tt]); neg = np.cumsum([max(-o["R"], 0) for o in tt]); out, n = [], 0
    for o in tr:
        j = bisect.bisect_left(t1, o["t"]); i = bisect.bisect_left(t1, o["t"] - hari * 86400); k = 1.0
        if j - i >= mn:
            p = pos[j - 1] - (pos[i - 1] if i else 0); q = neg[j - 1] - (neg[i - 1] if i else 0)
            if q > 0 and p / q < amb: k = w
        n += k < 1; out.append(dict(o, R=o["R"] * k))
    return out, n
def dd(tr):
    eq = np.cumsum([o["R"] for o in sorted(tr, key=lambda o: o["t_exit"])])
    return float((np.maximum.accumulate(np.concatenate([[0], eq]))[1:] - eq).max()) if len(eq) else 0.0
def pf(tr):
    R = np.array([o["R"] for o in tr]); return float(R[R > 0].sum() / max(-R[R <= 0].sum(), 1e-9))
for st in (False, True):
    s, tr = M.jalankan(True, st, {"START": START})
    mo, n = monitor(tr)
    yr = collections.defaultdict(lambda: [0.0, 0.0, 0, 0])
    for a, b in zip(tr, mo):
        y = time.gmtime(a["t"]).tm_year; yr[y][0] += a["R"]; yr[y][1] += b["R"]; yr[y][2] += 1; yr[y][3] += b["R"] != a["R"]
    k18 = [o for o in tr if o["t"] < AKHIR]; m18 = [o for o in mo if o["t"] < AKHIR]
    print(("STRES  " if st else "STANDAR") + " per tahun (juara vs +monitor, n, trade diperkecil): " +
          " · ".join(f"{y}: {v[0]:+.1f} vs {v[1]:+.1f} (n {v[2]}, kecil {v[3]})" for y, v in sorted(yr.items())))
    print(f"   Mar2018-Feb2020: juara R {sum(o['R'] for o in k18):+.1f} PF {pf(k18):.2f} DD {dd(k18):.1f} | +monitor R {sum(o['R'] for o in m18):+.1f}"
          f" PF {pf(m18):.2f} DD {dd(m18):.1f} | trade diperkecil {sum(1 for a, b in zip(k18, m18) if a['R'] != b['R'])}/{len(k18)}")
    print(f"   2018-2026: juara R {sum(o['R'] for o in tr):+.1f} DD {dd(tr):.1f} | +monitor R {sum(o['R'] for o in mo):+.1f} DD {dd(mo):.1f} | diperkecil {n}", flush=True)
