"""Statistik lengkap bot XAU live (MR + K6 + susulan, 5 Nov 2026) + pencarian celah: segmen yang LEMAH KONSISTEN di 3 periode.
R bersih biaya 0,40 USD; urutan candle ambigu M1 (2022+). Pemakaian: python statistik_live.py <xau_sambung.json> <ambigu.json>"""
import sys, json
import numpy as np
import audit_mesin as m, strat_mesin as sm, multi_mesin as mm
D = m.muat(sys.argv[1]); T, O, H, L, C = D
A = np.array(m.atr(list(H), list(L), list(C), 14)); F = m.fitur(D, A)
AMB = {int(k): v for k, v in json.load(open(sys.argv[2])).items()}
G = mm.baseline(D, A, F, ambigu=AMB); RN = m.net(G)
for x, r in zip(G, RN): x["Rn"] = float(r)
E = np.array(m.gb.ema(list(C), 200)); R2 = mm.rsi(C, 2)
# ATR relatif: ATR saat keputusan / median ATR 500 candle terakhir
idx = {int(t): i for i, t in enumerate(T)}
for x in G:
    i = x["ip"]; x["atr_rel"] = A[i] / np.median(A[max(0, i - 500):i + 1])
    x["searah"] = (C[i] > E[i]) == (x["d"] == 1)
    x["hari"] = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"][(int(T[x["i0"]]) // 86400 + 3) % 7]
    x["biaya_R"] = 0.40 / x["r0"]; x["jam"] = (x["t1"] - x["t0"]) / 3600
    x["rsi"] = R2[i]
P = (("2015-21", "2015-01-01", "2022-01-01"), ("2022-Jan25", "2022-01-01", "2025-02-01"), ("Setra", "2025-02-01", None))
def dalam(x, a, b): return x["t0"] >= m.ts(a) and (b is None or x["t0"] < m.ts(b))
def baris(nm, f):
    out, lemah = [], 0
    for pn, a, b in P:
        r = [x["Rn"] for x in G if f(x) and dalam(x, a, b)]
        if not r: out.append("      -      "); continue
        w = [v for v in r if v > 0]; l = [-v for v in r if v <= 0]
        pf = sum(w) / sum(l) if l else 9
        out.append(f"{np.mean(r):+.3f} PF{pf:4.2f} n{len(r):>4}")
        lemah += np.mean(r) < 0
    r = [x["Rn"] for x in G if f(x)]
    print(f"  {nm:<26}" + " | ".join(out) + f" | 12t {np.mean(r):+.3f} tot {sum(r):+6.1f}R" + ("  <<< LEMAH 3/3" if lemah == 3 else ""))
print("Kolom: rata R bersih/trade, PF, n per periode (2015-21 | 2022-Jan25 | Setra) | 12 tahun\n")
print("1) Total & per strategi/arah"); baris("SEMUA", lambda x: True)
for st in ("MR", "K6", "SUS"):
    baris(st, lambda x, st=st: x["strat"] == st)
    for d, nm in ((1, "BUY"), (-1, "SELL")): baris(f"  {st} {nm}", lambda x, st=st, d=d: x["strat"] == st and x["d"] == d)
print("\n2) Searah / melawan tren EMA200 H1 saat keputusan")
for st in ("MR", "SUS"):
    for v, nm in ((True, "searah"), (False, "lawan")): baris(f"{st} {nm} tren", lambda x, st=st, v=v: x["strat"] == st and x["searah"] == v)
print("\n3) Volatilitas (ATR saat keputusan / median ATR 500 candle)")
for lo, hi in ((0, 0.8), (0.8, 1.0), (1.0, 1.25), (1.25, 1.6), (1.6, 99)):
    for st in ("MR", "K6", "SUS"):
        baris(f"{st} ATR rel {lo}-{hi if hi < 99 else '+'}", lambda x, st=st, lo=lo, hi=hi: x["strat"] == st and lo <= x["atr_rel"] < hi)
print("\n4) Kedalaman RSI(2) MR (BUY: makin kecil makin ekstrem; SELL: makin besar)")
for lo, hi in ((0, 10), (10, 25), (25, 43.76)): baris(f"MR BUY RSI {lo}-{hi}", lambda x, lo=lo, hi=hi: x["strat"] == "MR" and x["d"] == 1 and lo <= x["rsi"] < hi)
for lo, hi in ((71.22, 85), (85, 95), (95, 101)): baris(f"MR SELL RSI {lo}-{hi}", lambda x, lo=lo, hi=hi: x["strat"] == "MR" and x["d"] == -1 and lo <= x["rsi"] < hi)
print("\n5) Hari"); [baris(h, lambda x, h=h: x["hari"] == h) for h in ("Sen", "Sel", "Rab", "Kam", "Jum")]
print("\n6) Cara keluar")
for w in ("SL", "TP", "TUTUP"): baris(w, lambda x, w=w: x["why"].startswith(w) or (w == "TUTUP" and "TUTUP" in x["why"]))
print("\n7) Biaya: rata biaya per trade dalam R per periode")
for pn, a, b in P:
    t = [x for x in G if dalam(x, a, b)]
    print(f"  {pn:<11} biaya {np.mean([x['biaya_R'] for x in t]):.3f}R/trade = {sum(x['biaya_R'] for x in t) / ((t[-1]['t1'] - t[0]['t0']) / 86400 / 365.25):.1f} R/thn · "
          f"R kotor/thn {sum(x['R'] for x in t) / ((t[-1]['t1'] - t[0]['t0']) / 86400 / 365.25):+.1f} · bersih {sum(x['Rn'] for x in t) / ((t[-1]['t1'] - t[0]['t0']) / 86400 / 365.25):+.1f}")
print("\n8) Drawdown terdalam (R bersih)")
c = np.cumsum(RN); pk = np.maximum.accumulate(np.concatenate([[0], c]))[1:]; dd = pk - c
ep, i = [], 0
while i < len(dd):
    if dd[i] > 0:
        j = i
        while j < len(dd) and dd[j] > 0: j += 1
        k = i + int(np.argmax(dd[i:j])); ep.append((dd[k], i, k, j)); i = j
    else: i += 1
for v, i, k, j in sorted(ep, reverse=True)[:5]:
    pul = m.wib(G[j]["t1"]).strftime("%b %Y") if j < len(G) else "belum pulih"
    print(f"  -{v:5.1f}R  mulai {m.wib(G[i]['t0']):%b %Y}, dasar {m.wib(G[k]['t1']):%b %Y}, pulih {pul} · trade {k - i + 1}")
print("\n9) Per tahun & bulan positif")
th = {}
for x in G: th.setdefault(m.wib(x["t0"]).year, []).append(x["Rn"])
print("  " + " · ".join(f"{y} {sum(v):+.0f}" for y, v in th.items()))
bl = {}
for x in G: bl.setdefault(m.wib(x["t0"]).strftime("%Y-%m"), 0); bl[m.wib(x["t0"]).strftime("%Y-%m")] += x["Rn"]
v = np.array(list(bl.values())); print(f"  bulan positif {np.mean(v > 0)*100:.0f}% · bulan terbaik {v.max():+.1f}R · terburuk {v.min():+.1f}R · median {np.median(v):+.2f}R")
