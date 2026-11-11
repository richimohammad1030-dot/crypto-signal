"""KURIKULUM SKILL 1 · SNR (support & resistance) untuk CRYPTO SWING · TAHAP 0 = definisi mesin (11 Nov 2026).
Adaptasi riset/KURIKULUM_SKILL.md: level dari H4 & D1 (dibentuk dari candle H1 Binance, hari = 00:00-24:00 UTC = 07:00-07:00
WIB, sama dengan blok XAU), dipakai untuk keputusan di candle cek H1 (tiap 4 jam). TANPA melihat masa depan: setiap level hanya
dipakai setelah candle pembentuknya (dan konfirmasi fraktal n candle) sudah tutup.
Empat jenis:
 a) SWING : pivot fraktal n = 2/3/5 candle tiap sisi di H4 & D1. Level berdekatan (<= 0,25 ATR D1, lebar zona maks 0,5 ATR D1) digabung jadi zona;
            kekuatan = jumlah pivot di zona (sentuhan), umur, timeframe (D1 > H4).
 b) PERIODE: high/low hari sebelumnya & minggu sebelumnya (minggu Senin 00:00 UTC).
 c) BULAT : harga kelipatan langkah s = 10^floor(log10(harga)) x {1, 0,5, 0,25}; kekuatan 3/2/1 (langkah besar = kuat).
            (Crypto berbeda skala harga, jadi "bulat" relatif terhadap orde besaran harga.)
 d) SD    : zona supply-demand H4: 1-3 candle dasar kecil (range <= 0,5 ATR H4) lalu gerak impulsif >= 2 ATR H4 dalam
            <= 3 candle; zona = range candle dasar; demand bila impuls naik, supply bila turun; SEGAR bila belum disentuh lagi.
Tahap 1 (Jumat berikutnya): peristiwa sentuh zona (<= 0,1 ATR H1) dari luar → MEMANTUL (>= 1 ATR menjauh tanpa tembus >= 0,5
ATR dalam 1-12 candle H1) vs TEMBUS, dibanding level ACAK (jarak sama); P >= 0,90 (bootstrap blok bulanan) di 2017-2019 DAN
2020-skrg, kedua arah.
Pemakaian: python skill_snr.py <repo> <data_dir> [koin=BTC]  → ringkasan zona di candle terakhir (cek kewajaran definisi)."""
import json, math, os, sys
import numpy as np

FRAKTAL = (2, 3, 5)


def agregasi(T, O, H, L, C, jam):
    """Candle H1 → candle `jam` jam (blok sejajar UTC). Return dict array + indeks H1 terakhir tiap blok."""
    T = np.asarray(T); blok = T // (jam * 3600)
    batas = np.flatnonzero(np.diff(blok)) + 1
    awal = np.concatenate([[0], batas]); akhir = np.concatenate([batas, [len(T)]]) - 1
    H, L, O, C = map(np.asarray, (H, L, O, C))
    return dict(T=blok[awal] * jam * 3600, O=O[awal], C=C[akhir], H=np.maximum.reduceat(H, awal),
                L=np.minimum.reduceat(L, awal), i_h1=akhir, lengkap=(akhir - awal + 1) == jam)


def atr(H, L, C, n=14):
    tr = np.maximum(H - L, np.maximum(abs(H - np.roll(C, 1)), abs(L - np.roll(C, 1)))); tr[0] = H[0] - L[0]
    out = np.empty_like(tr); out[0] = tr[0]
    for i in range(1, len(tr)): out[i] = out[i - 1] + (tr[i] - out[i - 1]) / n
    return out


def pivot(B, n):
    """Pivot fraktal: (indeks candle konfirmasi, harga, +1 high / -1 low). Diketahui setelah candle k+n tutup."""
    H, L, out = B["H"], B["L"], []
    for k in range(n, len(H) - n):
        if H[k] == H[k - n:k + n + 1].max(): out.append((k + n, H[k], 1))
        if L[k] == L[k - n:k + n + 1].min(): out.append((k + n, L[k], -1))
    return out


def zona_swing(B, A_d1, upto, tf):
    """Zona swing yang sudah terkonfirmasi s.d. candle `upto` (indeks B). Gabung level <= 0,25 ATR D1."""
    uniq = {}                                   # pivot yang sama (n = 2/3/5) dihitung sekali, waktu konfirmasi paling awal
    for n in FRAKTAL:
        for (k, p, s) in pivot_cache(B, n):
            if k <= upto and (p not in uniq or k < uniq[p][3]): uniq[p] = (p, n, tf, k)
    lv = sorted(uniq.values())
    zones = []
    for p, n, tf_, k in lv:
        if zones and p - zones[-1]["hi"] <= 0.25 * A_d1 and p - zones[-1]["lo"] <= 0.5 * A_d1:   # lebar zona maks 0,5 ATR D1
            z = zones[-1]; z["hi"] = max(z["hi"], p); z["n"] += 1; z["k_akhir"] = max(z["k_akhir"], k)
        else:
            zones.append(dict(jenis="SWING", tf=tf_, lo=p, hi=p, n=1, k_akhir=k))
    return zones


