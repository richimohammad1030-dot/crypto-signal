"""Keluarga BARU untuk bank saringan massal FX (sesi 27 Nov 2026). Dimuat otomatis oleh riset/massal/jalan.py
(fungsi bernama <KODE><3 digit>_...). Format: fungsi(M) -> yield (nama, trade inti dict(t0,t1,r,w,strat,pair)).
Semua ambang rezim dihitung WALK-FORWARD (kuantil trade tahun-tahun SEBELUMNYA saja) -> tanpa lihat masa depan.
Uji lokal: python riset/fx/massal/keluarga_usulan.py

F008 rezim range 5 hari (rng5 = (maks high - min low 5 hari D1 terakhir yang close) / ATR14 D1): SUSULAN lemah bila rng5
     tinggi (sesi 27 Nov: P_rasio 0,92 di 2017+, OOS TERKONTAMINASI karena fitur dipilih setelah melihat 2023).
F009 bobot SNR (skill 1 tahap 2): zona pantul (tahap 1) di jalur TP saat fill -> risiko × w; jalur bersih + angka bulat
     100 pip di jalur (tembus) -> × wb.
F010 gabungan F008 × F009 (+ monitor PF per pair).
F011 saringan fitur rezim lain (ER20, ER5, vol ATR14/100, momentum 20h) per bot, arah atas/bawah kuantil, WF.

Sesi 29 Nov 2026:
F012 SKILL SNR tahap 2 putaran 3 (definisi baru, KURIKULUM T10): JARAK ke zona pantul terdekat di arah TP (dalam R) sebagai
     bobot risiko — zona dekat (< d R) -> × wa; jalur bersih s.d. TP -> × wb. (Putaran 1 = ada/tidak di jalur; putaran 2 =
     konfluensi di level entry -> IS bagus, OOS lebih buruk, P_rasio OOS 0,17: gagal.)
F013 MITIGASI SL (ATURAN G b): kategori SL terbesar backtest = "sempat untung >= 0,5R lalu berbalik" 238/749, 222 di
     antaranya SUSULAN (SUSULAN tanpa BE; MFE median SL 0,84R vs menang 1,73R) -> SL SUSULAN ke entry di +be R.
F014 MITIGASI SL: "breakout palsu <= 2 jam" 252/749 (194 SUSULAN, jam isi median 19 WIB; R/trade isi 19-23 WIB +0,07 vs
     16-19 WIB +0,22) -> order SUSULAN kadaluarsa lebih awal (jam WIB), dengan/tanpa BE F013. Tutup 23:00 tetap.
F015 SUMBER EDGE BARU (nilai relatif, korelasi rendah dengan breakout): spread 2 pair berkorelasi (AUD/NZD, EUR/GBP,
     EUR/CHF) — z-skor return n hari log-rasio (sd dari 250 hari SEBELUMNYA) > q -> 07:00 WIB beli yang tertinggal & jual
     yang memimpin (rev) atau sebaliknya (mom), tutup 23:00 WIB. R = rata-rata 2 kaki dalam satuan 0,5 ATR14 D1, spread
     asli per kaki. Mandiri dan juara + RV × 0,5. [lit] Gatev, Goetzmann & Rouwenhorst 2006 (pairs trading)."""
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


