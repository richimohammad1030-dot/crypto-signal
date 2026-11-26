"""Saringan massal XAU (24 Nov 2026). Juara = multi_mesin.baseline (bot live) direproduksi dari komponen yang bisa disetel.
KELUARGA = bank ide: tiap keluarga menghasilkan varian (nama, trade). Sesi riset menambah keluarga BARU di bawah (beri id
X-<nomor>, tulis di riset/xau/ide.md); workflow saringan-malam.yml menjalankannya otomatis malam itu.
Data: bibit Dukascopy riset/data (2004-skrg) + Setra (data_dir/xau.json) sejak Feb 2025 bila ada."""
import gzip, json, os, sys, itertools
import numpy as np
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path[:0] = [REPO, os.path.join(REPO, "riset", "xau", "eksperimen"), os.path.dirname(__file__)]
import audit_mesin as m, multi_mesin as mm
import inti
gb = m.gb

RISIKO = 0.5                       # risiko live (%)
MINGGU_MIN = 3.0
STRES = 0.03                       # biaya tambahan R/trade untuk uji anti-optimis (FX lebih besar: H1 lebih optimis dari M5)                   # T8 XAU
PERIODE = (("2005-01-01", "2022-01-01"), ("2022-01-01", None))   # IS, OOS
BIAYA = 0.40


def muat(data_dir):
    rows = []
    for f in ("xau_dukascopy_h1_2004_2014.json.gz", "xau_dukascopy_h1.json.gz"):
        rows += json.load(gzip.open(os.path.join(REPO, "riset", "data", f), "rt"))
    rows = sorted({r[0]: r for r in rows}.values())
    D = [np.array([r[k] for r in rows], float) for k in range(5)]
    s = os.path.join(data_dir or "", "xau.json")
    if data_dir and os.path.exists(s):
        D = m.sambung(D, m.muat(s))
    A = np.array(m.atr(list(D[2]), list(D[3]), list(D[4]), gb.ATR_N))
    return D, A, m.fitur(D, A)


class Mesin:
    def __init__(self, D, A, F):
        self.D, self.A, self.F = D, A, F; self._c = {}
        self.sk = mm.sinyal_kombo(D); self.sig = mm.sinyal_live(D)
        self.sh = {i: d for i, d in mm.sinyal_hibrida(D).items() if i not in self.sk}

    def _k(self, key, fn):
        if key not in self._c: self._c[key] = fn()
        return self._c[key]

    def trades(self, ks=None, ms=None, mtp=None, k6s=None, k6tp="bot", sus=True):
        D, A, F = self.D, self.A, self.F
        ko = self._k(("ko", ks), lambda: [dict(x, strat0="KOMBO") for x in mm.trades_mr(D, A, self.sk, sl=ks or gb.KOMBO_SL_ATR)])
        mr = self._k(("mr", ms, mtp), lambda: [dict(x, strat0="MR") for x in mm.trades_mr(D, A, self.sh, sl=ms, tp=mtp)])
        k6 = self._k(("k6", k6s, k6tp), lambda: mm.trades_k6(D, A, F, sl=k6s, tp=k6tp))
        su = self._k(("sus",), lambda: mm.trades_sus(D, A, F, sig=self.sig)) if sus else False
        return mm.baseline(D, A, F, mr=ko + mr, k6=k6, sig=self.sig, sus=su)


def ke_inti(tr):
    return [dict(t0=x["t0"], t1=x["t1"], r=(x["R"] - BIAYA / x["r0"]) * x["w"], w=x["w"], strat=x.get("strat", "?"), ip=x.get("ip"))
            for x in tr if x["w"] > 0]


def bobot(tr, w):
    out = []
    for x in tr:
        k = w.get(x["strat"], 1.0)
        if k > 0: out.append(dict(x, r=x["r"] * k, w=x["w"] * k))
    return out


