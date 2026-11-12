"""KURIKULUM SKILL intraday · Skill 1 SNR · TAHAP 1b (13 Nov 2026): apakah TEMBUSAN level diikuti LANJUTAN?
Tahap 1 (11 Nov) lulus: level PERIODE (high/low hari & minggu sebelumnya) dan SWING-D1 lebih sering DITEMBUS dari level acak.
Pertanyaan 1b: setelah tembus (harga menembus >= 0,5 ATR H1 melewati level), apakah harga LANJUT searah tembusan lebih sering
daripada setelah tembusan level ACAK (level yang sama digeser ±U(0,5; 2) ATR D1, 3 salinan; pengenal level & peristiwa
sama dengan skrip 11 Nov)?
Definisi (H1, mulai candle tembus g, tanpa melihat masa depan dalam pengenal level):
  LANJUT = dalam 12 candle setelah g harga mencapai level + 1,5 ATR searah tembusan (yaitu +1 ATR lagi) SEBELUM ada close kembali
           di sisi asal level (gagal tembus / "fakeout"). GAGAL = close kembali di sisi asal lebih dulu. Selain itu netral.
  Juga: return rata-rata close g -> close g+6 dan g+12, searah tembusan, dalam ATR H1 (nyata vs acak).
LULUS 1b bila lift lanjut (nyata - acak) P >= 0,90 di 2020-22 DAN 2023-26 untuk kedua arah (tembus ke bawah support, ke atas
resistance). Bila lanjutan TIDAK lebih sering -> tembusan hanya "sentuh-dalam" (likuiditas) lalu balik, dan pemakaian tahap 2 berbeda.
Pemakaian: python riset/intraday/eksperimen/skill_snr_1b_2026-11-13.py <repo> <data_dir> [out.json]"""
import collections, importlib.util, json, os, sys, time
REPO, DATA = sys.argv[1:3]; OUTJ = sys.argv[3] if len(sys.argv) > 3 else None
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("snr0", os.path.join(HERE, "skill_snr_2026-11-11.py"))
snr0 = importlib.util.module_from_spec(spec); spec.loader.exec_module(snr0)
import numpy as np
bi, sb, PER = snr0.bi, snr0.sb, snr0.PER
rng = np.random.default_rng(13)

def breaks(T, H, L, C, A, lv, shift=0.0):
    """Peristiwa TEMBUS satu level: (t, arah_tembus, hasil, ret6, ret12). arah -1 = tembus support ke bawah, +1 = resistance ke atas."""
    nm, p, t_on, t_off, aD = lv; p = p + shift * aD
    a, b = np.searchsorted(T, t_on), np.searchsorted(T, t_off)
    if b - a < 2: return []
    out, k, n = [], max(a, 1), len(T)
    while k < b:
        ak = A[k]; pc = C[k - 1]
        d = 0
        if pc > p + 0.1 * ak and L[k] <= p - 0.5 * ak: d = -1           # dari atas, tembus ke bawah
        elif pc < p - 0.1 * ak and H[k] >= p + 0.5 * ak: d = 1           # dari bawah, tembus ke atas
        if d == 0: k += 1; continue
        res = 0
        for j in range(k + 1, min(k + 13, n)):
            if d * (C[j] - p) < 0: res = -1; break                        # close kembali di sisi asal
            if (d == 1 and H[j] >= p + 1.5 * ak) or (d == -1 and L[j] <= p - 1.5 * ak): res = 1; break
        r6 = d * (C[min(k + 6, n - 1)] - C[k]) / ak; r12 = d * (C[min(k + 12, n - 1)] - C[k]) / ak
        out.append((int(T[k]), d, res, float(r6), float(r12))); k += 12
    return out

