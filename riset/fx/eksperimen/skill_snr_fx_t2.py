"""KURIKULUM SKILL 1 · SNR · FX MAJOR · TAHAP 2 BISA MEMAKAI putaran 1 (sesi 27 Nov 2026).
Dari tahap 1 (skill_snr_fx_t1.py, 7/7 pair searah): SUPDEM & SWING (sendiri) dan konfluensi >= 3 lebih sering MEMANTUL,
BULAT 100 pip & PWL lebih sering DITEMBUS. Juara FX (UTAMA + SUSULAN = breakout PWH/PWL, LANJUT setelah TP) diberi SNR:
  F  = filter : batalkan order bila ada zona yang memantul (jenis dipilih) di JALUR TP (di luar entry+0,15R s.d. TP).
  TP = TP zona : TP dipotong ke tepi dekat zona penghalang (batal bila < 1R).
  SL = SL zona : SL dipindah ke balik zona penahan tepat di belakang entry (maks 0,5 ATR), TP tetap.
  B  = bulat  : batalkan order bila TIDAK ada pendorong tembus (bulat 100 / PWL) — hanya catatan, mengurangi frekuensi.
Semua keputusan memakai zona yang sudah tersedia (tav) sebelum order aktif (t_on). LANJUT dihitung ulang dari hasil baru.
Satuan: R per trade (risiko live 0,75% → %/thn = R/thn × 0,75). IS 2015-06..2022, OOS 2023-2026.
Pemakaian: python riset/fx/eksperimen/skill_snr_fx_t2.py"""
import os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(REPO, "riset", "xau", "eksperimen")); sys.path.insert(0, os.path.join(REPO, "forex_major"))
import numpy as np
os.chdir(os.path.join(REPO, "forex_major"))
import backtest as B
import skill_snr as sk
import saringan_2026_11_22 as S
import riset_putaran6 as P6
import riset_putaran7 as P7
import fx_live as F

IS = (S.SPLIT if False else None)
T_IS0 = 1433116800      # 2015-06-01
T_OOS = 1672531200      # 2023-01-01
T_END = 1763683200      # 2025-11-21 diganti saat jalan: akhir data


def zona_pair(P):
    sc = 1.0 / B.PIP[P.name]
    T = P.h1["t"].astype(float); O, H, L, C = (P.h1[k] * sc for k in "ohlc")
    Z, Bk = sk.bangun([T, O, H, L, C])
    cat = np.array(["SWING" if z["jenis"].startswith("SWING") else "PERIODE" if z["jenis"][:2] in ("PD", "PW") else "SUPDEM" for z in Z])
    return dict(sc=sc, lo=np.array([z["lo"] for z in Z]) / sc, hi=np.array([z["hi"] for z in Z]) / sc,
                tav=np.array([z["tav"] for z in Z]), exp=np.array([z["exp"] for z in Z]), cat=cat,
                kuat=np.array([z["kuat"] for z in Z]), tf=np.array([z["tf"] for z in Z]))


def di_jalur(Zp, o, cats, kuat_min=1, dari=0.15, sampai=1.0):
    """Zona aktif (kategori cats) yang SELURUHNYA/SEBAGIAN berada di (entry + dari·R, entry + sampai·(TP-entry)]. Return jarak tepi terdekat (harga) atau None."""
    s = o["side"]; e = o["price"]; r0 = abs(e - o["sl"]); tpd = abs(o["tp"] - e)
    a, b = e + s * dari * r0, e + s * sampai * tpd
    lo, hi = min(a, b), max(a, b)
    m = (Zp["tav"] <= o["t_on"]) & (Zp["exp"] > o["t_on"]) & np.isin(Zp["cat"], cats) & (Zp["kuat"] >= kuat_min) \
        & (Zp["hi"] >= lo) & (Zp["lo"] <= hi)
    if not m.any(): return None
    near = Zp["lo"][m] if s > 0 else Zp["hi"][m]
    return float(near.min()) if s > 0 else float(near.max())


def di_belakang(Zp, o, cats, maks_r=1.5):
    """Zona penahan di belakang entry (antara entry dan entry - maks_r·R). Return tepi jauh terjauh yang masih dalam batas."""
    s = o["side"]; e = o["price"]; r0 = abs(e - o["sl"])
    lo, hi = (e - maks_r * r0, e) if s > 0 else (e, e + maks_r * r0)
    m = (Zp["tav"] <= o["t_on"]) & (Zp["exp"] > o["t_on"]) & np.isin(Zp["cat"], cats) & (Zp["hi"] >= lo) & (Zp["lo"] <= hi)
    if not m.any(): return None
    far = Zp["lo"][m].min() if s > 0 else Zp["hi"][m].max()
    return float(far)


def bulat_dijalur(P, o):
    st = 100 * B.PIP[P.name]; s = o["side"]; e = o["price"]; tp = o["tp"]
    lo, hi = min(e, tp), max(e, tp)
    k = np.ceil(lo / st) * st
    return k <= hi


def bungkus(gen, ZP, mode, cats=("SUPDEM",), kuat_min=1, dari=0.15, sampai=1.0, data=None):
    Pm = {P.name: P for P in data} if data else {}
    def g(P):
        out = gen(P); Zp = ZP[P.name]; res = {}
        for d, lst in out.items():
            baru = []
            for o in lst:
                if mode == "F":
                    if di_jalur(Zp, o, cats, kuat_min, dari, sampai) is not None: continue
                elif mode == "TP":
                    z = di_jalur(Zp, o, cats, kuat_min, dari, sampai)
                    if z is not None:
                        r0 = abs(o["price"] - o["sl"]); nd = abs(z - o["price"])
                        if nd < 1.0 * r0: continue
                        o = dict(o, tp=o["price"] + o["side"] * nd)
                elif mode == "SL":
                    z = di_belakang(Zp, o, cats)
                    if z is not None:
                        r0 = abs(o["price"] - o["sl"]); a = r0 / 0.3
                        nsl = z - o["side"] * 0.05 * a
                        if abs(o["price"] - nsl) <= 0.5 * a and abs(o["price"] - nsl) > r0:
                            o = dict(o, sl=nsl)
                elif mode == "B":
                    if not bulat_dijalur(P, o): continue
                baru.append(o)
            if baru: res[d] = baru
        return res
    return g


