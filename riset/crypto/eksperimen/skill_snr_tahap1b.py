"""KURIKULUM SKILL 1 · SNR · TAHAP 1b (Jumat 20 Nov 2026): apakah TEMBUSAN level diikuti LANJUTAN?
Tahap 1 (13 Nov): level PERIODE & SWING-D1 lebih sering DITEMBUS daripada level acak. Tahap 1b menguji apakah tembusan itu
berguna untuk breakout: setelah candle H1 menembus level >= 0,5 ATR H1 (definisi TEMBUS tahap 1, peristiwa dari luar, jeda 12),
berapa gerak lanjutan searah tembusan dalam 1 / 3 / 5 hari (close ke close, dalam ATR D1 saat level dibuat)?
Pembanding: tembusan level ACAK (level sama digeser ±U(0,5; 2,0) ATR D1, 3 salinan) — sama seperti tahap 1.
Lanjutan nyata > acak dengan P >= 0,90 (bootstrap blok bulanan 2.000×) di 2017-19 DAN 2020-skrg, tembus ke atas DAN ke bawah
(4 sel, horizon 3 hari sebagai ukuran utama) = LULUS 1b untuk jenis itu. Juga dilaporkan: lanjutan absolut (> 0?) dan
peluang harga 3 hari kemudian masih di balik level.
Koin & data sama dengan tahap 1 (11 koin daftar bot dengan spot sejak <= 2018, data_lama).
Pemakaian: python skill_snr_tahap1b.py <repo> <data_lama> [out.json]"""
import collections, calendar, json, os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skill_snr_tahap1 as s1
REPO, DATA = sys.argv[1:3]; OUTJ = sys.argv[3] if len(sys.argv) > 3 else None
sb = s1.sb
rng = np.random.default_rng(20)
HOR = (24, 72, 120)


def tembusan(T, H, L, C, lv, shift=0.0):
    """[(t_tembus, arah_tembus, {h: lanjutan ATR D1}, masih_dibalik_3h)] — arah +1 = tembus resistance ke atas."""
    nm, p, t_on, t_off, aD = lv; p = p + shift * aD
    a, b = np.searchsorted(T, t_on), np.searchsorted(T, t_off)
    if b - a < 2 or aD <= 0: return []
    A = A_ALL
    hi, lo, cl = H[a:b], L[a:b], C[a:b]
    touch = (lo <= p + 0.1 * A[a:b]) & (hi >= p - 0.1 * A[a:b])
    out, nxt = [], 0
    for k in np.flatnonzero(touch):
        if k < 1 or k < nxt: continue
        ak = A[a + k]; pc = cl[k - 1]
        if pc > p + 0.1 * ak: d = 1
        elif pc < p - 0.1 * ak: d = -1
        else: continue
        g = a + k; hit = None
        for j in range(g, min(g + 12, len(T))):
            pen = (L[j] <= p - 0.5 * ak) if d == 1 else (H[j] >= p + 0.5 * ak)
            awa = (H[j] >= p + 1.0 * ak) if d == 1 else (L[j] <= p - 1.0 * ak)
            if pen: hit = j; break
            if awa and j > g: break
        nxt = k + 12
        if hit is None or hit + HOR[-1] >= len(T): continue
        bd = -d                                     # datang dari atas (support) → tembus ke bawah
        lan = {h: float((C[hit + h] - C[hit]) * bd / aD) for h in HOR}
        out.append((int(T[hit]), bd, lan, bool((C[hit + 72] - p) * bd > 0)))
    return out


