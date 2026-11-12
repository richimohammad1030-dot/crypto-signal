"""KURIKULUM SKILL 1 · SNR · TAHAP 1 PAHAM untuk CRYPTO SWING (Jumat 13 Nov 2026).
Definisi zona = tahap 0 crypto (skill_snr.py): SWING fraktal n=2/3/5 H4 & D1 · PERIODE high/low hari & minggu sebelumnya
(hari 00:00 UTC, minggu Senin) · BULAT 10^k × {1; 0,5; 0,25} · SD H4 (dasar 1-3 candle range <= 0,5 ATR H4, impuls >= 2 ATR
dalam <= 3 candle). Level aktif setelah terkonfirmasi (tanpa melihat masa depan); SWING & SD berlaku 30 hari, PERIODE 1 hari /
1 minggu, BULAT dibangun per 30 hari dari harga penutupan blok sebelumnya (±30%).
Peristiwa (sama dengan riset intraday & KURIKULUM_SKILL): candle H1 menyentuh level (±0,1 ATR H1) datang dari LUAR (close
sebelumnya > 0,1 ATR di luar). Dari atas = uji support, dari bawah = uji resistance. Dalam 1-12 candle: PANTUL = >= 1 ATR menjauh
tanpa lebih dulu menembus >= 0,5 ATR · TEMBUS = menembus >= 0,5 ATR dulu (candle dengan keduanya = TEMBUS) · selain itu netral.
Jeda 12 candle per level setelah peristiwa.
PEMBANDING ACAK: level yang sama digeser ±U(0,5; 2,0) × ATR D1 (3 salinan, masa berlaku sama). Lift = pantul nyata - acak.
P = bootstrap blok bulanan 2.000×: P(lift > 0). LULUS tahap 1 untuk satu jenis bila P >= 0,90 di 2017-2019 DAN 2020-skrg,
support DAN resistance (4 sel). Koin: BTC + 10 koin besar daftar bot dengan data spot sejak <= 2018 (data_lama).
Pemakaian: python skill_snr_tahap1.py <repo> <data_lama> [out.json]"""
import collections, calendar, json, math, os, sys, time
import numpy as np
REPO, DATA = sys.argv[1:3]; OUTJ = sys.argv[3] if len(sys.argv) > 3 else None
sys.path.insert(0, REPO)
import signal_bot as sb
PER = (("2017-19", 0, calendar.timegm((2020, 1, 1, 0, 0, 0))), ("2020-26", calendar.timegm((2020, 1, 1, 0, 0, 0)), 2_000_000_000))
rng = np.random.default_rng(13)


def wilder(x, n):
    o = np.empty_like(x); o[0] = x[0]
    for i in range(1, len(x)): o[i] = (o[i - 1] * (n - 1) + x[i]) / n
    return o


def agg(T, O, H, L, C, sec, off=0):
    k = (T - off) // sec; idx = np.flatnonzero(np.diff(k, prepend=k[0] - 1)); end = np.append(idx[1:], len(T)) - 1
    return dict(T=k[idx] * sec + off, O=O[idx], H=np.maximum.reduceat(H, idx), L=np.minimum.reduceat(L, idx), C=C[end])


def atr(H, L, C, n=14):
    tr = np.maximum(H - L, np.maximum(abs(H - np.roll(C, 1)), abs(L - np.roll(C, 1)))); tr[0] = H[0] - L[0]
    return wilder(tr, n)


def levels_for(T, O, H, L, C):
    """(jenis, harga, aktif_mulai, aktif_akhir, ATR D1 saat dibuat)."""
    out = []
    D1 = agg(T, O, H, L, C, 86400); H4 = agg(T, O, H, L, C, 14400)
    W1 = agg(T, O, H, L, C, 7 * 86400, off=4 * 86400)            # epoch = Kamis → minggu mulai Senin 00:00 UTC
    aD = atr(D1["H"], D1["L"], D1["C"]); aH4 = atr(H4["H"], H4["L"], H4["C"])
    atrD = lambda t: float(aD[max(int(np.searchsorted(D1["T"], t)) - 1, 0)])
    for tf, G, sec in (("H4", H4, 14400), ("D1", D1, 86400)):
        for n in (2, 3, 5):
            for i in range(n, len(G["T"]) - n):
                t_on = int(G["T"][i + n]) + sec
                if G["H"][i] == G["H"][i - n:i + n + 1].max(): out.append((f"SWING-{tf}-n{n}", float(G["H"][i]), t_on, t_on + 30 * 86400, atrD(t_on)))
                if G["L"][i] == G["L"][i - n:i + n + 1].min(): out.append((f"SWING-{tf}-n{n}", float(G["L"][i]), t_on, t_on + 30 * 86400, atrD(t_on)))
    for nm, G, sec in (("PERIODE-hari", D1, 86400), ("PERIODE-minggu", W1, 7 * 86400)):
        for i in range(1, len(G["T"])):
            t_on = int(G["T"][i])
            out += [(nm, float(G["H"][i - 1]), t_on, t_on + sec, atrD(t_on)), (nm, float(G["L"][i - 1]), t_on, t_on + sec, atrD(t_on))]
    M = agg(T, O, H, L, C, 30 * 86400)
    for i in range(1, len(M["T"])):
        p = float(M["C"][i - 1]); s0 = 10 ** math.floor(math.log10(p)); t_on = int(M["T"][i]); t_off = t_on + 30 * 86400
        for f, nm in ((1.0, "BULAT-1"), (0.5, "BULAT-0,5"), (0.25, "BULAT-0,25")):
            st = s0 * f; lo, hi = math.ceil(p * 0.7 / st), math.floor(p * 1.3 / st)
            for m in range(max(lo, 1), hi + 1):
                lv = m * st
                if f < 1 and abs(lv / (s0 * f * 2) - round(lv / (s0 * f * 2))) < 1e-9: continue   # hanya yang bukan kelipatan langkah lebih besar
                out.append((nm, float(lv), t_on, t_off, atrD(t_on)))
    for i in range(3, len(H4["T"]) - 3):
        for nb in (1, 2, 3):
            b0 = i - nb + 1
            if b0 < 1 or np.any((H4["H"][b0:i + 1] - H4["L"][b0:i + 1]) > 0.5 * aH4[b0:i + 1]): continue
            zh, zl = H4["H"][b0:i + 1].max(), H4["L"][b0:i + 1].min()
            for k in range(1, 4):
                if i + k >= len(H4["T"]): break
                up, dn = H4["C"][i + k] - zh, zl - H4["C"][i + k]
                if up >= 2 * aH4[i] or dn >= 2 * aH4[i]:
                    t_on = int(H4["T"][i + k]) + 14400
                    out.append(("SD-demand" if up > 0 else "SD-supply", float((zh + zl) / 2), t_on, t_on + 30 * 86400, atrD(t_on)))
                    break
            break
    return out


