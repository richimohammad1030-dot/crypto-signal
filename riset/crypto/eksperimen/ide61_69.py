"""Riset Jumat 20 Nov 2026 · walk-forward berlabuh (_wf.py, daftar sesuai masanya 2018-skrg, biaya REAL, replay penuh).

#61 Filter funding untuk SELL: masih perlu? (ide antri teratas, prioritas 1)
    Bot: SELL STOP hanya bila funding rata 72 jam > 0. Varian ambang funding (per 8 jam; HL per jam × 8):
    MATI (SELL selalu boleh bila koin punya funding/perp) · > -0,01% · > -0,003% · > 0 (juara) · > +0,003% · > +0,01%.
    Hipotesis: 2018 (tanpa arsip funding) SELL +83R → filter mungkin membuang SELL bagus; atau justru penyelamat 2021/2025.
    Sebelum arsip funding (sblm Sep 2019) / koin tanpa arsip Binance: SELL diizinkan (sama dengan _wf.fund_b) di semua varian.

#69 (ide baru, [lit] piramida Turtle — C. Faith, "Way of the Turtle", 2007, bab 'Adding units'): TAMBAH POSISI saat tren
    terbukti. Bila posisi sudah mencapai +L R (L = 2 atau 3) → tambah f × ukuran awal (f = 0,25 / 0,5) dengan order STOP di
    harga itu; tambahan ikut SL trailing posisi utama dan keluar bersama. Tidak memakai slot baru. Hipotesis: edge bot ada di
    ekor (2% trade terbaik = 34-80% R tahunan) → memperbesar trade yang sudah jalan menaikkan R/thn; risiko: koreksi dari
    puncak memakan tambahan (SL 72 candle lebar). Biaya tambahan: taker + slip masuk & keluar, funding aktual porsi tambahan.
    Risiko tambahan per trade dihitung (L + 1) × f R paling buruk bila SL belum bergeser (dilaporkan sebagai risiko terbuka).

Pemakaian: python ide61_69.py <repo> <data_lama>"""
import bisect, os, sys, time, pickle
import numpy as np, pandas as pd
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _wf
REPO, DATA = sys.argv[1], sys.argv[2]
_wf.load(REPO, DATA)
sb, t0, rp = _wf.sb, _wf.t0, _wf.rp
sys.path.insert(0, os.path.join(REPO, "riset")); import signifikansi as sig
ASLI_SFE, ASLI_BR, ASLI_FB = sb.Engine.step_fill_exit, sb.blended_R, _wf.fund_b
REAL = t0.SKEN["REAL"]


def fund8(c, t):
    """Funding rata 72 jam dalam satuan per 8 jam (Binance per settlement; HL per jam × 8). Pra-arsip = boleh."""
    ts, rs = rp.FUND.get(c, ([], []))
    a, b = bisect.bisect_right(ts, t - 72 * 3600), bisect.bisect_right(ts, t)
    if b - a >= 6: return sum(rs[a:b]) / (b - a)
    hts, hrs = rp.FUND_HL.get(c, ([], []))
    a2, b2 = bisect.bisect_right(hts, t - 72 * 3600), bisect.bisect_right(hts, t)
    if b2 - a2 >= 24: return 8 * sum(hrs[a2:b2]) / (b2 - a2)
    if not ts or t < ts[0]: return "pra"
    return None


def fb_ambang(thr):
    def f(c, t):
        v = fund8(c, t)
        if v is None: return None
        if v == "pra": return 1e-4
        if thr is None: return 1.0                       # MATI
        return v - thr
    return f


ADD = {}


def patch_add(L, fr):
    def sfe(self, coin, i, D):
        ASLI_SFE(self, coin, i, D)
        p = (self.s["coins"].get(coin) or {}).get("pos")
        if p is None or p[3] >= D["T"][i] or len(p) < 6 or not isinstance(p[5], dict) or p[5].get("add"): return
        d, e = p[0], p[1]; r0 = sb.pos_r0(p); lvl = e + d * L * r0
        if (d == 1 and D["H"][i] >= lvl) or (d == -1 and D["L"][i] <= lvl):
            px = max(lvl, D["O"][i]) if d == 1 else min(lvl, D["O"][i])
            p[5]["add"] = (px, fr, int(D["T"][i]))
            ADD[(coin, int(p[3]))] = (px, fr, int(D["T"][i]))

    def br(p, px):
        R = ASLI_BR(p, px); ext = sb.pos_ext(p)
        if ext.get("add"):
            ap, f, _ = ext["add"]; R += f * (px - ap) * p[0] / sb.pos_r0(p)
        return R
    sb.Engine.step_fill_exit = sfe; sb.blended_R = br


def biaya_add(df):
    """Kurangi fee & funding porsi tambahan dari R_REAL/R_KOTOR tetap = R mesin (sudah termasuk tambahan)."""
    fs = {}
    fee, fund, ada = [], [], []
    for x in df.itertuples():
        a = ADD.get((x.coin, int(x.t_fill)))
        if a is None: fee.append(0.0); fund.append(0.0); ada.append(False); continue
        ap, f, ta = a
        fee.append(f * (REAL["taker"] + REAL["slip"]) * (ap + x.ex) / x.r0)
        if x.coin not in fs: fs[x.coin] = t0.funding_series(x.coin)
        ft, frr = fs[x.coin]; D = rp.DATA[x.coin]
        s = 0.0
        for j in range(bisect.bisect_right(ft, ta), bisect.bisect_right(ft, x.t_exit)):
            k = bisect.bisect_right(D["T"], ft[j]) - 1
            s += f * frr[j] * x.d * D["C"][k] / x.r0
        fund.append(s); ada.append(True)
    df = df.copy(); df["add"] = ada
    df["R_REAL"] = df.R_REAL - np.array(fee) - np.array(fund)
    df["R_KONS"] = df.R_KONS - np.array(fee) * (0.0015 / 0.0008) - np.array(fund)
    return df


