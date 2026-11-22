"""KURIKULUM SKILL 1 · SNR · TAHAP 1 PAHAM putaran 2/3 (sesi riset Senin 23 Nov 2026, PROGRAM KILAT).
Definisi baru (dari putaran 1, skill_snr_t1.py) + uji KE ARAH MANA PUN (pantul ATAU tembus lebih sering dari acak):
  - Supply-demand H4/D1 dengan impuls 1,5 / 2 / 3 ATR, SENTUHAN PERTAMA saja (zona segar) vs sentuhan berikutnya.
  - Konfluensi: candle menyentuh >= 2 JENIS berbeda (SWING / PERIODE / BULAT / SUPDEM) di sisi yang sama pada candle itu.
  - Semua jenis (swing H4/D1, PDH/PDL, PWH/PWL, bulat, supdem) diuji ulang dengan horizon pendek 3 & 6 jam, ambang
    pantul 0,5 ATR (tembus tetap 0,5 ATR di balik tepi jauh) + horizon lama 12 jam/1 ATR sebagai pembanding.
Peristiwa, pembanding acak, dan bootstrap blok bulanan sama dengan putaran 1.
Vonis per kelompok (4 sel = 2004-14/2015-26 × support/resistance):
  PANTUL  = lift > 0 dan P(lift > 0) >= 0,90 di 4 sel;  TEMBUS = lift < 0 dan P(lift > 0) <= 0,10 di 4 sel.
Pemakaian: python skill_snr_t1b.py <xau_2004.json>"""
import sys, time
import numpy as np
sys.path.insert(0, ".")
import audit_mesin as m
import skill_snr as sk

t_ = time.time()
D = m.muat(sys.argv[1]); T, O, H, L, C = D
Ah = np.array(m.atr(list(H), list(L), list(C), 14)); N = len(T)
Z, B = sk.bangun(D)
for imp in (1.5, 3.0):                                   # supdem tambahan, diberi label impuls
    for tf in ("H4", "D1"):
        for z in sk.zona_supdem(B[tf], tf, impuls=imp):
            z["jenis"] = z["jenis"] + f"{int(imp * 10)}"; Z.append(z)
ev = sk.sentuhan(Z, D)
print(f"Data {N} candle {m.wib(T[0]):%Y-%m-%d} s.d. {m.wib(T[-1]):%Y-%m-%d}; zona {len(Z)}; sentuhan {len(ev)} ({time.time() - t_:.0f} dtk)")

KMAX = 12
I = np.array([e[0] for e in ev]); S = np.array([e[2] for e in ev])
LO = np.array([e[3]["lo"] for e in ev]); HI = np.array([e[3]["hi"] for e in ev])
KEY = np.array([e[1] for e in ev]).astype(str)
def kategori(k):
    if k.startswith("SWING"): return "SWING"
    if k.startswith(("PD", "PW")): return "PERIODE"
    if k.startswith("BULAT"): return "BULAT"
    return "SUPDEM"
CAT = np.array([kategori(k) for k in KEY])
# segar = sentuhan pertama zona supdem
seen = set(); SEGAR = np.zeros(len(ev), bool)
for n_, e in enumerate(ev):
    if e[1].startswith(("DEMAND", "SUPPLY")):
        k_ = id(e[3])
        if k_ not in seen: SEGAR[n_] = True; seen.add(k_)
# konfluensi = jumlah kategori berbeda (impuls 1,5/3 tidak dihitung ganda: kategori SUPDEM sama) pada candle & sisi yang sama
from collections import defaultdict
kat = defaultdict(set)
for n_ in range(len(ev)): kat[(I[n_], S[n_])].add(CAT[n_])
NK = np.array([len(kat[(I[n_], S[n_])]) for n_ in range(len(ev))])

a = Ah[I - 1]
keep = (I + KMAX < N) & np.isfinite(a) & (a > 0)
I, S, LO, HI, KEY, CAT, SEGAR, NK, a = I[keep], S[keep], LO[keep], HI[keep], KEY[keep], CAT[keep], SEGAR[keep], NK[keep], a[keep]
EDGE = np.where(S == 1, HI, LO); FAR = np.where(S == 1, LO, HI)
dist = (O[I] - EDGE) * S / a; wid = (HI - LO) / a
YR = np.array([m.wib(t).year for t in T]); MON = YR * 12 + np.array([m.wib(t).month for t in T])

def hasil(i, s, edge, far, a, K, pb, pt=0.5):
    off = np.arange(K + 1)
    hh = H[i[:, None] + off]; ll = L[i[:, None] + off]
    up = np.where(s[:, None] == 1, hh, -ll); dn = np.where(s[:, None] == 1, ll, -hh)
    e = (edge * s)[:, None]; f = (far * s)[:, None]; aa = a[:, None]
    pen = dn <= f - pt * aa; bnc = up >= e + pb * aa; bnc[:, 0] = False
    BIG = K + 5
    fp = np.where(pen.any(1), pen.argmax(1), BIG); fb = np.where(bnc.any(1), bnc.argmax(1), BIG)
    return np.where(fb < fp, 1, np.where(fp < BIG, 0, -1))