def events(T, H, L, C, A, lv, shift=0.0):
    nm, p, t_on, t_off, aD = lv; p = p + shift * aD
    a, b = np.searchsorted(T, t_on), np.searchsorted(T, t_off)
    if b - a < 2: return []
    hi, lo, cl, at = H[a:b], L[a:b], C[a:b], A[a:b]
    touch = (lo <= p + 0.1 * at) & (hi >= p - 0.1 * at)
    out, nxt = [], 0
    for k in np.flatnonzero(touch):
        if k < 1 or k < nxt: continue
        pc, ak = cl[k - 1], at[k]
        if pc > p + 0.1 * ak: d = 1
        elif pc < p - 0.1 * ak: d = -1
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
    now = time.time() * 1000; coins = []
    for c in sb.COINS:
        p = f"{DATA}/klines/{c}.json"
        if not os.path.exists(p): continue
        rows = [x for x in json.load(open(p)) if x[5] < now]
        if rows and rows[0][0] < calendar.timegm((2019, 1, 1, 0, 0, 0)): coins.append((c, rows))
        if len(coins) >= 11: break
    R = collections.defaultdict(list)
    for c, rows in coins:
        a = np.array([x[:5] for x in rows], float); T = a[:, 0].astype(np.int64)
        O, H, L, C = a[:, 1], a[:, 2], a[:, 3], a[:, 4]; A = atr(H, L, C)
        lvs = levels_for(T, O, H, L, C)
        for lv in lvs:
            R[(lv[0], "nyata")] += events(T, H, L, C, A, lv)
            for _ in range(3):
                R[(lv[0], "acak")] += events(T, H, L, C, A, lv, shift=rng.choice((-1, 1)) * rng.uniform(0.5, 2.0))
        print(f"{c}: mulai {time.strftime('%Y-%m', time.gmtime(T[0]))} · {len(lvs)} level", flush=True)
    jenis = sorted({k[0] for k in R})
    grup = {"SWING-H4": [j for j in jenis if j.startswith("SWING-H4")], "SWING-D1": [j for j in jenis if j.startswith("SWING-D1")],
            "PERIODE": [j for j in jenis if j.startswith("PERIODE")], "BULAT": [j for j in jenis if j.startswith("BULAT")],
            "SD": [j for j in jenis if j.startswith("SD")]}
    hasil = {"koin": [c for c, _ in coins]}

    def nilai(nama, js):
        out = {}
        for pn, a0, a1 in PER:
            for d, dn in ((1, "support"), (-1, "resistance")):
                ev = {k: [x for j in js for x in R[(j, k)] if a0 <= x[0] < a1 and x[1] == d] for k in ("nyata", "acak")}
                if len(ev["nyata"]) < 50: out[(pn, dn)] = None; continue
                pr = lambda e: np.mean([x[2] == 1 for x in e]); pt = lambda e: np.mean([x[2] == -1 for x in e])
                mk = lambda e: np.array([time.gmtime(x[0]).tm_year * 12 + time.gmtime(x[0]).tm_mon for x in e])
                mn, ma = mk(ev["nyata"]), mk(ev["acak"])
                bn = np.array([x[2] == 1 for x in ev["nyata"]]); ba = np.array([x[2] == 1 for x in ev["acak"]])
                months = np.unique(np.concatenate([mn, ma]))
                sn = np.array([(bn[mn == m].sum(), (mn == m).sum()) for m in months], float)
                sa = np.array([(ba[ma == m].sum(), (ma == m).sum()) for m in months], float)
                pick = rng.integers(0, len(months), (2000, len(months)))
                a_, b_ = sn[pick].sum(1), sa[pick].sum(1)
                ok = (a_[:, 1] > 0) & (b_[:, 1] > 0)
                P = float(np.mean(a_[ok, 0] / a_[ok, 1] - b_[ok, 0] / b_[ok, 1] > 0))
                out[(pn, dn)] = dict(n=len(ev["nyata"]), pantul=round(pr(ev["nyata"]) * 100, 1), pantul_acak=round(pr(ev["acak"]) * 100, 1),
                                     tembus=round(pt(ev["nyata"]) * 100, 1), tembus_acak=round(pt(ev["acak"]) * 100, 1),
                                     lift=round((pr(ev["nyata"]) - pr(ev["acak"])) * 100, 1), P=round(P, 3))
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
