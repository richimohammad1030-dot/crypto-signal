"""UJI PENUH sesi 23 Nov 2026: 3 teratas saringan_1123.py -> WALK-FORWARD BERLABUH 2004-2026 (pola ide65_67.py).
Sumber edge BARU (dari saringan: semua FADE level rugi, IKUT tembusan untung -> pelajaran lintas bot "level lebih sering ditembus"):
  BRK-PD   : close H1 tembus PDH/PDL (blok 07-07 WIB) >= 0,25 ATR, pertama kali hari itu -> market IKUT, SL 1,5 ATR, tanpa TP, tutup 23:00
  BRK-ASIA : sama dengan range Asia (candle 00:00-07:00 WIB)
  Dipasang di SLOT SUSULAN (hari K6 dilewati; bot berjalan tiap 2 jam di jam keputusan 09:00..21:00 WIB):
    F (isi)  : S3 live dulu di jam keputusan pertama; bila S3 tidak ekstrem -> pindai jam keputusan berikutnya untuk BRK
    G (ganti): BRK menggantikan S3 (pindai mulai jam keputusan pertama)
  + informasi: BRK mandiri (semua hari, 1 trade/hari) per tahun 2011-2026 & korelasi dengan sistem live.
Tambalan (antri): #68 KOMBO-SUS-SELL (jam keputusan pertama: KOMBO SELL dulu, selain itu S3 BUY; S3 SELL dibuang).
Walk-forward: tiap jendela pilih varian {dasar, ...} dari 2005..Y (skor = tahun minus paling sedikit, lalu R/thn), uji Y+1..Y+2.
P = signifikansi.banding rasio R/DD vs sistem live 2011-2026; juga Setra Feb 2025-skrg (sudah pernah dilihat = informasi).
Pemakaian (dari folder eksperimen): python uji_1123.py <xau_2004.json> <ambigu_m1_2022_2026.json>"""
import sys, collections
import numpy as np
sys.argv = sys.argv[:3]
exec(open("ide65_67.py").read().split("# ---------------- #65")[0].split('"""', 2)[2])
N = len(T)
i07a = np.array(i07); DAY = np.searchsorted(i07a, np.arange(N), side="right") - 1
ASH = np.array([H[max(0, i - 6):i + 1].max() for i in i07a]); ASL = np.array([L[max(0, i - 6):i + 1].min() for i in i07a])
LV = {"PD": (dH, dL), "ASIA": (ASH, ASL)}

def brk(q, k, jenis):
    """Sinyal tembus pertama hari itu di candle keputusan q (close sejak 07:00 belum pernah lewat ambang)."""
    hi, lo = LV[jenis]; a = A[q]; up = hi[k] + 0.25 * a; dn = lo[k] - 0.25 * a; i = i07a[k]
    before = C[i + 1:q] if q > i + 1 else np.array([C[i]])
    if C[q] > up and before.max() <= up: return 1
    if C[q] < dn and before.min() >= dn: return -1
    return 0

def mk(q, d, sl, st, tp=None):
    j = q + 1; dist = sl * A[q]
    if j >= N or dist <= 0.5: return None
    e = O[j]; ex, t1, why = sm._kelola(D, j, d, e, e - d * dist, e + d * tp * dist if tp else None)
    return dict(d=d, e=e, ex=ex, r0=dist, t0=T[j], t1=t1, why=why, w=1.0, i0=j, R=(ex - e) * d / dist, strat=st)

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
HARI_K6 = [x for x in m.jalankan({"tren_lawan_w": ("ema200", 0.0), "ambigu": AMB}, D, A, F) if x["w"] == 0 and x["ip"] not in SIG]
def slot(var):
    out = []
    for x in HARI_K6:
        q = x["i0"]
        while q < N and HR[q] not in JAM and HR[q] != sm.CLOSE: q += 1
        if q >= N - 1 or HR[q] not in JAM: continue
        k = DAY[q]; t_ = None
        if var == "68":
            if kombo_at(q) == -1: t_ = mk(q, -1, gb.KOMBO_SL_ATR, "SUSK")
            elif R2[q] <= gb.SUS_BUY: t_ = mk(q, 1, gb.SUS_SL_ATR, "SUS", gb.SUS_TP_R)
        else:
            jenis, mode = var.split("-")
            if mode == "F" and (R2[q] <= gb.SUS_BUY or R2[q] >= gb.SUS_SELL):
                t_ = mk(q, 1 if R2[q] <= gb.SUS_BUY else -1, gb.SUS_SL_ATR, "SUS", gb.SUS_TP_R)
            else:
                q2 = q if mode == "G" else q + 1
                while q2 < N - 1 and HR[q2] != sm.CLOSE and DAY[q2] == k:
                    if HR[q2] in JAM:
                        d = brk(q2, k, jenis)
                        if d: t_ = mk(q2, d, 1.5, "BRK" + jenis); break
                    q2 += 1
        if t_: t_["ip"] = x["ip"]; out.append(t_)
    return out

