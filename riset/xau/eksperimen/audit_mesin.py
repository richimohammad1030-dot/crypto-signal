"""Mesin audit XAU (30 Okt 2026): salinan urutan GoldEngine.step (gold_bot.py) dengan parameter yang bisa diubah
dan kait filter. Dengan parameter default + tanpa filter hasilnya WAJIB identik dengan riset/backtest_xau.py
(dicek oleh `cek_identik`).

Model eksekusi (sama dengan bot live):
- Order 07:00 WIB = BUY STOP di high range & SELL STOP di low range (OCO). Terisi di max(level, open) / min(level, open)
  (gap ikut dihitung). Jika satu candle menyentuh keduanya, BUY diambil (sama dengan bot).
- Candle saat terisi: hanya SL yang dicek (konservatif). Setelahnya SL dicek sebelum TP.
- Jam tutup: order menunggu dibatalkan, posisi ditutup di close candle.
- Biaya: `biaya` USD per trade (default 0,40 = spread + komisi) + `slip` USD tambahan per trade (stress test).
Waktu: jam UTC dari open candle. PLACE 23 = candle 06:00-07:00 WIB (close 07:00 WIB). CLOSE 15 = candle yang close 23:00 WIB.
"""
import sys, os, json, gzip, datetime as dt, math
import numpy as np

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, REPO)
import gold_bot as gb
from signal_bot import atr

INF = float("inf")


def muat(path):
    rows = json.load(gzip.open(path, "rt") if path.endswith(".gz") else open(path))
    return [np.array([r[k] for r in rows], dtype=float) for k in range(5)]


def ema(x, n):
    out, k, e = np.empty(len(x)), 2 / (n + 1), None
    for j, v in enumerate(x):
        e = v if e is None else e + k * (v - e)
        out[j] = e
    return out


