"""Uji 'analog / pencocokan rezim' walk-forward (31 Okt 2026, permintaan pemilik). Semua varian menu mematuhi aturan tetap pemilik:
sinyal 07:00 WIB, semua ditutup 23:00 WIB.
Setiap awal bulan M: ciri pasar dari data s.d. akhir bulan M-1 (return 63 & 126 hari, ATR D1/harga, ATR D1 vs rata-rata 1 tahun),
distandarkan hanya dengan data masa lalu. Cari k bulan masa lalu paling mirip (hasil bulan berikutnya sudah diketahui sebelum M),
pilih varian menu dengan rata-rata R bulan-berikutnya tertinggi (atau JEDA bila semua <= 0), terapkan di bulan M.
Pembanding: juara tetap, K6 tetap, dan 'momentum strategi' (pilih varian terbaik 6 bulan terakhir, tanpa analog).
Pemakaian: python analog_wf.py <xau_sambung.json> <ambigu_sisi.json>"""
import sys, os, json, datetime as dt
import numpy as np
import audit_mesin as m
import harian_mesin as hm
sys.path.insert(0, os.path.join(m.REPO, "riset")); import signifikansi as sg

D = m.muat(sys.argv[1]); T = D[0]
A = np.array(m.atr(list(D[2]), list(D[3]), list(D[4]), 14)); F = m.fitur(D, A)
AMB = {int(k): v for k, v in json.load(open(sys.argv[2])).items()}
idx, dh, dl, dc, datr = hm.harian(D)

MENU = {
    "juara": m.potong(m.jalankan({"ambigu": AMB}, D, A, F)),
    "K6": m.potong(m.jalankan({"ambigu": AMB, "tren_lawan_w": ("ema200", 0.0)}, D, A, F)),
    "K6b": m.potong(m.jalankan({"ambigu": AMB, "tren_lawan_w": ("ema200", 0.5)}, D, A, F)),
    "hanya BUY": m.potong(m.jalankan({"ambigu": AMB, "tren": None} if False else {"ambigu": AMB, "bobot": 1.0}, D, A, F)),
    "SL 2,5 ATR": m.potong(m.jalankan({"ambigu": AMB, "sl_atr": 2.5}, D, A, F)),
    "mom60 market": hm.simulasi(D, A, hm.arah_harian(dh, dl, dc, "mom", 60), idx, masuk="market", sl=3.0, rr=4),
}
MENU["hanya BUY"] = m.potong(m.replay(D, A=A, ambigu=AMB, plan=lambda i, hi, lo, a: (True, False, 1.0)))
MENU["hanya SELL"] = m.potong(m.replay(D, A=A, ambigu=AMB, plan=lambda i, hi, lo, a: (False, True, 1.0)))
NET = {k: (v, m.net(v)) for k, v in MENU.items()}


def bln(t):
    w = m.wib(t); return w.year * 12 + w.month - 1


months = sorted({bln(x["t0"]) for x in MENU["juara"]})
perf = {k: {} for k in MENU}                       # R bersih per bulan per varian
for k, (tr, r) in NET.items():
    for x, v in zip(tr, r): perf[k][bln(x["t0"])] = perf[k].get(bln(x["t0"]), 0) + v

# ciri pasar di akhir tiap bulan (bar harian terakhir bulan itu)
dmon = np.array([bln(T[i]) for i in idx])
feat = {}
for M in months:
    js = np.flatnonzero(dmon == M)
    if len(js) == 0: continue
    j = js[-1]
    if j < 260: continue
    a_rel = datr[j] / dc[j]; a_1y = np.nanmean(datr[j - 252:j] / dc[j - 252:j])
    feat[M] = np.array([dc[j] / dc[j - 63] - 1, dc[j] / dc[j - 126] - 1, a_rel, a_rel / a_1y])


def pilih_analog(M, k):
    prev = M - 1
    if prev not in feat: return None
    past = [p for p in feat if p + 1 <= M - 1]      # bulan p yang hasil bulan p+1 sudah diketahui
    if len(past) < 24: return None
    X = np.array([feat[p] for p in past]); mu, sd = X.mean(0), X.std(0) + 1e-12
    dist = np.sqrt((((X - mu) / sd - (feat[prev] - mu) / sd) ** 2).sum(1))
    near = [past[i] for i in np.argsort(dist)[:k]]
    skor = {v: np.mean([perf[v].get(p + 1, 0) for p in near]) for v in MENU}
    best = max(skor, key=skor.get)
    return best if skor[best] > 0 else "JEDA"


def pilih_momentum(M, n=6):
    if M - n < months[0]: return None
    skor = {v: sum(perf[v].get(q, 0) for q in range(M - n, M)) for v in MENU}
    best = max(skor, key=skor.get); return best if skor[best] > 0 else "JEDA"


def rakit(pemilih):
    out, pil = [], {}
    for M in months:
        if M < 2017 * 12: continue
        v = pemilih(M); pil[M] = v
        if v in MENU:
            out += [x for x in MENU[v] if bln(x["t0"]) == M]
    return sorted(out, key=lambda x: x["t0"]), pil


HASIL = {"juara tetap": (MENU["juara"], None), "K6 tetap": (MENU["K6"], None)}
for k in (3, 6, 12, 24):
    HASIL[f"analog k={k}"] = rakit(lambda M, k=k: pilih_analog(M, k))
for n in (3, 6, 12):
    HASIL[f"momentum strategi {n} bln"] = rakit(lambda M, n=n: pilih_momentum(M, n))

P = (("2017-2021", ("2017-01-01", "2022-01-01")), ("2022-Jan25", m.UJI), ("Setra-era", m.KONF), ("2017-skrg", ("2017-01-01", None)))
J = [x for x in MENU["juara"]]; jl = [(int(x["t1"]), float(v)) for x, v in zip(J, m.net(J))]
K6 = MENU["K6"]; kl = [(int(x["t1"]), float(v)) for x, v in zip(K6, m.net(K6))]
for nm, (tr, pil) in HASIL.items():
    print(f"\n### {nm}")
    for pn, (a, b) in P:
        print("  " + m.baris(pn, m.stat(tr, a=a, b=b)))
    pl = [(int(x["t1"]), float(v)) for x, v in zip(tr, m.net(tr))]
    t0 = int(m.ts("2017-01-01"))
    print(f"  P_rasio 2017-skrg vs juara {sg.banding(jl, pl, t0)['P_rasio_lebih_baik']:.3f} · vs K6 {sg.banding(kl, pl, t0)['P_rasio_lebih_baik']:.3f}")
    if pil:
        from collections import Counter
        print("  pilihan bulanan:", dict(Counter(pil.values())))
        akhir = [f"{M // 12}-{M % 12 + 1:02d}:{pil[M]}" for M in sorted(pil)[-10:]]
        print("  10 bulan terakhir:", ", ".join(akhir))
