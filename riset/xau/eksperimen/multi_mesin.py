"""Mesin riset BASELINE bot XAU multi-strategi (31 Okt 2026, ide #34) - acuan uji kesetaraan (riset/replay_xau.py),
patokan kesehatan (riset/baseline_xau.py), dan catatan bayangan (riset/xau/bayangan.py).
Maks 1 posisi/hari, keputusan 07:00 WIB: RSI(2) H1 <= MR_BUY -> BUY market / >= MR_SELL -> SELL market (SL 3 ATR, tanpa TP);
selain itu K6 (OCO 2 sisi, hari dilewati bila sisi lawan tren EMA200 H1 terisi duluan; SL 1,5 ATR, TP 4R). Tutup 23:00 WIB.
Konstanta diambil dari gold_bot.py agar bot & riset tidak bisa berbeda diam-diam."""
import numpy as np
import audit_mesin as m
import strat_mesin as sm
gb = m.gb


def rsi(C, n):
    C = np.asarray(C, float); d = np.diff(C, prepend=C[0]); up, dn = np.where(d > 0, d, 0), np.where(d < 0, -d, 0)
    a = 1 / n; au = np.zeros(len(C)); ad = np.zeros(len(C))
    for j in range(1, len(C)):
        au[j] = au[j - 1] + a * (up[j] - au[j - 1]); ad[j] = ad[j - 1] + a * (dn[j] - ad[j - 1])
    return 100 - 100 / (1 + au / np.maximum(ad, 1e-12))


def sinyal_mr(D, mr_buy=None, mr_sell=None, n=None):
    T, C = D[0], D[4]; R2 = rsi(C, n or gb.MR_N)
    lo_, hi_ = mr_buy or gb.MR_BUY, mr_sell or gb.MR_SELL
    HR = ((T // 3600) % 24).astype(int)
    return {int(i): (1 if R2[i] <= lo_ else -1) for i in np.flatnonzero(HR == sm.PLACE) if R2[i] <= lo_ or R2[i] >= hi_}


def trades_mr(D, A, sig=None, sl=None, tp=None):
    sig = sinyal_mr(D) if sig is None else sig
    return sm.jalan(D, A, lambda i: [(sig[i], "market", None)] if i in sig else None, sl=sl or gb.MR_SL_ATR, tp=tp)


def trades_k6(D, A, F, ambigu="buy", sl=None, tp="bot"):
    sp = {"tren_lawan_w": ("ema200", 0.0), "ambigu": ambigu}
    if sl: sp["sl_atr"] = sl
    if tp != "bot": sp["rr"] = tp
    return m.potong(m.jalankan(sp, D, A, F))


def baseline(D, A, F, ambigu="buy", mr=None, k6=None, sig=None):
    """Trade baseline: tiap trade diberi x['strat'] = 'MR' / 'K6'."""
    sig = sinyal_mr(D) if sig is None else sig
    mr = {x["ip"]: x for x in (trades_mr(D, A, sig) if mr is None else mr)}
    k6 = {x["ip"]: x for x in (trades_k6(D, A, F, ambigu) if k6 is None else k6)}
    out = []
    for i in sorted(set(mr) | set(k6)):
        x = mr.get(i) if i in sig else k6.get(i)
        if x: out.append(dict(x, strat="MR" if i in sig else "K6"))
    return sorted(out, key=lambda x: x["t1"])
