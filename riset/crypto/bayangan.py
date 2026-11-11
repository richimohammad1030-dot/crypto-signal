"""BAYANGAN bot crypto swing (11 Nov 2026, padanan riset/xau/bayangan.py): putar ulang menu aturan pada data final sejak versi live
(kesehatan.LIVE_START crypto) dan bandingkan dengan catatan live (jurnal/crypto-*.json). Penilaian strategi hanya dari akumulasi
>= 4-8 minggu (swing ±7 trade/minggu). Funding = sumber bot live (Hyperliquid dulu). R bersih skenario REAL + R kotor.
Menu: BASELINE (v2 live) · tanpa cut-loss stagnan · tanpa TP 25% · v1 (tanpa keduanya) · #19 risiko SELL 0,5% · LOW risiko 1/2.
Tambah penantang yang berstatus uji-maju ke MENU. Pemakaian: python riset/crypto/bayangan.py <repo> <data_dir>"""
import glob, json, os, sys
import numpy as np, pandas as pd
REPO, DATA_DIR = sys.argv[1], sys.argv[2]
sys.argv = sys.argv[:3]
sys.path.insert(0, os.path.join(REPO, "riset", "crypto", "eksperimen")); sys.path.insert(0, REPO)
import tahap0_semua_tahun as t0, kesehatan
rp = t0.rp; rp.load(REPO, DATA_DIR); sb = rp.sb
mulai = kesehatan.LIVE_START["crypto"]
t0.lengkapi_hl(mulai - 10 * 86400)
ASLI = dict(STAG_DAYS=sb.STAG_DAYS, TP1_FRAC=sb.TP1_FRAC)


def jalan(**ubah):
    for k, v in {**ASLI, **ubah}.items(): setattr(sb, k, v)
    df = t0.add_costs(t0.run_replay(fund_fn=t0.funding_hl_dulu)[0])
    for k, v in ASLI.items(): setattr(sb, k, v)
    return df


base = jalan()
lab = lambda r: sb.conviction(rp.DATA, r.coin, (int(r.t_fill) // 14400) * 14400 - 3600, r.d, r.e, r.sl0) or "NA"
skala = lambda df, w: df.assign(R_REAL=df.R_REAL * w, R_KOTOR=df.R_KOTOR * w)
MENU = {"BASELINE (v2 live)": base,
        "Tanpa stagnan": jalan(STAG_DAYS=1e9),
        "Tanpa TP 25%": jalan(TP1_FRAC=0.0),
        "v1 (tanpa keduanya)": jalan(STAG_DAYS=1e9, TP1_FRAC=0.0),
        "#19 SELL 0,5%": skala(base, np.where(base.d == -1, 0.5, 1.0))}
b2 = base[base.t_exit >= mulai].copy()
MENU["LOW risiko 1/2"] = skala(base, np.where([lab(r) == "LOW" if r.t_exit >= mulai else False for r in base.itertuples()], 0.5, 1.0))
live = []
for f in sorted(glob.glob(os.path.join(REPO, "jurnal", "crypto-*.json"))): live += json.load(open(f))
live = [x for x in live if x["t1"] >= mulai]
wib = lambda t: pd.to_datetime(t + 7 * 3600, unit="s").strftime("%d %b %Y")
print(f"Sejak {wib(mulai)} (data s.d. {wib(base.t_exit.max())}), R per 1R risiko:")
for nm, df in MENU.items():
    d = df[df.t_exit >= mulai]
    print(f"  {nm:<20} trade {len(d):>3} · win {np.mean(d.R_KOTOR > 0) * 100 if len(d) else 0:3.0f}% · kotor {d.R_KOTOR.sum():+6.2f}R · bersih {d.R_REAL.sum():+6.2f}R")
print(f"  {'LIVE (jurnal bot)':<20} trade {len(live):>3} · win {np.mean([x['R'] > 0 for x in live]) * 100:3.0f}% · kotor {sum(x['R'] for x in live):+6.2f}R")
