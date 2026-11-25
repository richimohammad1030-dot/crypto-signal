"""Keluarga BARU untuk bank saringan massal XAU (sesi 26 Nov 2026) — USULAN SALIN ke riset/massal/xau.py.
Sesi riset XAU hanya boleh menulis di riset/xau/ (bank riset/massal/xau.py di luar wewenang sesi & tidak tersalin ke main),
jadi keluarga ditulis di sini dalam format bank yang sama: fungsi(M) -> yield (nama, trade inti). Untuk dipakai workflow
saringan-malam: tambahkan `from keluarga_usulan import X008_tom` (sys.path riset/xau/massal) lalu masukkan ke KELUARGA.
Uji lokal: python riset/xau/massal/keluarga_usulan.py <data_dir>

X008 TOM (sumber edge baru, saringan_1126/uji_1126): BUY 07:00 di hari pergantian bulan (hari bursa terakhir n_akhir +
n_awal pertama), SL k ATR, tutup 23:00 — edge mandiri stabil +0,106/+0,035/+0,118 R/trade (2005-14/15-21/22-26), korelasi
+0,12 dengan live. Celah yang diserang: tahun minus (cara gabung TD/TB memberi 3/16 vs 4/16). Cara gabung (maks 1 posisi/hari):
TA ganti non-KOMBO · TB ganti trade SELL + isi kosong · TC isi hari kosong · TD lewati trade SELL hari TOM.
[lit] Ariel (1987) "A monthly effect in stock returns"; Baur (2013) "The autumn effect of gold"."""
import os, sys, itertools
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path[:0] = [os.path.join(REPO, "riset", "massal"), os.path.join(REPO, "riset", "xau", "eksperimen")]
import strat_mesin as sm, audit_mesin as m


def X008_tom(M):
    import xau as B
    T, O, H, L, C = M.D; A = M.A; N = len(T); HR = ((T // 3600) % 24).astype(int)
    i07 = np.flatnonzero(HR == sm.PLACE)
    bl = np.array([m.wib(T[i]).year * 12 + m.wib(T[i]).month for i in i07])
    awal = np.array([k - np.searchsorted(bl, bl[k]) for k in range(len(i07))])
    sisa = np.array([np.searchsorted(bl, bl[k], side="right") - 1 - k for k in range(len(i07))])
    RAW = [x for x in M.trades() if x["w"] > 0]
    hari = lambda i: int(np.searchsorted(i07, i, side="right") - 1)
    kraw = [hari(x["ip"] if x.get("ip") is not None else x["i0"] - 1) for x in RAW]
    for na, nw, k in itertools.product((1, 2), (2, 3, 4), (1.5, 2.0, 3.0)):
        tom = {}
        for kk, i in enumerate(i07):
            if (awal[kk] < nw or sisa[kk] < na) and i + 1 < N and k * A[i] > 0.5:
                e = O[i + 1]; slp = e - k * A[i]; ex, t1, why = sm._kelola(M.D, i + 1, 1, e, slp, None)
                tom[kk] = dict(d=1, e=e, ex=ex, r0=k * A[i], t0=T[i + 1], t1=t1, why=why, w=1.0, i0=i + 1, ip=i,
                               R=(ex - e) / (k * A[i]), strat="TOM")
        for mode in ("TA", "TB", "TC", "TD"):
            out, pakai = [], set()
            for x, kk in zip(RAW, kraw):
                if kk in tom:
                    pakai.add(kk)
                    if mode == "TA" and x["strat"] != "KOMBO": out.append(tom[kk]); continue
                    if mode == "TB" and x["d"] == -1: out.append(tom[kk]); continue
                    if mode == "TD" and x["d"] == -1: continue
                out.append(x)
            if mode in ("TA", "TB", "TC"): out += [t for kk, t in tom.items() if kk not in pakai]
            if mode == "TD" and k != 1.5: continue          # TD tidak memakai trade TOM -> SL tidak berpengaruh
            yield f"X008 TOM {mode} akhir{na} awal{nw} sl{k}", B.ke_inti(out)


if __name__ == "__main__":
    import xau as B, inti
    M = B.Mesin(*B.muat(sys.argv[1])); (a, b), (c, d) = B.PERIODE
    j = B.ke_inti(M.trades()); ji, jo = inti.nilai(j, 0.5, a, b, 3), inti.nilai(j, 0.5, c, d, 3)
    hs = []
    for nm, tr in X008_tom(M):
        si, so = inti.nilai(tr, 0.5, a, b, 3), inti.nilai(tr, 0.5, c, d, 3); hs.append((inti.kunci(si), nm, si, so))
    hs.sort(key=lambda h: h[0])
    print(f"JUARA | {inti.baris(ji)} | {inti.baris(jo)}")
    for _, nm, si, so in hs[:10]:
        print(f"{nm} | {inti.baris(si)} | {inti.baris(so)} | penantang {inti.penantang(si, so, ji, jo)}")
    print(f"varian {len(hs)} · penantang {sum(inti.penantang(h[2], h[3], ji, jo) for h in hs)}")
