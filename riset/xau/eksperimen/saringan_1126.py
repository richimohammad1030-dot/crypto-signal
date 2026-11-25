"""SARINGAN CEPAT sesi Kamis 26 Nov 2026 (ATURAN_BERSAMA E.2: maks 10 ide/varian, satu skrip, PERIODE PILIH SAJA 2005-2014).
Basis = mesin saringan massal (riset/massal/xau.py, juara live direproduksi; ambigu = BUY) -> penilaian sama dengan inti.nilai.
SKILL SNR tahap 2 putaran 2/3 (zona dari skill_snr.bangun, tanpa masa depan; ATR = ATR H1 candle keputusan):
  1 SNR-SL-ZONA   : KOMBO & MR: SL = tepi jauh zona SWING terdekat di belakang entry - 0,25 ATR (jarak 0,5-4 ATR); tidak ada -> SL ATR
  2 SNR-SL-KETAT  : sama, tetapi hanya bila SL zona LEBIH DEKAT dari SL ATR (memperkecil rugi)
  3 SNR-SL-D1     : sama dengan (1), hanya zona SWING D1
  4 SNR-FILTER-K3 : lewati trade (semua komponen) bila KONFLUENSI >= 3 jenis (SWING/PERIODE/BULAT 25+/SUPDEM) lawan dalam 1 ATR di depan
  5 SNR-TP-K6     : K6: TP = zona SWING lawan terdekat - 0,1 ATR bila jaraknya 1-4R (selain itu TP 4R)
SUMBER EDGE BARU (strategi mandiri, 1 trade/hari, SL 1,5 ATR, tanpa TP, tutup 23:00 WIB; dinilai R/trade & korelasi vs live):
  6 MOM-INTRA     : momentum intraday [lit] Gao, Han, Li & Zhou (2018, JFE "Market intraday momentum"): gerak 07:00->19:00 WIB
                    >= 1 ATR -> market searah di open 19:00 WIB (sesi New York), tutup 23:00
  7 TOM-BUY       : efek pergantian bulan [lit] Ariel (1987); emas: Baur (2013) "The autumn effect of gold" (musiman): BUY 07:00
                    di hari bursa terakhir bulan + 3 hari bursa pertama
  8 BOS-H4        : skill 2 (struktur pasar) uji awal: close 07:00 baru menembus swing high/low fraktal-2 H4 terakhir (belum
                    tembus 24 jam sebelumnya) -> IKUT arah tembusan (break of structure)
Pemakaian: python saringan_1126.py <data_dir berisi xau.json>"""
import sys, os, collections
import numpy as np
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path[:0] = [os.path.join(REPO, "riset", "massal"), os.path.dirname(os.path.abspath(__file__))]
import xau as B, inti, skill_snr as sk, strat_mesin as sm, audit_mesin as m