# pembanding acak (sama dengan putaran 1)
rng = np.random.default_rng(11)
yrs = np.unique(YR); CI = np.full(len(I), -1)
for y in yrs:
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
print(f"Pembanding acak cocok: {cm.mean() * 100:.1f}%")

HOR = {"3j/0,5": (3, 0.5), "6j/0,5": (6, 0.5), "12j/1,0": (12, 1.0)}
KODE = {h: hasil(I, S, EDGE, FAR, a, K, pb) for h, (K, pb) in HOR.items()}
CK = {h: np.where(cm, hasil(np.maximum(CI, 0), S, cedge, cfar, ac, K, pb), -1) for h, (K, pb) in HOR.items()}

def uji(mask, kode, ck, nboot=1500, cmask=None):
    cmask = mask if cmask is None else cmask
    mk = MON[I[mask]]; u, inv = np.unique(mk, return_inverse=True)
    rb = np.bincount(inv, kode[mask] == 1, len(u)); rd = np.bincount(inv, kode[mask] >= 0, len(u))
    pos = {v: k for k, v in enumerate(u)}; ci = np.array([pos.get(v, -1) for v in MON[I[cmask]]]); okc = ci >= 0
    cb = np.bincount(ci[okc], (ck[cmask] == 1)[okc], len(u)); cd = np.bincount(ci[okc], (ck[cmask] >= 0)[okc], len(u))
    if rd.sum() < 30 or cd.sum() < 30: return None
    b = rng.integers(0, len(u), (nboot, len(u)))
    lift = rb[b].sum(1) / np.maximum(rd[b].sum(1), 1) - cb[b].sum(1) / np.maximum(cd[b].sum(1), 1)
    return dict(n=int(rd.sum()), lift=rb.sum() / rd.sum() - cb.sum() / cd.sum(), P=float((lift > 0).mean()))

PER = {"04-14": YR[I] <= 2014, "15-26": YR[I] >= 2015}; ARAH = {"sup": S == 1, "res": S == -1}
VONIS = {}
def grup(nama, mask, cmask=None):
    cmask = mask if cmask is None else cmask
    baris = []
    for h in HOR:
        r = {(p, ar): uji(mask & pm & am, KODE[h], CK[h], cmask=cmask & pm & am) for p, pm in PER.items() for ar, am in ARAH.items()}
        ok = all(x is not None for x in r.values())
        v = "PANTUL" if ok and all(x["lift"] > 0 and x["P"] >= 0.9 for x in r.values()) else \
            "TEMBUS" if ok and all(x["lift"] < 0 and x["P"] <= 0.1 for x in r.values()) else "-"
        VONIS[(nama, h)] = (v, r)
        sel = " ".join(f"{x['lift'] * 100:+4.1f}/{x['P']:.2f}" if x else "n<30" for x in r.values())
        nmin = min((x["n"] for x in r.values() if x), default=0)
        baris.append(f"{h} {v:<6} [{sel}] nmin {nmin}")
    print(f"  {nama:<22} " + " | ".join(baris))

print("\nLift peluang pantul (poin %) / P(lift>0), sel: 04-14 sup, 04-14 res, 15-26 sup, 15-26 res")
print("Per jenis-tf (semua sentuhan):")
for k in sorted(set(KEY)): grup(k, KEY == k)
print("Supply-demand SENTUHAN PERTAMA (segar) per impuls & tf:")
for imp, suf in (("1,5", "15"), ("2,0", ""), ("3,0", "30")):
    for tf in ("H4", "D1"):
        kk = np.isin(KEY, [f"DEMAND{suf}-{tf}", f"SUPPLY{suf}-{tf}"])
        grup(f"SUPDEM{imp} {tf} segar", kk & SEGAR); grup(f"SUPDEM{imp} {tf} lama", kk & ~SEGAR)
# konfluensi yang ADIL untuk pembanding acak: candle acak j dihitung menyentuh level nyata kategori lain di sisi yang sama
# (tanpa ini, "sendiri" = candle kecil dan "konfluensi" = candle besar -> bias seleksi; putaran 2 awal sempat tertipu ini)
NKC = np.array([len(kat.get((int(j), int(s_)), set()) | {c}) if j >= 0 else 0 for j, s_, c in zip(CI, S, CAT)])
print("Per kategori & konfluensi (pembanding acak dengan syarat konfluensi yang sama):")
for c in ("SWING", "PERIODE", "BULAT", "SUPDEM"):
    grup(f"{c} sendiri", (CAT == c) & (NK == 1), (CAT == c) & (NKC == 1))
    grup(f"{c} konfluensi>=2", (CAT == c) & (NK >= 2), (CAT == c) & (NKC >= 2))
grup("KONFLUENSI>=2 semua", NK >= 2, NKC >= 2); grup("KONFLUENSI>=3 semua", NK >= 3, NKC >= 3)
print("  (versi BIAS, pembanding tanpa syarat konfluensi, hanya untuk catatan:)")
grup("  bias SWING sendiri", (CAT == "SWING") & (NK == 1))
lulus = [(k, v[0]) for k, v in VONIS.items() if v[0] != "-"]
print(f"\nLULUS PAHAM (arah mana pun): {len(lulus)} dari {len(VONIS)} kelompok×horizon")
for (nm, h), v in lulus: print(f"  {nm} · {h} · {v}")
print(f"waktu {time.time() - t_:.0f} dtk")
