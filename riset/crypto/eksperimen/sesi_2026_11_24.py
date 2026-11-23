"""Riset crypto Selasa 24 Nov 2026 · PERCEPATAN (ATURAN_BERSAMA E) · satu skrip saringan, 10 varian + juara.

SKILL SNR TAHAP 2 (BISA MEMAKAI), program kilat — 7 varian replay penuh (_wf.py, daftar sesuai masanya, biaya REAL):
  (ii) SL di balik level (ganti SL 8 ATR H1; r0 ikut berubah, risiko tetap 1R):
     S1 SL-SWING : SL = pivot SWING-D1 (fraktal n=2/3/5, sudah terkonfirmasi) terdekat di balik entry ∓ 1 ATR H1, dibatasi 4-16 ATR
     S2 SL-PERIODE: SL = low/high MINGGU sebelumnya (PWL/PWH) ∓ 1 ATR H1, dibatasi 4-16 ATR
     S3 SL-GESER : SL 8 ATR, tetapi bila ada pivot SWING-D1 di 6-11 ATR dari entry → SL digeser ke balik pivot (pivot ∓ 1 ATR)
  (iii) prioritas slot (urutan alokasi di candle cek; bot = peringkat market cap):
     S4 PRIO-PW  : koin yang harga tutupnya sudah menembus PWH (tren naik) / PWL (tren turun) didahulukan
     S5 PRIO-PD  : sama, dengan high/low HARI sebelumnya
  (i) filter entry dekat level lawan:
     S6 FILTER-1 : lewati order bila ada pivot SWING-D1 lawan dalam 1 ATR D1 di depan entry (BUY: high di atas; SELL: low di bawah)
     S7 FILTER-2 : sama, 2 ATR D1
SUMBER EDGE BARU #55 [lit] mean-reversion RSI(2) (Connors & Alvarez 2008, "Short Term Trading Strategies That Work"):
  portofolio TERPISAH (slot 5, risiko 1R/trade) di 10 koin teratas market cap sesuai masanya, candle D1 (UTC):
  BELI bila C > SMA200 & RSI2 < bawah; JUAL bila C < SMA200 & RSI2 > atas; masuk open hari berikut; keluar saat C melewati SMA5
  (open hari berikut), SL 3 ATR D1, batas 10 hari. Biaya taker+slip dua sisi + proksi funding 0,01%/8 jam (long bayar).
     R1 10/90 dua arah · R2 hanya BELI RSI2 < 10 · R3 5/95 dua arah
Saringan (E.2): periode pilih <= 2021 saja → 2-3 teratas ke walk-forward penuh + signifikansi (2020-skrg).
Pemakaian: python sesi_2026_11_24.py <repo> <data_lama>"""
import bisect, os, sys, time, pickle
import numpy as np, pandas as pd
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _wf
REPO, DATA = sys.argv[1], sys.argv[2]
MODE = sys.argv[3] if len(sys.argv) > 3 else ""          # "wf" = tahap B saja (_wf.load menimpa sys.argv)
_wf.load(REPO, DATA)
sb, t0, rp = _wf.sb, _wf.t0, _wf.rp
sys.path.insert(0, os.path.join(REPO, "riset")); import signifikansi as sig
ASLI_SC, ASLI_UNI = sb.Engine.step_check, _wf.UNI
REAL = t0.SKEN["REAL"]

# ------------------------------------------------------------------ level SNR per koin (tanpa melihat masa depan)
LV = {}


def _atr(H, L, C, n=14):
    pc = np.concatenate([[C[0]], C[:-1]])
    tr = np.maximum(H - L, np.maximum(abs(H - pc), abs(L - pc)))
    out = np.empty_like(tr); out[0] = tr[0]
    for k in range(1, len(tr)): out[k] = out[k - 1] + (tr[k] - out[k - 1]) / n
    return out


