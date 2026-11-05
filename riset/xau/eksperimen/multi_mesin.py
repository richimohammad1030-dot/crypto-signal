"""Mesin riset BASELINE bot XAU multi-strategi (31 Okt 2026, ide #34) - acuan uji kesetaraan (riset/replay_xau.py),
patokan kesehatan (riset/baseline_xau.py), dan catatan bayangan (riset/xau/bayangan.py).
Maks 1 posisi/hari, keputusan 07:00 WIB: RSI(2) H1 <= MR_BUY -> BUY market / >= MR_SELL -> SELL market (SL 3 ATR, tanpa TP);
selain itu K6 (OCO 2 sisi, hari dilewati bila sisi lawan tren EMA200 H1 terisi duluan; SL 1,5 ATR, TP 4R). Tutup 23:00 WIB.
Sejak 6 Nov 2026: hibrida #42b (tren harian SMA100 close 07:00 turun -> cermin SELL >= 70 / BUY <= 15), MR SELL >= 85 (#40),
SUSULAN (ide #37) pada hari K6 dilewati - RSI(2) di jam keputusan pertama (close 09:00..21:00 WIB) setelah
batas batal tersentuh <= SUS_BUY / >= SUS_SELL -> market di open berikutnya, SL 3 ATR, TP 1R, tutup 23:00 WIB.
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
    sig = sinyal_live(D) if sig is None else sig
    return sm.jalan(D, A, lambda i: [(sig[i], "market", None)] if i in sig else None, sl=sl or gb.MR_SL_ATR, tp=tp)


def trades_k6(D, A, F, ambigu="buy", sl=None, tp="bot"):
    sp = {"tren_lawan_w": ("ema200", 0.0), "ambigu": ambigu}
    if sl: sp["sl_atr"] = sl
    if tp != "bot": sp["rr"] = tp
    return m.potong(m.jalankan(sp, D, A, F))


def trades_sus(D, A, F, ambigu="buy", sig=None):
    """Susulan (sama persis dengan riset/xau/eksperimen/susulan.py kandidat S3, konstanta dari gold_bot)."""
    T, O, H, L, C = D
    HR = ((T // 3600) % 24).astype(int); R2 = rsi(C, gb.MR_N); jam = set(gb.SUS_JAM_UTC)
    sig = sinyal_live(D) if sig is None else sig
    out = []
    for x in m.jalankan({"tren_lawan_w": ("ema200", 0.0), "ambigu": ambigu}, D, A, F):
        if x["w"] != 0 or x["ip"] in sig: continue
        q = x["i0"]
        while q < len(T) and HR[q] not in jam and HR[q] != sm.CLOSE: q += 1
        if q >= len(T) - 1 or HR[q] not in jam: continue
        if not (R2[q] <= gb.SUS_BUY or R2[q] >= gb.SUS_SELL): continue
        d = 1 if R2[q] <= gb.SUS_BUY else -1; dist = gb.SUS_SL_ATR * A[q]
        if dist <= 0.5: continue
        j = q + 1; e = O[j]
        ex, t1, why = sm._kelola(D, j, d, e, e - d * dist, e + d * gb.SUS_TP_R * dist)
        out.append(dict(d=d, e=e, ex=ex, r0=dist, t0=T[j], t1=t1, why=why, w=1.0, ip=x["ip"], i0=j, R=(ex - e) * d / dist,
                        strat="SUS"))
    return out


def sinyal_live(D):
    """Sinyal MR bot live (sejak 6 Nov 2026 = hibrida #42b)."""
    return sinyal_hibrida(D)


def baseline(D, A, F, ambigu="buy", mr=None, k6=None, sig=None, sus=None):
    """Trade baseline (= bot live): tiap trade diberi x['strat'] = 'MR' / 'K6' / 'SUS'. sus=False -> tanpa susulan."""
    sig = sinyal_live(D) if sig is None else sig
    mr = {x["ip"]: x for x in (trades_mr(D, A, sig) if mr is None else mr)}
    k6 = {x["ip"]: x for x in (trades_k6(D, A, F, ambigu) if k6 is None else k6)}
    out = []
    for i in sorted(set(mr) | set(k6)):
        x = mr.get(i) if i in sig else k6.get(i)
        if x: out.append(dict(x, strat="MR" if i in sig else "K6"))
    if sus is not False:
        out += trades_sus(D, A, F, ambigu, sig) if sus is None else sus
    return sorted(out, key=lambda x: x["t1"])


def sinyal_connors(D, n=200, b=30.0, kuat=85.0):
    """Ide #42 (Connors cermin): tren D1 (close 07:00 > SMA n hari close 07:00) naik -> BUY RSI2 <= b, SELL hanya RSI2 >= kuat;
    tren turun -> cermin (SELL >= 100-b, BUY hanya <= 100-kuat)."""
    T, C = D[0], D[4]; R2 = rsi(C, gb.MR_N); HR = ((T // 3600) % 24).astype(int)
    i07 = np.flatnonzero(HR == sm.PLACE); c07 = C[i07]; cs = np.cumsum(np.insert(c07, 0, 0)); out = {}
    for k, i in enumerate(i07):
        if k < n - 1: continue
        ma = (cs[k + 1] - cs[k + 1 - n]) / n; r = R2[i]
        if c07[k] > ma:
            if r <= b: out[int(i)] = 1
            elif r >= kuat: out[int(i)] = -1
        else:
            if r >= 100 - b: out[int(i)] = -1
            elif r <= 100 - kuat: out[int(i)] = 1
    return out


def sinyal_hibrida(D, n=None, b=None, kuat=None):
    """Ide #42b: tren D1 naik (atau MA belum ada) -> sinyal MR live (MR_BUY/MR_SELL gold_bot); tren turun -> cermin Connors
    (SELL >= 100-b, BUY hanya <= 100-kuat)."""
    n = n or gb.TREND_D1_N; b = 100 - gb.MR_SELL_TURUN if b is None else b; kuat = 100 - gb.MR_BUY_TURUN if kuat is None else kuat
    T, C = D[0], D[4]; R2 = rsi(C, gb.MR_N); HR = ((T // 3600) % 24).astype(int)
    i07 = np.flatnonzero(HR == sm.PLACE); c07 = C[i07]; cs = np.cumsum(np.insert(c07, 0, 0)); out = {}
    for k, i in enumerate(i07):
        r = R2[i]
        if k < n - 1 or c07[k] > (cs[k + 1] - cs[k + 1 - n]) / n:
            if r <= gb.MR_BUY: out[int(i)] = 1
            elif r >= gb.MR_SELL: out[int(i)] = -1
        else:
            if r >= 100 - b: out[int(i)] = -1
            elif r <= 100 - kuat: out[int(i)] = 1
    return out
