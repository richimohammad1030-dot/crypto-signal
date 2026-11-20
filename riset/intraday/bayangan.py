"""Uji maju INTRADAY (siklus Jumat langkah 3): akumulasi LIVE vs REPLAY juara vs BAYANGAN (kandidat uji-maju) sejak tanggal mulai.
Bayangan (maks 3 kandidat, ATURAN_BERSAMA E.3): (I-25 GAGAL konfirmasi 2018-2019 pada 11 Nov 2026 -> kolom hanya pembanding; ganti dengan kandidat uji-maju berikutnya)
  I-25 bobot dispersi (sejak 6 Nov 2026): trade SAMA dengan juara, bobot risiko = clip(dispersi / median 365 hari, 0,5, 2),
       dispersi = simpangan baku return 24 jam 25 koin teratas (urutan signal_bot.COINS = yang dipakai bot), rata-rata bobot
       2020-2023 = 1 (normalisasi sama dengan riset 6 Nov, tetapi semesta = daftar bot, bukan daftar sesuai masanya).
  I-35 kandidat (sejak 20 Nov 2026 00 UTC, ATURAN_BERSAMA E.3): replay penuh dengan filter modul B: order B dilewati bila level
       PERIODE (high/low hari UTC & minggu ISO sebelumnya, dari H1 koin itu) berada dalam ±w ATR H1 dari harga limit
       (w = 0,25 -> kolom I35a; w = 0,5 -> kolom I35b). Modul A tidak berubah. Hanya trade dengan order sejak 20 Nov dihitung.
  I-36 kandidat (sejak 21 Nov 2026 00 UTC): idem, tetapi level = SWING-D1 (pivot fraktal n=3 di D1 UTC dari H1 koin itu, aktif
       setelah 3 candle kanan close, berlaku 30 hari), w = 0,5 ATR H1 (pilihan walk-forward jendela terakhir) -> kolom I36.
Penilaian strategi hanya dari akumulasi >= 4-8 minggu (intraday: >= 60 trade sebelum usulan).
Pemakaian: python riset/intraday/bayangan.py <repo> <data_dir>"""
import bisect, calendar, collections, datetime as dt, json, os, sys, time
REPO, DATA = sys.argv[1:3]
sys.path.insert(0, REPO); sys.path.insert(0, os.path.join(REPO, "riset"))
import numpy as np
import backtest_intraday as bi, signal_bot as sb

LIVE_START = calendar.timegm((2026, 10, 30, 9, 0, 0))      # juara v3 live 30 Okt 16:00 WIB
MULAI = {"I-25 bobot dispersi": calendar.timegm((2026, 11, 6, 0, 0, 0)), "I-35": calendar.timegm((2026, 11, 20, 0, 0, 0)),
         "I-36": calendar.timegm((2026, 11, 21, 0, 0, 0))}
now = time.time()
P, sent, ref = bi.run(REPO, DATA)
H1, M15 = bi.load(DATA, sb.COINS)
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
# ---- I-35: replay penuh juara dengan filter B dekat level PERIODE (salinan blok B bi.orders + filter sebelum sim)
LV = {}
for c, G in H1.items():
    d_ = G["T"] // 86400; w_ = (d_ + 3) // 7; tab = []
    for key, need in ((d_, 20), (w_, 140)):
        hi, lo = {}, {}
        u, inv = np.unique(key, return_inverse=True); cnt = np.bincount(inv)
        mx = np.full(len(u), -np.inf); mn = np.full(len(u), np.inf); np.maximum.at(mx, inv, G["H"]); np.minimum.at(mn, inv, G["L"])
        for k, kk in enumerate(u):
            if cnt[k] >= need: hi[int(kk)], lo[int(kk)] = float(mx[k]), float(mn[k])
        tab += [hi, lo]
    LV[c] = tab
def levels(c, t):
    dh, dl, wh, wl = LV[c]; d_ = t // 86400; w_ = (d_ + 3) // 7
    return [x for x in (dh.get(d_ - 1), dl.get(d_ - 1), wh.get(w_ - 1), wl.get(w_ - 1)) if x is not None]
SW = {}
for c, G in H1.items():
    d_ = G["T"] // 86400; u, inv = np.unique(d_, return_inverse=True); cnt = np.bincount(inv)
    mx = np.full(len(u), -np.inf); mn = np.full(len(u), np.inf); np.maximum.at(mx, inv, G["H"]); np.minimum.at(mn, inv, G["L"])
    ok = cnt >= 20; u, mx, mn = u[ok], mx[ok], mn[ok]; px, on = [], []
    for i in range(3, len(u) - 3):
        t_on = int(u[i + 3]) * 86400 + 86400
        if mx[i] == mx[i - 3:i + 4].max(): px.append(mx[i]); on.append(t_on)
        if mn[i] == mn[i - 3:i + 4].min(): px.append(mn[i]); on.append(t_on)
    SW[c] = (np.array(px, float), np.array(on, np.int64))
def swing(c, t):
    px, on = SW[c]; m = (on <= t) & (on + 30 * 86400 > t); return list(px[m])
