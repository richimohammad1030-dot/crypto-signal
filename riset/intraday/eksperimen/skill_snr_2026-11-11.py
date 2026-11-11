"""KURIKULUM SKILL intraday · Skill 1 SNR (support & resistance) · TAHAP 0 (definisi mesin) + TAHAP 1 (PAHAM).
Pola dari riset/KURIKULUM_SKILL.md (XAU), disesuaikan untuk crypto: level dari H4 & D1 tiap koin, peristiwa di H1.
Koin: 25 koin teratas daftar bot yang punya data H1 sejak 2020-2021 (semua yang tersedia). Periode PAHAM: 2020-2022 & 2023-2026.

TAHAP 0 · pengenal (tanpa melihat masa depan; level baru aktif setelah terkonfirmasi):
  a) SWING  : pivot fraktal n = 2/3/5 candle tiap sisi di H4 & D1 (aktif setelah n candle kanan close; berlaku 30 hari).
  b) PERIODE: high/low hari sebelumnya (blok 07:00-07:00 WIB = 00-00 UTC; berlaku 1 hari) & minggu sebelumnya (berlaku 1 minggu).
  c) BULAT  : kelipatan u×{0,01; 0,025; 0,05; 0,1}, u = 10^floor(log10 harga) (BTC 100k: 1.000/2.500/5.000/10.000; ETH 3k: 10/25/50/100).
  d) SD     : zona supply-demand H4: 1-3 candle dasar (range < 0,6 ATR H4) lalu gerak impulsif >= 2 ATR H4 dalam <= 3 candle;
              zona = range candle dasar; demand bila impuls naik, supply bila turun; segar = belum disentuh; berlaku 30 hari.
TAHAP 1 · uji PAHAM: peristiwa = candle H1 menyentuh zona (±0,1 ATR H1) datang dari LUAR (close sebelumnya > 0,1 ATR di luar).
  Dari atas = uji support (pantul = naik), dari bawah = uji resistance (pantul = turun). Dalam 1-12 candle:
  MEMANTUL = bergerak >= 1 ATR menjauh dari level tanpa lebih dulu menembus >= 0,5 ATR · TEMBUS = menembus >= 0,5 ATR dulu
  (candle yang memenuhi keduanya = TEMBUS, konservatif) · selain itu = netral. Jeda 12 candle per level setelah peristiwa.
  PEMBANDING ACAK: level yang sama digeser ±U(0,5; 2,0) × ATR D1 (arah acak, 3 salinan) dengan masa berlaku sama
  → sebaran jarak & kepadatan setara. Lift = peluang pantul nyata - acak. P = bootstrap blok bulanan 2.000×: P(lift > 0).
  LULUS tahap 1 bila P >= 0,90 di KEDUA periode DAN kedua arah (support & resistance) untuk jenis itu.
Pemakaian: python riset/intraday/eksperimen/skill_snr_2026-11-11.py <repo> <data_dir> [out.json]"""
import calendar, collections, json, os, sys, time
REPO, DATA = sys.argv[1:3]; OUTJ = sys.argv[3] if len(sys.argv) > 3 else None
sys.path.insert(0, REPO); sys.path.insert(0, os.path.join(REPO, "riset"))
import numpy as np
import backtest_intraday as bi, signal_bot as sb

PER = (("2020-22", calendar.timegm((2020, 1, 1, 0, 0, 0)), calendar.timegm((2023, 1, 1, 0, 0, 0))),
       ("2023-26", calendar.timegm((2023, 1, 1, 0, 0, 0)), 2_000_000_000))
rng = np.random.default_rng(11)

def agg(T, O, H, L, C, sec):
    k = T // sec; idx = np.flatnonzero(np.diff(k, prepend=k[0] - 1)); end = np.append(idx[1:], len(T)) - 1
    return dict(T=k[idx] * sec, O=O[idx], H=np.maximum.reduceat(H, idx), L=np.minimum.reduceat(L, idx), C=C[end], end_i=end)

def atr(H, L, C, n=14):
    tr = np.maximum(H - L, np.maximum(abs(H - np.roll(C, 1)), abs(L - np.roll(C, 1)))); tr[0] = H[0] - L[0]
    return bi.wilder(tr, n)