def main():
    R = collections.defaultdict(list)
    for c in sb.COINS[:25]:
        f = f"{DATA}/klines/{c}.json"
        rows = [x for x in bi.jload(f) if x[5] < time.time() * 1000] if os.path.exists(f) else []
        if len(rows) < 5000: continue
        a = np.array([x[:5] for x in rows], float); T = (a[:, 0] // 1000 if a[0, 0] > 1e11 else a[:, 0]).astype(np.int64)
        O, H, L, C = a[:, 1], a[:, 2], a[:, 3], a[:, 4]; A = snr0.atr(H, L, C)
        lvs = [lv for lv in snr0.levels_for(T, O, H, L, C) if lv[0].startswith(("PERIODE", "SWING-D1"))]
        for lv in lvs:
            g = "PERIODE" if lv[0].startswith("PERIODE") else "SWING-D1"
            R[(g, "nyata")] += breaks(T, H, L, C, A, lv)
            for _ in range(3):
                R[(g, "acak")] += breaks(T, H, L, C, A, lv, shift=rng.choice((-1, 1)) * rng.uniform(0.5, 2.0))
        print(f"{c}: {len(lvs)} level", flush=True)
    hasil = {}
    for g in ("PERIODE", "SWING-D1"):
        out = {}
        for pn, t0, t1 in PER:
            for d, dn in ((-1, "tembus-bawah"), (1, "tembus-atas")):
                ev = {kd: [x for x in R[(g, kd)] if t0 <= x[0] < t1 and x[1] == d] for kd in ("nyata", "acak")}
                if len(ev["nyata"]) < 50: out[f"{pn} {dn}"] = None; continue
                mk = lambda e: np.array([time.gmtime(x[0]).tm_year * 12 + time.gmtime(x[0]).tm_mon for x in e])
                mn, ma = mk(ev["nyata"]), mk(ev["acak"])
                ln, la = np.array([x[2] == 1 for x in ev["nyata"]]), np.array([x[2] == 1 for x in ev["acak"]])
                fn, fa = np.array([x[2] == -1 for x in ev["nyata"]]), np.array([x[2] == -1 for x in ev["acak"]])
                r12n, r12a = np.array([x[4] for x in ev["nyata"]]), np.array([x[4] for x in ev["acak"]])
                months = np.unique(np.concatenate([mn, ma]))
                sn = {m: (ln[mn == m].sum(), (mn == m).sum(), r12n[mn == m].sum()) for m in months}
                sa = {m: (la[ma == m].sum(), (ma == m).sum(), r12a[ma == m].sum()) for m in months}
                bs, br = [], []
                for _ in range(2000):
                    pick = rng.choice(months, len(months))
                    a1, n1, s1 = (sum(sn[m][i] for m in pick) for i in range(3)); a2, n2, s2 = (sum(sa[m][i] for m in pick) for i in range(3))
                    if n1 and n2: bs.append(a1 / n1 - a2 / n2); br.append(s1 / n1 - s2 / n2)
                out[f"{pn} {dn}"] = dict(n=len(ln), lanjut=round(ln.mean() * 100, 1), lanjut_acak=round(la.mean() * 100, 1),
                                        gagal=round(fn.mean() * 100, 1), gagal_acak=round(fa.mean() * 100, 1),
                                        lift=round((ln.mean() - la.mean()) * 100, 1), P=round(float(np.mean(np.array(bs) > 0)), 3),
                                        ret6=round(float(np.mean([x[3] for x in ev["nyata"]])), 3), ret6_acak=round(float(np.mean([x[3] for x in ev["acak"]])), 3),
                                        ret12=round(float(r12n.mean()), 3), ret12_acak=round(float(r12a.mean()), 3), P_ret12=round(float(np.mean(np.array(br) > 0)), 3))
        lulus = all(v is not None and v["P"] >= 0.90 for v in out.values())
        kebalikan = all(v is not None and v["P"] <= 0.10 for v in out.values())
        hasil[g] = dict(lulus=lulus, kebalikan=kebalikan, **out)
        print(f"\n{g}: {'LULUS TAHAP 1b (tembusan diikuti lanjutan)' if lulus else ('KEBALIKAN: tembusan lebih sering GAGAL' if kebalikan else 'belum / tidak konsisten')}")
        for k, v in out.items():
            print(f"  {k:<22} " + ("n<50" if v is None else
                  f"n={v['n']:6d} lanjut {v['lanjut']:5.1f}% vs acak {v['lanjut_acak']:5.1f}% (lift {v['lift']:+5.1f}, P {v['P']:.2f}) · gagal {v['gagal']:5.1f}% vs {v['gagal_acak']:5.1f}%"
                  f" · ret12 {v['ret12']:+.3f} vs {v['ret12_acak']:+.3f} ATR (P {v['P_ret12']:.2f})"))
    if OUTJ: json.dump(hasil, open(OUTJ, "w"), indent=1)

if __name__ == "__main__":
    main()