def _tiga_sus(M, be=None, tp=None, off_wib=None):
    """Juara dengan SUSULAN dimodifikasi: BE di +be R, TP tp × ATR, order kadaluarsa pada jam off_wib WIB."""
    import riset_putaran6 as P6, riset_putaran7 as P7, fx_live as FL, fx as BANK
    UK, SK, B3K = dict(FL.UK), dict(FL.SK, **({"tp": tp} if tp else {})), dict(FL.B3K)
    B.MAX_DAY = 2
    try: main = B.portfolio(P6.run_gen(M.data, P6.utama_gen(UK)))
    finally: B.MAX_DAY = 4
    filled = {(t["pair"], t["t"] // 86400) for t in main}
    g0 = P7.sus_gen(dict(SK, um=UK["dow"]), filled, UK["exp"])
    def g(P):
        out = g0(P)
        for d, lst in out.items():
            for o in lst:
                if be: o["be"] = be
                if off_wib: o["t_off"] = d * 86400 + (off_wib - 7) * 3600
        return out
    sus = P6.run_gen(M.data, g)
    b3 = P6.run_gen(M.data, P7.bot3_gen(B3K, main + sus))
    return sorted(BANK.ke_inti(main, "N3") + BANK.ke_inti(sus, "SUS") + BANK.ke_inti(b3, "B3"), key=lambda x: x["t1"])


def F012_snr_jarak(M):
    raw, ZP, T2 = _raw(M); Pm = {P.name: P for P in M.data}
    for cats, d, wa, wb in itertools.product((("SUPDEM",), ("SUPDEM", "SWING")), (0.75, 1.0, 1.5), (0.25, 0.5, 0.75), (1.0, 1.25, 1.5)):
        out = []
        for t in raw:
            w = 1.0
            if t["strat"] in ("N3", "SUS") and abs(t["tp"] - t["entry"]) > 0:
                o = dict(side=t["side"], price=t["entry"], sl=t["sl"], tp=t["tp"], t_on=t["t"]); r0 = abs(t["entry"] - t["sl"])
                z = T2.di_jalur(ZP[t["pair"]], o, cats, 1, 0.15, 1.0)
                if z is not None and abs(z - t["entry"]) < d * r0: w = wa
                elif z is None: w = wb
            out.append(dict(t, R=t["R"] * w))
        yield f"F012 SNR jarak {'+'.join(cats)} <{d}R w{wa} bersih{wb}", _inti(out)


def F013_sus_be(M):
    for be, tp in itertools.product((0.3, 0.5, 0.75, 1.0, 1.5), (0.8, 1.0)):
        yield f"F013 SUSULAN BE {be}R tp{tp}", _tiga_sus(M, be=be, tp=tp)


def F014_sus_kadaluarsa(M):
    for off, be in itertools.product((19, 20, 21, 22), (None, 0.5, 1.0)):
        yield f"F014 SUSULAN s/d {off}:00 WIB BE {be}", _tiga_sus(M, be=be, off_wib=off)


def _rv(M, pasangan, n, q, arah):
    from backtest import atr, prev_daily
    Pm = {P.name: P for P in M.data}; out = []
    for a, b in pasangan:
        A, Bp = Pm[a], Pm[b]; inv = b == "USDCHF"            # EURUSD vs 1/USDCHF
        ia, Da = prev_daily(A); ib, Db = prev_daily(Bp); Aa, Ab = atr(Da), atr(Db)
        ca = dict(zip(Da["t"] // 86400, np.log(Da["c"]))); cb = dict(zip(Db["t"] // 86400, (-1 if inv else 1) * np.log(Db["c"])))
        hari = sorted(set(ca) & set(cb)); x = np.array([ca[h] - cb[h] for h in hari]); pos = {h: i for i, h in enumerate(hari)}
        pa = {int(t): i for i, t in enumerate(A.h1["t"])}; pb = {int(t): i for i, t in enumerate(Bp.h1["t"])}
        for d in sorted(set(ia) & set(ib)):
            if (d + 3) % 7 >= 5: continue
            ja, jb = ia[d], ib[d]; hk = int(Da["t"][ja] // 86400)
            k = pos.get(hk)
            if k is None or k < 260 or hk != int(Db["t"][jb] // 86400): continue
            r = x[k - 255:k + 1]; rr = r[n:] - r[:-n]; sd = rr[:-1].std()
            if not sd > 0: continue
            z = rr[-1] / sd
            if abs(z) < q: continue
            s = (-1 if z > 0 else 1) * (1 if arah == "rev" else -1)       # s=+1: beli A, jual B(sintetis)
            i0a, i1a = pa.get(d * 86400), pa.get(d * 86400 + 15 * 3600); i0b, i1b = pb.get(d * 86400), pb.get(d * 86400 + 15 * 3600)
            if None in (i0a, i1a, i0b, i1b): continue
            ua, ub = 0.5 * Aa[ja], 0.5 * Ab[jb]
            if not (ua > 0 and ub > 0): continue
            sb = -s * (-1 if inv else 1)
            ra = s * (A.h1["c"][i1a] - A.h1["o"][i0a]) / ua - A.spread / ua
            rb = sb * (Bp.h1["c"][i1b] - Bp.h1["o"][i0b]) / ub - Bp.spread / ub
            out.append(dict(t0=d * 86400, t1=d * 86400 + 16 * 3600, r=0.5 * (ra + rb), w=1.0, strat="RV", pair=f"{a}/{b}"))
    return sorted(out, key=lambda x: x["t1"])


def F015_nilai_relatif(M):
    PS = {"AUDNZD": [("AUDUSD", "NZDUSD")], "EURGBP": [("EURUSD", "GBPUSD")], "EURCHF": [("EURUSD", "USDCHF")],
          "3pasang": [("AUDUSD", "NZDUSD"), ("EURUSD", "GBPUSD"), ("EURUSD", "USDCHF")]}
    base = M.tiga()
    for (nm, ps), n, q, arah in itertools.product(PS.items(), (1, 3, 5, 10), (1.0, 1.5, 2.0), ("rev", "mom")):
        rv = _rv(M, ps, n, q, arah)
        yield f"F015 RV {nm} n{n} z>{q} {arah}", rv
        if nm == "3pasang" and q >= 1.5:
            yield f"F015 juara + RV {nm} n{n} z>{q} {arah} x0.5", sorted(base + [dict(x, r=x["r"] * 0.5, w=0.5) for x in rv], key=lambda x: x["t1"])


if __name__ == "__main__":
    import fx as BANK
    M = BANK.Mesin(*BANK.muat(None)); t0 = time.time()
    for kel in ([globals()[a] for a in sys.argv[1:]] or (F008_rezim_rng5, F009_bobot_snr, F010_rng5_x_snr, F011_rezim_lain, F012_snr_jarak, F013_sus_be, F014_sus_kadaluarsa, F015_nilai_relatif)):
        n = 0
        for nm, tr in kel(M):
            n += 1
            if n <= 2: print(nm, len(tr), round(sum(x["r"] for x in tr), 1))
        print(kel.__name__, n, "varian", f"{time.time() - t0:.0f} dtk")
