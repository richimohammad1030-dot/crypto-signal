"""KURIKULUM SKILL 1 · SNR (support & resistance) · TAHAP 0 = DEFINISI MESIN (riset Jumat 13 Nov 2026).
Aturan pengenal pasti, tanpa penilaian subjektif dan TANPA MELIHAT MASA DEPAN (tiap level punya waktu 'tersedia' = close
candle terakhir yang dibutuhkan untuk mengenalinya). Level dari H4 & D1 (D1 = blok 07:00-07:00 WIB = hari UTC), dipakai di H1.
  a) SWING  : pivot fraktal n = 2/3/5 (high > n candle kiri & kanan; low sebaliknya) di H4 & D1, tersedia setelah n candle
              kanan close. Level berdekatan (<= 0,25 ATR14 D1 saat itu) digabung jadi zona [min, max]; kekuatan = jumlah
              sentuhan (pivot yang tergabung), umur, timeframe. Zona kedaluwarsa setelah 250 hari.
  b) PERIODE: high/low hari sebelumnya (PDH/PDL, blok 07-07 WIB) & minggu sebelumnya (PWH/PWL, Senin 07:00 WIB).
  c) BULAT  : kelipatan 10 / 25 / 50 / 100 USD (kelas = kelipatan terbesar yang membagi level).
  d) SUPDEM : candle dasar (1-3 candle berturut, tiap range <= 0,5 ATR14 tf itu) diikuti candle impulsif yang close >= 2 ATR
              di luar range dasar (<= 3 candle) -> zona = range dasar; DEMAND bila impuls naik, SUPPLY bila turun;
              tersedia setelah candle impuls close; status SEGAR sampai harga pertama kali kembali menyentuh zona.
Sentuhan (untuk tahap 1): candle H1 yang open di luar zona (jarak > 0,1 ATR H1) lalu high/low-nya masuk <= 0,1 ATR H1 dari zona.
Tahap 0 hanya: bangun semua level, cek tanpa-masa-depan, statistik jumlah/kerapatan/sentuhan per jenis & periode.
Pemakaian: python skill_snr.py <xau_2004.json>   (fungsi zona_* dipakai tahap 1/2)"""
import sys, json, time
import numpy as np
sys.path.insert(0, "."); import audit_mesin as m

