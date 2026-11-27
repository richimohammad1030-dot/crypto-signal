"""KURIKULUM SKILL 1 · SNR · FX MAJOR · TAHAP 0 (definisi) + TAHAP 1 PAHAM (sesi 27 Nov 2026, dimajukan dari 29 Nov).
Memakai ulang definisi XAU (riset/xau/eksperimen/skill_snr.py: SWING n=2/3/5 H4&D1, PDH/PDL, PWH/PWL, SUPDEM 1,5/2/3 ATR)
dan uji pembanding acak ADIL dari skill_snr_t1b.py (candle acak juga harus menyentuh level semu di jarak yang sama; konfluensi
pembanding dihitung terhadap level nyata kategori lain). Penyesuaian FX: harga diskalakan ke pip (1/pip) sehingga angka bulat
= kelipatan 50 & 100 pip (JPY 0,50/1,00). Hari 07:00-07:00 WIB = hari UTC (sama dgn XAU).
Data Dukascopy H1 2015-2026, 7 pair. Periode uji = 2015-2020 DAN 2021-2026. Bootstrap blok bulanan (bulan kalender sama
untuk semua pair, korelasi antar-pair tetap di dalam blok).
Vonis per kelompok (4 sel = 2 periode × support/resistance):
  PANTUL = lift > 0 dan P(lift>0) >= 0,90 di 4 sel;  TEMBUS = lift < 0 dan P <= 0,10 di 4 sel.
Tambahan FX: hasil per pair untuk kelompok yang lulus (konsisten >= 5/7 pair searah).
Pemakaian: python riset/fx/eksperimen/skill_snr_fx_t1.py [PAIR ...]"""
import os, sys, time, pickle
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "riset", "xau", "eksperimen")); sys.path.insert(0, os.path.join(REPO, "forex_major"))
import numpy as np
os.chdir(os.path.join(REPO, "forex_major"))
import backtest as B
import audit_mesin as m
import skill_snr as sk

PAIRS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD"]
KMAX = 12
HOR = {"3j/0,5": (3, 0.5), "6j/0,5": (6, 0.5), "12j/1,0": (12, 1.0)}


def kategori(k):
    if k.startswith("SWING"): return "SWING"
    if k.startswith(("PD", "PW")): return "PERIODE"
    if k.startswith("BULAT"): return "BULAT"
    return "SUPDEM"


def hasil(H, L, i, s, edge, far, a, K, pb, pt=0.5):
    off = np.arange(K + 1)
    hh = H[i[:, None] + off]; ll = L[i[:, None] + off]
    up = np.where(s[:, None] == 1, hh, -ll); dn = np.where(s[:, None] == 1, ll, -hh)
    e = (edge * s)[:, None]; f = (far * s)[:, None]; aa = a[:, None]
    pen = dn <= f - pt * aa; bnc = up >= e + pb * aa; bnc[:, 0] = False
    BIG = K + 5
    fp = np.where(pen.any(1), pen.argmax(1), BIG); fb = np.where(bnc.any(1), bnc.argmax(1), BIG)
    return np.where(fb < fp, 1, np.where(fp < BIG, 0, -1))


