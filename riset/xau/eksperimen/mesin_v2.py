"""MESIN ACUAN XAU v2 = #93v2 + OCO adaptif (dipasang pemilik 27 Nov 2026). Bot live (gold_bot.py) WAJIB identik (riset/replay_xau.py).
Lapisan di atas mesin dasar multi-strategi (KOMBO/MR/K6/SUS, multi_mesin.baseline) dan OCO 2 sisi lama (audit_mesin.replay):
  1. KOMBO SL 2,0 × ATR (sebelumnya 1,5).
  2. Bobot rezim (w_rez): MR 0,5× bila ER20 > ambang MR tahun itu; K6 0,5× bila ER20 > ambang K6 tahun itu.
     ER20 = |C_j - C_(j-20)| / Σ|ΔC| pada close harian (hari UTC = 07:00-07:00 WIB) hari j = hari terakhir yang sudah close saat
     sinyal. Ambang tahun Y = kuantil (MR 60%, K6 80%) ER20 trade strategi itu pada tahun (WIB) < Y (walk-forward, min 150 trade).
  3. Monitor edge per strategi (w_mon): 0,5× bila PF bersih (R - 0,40/r0)·w_rez trade strategi itu yang SUDAH TUTUP dalam 365
     hari sebelum jam sinyal < 1,0 (min 20 trade). Dihitung dari trade BAYANGAN mesin dasar (semua hari, termasuk hari OCO).
  4. OCO adaptif: hari d memakai OCO 2 sisi (risiko 1×) bila PF bersih trade OCO bayangan yang sudah tutup dalam 365 hari sebelum
     jam sinyal 07:00 >= 1,2 (min 8 trade); hari itu mesin dasar tidak dipakai (termasuk susulan). Selain itu mesin dasar.
  Jam sinyal t_sig = close candle keputusan (07:00 WIB; susulan = close candle keputusannya).
Pemakaian modul: trades(D, A, F, tabel=None) -> trade nyata (w = bobot risiko); ambang_tabel(D, A, F) -> {tahun: (mr, k6)}."""
import bisect, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import audit_mesin as m, multi_mesin as mm

KOMBO_SL = 2.0
BIAYA = 0.40
MR_Q, K6_Q, W_REZ = 0.6, 0.8, 0.5
MON_HARI, MON_AMB, MON_W, MON_N = 365, 1.0, 0.5, 20
OCO_HARI, OCO_AMB, OCO_N = 365, 1.2, 8


def tsig(x, T):
    return int(T[x["ip"]]) + 3600


def er20_harian(D):
    """{hari UTC k: ER20 hari sebelumnya yang sudah close (indeks hari ada di data)}."""
    T, O, H, L, C = D
    day = (np.asarray(T) // 86400).astype(int); ud, st = np.unique(day, return_index=True); en = np.append(st[1:], len(T))
    dc = np.asarray(C)[en - 1]; out = {}
    for k in range(21, len(ud)):
        j = k - 1; s = np.sum(np.abs(np.diff(dc[j - 20:j + 1])))
        out[int(ud[k])] = abs(dc[j] - dc[j - 20]) / s if s > 0 else 0.0
    return out


def dasar(D, A, F):
    sk = mm.sinyal_kombo(D); sig = mm.sinyal_live(D)
    sh = {i: d for i, d in mm.sinyal_hibrida(D).items() if i not in sk}
    ko = [dict(x, strat0="KOMBO") for x in mm.trades_mr(D, A, sk, sl=KOMBO_SL)]
    mr = [dict(x, strat0="MR") for x in mm.trades_mr(D, A, sh)]
    k6 = mm.trades_k6(D, A, F)
    su = mm.trades_sus(D, A, F, sig=sig)
    return [x for x in mm.baseline(D, A, F, mr=ko + mr, k6=k6, sig=sig, sus=su) if x["w"] > 0]


def ambang_tabel(D, A, F, base=None):
    T = D[0]; ER = er20_harian(D); base = base if base is not None else dasar(D, A, F); tab = {}
    yrs = sorted({m.wib(x["t0"]).year for x in base})
    for Y in range(yrs[0], yrs[-1] + 2):
        r = []
        for st, q in (("MR", MR_Q), ("K6", K6_Q)):
            v = [ER[tsig(x, T) // 86400] for x in base if x["strat"] == st and m.wib(x["t0"]).year < Y and tsig(x, T) // 86400 in ER]
            r.append(float(np.quantile(v, q)) if len(v) > 150 else None)
        tab[Y] = tuple(r)
    return tab


def _pf_jendela(t1s, pos, neg, t, hari, nmin):
    j = bisect.bisect_left(t1s, t); i = bisect.bisect_left(t1s, t - hari * 86400)
    if j - i < nmin: return None
    p = pos[j - 1] - (pos[i - 1] if i else 0); q = neg[j - 1] - (neg[i - 1] if i else 0)
    return p / q if q > 0 else float("inf")


def trades(D, A, F, tabel=None, base=None, oco=None, rinci=False):
    T = D[0]; ER = er20_harian(D)
    base = base if base is not None else dasar(D, A, F)
    tabel = tabel if tabel is not None else ambang_tabel(D, A, F, base)
    oco = oco if oco is not None else [dict(x, strat="OCO") for x in m.potong(m.replay(D, A=A))]
    # 1-2) bobot rezim
    for x in base:
        x = x; ts_ = tsig(x, T); y = m.wib(x["t0"]).year; thr = tabel.get(y, (None, None)); w = 1.0
        er = ER.get(ts_ // 86400)
        if er is not None:
            if x["strat"] == "MR" and thr[0] is not None and er > thr[0]: w = W_REZ
            if x["strat"] == "K6" and thr[1] is not None and er > thr[1]: w = W_REZ
        x["w_rez"] = w
    # 3) monitor per strategi (dari bayangan dasar)
    per = {}
    for x in sorted(base, key=lambda x: x["t1"]): per.setdefault(x["strat"], []).append(x)
    cum = {}
    for st, xs in per.items():
        r = [(x["R"] - BIAYA / x["r0"]) * x["w_rez"] for x in xs]
        cum[st] = ([x["t1"] for x in xs], np.cumsum([max(v, 0) for v in r]), np.cumsum([max(-v, 0) for v in r]))
    for x in base:
        pf = _pf_jendela(*cum[x["strat"]], tsig(x, T), MON_HARI, MON_N)
        x["w_mon"] = MON_W if (pf is not None and pf < MON_AMB) else 1.0
        x["w"] = x["w_rez"] * x["w_mon"]
    # 4) OCO adaptif per hari (hari = hari UTC candle 07:00)
    oc = sorted(oco, key=lambda x: x["t1"]); r = [x["R"] - BIAYA / x["r0"] for x in oc]
    ot = ([x["t1"] for x in oc], np.cumsum([max(v, 0) for v in r]), np.cumsum([max(-v, 0) for v in r]))
    hari = lambda x: int(T[x["ip"]] // 86400)
    jam07 = sorted({int(T[i]) for i in range(len(T)) if (int(T[i]) // 3600) % 24 == 23})
    aktif = {}
    for t in jam07:
        pf = _pf_jendela(*ot, t + 3600, OCO_HARI, OCO_N); aktif[t // 86400] = pf is not None and pf >= OCO_AMB
    out = [x for x in base if not aktif.get(hari(x), False)] + [dict(x, w=1.0) for x in oco if aktif.get(hari(x), False)]
    out.sort(key=lambda x: x["t0"])
    return (out, base, oco, aktif) if rinci else out