def juara_snr(data, ZP, mode=None, **kw):
    gu = P6.utama_gen(F.UK)
    if mode: gu = bungkus(gu, ZP, mode, data=data, **kw)
    B.MAX_DAY = 2
    try: main = B.portfolio(S.run(data, gu))
    finally: B.MAX_DAY = 4
    filled = {(t["pair"], t["t"] // 86400) for t in main}
    gs = P7.sus_gen(dict(F.SK, um=F.UK["dow"]), filled, F.UK["exp"])
    if mode: gs = bungkus(gs, ZP, mode, data=data, **kw)
    sus = S.run(data, gs)
    b3 = S.run(data, P7.bot3_gen(F.B3K, main + sus))
    return main + sus + b3


def bobot(tr, ZP, cats, w_hal=0.5, w_bulat=1.0, data=None):
    """Versi BOBOT (frekuensi tetap): risiko × w_hal bila zona memantul di jalur TP (dinilai saat fill), × w_bulat bila
    jalur bersih DAN ada angka bulat 100 pip di jalur (pendorong tembus)."""
    Pm = {P.name: P for P in data}; out = []
    for t in tr:
        o = dict(side=t["side"], price=t["entry"], sl=t["sl"], tp=t["tp"], t_on=t["t"])
        if abs(o["tp"] - o["price"]) < 1e-12: out.append(t); continue
        w = w_hal if di_jalur(ZP[t["pair"]], o, cats) is not None else (w_bulat if bulat_dijalur(Pm[t["pair"]], o) else 1.0)
        out.append(dict(t, R=t["R"] * w))
    return out


def runtun(tr):
    m = c = 0
    for t in sorted(tr, key=lambda x: x["t"]):
        c = c + 1 if t["R"] < 0 else 0; m = max(m, c)
    return m


def baris(nama, tr):
    a = S.ystat(tr, T_IS0, T_OOS); b = S.ystat(tr, T_OOS, T_END); f = S.ystat(tr, T_IS0, T_END)
    yi = (T_OOS - T_IS0) / 86400 / 365.25; yo = (T_END - T_OOS) / 86400 / 365.25
    def k(s, y): return (f"PF {s['pf']:.2f} WR {s['wr']:.0%} {s['R'] / y * 0.75:+5.1f}%/th DD {s['dd'] * 0.75:4.1f}% "
                         f"rasio {s['R'] / y / max(s['dd'], 1e-9):.2f} th- {s['neg']} {s['pw']:.1f}/mg")
    print(f"{nama:<34} IS {k(a, yi)} | OOS {k(b, yo)} | runtun {runtun(tr)} | th- semua {[y for y, v in f['years'].items() if v < 0]}")
    return a, b, f


if __name__ == "__main__":
    t0 = time.time()
    data = [B.load(p) for p in F.PAIRS]
    T_END = max(int(P.t[-1]) for P in data)
    ZP = {P.name: zona_pair(P) for P in data}
    print(f"zona siap {time.time() - t0:.0f} dtk")
    hasil = {}
    hasil["JUARA"] = baris("JUARA (live)", juara_snr(data, ZP))
    VAR = [
        ("F supdem jalur", dict(mode="F", cats=("SUPDEM",))),
        ("F swing jalur", dict(mode="F", cats=("SWING",))),
        ("F swing kuat>=2 jalur", dict(mode="F", cats=("SWING",), kuat_min=2)),
        ("F supdem+swing jalur", dict(mode="F", cats=("SUPDEM", "SWING"))),
        ("F supdem 0-60% jalur", dict(mode="F", cats=("SUPDEM",), sampai=0.6)),
        ("TP supdem", dict(mode="TP", cats=("SUPDEM",))),
        ("TP supdem+swing", dict(mode="TP", cats=("SUPDEM", "SWING"))),
        ("SL di balik supdem", dict(mode="SL", cats=("SUPDEM",))),
        ("SL di balik supdem+swing", dict(mode="SL", cats=("SUPDEM", "SWING"))),
        ("B bulat100 di jalur (wajib)", dict(mode="B")),
    ]
    for nm, kw in VAR: hasil[nm] = baris(nm, juara_snr(data, ZP, **kw))
    J = juara_snr(data, ZP)
    for nm, cats, wh, wb in [("W supdem 0,5x", ("SUPDEM",), 0.5, 1.0), ("W supdem 0,0x (=filter, frek tetap?)", ("SUPDEM",), 0.0, 1.0),
                             ("W supdem+swing 0,5x", ("SUPDEM", "SWING"), 0.5, 1.0), ("W supdem 0,5x + bulat 1,5x", ("SUPDEM",), 0.5, 1.5),
                             ("W supdem 0,5x + bulat 1,25x", ("SUPDEM",), 0.5, 1.25), ("W supdem+swing 0,5x + bulat 1,5x", ("SUPDEM", "SWING"), 0.5, 1.5)]:
        hasil[nm] = baris(nm, bobot(J, ZP, cats, wh, wb, data))
    print(f"waktu {time.time() - t0:.0f} dtk")
