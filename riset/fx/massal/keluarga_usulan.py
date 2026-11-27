"""Keluarga BARU untuk bank saringan massal FX (sesi 27 Nov 2026). Dimuat otomatis oleh riset/massal/jalan.py
(fungsi bernama <KODE><3 digit>_...). Format: fungsi(M) -> yield (nama, trade inti dict(t0,t1,r,w,strat,pair)).
Semua ambang rezim dihitung WALK-FORWARD (kuantil trade tahun-tahun SEBELUMNYA saja) -> tanpa lihat masa depan.
Uji lokal: python riset/fx/massal/keluarga_usulan.py

F008 rezim range 5 hari (rng5 = (maks high - min low 5 hari D1 terakhir yang close) / ATR14 D1): SUSULAN lemah bila rng5
     tinggi (sesi 27 Nov: P_rasio 0,92 di 2017+, OOS TERKONTAMINASI karena fitur dipilih setelah melihat 2023).
F009 bobot SNR (skill 1 tahap 2): zona pantul (tahap 1) di jalur TP saat fill -> risiko × w; jalur bersih + angka bulat
     100 pip di jalur (tembus) -> × wb.
F010 gabungan F008 × F009 (+ monitor PF per pair).
F011 saringan fitur rezim lain (ER20, ER5, vol ATR14/100, momentum 20h) per bot, arah atas/bawah kuantil, WF."""
import os, sys, time, itertools
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path[:0] = [os.path.join(REPO, "riset", "massal"), os.path.join(REPO, "riset", "fx", "eksperimen"),
                os.path.join(REPO, "riset", "xau", "eksperimen"), os.path.join(REPO, "forex_major")]
import backtest as B
from backtest import atr, prev_daily

_C = {}


def _fitur(M):
    if "fe" in _C: return _C["fe"]
    FE = {}
    for P in M.data:
        idx, D = prev_daily(P); A = atr(D); A100 = atr(D, 100); c = D["c"]
        for d, j in idx.items():
            if j < 110 or not (A[j] > 0): continue
            er = lambda n: abs(c[j] - c[j - n]) / max(np.sum(np.abs(np.diff(c[j - n:j + 1]))), 1e-12)
            FE[(P.name, d)] = dict(rng5=(D["h"][j - 4:j + 1].max() - D["l"][j - 4:j + 1].min()) / A[j], er20=er(20), er5=er(5),
                                   vol=A[j] / A100[j], mom20=(c[j] - c[j - 20]) / A[j])
    _C["fe"] = FE; return FE


def _raw(M):
    """Trade mentah juara (dengan entry/sl/tp/side) + zona SNR per pair; strat N3/SUS/B3."""
    if "raw" in _C: return _C["raw"]
    import skill_snr_fx_t2 as T2
    ZP = {P.name: T2.zona_pair(P) for P in M.data}
    raw = T2.juara_snr(M.data, ZP)
    _C["raw"] = (raw, ZP, T2); return _C["raw"]


def _inti(tr):
    return sorted([dict(t0=t["t"], t1=t["t_exit"], r=t["R"], w=1.0, strat=t["strat"], pair=t["pair"]) for t in tr], key=lambda x: x["t1"])


def _yr(t): return time.gmtime(t).tm_year


def _wf(trades, FE, strats, f, q, w, arah="atas", jendela=None, mulai=2017):
    """Bobot w untuk trade strat di `strats` bila fitur f di atas (arah='atas') / di bawah kuantil q dari trade tahun < Y."""
    th = {}
    for Y in range(2015, 2028):
        v = [FE[(x["pair"], x["t0"] // 86400)][f] for x in trades if x["strat"] in strats and (x["pair"], x["t0"] // 86400) in FE
             and _yr(x["t0"]) < Y and (jendela is None or _yr(x["t0"]) >= Y - jendela)]
        th[Y] = float(np.quantile(v, q)) if len(v) > 100 else None
    out = []
    for x in trades:
        k = 1.0; fe = FE.get((x["pair"], x["t0"] // 86400)); Y = _yr(x["t0"])
        if x["strat"] in strats and fe and Y >= mulai and th[Y] is not None:
            hit = fe[f] > th[Y] if arah == "atas" else fe[f] < th[Y]
            if hit: k = w
        if k > 0: out.append(dict(x, r=x["r"] * k, w=x.get("w", 1.0) * k))
    return out


def _snr(raw, ZP, T2, data, cats, wh, wb):
    return _inti(T2.bobot(raw, ZP, cats, wh, wb, data))


def F008_rezim_rng5(M):
    FE = _fitur(M); base = M.tiga()
    for strats, q, w, jd in itertools.product((("SUS",), ("SUS", "N3"), ("SUS", "N3", "B3")), (0.7, 0.8, 0.85, 0.9),
                                              (0.0, 0.5), (None, 4)):
        yield f"F008 rng5 >q{q} {'+'.join(strats)} w{w} {'eksp' if jd is None else f'{jd}th'}", _wf(base, FE, strats, "rng5", q, w, "atas", jd)


def F009_bobot_snr(M):
    raw, ZP, T2 = _raw(M)
    for cats, wh, wb in itertools.product((("SUPDEM",), ("SUPDEM", "SWING")), (0.25, 0.5, 0.75), (1.0, 1.25, 1.5)):
        yield f"F009 SNR {'+'.join(cats)} jalur w{wh} bulat{wb}", _snr(raw, ZP, T2, M.data, cats, wh, wb)


def F010_rng5_x_snr(M):
    import inti
    FE = _fitur(M); raw, ZP, T2 = _raw(M)
    for wh, wb, q, w, mon in itertools.product((0.5, 0.75), (1.0, 1.25, 1.5), (0.8, 0.9), (0.0, 0.5), (False, True)):
        tr = _wf(_snr(raw, ZP, T2, M.data, ("SUPDEM",), wh, wb), FE, ("SUS",), "rng5", q, w)
        if mon: tr = inti.monitor_pf(tr, 365, 1.0, 0.5, 20, "pair")
        yield f"F010 SNR w{wh} bulat{wb} + rng5>q{q} SUS w{w}{' + monitorPF pair' if mon else ''}", tr


def F011_rezim_lain(M):
    FE = _fitur(M); base = M.tiga()
    for strats, f, arah, q, w in itertools.product((("SUS",), ("N3",)), ("er20", "er5", "vol", "mom20"), ("atas", "bawah"),
                                                   (0.2, 0.8), (0.0, 0.5)):
        if (arah == "atas") != (q == 0.8): continue          # atas kuantil 80% / bawah kuantil 20%
        yield f"F011 {strats[0]} {f} {arah} q{q} w{w}", _wf(base, FE, strats, f, q, w, arah)


if __name__ == "__main__":
    import fx as BANK
    M = BANK.Mesin(*BANK.muat(None)); t0 = time.time()
    for kel in (F008_rezim_rng5, F009_bobot_snr, F010_rng5_x_snr, F011_rezim_lain):
        n = 0
        for nm, tr in kel(M):
            n += 1
            if n <= 2: print(nm, len(tr), round(sum(x["r"] for x in tr), 1))
        print(kel.__name__, n, "varian", f"{time.time() - t0:.0f} dtk")