_PC = {}
def pivot_cache(B, n):
    key = (id(B), n)
    if key not in _PC: _PC[key] = pivot(B, n)
    return _PC[key]


def zona_periode(D1, W1, d_upto, w_upto):
    z = []
    if d_upto >= 1: z += [dict(jenis="PDH", lo=D1["H"][d_upto - 1], hi=D1["H"][d_upto - 1]), dict(jenis="PDL", lo=D1["L"][d_upto - 1], hi=D1["L"][d_upto - 1])]
    if w_upto >= 1: z += [dict(jenis="PWH", lo=W1["H"][w_upto - 1], hi=W1["H"][w_upto - 1]), dict(jenis="PWL", lo=W1["L"][w_upto - 1], hi=W1["L"][w_upto - 1])]
    return z


def zona_bulat(harga, lebar=3):
    s0 = 10 ** math.floor(math.log10(harga)); z = {}
    for f, kuat in ((1, 3), (0.5, 2), (0.25, 1)):
        s = s0 * f; b = math.floor(harga / s)
        for m in range(b - lebar, b + lebar + 1):
            lv = round(m * s, 12)
            if m > 0 and lv not in z: z[lv] = dict(jenis="BULAT", lo=lv, hi=lv, kuat=kuat)   # level sama: simpan yang terkuat
    return list(z.values())


def zona_sd(B, A, upto):
    """Zona supply-demand H4 terkonfirmasi s.d. candle `upto`; segar = belum disentuh setelah impuls."""
    H, L, C, O = B["H"], B["L"], B["C"], B["O"]; out = []
    for k in range(20, upto - 3):
        for nb in (1, 2, 3):
            base = slice(k - nb + 1, k + 1)
            if (H[base] - L[base]).max() > 0.5 * A[k]: continue
            lo, hi = L[base].min(), H[base].max()
            for j in range(k + 1, min(k + 4, upto + 1)):
                if C[j] - hi >= 2 * A[k]: out.append(dict(jenis="DEMAND", lo=lo, hi=hi, k_impuls=j)); break
                if lo - C[j] >= 2 * A[k]: out.append(dict(jenis="SUPPLY", lo=lo, hi=hi, k_impuls=j)); break
            break
    for z in out:
        j = z["k_impuls"]
        z["segar"] = not bool(((L[j + 1:upto + 1] <= z["hi"]) & (H[j + 1:upto + 1] >= z["lo"])).any())
    return out


def zona_di(D, i, tf=("H4", "D1")):
    """Semua zona yang diketahui pada candle H1 ke-i (sudah tutup). D = dict candle H1 (T,O,H,L,C)."""
    H4 = agregasi(D["T"], D["O"], D["H"], D["L"], D["C"], 4)
    D1 = agregasi(D["T"], D["O"], D["H"], D["L"], D["C"], 24)
    W1 = agregasi([t + 3 * 86400 for t in D["T"]], D["O"], D["H"], D["L"], D["C"], 24 * 7)   # minggu mulai Senin UTC
    h4u, d1u, w1u = (int(np.searchsorted(B["i_h1"], i, side="right")) - 1 for B in (H4, D1, W1))
    A_d1 = atr(D1["H"], D1["L"], D1["C"])[max(d1u, 0)]; A_h4 = atr(H4["H"], H4["L"], H4["C"])
    z = []
    if "H4" in tf: z += zona_swing(H4, A_d1, h4u, "H4")
    if "D1" in tf: z += zona_swing(D1, A_d1, d1u, "D1")
    # hari/minggu yang SUDAH tutup: blok terakhir yang memuat i bisa belum lengkap → pakai blok sebelum blok berjalan
    d_cur = d1u if D1["i_h1"][d1u] == i and D1["lengkap"][d1u] else d1u
    z += zona_periode(D1, W1, d_cur, w1u)
    z += zona_bulat(D["C"][i]); z += zona_sd(H4, A_h4, h4u)
    return z


if __name__ == "__main__":
    data = sys.argv[2]; koin = sys.argv[3] if len(sys.argv) > 3 else "BTC"
    rows = json.load(open(f"{data}/klines/{koin}.json"))[-24 * 400:]
    D = dict(T=[r[0] for r in rows], O=[r[1] for r in rows], H=[r[2] for r in rows], L=[r[3] for r in rows], C=[r[4] for r in rows])
    i = len(rows) - 1; z = zona_di(D, i); px = D["C"][i]
    from collections import Counter
    print(f"{koin} harga {px} · zona dikenali: {dict(Counter(x['jenis'] + ('-' + x['tf'] if 'tf' in x else '') for x in z))}")
    dekat = sorted(z, key=lambda x: min(abs(px - x['lo']), abs(px - x['hi'])))[:8]
    for x in dekat:
        print(f"  {x['jenis']:<7} {x.get('tf', ''):<3} {x['lo']:.2f}-{x['hi']:.2f} jarak {min(abs(px - x['lo']), abs(px - x['hi'])) / px * 100:.2f}%"
              + (f" sentuhan {x['n']}" if 'n' in x else "") + (f" kuat {x['kuat']}" if 'kuat' in x else "") + (f" segar {x['segar']}" if 'segar' in x else ""))
