"""Uji maju INTRADAY (siklus Jumat langkah 3): akumulasi LIVE vs REPLAY juara vs BAYANGAN (kandidat uji-maju) sejak tanggal mulai.
Bayangan: (I-25 GAGAL konfirmasi 2018-2019 pada 11 Nov 2026 -> kolom hanya pembanding; ganti dengan kandidat uji-maju berikutnya)
  I-25 bobot dispersi (sejak 6 Nov 2026): trade SAMA dengan juara, bobot risiko = clip(dispersi / median 365 hari, 0,5, 2),
       dispersi = simpangan baku return 24 jam 25 koin teratas (urutan signal_bot.COINS = yang dipakai bot), rata-rata bobot
       2020-2023 = 1 (normalisasi sama dengan riset 6 Nov, tetapi semesta = daftar bot, bukan daftar sesuai masanya).
Penilaian strategi hanya dari akumulasi >= 4-8 minggu (intraday: >= 60 trade sebelum usulan).
Pemakaian: python riset/intraday/bayangan.py <repo> <data_dir>"""
import bisect, calendar, collections, datetime as dt, json, os, sys, time
REPO, DATA = sys.argv[1:3]
sys.path.insert(0, REPO); sys.path.insert(0, os.path.join(REPO, "riset"))
import numpy as np
import backtest_intraday as bi, signal_bot as sb

LIVE_START = calendar.timegm((2026, 10, 30, 9, 0, 0))      # juara v3 live 30 Okt 16:00 WIB
MULAI = {"I-25 bobot dispersi": calendar.timegm((2026, 11, 6, 0, 0, 0))}
now = time.time()
P, sent, ref = bi.run(REPO, DATA)
H1, _ = bi.load(DATA, sb.COINS)
U = [c for c in sb.COINS[:25] if c in H1]
def ret24(c, t):
    T, C = H1[c]["T"], H1[c]["C"]; k = bisect.bisect_right(T, t - 3600) - 1
    return C[k] / C[k - 24] - 1 if k >= 24 and T[k] > t - 3 * 3600 else None
def disp(t):
    r = [x for x in (ret24(c, t) for c in U) if x is not None]
    return float(np.std(r)) if len(r) >= 8 else np.nan
T0 = int(H1["BTC"]["T"][0]) // 86400 * 86400 + 40 * 86400
days = np.arange(T0, int(now), 86400); DS = np.array([disp(int(d)) for d in days])
def drel(t):
    j = bisect.bisect_right(days, t); a = DS[max(0, j - 365):j]; a = a[~np.isnan(a)]; x = disp(t)
    return x / np.median(a) if len(a) >= 60 and x == x else 1.0
w_raw = lambda o: float(np.clip(drel(o["t"]), 0.5, 2.0))
norm = np.mean([w_raw(o) for o in ref if o["t"] < bi.IS_END])

hist = json.load(open(os.path.join(REPO, "intraday_state.json"))).get("hist", [])
live = [h for h in hist if h[3] >= LIVE_START and h[4] < now]
rep = [o for o in ref if o["t_fill"] >= LIVE_START and o["t_exit"] < now]
wk = lambda t: (dt.datetime.fromtimestamp(t, dt.timezone.utc) + dt.timedelta(hours=7)).strftime("%G-W%V")
print(f"Sejak {time.strftime('%d %b %Y %H:%M', time.gmtime(LIVE_START + 7 * 3600))} WIB · normalisasi bobot I-25 = {norm:.3f}")
print(f"{'minggu':<9}{'live n':>7}{'live R':>8}{'replay n':>9}{'replay R':>9}{'I-25 R':>8}")
W = collections.defaultdict(lambda: [0, 0.0, 0, 0.0, 0.0])
for h in live: W[wk(h[4])][0] += 1; W[wk(h[4])][1] += h[7]
for o in rep:
    W[wk(o["t_exit"])][2] += 1; W[wk(o["t_exit"])][3] += o["R"]
    if o["t"] >= MULAI["I-25 bobot dispersi"]: W[wk(o["t_exit"])][4] += o["R"] * w_raw(o) / norm
for k in sorted(W):
    a = W[k]; print(f"{k:<9}{a[0]:>7}{a[1]:>+8.2f}{a[2]:>9}{a[3]:>+9.2f}{a[4]:>+8.2f}")
tot = [sum(W[k][i] for k in W) for i in range(5)]
print(f"{'total':<9}{tot[0]:>7}{tot[1]:>+8.2f}{tot[2]:>9}{tot[3]:>+9.2f}{tot[4]:>+8.2f}")
uj = [o for o in rep if o["t"] >= MULAI["I-25 bobot dispersi"]]
print(f"Uji maju I-25 sejak 6 Nov: {len(uj)} trade · juara {sum(o['R'] for o in uj):+.2f}R · I-25 {sum(o['R'] * w_raw(o) / norm for o in uj):+.2f}R "
      f"· bobot rata-rata {np.mean([w_raw(o) / norm for o in uj]) if uj else 0:.2f} · syarat usulan: >= 6 minggu & >= 60 trade")