def levels_for(T, O, H, L, C):
    """Daftar level: (jenis, harga, aktif_mulai_t, aktif_akhir_t, atrD1_saat_dibuat)."""
    out = []
    D1 = agg(T, O, H, L, C, 86400); H4 = agg(T, O, H, L, C, 14400); W1 = agg(T - 4 * 86400, O, H, L, C, 7 * 86400)
    W1["T"] = W1["T"] + 4 * 86400
    aD = atr(D1["H"], D1["L"], D1["C"]); aH4 = atr(H4["H"], H4["L"], H4["C"])
    def atrD(t):
        k = np.searchsorted(D1["T"], t) - 1; return float(aD[max(k, 0)])
    for tf, G, sec in (("H4", H4, 14400), ("D1", D1, 86400)):
        for n in (2, 3, 5):
            for i in range(n, len(G["T"]) - n):
                t_on = int(G["T"][i + n]) + sec                     # setelah n candle kanan close
                if G["H"][i] == G["H"][i - n:i + n + 1].max():
                    out.append((f"SWING-{tf}-n{n}", float(G["H"][i]), t_on, t_on + 30 * 86400, atrD(t_on)))
                if G["L"][i] == G["L"][i - n:i + n + 1].min():
                    out.append((f"SWING-{tf}-n{n}", float(G["L"][i]), t_on, t_on + 30 * 86400, atrD(t_on)))
    for nm, G, sec in (("PERIODE-hari", D1, 86400), ("PERIODE-minggu", W1, 7 * 86400)):
        for i in range(1, len(G["T"])):
            t_on = int(G["T"][i]); out += [(nm, float(G["H"][i - 1]), t_on, t_on + sec, atrD(t_on)), (nm, float(G["L"][i - 1]), t_on, t_on + sec, atrD(t_on))]
    # angka bulat: dibangun per bulan dari kisaran harga bulan sebelumnya (±30%)
    M = agg(T, O, H, L, C, 30 * 86400)
    for i in range(1, len(M["T"])):
        p = float(M["C"][i - 1]); u = 10 ** np.floor(np.log10(p)); t_on = int(M["T"][i]); t_off = t_on + 30 * 86400
        for f, nm in ((0.1, "BULAT-0,1u"), (0.05, "BULAT-0,05u"), (0.025, "BULAT-0,025u"), (0.01, "BULAT-0,01u")):
            st = u * f; lo, hi = np.ceil(p * 0.7 / st) * st, np.floor(p * 1.3 / st) * st
            for lv in np.arange(lo, hi + st / 2, st):
                if f < 0.1 and abs(lv / (u * 0.1) - round(lv / (u * 0.1))) < 1e-9: continue   # hanya level yang bukan kelipatan lebih besar
                out.append((nm, float(lv), t_on, t_off, atrD(t_on)))
    # supply-demand H4
    for i in range(3, len(H4["T"]) - 3):
        for nb in (1, 2, 3):
            b0 = i - nb + 1
            if b0 < 1 or np.any((H4["H"][b0:i + 1] - H4["L"][b0:i + 1]) >= 0.6 * aH4[b0:i + 1]): continue
            zh, zl = H4["H"][b0:i + 1].max(), H4["L"][b0:i + 1].min()
            for k in range(1, 4):
                if i + k >= len(H4["T"]): break
                up, dn = H4["H"][i + 1:i + k + 1].max() - zh, zl - H4["L"][i + 1:i + k + 1].min()
                if up >= 2 * aH4[i] or dn >= 2 * aH4[i]:
                    t_on = int(H4["T"][i + k]) + 14400
                    nm = "SD-demand" if up >= 2 * aH4[i] else "SD-supply"
                    out.append((nm, float((zh + zl) / 2), t_on, t_on + 30 * 86400, atrD(t_on)))   # tengah zona
                    break
            break
    return out

def events(T, H, L, C, A, lv, shift=0.0):
    """Peristiwa sentuh untuk satu level. Kembalikan list (t, arah_uji, hasil) hasil: 1 pantul, -1 tembus, 0 netral."""
    nm, p, t_on, t_off, aD = lv; p = p + shift * aD
    a, b = np.searchsorted(T, t_on), np.searchsorted(T, t_off)
    if b - a < 2: return []
    hi, lo, cl, at = H[a:b], L[a:b], C[a:b], A[a:b]
    touch = (lo <= p + 0.1 * at) & (hi >= p - 0.1 * at)
    out, nxt = [], 0
    for k in np.flatnonzero(touch):
        if k < 1 or k < nxt: continue
        pc, ak = cl[k - 1], at[k]
        if pc > p + 0.1 * ak: d = 1          # dari atas: uji support
        elif pc < p - 0.1 * ak: d = -1       # dari bawah: uji resistance
        else: continue
        g = a + k; res = 0
        for j in range(g, min(g + 12, len(T))):
            pen = (L[j] <= p - 0.5 * ak) if d == 1 else (H[j] >= p + 0.5 * ak)
            awa = (H[j] >= p + 1.0 * ak) if d == 1 else (L[j] <= p - 1.0 * ak)
            if pen: res = -1; break
            if awa and j > g: res = 1; break
        out.append((int(T[g]), d, res)); nxt = k + 12
    return out