def main():
    global A_ALL
    now = time.time() * 1000; coins = []
    for c in sb.COINS:
        pth = f"{DATA}/klines/{c}.json"
        if not os.path.exists(pth): continue
        rows = [x for x in json.load(open(pth)) if x[5] < now]
        if rows and rows[0][0] < calendar.timegm((2019, 1, 1, 0, 0, 0)): coins.append((c, rows))
        if len(coins) >= 11: break
    R = collections.defaultdict(list)
    for c, rows in coins:
        a = np.array([x[:5] for x in rows], float); T = a[:, 0].astype(np.int64)
        O, H, L, C = a[:, 1], a[:, 2], a[:, 3], a[:, 4]; A_ALL = s1.atr(H, L, C)
        lvs = [lv for lv in s1.levels_for(T, O, H, L, C) if lv[0].startswith(("PERIODE", "SWING-D1", "SWING-H4"))]
        for lv in lvs:
            g = "PERIODE" if lv[0].startswith("PERIODE") else lv[0][:8]
            R[(g, "nyata")] += tembusan(T, H, L, C, lv)
            for _ in range(3):
                R[(g, "acak")] += tembusan(T, H, L, C, lv, shift=rng.choice((-1, 1)) * rng.uniform(0.5, 2.0))
        print(f"{c}: {len(lvs)} level", flush=True)
    hasil = {"koin": [c for c, _ in coins]}
    for g in ("PERIODE", "SWING-D1", "SWING-H4"):
        sel = {}
        for pn, a0, a1 in s1.PER:
            for d, dn in ((1, "tembus atas"), (-1, "tembus bawah")):
                ev = {k: [x for x in R[(g, k)] if a0 <= x[0] < a1 and x[1] == d] for k in ("nyata", "acak")}
                if len(ev["nyata"]) < 50: sel[f"{pn} {dn}"] = None; continue
                mk = lambda e: np.array([time.gmtime(x[0]).tm_year * 12 + time.gmtime(x[0]).tm_mon for x in e])
                mn, ma = mk(ev["nyata"]), mk(ev["acak"])
                vn = np.array([x[2][72] for x in ev["nyata"]]); va = np.array([x[2][72] for x in ev["acak"]])
                months = np.unique(np.concatenate([mn, ma]))
                sn = np.array([(vn[mn == m].sum(), (mn == m).sum()) for m in months], float)
                sa = np.array([(va[ma == m].sum(), (ma == m).sum()) for m in months], float)
                pick = rng.integers(0, len(months), (2000, len(months)))
                a_, b_ = sn[pick].sum(1), sa[pick].sum(1); ok = (a_[:, 1] > 0) & (b_[:, 1] > 0)
                P = float(np.mean(a_[ok, 0] / a_[ok, 1] - b_[ok, 0] / b_[ok, 1] > 0))
                Pabs = float(np.mean(a_[ok, 0] / a_[ok, 1] > 0))
                sel[f"{pn} {dn}"] = dict(n=len(vn), n_acak=len(va),
                                         **{f"lan{h // 24}h": round(float(np.mean([x[2][h] for x in ev['nyata']])), 3) for h in HOR},
                                         **{f"acak{h // 24}h": round(float(np.mean([x[2][h] for x in ev['acak']])), 3) for h in HOR},
                                         dibalik3h=round(float(np.mean([x[3] for x in ev["nyata"]])) * 100, 1),
                                         dibalik3h_acak=round(float(np.mean([x[3] for x in ev["acak"]])) * 100, 1),
                                         P_vs_acak=round(P, 3), P_lanjut=round(Pabs, 3))
        lulus = all(v is not None and v["P_vs_acak"] >= 0.90 for v in sel.values())
        hasil[g] = dict(lulus_1b=lulus, **sel)
        print(f"\n{g}: {'LULUS 1b' if lulus else 'belum'}")
        for k, v in sel.items():
            print(f"  {k:<22} " + ("n<50" if v is None else
                  f"n={v['n']:6d} lanjut 1/3/5h {v['lan1h']:+.3f}/{v['lan3h']:+.3f}/{v['lan5h']:+.3f} vs acak "
                  f"{v['acak1h']:+.3f}/{v['acak3h']:+.3f}/{v['acak5h']:+.3f} ATR D1 · dibalik 3h {v['dibalik3h']:.0f}% vs {v['dibalik3h_acak']:.0f}% · "
                  f"P(vs acak) {v['P_vs_acak']:.2f} · P(lanjut>0) {v['P_lanjut']:.2f}"))
    if OUTJ: json.dump(hasil, open(OUTJ, "w"), indent=1)


if __name__ == "__main__":
    main()
