"""Ide #52 (10 Nov 2026, pemilik): SUSULAN WAJIB — setiap hari order pagi (K6) batal harus ada sinyal pengganti; strategi & RR
bebas asal win rate dan RR gabungan tinggi. Keputusan di jam keputusan pertama (close 09:00..21:00 WIB) setelah batas batal
tersentuh, masuk mulai candle berikutnya, tutup 23:00, tetap maks 1 posisi/hari. Sistem dasar = bot live (hibrida MA100).
Varian: (P) S3 live (RSI2 ekstrem) + PENGISI bila tidak ekstrem; atau (W) satu strategi untuk semua hari batal.
Pengisi/strategi: MR50 (BUY bila RSI2<50, SELL bila >=50) · IKUT (arah tembusan = lawan tren, market) · FADE (arah tren
EMA200, market) · D1 (arah tren harian SMA100) · OCO (stop di high/low 3 candle terakhir). SL 1/1,5/2/3 ATR × TP 0,5/1/1,5/2R/tanpa.
Pilih 2015-2021 (skor = R/thn gabungan pilih, syarat win susulan ≥ 50% & PF > 1), uji 2022-Jan 2025 & Setra.
Pemakaian: python susulan_wajib.py <sambung.json> <ambigu.json>"""
import sys, os, json, itertools
import numpy as np
import audit_mesin as m, strat_mesin as sm, multi_mesin as mm
sys.path.insert(0, os.path.join(m.REPO, "riset")); import signifikansi as sg
D = m.muat(sys.argv[1]); T, O, H, L, C = D
A = np.array(m.atr(list(H), list(L), list(C), 14)); F = m.fitur(D, A)
AMB = {int(k): v for k, v in json.load(open(sys.argv[2])).items()}
HR = ((T // 3600) % 24).astype(int); R2 = mm.rsi(C, 2); E = np.array(m.gb.ema(list(C), 200)); KEP = set(m.gb.SUS_JAM_UTC)
sig = mm.sinyal_live(D)
LIVE = mm.baseline(D, A, F, ambigu=AMB)
TANPA = mm.baseline(D, A, F, ambigu=AMB, sus=False)          # MR + K6 tanpa susulan
# SMA100 close 07:00 (tren harian bot)
i07 = np.flatnonzero(HR == sm.PLACE); c07 = C[i07]; cs = np.cumsum(np.insert(c07, 0, 0))
d1 = {}
for k, i in enumerate(i07):
    d1[int(i)] = 1 if k < 99 or c07[k] > (cs[k + 1] - cs[k - 99]) / 100 else -1
hari = []
for x in m.jalankan({"tren_lawan_w": ("ema200", 0.0), "ambigu": AMB}, D, A, F):
    if x["w"] != 0 or x["ip"] in sig: continue
    q = x["i0"]
    while q < len(T) and HR[q] not in KEP and HR[q] != sm.CLOSE: q += 1
    if q >= len(T) - 1 or HR[q] not in KEP: continue
    hari.append(dict(ip=x["ip"], q=q, tren=-x["d"], d1=d1.get(x["ip"], 1)))
print(f"hari K6 batal yang bisa diberi susulan (keputusan <= 21:00): {len(hari)}")
ekstrem = lambda q: R2[q] <= m.gb.SUS_BUY or R2[q] >= m.gb.SUS_SELL
def order(h, jenis):
    q = h["q"]
    if jenis == "S3": return [(1 if R2[q] <= m.gb.SUS_BUY else -1, "market", None)] if ekstrem(q) else []
    if jenis == "MR50": return [(1 if R2[q] < 50 else -1, "market", None)]
    if jenis == "IKUT": return [(-h["tren"], "market", None)]
    if jenis == "FADE": return [(h["tren"], "market", None)]
    if jenis == "D1": return [(h["d1"], "market", None)]
    if jenis == "OCO": return [(1, "stop", H[q - 2:q + 1].max()), (-1, "stop", L[q - 2:q + 1].min())]
def jalan(rencana, sl, tp):
    out = []
    for h, orders in rencana:
        if not orders: continue
        q = h["q"]; dist = sl * A[q]
        if dist <= 0.5: continue
        for j in range(q + 1, min(q + 20, len(T))):
            kand = []
            for d, jn, lvl in orders:
                if jn == "market":
                    if j == q + 1: kand.append((d, O[j]))
                elif (d == 1 and H[j] >= lvl) or (d == -1 and L[j] <= lvl):
                    kand.append((d, max(lvl, O[j]) if d == 1 else min(lvl, O[j])))
            if kand:
                ops = []
                for d, e in kand:
                    ex, t1, why = sm._kelola(D, j, d, e, e - d * dist, e + d * tp * dist if tp else None)
                    ops.append(dict(d=d, e=e, ex=ex, r0=dist, t0=T[j], t1=t1, why=why, w=1.0, ip=h["ip"], i0=j, R=(ex - e) * d / dist, strat="SUS"))
                out.append(min(ops, key=lambda z: z["R"])); break
            if HR[j] == sm.CLOSE: break
    return out
S3 = jalan([(h, order(h, "S3")) for h in hari], m.gb.SUS_SL_ATR, m.gb.SUS_TP_R)
P4 = (("pilih", m.PILIH), ("uji", m.UJI), ("Setra", m.KONF), ("12t", (None, None)))
res = []
for mode, jn, sl, tp in itertools.product(("P", "W"), ("MR50", "IKUT", "FADE", "D1", "OCO"), (1.0, 1.5, 2.0, 3.0), (0.5, 1, 1.5, 2, None)):
    hh = [h for h in hari if not (mode == "P" and ekstrem(h["q"]))]
    sus = (S3 if mode == "P" else []) + jalan([(h, order(h, jn)) for h in hh], sl, tp)
    G = sorted(TANPA + sus, key=lambda z: z["t1"])
    s = {pn: sm.ringkas(sus, a, b) for pn, (a, b) in P4}; g = {pn: sm.ringkas(G, a, b) for pn, (a, b) in P4}
    res.append(dict(k=(mode, jn, sl, tp), sus=sus, G=G, s=s, g=g))
def ok(r): return r["s"]["pilih"]["wr"] >= 0.50 and r["s"]["pilih"]["pf"] > 1
jl = [(int(x["t1"]), float(v)) for x, v in zip(LIVE, m.net(LIVE))]
def baris(nm, sus, G):
    s = {pn: sm.ringkas(sus, a, b) for pn, (a, b) in P4}; g = {pn: sm.ringkas(G, a, b) for pn, (a, b) in P4}
    gl = [(int(x["t1"]), float(v)) for x, v in zip(G, m.net(G))]
    pu = sg.banding(jl, gl, int(m.ts(m.UJI[0])), int(m.ts(m.UJI[1])))["P_rasio_lebih_baik"]
    pk = sg.banding(jl, gl, int(m.ts(m.KONF[0])), int(T[-1]))["P_rasio_lebih_baik"]
    print(f"{nm:<30} susulan n{s['12t']['n']:>4} ({s['12t']['n']/len(hari)*100:3.0f}% hari batal) win " +
          "/".join(f"{s[pn]['wr']*100:.0f}" for pn, _ in P4) + "% RR " + "/".join(f"{s[pn]['rr']:.2f}" for pn, _ in P4) +
          " PF " + "/".join(f"{s[pn]['pf']:.2f}" for pn, _ in P4) + " | GABUNG R/thn " + " · ".join(f"{g[pn]['rthn']:+.1f}" for pn, _ in P4) +
          f" DD {g['12t']['dd']:.0f}R thn+ {g['12t']['thn_pos']}/12 | P uji {pu:.2f} Setra {pk:.2f}")
print("kolom per periode: 2015-21 / 2022-Jan25 / Setra / 12 thn")
baris("BOT LIVE (S3 saja)", S3, LIVE)
print("\n10 teratas dipilih di 2015-2021 (syarat win susulan >= 50%, PF > 1):")
for r in sorted([r for r in res if ok(r)], key=lambda r: -r["g"]["pilih"]["rthn"])[:10]:
    md, jn, sl, tp = r["k"]; baris(f"{'S3+' if md == 'P' else ''}{jn} SL{sl} TP{tp or '-'}", r["sus"], r["G"])
print(f"\nlolos syarat di pilih: {sum(ok(r) for r in res)}/{len(res)}")