D, A, F = B.muat(sys.argv[1]); T, O, H, L, C = D; N = len(T)
M = B.Mesin(D, A, F); RAW = [x for x in M.trades() if x["w"] > 0]
HR = ((T // 3600) % 24).astype(int)
A0, A1 = "2005-01-01", "2015-01-01"

def nil(tr, nm, mandiri=False):
    s = inti.nilai(tr, B.RISIKO, A0, A1)
    t = [x for x in tr if inti.ts(A0) <= x["t0"] < inti.ts(A1)]; rt = np.mean([x["r"] for x in t])
    kor = ""
    if mandiri:
        hl, hg = collections.defaultdict(float), collections.defaultdict(float)
        for x in JL: hl[int(x["t0"] // 86400)] += x["r"]
        for x in t: hg[int(x["t0"] // 86400)] += x["r"]
        ks = sorted(set(hl) | set(hg)); kor = f" · kor {np.corrcoef([hl.get(k, 0) for k in ks], [hg.get(k, 0) for k in ks])[0, 1]:+.2f}"
    print(f"{nm:<16} n {s['n']:>5} · R/trade {rt:+.3f} · R/thn {s['rthn']:+5.1f} · minus {len(s['minus'])}/10 · PF {s['pf']:.2f} · "
          f"DD {s['ddR']:5.1f}R · win {s['wr'] * 100:3.0f}% · beruntun {s['beruntun']}{kor}")
    return dict(nm=nm, rt=rt, **s)

JL = [x for x in B.ke_inti(RAW) if inti.ts(A0) <= x["t0"] < inti.ts(A1)]
print(f"SARINGAN 2005-2014 · data {m.wib(T[0]):%Y-%m-%d} s.d. {m.wib(T[-1]):%Y-%m-%d}")
HAS = [nil(B.ke_inti(RAW), "0 JUARA")]

# ---------------- zona SNR ----------------
Z, _ = sk.bangun(D)
def arr(zs):
    return {k: np.array([z[k] for z in zs]) for k in ("tav", "exp", "lo", "hi")}
SW = arr([z for z in Z if z["jenis"].startswith("SWING")])
SWD = arr([z for z in Z if z["jenis"].startswith("SWING") and z["tf"] == "D1"])
PER = arr([z for z in Z if z["jenis"][:2] in ("PD", "PW")])
SD = arr([z for z in Z if z["jenis"] in ("DEMAND", "SUPPLY")])

def zona_belakang(S, t, e, d, a):
    """Tepi jauh zona terdekat di belakang entry (BUY: di bawah) dengan jarak 0,5-4 ATR."""
    ak = (S["tav"] <= t) & (S["exp"] > t)
    if d == 1:
        k = ak & (S["hi"] < e - 0.5 * a) & (S["lo"] >= e - 4 * a)
        return S["lo"][k][np.argmax(S["hi"][k])] if k.any() else None
    k = ak & (S["lo"] > e + 0.5 * a) & (S["hi"] <= e + 4 * a)
    return S["hi"][k][np.argmin(S["lo"][k])] if k.any() else None

def zona_depan(S, t, e, d, lo_, hi_):
    ak = (S["tav"] <= t) & (S["exp"] > t)
    if d == 1:
        k = ak & (S["lo"] > e + lo_) & (S["lo"] <= e + hi_); return S["lo"][k].min() if k.any() else None
    k = ak & (S["hi"] < e - lo_) & (S["hi"] >= e - hi_); return S["hi"][k].max() if k.any() else None

def ulang(x, slp, tpp):
    e, d = x["e"], x["d"]; ex, t1, why = sm._kelola(D, x["i0"], d, e, slp, tpp); dist = (e - slp) * d
    return dict(x, ex=ex, t1=t1, why=why, r0=dist, R=(ex - e) * d / dist)

def sl_zona(S, ketat):
    out = []
    for x in RAW:
        if x["strat"] in ("KOMBO", "MR") and inti.ts(A0) <= x["t0"] < inti.ts(A1):
            a = A[x["i0"] - 1]; z = zona_belakang(S, x["t0"], x["e"], x["d"], a)
            if z is not None:
                slp = z - x["d"] * 0.25 * a
                if not ketat or (x["e"] - slp) * x["d"] < x["r0"]:
                    out.append(ulang(x, slp, None)); continue
        out.append(x)
    return out
HAS.append(nil(B.ke_inti(sl_zona(SW, False)), "1 SNR-SL-ZONA"))
HAS.append(nil(B.ke_inti(sl_zona(SW, True)), "2 SNR-SL-KETAT"))
HAS.append(nil(B.ke_inti(sl_zona(SWD, False)), "3 SNR-SL-D1"))

def konfluensi(x):
    t, e, d = x["t0"], x["e"], x["d"]; a = A[x["i0"] - 1]; n = 0
    for S in (SW, PER, SD):
        n += zona_depan(S, t, e, d, 0.0, a) is not None
    lo, hi = (e, e + a) if d == 1 else (e - a, e)
    n += np.floor(hi / 25) * 25 > lo
    return n
G4 = [x for x in RAW if not (inti.ts(A0) <= x["t0"] < inti.ts(A1)) or konfluensi(x) < 3]
print(f"   (FILTER-K3 melewati {len(RAW) - len(G4)} trade 2005-14)")
HAS.append(nil(B.ke_inti(G4), "4 SNR-FILTER-K3"))
G5 = []
for x in RAW:
    if x["strat"] == "K6" and inti.ts(A0) <= x["t0"] < inti.ts(A1):
        a = A[x["i0"] - 1]; z = zona_depan(SW, x["t0"], x["e"], x["d"], 1.0 * x["r0"], 4.0 * x["r0"])
        if z is not None:
            G5.append(dict(ulang(x, x["sl"], z - x["d"] * 0.1 * a), r0=x["r0"])); G5[-1]["R"] = (G5[-1]["ex"] - x["e"]) * x["d"] / x["r0"]; continue
    G5.append(x)
HAS.append(nil(B.ke_inti(G5), "5 SNR-TP-K6"))

# ---------------- sumber edge baru (mandiri) ----------------
i07 = np.flatnonzero(HR == sm.PLACE)
def mk(q, d, st):
    j = q + 1; dist = 1.5 * A[q]
    if j >= N or dist <= 0.5: return None
    e = O[j]; ex, t1, why = sm._kelola(D, j, d, e, e - d * dist, None)
    return dict(d=d, e=e, ex=ex, r0=dist, t0=T[j], t1=t1, why=why, w=1.0, i0=j, R=(ex - e) * d / dist, strat=st)
def wib(i): return m.wib(T[i])
G6, G7, G8 = [], [], []
# 6 momentum intraday: candle close 19:00 WIB = open 11:00 UTC
for i in i07:
    q = i + 12
    if q >= N - 1 or HR[q] != 11 or (T[q] - T[i]) != 12 * 3600: continue
    mv = C[q] - C[i]
    if abs(mv) >= A[q]:
        x = mk(q, int(np.sign(mv)), "MOMI"); x and G6.append(x)
# 7 turn-of-month: hari bursa terakhir + 3 pertama
bl = np.array([wib(i).year * 12 + wib(i).month for i in i07])
for k, i in enumerate(i07):
    pos_awal = k - np.searchsorted(bl, bl[k]); akhir = k + 1 < len(bl) and bl[k + 1] != bl[k]
    if pos_awal < 3 or akhir:
        x = mk(i, 1, "TOM"); x and G7.append(x)
# 8 BOS H4 fraktal-2
H4 = sk.resample(T, O, H, L, C, 4 * 3600); h4, l4, tv = H4["h"], H4["l"], H4["tav"]
ph, pl = [], []
for j in range(2, len(h4) - 2):
    if h4[j] > h4[j - 2:j].max() and h4[j] > h4[j + 1:j + 3].max(): ph.append((tv[j + 2], h4[j]))
    if l4[j] < l4[j - 2:j].min() and l4[j] < l4[j + 1:j + 3].min(): pl.append((tv[j + 2], l4[j]))
pht, phv = np.array([p[0] for p in ph]), np.array([p[1] for p in ph]); plt_, plv = np.array([p[0] for p in pl]), np.array([p[1] for p in pl])
for i in i07:
    if i < 30: continue
    t = T[i] + 3600; a = np.searchsorted(pht, t, side="right") - 1; b = np.searchsorted(plt_, t, side="right") - 1
    if a < 0 or b < 0: continue
    if C[i] > phv[a] and C[i - 24:i].max() <= phv[a]: x = mk(i, 1, "BOS")
    elif C[i] < plv[b] and C[i - 24:i].min() >= plv[b]: x = mk(i, -1, "BOS")
    else: continue
    x and G8.append(x)
for G, nm in ((G6, "6 MOM-INTRA"), (G7, "7 TOM-BUY"), (G8, "8 BOS-H4")):
    HAS.append(nil(B.ke_inti(G), nm, mandiri=True))
    # informasi sisi (tidak dipakai memilih): per periode
    for a_, b_ in (("2005-01-01", "2015-01-01"),):
        for d in (1, -1):
            r = [v["r"] for v, x in zip(B.ke_inti(G), G) if inti.ts(a_) <= x["t0"] < inti.ts(b_) and x["d"] == d]
            if r: print(f"     {'BUY' if d == 1 else 'SELL'}: n {len(r)} R/trade {np.mean(r):+.3f}")
print("\nPeringkat ubah-juara (R/thn, minus) & mandiri (R/trade):")
for h in HAS:
    print(f"  {h['nm']:<16} R/trade {h['rt']:+.3f} · R/thn {h['rthn']:+5.1f} · minus {len(h['minus'])} · DD {h['ddR']:.0f}R · PF {h['pf']:.2f}")
