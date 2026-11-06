"""Ide #48 (6 Nov 2026, pemilik): OCO juara lama tetap UTAMA, strategi live sebagai TAMBAHAN dengan kriteria khusus. Maks 1
posisi/hari: hari dengan sinyal khusus -> MR (aturan hibrida live / ambang lebih ketat), hari lain -> OCO 2 sisi (SL 1,5 ATR,
TP 4R). Varian: kriteria = sinyal MR live / RSI2 <= b atau >= 100-b (b 5/10/20) / MR live + OCO hanya searah tren (K6 = live).
Pilih 2015-2021. Pemakaian: python oco_utama.py <sambung.json> <ambigu.json>"""
import sys, os, json
import numpy as np
import audit_mesin as m, strat_mesin as sm, multi_mesin as mm
sys.path.insert(0, os.path.join(m.REPO, "riset")); import signifikansi as sg
D = m.muat(sys.argv[1]); T, O, H, L, C = D
A = np.array(m.atr(list(H), list(L), list(C), 14)); F = m.fitur(D, A)
AMB = {int(k): v for k, v in json.load(open(sys.argv[2])).items()}
HR = ((T // 3600) % 24).astype(int); R2 = mm.rsi(C, 2)
oco = {x["ip"]: x for x in m.potong(m.jalankan({"ambigu": AMB}, D, A, F))}
for x in oco.values(): x["strat"] = "OCO"
live = mm.baseline(D, A, F, ambigu=AMB)
jl = [(int(x["t1"]), float(v)) for x, v in zip(live, m.net(live))]
P4 = (("2015-21", m.PILIH), ("2022-Jan25", m.UJI), ("Setra", m.KONF), ("12t", (None, None)))
def lapor(nm, G):
    G = sorted(G, key=lambda z: z["t1"]); gl = [(int(x["t1"]), float(v)) for x, v in zip(G, m.net(G))]
    pu = sg.banding(jl, gl, int(m.ts(m.UJI[0])), int(m.ts(m.UJI[1])))["P_rasio_lebih_baik"]
    pk = sg.banding(jl, gl, int(m.ts(m.KONF[0])), int(T[-1]))["P_rasio_lebih_baik"]
    s = {pn: sm.ringkas(G, a, b) for pn, (a, b) in P4}; th = m.stat(G)["thn"]
    print(f"{nm:<38} " + " · ".join(f"{s[pn]['rthn']:+6.1f}" for pn, _ in P4) + f" | /mg {s['12t']['per_mg']:.1f} win {s['12t']['wr']*100:.0f}%"
          f" PF {s['12t']['pf']:.2f} DD {s['12t']['dd']:.0f}R W/L {s['12t']['wmax']}/{s['12t']['lmax']} thn+ {s['12t']['thn_pos']}/12 | P vs live uji {pu:.2f} Setra {pk:.2f}")
def gabung(sig):
    mr = {x["ip"]: x for x in mm.trades_mr(D, A, sig)}
    out = []
    for ip in sorted(set(mr) | set(oco)):
        x = mr.get(ip) if ip in sig else oco.get(ip)
        if x: out.append(dict(x, strat="MR" if ip in sig else "OCO"))
    return out
print("R/thn: 2015-21 · 2022-Jan25 · Setra · 12t")
lapor("Bot live (hibrida MR + K6 + susulan)", live)
lapor("OCO juara lama saja", list(oco.values()))
lapor("OCO + MR (sinyal hibrida live)", gabung(mm.sinyal_live(D)))
i07 = np.flatnonzero(HR == sm.PLACE)
for b in (5, 10, 20, 30):
    sig = {int(i): (1 if R2[i] <= b else -1) for i in i07 if R2[i] <= b or R2[i] >= 100 - b}
    lapor(f"OCO + MR hanya RSI<={b} / >={100-b}", gabung(sig))
