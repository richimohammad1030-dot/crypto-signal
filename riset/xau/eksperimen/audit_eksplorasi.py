"""Audit XAU langkah 3-4 tahap 1: pindai satu dimensi per varian. SELEKSI HANYA DI 2015-2021 (periode PILIH).
Periode UJI (2022 - Jan 2025) sengaja tidak dicetak di tahap ini agar tidak ikut memilih.
Pemakaian: python audit_eksplorasi.py <xau_panjang.json> > hasil.txt"""
import sys, json
import numpy as np
import audit_mesin as m

D = m.muat(sys.argv[1])
T, O, H, L, C = D
A = np.array(m.atr(list(H), list(L), list(C), m.gb.ATR_N))
F = m.fitur(D, A)
HARI = lambda i: int(m.wib(T[i] + 3600).strftime("%w"))       # hari WIB saat order aktif (1 = Senin)
a, b = m.PILIH


def evaluasi(tr):
    s = m.stat(tr, a=a, b=b)
    th = {y: v for y, v in s["thn"].items()}
    return s, th


base, th0 = evaluasi(m.replay(D, A=A))
VAR = []


def add(grup, nama, plan=None, **kw):
    VAR.append((grup, nama, plan, kw))


# G1 TP (R)
for rr in (0.5, 1, 1.5, 2, 3, 4, 6, None):
    add("TP", f"TP {rr}R" if rr else "tanpa TP", rr=rr)
# G2 SL ATR
for sl in (1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0):
    add("SL", f"SL {sl} ATR", sl_atr=sl)
# G3 SL di sisi range seberang
for f_ in (0.5, 1.0):
    for rr in (1, 2, 4):
        add("SL range", f"SL {f_}x range, TP {rr}R", sl_mode="range", sl_atr=f_, rr=rr)
# G4 jam tutup (UTC; 15 = 23:00 WIB)
for ch in (12, 13, 14, 16, 17, 18, 19, 20):
    add("Tutup", f"tutup {(ch + 8) % 24:02d}:00 WIB", close_hr=ch)
# G5 range & jam pasang
for n in (1, 2, 4, 5, 6):
    add("Range", f"range {n} candle (07 WIB)", range_n=n)
for ph, n, nm in ((0, 4, "05-08 WIB, pasang 08"), (1, 5, "05-09, pasang 09"), (2, 6, "05-10, pasang 10"),
                  (6, 8, "Asia 06-14, pasang 14 (London)"), (6, 4, "10-14, pasang 14"), (7, 9, "Asia 07-15, pasang 15"),
                  (12, 6, "13-19, pasang 19 (NY)")):
    add("Range", f"range {nm}", place_hr=ph, range_n=n, close_hr=20 if ph >= 6 else 15)
# G6 buffer entry
for bf in (0.1, 0.2, 0.3, 0.5):
    add("Buffer", f"entry +{bf} ATR di luar range", buf=bf)
# G7 breakeven
for be in (1, 2):
    add("BE", f"SL ke entry setelah +{be}R", be_r=be)
# G8 lewati hari
for d, nm in ((1, "Senin"), (2, "Selasa"), (3, "Rabu"), (4, "Kamis"), (5, "Jumat")):
    add("Hari", f"lewati {nm}", plan=lambda i, hi, lo, at, d=d: None if HARI(i) == d else (True, True, 1.0))
# G9 rezim volatilitas (#21) + biaya
def f_min(key, x):
    return lambda i, hi, lo, at: (True, True, 1.0) if F[key][i] >= x else None
for x in (0.0025, 0.003, 0.0035, 0.004, 0.0045):
    add("Vol", f"ATR H1/harga >= {x*100:.2f}%", plan=f_min("atr_rel", x))
for x in (0.8, 0.9, 1.0, 1.1, 1.2):
    add("Vol", f"ATR vs rata 1 thn >= {x}", plan=f_min("atr_vs1y", x))
for x in (0.3, 0.4, 0.5, 0.6, 0.7):
    add("Vol", f"persentil ATR 1 thn >= {int(x*100)}", plan=f_min("pct1y", x))
for x in (0.008, 0.01, 0.012, 0.014):
    add("Vol", f"ATR D1/harga >= {x*100:.1f}%", plan=f_min("d_atr_rel", x))
for c in (0.02, 0.03, 0.05, 0.08):
    add("Biaya", f"lewati jika biaya > {c:.2f}R", plan=lambda i, hi, lo, at, c=c: (True, True, 1.0) if 0.40 / (1.5 * at) <= c else None)
# G10 tren
for key, nm in (("d_ema20", "D1 EMA20"), ("d_ema50", "D1 EMA50"), ("d_ema200", "D1 EMA200"), ("ema50", "H1 EMA50"),
                ("ema200", "H1 EMA200")):
    add("Tren", f"hanya searah {nm}", plan=lambda i, hi, lo, at, k=key: (C[i] > F[k][i], C[i] < F[k][i], 1.0))
add("Tren", "hanya searah momentum D1 20 hari", plan=lambda i, hi, lo, at: (F["d_ret20"][i] > 0, F["d_ret20"][i] < 0, 1.0))
add("Tren", "hanya BUY", plan=lambda i, hi, lo, at: (True, False, 1.0))
add("Tren", "hanya SELL", plan=lambda i, hi, lo, at: (False, True, 1.0))

out = []
print(f"PERIODE PILIH 2015-2021 (bersih biaya 0,40 USD). Juara: {m.baris('juara', base)}")
print("per tahun juara:", th0)
for g, nm, plan, kw in VAR:
    s, th = evaluasi(m.replay(D, A=A, plan=plan, **kw))
    lebih = sum(1 for y in th0 if th.get(y, 0) > th0[y])
    out.append(dict(grup=g, nama=nm, s=s, thn_lebih=lebih))
    print(f"[{g}] {m.baris(nm, s)} thn>juara={lebih}/{len(th0)}")
json.dump([dict(grup=o["grup"], nama=o["nama"], thn_lebih=o["thn_lebih"],
                **{k: v for k, v in o["s"].items() if k != "thn"}) for o in out], open("/tmp/data/eksplorasi_pilih.json", "w"))
