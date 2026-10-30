"""Audit XAU: aturan henti (kill switch) drawdown & frekuensi kedua sisi tersentuh dalam 1 candle.
Pemakaian: python audit_henti.py <xau_sambung.json>"""
import sys
import numpy as np
import audit_mesin as m
D = m.muat(sys.argv[1]); A = np.array(m.atr(list(D[2]), list(D[3]), list(D[4]), 14)); F = m.fitur(D, A)
T, O, H, L, C = D
for nm, spec in (("juara", {}), ("K6b", {"tren_lawan_w": ("ema200", 0.5)})):
    tr = m.potong(m.jalankan(spec, D, A, F)); r = m.net(tr)
    print(f"\n== {nm}: kill switch (berhenti permanen saat DD dari puncak >= X R), mulai di berbagai tanggal")
    for mulai in ("2015-01-01", "2017-01-01", "2019-01-01", "2021-01-01", "2023-01-01", "2025-02-01"):
        idx = [j for j, x in enumerate(tr) if x["t0"] >= m.ts(mulai)]; rr_ = r[idx]
        row = f"  mulai {mulai}: tanpa henti {rr_.sum():+7.1f}R"
        for X in (15, 20, 25):
            eq = np.cumsum(rr_); pk = np.maximum.accumulate(np.concatenate([[0], eq]))[1:]; hit = np.flatnonzero(pk - eq >= X)
            row += (f" | X={X}: henti {m.wib(tr[idx[hit[0]]]['t0']).date()} pada {eq[hit[0]]:+.1f}R" if len(hit) else f" | X={X}: tidak kena ({eq[-1]:+.1f}R)")
        print(row)
# kedua sisi tersentuh dalam candle yang sama saat terisi (bot mengambil BUY; urutan sebenarnya tidak diketahui)
tr = m.replay(D, A=A); amb = 0
for x in tr:
    i = x["i0"]; ip = x["ip"]; hi, lo = H[ip - 2:ip + 1].max(), L[ip - 2:ip + 1].min()
    if H[i] >= hi and L[i] <= lo: amb += 1
print(f"\nCandle terisi yang menyentuh high DAN low range: {amb}/{len(tr)} ({amb/len(tr)*100:.1f}%) - arah trade tidak pasti di data H1")
