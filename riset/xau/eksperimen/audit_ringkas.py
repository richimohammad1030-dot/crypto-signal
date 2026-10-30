"""Audit XAU poin 5: tabel lengkap kandidat akhir per periode (risiko 1% dan 0,5%), per tahun, stress slip.
Opsional: urutan candle ambigu dari M1 (audit_m1.py) -> argumen ke-2 /tmp/data/ambigu_sisi.json.
Pemakaian: python audit_ringkas.py <xau_sambung.json> [ambigu_sisi.json]"""
import sys, json
import numpy as np
import audit_mesin as m
D = m.muat(sys.argv[1]); A = np.array(m.atr(list(D[2]), list(D[3]), list(D[4]), 14)); F = m.fitur(D, A)
K = {"Juara (live)": {}, "K6: lewati bila lawan EMA200 H1 terisi": {"tren_lawan_w": ("ema200", 0.0)},
     "K6b: lawan EMA200 H1 risiko 1/2": {"tren_lawan_w": ("ema200", 0.5)}}
P = (("2015-2021 (pilih)", m.PILIH), ("2022-Jan 2025 (uji)", m.UJI), ("Feb 2025-skrg Setra", m.KONF),
     ("2015-Jan 2025 (Duka)", (None, "2025-02-01")), ("2015-skrg semua", (None, None)))
AMB = {int(k): v for k, v in json.load(open(sys.argv[2])).items()} if len(sys.argv) > 2 else "buy"
print("Urutan candle ambigu:", "M1 Dukascopy" if isinstance(AMB, dict) else "asumsi bot (BUY)")
for nm, spec in K.items():
    tr = m.potong(m.jalankan(dict(spec, ambigu=AMB), D, A, F))
    print(f"\n### {nm}")
    print("| Periode | Trade/bln | Win | RR | Exp R | PF | R/thn | DD R | DD% 1% | CAGR 1% | DD% 0,5% | CAGR 0,5% | W/L maks | Bln+ | Tanpa 2% | Slip+0,2 R/thn |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for pn, (a, b) in P:
        s = m.stat(tr, a=a, b=b); h = m.stat(tr, a=a, b=b, risk=0.005); x = m.stat(tr, a=a, b=b, slip=0.2)
        print(f"| {pn} | {s['perbln']:.1f} | {s['wr']*100:.1f}% | {s['rr']:.2f} | {s['avg']:+.3f} | {s['pf']:.2f} | {s['rthn']:+.1f} | "
              f"{s['dd']:.1f} | {s['ddpct']:.1f}% | {s['cagr']:+.1f}% | {h['ddpct']:.1f}% | {h['cagr']:+.1f}% | {s['wmax']}/{s['lmax']} | "
              f"{s['blnpos']:.0f}% | {s['tanpa2']:+.1f} | {x['rthn']:+.1f} |")
    print("Per tahun (R bersih):", " · ".join(f"{y} {v:+.1f}" for y, v in m.stat(tr)["thn"].items()))