def main():
    coins = [c for c in sb.COINS[:25]]
    R = collections.defaultdict(list)          # (jenis, nyata/acak) -> list (t, d, res)
    for c in coins:
        rows = [x for x in bi.jload(f"{DATA}/klines/{c}.json") if x[5] < time.time() * 1000] if os.path.exists(f"{DATA}/klines/{c}.json") else []
        if len(rows) < 5000: continue
        a = np.array([x[:5] for x in rows], float); T = (a[:, 0] // 1000 if a[0, 0] > 1e11 else a[:, 0]).astype(np.int64)
        O, H, L, C = a[:, 1], a[:, 2], a[:, 3], a[:, 4]; A = atr(H, L, C)
        lvs = levels_for(T, O, H, L, C)
        for lv in lvs:
            R[(lv[0], "nyata")] += events(T, H, L, C, A, lv)
            for _ in range(3):
                R[(lv[0], "acak")] += events(T, H, L, C, A, lv, shift=rng.choice((-1, 1)) * rng.uniform(0.5, 2.0))
        print(f"{c}: {len(lvs)} level", flush=True)
    jenis = sorted({k[0] for k in R})
    # kelompok gabungan
    grup = {"SWING-H4": [j for j in jenis if j.startswith("SWING-H4")], "SWING-D1": [j for j in jenis if j.startswith("SWING-D1")],
            "PERIODE": [j for j in jenis if j.startswith("PERIODE")], "BULAT": [j for j in jenis if j.startswith("BULAT")],
            "SD": [j for j in jenis if j.startswith("SD")]}
    hasil = {}
    def nilai(nama, js):
        out = {}
        for pn, t0, t1 in PER:
            for d, dn in ((1, "support"), (-1, "resistance")):
                ev = {}
                for kind in ("nyata", "acak"):
                    e = [x for j in js for x in R[(j, kind)] if t0 <= x[0] < t1 and x[1] == d]
                    ev[kind] = e
                if len(ev["nyata"]) < 50: out[(pn, dn)] = None; continue
                pr = lambda e: np.mean([x[2] == 1 for x in e]); pt = lambda e: np.mean([x[2] == -1 for x in e])
                lift = pr(ev["nyata"]) - pr(ev["acak"])
                mk = lambda e: np.array([time.gmtime(x[0]).tm_year * 12 + time.gmtime(x[0]).tm_mon for x in e])
                mn, ma = mk(ev["nyata"]), mk(ev["acak"]); bn = np.array([x[2] == 1 for x in ev["nyata"]]); ba = np.array([x[2] == 1 for x in ev["acak"]])
                months = np.unique(np.concatenate([mn, ma]))
                sn = {m: (bn[mn == m].sum(), (mn == m).sum()) for m in months}; sa = {m: (ba[ma == m].sum(), (ma == m).sum()) for m in months}
                bs = []
                for _ in range(2000):
                    pick = rng.choice(months, len(months))
                    a1 = sum(sn[m][0] for m in pick); n1 = sum(sn[m][1] for m in pick); a2 = sum(sa[m][0] for m in pick); n2 = sum(sa[m][1] for m in pick)
                    if n1 and n2: bs.append(a1 / n1 - a2 / n2)
                P = float(np.mean(np.array(bs) > 0))
                out[(pn, dn)] = dict(n=len(ev["nyata"]), pantul=round(pr(ev["nyata"]) * 100, 1), pantul_acak=round(pr(ev["acak"]) * 100, 1),
                                     tembus=round(pt(ev["nyata"]) * 100, 1), tembus_acak=round(pt(ev["acak"]) * 100, 1), lift=round(lift * 100, 1), P=round(P, 3))
        lulus = all(v is not None and v["P"] >= 0.90 for v in out.values())
        hasil[nama] = dict(lulus=lulus, **{f"{k[0]} {k[1]}": v for k, v in out.items()})
        print(f"\n{nama}: {'LULUS TAHAP 1' if lulus else 'belum'}")
        for k, v in out.items():
            print(f"  {k[0]} {k[1]:<10} " + ("n<50" if v is None else f"n={v['n']:6d} pantul {v['pantul']:5.1f}% vs acak {v['pantul_acak']:5.1f}% (lift {v['lift']:+5.1f}) · tembus {v['tembus']:5.1f}% vs {v['tembus_acak']:5.1f}% · P {v['P']:.2f}"))
    for g, js in grup.items(): nilai(g, js)
    for j in jenis: nilai(j, [j])
    if OUTJ: json.dump(hasil, open(OUTJ, "w"), indent=1)

if __name__ == "__main__":
    main()
