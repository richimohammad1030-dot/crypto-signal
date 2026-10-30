"""Audit XAU: OCO 2 sisi tetap, sisi lawan tren diberi bobot 0 (hari dilewati) atau 0,5. SELEKSI di 2015-2021.
Juga dicetak periode UJI hanya untuk varian yang dipilih (baris PILIHAN). Pemakaian: python audit_tren.py <xau_sambung.json>"""
import sys
import numpy as np
import audit_mesin as m
D = m.muat(sys.argv[1]); A = np.array(m.atr(list(D[2]), list(D[3]), list(D[4]), 14)); F = m.fitur(D, A)
for k in (100,):
    F[f"ema{k}"] = m.ema(D[4], k)
J = m.stat(m.replay(D, A=A), a=m.PILIH[0], b=m.PILIH[1])
print(m.baris("juara (pilih)", J), J["thn"])
res = []
for e in ("ema50", "ema100", "ema200", "d_ema20", "d_ema50", "d_ema200"):
    for w in (0.0, 0.5):
        tr = m.jalankan({"tren_lawan_w": (e, w)}, D, A, F)
        s = m.stat(tr, a=m.PILIH[0], b=m.PILIH[1]); res.append((s["ratio"], e, w, s))
        lebih = sum(1 for y in J["thn"] if s["thn"].get(y, 0) > J["thn"][y])
        print(m.baris(f"{e} lawan bobot {w}", s), f"thn>juara {lebih}/7")
