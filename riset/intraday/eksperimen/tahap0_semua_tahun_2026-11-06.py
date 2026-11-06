"""TAHAP 0 (6 Nov 2026) · verifikasi "untung di SEMUA tahun kalender" untuk juara intraday v3.
Mesin = riset/backtest_intraday.py (orders + sim, TIDAK diubah) dengan replay penuh portofolio; daftar koin SESUAI MASANYA
(riset/pit.py, termasuk koin delisting) = uji utama, daftar tetap (signal_bot.COINS) = pembanding.
Eksekusi:
  standar : biaya juara (limit/TP maker 0,02%, SL/market/waktu taker 0,07% termasuk slippage) + funding tiap settlement.
  stres   : taker 0,12% (slippage tambahan 0,05%) DAN limit entry hanya terisi jika harga MENEMBUS limit >= 0,05%
            (model antrian: sentuhan pas di limit tidak dianggap terisi), TP limit juga harus tembus 0,05%.
Keluaran: tabel per tahun (R bersih, trade/minggu, win, RR, PF, DD dalam tahun, menang/kalah beruntun), versi tanpa 2% trade
terbaik (per tahun dan global), per modul/arah, per sesi (jam isi WIB), per koin, bulan terburuk; CSV trade.
Pemakaian: python riset/intraday/eksperimen/tahap0_semua_tahun_2026-11-06.py <repo> <data> <out_dir>"""
import collections, csv, json, os, sys, time
REPO, DATA, OUT = sys.argv[1:4]
sys.path.insert(0, REPO); sys.path.insert(0, os.path.join(REPO, "riset"))
import numpy as np
import backtest_intraday as bi, pit, signal_bot as sb

P0 = dict(bi.PARAM)
SIM0 = bi.sim

# ------------------------------------------------------------------ eksekusi stres (salinan sim() + antrian/slippage)
EPS = 0.0005
def sim_stres(D, i0, d, lim, r0, tp, valid_bars, hold_bars, rsi_exit, P):
    T, O, H, L, C = D["T"], D["O"], D["H"], D["L"], D["C"]; n = len(T)
    t_exp = int(T[i0]) + valid_bars * 900
    thr = lim * (1 - d * EPS)                                  # harga harus menembus limit 0,05%
    for j in range(i0, min(i0 + valid_bars, n)):
        if (d == 1 and L[j] <= thr) or (d == -1 and H[j] >= thr):
            fill, j0 = (min(lim, O[j]) if d == 1 else max(lim, O[j])), j; break
    else:
        return dict(filled=False, t_exp=t_exp), min(i0 + valid_bars, n)
    sl = fill - d * r0
    tpx = None if tp is None else tp * (1 + d * EPS)
    for j in range(j0, min(j0 + hold_bars, n)):
        if (d == 1 and L[j] <= sl) or (d == -1 and H[j] >= sl):
            px = sl if j == j0 else (min(sl, O[j]) if d == 1 else max(sl, O[j])); cx, why = P["TAKER"], "SL"; break
        if tpx is not None and ((d == 1 and H[j] >= tpx) or (d == -1 and L[j] <= tpx)) and not (j == j0 and d * (C[j] - tpx) < 0):
            px, cx, why = tp, P["MAKER"], "TP"; break
    else:
        j = min(j0 + hold_bars, n) - 1; px, cx, why = C[j], P["TAKER"], "WAKTU"
    pnl = d * (px - fill) - (P["MAKER"] + cx) / 100 * fill - bi.funding_cost(D, int(T[j0]), int(T[j]), d) * fill
    return dict(filled=True, t_exp=t_exp, t_fill=int(T[j0]), t_exit=int(T[j]) + 900, R=float(pnl / r0), why=why,
                entry=float(fill), exit=float(px)), j + 1

# ------------------------------------------------------------------ data
pit._load(DATA)
ALL = sorted({c for m in pit._SNAP for c in pit.ranked(DATA, m)[:70]} | set(sb.COINS))
H1, M15 = bi.load(DATA, ALL)
first = {c: int(D["T"][900]) for c, D in M15.items() if len(D["T"]) > 900}
uni = pit.universe_fn(DATA, lambda c, t: c in first and c in H1 and first[c] <= t)
FIX = {c: i for i, c in enumerate(sb.COINS)}

