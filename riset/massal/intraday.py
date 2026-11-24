"""Saringan massal INTRADAY crypto (24 Nov 2026). Juara = riset/backtest_intraday.py PARAM (strategi #2 live), R bersih biaya.
Bank ide: keluarga I-M<nomor>; sesi riset intraday menambah keluarga baru di bawah.
Data: <data_dir>/klines + funding (unduh_crypto.py) dan k15m (unduh_intraday.py), koin bot (signal_bot.COINS)."""
import os, sys, itertools
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path[:0] = [REPO, os.path.join(REPO, "riset"), os.path.dirname(__file__)]
import backtest_intraday as BI
import signal_bot as sb
import inti

RISIKO = 1.0
MINGGU_MIN = 3.0
PERIODE = (("2020-03-01", "2024-01-01"), ("2024-01-01", None))


def muat(data_dir):
    return BI.load(data_dir, sb.COINS)


class Mesin:
    def __init__(self, H1, M15):
        self.H1, self.M15 = H1, M15; self._c = {}

    def trades(self, **ubah):
        key = tuple(sorted(ubah.items()))
        if key not in self._c:
            P = dict(BI.PARAM, **ubah)
            _, taken = BI.portfolio(BI.orders(self.H1, self.M15, P), sb.COINS, P["CAP"], P["PEND"])
            self._c[key] = sorted([dict(t0=o["t_fill"], t1=o["t_exit"], r=o["R"], w=1.0, strat=o["m"], koin=o["c"]) for o in taken],
                                  key=lambda x: x["t1"])
        return self._c[key]


def bobot(tr, w):
    return [dict(x, r=x["r"] * w.get(x["strat"], 1.0)) for x in tr if w.get(x["strat"], 1.0) > 0]


# ======================= BANK IDE =======================
def IM001_monitor_pf(M):
    base = M.trades()
    for hari, amb, w, kun, mn in itertools.product((90, 180, 365), (0.9, 1.0, 1.1), (0.0, 0.5), (None, "strat", "koin"), (20, 40)):
        yield f"IM001 monitorPF {hari}h <{amb} w{w} {kun or 'bot'} n{mn}", inti.monitor_pf(base, hari, amb, w, mn, kun)


def IM002_kurva_ekuitas(M):
    base = M.trades()
    for n, w in itertools.product((10, 20, 40, 80), (0.0, 0.5)):
        yield f"IM002 kurva-ekuitas n{n} w{w}", inti.monitor_ekuitas(base, n, w)


def IM003_bobot_modul(M):
    base = M.trades()
    for a, b in itertools.product((0.5, 0.75, 1.0, 1.25, 1.5), repeat=2):
        if (a, b) != (1.0, 1.0): yield f"IM003 bobot A{a} B{b}", bobot(base, dict(A=a, B=b))


def IM004_param(M):
    """SL/TP modul A & B dan kapasitas posisi."""
    for asl, atp in itertools.product((2.5, 3.0, 3.5), (1.5, 2.0, 2.5)):
        yield f"IM004 A sl{asl} tpR{atp}", M.trades(A_SL=asl, A_TP_R=atp)
    for bsl, btp in itertools.product((1.25, 1.5, 2.0), (0.8, 1.0, 1.2)):
        yield f"IM004 B sl{bsl} tpf{btp}", M.trades(B_SL=bsl, B_TPF=btp)
    for cap in (2, 4, 5):
        yield f"IM004 CAP{cap}", M.trades(CAP=cap, PEND=max(cap, 3))


def IM005_jeda_beruntun(M):
    """T7 kalah beruntun: berhenti setelah k kalah beruntun sampai trade bayangan menang (+ kombinasi monitor PF)."""
    base = M.trades()
    for k in (3, 4, 5, 6, 7, 8):
        yield f"IM005 jeda setelah {k} kalah", inti.jeda_beruntun(base, k)
        yield f"IM005 jeda {k} + monitorPF 365h <1.0", inti.jeda_beruntun(inti.monitor_pf(base, 365, 1.0, 0.0, 20), k)


KELUARGA = [IM001_monitor_pf, IM002_kurva_ekuitas, IM003_bobot_modul, IM004_param, IM005_jeda_beruntun]


def juara(M):
    return "JUARA (live)", M.trades()
