"""UJI PENUH sesi 26 Nov 2026: 3 teratas -> WALK-FORWARD BERLABUH 2004-2026 + P_rasio (signifikansi.banding) + Setra.
Basis = mesin saringan massal (riset/massal/xau.py; juara live, ambigu BUY) dalam satuan inti (r bersih biaya 0,40 USD).
  A  SKILL SNR (ii) SL di balik zona SWING (saringan_1126 no.1-3): WF pilih {dasar, ZONA, KETAT, D1}.
  B  SUMBER EDGE BARU: pergantian bulan (TOM) BUY 07:00 (hari bursa terakhir + 3 pertama; saringan no.7, lift +0,13R/trade
     vs BUY semua hari 2005-14). Maks 1 posisi/hari -> cara gabung:
       TA  hari TOM: KOMBO tetap prioritas; selain itu TOM BUY menggantikan MR/K6/SUS
       TB  hari TOM: hanya trade SELL juara yang diganti TOM BUY (+ isi hari kosong)
       TC  hari TOM: hanya isi hari tanpa trade juara
       TD  hari TOM: trade SELL juara dilewati (tanpa trade baru)
     WF pilih {dasar, TA, TB, TC, TD}.
  C  T2 MONITOR EDGE (penantang saringan massal 24-25 Nov: X006/X002): risiko komponen/bot turun bila PF trade tutup
     N hari terakhir < ambang. WF pilih dari {dasar} + 72 varian X002 + 16 varian X006. Juga varian tetap teratas & DD pada
     risiko 0,8% (syarat blocker B2: DD <= 20%).
Jendela: pilih 2005..Y -> uji Y+1..Y+2, Y = 2010..2024 (semua tahun 2011-2026 hasil uji). Skor = tahun minus paling sedikit, lalu R/thn.
Pemakaian: python uji_1126.py <data_dir berisi xau.json>"""
import sys, os, collections, itertools
import numpy as np
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "saringan_1126.py")).read().split('"""', 2)[2])
sys.path.insert(0, os.path.join(REPO, "riset")); import signifikansi as sg
HAS = []
WIN = [(Y, Y + 1, Y + 2) for Y in range(2010, 2025, 2)]
yr = inti.tahun

def per_tahun(tr, y0, y1):
    th = {y: 0.0 for y in range(y0, y1 + 1)}
    for x in tr:
        y = yr(x["t1"])
        if y0 <= y <= y1: th[y] += x["r"]
    return th

def skor(tr, y1):
    v = np.array(list(per_tahun(tr, 2005, y1).values())); return (-(v < 0).sum(), round(v.mean(), 6))

LIVE = B.ke_inti(RAW)
def ringkas(nm, tr, base=None):
    base = base or LIVE
    th = per_tahun(tr, 2011, 2026); v = np.array(list(th.values()))
    s = [x for x in tr if yr(x["t1"]) >= 2011]; r = np.array([x["r"] for x in sorted(s, key=lambda x: x["t1"])]); c = np.cumsum(r)
    dd = (np.maximum.accumulate(np.concatenate([[0], c]))[1:] - c).max()
    t0, t1 = int(inti.ts("2011-01-01")), int(inti.ts("2027-01-01")); ts25 = int(inti.ts("2025-02-01"))
    jl = [(int(x["t1"]), x["r"]) for x in base]; gl = [(int(x["t1"]), x["r"]) for x in tr]
    P = sg.banding(jl, gl, t0, t1)["P_rasio_lebih_baik"]
    Ps = sg.banding(jl, gl, ts25, t1); s8 = inti.nilai(tr, 0.8, "2011-01-01", None)
    print(f"{nm:<26} " + " ".join(f"{y % 100}:{x_:+.0f}" for y, x_ in th.items()))
    print(f"{'':<26} R/thn {v.mean():+5.1f} · minus {(v < 0).sum()}/16 · terburuk {v.min():+.0f} · DD {dd:.0f}R · R/trade {r.mean():+.3f} · "
          f"{len(r) / 16 / 52.18:.1f}/mg · P {P:.2f} · Setra P {Ps['P_rasio_lebih_baik']:.2f} ({Ps['penantang']['R_thn']:+.1f} vs "
          f"{Ps['juara']['R_thn']:+.1f}) · @0,8%: DD {s8['dd']:.1f}% {s8['persen']:+.1f}%/thn · beruntun {s8['beruntun']}")
    return dict(nm=nm, rthn=v.mean(), minus=int((v < 0).sum()), worst=v.min(), dd=dd, P=P, Ps=Ps["P_rasio_lebih_baik"], th=th,
                dd8=s8["dd"], p8=s8["persen"], ber=s8["beruntun"], mg=len(r) / 16 / 52.18)

def wf(nm, SIS):
    sel, pil = [], []
    for Y, a, b in WIN:
        best = max((skor(tr, Y), k) for k, tr in SIS.items()); pil.append((Y, best[1]))
        sel += [x for x in SIS[best[1]] if a <= yr(x["t1"]) <= b]
    r = ringkas(nm, sel); print("   pilihan:", pil); r["pil"] = pil; return r

print("\n=== SISTEM LIVE (uji 2011-2026) ===")
HAS.append(ringkas("SISTEM LIVE", LIVE))

# ---------------- A: SNR SL zona ----------------
def sl_zona_all(S, ketat):
    out = []
    for x in RAW:
        if x["strat"] in ("KOMBO", "MR"):
            a = A[x["i0"] - 1]; z = zona_belakang(S, x["t0"], x["e"], x["d"], a)
            if z is not None:
                slp = z - x["d"] * 0.25 * a
                if not ketat or (x["e"] - slp) * x["d"] < x["r0"]:
                    out.append(ulang(x, slp, None)); continue
        out.append(x)
    return B.ke_inti(out)