def jalankan(pitmode, stres=False, P=None):
    P = dict(P0, **(P or {}))
    if stres: P["TAKER"] = 0.12
    bi.sim = sim_stres if stres else SIM0
    try:
        if pitmode:
            rank_fn = lambda c, t: uni(t).index(c) if c in uni(t) else 999
            ords = [o for o in bi.orders(H1, {c: M15[c] for c in M15}, P, rank_fn) if o["c"] in uni(o["t"])]
            rank_of = lambda o: uni(o["t"]).index(o["c"])
        else:
            ords = bi.orders(H1, {c: M15[c] for c in sb.COINS if c in M15}, P)
            rank_of = lambda o: FIX[o["c"]]
    finally:
        bi.sim = SIM0
    ev = sorted(ords, key=lambda o: (o["t"], rank_of(o)))
    pend, pos, sent, taken = [], [], [], []
    def settle(now):
        nonlocal pend, pos
        while True:
            cand = [(o["t_fill"], rank_of(o), k) for k, (_, o) in enumerate(pend) if o["filled"] and o["t_fill"] < now]
            if not cand: break
            tf, _, k = min(cand); o = pend[k][1]
            pos = [(e, c) for e, c in pos if e > tf]
            pend = [p for p in pend if p[1] is not o and p[0] > tf]
            if len(pos) < P["CAP"]:
                pos.append((o["t_exit"], o["c"])); taken.append(o)
                if len(pos) >= P["CAP"]: pend = []
        pend = [p for p in pend if p[0] > now]; pos = [(e, c) for e, c in pos if e > now]
    for o in ev:
        settle(o["t"])
        if o["c"] in {c for _, c in pos} | {x["c"] for _, x in pend} or len(pend) >= P["PEND"] or len(pos) >= P["CAP"]: continue
        sent.append(o); pend.append(((o["t_fill"] + 1) if o["filled"] else o["t_exp"], o))
    settle(2_000_000_000)
    return sent, sorted(taken, key=lambda o: o["t_exit"])

# ------------------------------------------------------------------ statistik
YR = lambda o: time.gmtime(o["t"]).tm_year
def sesi(o):
    h = (time.gmtime(o["t_fill"]).tm_hour + 7) % 24              # jam isi WIB
    return "07-15 Asia" if 7 <= h < 15 else "15-20 Eropa" if 15 <= h < 20 else "20-02 AS" if (h >= 20 or h < 2) else "02-07 sepi"
def grup(o): return "A-long" if o["m"] == "A" else ("B-long" if o["d"] == 1 else "B-short")