pagi = [dict(x) for x in BASE if x["strat"] != "SUS"]
SIS = {"0": LIVE}
NAMA = {"0": "dasar (live)", "68": "#68 KOMBO-SUS-SELL", "PD-F": "BRK-PD isi slot", "PD-G": "BRK-PD ganti S3",
        "ASIA-F": "BRK-ASIA isi slot", "ASIA-G": "BRK-ASIA ganti S3"}
for v in NAMA:
    if v != "0": SIS[v] = siap([dict(x) for x in pagi] + slot(v))

print("\n=== Varian tetap 2005-2026 (informasi) & 2011-2026 ===")
for v, G in SIS.items():
    ringkas(f"{NAMA[v]} 05-26", G, [1.0] * len(G), 2005, 2026)
    if v != "0":
        for st in sorted({x["strat"] for x in G if x["strat"] not in ("KOMBO", "MR", "K6")}):
            r = [x["Rn"] for x in G if x["strat"] == st]
            per = " · ".join(f"{a_}-{b_ % 100:02d} {np.mean([x['Rn'] for x in G if x['strat'] == st and a_ <= x['y'] <= b_] or [0]):+.3f}"
                             for a_, b_ in ((2005, 2014), (2015, 2021), (2022, 2026)))
            print(f"      {st}: n {len(r)} · R/trade {np.mean(r):+.3f} · win {np.mean(np.array(r) > 0) * 100:.0f}% · {per}")

def wf(nama, kand):
    sel = []; pil = []
    for Y, a, b in WIN:
        best = max(((skor(SIS[v], [1.0] * len(SIS[v]), 2005, Y), v) for v in kand))
        pil.append((Y, best[1])); sel += [x for x in SIS[best[1]] if a <= x["y"] <= b]
    r = ringkas(nama, sel, [1.0] * len(sel)); print("   pilihan:", pil); return r, sel
print("\n=== WALK-FORWARD (uji 2011-2026, semua tahun hasil uji) ===")
ringkas("SISTEM LIVE", LIVE, [1.0] * len(LIVE))
R68, _ = wf("#68 WF {dasar,68}", ["0", "68"])
RPD, SPD = wf("BRK-PD WF {dasar,F,G}", ["0", "PD-F", "PD-G"])
RAS, SAS = wf("BRK-ASIA WF {dasar,F,G}", ["0", "ASIA-F", "ASIA-G"])
for v in ("PD-F", "PD-G", "ASIA-F", "ASIA-G", "68"):
    G = [x for x in SIS[v] if x["y"] >= 2011]; ringkas(f"  tetap {NAMA[v]} 11-26", G, [1.0] * len(G))

# BRK mandiri (sumber edge baru sebagai strategi sendiri; informasi diversifikasi)
print("\n=== BRK mandiri semua hari (1 trade/hari, jam keputusan 09..21 WIB tiap 2 jam) ===")
for jenis in ("PD", "ASIA"):
    G = []
    for k, i in enumerate(i07a[1:], 1):
        q = i + 1
        while q < N - 1 and HR[q] != sm.CLOSE and DAY[q] == k:
            if HR[q] in JAM:
                d = brk(q, k, jenis)
                if d:
                    t_ = mk(q, d, 1.5, "BRK" + jenis)
                    if t_: G.append(t_)
                    break
            q += 1
    G = siap(G)
    hl = collections.defaultdict(float); hg = collections.defaultdict(float)
    for x in LIVE: hl[int(x["t0"] // 86400)] += x["Rn"]
    for x in G: hg[int(x["t0"] // 86400)] += x["Rn"]
    ks = sorted(set(hl) | set(hg)); kor = np.corrcoef([hl.get(k_, 0) for k_ in ks], [hg.get(k_, 0) for k_ in ks])[0, 1]
    th = {y: sum(x["Rn"] for x in G if x["y"] == y) for y in range(2005, 2027)}
    print(f"BRK-{jenis} mandiri: n {len(G)} · R/trade {np.mean([x['Rn'] for x in G]):+.3f} · korelasi harian vs live {kor:+.2f}")
    print("   " + " ".join(f"{y % 100}:{v_:+.0f}" for y, v_ in th.items()) + f" · minus {sum(v_ < 0 for v_ in th.values())}/22")