print("\n=== A · SKILL SNR (ii) SL di balik zona SWING ===")
SA = {"dasar": LIVE, "ZONA": sl_zona_all(SW, False), "KETAT": sl_zona_all(SW, True), "D1": sl_zona_all(SWD, False)}
for k in ("ZONA", "KETAT", "D1"): ringkas(f"  tetap SL-{k}", SA[k])
HAS.append(wf("A SNR-SL WF", SA))
for k in ("ZONA",):
    s5 = inti.nilai(SA[k], 0.5, "2005-01-01", None); j5 = inti.nilai(LIVE, 0.5, "2005-01-01", None)
    print(f"   2005-2026 SL-{k}: minus {s5['minus']} PF {s5['pf']:.2f} DD {s5['dd']:.1f}% vs live minus {j5['minus']} PF {j5['pf']:.2f} DD {j5['dd']:.1f}%")

# ---------------- B: TOM ----------------
print("\n=== B · SUMBER EDGE BARU: pergantian bulan (TOM) BUY 07:00 ===")
hari = lambda i: int(np.searchsorted(i07, i, side="right") - 1)
TOMK = {hari(x["i0"] - 1): x for x in G7}                  # hari TOM -> trade TOM (entry open setelah close 07:00)
def gab(mode):
    out, dipakai = [], set()
    for x in RAW:
        k = hari(x["ip"] if x.get("ip") is not None else x["i0"] - 1)
        if k in TOMK:
            dipakai.add(k)
            if mode == "TA" and x["strat"] != "KOMBO": out.append(TOMK[k]); continue
            if mode == "TB" and x["d"] == -1: out.append(TOMK[k]); continue
            if mode == "TD" and x["d"] == -1: continue
        out.append(x)
    if mode in ("TA", "TB", "TC"):
        out += [t for k, t in TOMK.items() if k not in dipakai]
    return B.ke_inti(out)
SB = {"dasar": LIVE, **{k: gab(k) for k in ("TA", "TB", "TC", "TD")}}
for k in ("TA", "TB", "TC", "TD"): ringkas(f"  tetap {k}", SB[k])
HAS.append(wf("B TOM WF", SB))
TM = B.ke_inti(G7); th = per_tahun(TM, 2005, 2026)
hl, hg = collections.defaultdict(float), collections.defaultdict(float)
for x in LIVE: hl[int(x["t0"] // 86400)] += x["r"]
for x in TM: hg[int(x["t0"] // 86400)] += x["r"]
ks = sorted(set(hl) | set(hg))
print(f"TOM mandiri 2005-2026: n {len(TM)} · R/trade {np.mean([x['r'] for x in TM]):+.3f} · minus {sum(v < 0 for v in th.values())}/22 · "
      f"kor harian vs live {np.corrcoef([hl.get(k, 0) for k in ks], [hg.get(k, 0) for k in ks])[0, 1]:+.2f}")
print("   " + " ".join(f"{y % 100}:{v:+.0f}" for y, v in th.items()))
for a_, b_ in (("2005-01-01", "2015-01-01"), ("2015-01-01", "2022-01-01"), ("2022-01-01", "2027-01-01")):
    v = [x["r"] for x in TM if inti.ts(a_) <= x["t0"] < inti.ts(b_)]
    print(f"   TOM {a_[:4]}-{int(b_[:4]) - 1}: n {len(v)} R/trade {np.mean(v):+.3f}")

# ---------------- C: monitor edge (T2) ----------------
print("\n=== C · T2 MONITOR EDGE (penantang massal X002/X006) ===")
SC = {"dasar": LIVE}
for hr_, amb, w, kun, mn in itertools.product((180, 365, 730), (0.9, 1.0, 1.1), (0.0, 0.5), (None, "strat"), (15, 30)):
    SC[f"X002 {hr_}h<{amb} w{w} {kun or 'bot'} n{mn}"] = inti.monitor_pf(LIVE, hr_, amb, w, mn, kun)
for ks_, ms, k6s in itertools.product((1.5, 2.0), (2.5, 3.0), (1.25, 1.5)):
    bs = B.ke_inti(M.trades(ks_, ms, None, k6s))
    for hr_, amb in itertools.product((365, 730), (0.9, 1.0)):
        SC[f"X006 kombo{ks_} mr{ms} k6{k6s} {hr_}h<{amb}"] = inti.monitor_pf(bs, hr_, amb, 0.0, 20, "strat")
for k in ("X006 kombo2.0 mr3.0 k61.5 365h<1.0", "X002 730h<1.1 w0.0 bot n15", "X002 365h<1.0 w0.0 strat n15",
          "X002 365h<1.0 w0.5 strat n15", "X002 365h<1.0 w0.5 bot n15"):
    ringkas(f"  tetap {k[:24]}", SC[k]); print(f"     ({k})")
HAS.append(wf("C MONITOR WF (89 varian)", SC))
SC2 = {k: v for k, v in SC.items() if k == "dasar" or k.startswith("X002") and "strat" in k}
HAS.append(wf("C' MONITOR per strat WF", SC2))
print("\nRingkas:")
for h in HAS:
    print(f"  {h['nm']:<26} R/thn {h['rthn']:+5.1f} · minus {h['minus']} · terburuk {h['worst']:+.0f} · DD {h['dd']:.0f}R · P {h['P']:.2f} · "
          f"Setra {h['Ps']:.2f} · @0,8% DD {h['dd8']:.1f}% {h['p8']:+.1f}%/thn · {h['mg']:.1f}/mg")
