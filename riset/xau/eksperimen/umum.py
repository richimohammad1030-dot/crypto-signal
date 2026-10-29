"""Mesin replay XAU untuk eksperimen: salinan urutan GoldEngine.step (gold_bot.py) dengan kait (hook)
pada saat pemasangan order 07:00 WIB. Tanpa hook, hasilnya harus identik dengan backtest_xau.py.
Kait `plan(i, ctx)` mengembalikan None (lewati hari) atau dict:
  {"buy": bool, "sell": bool, "w_buy": float, "w_sell": float}  (w = bobot risiko, 1 = penuh)
"""
import sys, os, json, datetime as dt
import numpy as np

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, REPO)
import gold_bot as gb
from signal_bot import atr

BIAYA_USD = 0.40
INF = float("inf")


def muat(path):
    rows = json.load(open(path))
    T = [r[0] for r in rows]; O = [r[1] for r in rows]; H = [r[2] for r in rows]
    L = [r[3] for r in rows]; C = [r[4] for r in rows]
    return T, O, H, L, C


def ema(x, n):
    out, k, e = [], 2 / (n + 1), None
    for v in x:
        e = v if e is None else e + k * (v - e)
        out.append(e)
    return out


def replay(T, O, H, L, C, plan=None, range_n=gb.RANGE_N, sl_atr=gb.SL_ATR, rr=gb.RR,
           place_hr=gb.PLACE_HOUR_UTC, close_hr=gb.CLOSE_HOUR_UTC):
    A = gb_atr = atr(H, L, C, gb.ATR_N)
    ctx = {"T": T, "O": O, "H": H, "L": L, "C": C, "A": A}
    trades, pend, pos = [], None, None

    def rec(d, e, ex, r0, t0, t1, why, w):
        R = (ex - e) * d / r0 if r0 else 0.0
        trades.append(dict(d=d, t0=t0, t1=t1, e=e, ex=ex, r0=r0, R=R, w=w, why=why))

    for i in range(250, len(T)):
        t, hr = T[i], (T[i] // 3600) % 24
        if pos is None and pend:
            b, s_ = pend["buy"], pend["sell"]
            hit = None
            if H[i] >= b[0]:
                hit = (1, max(b[0], O[i]), b[1], b[2], pend["w_buy"])
            elif L[i] <= s_[0]:
                hit = (-1, min(s_[0], O[i]), s_[1], s_[2], pend["w_sell"])
            if hit:
                d, fill, slp, tpp, w = hit
                r0 = abs(fill - slp)
                pend = None
                pos = {"d": d, "e": fill, "sl": slp, "tp": tpp, "r0": r0, "t0": t, "w": w}
                if (d == 1 and L[i] <= slp) or (d == -1 and H[i] >= slp):
                    rec(d, fill, slp, r0, t, t, "SL", w); pos = None
        elif pos is not None and pos["t0"] < t:
            d = pos["d"]
            if (d == 1 and L[i] <= pos["sl"]) or (d == -1 and H[i] >= pos["sl"]):
                rec(d, pos["e"], pos["sl"], pos["r0"], pos["t0"], t, "SL", pos["w"]); pos = None
            elif (d == 1 and H[i] >= pos["tp"]) or (d == -1 and L[i] <= pos["tp"]):
                rec(d, pos["e"], pos["tp"], pos["r0"], pos["t0"], t, "TP", pos["w"]); pos = None
        if hr == close_hr:
            pend = None
            if pos:
                rec(pos["d"], pos["e"], C[i], pos["r0"], pos["t0"], t, "23:00", pos["w"]); pos = None
        if hr == place_hr and pos is None:
            hi, lo, a = max(H[i - range_n + 1:i + 1]), min(L[i - range_n + 1:i + 1]), A[i]
            if abs(sl_atr * a) > 0.5:
                p = {"buy": True, "sell": True, "w_buy": 1.0, "w_sell": 1.0}
                if plan is not None:
                    p = plan(i, ctx, hi, lo, a)
                if p is None:
                    continue
                pend = {"buy": [hi if p["buy"] else INF, hi - sl_atr * a, hi + rr * sl_atr * a],
                        "sell": [lo if p["sell"] else -INF, lo + sl_atr * a, lo - rr * sl_atr * a],
                        "w_buy": p.get("w_buy", 1.0), "w_sell": p.get("w_sell", 1.0)}
    return trades


def wib(ts):
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc) + dt.timedelta(hours=7)


