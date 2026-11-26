"""Riset crypto Jumat 27 Nov 2026 · SKILL SNR tahap 2 (BISA MEMAKAI) putaran 2 · saringan 7 varian + juara (ATURAN_BERSAMA E.2).
Lanjutan sesi_2026_11_24.py (level SNR, pembanding, walk-forward dipakai ulang dari modul itu).
  (iv) keluar di level SNR (replay penuh _wf.py, daftar sesuai masanya, biaya REAL):
     T1 TRAIL-SWING     : trailing 72 candle DIGANTI SL di balik pivot SWING-D1 terbaru yang terkonfirmasi (low−1 ATR H1 utk BUY),
                          hanya mengetat
     T2 TRAIL-SWING+72  : trailing 72 candle tetap, ditambah pivot SWING-D1 (ambil yang lebih ketat)
     T3 TRAIL-PW        : trailing 72 DIGANTI low/high minggu lalu (PWL−1 ATR utk BUY), hanya mengetat
     T4 TRAIL-PW+72     : trailing 72 + PWL/PWH (lebih ketat)
     T5 TP-LEVEL        : TP sebagian 25% di pivot SWING-D1 lawan terdekat (high di atas entry utk BUY) bila 0,5-2R; selain itu 1R
  (v) strategi mandiri TEMBUS PWH/PWL (portofolio terpisah, 20 koin teratas sesuai masanya, slot 5, 1R/trade):
     candle H1 close pertama minggu itu di atas PWH (BUY) / di bawah PWL (SELL) searah EMA 200 H1 → masuk open candle berikut,
     SL 1,5 ATR D1 di balik level (PWH−1,5 ATR utk BUY).
     P1 keluar TP 2R / SL / 5 hari · P2 keluar trailing 72 candle H1 (sama dengan juara) / SL
     Biaya: taker+slip dua sisi, proksi funding 0,01%/8 jam (long bayar, short terima). SL dicek dulu (urutan candle terburuk).
Pemakaian: python sesi_2026_11_27.py <repo> <data_lama> [wf]"""
import bisect, os, pickle, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
REPO, DATA = sys.argv[1], sys.argv[2]
MODE = sys.argv[3] if len(sys.argv) > 3 else ""
KUNCI = sys.argv[4:]                            # disimpan sebelum _wf.load menimpa sys.argv
import sesi_2026_11_24 as S                     # memanggil _wf.load(REPO, DATA)
_wf, sb, t0, rp = S._wf, S.sb, S.t0, S.rp
ASLI_SC, ASLI_FE, ASLI_TP = sb.Engine.step_check, sb.Engine.step_fill_exit, sb.tp1_price
REAL = t0.SKEN["REAL"]


def patch_trail(mode, tetap72):
    def sc(self, coin, i, D, allow):
        cs = self.s["coins"].get(coin) or {}
        p = cs.get("pos")
        sl_lama = p[2] if p is not None else None
        ASLI_SC(self, coin, i, D, allow)
        p = (self.s["coins"].get(coin) or {}).get("pos")
        if p is None or sl_lama is None or coin not in S.LV: return
        d, A = p[0], D["A"][i]
        if not tetap72: p[2] = sl_lama                      # batalkan trailing 72 candle
        if mode == "SWING":
            pv = S.pivot(coin, i, -d)
            pv = pv[(pv - D["C"][i]) * d < 0]                  # pivot di belakang harga sekarang
            if not len(pv): return
            lv = (pv.max() if d == 1 else pv.min()) - d * A
        else:
            lv = S.LV[coin]["WL" if d == 1 else "WH"][i]
            if np.isnan(lv): return
            lv = lv - d * A
        if (lv - p[2]) * d > 0 and (D["C"][i] - lv) * d > 0: p[2] = lv
    sb.Engine.step_check = sc


TPMAP, CUR = {}, [None]


def patch_tp():
    def fe(self, coin, i, D):
        cs = self.s["coins"].get(coin) or {}
        ada = cs.get("pos") is not None
        if not ada and cs.get("pend") and coin in S.LV:       # siapkan target bila order terisi di candle ini
            d, en, sl = cs["pend"]; r0 = abs(en - sl)
            pv = S.pivot(coin, i - 1, d); jar = (pv - en) * d
            ok = pv[(jar >= 0.5 * r0) & (jar <= 2 * r0)]
            TPMAP[coin] = (ok.min() if d == 1 else ok.max()) if len(ok) else None
        CUR[0] = coin
        ASLI_FE(self, coin, i, D)

    def tp(d, e, r0):
        lv = TPMAP.get(CUR[0])
        return lv if lv is not None and (lv - e) * d > 0 else ASLI_TP(d, e, r0)
    sb.Engine.step_fill_exit = fe; sb.tp1_price = tp