VAR = {"juara": {}}
for thr, nm in ((None, "MATI"), (-1e-4, "> -0,01%"), (-3e-5, "> -0,003%"), (3e-5, "> +0,003%"), (1e-4, "> +0,01%")):
    VAR[f"#61 {nm}"] = dict(thr=thr)
for L in (2.0, 3.0):
    for fr in (0.25, 0.5):
        VAR[f"#69 +{int(fr*100)}% @{L:.0f}R"] = dict(add=(L, fr))


def jalan(nm):
    kw = VAR[nm]; a = time.time(); ADD.clear()
    if "thr" in kw: _wf.fund_b = fb_ambang(kw["thr"])
    if "add" in kw: patch_add(*kw["add"])
    try:
        df = _wf.run()
        if "add" in kw: df = biaya_add(df)
    finally:
        sb.Engine.step_fill_exit, sb.blended_R, _wf.fund_b = ASLI_SFE, ASLI_BR, ASLI_FB
    t = _wf.per_tahun(df)
    print(f"{nm:<20} n {len(df):5d} tot {df.R_REAL.sum():7.1f} DD {t0.maxdd(df.R_REAL.values):5.1f} avg {df.R_REAL.mean():+.3f} "
          f"SELL {int((df.d == -1).sum())} · <1R {int((t < 1).sum())} · " + " ".join(f"{y % 100:02d}:{v:+.0f}" for y, v in t.items())
          + f" · {time.time() - a:.0f}s", flush=True)
    return nm, df


def ringkas(df, nm):
    t = _wf.per_tahun(df); u = df[df.year >= 2020]; k = max(1, int(round(len(u) * 0.02)))
    lama, baru = u[u.year <= 2023], u[u.year >= 2024]
    rs = lambda x: x.R_REAL.sum() / max(t0.maxdd(x.R_REAL.values), 1)
    return dict(nama=nm, n=len(u), R_thn=float(t[t.index >= 2020].mean()), avg=float(u.R_REAL.mean()), win=float((u.R_REAL > 0).mean() * 100),
                dd=t0.maxdd(u.R_REAL.values), rasio_lama=rs(lama), rasio_baru=rs(baru),
                tanpa2=float(np.sort(u.R_REAL.values)[:-k].sum()), kurang1=int((t[t.index >= 2020] < 1).sum()),
                terburuk=float(t[t.index >= 2020].min()), sd=float(t[(t.index >= 2020) & (t.index <= 2025)].std()),
                sell_n=int((u.d == -1).sum()), sell_avg=float(u[u.d == -1].R_REAL.mean()))


def wf(hasil, nama_grup, keys):
    tab, pilih, u = _wf.walk({k: hasil[k] for k in keys})
    j = hasil["juara"]; ju = j[j.year >= 2020]
    b = sig.banding([(int(x.t_exit), x.R_REAL) for x in ju.itertuples()], [(int(x.t_exit), x.R_REAL) for x in u.itertuples()], mulai=1577836800)
    print(f"\n== WALK-FORWARD {nama_grup} ({len(keys)} varian termasuk juara) ==")
    print("pilihan per jendela:", pilih)
    print("uji tersambung per tahun:", {int(y): round(float(r), 1) for y, r in tab.items()})
    print("juara per tahun        :", {int(y): round(float(r), 1) for y, r in _wf.per_tahun(ju).items()})
    print(f"tahun < +1R: {int((tab < 1).sum())} · terburuk {tab.min():+.1f} · R/thn {tab.mean():.1f} (juara {_wf.per_tahun(ju).mean():.1f}) · "
          f"DD uji {t0.maxdd(u.R_REAL.values):.1f} (juara {t0.maxdd(ju.R_REAL.values):.1f})")
    print("signifikansi (uji tersambung vs juara, 2020-skrg):", b)
    return dict(pilih=pilih, tab=tab, sig=b, u=u)


if __name__ == "__main__":
    with Pool(2) as pool:
        hasil = dict(pool.map(jalan, list(VAR), chunksize=1))
    pickle.dump(hasil, open(f"{DATA}/ide61_69.pkl", "wb"))
    out = {"ringkas": [ringkas(df, k) for k, df in hasil.items()]}
    print("\n" + pd.DataFrame(out["ringkas"]).round(3).to_string(index=False))
    for k, df in hasil.items():
        if k.startswith("#69"):
            u = df[df.year >= 2020]
            print(f"{k}: trade dgn tambahan {int(u['add'].sum())} ({u['add'].mean() * 100:.0f}%), R rata trade bertambah "
                  f"{u[u['add']].R_REAL.mean():+.2f}, tanpa tambahan {u[~u['add']].R_REAL.mean():+.2f}")
    out["wf61"] = wf(hasil, "#61 funding SELL", ["juara"] + [k for k in hasil if k.startswith("#61")])
    out["wf69"] = wf(hasil, "#69 piramida", ["juara"] + [k for k in hasil if k.startswith("#69")])
    pickle.dump(out, open(f"{DATA}/ide61_69_wf.pkl", "wb"))
