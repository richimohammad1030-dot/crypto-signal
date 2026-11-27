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


def trades_oco(D, A, F, ambang=1.2, hari=365, w_oco=1.0, n_min=8, base=None, base_final=None):
    """KANDIDAT X010 + OCO ADAPTIF (27 Nov 2026, cara pikir pemilik: edge sekarang -> OCO; bila OCO gagal, kembali).
    OCO 2 sisi (juara lama, m.replay) = strategi ke-5 di bayangan. Hari d: bila PF bersih trade OCO yang SUDAH TUTUP dalam
    `hari` terakhir >= ambang (min n_min trade) -> hari itu memakai OCO (risiko w_oco), selain itu trade X010.
    2005-2026 @0,5%: +13,4 R/thn, DD 28R (juara 52R), 5/22 minus, P_rasio 0,83; sejak 2 Nov 2026 +9,8R (juara -0,1R)."""
    import bisect
    import numpy as np
    import audit_mesin as m
    X = base_final if base_final is not None else trades(D, A, F, base=base); T = D[0]
    oco = [dict(x, strat="OCO") for x in m.potong(m.replay(D, A=A))]
    day = lambda x: int(T[x["ip"]] // 86400) if x.get("ip") is not None else int(x["t0"] // 86400)
    BIAYA = 0.40
    cl = sorted(oco, key=lambda x: x["t1"]); t1 = [x["t1"] for x in cl]
    pos = np.cumsum([max(x["R"] - BIAYA / x["r0"], 0) for x in cl]); neg = np.cumsum([max(-(x["R"] - BIAYA / x["r0"]), 0) for x in cl])
    def aktif(d):
        j = bisect.bisect_left(t1, d * 86400); i = bisect.bisect_left(t1, d * 86400 - hari * 86400)
        if j - i < n_min: return False
        p = pos[j - 1] - (pos[i - 1] if i else 0); q = neg[j - 1] - (neg[i - 1] if i else 0)
        return q > 0 and p / q >= ambang
    Xd, Od = {}, {}
    for x in X: Xd.setdefault(day(x), x)
    for x in oco: Od.setdefault(day(x), x)
    out = []
    for d in sorted(set(Xd) | set(Od)):
        if d in Od and aktif(d): out.append(dict(Od[d], w=w_oco))
        elif d in Xd: out.append(Xd[d])
    return out


def trades_v2(D, A, F, oco=True, ambang=1.2):
    """#93v2 (27 Nov 2026, optimasi P): KOMBO SL 2,0 ATR (live 1,5) · MR 0,5× bila ER20 > q60 WF (KOMBO TIDAK dikecilkan) ·
    K6 0,5× bila ER20 > q80 · SUSULAN penuh · monitor PF 365h per strategi < 1,0 -> 0,5× · (opsional) OCO adaptif PF 365h >= 1,2.
    2005-26 @0,5%: tanpa OCO +13,2 R/thn DD 28R P 0,93 (Setra 0,84); + OCO +14,0 R/thn DD 28R P 0,87 (Setra 0,51);
    WF pemilihan dari 240 varian P 0,73-0,75. Sejak 2 Nov: +2,6R / +9,8R (live -0,1R)."""
    import inti, keluarga_usulan as K
    K._FX.clear()
    import xau as XB
    Mx = XB.Mesin(D, A, F)
    raw = [x for x in Mx.trades(2.0, 3.0, None, 1.5) if x["w"] > 0]
    at = [(("MR",), "er20", "atas", 0.6, 0.5), (("K6",), "er20", "atas", 0.8, 0.5)]
    w1 = K._wf_xau(raw, K._fitur_xau(_M(D)), at)
    ii = [dict(t0=x["t0"], t1=x["t1"], r=(x["R"] - 0.40 / x["r0"]) * x["w"], w=x["w"], strat=x["strat"], _i=k) for k, x in enumerate(w1)]
    km = {y["_i"]: y["w"] / max(ii[y["_i"]]["w"], 1e-12) for y in inti.monitor_pf(ii, 365, 1.0, 0.5, 20, "strat")}
    w2 = [dict(x, w=x["w"] * km.get(k, 0.0)) for k, x in enumerate(w1) if km.get(k, 0.0) > 0]
    if not oco: return w2
    return trades_oco(D, A, F, ambang=ambang, base_final=w2)
