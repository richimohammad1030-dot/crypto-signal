"""Saringan massal FX MAJOR (24 Nov 2026). Juara = UTAMA + SUSULAN + LANJUT persis fx_live (via saringan_2026_11_22.juara,
spread asli Exness +0,2 pip). Bank ide: keluarga F-<nomor>; sesi riset FX menambah keluarga baru di bawah.
Data: forex_major/data (Dukascopy H1 2015-skrg, 7 pair)."""
import os, sys, itertools
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path[:0] = [os.path.join(REPO, "forex_major"), os.path.join(REPO, "riset", "fx", "eksperimen"), os.path.dirname(__file__)]
import backtest as B
import riset_putaran6 as P6, riset_putaran7 as P7
import fx_live as FL
import saringan_2026_11_22 as SG
import inti

RISIKO = FL.RISK_PCT
MINGGU_MIN = 3.0
PERIODE = (("2015-06-01", "2023-01-01"), ("2023-01-01", None))


def muat(data_dir):
    return ([B.load(p) for p in FL.PAIRS],)


class Mesin:
    def __init__(self, data):
        self.data = data; self._c = {}

    def tiga(self, uk=None, sk=None, b3=None, max_utama=2):
        key = (tuple(sorted((uk or {}).items())), tuple(sorted((sk or {}).items())), tuple(sorted((b3 or {}).items())), max_utama)
        if key in self._c: return self._c[key]
        UK, SK, B3K = dict(FL.UK, **(uk or {})), dict(FL.SK, **(sk or {})), dict(FL.B3K, **(b3 or {}))
        B.MAX_DAY = max_utama
        try: main = B.portfolio(P6.run_gen(self.data, P6.utama_gen(UK)))
        finally: B.MAX_DAY = 4
        filled = {(t["pair"], t["t"] // 86400) for t in main}
        sus = P6.run_gen(self.data, P7.sus_gen(dict(SK, um=UK["dow"]), filled, UK["exp"]))
        b3 = P6.run_gen(self.data, P7.bot3_gen(B3K, main + sus))
        out = ke_inti(main, "N3") + ke_inti(sus, "SUS") + ke_inti(b3, "B3")
        self._c[key] = sorted(out, key=lambda x: x["t1"]); return self._c[key]


def ke_inti(tr, k):
    return [dict(t0=t["t"], t1=t["t_exit"], r=t["R"], w=1.0, strat=k, pair=t["pair"]) for t in tr]


def bobot(tr, w):
    return [dict(x, r=x["r"] * w.get(x["strat"], 1.0)) for x in tr if w.get(x["strat"], 1.0) > 0]


# ======================= BANK IDE =======================
def F001_monitor_pf(M):
    base = M.tiga()
    for hari, amb, w, kun, mn in itertools.product((180, 365, 730), (0.9, 1.0, 1.1), (0.0, 0.5), (None, "strat", "pair"), (15, 30)):
        yield f"F001 monitorPF {hari}h <{amb} w{w} {kun or 'bot'} n{mn}", inti.monitor_pf(base, hari, amb, w, mn, kun)


def F002_kurva_ekuitas(M):
    base = M.tiga()
    for n, w in itertools.product((10, 20, 40, 60), (0.0, 0.5)):
        yield f"F002 kurva-ekuitas n{n} w{w}", inti.monitor_ekuitas(base, n, w)


def F003_bobot_bot(M):
    base = M.tiga()
    for a, b, c in itertools.product((0.5, 0.75, 1.0, 1.5), repeat=3):
        if (a, b, c) != (1.0, 1.0, 1.0): yield f"F003 bobot N3{a} SUS{b} B3{c}", bobot(base, dict(N3=a, SUS=b, B3=c))


def F004_utama(M):
    """Parameter UTAMA (celah: tahun minus, DD)."""
    for slm, tpm, be in itertools.product((0.2, 0.3, 0.4), (0.5, 0.6, 0.8, 1.0), (0.3, 0.5, 0.7)):
        yield f"F004 UTAMA sl{slm} tp{tpm} be{be}", M.tiga(uk=dict(slm=slm, tpm=tpm, be=be))


def F005_susulan(M):
    for sl, tp in itertools.product((0.2, 0.3, 0.4), (0.6, 0.8, 1.0)):
        yield f"F005 SUSULAN sl{sl} tp{tp}", M.tiga(sk=dict(sl=sl, tp=tp))


def F006_pair(M):
    """Pair dibuang satu per satu (pair lemah menarik tahun minus?)."""
    base = M.tiga()
    for p in FL.PAIRS:
        yield f"F006 tanpa {p}", [x for x in base if x["pair"] != p]


KELUARGA = [F001_monitor_pf, F002_kurva_ekuitas, F003_bobot_bot, F004_utama, F005_susulan, F006_pair]


def juara(M):
    return "JUARA (live)", M.tiga()
