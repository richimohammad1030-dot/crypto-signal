"""Rezim emas per bulan (31 Okt 2026): tren vs sideways (efficiency ratio close harian) x volatil vs tenang (ATR D1/harga vs
median 2015-2021). Hasil K6 & RSI2 fade per rezim (bulan yang SAMA = tahu rezim sempurna, batas atas) dan dengan rezim
BULAN SEBELUMNYA (yang bisa diketahui bot). Plus uji 'tahun analog' (pola bulanan tahun mirip).
Pemakaian: python rezim_bulanan.py <xau_sambung.json> <ambigu.json>"""
import sys, json, pickle
import numpy as np
import audit_mesin as m
import strat_mesin as sm
import harian_mesin as hm
D = m.muat(sys.argv[1]); A = np.array(m.atr(list(D[2]), list(D[3]), list(D[4]), 14)); F = m.fitur(D, A)
AMB = {int(k): v for k, v in json.load(open(sys.argv[2])).items()}
idx, dh, dl, dc, datr = hm.harian(D); T = D[0]
bl = np.array([m.wib(D[0][i]).year * 12 + m.wib(D[0][i]).month - 1 for i in idx])
months = sorted(set(bl))[1:]
er, vol, ret = {}, {}, {}
for M in months:
    j = np.flatnonzero(bl == M)
    c = dc[j[0] - 1:j[-1] + 1]
    er[M] = abs(c[-1] - c[0]) / np.sum(np.abs(np.diff(c)))        # efficiency ratio: 1 = tren lurus, 0 = bolak-balik
    vol[M] = np.nanmean(datr[j] / dc[j]); ret[M] = c[-1] / c[0] - 1
pil = [M for M in months if M < 2022 * 12]
er_med, vol_med = np.median([er[M] for M in pil]), np.median([vol[M] for M in pil])
rez = {M: ("TREN" if er[M] >= er_med else "SIDEWAYS") + "-" + ("VOLATIL" if vol[M] >= vol_med else "TENANG") for M in months}
K6 = m.potong(m.jalankan({"tren_lawan_w": ("ema200", 0.0), "ambigu": AMB}, D, A, F))
MR = pickle.load(open("/tmp/data/mr_top.pkl", "rb"))[("RSI2", 0.35, "tanpa", "market", 3.0, None)][0]
def perbulan(tr):
    out = {}
    for x, v in zip(tr, m.net(tr)):
        w = m.wib(x["t0"]); k = w.year * 12 + w.month - 1; out[k] = out.get(k, 0) + v
    return out
pk, pm = perbulan(K6), perbulan(MR)
print(f"Ambang (median 2015-21): efficiency ratio {er_med:.3f}, ATR D1/harga {vol_med*100:.2f}%")
from collections import Counter
c = Counter(rez[M] for M in months); print("Jumlah bulan per rezim:", dict(c))
runs, cur, n = [], rez[months[0]], 0
for M in months:
    if rez[M] == cur: n += 1
    else: runs.append(n); cur, n = rez[M], 1
runs.append(n); print(f"Pergantian rezim: {len(runs)-1} kali dalam {len(months)} bulan; lama rata-rata {np.mean(runs):.1f} bln, terpanjang {max(runs)} bln")
stay = np.mean([rez[a] == rez[b] for a, b in zip(months[:-1], months[1:])])
print(f"Peluang rezim bulan depan = bulan ini: {stay*100:.0f}% (acak dengan 4 rezim ±25-30%)")
print("\nR bersih per bulan (rata-rata) per rezim:  [rezim bulan YANG SAMA]  |  [rezim BULAN SEBELUMNYA, bisa diketahui bot]")
for r in sorted(c):
    a = [M for M in months if rez[M] == r]; b = [M for M in months[1:] if rez[M - 1] == r]
    print(f"  {r:<17} K6 {np.mean([pk.get(M,0) for M in a]):+5.2f} RSI2 {np.mean([pm.get(M,0) for M in a]):+5.2f}  |  "
          f"K6 {np.mean([pk.get(M,0) for M in b]):+5.2f} RSI2 {np.mean([pm.get(M,0) for M in b]):+5.2f}   (n={len(a)}/{len(b)})")
# pemilih rezim sederhana: bulan depan pakai strategi terbaik untuk rezim bulan ini (tabel dihitung HANYA dari bulan sebelumnya)
tot = {"K6 saja": 0, "RSI2 saja": 0, "pemilih rezim": 0, "sempurna (tahu bulan sama)": 0}; mon_sel = []
for i, M in enumerate(months[1:], 1):
    hist = [(rez[P - 1], pk.get(P, 0), pm.get(P, 0)) for P in months[1:i] if P - 1 in rez]
    r = rez[M - 1]; hk = [x[1] for x in hist if x[0] == r]; hm_ = [x[2] for x in hist if x[0] == r]
    if len(hk) >= 6:
        pick = "K6" if np.mean(hk) >= np.mean(hm_) else "RSI2"
        mon_sel.append((M, pick))
        tot["pemilih rezim"] += pk.get(M, 0) if pick == "K6" else pm.get(M, 0)
        tot["K6 saja"] += pk.get(M, 0); tot["RSI2 saja"] += pm.get(M, 0)
        tot["sempurna (tahu bulan sama)"] += max(pk.get(M, 0), pm.get(M, 0))
print(f"\nPemilih rezim walk-forward ({len(mon_sel)} bulan, mulai {mon_sel[0][0]//12}-{mon_sel[0][0]%12+1:02d}): ",
      {k: round(v, 1) for k, v in tot.items()})
# TAHUN ANALOG: bulan m tahun Y diprediksi naik/turun dari bulan m tahun analog (paling mirip di bulan 1..m-1 tahun Y)
yrs = sorted({M // 12 for M in months}); hit = n_ = up = 0
for Y in yrs[2:]:
    for mo in range(3, 12):
        M = Y * 12 + mo
        if M not in ret: continue
        cur = np.array([ret.get(Y * 12 + k, 0) for k in range(mo)])
        best, bc = None, -2
        for Z in yrs:
            if Z >= Y: continue
            past = np.array([ret.get(Z * 12 + k, 0) for k in range(mo)])
            cc = np.corrcoef(cur, past)[0, 1] if np.std(past) > 0 else -2
            if cc > bc: bc, best = cc, Z
        pred = np.sign(ret.get(best * 12 + mo, 0)); hit += pred == np.sign(ret[M]); up += ret[M] > 0; n_ += 1
print(f"\nTahun analog: arah bulan berikutnya benar {hit}/{n_} = {hit/n_*100:.0f}% | selalu tebak 'naik' benar {up/n_*100:.0f}%")
for a_, b_ in ((2025, 2021), (2021, 2025)):
    pass
x = [ret.get(2021 * 12 + k, 0) for k in range(12)]; y = [ret.get(2025 * 12 + k, 0) for k in range(12)]
print(f"Contoh pemilik: korelasi return bulanan emas 2021 vs 2025 = {np.corrcoef(x, y)[0,1]:+.2f}; "
      f"arah bulan sama {sum(np.sign(a)==np.sign(b) for a,b in zip(x,y))}/12; total 2021 {np.prod([1+v for v in x])-1:+.0%}, 2025 {np.prod([1+v for v in y])-1:+.0%}")
