"""Saringan massal CRYPTO SWING (24 Nov 2026). Juara = replay mesin asli signal_bot (riset/crypto/eksperimen/tahap0_semua_tahun.py),
R_REAL (biaya fee + slip + funding aktual). Replay penuh ±beberapa menit, jadi keluarga di sini kebanyakan PASCA-PROSES
atas trade juara (monitor edge, bobot arah/koin); varian mesin (gate/parameter) ditambahkan sesi riset crypto sebagai keluarga
baru yang memanggil _replay.make_engine_cls (lihat _wf.py). Data: <data_dir>/klines, funding, funding_hl (unduh_crypto.py)."""
import os, subprocess, sys, itertools
import pandas as pd
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.dirname(__file__))
import inti

RISIKO = 1.0
MINGGU_MIN = 3.0
PERIODE = (("2020-01-01", "2024-01-01"), ("2024-01-01", None))


def muat(data_dir):
    out = os.path.join(data_dir, "massal_crypto_juara.csv")
    subprocess.run([sys.executable, os.path.join(REPO, "riset", "crypto", "eksperimen", "tahap0_semua_tahun.py"), REPO, data_dir, out],
                   check=True, cwd=REPO, capture_output=True)
    return (pd.read_csv(out),)


class Mesin:
    def __init__(self, df):
        self.base = sorted([dict(t0=int(r.t_fill) // (1000 if r.t_fill > 1e11 else 1), t1=int(r.t_exit) // (1000 if r.t_exit > 1e11 else 1),
                                 r=float(r.R_REAL), w=1.0, strat="BUY" if r.d == 1 else "SELL", koin=r.coin) for r in df.itertuples()],
                           key=lambda x: x["t1"])


def bobot(tr, w):
    return [dict(x, r=x["r"] * w.get(x["strat"], 1.0)) for x in tr if w.get(x["strat"], 1.0) > 0]


# ======================= BANK IDE =======================
def CM001_monitor_pf(M):
    for hari, amb, w, kun, mn in itertools.product((180, 365, 730), (0.9, 1.0, 1.1), (0.0, 0.5), (None, "strat", "koin"), (15, 30)):
        yield f"CM001 monitorPF {hari}h <{amb} w{w} {kun or 'bot'} n{mn}", inti.monitor_pf(M.base, hari, amb, w, mn, kun)


def CM002_kurva_ekuitas(M):
    for n, w in itertools.product((10, 20, 40, 80), (0.0, 0.5)):
        yield f"CM002 kurva-ekuitas n{n} w{w}", inti.monitor_ekuitas(M.base, n, w)


def CM003_bobot_arah(M):
    for a, b in itertools.product((0.5, 0.75, 1.0, 1.25), repeat=2):
        if (a, b) != (1.0, 1.0): yield f"CM003 bobot BUY{a} SELL{b}", bobot(M.base, dict(BUY=a, SELL=b))


def CM004_jeda_beruntun(M):
    """T7 kalah beruntun: berhenti setelah k kalah beruntun sampai trade bayangan menang (+ kombinasi monitor PF)."""
    base = M.base
    for k in (3, 4, 5, 6, 7, 8):
        yield f"CM004 jeda setelah {k} kalah", inti.jeda_beruntun(base, k)
        yield f"CM004 jeda {k} + monitorPF 365h <1.0", inti.jeda_beruntun(inti.monitor_pf(base, 365, 1.0, 0.0, 20), k)


KELUARGA = [CM001_monitor_pf, CM002_kurva_ekuitas, CM003_bobot_arah, CM004_jeda_beruntun]


def juara(M):
    return "JUARA (live)", M.base
