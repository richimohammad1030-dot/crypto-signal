"""Audit XAU tahap 2b: kandidat yang DIPILIH di 2015-2021 (audit_grid.py) diuji di 2022 - Jan 2025 (Dukascopy),
lalu dikonfirmasi SEKALI di Feb 2025 - sekarang (Setra, data sambung untuk pemanasan fitur).
Pemakaian: python audit_uji.py <xau_panjang.json> <setra.json>"""
import sys, os, json
import numpy as np
import audit_mesin as m
sys.path.insert(0, os.path.join(m.REPO, "riset"))
import signifikansi as sg

DK = m.muat(sys.argv[1]); SE = m.muat(sys.argv[2])
SB = m.sambung(DK, SE)
DATA = {}
for nm, D in (("duka", DK), ("sambung", SB)):
    A = np.array(m.atr(list(D[2]), list(D[3]), list(D[4]), m.gb.ATR_N)); F = m.fitur(D, A); F["ema100"] = m.ema(D[4], 100)
    DATA[nm] = (D, A, F)

KAND = {
    "juara": {},
    "K1 biaya<=0,05R + range 04-08 (pasang 08)": {"biaya_maks": 0.05, "place_hr": 0, "range_n": 4},
    "K2 biaya<=0,04R + SL 2 ATR + tanpa TP + range 04-08": {"biaya_maks": 0.04, "sl_atr": 2.0, "rr": None, "place_hr": 0, "range_n": 4},
    "K3 biaya<=0,05R saja (aturan lain = juara)": {"biaya_maks": 0.05},
    "K4 biaya<=0,04R + SL 2 ATR + range 04-08": {"biaya_maks": 0.04, "sl_atr": 2.0, "place_hr": 0, "range_n": 4},
    "K5 K1 + lewati hari bila sisi lawan EMA100 H1 terisi": {"biaya_maks": 0.05, "place_hr": 0, "range_n": 4, "tren_lawan_w": ("ema100", 0.0)},
    "K6 juara + lewati hari bila sisi lawan EMA200 H1 terisi": {"tren_lawan_w": ("ema200", 0.0)},
}
PER = (("Pilih 2015-2021", "duka", m.PILIH), ("UJI 2022-Jan2025", "duka", m.UJI), ("Duka 2015-Jan2025", "duka", (None, "2025-02-01")),
       ("KONF Feb2025-skrg Setra", "sambung", m.KONF), ("Semua (sambung)", "sambung", (None, None)))

hasil = {}
for nm, spec in KAND.items():
    print(f"\n### {nm}  spec={spec}")
    tr = {k: m.jalankan(spec, *DATA[k]) for k in DATA}
    hasil[nm] = tr
    for pn, src, (a, b) in PER:
        s = m.stat(tr[src], a=a, b=b)
        print(f"  {m.baris(pn, s)}")
    s = m.stat(tr["sambung"]); print("  per tahun (sambung):", s["thn"])
    os.makedirs("/tmp/data/kand", exist_ok=True)
    m.csv_out(f"/tmp/data/kand/{nm.split()[0]}.csv", tr["sambung"])

print("\n### Signifikansi vs juara (bootstrap blok bulanan, rasio R/DD)")
J = hasil["juara"]["sambung"]
for nm in KAND:
    if nm == "juara": continue
    P = hasil[nm]["sambung"]
    J_, P_ = m.potong(J), m.potong(P)
    jl = [(int(x["t1"]), float(v)) for x, v in zip(J_, m.net(J_))]; pl = [(int(x["t1"]), float(v)) for x, v in zip(P_, m.net(P_))]
    for pn, (a, b) in (("pilih", m.PILIH), ("UJI", m.UJI), ("KONF", m.KONF)):
        r = sg.banding(jl, pl, int(m.ts(a)) if a else None, int(m.ts(b)) if b else None)
        print(f"  {nm[:3]} {pn:<5} P_rasio={r['P_rasio_lebih_baik']:.3f} P_R={r['P_R_lebih_baik']:.3f} "
              f"juara {r['juara']} penantang {r['penantang']}")

print("\n### Stress biaya (UJI & KONF): biaya 0,40 + slip 0,20 USD")
for nm in KAND:
    for pn, src, (a, b) in PER[1:4:2]:
        s = m.stat(hasil[nm][src], slip=0.20, a=a, b=b); print(f"  {nm[:3]} {m.baris(pn, s)}")
