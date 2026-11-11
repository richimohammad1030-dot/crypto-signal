"""EVALUASI LENGKAP juara intraday v3 (11 Nov 2026, permintaan pemilik). Mesin = riset/backtest_intraday.py (tidak diubah);
replay penuh portofolio memakai tahap0_semua_tahun_2026-11-06.py (PIT = uji utama, daftar tetap = pembanding = koin bot live).
Isi: per periode, per tahun, per koin, per arah/modul, per jam & sesi isi (WIB), win, RR, PF, R/trade, DD, beruntun,
trade/minggu; tahun minus; DD terdalam & lama pulih; porsi biaya & funding terhadap edge; peluang tahun minus.
Komponen biaya: salinan sim() yang juga mencatat R kotor, R fee (maker/taker termasuk slippage) dan R funding (hasil bersih sama persis).
Pemakaian: python riset/intraday/eksperimen/evaluasi_2026-11-11.py <repo> <data> <out_dir>"""
import collections, csv, json, math, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
REPO, DATA, OUT = sys.argv[1:4]
import importlib.util
spec = importlib.util.spec_from_file_location("t0", os.path.join(HERE, "tahap0_semua_tahun_2026-11-06.py"))
M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)
import numpy as np
bi = M.bi

def sim_komp(D, i0, d, lim, r0, tp, valid_bars, hold_bars, rsi_exit, P):
    r, nxt = SIM_ASLI(D, i0, d, lim, r0, tp, valid_bars, hold_bars, rsi_exit, P)
    if r["filled"]:
        T = D["T"]; j0 = int(np.searchsorted(T, r["t_fill"])); j = int(np.searchsorted(T, r["t_exit"] - 900))
        fill, px = r["entry"], r["exit"]; cx = P["MAKER"] if r["why"] == "TP" else P["TAKER"]
        r["Rg"] = float(d * (px - fill) / r0)
        r["Rfee"] = float(-(P["MAKER"] + cx) / 100 * fill / r0)
        r["Rfund"] = float(-bi.funding_cost(D, int(T[j0]), int(T[j]), d) * fill / r0)
    return r, nxt
SIM_ASLI = M.SIM0
M.SIM0 = sim_komp

YR = M.YR
def grup(o): return "A-long" if o["m"] == "A" else ("B-long" if o["d"] == 1 else "B-short")
def jam(o): return (time.gmtime(o["t_fill"]).tm_hour + 7) % 24

