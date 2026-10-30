"""Frekuensi trade per minggu & tabel lengkap varian (31 Okt 2026, pertanyaan pemilik: target >= 1 entry per hari).
Hari bursa = hari dengan order 07:00. Pemakaian: python frekuensi.py <xau_sambung.json> <ambigu_sisi.json>"""
import sys, json
import numpy as np
import audit_mesin as m
D = m.muat(sys.argv[1]); A = np.array(m.atr(list(D[2]), list(D[3]), list(D[4]), 14)); F = m.fitur(D, A)
AMB = {int(k): v for k, v in json.load(open(sys.argv[2])).items()}
T, C = D[0], D[4]
V = {"Juara (OCO 2 sisi)": {}, "K6 (lewati)": {"tren_lawan_w": ("ema200", 0.0)},
     "K6b (lawan risiko 1/2)": {"tren_lawan_w": ("ema200", 0.5)}, "K6c (lawan risiko 1/4)": {"tren_lawan_w": ("ema200", 0.25)}}
# hari order (semua hari bursa yang punya sinyal 07:00)
HR = ((T // 3600) % 24).astype(int); idx = [i for i in np.flatnonzero(HR == m.gb.PLACE_HOUR_UTC) if i >= 250]
hari = {m.wib(T[i] + 3600).date() for i in idx}
def minggu(d): y, w, _ = d.isocalendar(); return (y, w)
nhari = {}
for d in hari: nhari[minggu(d)] = nhari.get(minggu(d), 0) + 1
P = (("2015-2021", m.PILIH), ("2022-Jan25", m.UJI), ("Feb25-skrg", m.KONF), ("2015-skrg", (None, None)))
for nm, sp in V.items():
    tr = m.potong(m.jalankan(dict(sp, ambigu=AMB), D, A, F))
    print(f"\n### {nm}")
    print("| Periode | Trade/minggu | Win | RR | Exp R | PF | R/thn | DD R | DD% 1% | CAGR 1% | W/L maks | Bln+ | Tanpa 2% |")
    for pn, (a, b) in P:
        s = m.stat(tr, a=a, b=b)
        print(f"| {pn} | {s['perbln']*12/52:.1f} | {s['wr']*100:.1f}% | {s['rr']:.2f} | {s['avg']:+.3f} | {s['pf']:.2f} | {s['rthn']:+.1f} | "
              f"{s['dd']:.1f} | {s['ddpct']:.1f}% | {s['cagr']:+.1f}% | {s['wmax']}/{s['lmax']} | {s['blnpos']:.0f}% | {s['tanpa2']:+.0f} |")
    # trade per minggu (hanya minggu dengan 5 hari bursa)
    cnt = {}
    for x in tr: k = minggu(m.wib(x["t0"]).date()); cnt[k] = cnt.get(k, 0) + 1
    print("Distribusi trade per minggu (minggu 5 hari bursa) per tahun: 0 / 1 / 2 / 3 / 4 / 5 hari | rata-rata")
    for y in range(2015, 2027):
        ws = [k for k, n in nhari.items() if n == 5 and k[0] == y]
        if not ws: continue
        dist = np.bincount([min(cnt.get(k, 0), 5) for k in ws], minlength=6)
        print(f"  {y}: " + " / ".join(f"{d/len(ws)*100:3.0f}%" for d in dist) + f" | {np.mean([cnt.get(k,0) for k in ws]):.1f}/5")
    allw = [k for k, n in nhari.items() if n == 5]
    print(f"  SEMUA: rata-rata {np.mean([cnt.get(k,0) for k in allw]):.2f}/5, minggu <= 2 trade: "
          f"{np.mean([cnt.get(k,0) <= 2 for k in allw])*100:.0f}%, minggu >= 4 trade: {np.mean([cnt.get(k,0) >= 4 for k in allw])*100:.0f}%")