def stat(tr):
    if not tr: return dict(n=0, R=0.0)
    tr = sorted(tr, key=lambda o: o["t_exit"]); R = np.array([o["R"] for o in tr])
    t0 = min(o["t"] for o in tr); t1 = max(o["t_exit"] for o in tr); mg = max((t1 - t0) / 604800, 1)
    day = collections.defaultdict(float)
    for o in tr: day[o["t_exit"] // 86400] += o["R"]
    eq = np.cumsum([day[k] for k in sorted(day)]); dd = float((np.maximum.accumulate(np.concatenate([[0], eq]))[1:] - eq).max())
    w = l = bw = bl = 0
    for r in R: w, l = (w + 1, 0) if r > 0 else (0, l + 1); bw, bl = max(bw, w), max(bl, l)
    win, los = R[R > 0], R[R <= 0]
    k = max(1, len(R) // 50); tanpa = float(np.sort(R)[::-1][k:].sum())
    return dict(n=len(R), per_mg=round(len(R) / mg, 1), R=round(float(R.sum()), 1), avg=round(float(R.mean()), 3),
                win=round(float((R > 0).mean() * 100), 1), RR=round(float(win.mean() / -los.mean()), 2) if len(win) and len(los) else None,
                PF=round(float(win.sum() / -los.sum()), 2) if len(los) else None, DD=round(dd, 1), mb=bw, kb=bl, tanpa2=round(tanpa, 1))

def laporan(nama, sent, tr, f):
    pr = lambda *a: print(*a, file=f, flush=True)
    pr(f"\n================ {nama} ================")
    S = stat(tr); pr(f"SEMUA  n={S['n']} R={S['R']:+} avg={S['avg']:+} win={S['win']}% RR={S['RR']} PF={S['PF']} DD={S['DD']}R "
                     f"beruntun {S['mb']}/{S['kb']} tanpa2%={S['tanpa2']:+} fill={len(tr)/max(len(sent),1)*100:.0f}%")
    # tanpa 2% terbaik GLOBAL: buang top 2% seluruh periode, lalu hitung per tahun
    k = max(1, len(tr) // 50); top = set(id(o) for o in sorted(tr, key=lambda o: -o["R"])[:k])
    pr(f"{'tahun':<6}{'n':>5}{'tr/mg':>7}{'R':>8}{'avg':>8}{'win%':>7}{'RR':>6}{'PF':>6}{'DD':>6}{'mb/kb':>7}{'-2%thn':>8}{'-2%glob':>8}")
    rows = {}
    for y in sorted({YR(o) for o in tr}):
        t = [o for o in tr if YR(o) == y]; s = stat(t); g = round(sum(o["R"] for o in t if id(o) not in top), 1)
        rows[y] = dict(s, tanpa2_glob=g)
        pr(f"{y:<6}{s['n']:>5}{s['per_mg']:>7}{s['R']:>+8.1f}{s['avg']:>+8.3f}{s['win']:>7}{s['RR']:>6}{s['PF']:>6}{s['DD']:>6}{str(s['mb'])+'/'+str(s['kb']):>7}{s['tanpa2']:>+8.1f}{g:>+8.1f}")
    neg = [y for y, s in rows.items() if s["R"] <= 0]; neg2 = [y for y, s in rows.items() if s["tanpa2"] <= 0]
    neg3 = [y for y, s in rows.items() if s["tanpa2_glob"] <= 0]
    worst = min(rows, key=lambda y: rows[y]["R"])
    pr(f"tahun minus: {neg or '-'} · tanpa 2% (per tahun): {neg2 or '-'} · tanpa 2% (global): {neg3 or '-'} · tahun terburuk {worst} ({rows[worst]['R']:+}R)")
    def tabel(judul, keyf):
        keys = sorted({keyf(o) for o in tr})
        pr(f"-- per tahun × {judul} (R bersih / n) --")
        pr(f"{'':<12}" + "".join(f"{y:>12}" for y in sorted(rows)) + f"{'total':>12}")
        out = {}
        for kk in keys:
            cells = []
            for y in sorted(rows):
                t = [o for o in tr if YR(o) == y and keyf(o) == kk]
                cells.append(f"{sum(o['R'] for o in t):+.1f}/{len(t)}")
            t = [o for o in tr if keyf(o) == kk]
            out[kk] = round(sum(o["R"] for o in t), 1)
            pr(f"{kk:<12}" + "".join(f"{c:>12}" for c in cells) + f"{f'{out[kk]:+.1f}/{len(t)}':>12}")
        return out
    tabel("modul", grup)
    tabel("arah", lambda o: "long" if o["d"] == 1 else "short")
    tabel("sesi isi", sesi)
    tabel("keluar", lambda o: o["why"])
    # per koin
    pc = collections.defaultdict(list)
    for o in tr: pc[o["c"]].append(o["R"])
    ks = sorted(pc, key=lambda c: sum(pc[c]))
    pr(f"-- per koin: {len(pc)} koin, {sum(sum(v) > 0 for v in pc.values())} positif · terburuk: " +
       ", ".join(f"{c} {sum(pc[c]):+.1f}/{len(pc[c])}" for c in ks[:8]) + " · terbaik: " +
       ", ".join(f"{c} {sum(pc[c]):+.1f}/{len(pc[c])}" for c in ks[::-1][:8]))
    top_share = sorted(((sum(v), c) for c, v in pc.items()), reverse=True)
    pr(f"   tanpa 3 koin terbaik: total {S['R'] - sum(x for x, _ in top_share[:3]):+.1f}R")
    # per tahun tanpa koin terbaik tahun itu
    pr("   per tahun tanpa koin terbaik tahun itu: " + " ".join(
        f"{y}:{rows[y]['R'] - max(sum(o['R'] for o in tr if YR(o) == y and o['c'] == c) for c in {o['c'] for o in tr if YR(o) == y}):+.0f}" for y in sorted(rows)))
    # bulan
    mon = collections.defaultdict(float)
    for o in tr: mon[time.strftime("%Y-%m", time.gmtime(o["t"]))] += o["R"]
    mv = sorted(mon.items(), key=lambda x: x[1])
    pr(f"-- bulan: {len(mon)} bulan, positif {sum(v > 0 for v in mon.values())} ({sum(v > 0 for v in mon.values()) / len(mon) * 100:.0f}%) · 6 terburuk: " +
       ", ".join(f"{k} {v:+.1f}" for k, v in mv[:6]))
    # 12 bulan bergulir
    ks = sorted(mon); roll = [(ks[i], sum(mon[k] for k in ks[i - 11:i + 1])) for i in range(11, len(ks))]
    rmin = min(roll, key=lambda x: x[1])
    pr(f"-- 12 bulan bergulir terendah: berakhir {rmin[0]} {rmin[1]:+.1f}R · jendela 12 bln minus: {sum(v <= 0 for _, v in roll)}/{len(roll)}")
    return dict(semua=S, tahun=rows, minus=neg, minus_tanpa2=neg2, minus_tanpa2_glob=neg3, terburuk=worst, bulan=dict(mon))

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    f = open(f"{OUT}/tahap0.txt", "w")
    class Tee:
        def write(self, s): f.write(s); sys.stdout.write(s)
        def flush(self): f.flush(); sys.stdout.flush()
    tee = Tee(); hasil = {}
    for nama, pm, st in (("PIT standar (UJI UTAMA)", True, False), ("TETAP standar (pembanding)", False, False),
                         ("PIT stres eksekusi", True, True), ("TETAP stres eksekusi", False, True)):
        s, t = jalankan(pm, st)
        hasil[nama] = laporan(nama, s, t, tee)
        with open(f"{OUT}/trades_{'pit' if pm else 'tetap'}_{'stres' if st else 'std'}.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["t", "t_fill", "t_exit", "c", "m", "d", "vr", "entry", "exit", "R", "why"], extrasaction="ignore")
            w.writeheader(); w.writerows(t)
    json.dump(hasil, open(f"{OUT}/tahap0.json", "w"), indent=1, default=str)
