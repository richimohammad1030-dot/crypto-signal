"""Mesin umum strategi XAU dalam jendela TETAP pemilik: order dibuat 07:00 WIB, semua ditutup 23:00 WIB (31 Okt 2026).
rencana(i) -> list order [(d, jenis, level)] (jenis: "market" | "limit" | "stop"), OCO: order pertama yang terisi menang.
Jika >1 order terisi di candle yang sama -> dipakai hasil TERBURUK (konservatif, tanpa data M1).
Setelah terisi: candle terisi hanya cek SL; lalu SL sebelum TP; tutup di close candle 23:00 WIB. SL/TP dalam ATR H1 / R.
Biaya dihitung di audit_mesin.stat (0,40 USD/trade + slip opsional)."""
import numpy as np
import audit_mesin as m

PLACE, CLOSE = m.gb.PLACE_HOUR_UTC, m.gb.CLOSE_HOUR_UTC


def _kelola(D, q0, d, e, slp, tpp):
    """Kelola posisi dari candle q0 (candle terisi). Return (exit, t1, why, q_akhir)."""
    T, O, H, L, C = D
    HR = ((T[q0] // 3600) % 24)
    if (d == 1 and L[q0] <= slp) or (d == -1 and H[q0] >= slp):
        return slp, T[q0], "SL"
    if HR == CLOSE:
        return C[q0], T[q0], "TUTUP"
    for q in range(q0 + 1, min(q0 + 30, len(T))):
        if (d == 1 and L[q] <= slp) or (d == -1 and H[q] >= slp):
            return slp, T[q], "SL"
        if tpp is not None and ((d == 1 and H[q] >= tpp) or (d == -1 and L[q] <= tpp)):
            return tpp, T[q], "TP"
        if (T[q] // 3600) % 24 == CLOSE:
            return C[q], T[q], "TUTUP"
    return C[min(q0 + 29, len(T) - 1)], T[min(q0 + 29, len(T) - 1)], "TUTUP"


def jalan(D, A, rencana, sl=1.5, tp=None, start=250):
    T, O, H, L, C = D
    HR = ((T // 3600) % 24).astype(int)
    trades = []
    for i in np.flatnonzero(HR == PLACE):
        if i < start or i + 1 >= len(T):
            continue
        orders = rencana(i)
        if not orders:
            continue
        a = A[i]; dist = sl * a
        if dist <= 0.5:
            continue
        hasil = None
        for q in range(i + 1, min(i + 30, len(T))):
            kandidat = []
            for d, jenis, lvl in orders:
                if jenis == "market":
                    if q == i + 1: kandidat.append((d, O[q]))
                elif jenis == "limit":
                    if (d == 1 and L[q] <= lvl) or (d == -1 and H[q] >= lvl):
                        kandidat.append((d, min(lvl, O[q]) if d == 1 else max(lvl, O[q])))
                else:
                    if (d == 1 and H[q] >= lvl) or (d == -1 and L[q] <= lvl):
                        kandidat.append((d, max(lvl, O[q]) if d == 1 else min(lvl, O[q])))
            if kandidat:
                opsi = []
                for d, e in kandidat:
                    slp = e - d * dist; tpp = e + d * tp * dist if tp else None
                    ex, t1, why = _kelola(D, q, d, e, slp, tpp)
                    opsi.append(dict(d=d, e=e, ex=ex, r0=dist, t0=T[q], t1=t1, why=why, w=1.0, ip=i, i0=q,
                                     R=(ex - e) * d / dist))
                hasil = min(opsi, key=lambda x: x["R"])          # konservatif bila >1 terisi di candle sama
                break
            if HR[q] == CLOSE:
                break
        if hasil:
            trades.append(hasil)
    return trades


def ringkas(trades, a=None, b=None, biaya=0.40, slip=0.0):
    """Statistik + kriteria pemilik: win >= 40%, PF > 1, trade/minggu >= 3, beruntun kalah tidak jauh dari menang."""
    s = m.stat(trades, biaya=biaya, slip=slip, a=a, b=b)
    s["per_mg"] = s["perbln"] * 12 / 52
    th = s["thn"]; s["thn_pos"] = sum(v > 0 for v in th.values()); s["thn_n"] = len(th)
    return s


def lulus(s):
    return (s["wr"] >= 0.40 and s["pf"] > 1.0 and s["per_mg"] >= 3.0 and s["lmax"] <= s["wmax"] + 4
            and s["thn_pos"] > s["thn_n"] / 2)