def orders_i35(w, levels=levels):
    Q = dict(P); Q["B_ON"] = False; out = bi.orders(H1, M15, Q)
    for c, D in M15.items():
        T = D["T"]; G = H1[c]; GA = G["A"]; nxt = 0
        for i in np.flatnonzero(T % 86400 == 0):
            if i < max(nxt, 900) or T[i] < P["START"]: continue
            k = D["h1"].get(int(T[i]) - 3600)
            if k is None or k < 400: continue
            a = GA[k]; vr = a / GA[k - 336:k].mean(); tr = int(G["reg"][k])
            if vr < P["B_VR"] or a / G["C"][k] < P["B_ATRP"] or tr == 0: continue
            if P["B_BTC"] and int(G["btc"][k]) != tr: continue
            if tr == -1 and (not P["B_SHORT"] or (bi.funding_avg72(G, int(G["T"][k])) or 0) <= 0): continue
            o = D["O"][i]; lim = o - tr * P["B_K"] * a
            if any(abs(x - lim) <= w * a for x in levels(c, int(T[i]))): continue
            r, nxt = bi.sim(D, i, tr, lim, P["B_SL"] * a, lim + tr * P["B_TPF"] * P["B_K"] * a, P["B_VALID_JAM"] * 4, P["B_HOLD_JAM"] * 4, None, P)
            out.append(dict(r, t=int(T[i]), c=c, m="B", d=tr, vr=float(vr)))
    return out
I35 = {}
for nm, w, lf, mu in (("I35a", 0.25, levels, "I-35"), ("I35b", 0.5, levels, "I-35"), ("I36", 0.5, swing, "I-36")):
    _, tk = bi.portfolio(orders_i35(w, lf), sb.COINS, P["CAP"], P["PEND"])
    I35[nm] = [o for o in tk if o["t"] >= MULAI[mu] and o["t_exit"] < now]
w_raw = lambda o: float(np.clip(drel(o["t"]), 0.5, 2.0))
norm = np.mean([w_raw(o) for o in ref if o["t"] < bi.IS_END])

hist = json.load(open(os.path.join(REPO, "intraday_state.json"))).get("hist", [])
live = [h for h in hist if h[3] >= LIVE_START and h[4] < now]
rep = [o for o in ref if o["t_fill"] >= LIVE_START and o["t_exit"] < now]
wk = lambda t: (dt.datetime.fromtimestamp(t, dt.timezone.utc) + dt.timedelta(hours=7)).strftime("%G-W%V")
print(f"Sejak {time.strftime('%d %b %Y %H:%M', time.gmtime(LIVE_START + 7 * 3600))} WIB · normalisasi bobot I-25 = {norm:.3f}")
print(f"{'minggu':<9}{'live n':>7}{'live R':>8}{'replay n':>9}{'replay R':>9}{'I-25 R':>8}{'I35a R':>8}{'I35b R':>8}{'I36 R':>8}")
W = collections.defaultdict(lambda: [0, 0.0, 0, 0.0, 0.0, 0.0, 0.0, 0.0])
for h in live: W[wk(h[4])][0] += 1; W[wk(h[4])][1] += h[7]
for o in rep:
    W[wk(o["t_exit"])][2] += 1; W[wk(o["t_exit"])][3] += o["R"]
    if o["t"] >= MULAI["I-25 bobot dispersi"]: W[wk(o["t_exit"])][4] += o["R"] * w_raw(o) / norm
for j, nm in ((5, "I35a"), (6, "I35b"), (7, "I36")):
    for o in I35[nm]: W[wk(o["t_exit"])][j] += o["R"]
for k in sorted(W):
    a = W[k]; print(f"{k:<9}{a[0]:>7}{a[1]:>+8.2f}{a[2]:>9}{a[3]:>+9.2f}{a[4]:>+8.2f}{a[5]:>+8.2f}{a[6]:>+8.2f}{a[7]:>+8.2f}")
tot = [sum(W[k][i] for k in W) for i in range(8)]
print(f"{'total':<9}{tot[0]:>7}{tot[1]:>+8.2f}{tot[2]:>9}{tot[3]:>+9.2f}{tot[4]:>+8.2f}{tot[5]:>+8.2f}{tot[6]:>+8.2f}{tot[7]:>+8.2f}")
uj = [o for o in rep if o["t"] >= MULAI["I-25 bobot dispersi"]]
print(f"Uji maju I-25 sejak 6 Nov: {len(uj)} trade · juara {sum(o['R'] for o in uj):+.2f}R · I-25 {sum(o['R'] * w_raw(o) / norm for o in uj):+.2f}R "
      f"· bobot rata-rata {np.mean([w_raw(o) / norm for o in uj]) if uj else 0:.2f} · syarat usulan: >= 6 minggu & >= 60 trade")
for mu, cols, tgl in (("I-35", ("I35a", "I35b"), "20 Nov"), ("I-36", ("I36",), "21 Nov")):
    uj = [o for o in rep if o["t"] >= MULAI[mu]]
    print(f"Kandidat {mu} sejak {tgl} (data baru saja): juara {len(uj)} trade {sum(o['R'] for o in uj):+.2f}R · "
          + " · ".join(f"{nm} {len(I35[nm])} trade {sum(o['R'] for o in I35[nm]):+.2f}R" for nm in cols))
print("Kandidat: naik uji-maju bila >= 6 minggu & lebih baik dari juara; gagal bila 8 minggu tidak lebih baik")