def replay(D, place_hr=gb.PLACE_HOUR_UTC, close_hr=gb.CLOSE_HOUR_UTC, range_n=gb.RANGE_N, sl_atr=gb.SL_ATR,
           rr=gb.RR, atr_n=gb.ATR_N, plan=None, A=None, start=250, buf=0.0, sl_mode="atr", be_r=None, ambigu="buy"):
    """D = (T, O, H, L, C) numpy. plan(i, hi, lo, a) -> None (lewati) atau (buy_ok, sell_ok, bobot).
    buf = entry digeser buf x ATR di luar range. sl_mode "atr" (bot) | "range" (SL di sisi range seberang, sl_atr = faktor
    lebar range). ambigu = "buy" (bot) | "sell" | dict {t_candle: 1/-1} dari M1 (audit_m1.py): sisi yang diambil bila 1 candle menyentuh keduanya. be_r = SL digeser ke entry setelah harga mencapai +be_r R (berlaku mulai candle berikutnya)."""
    T, O, H, L, C = D
    if A is None:
        A = np.array(atr(list(H), list(L), list(C), atr_n))
    HR = ((T // 3600) % 24).astype(int)
    trades, pend, pos = [], None, None
    for i in range(start, len(T)):
        t, hr = T[i], HR[i]
        if pos is None and pend:
            b, s_ = pend["buy"], pend["sell"]
            hit = None
            jual_dulu = L[i] <= s_[0] and (ambigu == "sell" or (isinstance(ambigu, dict) and ambigu.get(int(t), 1) == -1))
            if H[i] >= b[0] and not jual_dulu:
                hit = (1, max(b[0], O[i]), b[1], b[2])
            elif L[i] <= s_[0]:
                hit = (-1, min(s_[0], O[i]), s_[1], s_[2])
            if hit:
                d, fill, slp, tpp = hit
                w_ = pend["w"][0 if d == 1 else 1] if isinstance(pend["w"], tuple) else pend["w"]
                pos = dict(d=d, e=fill, sl=slp, tp=tpp, r0=abs(fill - slp), t0=t, w=w_, i0=i, a=pend["a"], ip=pend["ip"])
                pend = None
                if (d == 1 and L[i] <= slp) or (d == -1 and H[i] >= slp):
                    pos.update(ex=slp, t1=t, why="SL"); trades.append(pos); pos = None
        elif pos is not None and pos["t0"] < t:
            d = pos["d"]
            if (d == 1 and L[i] <= pos["sl"]) or (d == -1 and H[i] >= pos["sl"]):
                pos.update(ex=pos["sl"], t1=t, why="SL"); trades.append(pos); pos = None
            elif (d == 1 and H[i] >= pos["tp"]) or (d == -1 and L[i] <= pos["tp"]):
                pos.update(ex=pos["tp"], t1=t, why="TP"); trades.append(pos); pos = None
            elif be_r is not None and ((d == 1 and H[i] >= pos["e"] + be_r * pos["r0"]) or
                                       (d == -1 and L[i] <= pos["e"] - be_r * pos["r0"])):
                pos["sl"] = pos["e"] if d * (pos["e"] - pos["sl"]) > 0 else pos["sl"]
        if hr == close_hr:
            pend = None
            if pos:
                pos.update(ex=C[i], t1=t, why="TUTUP"); trades.append(pos); pos = None
        if hr == place_hr and pos is None:
            hi, lo, a = H[i - range_n + 1:i + 1].max(), L[i - range_n + 1:i + 1].min(), A[i]
            dist = sl_atr * a if sl_mode == "atr" else sl_atr * (hi - lo)
            if abs(dist) > 0.5:
                p = (True, True, 1.0) if plan is None else plan(i, hi, lo, a)
                if p is None:
                    continue
                bo, so, w = p
                eb, es = hi + buf * a, lo - buf * a
                tpb = eb + rr * dist if rr else INF
                tps = es - rr * dist if rr else -INF
                pend = {"buy": [eb if bo else INF, eb - dist, tpb],
                        "sell": [es if so else -INF, es + dist, tps], "w": w, "a": a, "ip": i}
    for x in trades:
        x["R"] = (x["ex"] - x["e"]) * x["d"] / x["r0"] if x["r0"] else 0.0
    return trades


def cek_identik(repo_csv, trades):
    import csv
    ref = list(csv.DictReader(open(repo_csv)))
    if len(ref) != len(trades):
        return f"BEDA jumlah {len(ref)} vs {len(trades)}"
    bad = sum(1 for r, t in zip(ref, trades) if int(float(r["t0"])) != int(t["t0"]) or abs(float(r["R"]) - t["R"]) > 1e-9
              or int(r["d"]) != t["d"])
    return "IDENTIK" if bad == 0 else f"BEDA {bad} trade"


def wib(ts):
    return dt.datetime.fromtimestamp(int(ts), dt.timezone.utc) + dt.timedelta(hours=7)


def ts(s):
    return dt.datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp()


def net(trades, biaya=0.40, slip=0.0):
    return np.array([(x["R"] - (biaya + slip) / x["r0"]) * x["w"] for x in trades]) if trades else np.array([])


def potong(trades, a=None, b=None):
    """Trade dalam periode; trade berbobot 0 (hari dilewati) dibuang."""
    return [x for x in trades if x["w"] > 0 and (a is None or x["t0"] >= ts(a)) and (b is None or x["t0"] < ts(b))]


def streak(r, menang):
    best = cur = 0
    for v in r:
        cur = cur + 1 if (v > 0) == menang else 0
        best = max(best, cur)
    return best


def stat(trades, biaya=0.40, slip=0.0, risk=0.01, a=None, b=None):
    tr = potong(trades, a, b)
    r = net(tr, biaya, slip)
    if len(r) == 0:
        return dict(n=0, tot=0, avg=0, wr=0, dd=0, ratio=0, tanpa2=0, pf=0, rr=0, rthn=0, ddpct=0, cagr=0, wmax=0,
                    lmax=0, blnpos=0, perbln=0, thn={})
    t0 = ts(a) if a else tr[0]["t0"]; t1 = ts(b) if b else tr[-1]["t1"]
    yrs = max((min(t1, tr[-1]["t1"] + 86400) - t0) / (365.25 * 86400), 1 / 12)
    eq = np.cumsum(r); dd = float(np.max(np.maximum.accumulate(np.concatenate([[0], eq]))[1:] - eq))
    k = max(1, int(round(len(r) * 0.02)))
    win, los = r[r > 0], r[r <= 0]
    e = np.cumprod(1 + risk * r); pk = np.maximum.accumulate(np.concatenate([[1], e]))[1:]
    ddp = float(np.max(1 - e / pk))
    mon = {}
    thn = {}
    for x, v in zip(tr, r):
        w = wib(x["t0"]); mon[(w.year, w.month)] = mon.get((w.year, w.month), 0) + v
        thn[w.year] = thn.get(w.year, 0) + v
    tot = float(r.sum())
    return dict(n=len(r), tot=tot, avg=tot / len(r), wr=float((r > 0).mean()), dd=dd, ratio=tot / dd if dd > 0 else INF,
                tanpa2=float(np.sort(r)[:-k].sum()), pf=float(win.sum() / -los.sum()) if los.sum() < 0 else INF,
                rr=float(win.mean() / -los.mean()) if len(win) and len(los) and los.mean() < 0 else 0,
                rthn=tot / yrs, ddpct=ddp * 100, cagr=(float(e[-1]) ** (1 / yrs) - 1) * 100, wmax=streak(r, True),
                lmax=streak(r, False), blnpos=100 * np.mean([v > 0 for v in mon.values()]), perbln=len(r) / (yrs * 12),
                thn={k_: round(v, 1) for k_, v in sorted(thn.items())})


def baris(nama, s):
    return (f"{nama:<34} n={s['n']:>5} win={s['wr']*100:4.1f}% rr={s['rr']:.2f} exp={s['avg']:+.3f} pf={s['pf']:.2f} "
            f"R/thn={s['rthn']:+6.1f} DD={s['dd']:5.1f}R/{s['ddpct']:4.1f}% rasio={s['ratio']:+.2f} "
            f"CAGR={s['cagr']:+5.1f}% tanpa2%={s['tanpa2']:+6.1f} W/L={s['wmax']}/{s['lmax']} bln+={s['blnpos']:.0f}% "
            f"/bln={s['perbln']:.1f}")


def csv_out(path, trades, biaya=0.40, slip=0.0):
    import csv
    trades = potong(trades)
    r = net(trades, biaya, slip)
    with open(path, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["t0", "t1", "d", "R"])
        for x, v in zip(trades, r):
            w.writerow([int(x["t0"]), int(x["t1"]), x["d"], round(float(v), 5)])


# Periode audit (ditentukan SEBELUM eksplorasi)
PILIH = (None, "2022-01-01")         # 2015-2021: memilih parameter
UJI = ("2022-01-01", "2025-02-01")   # 2022 - Jan 2025: menguji
KONF = ("2025-02-01", None)          # Feb 2025 - sekarang (Setra): konfirmasi sekali


def fitur(D, A=None):
    """Fitur per candle (hanya memakai data sampai candle itu close; aman dipakai saat order 07:00 WIB)."""
    import pandas as pd
    T, O, H, L, C = D
    if A is None:
        A = np.array(atr(list(H), list(L), list(C), gb.ATR_N))
    F = {"atr_rel": A / C}
    s = pd.Series(F["atr_rel"])
    F["atr_vs1y"] = (s / s.rolling(5800, min_periods=2000).mean()).values          # ±1 tahun candle H1 emas
    F["pct1y"] = s.rolling(5800, min_periods=2000).rank(pct=True).values
    for n in (50, 100, 200):
        F[f"ema{n}"] = ema(C, n)
    # D1 versi "24 jam berakhir di candle ini": dihitung di setiap candle jam 23 UTC (07:00 WIB)
    HR = ((T // 3600) % 24).astype(int)
    idx = np.flatnonzero(HR == gb.PLACE_HOUR_UTC)
    dc, dtr, prev = [], [], None
    for j, i in enumerate(idx):
        lo_i = idx[j - 1] + 1 if j else max(0, i - 23)
        hh, ll = H[lo_i:i + 1].max(), L[lo_i:i + 1].min()
        tr_ = hh - ll if prev is None else max(hh, prev) - min(ll, prev)
        dc.append(C[i]); dtr.append(tr_); prev = C[i]
    dc, dtr = np.array(dc), np.array(dtr)
    d_atr = pd.Series(dtr).rolling(14).mean().values
    F["d_idx"] = idx
    F["d_atr_rel"] = np.full(len(T), np.nan); F["d_atr_rel"][idx] = d_atr / dc
    for n in (20, 50, 200):
        e = ema(dc, n); F[f"d_ema{n}"] = np.full(len(T), np.nan); F[f"d_ema{n}"][idx] = e
    F["d_ret20"] = np.full(len(T), np.nan); F["d_ret20"][idx] = pd.Series(dc).pct_change(20).values
    F["d_close"] = np.full(len(T), np.nan); F["d_close"][idx] = dc
    return F


def sambung(duka, setra, mulai="2025-02-01"):
    """Data sambung: Dukascopy sebelum `mulai`, Setra sejak `mulai` (agar fitur 1 tahun punya pemanasan)."""
    c = ts(mulai)
    a = [x[duka[0] < c] for x in duka]; b = [x[setra[0] >= c] for x in setra]
    return [np.concatenate([p, q]) for p, q in zip(a, b)]


def rencana(spec, D, F):
    """Bangun kait plan dari spesifikasi dict:
    vol=(fitur, ambang_min) · volmax=(fitur, ambang_maks) · hari=[hari WIB dilewati, 1=Senin] ·
    tren=nama ema (hanya searah) · tren_lawan_w=(ema, bobot sisi lawan tren; OCO tetap 2 sisi) · bobot=w (risiko relatif) · biaya_maks=c (R, asumsi SL 1,5 ATR)."""
    T, C = D[0], D[4]
    def plan(i, hi, lo, at):
        if "vol" in spec:
            k, x = spec["vol"]; v = F[k][i]
            if np.isnan(v) or v < x: return None
        if "volmax" in spec:
            k, x = spec["volmax"]; v = F[k][i]
            if np.isnan(v) or v > x: return None
        if "hari" in spec and int(wib(T[i] + 3600).strftime("%w")) in spec["hari"]: return None
        if "biaya_maks" in spec and 0.40 / (spec.get("sl_atr", 1.5) * at) > spec["biaya_maks"]: return None
        bo = so = True; wb = ws = 1.0
        if "tren" in spec:
            e = F[spec["tren"]][i]
            if np.isnan(e): return None
            bo, so = C[i] > e, C[i] < e
        if "tren_lawan_w" in spec:                     # OCO tetap 2 sisi; sisi lawan tren diberi bobot (0 = hari dilewati)
            k, wl = spec["tren_lawan_w"]; e = F[k][i]
            if np.isnan(e): return None
            return (True, True, (1.0, wl) if C[i] > e else (wl, 1.0))
        return (bo, so, spec.get("bobot", 1.0))
    return plan


MESIN_KW = ("place_hr", "close_hr", "range_n", "sl_atr", "rr", "buf", "sl_mode", "be_r", "ambigu")


def jalankan(spec, D, A, F):
    kw = {k: spec[k] for k in MESIN_KW if k in spec}
    plan = rencana(spec, D, F) if any(k in spec for k in ("vol", "volmax", "hari", "tren", "biaya_maks", "tren_lawan_w")) else None
    return replay(D, A=A, plan=plan, **kw)
