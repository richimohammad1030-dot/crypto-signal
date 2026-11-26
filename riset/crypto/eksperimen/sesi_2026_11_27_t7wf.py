"""Sesi 27 Nov 2026 · TAHAP B untuk keluarga T7 (CM008 TP sebagian awal): walk-forward berlabuh, daftar SESUAI MASANYA (_wf.py),
biaya REAL, seluruh data Nov 2017-skrg. Varian = TP sebagian FRAC @ R (tanpa impas), SL/trailing/stagnan juara tidak berubah.
Aturan pilih per jendela (objektif MILESTONE T7, ditetapkan sebelum melihat hasil uji): (1) tahun < +1R paling sedikit,
(2) runtun kalah maks paling kecil, (3) R/thn terbesar — semua di periode pilih saja.
Juga dilaporkan: aturan pilih standar _wf (tahun < +1R lalu R/thn), P_rasio vs juara (riset/signifikansi.py), target T1-T8
(riset/massal/inti.nilai) pada uji tersambung 2020-skrg, dan uji stres +0,03R/trade + TP baru terisi bila harga MELEWATI
level 0,02R (ATURAN_BERSAMA G.3: limit 'sentuh' tidak dihitung).
Pemakaian: python sesi_2026_11_27_t7wf.py <repo> <data_lama>"""
import os, pickle, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _wf
REPO, DATA = sys.argv[1], sys.argv[2]
_wf.load(REPO, DATA)
sb, t0 = _wf.sb, _wf.t0
sys.path.insert(0, os.path.join(REPO, "riset")); sys.path.insert(0, os.path.join(REPO, "riset", "massal"))
import signifikansi as sig, inti

VAR = {"juara": {}}
for tr, fr in ((0.25, 0.67), (0.3, 0.5), (0.3, 0.67), (0.3, 0.75), (0.4, 0.67), (0.4, 0.75)):
    VAR[f"TP{fr:g}@{tr:g}R"] = dict(TP1_R=tr, TP1_FRAC=fr)
# pengisian limit realistis: harga harus MELEWATI TP 0,02R (tp1_price dipakai sebagai pemicu; isi dikoreksi ke level asli)
VAR["TP0.67@0.3R lewat"] = dict(TP1_R=0.32, TP1_FRAC=0.67, _isi=0.3)


def runtun(v):
    best = cur = 0
    for x in v:
        cur = cur + 1 if x < 0 else 0; best = max(best, cur)
    return best


def jalan(nm):
    kw = dict(VAR[nm]); isi = kw.pop("_isi", None); a = time.time()
    df = _wf.run(ubah=kw)
    if isi is not None:                                       # koreksi porsi TP: terisi di 0,30R walau pemicu 0,32R
        has = df.px_part.notna(); fr = kw["TP1_FRAC"]
        kor = np.where(has, fr * (isi - kw["TP1_R"]), 0.0)
        for k in ("R", "R_REAL", "R_KONS"): df[k] = df[k] + kor
    t = _wf.per_tahun(df)
    print(f"{nm:<20} n {len(df):5d} tot {df.R_REAL.sum():7.1f} DD {t0.maxdd(df.R_REAL.values):5.1f} win {(df.R_REAL > 0).mean() * 100:.0f}% "
          f"runtun {runtun(df.R_REAL.values)} · " + " ".join(f"{y % 100:02d}:{v:+.0f}" for y, v in t.items()) + f" · {time.time() - a:.0f}s", flush=True)
    return nm, df


def skor_t7(df, y_max):
    u = df[df.year <= y_max]; t = _wf.per_tahun(u)
    return (int((t < 1).sum()), runtun(u.R_REAL.values), -float(t.mean()))


def ke_inti(df):
    return [dict(t0=int(r.t_fill), t1=int(r.t_exit), r=float(r.R_REAL)) for r in df.itertuples()]


def lapor(nama, pilih, u, j):
    ju = j[j.year >= 2020]; tab = _wf.per_tahun(u)
    b = sig.banding([(int(x.t_exit), x.R_REAL) for x in ju.itertuples()], [(int(x.t_exit), x.R_REAL) for x in u.itertuples()], mulai=1577836800)
    s, sj = inti.nilai(ke_inti(u), 1.0), inti.nilai(ke_inti(ju), 1.0)
    st = inti.nilai([dict(x, r=x["r"] - 0.03) for x in ke_inti(u)], 1.0)
    print(f"\n== WF {nama} ==\npilihan: {pilih}")
    print("uji per tahun:", {int(y): round(float(r), 1) for y, r in tab.items()})
    print("juara        :", {int(y): round(float(r), 1) for y, r in _wf.per_tahun(ju).items()})
    for nm, x in (("WF", s), ("juara", sj), ("WF stres", st)):
        print(f"  {nm:<9} n {x['n']} PF {x['pf']:.2f} WR {x['wr']*100:.0f}% {x['persen']:+.1f}%/thn DD {x['dd']:.1f}% runtun {x['beruntun']} "
              f"minus {x['minus']} rasio {x['rasio']:.2f} target {x['n_lolos']}/7 {[k for k, v in x['lolos'].items() if not v]}")
    print("signifikansi:", b, flush=True)
    return dict(pilih=pilih, tab=tab, sig=b, s=s, sj=sj, st=st)


if __name__ == "__main__":
    H = dict(jalan(k) for k in VAR)                # berurutan (memori)
    pickle.dump(H, open(f"{DATA}/sesi_1127_t7wf.pkl", "wb"))
    j = H["juara"]; out = {}
    utama = {k: v for k, v in H.items() if not k.endswith("lewat")}
    # (A) aturan pilih T7
    pilih, uji = [], []
    for y_max, (a, b) in _wf.JENDELA:
        nm = min(utama, key=lambda k: skor_t7(utama[k], y_max)); pilih.append((y_max, nm))
        uji.append(utama[nm][(utama[nm].year >= a) & (utama[nm].year <= b)])
    out["T7"] = lapor("aturan pilih T7 (tahun<1R, runtun, R/thn)", pilih, pd.concat(uji).sort_values("t_exit"), j)
    # (B) aturan pilih standar
    tab, pl, u = _wf.walk(utama); out["std"] = lapor("aturan pilih standar (tahun<1R, R/thn)", pl, u, j)
    # (C) varian tetap TP0.67@0.3R dan versi 'lewat' (bukan WF: parameter dipilih sesi ini di daftar tetap 2020-23 → bias, info saja)
    for k in ("TP0.67@0.3R", "TP0.67@0.3R lewat", "TP0.75@0.3R"):
        out[k] = lapor(f"{k} tetap (info, parameter dari IS 2020-23)", [k], H[k][H[k].year >= 2020].sort_values("t_exit"), j)
    for k in H: print(k, "P(tahun minus) %:", t0.p_minus(H[k]))
    pickle.dump(out, open(f"{DATA}/sesi_1127_t7wf_hasil.pkl", "wb"))
