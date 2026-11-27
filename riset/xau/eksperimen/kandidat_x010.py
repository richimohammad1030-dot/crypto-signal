"""KANDIDAT XAU X010 (sesi 27 Nov 2026) dalam format trade mentah bot (bobot di kolom w) untuk bayangan.py / uji maju.
Aturan (semua ambang walk-forward = kuantil hari-hari tahun SEBELUMNYA, fitur D1 hari sebelumnya yang sudah close):
  - SUSULAN risiko 0,5×.
  - MR & KOMBO risiko 0,5× bila efisiensi tren 20 hari (ER20) > kuantil 60%.
  - K6 risiko 0,5× bila ER20 > kuantil 80%.
  - Monitor edge per strategi: risiko 0,5× bila PF trade strategi itu yang sudah tutup dalam 365 hari < 1,0 (min 20 trade).
Hasil 2005-2026 @0,5%: +12,6 R/thn (juara +13,8), DD 28R (juara 52R), P_rasio 0,88, Setra Feb 2025+ 0,87; @0,7%:
+8,8%/thn DD 19,3% vs juara @0,5% +6,9%/thn DD 26%. Rasio lebih buruk di 2015-18 & 2019-21. BELUM lolos gerbang (P < 0,90).
Pemakaian: trades(D, A, F) -> list trade mentah (dict dgn w)."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path[:0] = [HERE, os.path.join(REPO, "riset", "massal"), os.path.join(REPO, "riset", "xau", "massal")]
import multi_mesin as mm


class _M:
    def __init__(self, D): self.D = D


def trades(D, A, F, base=None):
    import keluarga_usulan as K, inti
    K._FX.clear()
    raw = [x for x in (base if base is not None else mm.baseline(D, A, F)) if x["w"] > 0]
    at = [(("SUS",), None, "", 0, 0.5), (("MR", "KOMBO"), "er20", "atas", 0.6, 0.5), (("K6",), "er20", "atas", 0.8, 0.5)]
    w1 = K._wf_xau(raw, K._fitur_xau(_M(D)), at)
    BIAYA = 0.40
    ii = [dict(t0=x["t0"], t1=x["t1"], r=(x["R"] - BIAYA / x["r0"]) * x["w"], w=x["w"], strat=x.get("strat", "?"), _i=k)
          for k, x in enumerate(w1)]
    k_mon = {y["_i"]: y["w"] / max(ii[y["_i"]]["w"], 1e-12) for y in inti.monitor_pf(ii, 365, 1.0, 0.5, 20, "strat")}
    return [dict(x, w=x["w"] * k_mon.get(k, 0.0)) for k, x in enumerate(w1) if k_mon.get(k, 0.0) > 0]