def resample(T, O, H, L, C, detik):
    k = (T // detik).astype(np.int64); u, s = np.unique(k, return_index=True); e = np.append(s[1:], len(T))
    return dict(t0=u * detik, o=O[s], h=np.maximum.reduceat(H, s), l=np.minimum.reduceat(L, s), c=C[e - 1],
                tav=T[e - 1] + 3600)            # tersedia = close candle H1 terakhir dalam blok

def atr(b, n=14):
    return np.array(m.atr(list(b["h"]), list(b["l"]), list(b["c"]), n))

def zona_swing(b, n, tf, gabung=0.25, umur_hari=250, atr_d1=None, lebar_maks=0.5):
    """Pivot fraktal -> list zona dict(lo, hi, sisi, kuat, tav, exp, tf, jenis). sisi +1 = support (pivot low), -1 = resistance."""
    h, l, tav = b["h"], b["l"], b["tav"]; A = atr(b) if atr_d1 is None else atr_d1
    piv = []
    for j in range(n, len(h) - n):
        t = tav[j + n]                          # baru diketahui setelah n candle kanan close
        if h[j] > h[j - n:j].max() and h[j] > h[j + 1:j + n + 1].max(): piv.append((t, h[j], -1, A[j]))
        if l[j] < l[j - n:j].min() and l[j] < l[j + 1:j + n + 1].min(): piv.append((t, l[j], 1, A[j]))
    piv.sort(); Z = []
    for t, p, s, a in piv:
        a = a if np.isfinite(a) and a > 0 else p * 0.01
        cocok = [z for z in Z if z["exp"] > t and z["lo"] - gabung * a <= p <= z["hi"] + gabung * a
                 and max(z["hi"], p) - min(z["lo"], p) <= lebar_maks * a]
        if cocok:
            z = max(cocok, key=lambda z: z["kuat"]); z["exp"] = t      # versi lama berakhir; versi baru mulai t (tanpa masa depan)
            Z.append(dict(z, lo=min(z["lo"], p), hi=max(z["hi"], p), kuat=z["kuat"] + 1, sisi=s, tav=t,
                          exp=t + umur_hari * 86400, src=z["src"] + [(t, p)]))
        else:
            Z.append(dict(lo=p, hi=p, sisi=s, kuat=1, tav=t, exp=t + umur_hari * 86400, tf=tf, jenis=f"SWING{n}", src=[(t, p)]))
    return Z

def zona_periode(D1, W1):
    Z = []
    for b, nm, dur in ((D1, "PD", 86400), (W1, "PW", 7 * 86400)):
        for j in range(len(b["h"]) - 1):
            t = b["tav"][j]; e = t + dur + 3 * 86400        # berlaku periode berikutnya (+ libur)
            Z.append(dict(lo=b["h"][j], hi=b["h"][j], sisi=-1, kuat=1, tav=t, exp=e, tf=nm, jenis=nm + "H"))
            Z.append(dict(lo=b["l"][j], hi=b["l"][j], sisi=1, kuat=1, tav=t, exp=e, tf=nm, jenis=nm + "L"))
    return Z

def level_bulat(harga, langkah):
    return np.arange(np.floor(harga.min() / langkah) * langkah, harga.max() + langkah, langkah)

def kelas_bulat(x):
    for k in (100, 50, 25, 10):
        if abs(x / k - round(x / k)) < 1e-9: return k
    return 0

def zona_supdem(b, tf, kecil=0.5, impuls=2.0):
    o, h, l, c, tav = b["o"], b["h"], b["l"], b["c"], b["tav"]; A = atr(b); Z = []
    for j in range(15, len(c) - 4):
        for nb in (1, 2, 3):
            s = slice(j - nb + 1, j + 1)
            if not np.all(h[s] - l[s] <= kecil * A[j]): continue
            lo, hi = l[s].min(), h[s].max()
            for k in range(j + 1, min(j + 4, len(c))):
                if c[k] >= hi + impuls * A[j]: Z.append(dict(lo=lo, hi=hi, sisi=1, kuat=nb, tav=tav[k], exp=tav[k] + 250 * 86400, tf=tf, jenis="DEMAND")); break
                if c[k] <= lo - impuls * A[j]: Z.append(dict(lo=lo, hi=hi, sisi=-1, kuat=nb, tav=tav[k], exp=tav[k] + 250 * 86400, tf=tf, jenis="SUPPLY")); break
            else: continue
            break
    return Z

def bangun(D):
    T, O, H, L, C = D
    H4 = resample(T, O, H, L, C, 4 * 3600); D1 = resample(T, O, H, L, C, 86400)
    W1 = resample(T + 3 * 86400, O, H, L, C, 7 * 86400); W1["t0"] -= 3 * 86400        # minggu mulai Senin 00:00 UTC
    Ad1 = atr(D1)
    # ATR D1 dipetakan ke candle H4 (nilai hari sebelumnya yang sudah close)
    jd = np.searchsorted(D1["tav"], H4["tav"], side="right") - 1; Ad1_h4 = np.where(jd >= 0, Ad1[np.maximum(jd, 0)], np.nan)
    Z = []
    for n in (2, 3, 5):
        Z += zona_swing(H4, n, "H4", atr_d1=Ad1_h4)
        Z += zona_swing(D1, n, "D1", atr_d1=Ad1)
    Z += zona_periode(D1, W1)
    Z += zona_supdem(H4, "H4") + zona_supdem(D1, "D1")
    return Z, dict(H4=H4, D1=D1, W1=W1)

def cek_tanpa_masa_depan(Z, D):
    """Tiap versi zona: semua pivot sumbernya sudah diketahui (t <= tav) dan harga pivot ada di candle H1 yang close <= tav;
    zona periode: level = high/low candle yang close <= tav; supdem: candle impuls close <= tav (dicek lewat konstruksi)."""
    T, O, H, L, C = D; buruk = 0; n = 0
    for z in Z[::20]:
        n += 1
        if "src" in z:
            if max(t for t, _ in z["src"]) > z["tav"]: buruk += 1; continue
            if not (np.isclose(z["lo"], min(p for _, p in z["src"])) and np.isclose(z["hi"], max(p for _, p in z["src"]))): buruk += 1; continue
        t_awal = min(t for t, _ in z["src"]) if "src" in z else z["tav"]
        msk = (T + 3600 <= z["tav"]) & (T >= t_awal - 60 * 86400)
        if z["jenis"] in ("DEMAND", "SUPPLY"): continue
        if not ((np.isclose(H[msk], z["hi"]).any() or np.isclose(L[msk], z["hi"]).any()) and (np.isclose(H[msk], z["lo"]).any() or np.isclose(L[msk], z["lo"]).any())): buruk += 1
    return f"{buruk} dari {n}"

def sentuhan(Z, D, jenis_fn=lambda z: z["jenis"] + "-" + z["tf"], dekat=0.1, bulat=(10, 25, 50, 100)):
    """Peristiwa sentuhan per candle H1 (dari luar zona). Kembalikan list (i, kunci, sisi_relatif, lo, hi)."""
    T, O, H, L, C = D; Ah = np.array(m.atr(list(H), list(L), list(C), 14)); ev = []
    Z = sorted(Z, key=lambda z: z["tav"]); tav = np.array([z["tav"] for z in Z]); k0 = 0; aktif = []
    for i in range(1, len(T)):
        while k0 < len(Z) and tav[k0] <= T[i]: aktif.append(Z[k0]); k0 += 1     # tersedia sebelum candle i open
        if i % 500 == 0: aktif = [z for z in aktif if z["exp"] > T[i]]
        a = Ah[i - 1]; o = O[i]
        if not np.isfinite(a) or a <= 0: continue
        for z in aktif:
            if z["exp"] <= T[i]: continue
            if o > z["hi"] + dekat * a and L[i] <= z["hi"] + dekat * a: ev.append((i, jenis_fn(z), 1, z))     # dari atas -> uji support
            elif o < z["lo"] - dekat * a and H[i] >= z["lo"] - dekat * a: ev.append((i, jenis_fn(z), -1, z))  # dari bawah -> uji resistance
        for st in bulat:
            lv = np.ceil((L[i] - dekat * a) / st) * st
            while lv <= H[i] + dekat * a:
                if kelas_bulat(lv) == st:
                    if o > lv + dekat * a: ev.append((i, f"BULAT{st}", 1, dict(lo=lv, hi=lv)))
                    elif o < lv - dekat * a: ev.append((i, f"BULAT{st}", -1, dict(lo=lv, hi=lv)))
                lv += st
    return ev

if __name__ == "__main__":
    D = m.muat(sys.argv[1]); T = D[0]; t_ = time.time()
    Z, B = bangun(D)
    print(f"Data H1 {len(T)} candle {m.wib(T[0]):%Y-%m-%d} s.d. {m.wib(T[-1]):%Y-%m-%d}; H4 {len(B['H4']['t0'])}, D1 {len(B['D1']['t0'])}, W1 {len(B['W1']['t0'])}")
    print(f"Cek tanpa-masa-depan (sampel 1/20 zona): {cek_tanpa_masa_depan(Z, D)} pelanggaran")
    jumlah = {}
    for z in Z: jumlah.setdefault(z["jenis"] + "-" + z["tf"], []).append(z)
    print("\nZona per jenis: jumlah · rata kekuatan · lebar median (USD) · zona/tahun")
    yrs = (T[-1] - T[0]) / 86400 / 365.25
    for k in sorted(jumlah):
        zs = jumlah[k]
        print(f"  {k:<14} {len(zs):>6} · kuat {np.mean([z['kuat'] for z in zs]):4.2f} · lebar {np.median([z['hi'] - z['lo'] for z in zs]):6.2f} · {len(zs) / yrs:6.1f}/thn")
    ev = sentuhan(Z, D)
    hari = len(np.unique(T // 86400))
    print(f"\nSentuhan (candle H1 dari luar zona, <= 0,1 ATR): total {len(ev)} ({len(ev) / hari:.1f}/hari bursa); per jenis & periode:")
    per = {}
    for i, k, s, z in ev:
        y = m.wib(T[i]).year; p = "2004-14" if y <= 2014 else "2015-26"
        per.setdefault(k, {}).setdefault(p, [0, 0]); per[k][p][0 if s == 1 else 1] += 1
    for k in sorted(per):
        print(f"  {k:<14} " + " · ".join(f"{p}: sup {v[0]:>6} res {v[1]:>6}" for p, v in sorted(per[k].items())))
    print(f"\nwaktu {time.time() - t_:.0f} dtk")
