"""Ide #49 (6 Nov 2026, pemilik: sistem ADAPTIF, target tanpa tahun minus). Meta-strategi walk-forward: tiap awal bulan pilih
strategi menu dengan R bersih terbaik N bulan terakhir (hanya data masa lalu), lalu jalankan bulan itu. Menu: bot live (hibrida),
#40 saja, MR SELL 71,22, Connors MA200, hibrida MA200, K6 saja, MR saja, OCO juara lama, KOSONG (tidak trade).
N = 1/3/6/12 bulan; varian 'pilih hanya bila terbaik > 0' (selain itu kosong). Metrik utama: tahun minus & tahun terburuk.
Pemakaian: python adaptif.py <sambung.json> <ambigu.json>"""
import sys, json
import numpy as np
import audit_mesin as m, strat_mesin as sm, multi_mesin as mm
D = m.muat(sys.argv[1]); T, O, H, L, C = D
A = np.array(m.atr(list(H), list(L), list(C), 14)); F = m.fitur(D, A)
AMB = {int(k): v for k, v in json.load(open(sys.argv[2])).items()}
MENU = {"live": mm.baseline(D, A, F, ambigu=AMB),
        "#40": mm.baseline(D, A, F, ambigu=AMB, sig=mm.sinyal_mr(D)),
        "71": mm.baseline(D, A, F, ambigu=AMB, sig=mm.sinyal_mr(D, mr_sell=71.22)),
        "conMA200": mm.baseline(D, A, F, ambigu=AMB, sig=mm.sinyal_connors(D, 200)),
        "hibMA200": mm.baseline(D, A, F, ambigu=AMB, sig=mm.sinyal_hibrida(D, 200)),
        "K6": mm.trades_k6(D, A, F, ambigu=AMB), "MR": mm.trades_mr(D, A, mm.sinyal_live(D)),
        "OCO": m.potong(m.jalankan({"ambigu": AMB}, D, A, F))}
bln = lambda t: m.wib(t).strftime("%Y-%m")
R = {}
for k, tr in MENU.items():
    for x, v in zip(tr, m.net(tr)): R.setdefault(k, {}).setdefault(bln(x["t0"]), []).append((x, float(v)))
semua = sorted({b for k in R for b in R[k]})
def thn(per_bln):
    th = {}
    for b, v in per_bln.items(): th[b[:4]] = th.get(b[:4], 0) + v
    return th
def tampil(nm, th, pilih=None):
    v = np.array(list(th.values())); ex = f" | dipilih: {pilih}" if pilih else ""
    print(f"{nm:<30} total {v.sum():+6.0f}R · R/thn {v.mean():+5.1f} · tahun minus {int((v < 0).sum())}/12 · terburuk {v.min():+4.0f} | "
          + " ".join(f"{y[2:]}:{x:+.0f}" for y, x in th.items()) + ex)
for k in MENU:
    tampil(f"tetap: {k}", thn({b: sum(v for _, v in R[k].get(b, [])) for b in semua}))
print()
for N in (1, 3, 6, 12):
    for syarat in (False, True):
        pb, cnt = {}, {}
        for j, b in enumerate(semua):
            if j < 12: continue
            skor = {k: sum(v for bb in semua[j - N:j] for _, v in R[k].get(bb, [])) for k in MENU}
            k = max(skor, key=skor.get)
            if syarat and skor[k] <= 0: k = "kosong"
            cnt[k] = cnt.get(k, 0) + 1
            pb[b] = 0.0 if k == "kosong" else sum(v for _, v in R[k].get(b, []))
        top = ", ".join(f"{k} {v}" for k, v in sorted(cnt.items(), key=lambda z: -z[1])[:4])
        tampil(f"ADAPTIF N={N}{' (>0)' if syarat else ''}", thn(pb), top)
