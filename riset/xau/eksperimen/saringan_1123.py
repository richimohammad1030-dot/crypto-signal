"""SARINGAN CEPAT sesi riset Senin 23 Nov 2026 (ATURAN_BERSAMA E.2: maks 10 ide/varian, satu skrip, PERIODE PILIH SAJA 2005-2014).
Metrik 2005-2014 (bersih biaya 0,40 USD): n, R/trade, R/thn, tahun minus, terburuk, DD, win, korelasi R harian vs sistem live.
Semua strategi mandiri: keputusan di close candle H1 08:00..21:00 WIB (07:00 untuk RANGE-FADE), market di open berikutnya,
SL 1,5 ATR(14) H1, tanpa TP, tutup 23:00 WIB, maks 1 trade/hari (sinyal pertama). Tanpa penyetelan parameter.
  1 #68  KOMBO-SUS-SELL : hari K6 dilewati, jam keputusan pertama: KOMBO SELL dulu, selain itu S3 BUY (S3 SELL dibuang)  [ubah juara]
  2 #43  TS-PD          : turtle soup PDH/PDL (high > PDH + 0,1 ATR lalu close kembali < PDH -> SELL; cermin PDL)
  3 baru TS-PW          : sama dengan high/low minggu lalu
  4 baru SWEEP-ASIA     : sapuan range Asia (00:00-07:00 WIB) lalu close kembali di dalam -> fade (keputusan 08:00-16:00 WIB)
  5 baru BRK-PD         : close tembus PDH/PDL >= 0,25 ATR (pertama kali hari itu) -> IKUT arah (pelajaran lintas bot: level ditembus)
  6 baru BRK-ASIA       : close tembus range Asia >= 0,25 ATR -> IKUT
  7 #56  BB-SQZ         : lebar Bollinger 20/2 candle sebelumnya <= persentil 10% dari 120 candle, close keluar pita -> IKUT
  8 baru RANGE-FADE     : range hari sebelumnya (07-07) > 1,8 x rata 14 hari -> 07:00 lawan arah body hari sebelumnya
  9 SKILL SNR-FILTER    : lewati trade juara bila ada zona SWING D1 lawan dalam <= 1 ATR di depan harga masuk  [ubah juara]
 10 SKILL SNR-PANTUL   : sentuhan SWING-sendiri / konfluensi >= 3 jenis (lulus PAHAM 23 Nov) -> market arah pantul di open
                        berikutnya, SL = tepi jauh - 0,5 ATR, TP = tepi dekat + 1 ATR (definisi PAHAM), tutup 23:00
Pemakaian (dari folder eksperimen): python saringan_1123.py <xau_2004.json> <ambigu_m1_2022_2026.json>"""
import sys, collections
import numpy as np
sys.argv = sys.argv[:3]
exec(open("simetris.py").read().split("KAND = {}")[0])
import skill_snr as sk
gb = m.gb
Y0, Y1 = 2005, 2014
N = len(T)
def yr(t): return m.wib(t).year