def bangun(c):
    D = rp.DATA[c]; T = np.asarray(D["T"], np.int64)
    H, L, C, O = (np.asarray(D[k], float) for k in "HLCO")
    out = {}
    for nm, key in (("D", T // 86400), ("W", (T // 86400 + 3) // 7)):
        st = np.flatnonzero(np.r_[True, np.diff(key) != 0]); en = np.r_[st[1:], len(T)] - 1
        bh, bl, bc = np.maximum.reduceat(H, st), np.minimum.reduceat(L, st), C[en]
        b = np.searchsorted(st, np.arange(len(T)), side="right") - 1          # blok berjalan tiap candle H1
        prev = b - 1                                                          # blok sebelumnya (sudah tutup)
        ok = prev >= 0
        out[nm + "H"] = np.where(ok, bh[np.maximum(prev, 0)], np.nan)
        out[nm + "L"] = np.where(ok, bl[np.maximum(prev, 0)], np.nan)
        if nm == "D":
            ad = _atr(bh, bl, bc)
            out["AD1"] = np.where(ok, ad[np.maximum(prev, 0)], np.nan)
            piv = {}
            for n in (2, 3, 5):
                for k in range(n, len(st) - n):
                    conf = en[k + n]
                    if bh[k] == bh[k - n:k + n + 1].max(): piv[(bh[k], 1)] = min(piv.get((bh[k], 1), conf), conf)
                    if bl[k] == bl[k - n:k + n + 1].min(): piv[(bl[k], -1)] = min(piv.get((bl[k], -1), conf), conf)
            arr = sorted((v, p, s) for (p, s), v in piv.items())
            out["pc"] = np.array([a[0] for a in arr]); out["pp"] = np.array([a[1] for a in arr]); out["ps"] = np.array([a[2] for a in arr])
    LV[c] = out


def pivot(c, i, s):
    """Harga pivot SWING-D1 jenis s (+1 high / -1 low) yang sudah terkonfirmasi pada candle H1 ke-i."""
    z = LV[c]; m = bisect.bisect_right(z["pc"], i)
    p, ss = z["pp"][:m], z["ps"][:m]
    return p[ss == s]


# ------------------------------------------------------------------ varian skill
def patch_sl(mode):
    def sc(self, coin, i, D, allow_new):
        ASLI_SC(self, coin, i, D, allow_new)
        cs = self.s["coins"].get(coin) or {}
        if cs.get("pos") is not None or not cs.get("pend"): return
        d, en, sl = cs["pend"]; A = D["A"][i]
        if mode == "SWING":
            p = pivot(coin, i, -d)
            p = p[(p - en) * d < -0.5 * A]
            if not len(p): return
            lv = p.max() if d == 1 else p.min()
            dist = min(max(abs(en - (lv - d * A)), 4 * A), 16 * A)
        elif mode == "PERIODE":
            lv = LV[coin]["WL" if d == 1 else "WH"][i]
            if np.isnan(lv) or (lv - en) * d >= 0: return
            dist = min(max(abs(en - (lv - d * A)), 4 * A), 16 * A)
        else:                                                  # GESER
            p = pivot(coin, i, -d); jar = (en - p) * d
            p = p[(jar >= 6 * A) & (jar <= 11 * A)]
            if not len(p): return
            lv = p.max() if d == 1 else p.min()
            dist = abs(en - (lv - d * A))
        cs["pend"] = [d, en, en - d * dist]
    sb.Engine.step_check = sc


def patch_prio(jenis):
    def uni(t):
        U = ASLI_UNI(t)
        if (t // 3600) % 24 not in sb.CHECK_HOURS_UTC: return U
        dep, bel = [], []
        for c in U:
            i = rp.IDX.get(c, {}).get(t)
            if i is None or c not in LV: bel.append(c); continue
            D = rp.DATA[c]; Ci, ES, EF = D["C"][i], D["ES"][i], D["EF"][i]
            hi, lo = LV[c][jenis + "H"][i], LV[c][jenis + "L"][i]
            if (Ci > ES and EF > ES and Ci > hi) or (Ci < ES and EF < ES and Ci < lo): dep.append(c)
            else: bel.append(c)
        return dep + bel
    _wf.UNI = uni


def gate_filter(k):
    def g(coin, i, D, d, en, sl, T):
        if coin not in LV: return True
        ad = LV[coin]["AD1"][i]
        if np.isnan(ad): return True
        p = pivot(coin, i, d)                                  # level lawan di depan: BUY → high, SELL → low
        jar = (p - en) * d
        return not bool(((jar > 0) & (jar <= k * ad)).any())
    return g


VAR = {"juara": {}, "S1 SL-SWING": dict(sl="SWING"), "S2 SL-PERIODE": dict(sl="PERIODE"), "S3 SL-GESER": dict(sl="GESER"),
       "S4 PRIO-PW": dict(prio="W"), "S5 PRIO-PD": dict(prio="D"), "S6 FILTER-1": dict(filt=1.0), "S7 FILTER-2": dict(filt=2.0)}


def jalan(nm):
    kw = VAR[nm]; a = time.time(); gate = None
    if "sl" in kw: patch_sl(kw["sl"])
    if "prio" in kw: patch_prio(kw["prio"])
    if "filt" in kw: gate = gate_filter(kw["filt"])
    try:
        df = _wf.run(gate=gate)
    finally:
        sb.Engine.step_check, _wf.UNI = ASLI_SC, ASLI_UNI
    t = _wf.per_tahun(df)
    print(f"{nm:<15} n {len(df):5d} tot {df.R_REAL.sum():7.1f} DD {t0.maxdd(df.R_REAL.values):5.1f} avg {df.R_REAL.mean():+.3f} · "
          + " ".join(f"{y % 100:02d}:{v:+.0f}" for y, v in t.items()) + f" · {time.time() - a:.0f}s", flush=True)
    return nm, df


# ------------------------------------------------------------------ #55 RSI(2) portofolio terpisah
def rsi(C, n=2):
    d = np.diff(C, prepend=C[0]); up, dn = np.clip(d, 0, None), np.clip(-d, 0, None)
    au, ad = np.empty_like(C), np.empty_like(C); au[0], ad[0] = up[0], dn[0]
    for k in range(1, len(C)):
        au[k] = au[k - 1] + (up[k] - au[k - 1]) / n; ad[k] = ad[k - 1] + (dn[k] - ad[k - 1]) / n
    return 100 - 100 / (1 + au / np.maximum(ad, 1e-12))


def harian(c):
    D = rp.DATA[c]; T = np.asarray(D["T"], np.int64); day = T // 86400
    st = np.flatnonzero(np.r_[True, np.diff(day) != 0]); en = np.r_[st[1:], len(T)] - 1
    lengkap = (en - st + 1) == 24
    H, L, C, O = (np.asarray(D[k], float) for k in "HLCO")
    B = dict(day=day[st][lengkap], O=O[st][lengkap], H=np.maximum.reduceat(H, st)[lengkap], L=np.minimum.reduceat(L, st)[lengkap], C=C[en][lengkap])
    s = pd.Series(B["C"])
    B["S200"] = s.rolling(200).mean().values; B["S5"] = s.rolling(5).mean().values
    B["RSI"] = rsi(B["C"]); B["ATR"] = _atr(B["H"], B["L"], B["C"])
    return B


def rsi2(lo, hi, dua_arah, top=10, slot=5, sl_atr=3.0, maks=10):
    HB = {c: harian(c) for c in rp.DATA}
    IX = {c: {int(dy): k for k, dy in enumerate(B["day"])} for c, B in HB.items()}
    days = sorted({int(x) for B in HB.values() for x in B["day"]})
    pos, rows = {}, []
    for dy in days:
        # 1) kelola posisi pada candle hari dy
        for c in list(pos):
            k = IX[c].get(dy)
            if k is None: continue
            B, p = HB[c], pos[c]
            if p["k_in"] == k:                                  # hari masuk: isi di open
                p["e"] = B["O"][k]; p["sl"] = p["e"] - p["d"] * p["r0"]
            d, e, sl = p["d"], p["e"], p["sl"]
            ex = None
            if (d == 1 and B["L"][k] <= sl) or (d == -1 and B["H"][k] >= sl):
                ex = min(sl, B["O"][k]) if d == 1 else max(sl, B["O"][k]); why = "SL"
            elif p.get("keluar"):
                ex, why = B["O"][k], "SMA5/waktu"
            if ex is not None:
                rows.append(dict(coin=c, d=d, t_fill=int(HB[c]["day"][p["k_in"]] * 86400), t_exit=int(dy * 86400), e=e, ex=ex, r0=p["r0"], why=why))
                del pos[c]; continue
            if p.get("keluar") is None and ((d == 1 and B["C"][k] > B["S5"][k]) or (d == -1 and B["C"][k] < B["S5"][k]) or k - p["k_in"] >= maks - 1):
                p["keluar"] = True                              # keluar di open hari berikut
        # 2) sinyal baru di tutup hari dy → masuk open hari berikut
        U = _wf.UNI(dy * 86400 + 86399)[:top]
        cand = []
        for c in U:
            k = IX.get(c, {}).get(dy)
            if c in pos or k is None or k < 210 or np.isnan(HB[c]["S200"][k]): continue
            B = HB[c]
            if B["C"][k] > B["S200"][k] and B["RSI"][k] < lo: cand.append((B["RSI"][k], c, 1, k))
            elif dua_arah and B["C"][k] < B["S200"][k] and B["RSI"][k] > hi: cand.append((100 - B["RSI"][k], c, -1, k))
        for _, c, d, k in sorted(cand):
            if len(pos) >= slot: break
            if k + 1 >= len(HB[c]["day"]): continue
            pos[c] = dict(d=d, k_in=k + 1, r0=sl_atr * HB[c]["ATR"][k])
    df = pd.DataFrame(rows)
    fee = (REAL["taker"] + REAL["slip"]) * (df.e + df.ex) / df.r0
    hold8 = (df.t_exit - df.t_fill) / 28800 + 3                # masuk open, keluar open; +1 hari kasar
    fund = df.d * 0.0001 * hold8 * df.e / df.r0
    df["R"] = (df.ex - df.e) * df.d / df.r0
    df["R_REAL"] = df.R - fee - fund
    df["year"] = pd.to_datetime(df.t_exit, unit="s").dt.year
    return df[df.year >= _wf.MULAI].sort_values("t_exit").reset_index(drop=True)


RVAR = {"R1 RSI2 10/90": (10, 90, True), "R2 RSI2 beli<10": (10, 90, False), "R3 RSI2 5/95": (5, 95, True)}


# ------------------------------------------------------------------ evaluasi
def ringkas(df, nm, y1=2021, y0=_wf.MULAI):
    u = df[(df.year >= y0) & (df.year <= y1)]; t = _wf.per_tahun(u)
    dd = t0.maxdd(u.R_REAL.values)
    return dict(nama=nm, n=len(u), R_trade=float(u.R_REAL.mean()) if len(u) else 0, R_thn=float(t.mean()) if len(t) else 0,
                DD=dd, rasio=float(u.R_REAL.sum() / max(dd, 1)), kurang1=int((t < 1).sum()), terburuk=float(t.min()) if len(t) else 0)


def gabung(a, b):
    return pd.concat([a[["coin", "d", "t_fill", "t_exit", "R_REAL", "year"]], b[["coin", "d", "t_fill", "t_exit", "R_REAL", "year"]]]).sort_values("t_exit").reset_index(drop=True)


def wf(hasil, nama, keys):
    tab, pilih, u = _wf.walk({k: hasil[k] for k in keys})
    j = hasil["juara"]; ju = j[j.year >= 2020]
    b = sig.banding([(int(x.t_exit), x.R_REAL) for x in ju.itertuples()], [(int(x.t_exit), x.R_REAL) for x in u.itertuples()], mulai=1577836800)
    print(f"\n== WALK-FORWARD {nama} ({len(keys)} varian termasuk juara) ==")
    print("pilihan per jendela:", pilih)
    print("uji tersambung per tahun:", {int(y): round(float(r), 1) for y, r in tab.items()})
    print("juara per tahun        :", {int(y): round(float(r), 1) for y, r in _wf.per_tahun(ju).items()})
    print(f"tahun < +1R: {int((tab < 1).sum())} · terburuk {tab.min():+.1f} · R/thn {tab.mean():.1f} (juara {_wf.per_tahun(ju).mean():.1f}) · "
          f"DD uji {t0.maxdd(u.R_REAL.values):.1f} (juara {t0.maxdd(ju.R_REAL.values):.1f})")
    print("signifikansi:", b, flush=True)
    return dict(pilih=pilih, tab=tab, sig=b)


if __name__ == "__main__" and MODE != "wf":
    a = time.time()
    for c in rp.DATA: bangun(c)
    print(f"level SNR {len(LV)} koin · {time.time() - a:.0f}s", flush=True)
    with Pool(2) as pool:
        hasil = dict(pool.map(jalan, list(VAR), chunksize=1))
    for nm, (lo, hi, dua) in RVAR.items():
        df = rsi2(lo, hi, dua); hasil[nm] = df
        t = _wf.per_tahun(df)
        print(f"{nm:<15} n {len(df):5d} tot {df.R_REAL.sum():7.1f} DD {t0.maxdd(df.R_REAL.values):5.1f} avg {df.R_REAL.mean():+.3f} win {(df.R_REAL > 0).mean() * 100:.0f}% · "
              + " ".join(f"{y % 100:02d}:{v:+.0f}" for y, v in t.items()), flush=True)
    pickle.dump(hasil, open(f"{DATA}/sesi_1124.pkl", "wb"))
    j = hasil["juara"]
    print("\n== SARINGAN (periode pilih 2018-2021 saja) ==")
    rows = [ringkas(hasil[k], k) for k in VAR]
    for k in RVAR:
        r = ringkas(hasil[k], k + " (mandiri)"); rows.append(r)
        rows.append(ringkas(gabung(j, hasil[k]), k + " + juara"))
    S = pd.DataFrame(rows); print(S.round(3).to_string(index=False))
    # korelasi bulanan RSI2 vs juara (2018-2021)
    m = lambda df: df[df.year <= 2021].groupby(pd.to_datetime(df.t_exit, unit="s").dt.to_period("M")).R_REAL.sum()
    for k in RVAR:
        x = pd.concat([m(j), m(hasil[k])], axis=1).fillna(0)
        print(f"korelasi bulanan {k} vs juara (2018-21): {x.corr().iloc[0, 1]:+.2f}")
    pickle.dump(S, open(f"{DATA}/sesi_1124_saringan.pkl", "wb"))


def tahap_b():
    """Uji penuh 2-3 teratas saringan: walk-forward + signifikansi (dipanggil: python sesi_2026_11_24.py <repo> <data> wf)."""
    hasil = pickle.load(open(f"{DATA}/sesi_1124.pkl", "rb")); j = hasil["juara"]
    out = {}
    out["prio"] = wf(hasil, "SKILL SNR (iii) prioritas slot", ["juara", "S4 PRIO-PW", "S5 PRIO-PD"])
    out["prio_pw"] = wf(hasil, "S4 PRIO-PW saja vs juara", ["juara", "S4 PRIO-PW"])
    g = {"juara": j}
    for k in RVAR: g[k] = gabung(j, hasil[k])
    out["rsi2"] = wf(g, "#55 RSI(2) portofolio terpisah + juara", list(g))
    for k in ("S4 PRIO-PW", "S5 PRIO-PD"):
        print(k, "P(tahun minus):", t0.p_minus(hasil[k]), "juara:", t0.p_minus(j))
    pickle.dump(out, open(f"{DATA}/sesi_1124_wf.pkl", "wb"))


if __name__ == "__main__" and MODE == "wf":
    tahap_b()
