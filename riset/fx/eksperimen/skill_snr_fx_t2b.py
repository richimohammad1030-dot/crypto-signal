"""SKILL SNR FX · TAHAP 2 putaran 1b (27 Nov 2026): signifikansi versi BOBOT + gabungan dengan monitor edge (T2).
Bobot SNR: risiko × w bila zona SUPDEM (memantul di tahap 1) ada di jalur TP saat fill; × wb bila jalur bersih dan ada angka
bulat 100 pip (pendorong tembus). Monitor: riset/massal/inti.monitor_pf (PF trade tutup N hari < ambang -> × w_turun),
dihitung dari R MENTAH (monitor tidak melihat bobot SNR), lalu dikalikan dengan bobot SNR.
Signifikansi = riset/signifikansi.banding (bootstrap blok bulanan berpasangan, P rasio R/DD) vs JUARA live, periode penuh & OOS.
Pemakaian: python riset/fx/eksperimen/skill_snr_fx_t2b.py"""
import os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(REPO, "riset")); sys.path.insert(0, os.path.join(REPO, "riset", "massal"))
import numpy as np
import skill_snr_fx_t2 as T2
import backtest as B, fx_live as F
import signifikansi as SG
import inti


def monitor(tr, hari, amb, w, kunci="pair", mn=20):
    x = [dict(t0=t["t"], t1=t["t_exit"], r=t["R"], pair=t["pair"], strat=t["strat"], _i=i) for i, t in enumerate(tr)]
    k = {}
    for y in inti.monitor_pf(x, hari, amb, w, mn, kunci): k[y["_i"]] = y["w"]
    return [dict(t, R=t["R"] * k.get(i, 0.0)) for i, t in enumerate(tr) if k.get(i, 0.0) > 0]


def sig(J, X, mulai=None):
    a = [(t["t_exit"], t["R"]) for t in J]; b = [(t["t_exit"], t["R"]) for t in X]
    r = SG.banding(a, b, mulai=mulai)
    return r


if __name__ == "__main__":
    t0 = time.time()
    data = [B.load(p) for p in F.PAIRS]; T2.T_END = max(int(P.t[-1]) for P in data)
    ZP = {P.name: T2.zona_pair(P) for P in data}
    J = T2.juara_snr(data, ZP)
    VAR = {
        "SNR w0,5": T2.bobot(J, ZP, ("SUPDEM",), 0.5, 1.0, data),
        "SNR w0,5 + bulat1,25": T2.bobot(J, ZP, ("SUPDEM",), 0.5, 1.25, data),
        "SNR w0,5 + bulat1,5": T2.bobot(J, ZP, ("SUPDEM",), 0.5, 1.5, data),
        "SNR w0,25": T2.bobot(J, ZP, ("SUPDEM",), 0.25, 1.0, data),
    }
    for hari in (365, 730):
        M = monitor(J, hari, 1.0, 0.5)
        VAR[f"monitor pair {hari}h<1 w0,5"] = M
        for nm in ("SNR w0,5", "SNR w0,5 + bulat1,25"):
            wb = 1.25 if "bulat" in nm else 1.0
            VAR[f"{nm} + monitor {hari}h"] = T2.bobot(M, ZP, ("SUPDEM",), 0.5, wb, data)
    T2.baris("JUARA (live)", J)
    for nm, X in VAR.items():
        T2.baris(nm, X)
        for lbl, m in (("penuh", T2.T_IS0), ("OOS", T2.T_OOS)):
            r = sig(J, X, m)
            print(f"      signifikansi {lbl}: {r}")
    print(f"waktu {time.time() - t0:.0f} dtk")