# ======================= BANK IDE (keluarga) =======================
def X001_komponen(M):
    """SL/TP tiap komponen + susulan on/off (celah: DD, kalah beruntun, tahun minus)."""
    for ks, ms, mtp, k6s, k6tp, sus in itertools.product((1.0, 1.5, 2.0, 2.5), (2.0, 2.5, 3.0, 3.5), (None, 1.0, 2.0),
                                                          (1.25, 1.5, 2.0), (2.0, 3.0, "bot", None), (True, False)):
        yield (f"X001 kombo{ks} mr{ms}/tp{mtp} k6{k6s}/tp{k6tp} sus{int(sus)}",
               ke_inti(M.trades(ks, ms, mtp, k6s, k6tp, sus)))


def X002_monitor_pf(M):
    """T2 adaptif: risiko turun/strategi mati bila PF bergulir < ambang (tanpa melihat masa depan)."""
    base = ke_inti(M.trades())
    for hari, amb, w, kun, mn in itertools.product((180, 365, 730), (0.9, 1.0, 1.1), (0.0, 0.5), (None, "strat"), (15, 30)):
        yield f"X002 monitorPF {hari}h <{amb} w{w} {kun or 'bot'} n{mn}", inti.monitor_pf(base, hari, amb, w, mn, kun)


def X003_monitor_ekuitas(M):
    base = ke_inti(M.trades())
    for n, w in itertools.product((10, 20, 40, 60), (0.0, 0.5)):
        yield f"X003 kurva-ekuitas n{n} w{w}", inti.monitor_ekuitas(base, n, w)


def X004_bobot_strategi(M):
    """Bobot risiko relatif per strategi (memangkas strategi lemah / memperbesar yang kuat)."""
    base = ke_inti(M.trades())
    for a, b, c, d in itertools.product((0.5, 1.0, 1.5), repeat=4):
        if (a, b, c, d) == (1.0,) * 4: continue
        yield f"X004 bobot KOMBO{a} MR{b} K6{c} SUS{d}", bobot(base, dict(KOMBO=a, MR=b, K6=c, SUS=d))


def X005_filter_vol(M):
    """Lewati hari volatilitas ekstrem (persentil ATR 1 tahun pada candle keputusan)."""
    base = ke_inti(M.trades()); P = M.F["pct1y"]
    for lo, hi in ((None, 0.8), (None, 0.9), (None, 0.95), (0.05, None), (0.1, None), (0.2, None), (0.1, 0.9)):
        out = [x for x in base if x["ip"] is None or np.isnan(P[x["ip"]]) or ((lo is None or P[x["ip"]] >= lo) and (hi is None or P[x["ip"]] <= hi))]
        yield f"X005 vol-pct1y {lo}-{hi}", out


def X006_kombinasi_adaptif(M):
    """Gabungan: komponen terbaik umum (SL lebih lebar/sempit) + monitor PF per strategi."""
    for ks, ms, k6s in itertools.product((1.5, 2.0), (2.5, 3.0), (1.25, 1.5)):
        base = ke_inti(M.trades(ks, ms, None, k6s))
        for hari, amb in itertools.product((365, 730), (0.9, 1.0)):
            yield f"X006 kombo{ks} mr{ms} k6{k6s} + monitorPF {hari}h <{amb} strat", inti.monitor_pf(base, hari, amb, 0.0, 20, "strat")


def X007_jeda_beruntun(M):
    """T7 kalah beruntun: berhenti setelah k kalah beruntun sampai trade bayangan menang (+ kombinasi monitor PF)."""
    base = ke_inti(M.trades())
    for k in (3, 4, 5, 6, 7, 8):
        yield f"X007 jeda setelah {k} kalah", inti.jeda_beruntun(base, k)
        yield f"X007 jeda {k} + monitorPF 365h <1.0", inti.jeda_beruntun(inti.monitor_pf(base, 365, 1.0, 0.0, 20), k)


KELUARGA = [X001_komponen, X002_monitor_pf, X003_monitor_ekuitas, X004_bobot_strategi, X005_filter_vol, X006_kombinasi_adaptif, X007_jeda_beruntun]


def juara(M):
    return "JUARA (live)", ke_inti(M.trades())
