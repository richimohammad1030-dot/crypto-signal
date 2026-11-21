"""Saringan cepat FX MAJOR · 22 Nov 2026 (maks 10 ide, periode pilih IS 2015-2022 saja).
Juara = UTAMA + SUSULAN + LANJUT persis seperti forex_major/fx_live.py (dibangun vektor per seluruh hari, hasil sama dgn F.day).
Tiap ide diukur sebagai ARUS TAMBAHAN (standalone) + efek gabungan pada juara (trade/mgg, tahun minus, DD).
Pemakaian: python riset/fx/eksperimen/saringan_2026_11_22.py [is|full] [setra]  -> cetak tabel, simpan /tmp/fx_saring_<mode>.pkl"""
import os, sys, time, pickle
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "forex_major"))
import numpy as np
import backtest as B
from backtest import order, atr, prev_daily
import riset_putaran6 as P6          # spread asli Exness (+0,2 pip)
import riset_putaran7 as P7
import riset_putaran4 as R4
import fx_live as F
from riset_putaran2 import SPLIT, pf

END_SIG = 13 * 3600                  # pemicu tindak lanjut sebelum 20:00 WIB (sama dgn LANJUT)


def run(data, gen):
    return P6.run_gen(data, gen)


def juara(data, max_utama=2):
    B.MAX_DAY = max_utama
    try: main = B.portfolio(run(data, P6.utama_gen(F.UK)))
    finally: B.MAX_DAY = 4
    filled = {(t["pair"], t["t"] // 86400) for t in main}
    sus = run(data, P7.sus_gen(dict(F.SK, um=F.UK["dow"]), filled, F.UK["exp"]))
    b3 = run(data, P7.bot3_gen(F.B3K, main + sus))
    for t, k in [(x, "N3") for x in main] + [(x, "SUS") for x in sus] + [(x, "B3") for x in b3]: t["bot"] = k
    return main, sus, b3


def _mfe(P, t):
    H = P.h1; i0 = int(np.searchsorted(H["t"], t["t"])); i1 = int(np.searchsorted(H["t"], t["t_exit"]))
    r0 = abs(t["entry"] - t["sl"]); s = t["side"]
    return max(((H["h"][i] - t["entry"]) if s > 0 else (t["entry"] - H["l"][i])) for i in range(i0, i1 + 1)) / r0


def gen_after(base, kind, build):
    """Pemicu dari trade dasar (UTAMA+SUSULAN): kind 'sl' (R<=-0,5, kena SL) atau 'be' (keluar impas). build(P,t,a,i,i0,d)->order|None."""
    trig = {}
    for t in base:
        r = t["R"]; ok = (r <= -0.5 and t["why"] == "sl") if kind == "sl" else (-0.5 < r <= 0.05 and t["why"] != "close")
        if ok and (t["t_exit"] % 86400) < END_SIG: trig.setdefault((t["pair"], t["t_exit"] // 86400), t)
    def gen(P):
        idx, D = prev_daily(P); A = atr(D); H = P.h1; pos = {int(x): i for i, x in enumerate(H["t"])}; out = {}
        for (pair, d), t in trig.items():
            if pair != P.name or d not in idx: continue
            t_on = (t["t_exit"] // 3600 + 1) * 3600; i = pos.get(t_on - 3600); i0 = pos.get(d * 86400)
            if i is None or i0 is None: continue
            o = build(P, t, A[idx[d]], i, i0, d, t_on)
            if o: out.setdefault(d, []).append(o)
        return out
    return gen


# ---- ide 1: BALAS struktur (balik, SL di ekstrem hari itu = puncak stop hunt, TP 1R) ----
def b_struktur(P, t, a, i, i0, d, t_on):
    H = P.h1; s = -t["side"]; px = H["c"][i]
    ext = H["h"][i0:i + 1].max() if t["side"] > 0 else H["l"][i0:i + 1].min()
    sl = ext - s * 0.05 * a; risk = abs(px - sl)
    if not (0.1 * a <= risk <= 0.6 * a): return None
    return order(P.name, "BALs", s, "market", px, sl, px + s * 1.0 * risk, t_on)


# ---- ide 2: BALAS hanya breakout palsu (SL <= 2 jam & MFE < 0,3R), balik SL/TP 0,3/0,45 ATR ----
def mk_palsu(Pm):
    def b(P, t, a, i, i0, d, t_on):
        if t["t_exit"] - t["t"] > 2 * 3600 or _mfe(Pm[P.name], t) >= 0.3: return None
        H = P.h1; s = -t["side"]; px = H["c"][i]
        return order(P.name, "BALp", s, "market", px, px - s * 0.3 * a, px + s * 0.45 * a, t_on)
    return b


# ---- ide 3: BALAS searah = tembus ulang ekstrem hari itu (stop hunt lalu lanjut) ----
def b_rebreak(P, t, a, i, i0, d, t_on):
    H = P.h1; s = t["side"]
    ext = H["h"][i0:i + 1].max() if s > 0 else H["l"][i0:i + 1].min()
    return order(P.name, "BALr", s, "stop", ext, ext - s * 0.3 * a, ext + s * 0.6 * a, t_on)


# ---- ide 6: pasang ulang setelah keluar BE (stop di entry lama, SL/TP 0,3/0,6, BE 0,5) ----
def b_rearm(P, t, a, i, i0, d, t_on):
    s = t["side"]; e = t["entry"]
    o = order(P.name, "RE", s, "stop", e + s * 0.05 * a, e - s * 0.25 * a, e + s * 0.65 * a, t_on); o["be"] = 0.5
    return o


# ---- ide 4/5: level bulan lalu / range minggu berjalan, hanya pair-hari tanpa isi UTAMA & SUSULAN ----
def gen_level(kind, busy):
    def gen(P):
        idx, D = prev_daily(P); A = atr(D); out = {}
        dd = D["t"] // 86400; wk = (dd + 3) // 7
        mon = np.array([time.gmtime(int(x)).tm_year * 12 + time.gmtime(int(x)).tm_mon for x in D["t"]])
        for d, j in idx.items():
            wd = (d + 3) % 7
            if j < 110 or wd == 0 or (P.name, d) in busy: continue
            if kind == "bulan":
                cm = time.gmtime(d * 86400); key = cm.tm_year * 12 + cm.tm_mon - 1; m = mon == key
            else:
                if wd < 2: continue                                   # Rabu-Jumat (Senin-kemarin >= 2 hari)
                m = (wk == (d + 3) // 7) & (dd < d)
            if not m.any(): continue
            hh, ll = D["h"][m].max(), D["l"][m].min(); a = A[j]; t0 = d * 86400; lst = []
            if kind == "minggu_jalan":
                wm = wk == ((d + 3) // 7 - 1)
                if not wm.any(): continue
                ph, pl = D["h"][wm].max(), D["l"][wm].min()
                if hh >= ph: hh = None
                if ll <= pl: ll = None
            if hh is not None and D["h"][j] < hh and hh - D["c"][j] <= 2 * a:
                lst.append(order(P.name, "LV", 1, "stop", hh, hh - 0.3 * a, hh + 0.6 * a, t0, oco=("LV", d)))
            if ll is not None and D["l"][j] > ll and D["c"][j] - ll <= 2 * a:
                lst.append(order(P.name, "LV", -1, "stop", ll, ll + 0.3 * a, ll - 0.6 * a, t0, oco=("LV", d)))
            for o in lst: o["be"] = 0.5
            if lst: out[d] = lst
        return out
    return gen


# ---- ide 9 [lit]: aliran akhir bulan London fix — fade arah USD bulan berjalan di hari kerja terakhir ----
def gen_akhir_bulan(P):
    idx, D = prev_daily(P); A = atr(D); H = P.h1; pos = {int(x): i for i, x in enumerate(H["t"])}; out = {}
    for d, j in idx.items():
        wd = (d + 3) % 7
        if j < 30 or wd > 4: continue
        nxt = d + (3 if wd == 4 else 1)
        if time.gmtime(nxt * 86400).tm_mon == time.gmtime(d * 86400).tm_mon: continue   # bukan hari kerja terakhir
        i = pos.get(d * 86400 + 7 * 3600)                                                # candle close 15:00 WIB
        if i is None: continue
        cm = time.gmtime(d * 86400); first = None
        for k in range(j, -1, -1):
            if time.gmtime(int(D["t"][k])).tm_mon != cm.tm_mon: first = k; break
        if first is None: continue
        mtd = H["c"][i] - D["c"][first]; a = A[j]
        if abs(mtd) < 0.5 * a: continue
        s = -1 if mtd > 0 else 1; px = H["c"][i]
        out[d] = [order(P.name, "AB", s, "market", px, px - s * 0.6 * a, px + s * 0.6 * a, d * 86400 + 8 * 3600)]
    return out


# ---- ide 10 [lit]: momentum keranjang USD (indeks USD sintetis 7 pair tembus range 20 hari) -> 2 pair terkuat searah ----
def gen_usd_mom(data, look=20, mom=5):
    ser = {}
    for P in data:
        D = P.d1; s = 1 if P.name.startswith("USD") else -1
        lc = np.log(D["c"]); ser[P.name] = {int(t // 86400): (s * lc[k], k) for k, t in enumerate(D["t"])}
    days = sorted(set.intersection(*[set(v) for v in ser.values()]))
    r = [0.0] + [np.mean([ser[p][days[k]][0] - ser[p][days[k - 1]][0] for p in ser]) for k in range(1, len(days))]
    idx = np.cumsum(r); sig = {}
    for k in range(look + mom + 1, len(days) - 1):
        d = days[k] + 1
        while (d + 3) % 7 > 4: d += 1                                   # hari bursa berikutnya
        if (d + 3) % 7 == 0: continue                                   # tanpa Senin
        last = idx[k]; w = idx[k - look:k]
        u = 1 if last > w.max() else -1 if last < w.min() else 0
        if not u: continue
        sc = sorted(((ser[p][days[k]][0] - ser[p][days[k - mom]][0]) * u, p) for p in ser)[::-1][:2]
        for _, p in sc: sig[(p, d)] = u
    def gen(P):
        idxd, D = prev_daily(P); A = atr(D); out = {}
        for d, j in idxd.items():
            u = sig.get((P.name, d))
            if not u or j < 30: continue
            s = u if P.name.startswith("USD") else -u; px = D["c"][j]; a = A[j]
            out[d] = [order(P.name, "USDM", s, "market", px, px - s * 0.5 * a, px + s * 1.0 * a, d * 86400)]
        return out
    return gen


def ystat(tr, lo, hi):
    tr = [t for t in tr if lo <= t["t"] < hi]
    if not tr: return dict(n=0)
    R = np.array([t["R"] for t in sorted(tr, key=lambda x: x["t"])]); eq = np.cumsum(R)
    dd = float((np.maximum.accumulate(np.insert(eq, 0, 0))[1:] - eq).max()); yrs = {}
    for t in tr: y = time.gmtime(t["t"]).tm_year; yrs[y] = yrs.get(y, 0) + t["R"]
    w = (hi - lo) / 86400 / 7
    return dict(n=len(R), avg=float(R.mean()), pf=pf(tr)[0], R=float(R.sum()), dd=dd, wr=float((R > 0).mean()), pw=len(R) / w,
                neg=sum(v < 0 for v in yrs.values()), ny=len(yrs), worst=min(yrs.values()), years={y: round(v, 1) for y, v in sorted(yrs.items())})


def fmt(s):
    if not s["n"]: return "0 trade"
    return (f"n {s['n']:4d} | {s['avg']:+.3f}R/tr | PF {s['pf']:.2f} | {s['R']:+6.1f}R | DD {s['dd']:5.1f} | WR {s['wr']:.0%} | "
            f"{s['pw']:.2f}/mgg | th- {s['neg']}/{s['ny']} terburuk {s['worst']:+.1f}")


def ide_semua(data, base3):
    main, sus, b3 = base3; base = main + sus; Pm = {P.name: P for P in data}
    busy = {(t["pair"], t["t"] // 86400) for t in base}
    out = {}
    out["1 BALAS struktur (balik, SL ekstrem hari, TP 1R)"] = ("tambah", run(data, gen_after(base, "sl", b_struktur)))
    out["2 BALAS palsu (SL<=2j & MFE<0,3R, balik 0,3/0,45)"] = ("tambah", run(data, gen_after(base, "sl", mk_palsu(Pm))))
    out["3 BALAS tembus ulang ekstrem (searah, 0,3/0,6)"] = ("tambah", run(data, gen_after(base, "sl", b_rebreak)))
    out["4 Level bulan lalu (pair-hari kosong) [ide 7]"] = ("tambah", run(data, gen_level("bulan", busy)))
    out["5 Range minggu berjalan Rabu-Jumat (pair-hari kosong)"] = ("tambah", run(data, gen_level("minggu_jalan", busy)))
    out["6 Pasang ulang setelah BE (stop di entry)"] = ("tambah", run(data, gen_after(base, "be", b_rearm)))
    m3, s3, b33 = juara(data, 3)
    out["7 UTAMA maks 3 posisi/hari"] = ("ganti", m3 + s3 + b33)
    out["9 Akhir bulan fade USD MTD (London fix) [lit]"] = ("tambah", run(data, gen_akhir_bulan))
    out["10 Momentum keranjang USD 20 hari, 2 pair terkuat [lit]"] = ("tambah", run(data, gen_usd_mom(data)))
    return out


def bobot_vol(data, tr):
    """ide 8 [ide 11]: risiko 1,25x bila ATR14/ATR100 >= 1,1, 0,75x bila < 0,9 (rezim volatilitas hari sebelumnya)."""
    rv = {}
    for P in data:
        idx, D = prev_daily(P); A, A100 = atr(D), atr(D, 100)
        for d, j in idx.items(): rv[(P.name, d)] = A[j] / A100[j]
    out = []
    for t in tr:
        r = rv.get((t["pair"], t["t"] // 86400), 1.0); w = 1.25 if r >= 1.1 else 0.75 if r < 0.9 else 1.0
        out.append(dict(t, R=t["R"] * w))
    return out


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "is"
    t0 = time.time()
    if len(sys.argv) > 2 and sys.argv[2] == "setra":
        os.environ["FX_DATA"] = "data_setra/{pair}_1h.json.gz"
    data = [B.load(p) for p in F.PAIRS]
    lo, hi = (1420070400, SPLIT) if mode == "is" else (SPLIT, 1900000000) if mode == "oos" else (0, 1900000000)
    if mode == "oos" or mode == "full":
        hi = min(hi, max(int(P.t[-1]) for P in data) + 1); lo = max(lo, min(int(P.t[0]) for P in data) + 120 * 86400)
    base3 = juara(data); J = sorted(sum(base3, []), key=lambda x: x["t"])
    print(f"data {time.time() - t0:.0f}s | periode {time.strftime('%Y-%m-%d', time.gmtime(lo))} .. {time.strftime('%Y-%m-%d', time.gmtime(hi - 1))}")
    sj = ystat(J, lo, hi); print("JUARA 3 bot :", fmt(sj), sj["years"])
    for k, tr in zip(("UTAMA", "SUSULAN", "LANJUT"), base3): print(f"  {k:<10}:", fmt(ystat(tr, lo, hi)))
    res = ide_semua(data, base3)
    res["8 Risiko per rezim vol ATR14/ATR100 [ide 11]"] = ("ganti", bobot_vol(data, J))
    print("\n| ide | arus sendiri | GABUNG juara+ide |")
    for k, (how, tr) in res.items():
        g = tr if how == "ganti" else J + tr
        s1 = ystat(tr, lo, hi); s2 = ystat(g, lo, hi)
        print(f"{k}\n   sendiri: {fmt(s1)}\n   gabung : {fmt(s2)}  (R/DD {s2['R'] / max(s2['dd'], 1):.2f} vs juara {sj['R'] / max(sj['dd'], 1):.2f})")
    pickle.dump(dict(J=J, base3=base3, res=res), open(f"/tmp/fx_saring_{mode}{'_setra' if len(sys.argv) > 2 else ''}.pkl", "wb"))
    print(f"\nselesai {time.time() - t0:.0f}s")
