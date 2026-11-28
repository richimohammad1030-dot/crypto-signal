"""KURIKULUM SKILL 1 · SNR · FX MAJOR · TAHAP 2 putaran 2 (sesi 29 Nov 2026): SNR DI LEVEL BREAKOUT (PWH/PWL) itu sendiri.
Putaran 1 menilai zona di JALUR TP. Putaran 2 menilai KONFLUENSI di level entry: UTAMA & SUSULAN = stop order di high/low
minggu lalu. Dari tahap 1 (7/7 pair): SUPDEM/SWING lebih sering MEMANTUL, BULAT 100 pip lebih sering DITEMBUS.
Hipotesis: level minggu lalu yang berimpit zona pantul (±k·R dari entry) lebih sering gagal tembus (breakout palsu -> SL);
level yang berimpit angka bulat 100 pip lebih sering tembus.
Cara pakai (frekuensi tetap, bobot risiko; zona hanya yang tersedia sebelum order aktif = tanpa lihat masa depan):
  K  : risiko × wk bila zona pantul (cats, kuat >= kmin) berpotongan [entry - k·R, entry + k·R]
  KB : K + risiko × wb bila angka bulat 100 pip dalam [entry, entry + k·R] (searah tembus) dan tidak ada zona pantul
Pilih varian HANYA dari IS 2015-06..2022 (rasio R/DD IS), lalu OOS 2023-2026 + uji stres +0,05R/trade + signifikansi.
Pemakaian: python riset/fx/eksperimen/skill_snr_fx_t2c.py"""
import os, sys, time, itertools
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(REPO, "riset"))
import numpy as np
import skill_snr_fx_t2 as T2
import backtest as B, fx_live as F
import signifikansi as SG


def konfluensi(Zp, o, cats, k, kmin=1):
    e = o["price"]; r0 = abs(e - o["sl"]); lo, hi = e - k * r0, e + k * r0
    m = (Zp["tav"] <= o["t_on"]) & (Zp["exp"] > o["t_on"]) & np.isin(Zp["cat"], cats) & (Zp["kuat"] >= kmin) \
        & (Zp["hi"] >= lo) & (Zp["lo"] <= hi)
    return bool(m.any())


def bulat_dekat(P, o, k):
    st = 100 * B.PIP[P.name]; e = o["price"]; r0 = abs(e - o["sl"]); s = o["side"]
    a, b = sorted((e, e + s * k * r0)); return np.ceil(a / st) * st <= b


def pakai(tr, ZP, data, cats, k, wk, kmin=1, wb=1.0, strats=("N3", "SUS")):
    Pm = {P.name: P for P in data}; out = []
    for t in tr:
        w = 1.0
        if t["strat"] in strats:
            o = dict(side=t["side"], price=t["entry"], sl=t["sl"], tp=t["tp"], t_on=t["t"])
            if abs(o["price"] - o["sl"]) > 0:
                if konfluensi(ZP[t["pair"]], o, cats, k, kmin): w = wk
                elif wb != 1.0 and bulat_dekat(Pm[t["pair"]], o, k): w = wb
        if w > 0: out.append(dict(t, R=t["R"] * w))
    return out


def stat(tr, a, b, stres=0.0):
    R = np.array([t["R"] - (stres if t["R"] != 0 else 0) for t in tr if a <= t["t_exit"] < b])
    eq = np.cumsum(R); dd = float((np.maximum.accumulate(np.insert(eq, 0, 0))[1:] - eq).max()) if len(R) else 0
    yrs = {}
    for t in tr:
        if a <= t["t_exit"] < b: y = time.gmtime(t["t_exit"]).tm_year; yrs[y] = yrs.get(y, 0) + t["R"]
    pf = R[R > 0].sum() / max(-R[R < 0].sum(), 1e-9)
    th = (b - a) / 86400 / 365.25
    return dict(n=len(R), pf=pf, R=R.sum(), dd=dd, rasio=R.sum() / th / max(dd, 1e-9), neg=[y for y, v in yrs.items() if v < 0])


