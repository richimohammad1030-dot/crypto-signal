"""Mesin XAU 'logika harian dalam jendela tetap' (31 Okt 2026, permintaan pemilik):
SINYAL TETAP 07:00 WIB dan SEMUA DITUTUP 23:00 WIB (aturan pemilik yang tidak boleh berubah). Yang boleh berubah: arah, cara masuk,
SL/TP. Satu arah per hari (tanpa OCO) -> tidak ada masalah candle ambigu BUY/SELL.
Arah dari data harian (bar 24 jam yang berakhir 07:00 WIB): tren Donchian 20 hari (gaya bot swing crypto), EMA D1, momentum (TSMOM).
Masuk: "market" (open candle 07:00), "limit" (pullback k x ATR H1), "stop" (breakout high/low range 3 candle).
Model eksekusi sama dengan mesin audit: candle saat terisi hanya cek SL, lalu SL sebelum TP, tutup di close candle 23:00 WIB.
Biaya 0,40 USD/trade (+ slip opsional di audit_mesin.stat)."""
import numpy as np
import audit_mesin as m

PLACE, CLOSE = m.gb.PLACE_HOUR_UTC, m.gb.CLOSE_HOUR_UTC


def harian(D):
    """Bar harian (24 jam berakhir di candle 07:00 WIB): indeks candle, O H L C harian."""
    T, O, H, L, C = D
    HR = ((T // 3600) % 24).astype(int)
    idx = np.flatnonzero(HR == PLACE)
    dh, dl, dc = [], [], []
    for j, i in enumerate(idx):
        lo_i = idx[j - 1] + 1 if j else max(0, i - 23)
        dh.append(H[lo_i:i + 1].max()); dl.append(L[lo_i:i + 1].min()); dc.append(C[i])
    dh, dl, dc = np.array(dh), np.array(dl), np.array(dc)
    tr = np.maximum(dh, np.r_[dc[0], dc[:-1]]) - np.minimum(dl, np.r_[dc[0], dc[:-1]])
    datr = np.convolve(tr, np.ones(14) / 14, mode="full")[:len(tr)]; datr[:14] = np.nan
    return idx, dh, dl, dc, datr


def arah_harian(dh, dl, dc, jenis, n):
    """Arah (+1/-1/0) per hari, hanya memakai data sampai bar hari itu."""
    k = len(dc); d = np.zeros(k)
    if jenis == "donchian":                       # tren seperti bot swing: breakout n hari mengubah arah, bertahan sampai breakout lawan
        st = 0
        for j in range(n + 1, k):
            if dc[j] > dh[j - n:j].max(): st = 1
            elif dc[j] < dl[j - n:j].min(): st = -1
            d[j] = st
    elif jenis == "ema":
        e = m.ema(dc, n); d[n:] = np.sign(dc[n:] - e[n:])
    elif jenis == "mom":                          # time-series momentum n hari
        d[n:] = np.sign(dc[n:] - dc[:-n])
    return d


def simulasi(D, A, arah, idx, masuk="market", k=0.5, sl=1.5, rr=None, sl_d1=None, datr=None, range_n=3, sisi=(1, -1)):
    """arah[j] untuk hari j (idx[j] = candle 07:00). sl dalam ATR H1 (atau sl_d1 x ATR harian bila diisi)."""
    T, O, H, L, C = D
    HR = ((T // 3600) % 24).astype(int)
    trades = []
    for j, i in enumerate(idx):
        d = int(arah[j])
        if d == 0 or d not in sisi or i < 250 or i + 1 >= len(T):
            continue
        a = A[i]
        dist = sl_d1 * datr[j] if sl_d1 else sl * a
        if not dist or np.isnan(dist) or dist <= 0.5:
            continue
        if masuk == "market":
            lvl = None
        elif masuk == "limit":
            lvl = C[i] - d * k * a
        else:                                   # stop di high/low range 3 candle
            lvl = H[i - range_n + 1:i + 1].max() if d == 1 else L[i - range_n + 1:i + 1].min()
        pos = None
        for q in range(i + 1, len(T)):
            if T[q] - T[i] > 30 * 3600: break   # jaga-jaga celah data
            if pos is None:
                if masuk == "market":
                    e = O[q]
                elif masuk == "limit":
                    if not ((d == 1 and L[q] <= lvl) or (d == -1 and H[q] >= lvl)):
                        if HR[q] == CLOSE: break
                        continue
                    e = min(lvl, O[q]) if d == 1 else max(lvl, O[q])
                else:
                    if not ((d == 1 and H[q] >= lvl) or (d == -1 and L[q] <= lvl)):
                        if HR[q] == CLOSE: break
                        continue
                    e = max(lvl, O[q]) if d == 1 else min(lvl, O[q])
                slp = e - d * dist; tpp = e + d * rr * dist if rr else None
                pos = dict(d=d, e=e, sl=slp, tp=tpp, r0=dist, t0=T[q], w=1.0, ip=i, i0=q)
                if (d == 1 and L[q] <= slp) or (d == -1 and H[q] >= slp):
                    pos.update(ex=slp, t1=T[q], why="SL"); break
            else:
                if (d == 1 and L[q] <= pos["sl"]) or (d == -1 and H[q] >= pos["sl"]):
                    pos.update(ex=pos["sl"], t1=T[q], why="SL"); break
                if tpp is not None and ((d == 1 and H[q] >= tpp) or (d == -1 and L[q] <= tpp)):
                    pos.update(ex=tpp, t1=T[q], why="TP"); break
            if HR[q] == CLOSE:
                if pos: pos.update(ex=C[q], t1=T[q], why="TUTUP")
                break
        if pos and "ex" in pos:
            pos["R"] = (pos["ex"] - pos["e"]) * d / pos["r0"]; trades.append(pos)
    return trades
