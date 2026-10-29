"""Alat bersama eksperimen intraday: muat data sekali, hitung order per modul, replay penuh portofolio,
dan bandingkan dengan juara memakai kriteria PROSEDUR.md (langkah 3.4)."""
import collections, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "riset")); sys.path.insert(0, REPO)
import backtest_intraday as bi
import signal_bot as sb

_cache = {}
def data(data_dir):
    if "d" not in _cache: _cache["d"] = bi.load(data_dir, sb.COINS)
    return _cache["d"]

def orders_mod(data_dir, P, mod):
    """Order kandidat satu modul (A atau B) dengan parameter P."""
    H1, M15 = data(data_dir)
    Q = dict(bi.PARAM, **P); Q["A_ON"], Q["B_ON"] = (mod == "A"), (mod == "B")
    return bi.orders(H1, M15, Q)

YEARS = list(range(2020, 2027))
def ringkas(sent, taken):
    out = dict(semua=bi.stats(taken, sent), lama=bi.stats(taken, sent, b=bi.IS_END), baru=bi.stats(taken, sent, a=bi.IS_END))
    yr = collections.defaultdict(float)
    for o in taken: yr[time.gmtime(o["t"]).tm_year] += o["R"]
    out["tahun"] = {y: round(yr.get(y, 0.0), 1) for y in YEARS}
    return out

def keputusan(base, alt):
    """LOLOS-kriteria tanpa uji tetangga (tetangga dinilai di skrip pemanggil)."""
    r_l = alt["lama"]["rasio"] / base["lama"]["rasio"] - 1
    r_b = alt["baru"]["rasio"] / base["baru"]["rasio"] - 1
    th = sum(alt["tahun"][y] >= base["tahun"][y] for y in YEARS)
    t2 = alt["semua"]["tanpa_top2"] >= base["semua"]["tanpa_top2"]
    ok = r_l >= 0.10 and r_b >= 0.10 and th >= 5 and t2
    return dict(lolos=ok, d_rasio_lama=round(r_l * 100, 1), d_rasio_baru=round(r_b * 100, 1), tahun_ok=th, top2_ok=t2)

def baris(nama, s, k=None):
    L, B, S = s["lama"], s["baru"], s["semua"]
    t = f"{nama:<16} n={S['n']:>5} fill={S['fill']:>5} win={S['win']:>5} R/tr={S['avgR']:+.4f} R/thn={S['totR_thn']:>5} DD={S['maxDD']:>5} " \
        f"rasio L={L['rasio']:>5} B={B['rasio']:>5} top2={S['tanpa_top2']:>6} thn={s['tahun']}"
    if k: t += f"  -> dL={k['d_rasio_lama']:+}% dB={k['d_rasio_baru']:+}% thnOK={k['tahun_ok']}/7 top2OK={k['top2_ok']} {'LOLOS' if k['lolos'] else 'gagal'}"
    return t
