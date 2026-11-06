"""Putaran 1 lanjutan (6 Nov 2026): uji TETANGGA definisi dispersi untuk I-25 (bobot = drel, batas [0,5; 2], k = 1).
Variasi: jendela return 12/24/48 jam, semesta 10/25/50 koin teratas bulan berjalan, median acuan 180/365/730 hari.
Juga: risiko terbuka bersamaan maksimum (bobot × 1%) dan uji per tahun dengan dispersi dihitung hanya dari koin yang ada.
Pemakaian: python riset/intraday/eksperimen/opt1b_tetangga_dispersi_2026-11-06.py <repo> <data> <dir_tahap0>"""
import os, sys, time, bisect
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.argv = sys.argv[:4]
import importlib.util
spec = importlib.util.spec_from_file_location("opt1", os.path.join(HERE, "opt1_ukuran_posisi_2026-11-06.py"))
M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)   # memuat data & indikator (tanpa __main__)

def retH(c, t, h):
    if c not in M.CT:
        try: M.CT[c] = M.h1(c)
        except Exception: M.CT[c] = (np.array([], np.int64), np.array([]))
    T, C = M.CT[c]; k = bisect.bisect_right(T, t - 3600) - 1
    return C[k] / C[k - h] - 1 if k >= h and T[k] > t - 3 * 3600 else None
def dispv(t, h, n):
    u = M.pit.ranked(M.DATA, time.strftime("%Y-%m", time.gmtime(t)))[:n]
    r = [x for x in (retH(c, t, h) for c in u) if x is not None]
    return float(np.std(r)) if len(r) >= min(8, n - 2) else np.nan

def pasang(h, n, look):
    ser = np.array([dispv(int(d), h, n) for d in M.days]); cache = {}
    for v in M.SETS.values():
        for o in v:
            if o["t"] not in cache:
                j = bisect.bisect_right(M.days, o["t"]); a = ser[max(0, j - look):j]; a = a[~np.isnan(a)]; x = dispv(o["t"], h, n)
                cache[o["t"]] = x / np.median(a) if len(a) >= 60 and x == x else 1.0
            o["drel"] = cache[o["t"]]

W = lambda o: float(np.clip(o["drel"], 0.5, 2.0))
b = M.BASE["pit_std"][0]
print(f"JUARA rasio L {b['lama']['rasio']} B {b['baru']['rasio']} DD {b['semua']['maxDD']} thn {list(b['tahun'].values())} stres terburuk {min(M.BASE['pit_stres'][0]['tahun'].values())}")
for h, n, look in ((24, 25, 365), (12, 25, 365), (48, 25, 365), (24, 10, 365), (24, 50, 365), (24, 25, 180), (24, 25, 730), (48, 50, 365), (12, 10, 365)):
    pasang(h, n, look)
    M.uji(f"I25 {h}j top{n} med{look}", W)
# risiko terbuka bersamaan (definisi dasar)
pasang(24, 25, 365)
tr = M.SETS["pit_std"]; w = np.array([W(o) for o in tr]); isw = np.array([o["t"] < M.IS_END for o in tr]); w = w / w[isw].mean()
ev = sorted([(int(o["t_fill"]) if "t_fill" in o else o["t"], wi) for o, wi in zip(tr, w)] + [(o["t_exit"], -wi) for o, wi in zip(tr, w)])
cur = mx = 0.0
for _, x in ev: cur += x; mx = max(mx, cur)
print(f"risiko terbuka bersamaan maks (bobot × 1%): {mx:.2f}% (juara 3,00%) · bobot > 1,25: {np.mean(w > 1.25) * 100:.0f}% trade · < 0,75: {np.mean(w < 0.75) * 100:.0f}%")