VAR = {"juara": {}, "T1 TRAIL-SWING": dict(tr=("SWING", False)), "T2 TRAIL-SWING+72": dict(tr=("SWING", True)),
       "T3 TRAIL-PW": dict(tr=("PW", False)), "T4 TRAIL-PW+72": dict(tr=("PW", True)), "T5 TP-LEVEL": dict(tp=True)}


def jalan(nm):
    kw = VAR[nm]; a = time.time()
    if "tr" in kw: patch_trail(*kw["tr"])
    if "tp" in kw: patch_tp()
    try:
        df = _wf.run()
    finally:
        sb.Engine.step_check, sb.Engine.step_fill_exit, sb.tp1_price = ASLI_SC, ASLI_FE, ASLI_TP
    t = _wf.per_tahun(df)
    print(f"{nm:<18} n {len(df):5d} tot {df.R_REAL.sum():7.1f} DD {t0.maxdd(df.R_REAL.values):5.1f} avg {df.R_REAL.mean():+.3f} "
          f"win {(df.R_REAL > 0).mean() * 100:.0f}% · " + " ".join(f"{y % 100:02d}:{v:+.0f}" for y, v in t.items()) + f" · {time.time() - a:.0f}s", flush=True)
    return nm, df


# ------------------------------------------------------------------ (v) strategi mandiri tembus PWH/PWL
def tembus_pw(keluar, top=20, slot=5, sl_atr=1.5, tp_r=2.0, maks_h=120):
    pos, rows = {}, []
    times = sorted({t for d in rp.DATA.values() for t in d["T"]})
    sudah = {}                                                  # (coin, minggu, arah) yang sudah dipakai
    for t in times:
        for c in list(pos):                                     # kelola posisi di candle t
            i = rp.IDX[c].get(t)
            if i is None: continue
            D, p = rp.DATA[c], pos[c]
            if i < p["i_in"]: continue
            if i == p["i_in"]:
                p["e"] = D["O"][i]; p["sl"] = p["lv"] - p["d"] * p["r0x"]; p["r0"] = abs(p["e"] - p["sl"])
                if p["r0"] <= 0 or (p["e"] - p["sl"]) * p["d"] <= 0: del pos[c]; continue
            d, e, sl, r0 = p["d"], p["e"], p["sl"], p["r0"]
            H, L, O, C = D["H"][i], D["L"][i], D["O"][i], D["C"][i]
            ex = why = None
            if (d == 1 and L <= sl) or (d == -1 and H >= sl):
                ex = min(sl, O) if d == 1 else max(sl, O); why = "SL"
            elif keluar == "TP" and ((d == 1 and H >= e + tp_r * r0) or (d == -1 and L <= e - tp_r * r0)) and i > p["i_in"]:
                ex = e + d * tp_r * r0; why = "TP"
            elif keluar == "TP" and i - p["i_in"] >= maks_h:
                ex = C; why = "waktu"
            if ex is not None:
                rows.append(dict(coin=c, d=d, t_fill=int(D["T"][p["i_in"]]), t_exit=int(t), e=e, ex=ex, r0=r0, why=why)); del pos[c]; continue
            if keluar == "TRAIL" and (t // 3600) % 24 in sb.CHECK_HOURS_UTC and i - p["i_in"] >= 1:
                v = min(D["L"][i - sb.TRAIL + 1:i + 1]) if d == 1 else max(D["H"][i - sb.TRAIL + 1:i + 1])
                if (v - p["sl"]) * d > 0: p["sl"] = v
        U = _wf.UNI(t)[:top]
        for c in U:                                              # sinyal di close candle t → masuk open candle berikut
            if c in pos or len(pos) >= slot or c not in S.LV: continue
            i = rp.IDX[c].get(t)
            if i is None or i < 1300 or i + 1 >= len(rp.DATA[c]["T"]): continue
            D, Z = rp.DATA[c], S.LV[c]
            wk = (int(t) // 86400 + 3) // 7
            hi, lo, ad, Ci, Cp, ES = Z["WH"][i], Z["WL"][i], Z["AD1"][i], D["C"][i], D["C"][i - 1], D["ES"][i]
            if np.isnan(hi) or np.isnan(ad): continue
            for d, lv, cond in ((1, hi, Ci > hi and Cp <= hi and Ci > ES), (-1, lo, Ci < lo and Cp >= lo and Ci < ES)):
                if cond and (c, wk, d) not in sudah:
                    sudah[(c, wk, d)] = 1
                    pos[c] = dict(d=d, i_in=i + 1, lv=lv, r0x=sl_atr * ad); break
    df = pd.DataFrame(rows)
    fee = (REAL["taker"] + REAL["slip"]) * (df.e + df.ex) / df.r0
    fund = df.d * 0.0001 * ((df.t_exit - df.t_fill) / 28800) * df.e / df.r0
    df["R"] = (df.ex - df.e) * df.d / df.r0
    df["R_REAL"] = df.R - fee - fund
    df["year"] = pd.to_datetime(df.t_exit, unit="s").dt.year
    return df[df.year >= _wf.MULAI].sort_values("t_exit").reset_index(drop=True)


PVAR = {"P1 TEMBUS-PW TP2R": "TP", "P2 TEMBUS-PW TRAIL": "TRAIL"}


def runtun(v):
    best = cur = 0
    for x in v:
        cur = cur + 1 if x < 0 else 0; best = max(best, cur)
    return best


if __name__ == "__main__" and MODE != "wf":
    a = time.time()
    for c in rp.DATA: S.bangun(c)
    print(f"level SNR {len(S.LV)} koin · {time.time() - a:.0f}s", flush=True)
    hasil = dict(jalan(k) for k in VAR)            # berurutan (Pool macet karena memori 2,6 GB/proses)
    for nm, k in PVAR.items():
        df = tembus_pw(k); hasil[nm] = df
        t = _wf.per_tahun(df)
        print(f"{nm:<18} n {len(df):5d} tot {df.R_REAL.sum():7.1f} DD {t0.maxdd(df.R_REAL.values):5.1f} avg {df.R_REAL.mean():+.3f} "
              f"win {(df.R_REAL > 0).mean() * 100:.0f}% · " + " ".join(f"{y % 100:02d}:{v:+.0f}" for y, v in t.items()), flush=True)
    pickle.dump(hasil, open(f"{DATA}/sesi_1127.pkl", "wb"))
    j = hasil["juara"]
    print("\n== SARINGAN (periode pilih 2018-2021 saja) ==")
    rows = []
    for k in VAR:
        r = S.ringkas(hasil[k], k); r["runtun"] = runtun(hasil[k][hasil[k].year <= 2021].R_REAL.values); rows.append(r)
    for k in PVAR:
        r = S.ringkas(hasil[k], k + " (mandiri)"); r["runtun"] = runtun(hasil[k][hasil[k].year <= 2021].R_REAL.values); rows.append(r)
        g = S.gabung(j, hasil[k]); r = S.ringkas(g, k + " + juara"); r["runtun"] = runtun(g[g.year <= 2021].R_REAL.values); rows.append(r)
    print(pd.DataFrame(rows).round(3).to_string(index=False))
    m = lambda df: df[df.year <= 2021].groupby(pd.to_datetime(df.t_exit, unit="s").dt.to_period("M")).R_REAL.sum()
    for k in PVAR:
        x = pd.concat([m(j), m(hasil[k])], axis=1).fillna(0)
        print(f"korelasi bulanan {k} vs juara (2018-21): {x.corr().iloc[0, 1]:+.2f}")


if __name__ == "__main__" and MODE == "wf":
    hasil = pickle.load(open(f"{DATA}/sesi_1127.pkl", "rb")); j = hasil["juara"]
    keys = KUNCI or [k for k in VAR if k != "juara"][:2]
    out = {"skill": S.wf(hasil, "SKILL SNR (iv) " + ", ".join(keys), ["juara"] + keys)}
    for k in keys:
        out[k] = S.wf(hasil, f"{k} saja vs juara", ["juara", k])
        print(k, "P(tahun minus):", t0.p_minus(hasil[k]), "juara:", t0.p_minus(j), "· runtun 2020-skrg", runtun(hasil[k][hasil[k].year >= 2020].R_REAL.values),
              "juara", runtun(j[j.year >= 2020].R_REAL.values))
    pickle.dump(out, open(f"{DATA}/sesi_1127_wf.pkl", "wb"))