def net(trades):
    """R bersih biaya per trade (sudah dikali bobot risiko)."""
    return np.array([(t["R"] - BIAYA_USD / t["r0"]) * t["w"] for t in trades]) if trades else np.array([])


def stat(trades):
    r = net(trades)
    if len(r) == 0:
        return dict(n=0, tot=0, avg=0, wr=0, dd=0, ratio=0, tanpa2=0)
    eq = np.cumsum(r); dd = float(np.max(np.maximum.accumulate(np.concatenate([[0], eq]))[1:] - eq))
    k = max(1, int(round(len(r) * 0.02)))
    tanpa = float(np.sort(r)[:-k].sum())
    tot = float(r.sum())
    return dict(n=len(r), tot=tot, avg=tot / len(r), wr=float(np.mean([t["R"] > 0 for t in trades])),
                dd=dd, ratio=tot / dd if dd > 0 else float("inf"), tanpa2=tanpa)


def kuartal(t):
    w = wib(t["t0"]); return f"{w.year}Q{(w.month - 1) // 3 + 1}"


def paruh(t):
    return "P1 2025" if wib(t["t0"]).year == 2025 else "P2 2026"


def ringkas(nama, trades):
    out = {"semua": stat(trades)}
    for key in ("P1 2025", "P2 2026"):
        out[key] = stat([t for t in trades if paruh(t) == key])
    qs = sorted({kuartal(t) for t in trades})
    out["kuartal"] = {q: stat([t for t in trades if kuartal(t) == q]) for q in qs}
    return out


def baris(nama, s):
    return (f"| {nama} | {s['n']} | {s['tot']:+.1f} | {s['avg']:+.3f} | {s['wr']*100:.0f}% | "
            f"{s['dd']:.1f} | {s['ratio']:.2f} | {s['tanpa2']:+.1f} |")


HDR = "| Varian | Trade | Total R | R/trade | Win | DD | R/DD | Tanpa 2% top |\n|---|---|---|---|---|---|---|---|"


def nilai(juara, var):
    """Kriteria LOLOS dari PROSEDUR.md. Kembalikan (keputusan, alasan list)."""
    alasan = []
    ok = True
    for key in ("P1 2025", "P2 2026"):
        a, b = juara[key]["ratio"], var[key]["ratio"]
        naik = (b - a) / abs(a) if a else 0
        if not (a > 0 and naik >= 0.15):
            ok = False; alasan.append(f"R/DD {key}: {a:.2f} -> {b:.2f} ({naik*100:+.0f}%)")
    qs = sorted(juara["kuartal"])[-7:]
    tidak_buruk = sum(1 for q in qs if var["kuartal"].get(q, stat([]))["tot"] >= juara["kuartal"][q]["tot"] - 1e-9)
    if tidak_buruk < 5:
        ok = False; alasan.append(f"tidak lebih buruk hanya di {tidak_buruk}/7 kuartal")
    turun = 1 - var["semua"]["n"] / juara["semua"]["n"]
    if turun > 0.40:
        ok = False; alasan.append(f"trade turun {turun*100:.0f}%")
    if var["semua"]["tanpa2"] <= 0:
        ok = False; alasan.append("negatif tanpa 2% trade terbaik")
    return ("LOLOS" if ok else "GAGAL"), alasan, tidak_buruk