def siap(G):
    G = sorted([x for x in G if Y0 <= yr(x["t0"]) <= Y1 and x["w"] > 0], key=lambda z: z["t1"])
    for x, v in zip(G, m.net(G)): x["Rn"] = float(v); x["y"] = yr(x["t0"]); x["hari"] = int((x["t0"] + 7 * 3600) // 86400)
    return G

LIVE = siap([dict(x) for x in BASE])
def harian(G):
    d = collections.defaultdict(float)
    for x in G: d[x["hari"]] += x["Rn"]
    return d
HL = harian(LIVE)

def ukur(nm, G, ubah=False):
    G = siap(G) if G and "Rn" not in G[0] else G
    th = {y: 0.0 for y in range(Y0, Y1 + 1)}
    for x in G: th[x["y"]] += x["Rn"]
    v = np.array(list(th.values())); r = np.array([x["Rn"] for x in G]) if G else np.zeros(1)
    c = np.cumsum(r); dd = (np.maximum.accumulate(np.concatenate([[0], c]))[1:] - c).max()
    hg = harian(G); ks = sorted(set(hg) | set(HL))
    kor = np.corrcoef([hg.get(k, 0) for k in ks], [HL.get(k, 0) for k in ks])[0, 1] if len(G) > 5 else np.nan
    print(f"{nm:<22} n {len(G):>5} · R/trade {r.mean():+.3f} · R/thn {v.mean():+5.1f} · minus {(v < 0).sum()}/10 · terburuk {v.min():+5.1f} · "
          f"DD {dd:5.1f}R · win {np.mean(r > 0) * 100:3.0f}% · {'' if ubah else f'kor {kor:+.2f}'}")
    return dict(nm=nm, n=len(G), rt=r.mean(), rthn=v.mean(), minus=int((v < 0).sum()), worst=v.min(), dd=dd, th=th)

def trade(q, d, sl_dist, st, tp_dist=None):
    j = q + 1
    if j >= N or sl_dist <= 0.5: return None
    e = O[j]; ex, t1, why = sm._kelola(D, j, d, e, e - d * sl_dist, e + d * tp_dist if tp_dist else None)
    return dict(d=d, e=e, ex=ex, r0=sl_dist, t0=T[j], t1=t1, why=why, w=1.0, i0=j, R=(ex - e) * d / sl_dist, strat=st)

# ---------- konteks harian ----------
i07a = np.array(i07)
DAY = np.searchsorted(i07a, np.arange(N), side="right") - 1        # indeks hari dagang (blok mulai close 07:00)
ASH = np.array([H[max(0, i - 6):i + 1].max() for i in i07a]); ASL = np.array([L[max(0, i - 6):i + 1].min() for i in i07a])
wk = np.array([m.wib(t).isocalendar()[:2] for t in T]); wkey = wk[:, 0] * 100 + wk[:, 1]
WH, WL = {}, {}
for k_ in np.unique(wkey):
    s_ = wkey == k_; WH[k_] = H[s_].max(); WL[k_] = L[s_].min()
ukeys = np.unique(wkey); prevw = {ukeys[n]: ukeys[n - 1] for n in range(1, len(ukeys))}
mid = sma(C, 20); sd = np.array([C[max(0, i - 19):i + 1].std() if i >= 19 else np.nan for i in range(N)])
bw = 4 * sd / mid
DR = dH - dL; DRm = np.array([DR[max(0, k - 14):k].mean() if k >= 14 else np.nan for k in range(len(DR))])
JAM_KEP = set(range(0, 14))           # candle open UTC 0..13 = close 08:00..21:00 WIB

def mandiri(aturan, st, jam=JAM_KEP):
    out = []
    for k, i in enumerate(i07a):
        if not (Y0 <= yr(T[i]) <= Y1) or k == 0: continue
        q = i + 1
        while q < N - 1 and HR[q] != sm.CLOSE and DAY[q] == k:
            if HR[q] in jam:
                d = aturan(q, k)
                if d:
                    x = trade(q, d, 1.5 * A[q], st)
                    if x: out.append(x)
                    break
            q += 1
    return out

def ts_level(hi, lo):
    def f(q, k):
        a = A[q]
        if H[q] > hi(k) + 0.1 * a and C[q] < hi(k): return -1
        if L[q] < lo(k) - 0.1 * a and C[q] > lo(k): return 1
        return 0
    return f
def brk_level(hi, lo):
    def f(q, k):
        a = A[q]; up = hi(k) + 0.25 * a; dn = lo(k) - 0.25 * a
        if C[q] > up and C[q - 1] <= up: return 1
        if C[q] < dn and C[q - 1] >= dn: return -1
        return 0
    return f
pwh = lambda k: WH.get(prevw.get(wkey[i07a[k] + 1], -1), np.inf); pwl = lambda k: WL.get(prevw.get(wkey[i07a[k] + 1], -1), -np.inf)
def bbsqz(q, k):
    if q < 140 or not np.isfinite(bw[q - 1]): return 0
    if bw[q - 1] > np.nanpercentile(bw[q - 120:q], 10): return 0
    if C[q] > mid[q] + 2 * sd[q]: return 1
    if C[q] < mid[q] - 2 * sd[q]: return -1
    return 0

HASIL = []
print(f"SARINGAN CEPAT {Y0}-{Y1} (periode pilih). Data {m.wib(T[0]):%Y-%m-%d} s.d. {m.wib(T[-1]):%Y-%m-%d}")
base = ukur("SISTEM LIVE", LIVE, ubah=True)

# 1. #68 KOMBO susulan SELL (pola ide65_67.susulan)
mp = (H + L) / 2
s13, s8, s5 = mm._smma(mp, 13), mm._smma(mp, 8), mm._smma(mp, 5)
e_ = lambda x, n: np.array(gb.ema(list(x), n))
mac = e_(C, 12) - e_(C, 26); MH = mac - e_(mac, 9)
def kombo_at(i):
    if i < 8: return 0
    jaw, teeth, lips = s13[i - 8], s8[i - 5], s5[i - 3]
    alg = 1 if lips > teeth > jaw else -1 if lips < teeth < jaw else 0
    mc = 1 if MH[i] > 0 else -1
    rs = 1 if R2[i] <= gb.KOMBO_RSI_BUY else -1 if R2[i] >= gb.KOMBO_RSI_SELL else 0
    return alg if (alg != 0 and alg == mc == rs) else 0
JAM = set(gb.SUS_JAM_UTC); SIG = mm.sinyal_live(D)
sus68 = []
for x in m.jalankan({"tren_lawan_w": ("ema200", 0.0), "ambigu": AMB}, D, A, F):
    if x["w"] != 0 or x["ip"] in SIG: continue
    q = x["i0"]
    while q < N and HR[q] not in JAM and HR[q] != sm.CLOSE: q += 1
    if q >= N - 1 or HR[q] not in JAM: continue
    if kombo_at(q) == -1: t_ = trade(q, -1, gb.KOMBO_SL_ATR * A[q], "SUSK")
    elif R2[q] <= gb.SUS_BUY: t_ = trade(q, 1, gb.SUS_SL_ATR * A[q], "SUS", gb.SUS_TP_R * gb.SUS_SL_ATR * A[q])
    else: t_ = None
    if t_: sus68.append(t_)
G68 = [dict(x) for x in BASE if x["strat"] != "SUS"] + sus68
HASIL.append(ukur("1 #68 KOMBO-SUS-SELL", G68, ubah=True))

# 2-8 strategi mandiri
HASIL.append(ukur("2 #43 TS-PD", mandiri(ts_level(lambda k: dH[k], lambda k: dL[k]), "TSPD")))
HASIL.append(ukur("3 TS-PW", mandiri(ts_level(pwh, pwl), "TSPW")))
HASIL.append(ukur("4 SWEEP-ASIA", mandiri(ts_level(lambda k: ASH[k], lambda k: ASL[k]), "SWA", jam=set(range(0, 9)))))
HASIL.append(ukur("5 BRK-PD (tembus)", mandiri(brk_level(lambda k: dH[k], lambda k: dL[k]), "BRKPD")))
HASIL.append(ukur("6 BRK-ASIA (tembus)", mandiri(brk_level(lambda k: ASH[k], lambda k: ASL[k]), "BRKA")))
HASIL.append(ukur("7 #56 BB-SQZ", mandiri(bbsqz, "BBS")))
rf = []
for k, i in enumerate(i07a):
    if Y0 <= yr(T[i]) <= Y1 and np.isfinite(DRm[k]) and DR[k] > 1.8 * DRm[k] and dC[k] != dO[k]:
        x = trade(i, -int(np.sign(dC[k] - dO[k])), 1.5 * A[i], "RF")
        if x: rf.append(x)
HASIL.append(ukur("8 RANGE-FADE", rf))

# 9-10 SKILL SNR tahap 2
Z, B = sk.bangun(D)
ZD1 = [z for z in Z if z["jenis"].startswith("SWING") and z["tf"] == "D1"]
zt = np.array([z["tav"] for z in ZD1]); ze = np.array([z["exp"] for z in ZD1]); zl = np.array([z["lo"] for z in ZD1]); zh = np.array([z["hi"] for z in ZD1])
def lawan_dekat(x):
    t, e, a, d = x["t0"], x["e"], x["r0"], x["d"]
    a = A[x["i0"] - 1]; akt = (zt <= t) & (ze > t)
    return bool((akt & (zl > e) & (zl <= e + a)).any()) if d == 1 else bool((akt & (zh < e) & (zh >= e - a)).any())
GL = [dict(x) for x in BASE if Y0 <= yr(x["t0"]) <= Y1]
G9 = [x for x in GL if not lawan_dekat(x)]
print(f"   (SNR-FILTER melewati {len(GL) - len(G9)} dari {len(GL)} trade juara)")
HASIL.append(ukur("9 SNR-FILTER D1", G9, ubah=True))
ev = sk.sentuhan(Z, D, bulat=(10, 25, 50, 100))
def kat_(k):
    return "SWING" if k.startswith("SWING") else "PERIODE" if k.startswith(("PD", "PW")) else "BULAT" if k.startswith("BULAT") else "SUPDEM"
kat = collections.defaultdict(set)
for e in ev: kat[(e[0], e[2])].add(kat_(e[1]))
pil = {}
for i, key, s, z in ev:
    if not (Y0 <= yr(T[i]) <= Y1) or HR[i] not in JAM_KEP: continue
    ks_ = kat[(i, s)]
    if not (ks_ == {"SWING"} or len(ks_) >= 3): continue
    k = DAY[i]
    if k in pil and pil[k][0] <= i: continue
    edge, far = (z["hi"], z["lo"]) if s == 1 else (z["lo"], z["hi"])
    pil[k] = (i, s, edge, far)
sp = []
for k, (i, s, edge, far) in sorted(pil.items()):
    a = A[i - 1]
    if (C[i] - far) * s <= 0: continue                       # sudah close tembus: bukan pantul
    j = i + 1
    if j >= N or HR[i] == sm.CLOSE: continue
    e = O[j]; slp = far - s * 0.5 * a; dist = (e - slp) * s
    if dist <= 0.5: continue
    tpp = edge + s * 1.0 * a
    if (tpp - e) * s <= 0: continue
    ex, t1, why = sm._kelola(D, j, s, e, slp, tpp)
    sp.append(dict(d=s, e=e, ex=ex, r0=dist, t0=T[j], t1=t1, why=why, w=1.0, i0=j, R=(ex - e) * s / dist, strat="SNRP"))
HASIL.append(ukur("10 SNR-PANTUL", sp))

print("\nPeringkat (strategi mandiri: R/trade lalu tahun minus; ubah-juara: selisih R/thn vs live):")
for h in HASIL:
    print(f"  {h['nm']:<22} R/trade {h['rt']:+.3f} · R/thn {h['rthn']:+5.1f} (live {base['rthn']:+.1f}) · minus {h['minus']} · DD {h['dd']:.0f}")
