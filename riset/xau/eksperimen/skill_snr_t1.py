"""KURIKULUM SKILL 1 · SNR · TAHAP 1 = PAHAM (riset Jumat 20 Nov 2026). Apakah level SNR (skill_snr.py, tahap 0) NYATA:
harga lebih sering MEMANTUL di level dibanding level ACAK pembanding?
Peristiwa  = sentuhan skill_snr.sentuhan (candle H1 open di luar zona > 0,1 ATR, high/low masuk <= 0,1 ATR dari tepi zona).
Hasil (12 candle H1, a = ATR14 H1 candle sebelumnya), contoh support (datang dari atas; resistance = cermin):
  PANTUL = high candle i+1..i+12 >= tepi_dekat + 1 ATR SEBELUM low candle i..i+12 <= tepi_jauh - 0,5 ATR
  TEMBUS = tembus lebih dulu (candle yang memenuhi keduanya dihitung TEMBUS, konservatif); NETRAL = tidak keduanya.
  Peluang pantul = PANTUL / (PANTUL + TEMBUS). LANJUT (setelah TEMBUS) = low <= tepi_jauh - 1,5 ATR dalam 12 candle.
Pembanding acak (waktu acak, sebaran jarak sama): tiap peristiwa nyata (candle i, jarak open-tepi d ATR, lebar zona w ATR,
  arah sama) dipasangkan dengan candle acak j di TAHUN yang sama; level semu = open_j -/+ d x ATR_j dengan lebar w x ATR_j;
  dipakai bila candle j juga menyentuhnya (syarat sentuhan sama). Hasil diukur dengan aturan yang sama.
Lift = peluang pantul nyata - acak. P = bootstrap blok BULANAN (2.000x) peluang lift > 0. Lulus PAHAM (KURIKULUM): P >= 0,90
di 2004-2014 DAN 2015-2026, untuk KEDUA arah (support & resistance), per jenis. Juga dilaporkan per timeframe & kekuatan,
zona supply-demand segar (sentuhan pertama) vs sudah disentuh, dan LANJUT setelah tembus zona kuat (swing kuat >= 3).
Pemakaian: python skill_snr_t1.py <xau_2004.json>"""
import sys, time
import numpy as np
sys.path.insert(0, ".")
import audit_mesin as m
import skill_snr as sk

t_ = time.time()
D = m.muat(sys.argv[1]); T, O, H, L, C = D
Ah = np.array(m.atr(list(H), list(L), list(C), 14)); N = len(T)
Z, B = sk.bangun(D)
ev = sk.sentuhan(Z, D)
print(f"Data {len(T)} candle {m.wib(T[0]):%Y-%m-%d} s.d. {m.wib(T[-1]):%Y-%m-%d}; zona {len(Z)}; sentuhan {len(ev)} ({time.time() - t_:.0f} dtk)")

K = 12
# ---- susun array peristiwa nyata ----
I = np.array([e[0] for e in ev]); S = np.array([e[2] for e in ev])
LO = np.array([e[3]["lo"] for e in ev]); HI = np.array([e[3]["hi"] for e in ev])
KEY = np.array([e[1] for e in ev])
KUAT = np.array([e[3].get("kuat", 1) for e in ev])
seen = set(); SEGAR = np.zeros(len(ev), bool)
for n_, e in enumerate(ev):
    z = e[3]
    if e[1].startswith(("DEMAND", "SUPPLY")):
        k_ = id(z)
        if k_ not in seen: SEGAR[n_] = True; seen.add(k_)
a = Ah[I - 1]
keep = (I + K < N) & np.isfinite(a) & (a > 0)
I, S, LO, HI, KEY, KUAT, SEGAR, a = I[keep], S[keep], LO[keep], HI[keep], KEY[keep], KUAT[keep], SEGAR[keep], a[keep]
EDGE = np.where(S == 1, HI, LO); FAR = np.where(S == 1, LO, HI)
dist = (O[I] - EDGE) * S / a                 # > 0,1 (datang dari luar)
wid = (HI - LO) / a
YR = np.array([m.wib(t).year for t in T])
MON = np.array([m.wib(t).year * 12 + m.wib(t).month for t in T])

def hasil(i, s, edge, far, a):
    """Vektor: kode 1 = PANTUL, 0 = TEMBUS, -1 = NETRAL; lanjut = bool (tembus lanjut 1,5 ATR)."""
    off = np.arange(K + 1)
    hh = H[i[:, None] + off]; ll = L[i[:, None] + off]
    up = np.where(s[:, None] == 1, hh, -ll); dn = np.where(s[:, None] == 1, ll, -hh)    # orientasi: arah pantul = naik
    e = (edge * s)[:, None]; f = (far * s)[:, None]; aa = a[:, None]
    pen = dn <= f - 0.5 * aa; bnc = up >= e + aa; bnc[:, 0] = False
    BIG = K + 5
    fp = np.where(pen.any(1), pen.argmax(1), BIG); fb = np.where(bnc.any(1), bnc.argmax(1), BIG)
    kode = np.where(fb < fp, 1, np.where(fp < BIG, 0, -1))
    lanjut = (dn <= f - 1.5 * aa).any(1)
    return kode, lanjut

kode, lanjut = hasil(I, S, EDGE, FAR, a)

# ---- pembanding acak ----
rng = np.random.default_rng(11)
yrs = np.unique(YR); idx_th = {y: np.flatnonzero((YR == y) & (np.arange(N) > 20) & (np.arange(N) < N - K - 1)) for y in yrs}
CI = np.full(len(I), -1)
for y in yrs:
    sel = np.flatnonzero(YR[I] == y); pool = idx_th[y]
    if not len(sel): continue
    sisa = sel.copy()
    for _ in range(40):
        if not len(sisa): break
        j = pool[rng.integers(0, len(pool), len(sisa))]; aj = Ah[j - 1]
        lvl = O[j] - S[sisa] * dist[sisa] * aj          # tepi dekat semu
        ok = np.isfinite(aj) & (aj > 0) & np.where(S[sisa] == 1, L[j] <= lvl + 0.1 * aj, H[j] >= lvl - 0.1 * aj)
        CI[sisa[ok]] = j[ok]; sisa = sisa[~ok]