def per_pair(pair, seed=11):
    t_ = time.time()
    P = B.load(pair); sc = 1.0 / B.PIP[pair]
    T = P.h1["t"].astype(float); O, H, L, C = (P.h1[k] * sc for k in "ohlc")
    D = [T, O, H, L, C]
    Z, Bk = sk.bangun(D)
    for imp in (1.5, 3.0):
        for tf in ("H4", "D1"):
            for z in sk.zona_supdem(Bk[tf], tf, impuls=imp):
                z["jenis"] = z["jenis"] + f"{int(imp * 10)}"; Z.append(z)
    cek = sk.cek_tanpa_masa_depan(Z, D)
    ev = sk.sentuhan(Z, D, bulat=(50, 100))
    N = len(T); Ah = np.array(m.atr(list(H), list(L), list(C), 14))
    I = np.array([e[0] for e in ev]); S = np.array([e[2] for e in ev])
    LO = np.array([e[3]["lo"] for e in ev]); HI = np.array([e[3]["hi"] for e in ev])
    KEY = np.array([e[1] for e in ev]).astype(str); CAT = np.array([kategori(k) for k in KEY])
    seen = set(); SEGAR = np.zeros(len(ev), bool)
    for n_, e in enumerate(ev):
        if e[1].startswith(("DEMAND", "SUPPLY")):
            k_ = id(e[3])
            if k_ not in seen: SEGAR[n_] = True; seen.add(k_)
    kat = defaultdict(set)
    for n_ in range(len(ev)): kat[(I[n_], S[n_])].add(CAT[n_])
    NK = np.array([len(kat[(I[n_], S[n_])]) for n_ in range(len(ev))])
    a = Ah[I - 1]
    keep = (I + KMAX < N) & np.isfinite(a) & (a > 0)
    I, S, LO, HI, KEY, CAT, SEGAR, NK, a = I[keep], S[keep], LO[keep], HI[keep], KEY[keep], CAT[keep], SEGAR[keep], NK[keep], a[keep]
    EDGE = np.where(S == 1, HI, LO); FAR = np.where(S == 1, LO, HI)
    dist = (O[I] - EDGE) * S / a; wid = (HI - LO) / a
    YR = np.array([m.wib(t).year for t in T]); MON = YR * 12 + np.array([m.wib(t).month for t in T])
    rng = np.random.default_rng(seed); CI = np.full(len(I), -1)
    for y in np.unique(YR):
        sel = np.flatnonzero(YR[I] == y)
        pool = np.flatnonzero((YR == y) & (np.arange(N) > 20) & (np.arange(N) < N - KMAX - 1))
        sisa = sel.copy()
        for _ in range(40):
            if not len(sisa) or not len(pool): break
            j = pool[rng.integers(0, len(pool), len(sisa))]; aj = Ah[j - 1]
            lvl = O[j] - S[sisa] * dist[sisa] * aj
            ok = np.isfinite(aj) & (aj > 0) & np.where(S[sisa] == 1, L[j] <= lvl + 0.1 * aj, H[j] >= lvl - 0.1 * aj)
            CI[sisa[ok]] = j[ok]; sisa = sisa[~ok]
    cm = CI >= 0
    ac = np.where(cm, Ah[np.maximum(CI, 1) - 1], 1.0)
    cedge = np.where(cm, O[np.maximum(CI, 0)] - S * dist * ac, 0.0); cfar = cedge - S * wid * ac
    KODE = {h: hasil(H, L, I, S, EDGE, FAR, a, K, pb) for h, (K, pb) in HOR.items()}
    CK = {h: np.where(cm, hasil(H, L, np.maximum(CI, 0), S, cedge, cfar, ac, K, pb), -1) for h, (K, pb) in HOR.items()}
    NKC = np.array([len(kat.get((int(j), int(s_)), set()) | {c}) if j >= 0 else 0 for j, s_, c in zip(CI, S, CAT)])
    njenis = defaultdict(int)
    for z in Z: njenis[z["jenis"] + "-" + z["tf"]] += 1
    out = dict(pair=pair, S=S, KEY=KEY, CAT=CAT, SEGAR=SEGAR, NK=NK, NKC=NKC, YR=YR[I], MON=MON[I], KODE=KODE, CK=CK,
               cm=cm.mean(), nzona=len(Z), njenis=dict(njenis), cek=cek, nev=len(I), hari=len(np.unique(T // 86400)),
               periode=(m.wib(T[0]).strftime("%Y-%m-%d"), m.wib(T[-1]).strftime("%Y-%m-%d")), dtk=time.time() - t_)
    return out


def uji(R, mask, h, rng, nboot=1500, cmask=None):
    cmask = mask if cmask is None else cmask
    kode, ck, MON = R["KODE"][h], R["CK"][h], R["MON"]
    mk = MON[mask]; u, inv = np.unique(mk, return_inverse=True)
    rb = np.bincount(inv, kode[mask] == 1, len(u)); rd = np.bincount(inv, kode[mask] >= 0, len(u))
    pos = {v: k for k, v in enumerate(u)}; ci = np.array([pos.get(v, -1) for v in MON[cmask]], dtype=int); okc = ci >= 0
    cb = np.bincount(ci[okc], (ck[cmask] == 1)[okc], len(u)); cd = np.bincount(ci[okc], (ck[cmask] >= 0)[okc], len(u))
    if rd.sum() < 30 or cd.sum() < 30: return None
    b = rng.integers(0, len(u), (nboot, len(u)))
    lift = rb[b].sum(1) / np.maximum(rd[b].sum(1), 1) - cb[b].sum(1) / np.maximum(cd[b].sum(1), 1)
    return dict(n=int(rd.sum()), lift=rb.sum() / rd.sum() - cb.sum() / cd.sum(), P=float((lift > 0).mean()))


def gabung(rs):
    R = {k: np.concatenate([r[k] for r in rs]) for k in ("S", "KEY", "CAT", "SEGAR", "NK", "NKC", "YR", "MON")}
    R["PAIR"] = np.concatenate([np.full(r["nev"], r["pair"]) for r in rs])
    R["KODE"] = {h: np.concatenate([r["KODE"][h] for r in rs]) for h in HOR}
    R["CK"] = {h: np.concatenate([r["CK"][h] for r in rs]) for h in HOR}
    return R


def main(pairs):
    t0 = time.time(); cache = "/tmp/fx_snr_t1.pkl"; rs = {}
    if os.path.exists(cache): rs = pickle.load(open(cache, "rb"))
    for p in pairs:
        if p not in rs:
            rs[p] = per_pair(p); pickle.dump(rs, open(cache, "wb"))
        r = rs[p]
        print(f"{p}: {r['periode'][0]}..{r['periode'][1]} zona {r['nzona']} sentuhan {r['nev']} ({r['nev'] / r['hari']:.1f}/hari) "
              f"acak cocok {r['cm'] * 100:.0f}% · cek masa depan {r['cek']} pelanggaran · {r['dtk']:.0f} dtk")
    R = gabung([rs[p] for p in pairs]); rng = np.random.default_rng(7)
    PER = {"15-20": R["YR"] <= 2020, "21-26": R["YR"] >= 2021}; ARAH = {"sup": R["S"] == 1, "res": R["S"] == -1}
    VONIS = {}

    def grup(nama, mask, cmask=None):
        cmask = mask if cmask is None else cmask; baris = []
        for h in HOR:
            r = {(p, ar): uji(R, mask & pm & am, h, rng, cmask=cmask & pm & am) for p, pm in PER.items() for ar, am in ARAH.items()}
            ok = all(x is not None for x in r.values())
            v = "PANTUL" if ok and all(x["lift"] > 0 and x["P"] >= 0.9 for x in r.values()) else \
                "TEMBUS" if ok and all(x["lift"] < 0 and x["P"] <= 0.1 for x in r.values()) else "-"
            VONIS[(nama, h)] = (v, r, mask, cmask)
            sel = " ".join(f"{x['lift'] * 100:+4.1f}/{x['P']:.2f}" if x else "n<30" for x in r.values())
            nmin = min((x["n"] for x in r.values() if x), default=0)
            baris.append(f"{h} {v:<6} [{sel}] n{nmin}")
        print(f"  {nama:<24} " + " | ".join(baris))

    KEY, CAT, NK, NKC, SEGAR = R["KEY"], R["CAT"], R["NK"], R["NKC"], R["SEGAR"]
    print("\nLift peluang pantul (poin %) / P(lift>0), sel: 15-20 sup, 15-20 res, 21-26 sup, 21-26 res")
    print("Per jenis-tf (semua sentuhan):")
    for k in sorted(set(KEY)): grup(k, KEY == k)
    print("Supply-demand SENTUHAN PERTAMA (segar):")
    for imp, suf in (("1,5", "15"), ("2,0", ""), ("3,0", "30")):
        for tf in ("H4", "D1"):
            kk = np.isin(KEY, [f"DEMAND{suf}-{tf}", f"SUPPLY{suf}-{tf}"])
            grup(f"SUPDEM{imp} {tf} segar", kk & SEGAR)
    print("Per kategori & konfluensi (pembanding adil):")
    for c in ("SWING", "PERIODE", "BULAT", "SUPDEM"):
        grup(f"{c} sendiri", (CAT == c) & (NK == 1), (CAT == c) & (NKC == 1))
        grup(f"{c} konfl>=2", (CAT == c) & (NK >= 2), (CAT == c) & (NKC >= 2))
    grup("KONFLUENSI>=2 semua", NK >= 2, NKC >= 2); grup("KONFLUENSI>=3 semua", NK >= 3, NKC >= 3)
    lulus = [(k, v) for k, v in VONIS.items() if v[0] != "-"]
    print(f"\nLULUS PAHAM (4 sel, arah mana pun): {len(lulus)} dari {len(VONIS)} kelompok×horizon")
    for (nm, h), (v, r, mask, cmask) in lulus:
        sgn = 1 if v == "PANTUL" else -1; per = []
        for p in pairs:
            pm = R["PAIR"] == p; x = uji(R, mask & pm, h, rng, nboot=500, cmask=cmask & pm)
            per.append((p, x))
        cocok = sum(1 for _, x in per if x and sgn * x["lift"] > 0)
        rata = np.mean([x["lift"] for x in r.values()]) * 100
        print(f"  {nm} · {h} · {v} · lift rata {rata:+.1f} poin · searah di {cocok}/{len(pairs)} pair: "
              + " ".join(f"{p[:3]}{p[3:6].lower()} {x['lift'] * 100:+.1f}" if x else f"{p} n<30" for p, x in per))
    print(f"waktu total {time.time() - t0:.0f} dtk")


if __name__ == "__main__":
    main(sys.argv[1:] or PAIRS)
