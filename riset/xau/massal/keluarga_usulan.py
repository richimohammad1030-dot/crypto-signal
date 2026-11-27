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
import inti


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


# ---------------- sesi 27 Nov 2026: rezim pasar (WF) ----------------
# X009: bobot strategi menurut rezim hari sebelumnya (fitur D1 yang sudah close), ambang = kuantil trade strategi itu
# pada tahun-tahun SEBELUMNYA (walk-forward, tanpa lihat masa depan). Hipotesis dari IS 2005-21 (rezim_fitur_2026_11_27.py):
# MR/KOMBO melemah saat efisiensi tren 20 hari (ER20) tinggi; SUS tanpa edge di IS (-1,7R/883 trade 2005-26).
_FX = {}
def _fitur_xau(M):
    if "fe" in _FX: return _FX["fe"]
    T, O, H, L, C = M.D
    day = (T // 86400).astype(int); ud, st = np.unique(day, return_index=True); en = np.append(st[1:], len(T))
    dh = np.maximum.reduceat(H, st); dl = np.minimum.reduceat(L, st); dc = C[en - 1]
    tr_ = np.maximum(dh[1:] - dl[1:], np.maximum(abs(dh[1:] - dc[:-1]), abs(dl[1:] - dc[:-1]))); tr_ = np.insert(tr_, 0, dh[0] - dl[0])
    def sma(x, n):
        c = np.cumsum(np.insert(x, 0, 0)); o = np.full(len(x), np.nan); o[n - 1:] = (c[n:] - c[:-n]) / n; return o
    a14, a100 = sma(tr_, 14), sma(tr_, 100); FE = {}
    for k in range(110, len(ud)):
        j = k - 1
        er = lambda n: abs(dc[j] - dc[j - n]) / max(np.sum(np.abs(np.diff(dc[j - n:j + 1]))), 1e-12)
        FE[int(ud[k])] = dict(er20=er(20), er5=er(5), vol=a14[j] / a100[j], rng5=(dh[j - 4:j + 1].max() - dl[j - 4:j + 1].min()) / a14[j],
                              mom20=abs(dc[j] - dc[j - 20]) / a14[j])
    _FX["fe"] = FE; return FE


def _wf_xau(RAW, FE, aturan, mulai=2008):
    yr = lambda t: m.wib(t).year; th = {}
    def ambang(strats, f, q, Y):
        k = (strats, f, q, Y)
        if k not in th:
            v = [FE[int(x["t0"] // 86400)][f] for x in RAW if x["strat"] in strats and int(x["t0"] // 86400) in FE and yr(x["t0"]) < Y]
            th[k] = float(np.quantile(v, q)) if len(v) > 150 else None
        return th[k]
    out = []
    for x in RAW:
        k = 1.0; fe = FE.get(int(x["t0"] // 86400)); Y = yr(x["t0"])
        for strats, f, arah, q, w in aturan:
            if x["strat"] not in strats: continue
            if f is None: k *= w; continue
            a = ambang(strats, f, q, Y) if fe and Y >= mulai else None
            if a is not None and ((fe[f] > a) if arah == "atas" else (fe[f] < a)): k *= w
        out.append(dict(x, w=x["w"] * k))
    return out


def X009_rezim(M):
    import xau as B
    FE = _fitur_xau(M); RAW = [x for x in M.trades() if x["w"] > 0]
    for strats, f, arah, q, w in itertools.product((("MR", "KOMBO"), ("MR",), ("KOMBO",), ("K6",), ("SUS",)),
                                                    ("er20", "er5", "vol", "rng5", "mom20"), ("atas", "bawah"), (0.2, 0.4, 0.6, 0.8), (0.0, 0.5)):
        if (arah == "atas") != (q >= 0.6): continue
        yield f"X009 {'+'.join(strats)} {f} {arah} q{q} w{w}", B.ke_inti(_wf_xau(RAW, FE, [(strats, f, arah, q, w)]))


def X010_rezim_gabung(M):
    """Gabungan rezim + nasib SUS (celah tahun minus/DD/beruntun) + monitor PF per strategi."""
    import xau as B
    FE = _fitur_xau(M); RAW = [x for x in M.trades() if x["w"] > 0]
    for wsus, q, wmr, k6, mon in itertools.product((1.0, 0.5, 0.0), (0.6, 0.8), (0.5, 0.0), (False, True), (False, True)):
        at = [(("SUS",), None, "", 0, wsus), (("MR", "KOMBO"), "er20", "atas", q, wmr)]
        if k6: at.append((("K6",), "er20", "atas", 0.8, 0.5))
        tr = B.ke_inti(_wf_xau(RAW, FE, at))
        if mon: tr = inti.monitor_pf(tr, 365, 1.0, 0.5, 20, "strat")
        yield f"X010 SUS{wsus} MR/KOMBO er20>q{q} w{wmr}{' K6 er20>q0.8 w0.5' if k6 else ''}{' + monitorPF strat' if mon else ''}", tr


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