cm = CI >= 0
ac = np.where(cm, Ah[np.maximum(CI, 1) - 1], 1.0)
cedge = np.where(cm, O[np.maximum(CI, 0)] - S * dist * ac, 0.0)
cfar = cedge - S * wid * ac
ck, cl = hasil(np.maximum(CI, 0), S, cedge, cfar, ac)
ck = np.where(cm, ck, -1)
print(f"Pembanding acak cocok: {cm.mean() * 100:.1f}% peristiwa")

def uji(mask, nboot=2000):
    """Peluang pantul nyata vs acak + P bootstrap blok bulanan."""
    mk = MON[I[mask]]; u, inv = np.unique(mk, return_inverse=True)
    rb = np.bincount(inv, (kode[mask] == 1), len(u)); rd = np.bincount(inv, (kode[mask] >= 0), len(u))
    cb = np.bincount(inv, (ck[mask] == 1), len(u)); cd = np.bincount(inv, (ck[mask] >= 0), len(u))
    if rd.sum() < 30 or cd.sum() < 30: return None
    pr, pc = rb.sum() / rd.sum(), cb.sum() / cd.sum()
    b = rng.integers(0, len(u), (nboot, len(u)))
    lift = rb[b].sum(1) / np.maximum(rd[b].sum(1), 1) - cb[b].sum(1) / np.maximum(cd[b].sum(1), 1)
    return dict(n=int(rd.sum()), pr=pr, pc=pc, lift=pr - pc, P=float((lift > 0).mean()))

PER = {"2004-14": YR[I] <= 2014, "2015-26": YR[I] >= 2015}
ARAH = {"sup": S == 1, "res": S == -1}
def grup(nama, mask, cetak=True):
    hasil_ = {}
    for pn, pm in PER.items():
        for an, am in ARAH.items():
            hasil_[(pn, an)] = uji(mask & pm & am)
    lulus = all(r is not None and r["P"] >= 0.90 and r["lift"] > 0 for r in hasil_.values())
    nyata_bal = all(r is not None and r["P"] <= 0.10 for r in hasil_.values())
    if cetak:
        s = " | ".join(f"{pn} {an}: " + (f"{r['pr'] * 100:4.1f}% vs {r['pc'] * 100:4.1f}% ({r['lift'] * 100:+4.1f}) P {r['P']:.2f} n {r['n']}" if r else "n<30")
                       for (pn, an), r in hasil_.items())
        print(f"  {nama:<16} {'LULUS' if lulus else ('TERBALIK' if nyata_bal else '-'):<8} {s}")
    return lulus, hasil_

print(f"\nPeluang PANTUL (vs TEMBUS) nyata vs acak, lift (poin %), P bootstrap bulanan. Lulus = P >= 0,90 di 4 sel.")
print("Per jenis-tf:")
REKAP = {}
for k in sorted(set(KEY)):
    REKAP[k] = grup(k, KEY == k)
print("Per JENIS (gabungan tf):")
JEN = {"SWING": np.char.startswith(KEY.astype(str), "SWING"), "PERIODE": np.isin(KEY, ["PDH-PD", "PDL-PD", "PWH-PW", "PWL-PW"]),
       "BULAT": np.char.startswith(KEY.astype(str), "BULAT"), "SUPDEM": np.char.startswith(KEY.astype(str), "DEMAND") | np.char.startswith(KEY.astype(str), "SUPPLY")}
REKAP_J = {nm: grup(nm, mk) for nm, mk in JEN.items()}
print("Swing per timeframe & kekuatan:")
for tf in ("H4", "D1"):
    for kk, km in (("kuat1", KUAT == 1), ("kuat2", KUAT == 2), ("kuat3+", KUAT >= 3)):
        grup(f"SWING {tf} {kk}", JEN["SWING"] & np.char.endswith(KEY.astype(str), tf) & km)
print("Supply-demand segar vs sudah disentuh:")
grup("SUPDEM segar", JEN["SUPDEM"] & SEGAR); grup("SUPDEM lama", JEN["SUPDEM"] & ~SEGAR)
print("Semua peristiwa:"); grup("SEMUA", np.ones(len(I), bool))

print("\nLANJUT setelah TEMBUS (low <= tepi jauh - 1,5 ATR dalam 12 candle | tembus), nyata vs acak:")
for nm, mk in (("SWING kuat3+", JEN["SWING"] & (KUAT >= 3)), ("SWING D1", JEN["SWING"] & np.char.endswith(KEY.astype(str), "D1")),
               ("PERIODE", JEN["PERIODE"]), ("BULAT100", KEY == "BULAT100"), ("SEMUA", np.ones(len(I), bool))):
    out = []
    for pn, pm in PER.items():
        r_ = mk & pm & (kode == 0); c_ = mk & pm & (ck == 0)
        out.append(f"{pn}: {lanjut[r_].mean() * 100:4.1f}% (n {r_.sum()}) vs {cl[c_].mean() * 100:4.1f}%")
    print(f"  {nm:<14} " + " | ".join(out))
print("\nNETRAL (tidak pantul/tembus dalam 12 jam): nyata {:.1f}% vs acak {:.1f}%".format((kode == -1).mean() * 100, (ck[cm] == -1).mean() * 100))
print(f"waktu {time.time() - t_:.0f} dtk")