def dd_episodes(tr):
    day = collections.defaultdict(float)
    for o in tr: day[o["t_exit"] // 86400] += o["R"]
    ks = sorted(day); eq = np.cumsum([day[k] for k in ks])
    eps, pk, pk_i, cur = [], 0.0, -1, None
    for i, v in enumerate(eq):
        if v >= pk:
            if cur: cur["pulih"] = ks[i]; eps.append(cur); cur = None
            pk, pk_i = v, i
        else:
            dd = pk - v
            if cur is None: cur = dict(puncak=ks[pk_i] if pk_i >= 0 else ks[0], dd=dd, dasar=ks[i], pulih=None)
            elif dd > cur["dd"]: cur["dd"], cur["dasar"] = dd, ks[i]
    if cur: eps.append(cur)
    tgl = lambda k: time.strftime("%Y-%m-%d", time.gmtime(k * 86400)) if k else "belum"
    eps = sorted(eps, key=lambda e: -e["dd"])[:5]
    return [dict(dd=round(e["dd"], 1), puncak=tgl(e["puncak"]), dasar=tgl(e["dasar"]), pulih=tgl(e["pulih"]),
                 hari_turun=e["dasar"] - e["puncak"], hari_pulih=(e["pulih"] - e["dasar"]) if e["pulih"] else None,
                 hari_total=(e["pulih"] - e["puncak"]) if e["pulih"] else None) for e in eps]

def ekuitas_pct(tr, risk=0.01):
    eq, pk, dd, beg = 1.0, 1.0, 0.0, None
    for o in sorted(tr, key=lambda o: o["t_exit"]):
        eq *= 1 + risk * o["R"]; pk = max(pk, eq); dd = max(dd, 1 - eq / pk)
    yrs = (tr[-1]["t_exit"] - tr[0]["t"]) / 31557600
    return round((eq ** (1 / yrs) - 1) * 100, 1), round(dd * 100, 1)

def peluang_minus(tr):
    """(a) dari R tahunan (disetahunkan untuk tahun parsial), normal; (b) dari R/trade iid × trade/thn; (c) bootstrap blok bulan."""
    yr = collections.defaultdict(list)
    for o in tr: yr[YR(o)].append(o)
    ann = []
    for y, v in sorted(yr.items()):
        t0 = max(min(o["t"] for o in v), time.mktime((y, 1, 1, 0, 0, 0, 0, 0, 0)) - time.timezone)
        t1 = min(max(o["t_exit"] for o in v), time.mktime((y + 1, 1, 1, 0, 0, 0, 0, 0, 0)) - time.timezone)
        frac = max((t1 - t0) / 31557600, 0.1); ann.append(sum(o["R"] for o in v) / frac)
    ann = np.array(ann); mu, sd = ann.mean(), ann.std(ddof=1)
    Phi = lambda z: 0.5 * (1 + math.erf(z / math.sqrt(2)))
    R = np.array([o["R"] for o in tr]); yrs = (tr[-1]["t_exit"] - tr[0]["t"]) / 31557600; n = len(R) / yrs
    a = Phi(-mu / sd); b = Phi(-(R.mean() * n) / (R.std(ddof=1) * math.sqrt(n)))
    mon = collections.defaultdict(float)
    for o in tr: mon[time.strftime("%Y-%m", time.gmtime(o["t"]))] += o["R"]
    mv = np.array(list(mon.values())); rng = np.random.default_rng(7)
    c = float((rng.choice(mv, size=(20000, 12)).sum(1) <= 0).mean())
    return dict(R_thn_rata=round(mu, 1), R_thn_sd=round(sd, 1), p_normal_tahunan=round(a * 100, 1),
                R_trade=round(float(R.mean()), 4), sd_trade=round(float(R.std(ddof=1)), 3), trade_thn=round(n), p_iid=round(b * 100, 1),
                p_bootstrap_bulan=round(c * 100, 1), edge_2x_untuk_p5=round(float(1.645 * sd / max(mu, 1e-9)), 2))

def laporan(nama, sent, tr, f):
    pr = lambda *a: print(*a, file=f, flush=True)
    base = M.laporan(nama, sent, tr, f)
    pr("-- per periode --")
    for lab, a, b in (("2020-2023", None, bi.IS_END), ("2024-skrg", bi.IS_END, None), ("live v3 (30 Okt+)", 1793350800, None), ("semua", None, None)):
        t = [o for o in tr if (a is None or o["t"] >= a) and (b is None or o["t"] < b)]
        if not t: pr(f"{lab:<18} -"); continue
        s = M.stat(t); st = bi.stats(t, [o for o in sent if (a is None or o["t"] >= a) and (b is None or o["t"] < b)])
        pr(f"{lab:<18} n={s['n']} /mg={s['per_mg']} R={s['R']:+} R/tr={s['avg']:+} win={s['win']}% RR={s['RR']} PF={s['PF']} DD={s['DD']} "
           f"R/thn={st.get('totR_thn')} rasio={st.get('rasio')} beruntun {s['mb']}/{s['kb']} fill={st.get('fill')}%")
    pr("-- per modul (semua): R/tr, win, RR, PF --")
    for g in ("A-long", "B-long", "B-short"):
        s = M.stat([o for o in tr if grup(o) == g]); pr(f"{g:<8} n={s['n']} R={s['R']:+} R/tr={s['avg']:+} win={s['win']}% RR={s['RR']} PF={s['PF']} DD={s['DD']} beruntun {s['mb']}/{s['kb']}")
    pr("-- per jam isi WIB (n / R / R/tr / win) --")
    for h in range(24):
        t = [o for o in tr if jam(o) == h]
        if t: s = M.stat(t); pr(f"{h:02d} n={s['n']:4d} R={s['R']:+7.1f} R/tr={s['avg']:+.3f} win={s['win']}%")
    pc = collections.defaultdict(list)
    for o in tr: pc[o["c"]].append(o)
    pr(f"-- per koin ({len(pc)} koin; ≥ 20 trade) --")
    for c in sorted(pc, key=lambda c: -sum(o["R"] for o in pc[c])):
        if len(pc[c]) >= 20:
            s = M.stat(pc[c]); pr(f"{c:<7} n={s['n']:4d} R={s['R']:+6.1f} R/tr={s['avg']:+.3f} win={s['win']}% PF={s['PF']}")
    eps = dd_episodes(tr); cagr, ddp = ekuitas_pct(tr)
    pr("-- 5 drawdown terdalam (R, harian) --")
    for e in eps: pr(f"DD {e['dd']}R puncak {e['puncak']} dasar {e['dasar']} pulih {e['pulih']} · turun {e['hari_turun']} hari, pulih {e['hari_pulih']} hari, total {e['hari_total']} hari")
    pr(f"CAGR risiko 1% {cagr}% · DD ekuitas {ddp}%")
    Rg = sum(o["Rg"] for o in tr); Rf = sum(o["Rfee"] for o in tr); Ru = sum(o["Rfund"] for o in tr); Rn = sum(o["R"] for o in tr)
    pr(f"-- biaya: R kotor {Rg:+.1f} · fee+slip {Rf:+.1f} ({Rf / len(tr):+.4f}R/trade) · funding {Ru:+.1f} ({Ru / len(tr):+.4f}R/trade) · bersih {Rn:+.1f}")
    pr(f"   fee = {-Rf / Rg * 100:.0f}% edge kotor · funding = {-Ru / Rg * 100:+.0f}% edge kotor · cek selisih bersih {Rg + Rf + Ru - Rn:+.4f}")
    for g in ("A-long", "B-long", "B-short"):
        t = [o for o in tr if grup(o) == g]
        pr(f"   {g:<8} kotor {sum(o['Rg'] for o in t) / len(t):+.4f} fee {sum(o['Rfee'] for o in t) / len(t):+.4f} funding {sum(o['Rfund'] for o in t) / len(t):+.4f} bersih {sum(o['R'] for o in t) / len(t):+.4f} R/trade")
    for y in sorted({YR(o) for o in tr}):
        t = [o for o in tr if YR(o) == y]
        pr(f"   {y} kotor {sum(o['Rg'] for o in t):+6.1f} fee {sum(o['Rfee'] for o in t):+6.1f} funding {sum(o['Rfund'] for o in t):+5.1f} bersih {sum(o['R'] for o in t):+6.1f}")
    pm = peluang_minus(tr)
    pr(f"-- peluang tahun minus: {pm}")
    base.update(periode=None, dd_eps=eps, cagr=cagr, ddp=ddp, biaya=dict(kotor=round(Rg, 1), fee=round(Rf, 1), funding=round(Ru, 1), bersih=round(Rn, 1)), peluang=pm)
    return base

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    f = open(f"{OUT}/evaluasi.txt", "w")
    class Tee:
        def write(self, s): f.write(s); sys.stdout.write(s)
        def flush(self): f.flush(); sys.stdout.flush()
    tee = Tee(); hasil = {}
    for nama, pm in (("PIT biaya juara (UJI UTAMA)", True), ("TETAP = koin bot live (pembanding)", False)):
        s, t = M.jalankan(pm, False)
        hasil[nama] = laporan(nama, s, t, tee)
        with open(f"{OUT}/trades_{'pit' if pm else 'tetap'}.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["t", "t_fill", "t_exit", "c", "m", "d", "vr", "entry", "exit", "R", "Rg", "Rfee", "Rfund", "why"], extrasaction="ignore")
            w.writeheader(); w.writerows(t)
    json.dump(hasil, open(f"{OUT}/evaluasi.json", "w"), indent=1, default=str)
