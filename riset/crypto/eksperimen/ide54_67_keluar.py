"""Riset Jumat 13 Nov 2026 · jalur OPTIMASI a (aturan KELUAR), walk-forward berlabuh (_wf.py, daftar sesuai masanya, biaya REAL).
#54 TP sebagian lebih awal / lebih besar / bertingkat: pindahkan untung dari ekor ke trade biasa.
    Satu tingkat: porsi TP1_FRAC {0,25 · 0,33 · 0,50} × jarak TP1_R {0,75 · 1,0 · 1,5} R (juara = 0,25 @ 1,0R).
    Dua tingkat: 25% @ 1R + 25% @ 2R / 3R (mesin turunan: porsi & R rata-rata TP digabung di ext, blended_R tetap benar).
#67 (ide baru) SL pindah ke impas setelah TP1 terisi: SL = entry + off × r0, off {0 (impas), -0,5 (setengah risiko)}.
    Hipotesis: setelah +1R, trade yang berbalik penuh ke SL awal (-1R × 75%) adalah kerugian terbesar yang bisa dicegah;
    tandingannya: SL 8 ATR sengaja lebar, SL ketat memotong tren yang sempat koreksi (ekor). Dicek dengan data.
Semua varian = replay penuh (slot ikut berubah). Pilih per jendela dengan aturan _wf.walk (tahun < +1R paling sedikit, lalu R/thn).
Catatan biaya dua tingkat: fee maker & porsi funding memakai TP1_FRAC (0,25) → tingkat kedua sedikit dilebihkan biayanya (konservatif kecil).
Pemakaian: python ide54_64_keluar.py <repo> <data_lama>   (data dari eksperimen/unduh_lama.py)"""
import os, sys, time, pickle
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _wf
REPO, DATA = sys.argv[1], sys.argv[2]
_wf.load(REPO, DATA)
sb, t0 = _wf.sb, _wf.t0
sys.path.insert(0, os.path.join(REPO, "riset")); import signifikansi as sig
ASLI_SFE = sb.Engine.step_fill_exit


def patch(tp2=None, be=None):
    """tp2 = (R, porsi) tingkat kedua; be = offset SL (R) setelah TP1. None = tidak dipakai."""
    def sfe(self, coin, i, D):
        ASLI_SFE(self, coin, i, D)
        cs = self.s["coins"].get(coin) or {}
        p = cs.get("pos")
        if p is None or len(p) < 6 or not isinstance(p[5], dict) or not p[5].get("part"): return
        ext = p[5]; d, e = p[0], p[1]; r0 = sb.pos_r0(p)
        if be is not None and p[3] < D["T"][i]:
            lvl = e + d * be * r0
            if (d == 1 and lvl > p[2]) or (d == -1 and lvl < p[2]): p[2] = lvl
        if tp2 is not None and not ext.get("tp2") and ext.get("partT", 1e18) < D["T"][i]:
            R2, f2 = tp2; lvl = e + d * R2 * r0; O, H, L = D["O"][i], D["H"][i], D["L"][i]
            if (d == 1 and H >= lvl) or (d == -1 and L <= lvl):
                px = max(lvl, O) if d == 1 else min(lvl, O)
                f1 = ext["part"]
                ext["partR"] = (f1 * ext["partR"] + f2 * (px - e) * d / r0) / (f1 + f2)
                ext["part"] = f1 + f2; ext["tp2"] = True
    sb.Engine.step_fill_exit = sfe


def jalan(ubah=None, tp2=None, be=None):
    if tp2 is not None or be is not None: patch(tp2, be)
    try:
        return _wf.run(ubah=ubah)
    finally:
        sb.Engine.step_fill_exit = ASLI_SFE


VAR = {}
for fr in (0.25, 0.33, 0.50):
    for r in (0.75, 1.0, 1.5):
        nm = "juara" if (fr, r) == (0.25, 1.0) else f"#54 {int(fr*100)}%@{r}R"
        VAR[nm] = dict(ubah={"TP1_FRAC": fr, "TP1_R": r})
for r2 in (2.0, 3.0):
    VAR[f"#54 25%@1R+25%@{r2:.0f}R"] = dict(tp2=(r2, 0.25))
VAR["#67 impas stl TP1"] = dict(be=0.0)
VAR["#67 -0,5R stl TP1"] = dict(be=-0.5)

hasil = {}
for nm, kw in VAR.items():
    a = time.time()
    df = jalan(**kw)
    hasil[nm] = df
    t = _wf.per_tahun(df)
    print(f"{nm:<24} n {len(df):5d} tot {df.R_REAL.sum():7.1f} DD {t0.maxdd(df.R_REAL.values):5.1f} "
          f"avg {df.R_REAL.mean():+.3f} · <1R {int((t<1).sum())} · " + " ".join(f"{y%100:02d}:{v:+.0f}" for y, v in t.items())
          + f" · {time.time()-a:.0f}s", flush=True)
pickle.dump(hasil, open(f"{DATA}/ide54_64.pkl", "wb"))


def ringkas(df, nm):
    t = _wf.per_tahun(df); u = df[df.year >= 2020]
    k = max(1, int(round(len(u) * 0.02)))
    return dict(nama=nm, n=len(u), R_thn=float(t[t.index >= 2020].mean()), avg=float(u.R_REAL.mean()),
                win=float((u.R_REAL > 0).mean() * 100), dd=t0.maxdd(u.R_REAL.values),
                tanpa2=float(np.sort(u.R_REAL.values)[:-k].sum()), kurang1=int((t[t.index >= 2020] < 1).sum()),
                terburuk=float(t[t.index >= 2020].min()), sd=float(t[(t.index >= 2020) & (t.index <= 2025)].std()))


def wf(nama_grup, keys):
    v = {k: hasil[k] for k in keys}
    tab, pilih, u = _wf.walk(v)
    j = hasil["juara"]; ju = j[j.year >= 2020]
    ts = 1577836800
    b = sig.banding([(int(x.t_exit), x.R_REAL) for x in ju.itertuples()], [(int(x.t_exit), x.R_REAL) for x in u.itertuples()], mulai=ts)
    print(f"\n== WALK-FORWARD {nama_grup} ({len(keys)} varian) ==")
    print("pilihan per jendela:", pilih)
    print("uji tersambung per tahun:", {int(y): round(float(r), 1) for y, r in tab.items()})
    print("juara per tahun        :", {int(y): round(float(r), 1) for y, r in _wf.per_tahun(ju).items()})
    print(f"tahun < +1R: {int((tab < 1).sum())} · terburuk {tab.min():+.1f} · R/thn {tab.mean():.1f} (juara {_wf.per_tahun(ju).mean():.1f})")
    print("signifikansi (uji tersambung vs juara, 2020-skrg):", b)
    return dict(pilih=pilih, tab=tab, sig=b, u=u)


out = {"ringkas": [ringkas(df, k) for k, df in hasil.items()]}
print("\n" + pd.DataFrame(out["ringkas"]).round(3).to_string(index=False))
k54 = [k for k in hasil if k == "juara" or k.startswith("#54")]
k64 = ["juara"] + [k for k in hasil if k.startswith("#67")]
out["wf54"], out["wf64"] = wf("#54 TP", k54), wf("#67 SL impas", k64)
pickle.dump(out, open(f"{DATA}/ide54_64_wf.pkl", "wb"))