if __name__ == "__main__":
    t0 = time.time()
    data = [B.load(p) for p in F.PAIRS]; END = max(int(P.t[-1]) for P in data) + 1
    ZP = {P.name: T2.zona_pair(P) for P in data}
    J = T2.juara_snr(data, ZP)
    for t in J: t.setdefault("strat", t.get("strat"))
    IS, OOS = (T2.T_IS0, T2.T_OOS), (T2.T_OOS, END)
    sj = stat(J, *IS); so = stat(J, *OOS)
    print(f"JUARA IS PF {sj['pf']:.2f} R {sj['R']:+.0f} DD {sj['dd']:.1f} rasio {sj['rasio']:.2f} th- {sj['neg']} | OOS PF {so['pf']:.2f} R {so['R']:+.0f} DD {so['dd']:.1f} rasio {so['rasio']:.2f} th- {so['neg']}")
    # berapa SL juara yang berimpit konfluensi vs berapa pemenang (ATURAN G: dicegah vs ikut hilang)
    rows = []
    VAR = list(itertools.product((("SUPDEM",), ("SWING",), ("SUPDEM", "SWING")), (0.25, 0.5, 1.0), (0.0, 0.5), (1, 2), (1.0, 1.5)))
    for cats, k, wk, kmin, wb in VAR:
        X = pakai(J, ZP, data, cats, k, wk, kmin, wb)
        a = stat(X, *IS); b = stat(X, *OOS); bs = stat(X, *OOS, 0.05)
        rows.append((a["rasio"], f"{'+'.join(cats)} k{k} w{wk} kuat>={kmin} bulat{wb}", a, b, bs, X))
    rows.sort(key=lambda r: -r[0])
    print(f"{len(VAR)} varian diuji (dipilih dari IS saja)")
    for ras, nm, a, b, bs, X in rows[:12]:
        print(f"{nm:<38} IS n{a['n']} PF {a['pf']:.2f} R {a['R']:+.0f} DD {a['dd']:.1f} rasio {a['rasio']:.2f} th- {a['neg']} | "
              f"OOS PF {b['pf']:.2f} R {b['R']:+.0f} DD {b['dd']:.1f} rasio {b['rasio']:.2f} th- {b['neg']} | stres OOS PF {bs['pf']:.2f}")
    # mitigasi SL: SL juara UTAMA/SUSULAN dengan konfluensi SUPDEM+SWING k0,5
    for cats, k in ((("SUPDEM", "SWING"), 0.5), (("SUPDEM",), 0.5)):
        sl = win = sl_k = win_k = 0
        for t in J:
            if t["strat"] not in ("N3", "SUS"): continue
            o = dict(side=t["side"], price=t["entry"], sl=t["sl"], tp=t["tp"], t_on=t["t"])
            kf = konfluensi(ZP[t["pair"]], o, cats, k)
            if t["R"] <= -0.5: sl += 1; sl_k += kf
            elif t["R"] > 0.05: win += 1; win_k += kf
        print(f"konfluensi {'+'.join(cats)} k{k}: SL berimpit {sl_k}/{sl} ({sl_k / max(sl, 1):.0%}) · menang berimpit {win_k}/{win} ({win_k / max(win, 1):.0%})")
    print("\nSignifikansi 2 teratas IS (bootstrap blok bulanan, vs juara):")
    for ras, nm, a, b, bs, X in rows[:2]:
        for lbl, m in (("penuh", T2.T_IS0), ("OOS", T2.T_OOS)):
            r = SG.banding([(t["t_exit"], t["R"]) for t in J], [(t["t_exit"], t["R"]) for t in X], mulai=m)
            print(f"  {nm} {lbl}: P_rasio {r['P_rasio_lebih_baik']:.3f} P_R {r['P_R_lebih_baik']:.3f} juara {r['juara']} penantang {r['penantang']}")
    print(f"waktu {time.time() - t0:.0f} dtk")
