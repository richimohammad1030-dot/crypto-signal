"""Evaluasi mingguan (pemilik, 11 Nov 2026): PENYEBAB tiap SL bot crypto swing live dalam N hari terakhir (padanan riset/xau/sebab_sl.py).
SL = trade live "kena SL" dengan R <= -0,9 (SL awal). Cut-loss stagnan dihitung terpisah (bukan SL).
Kategori (urutan cek):
- DATA     : trade live beda dengan replay mesin asli pada data final (koin/arah/jam fill/R) → bug data/eksekusi, WAJIB dianalisa.
             (HYPE tidak ada di replay karena datanya pendek → ditandai DATA? bukan bug.)
- NEWS     : event USD high-impact (ForexFactory minggu berjalan) dalam 3 jam sebelum candle SL, ATAU kejadian besar crypto
             (riset/crypto/kejadian.json, tambah manual) di hari SL ±1 hari → aman, bukan celah.
- LONJAKAN : candle SL bergerak >= 2,5 ATR(14) H1 koin itu (dicatat; "pasar" bila candle BTC jam itu juga >= 2,5 ATR).
- CELAH    : selain itu → WAJIB dianalisa: arah, label conviction, BTC searah/lawan, ATR relatif, umur posisi, dan pembanding
             porsi SL historis (replay 2020-skrg) untuk arah × label × BTC yang sama.
CELAH berulang: >= 2 SL kelompok sama dalam 28 hari DAN porsinya di atas historis dengan peluang binomial < 10% → buka ide baru.
Pemakaian: python riset/crypto/sebab_sl.py <repo> <data_dir> [hari=7]   (data dari riset/unduh_crypto.py)"""
import bisect, datetime as dt, glob, json, math, os, sys
import numpy as np, pandas as pd
REPO, DATA_DIR = sys.argv[1], sys.argv[2]
HARI = int(sys.argv[3]) if len(sys.argv) > 3 else 7
sys.argv = sys.argv[:3]
sys.path.insert(0, os.path.join(REPO, "riset", "crypto", "eksperimen")); sys.path.insert(0, REPO)
import tahap0_semua_tahun as t0
from signal_bot import http_json, NEWS_URL
VERSI_SEJAK = "2026-10-24T00:00+07:00"   # aturan bot terakhir berubah (v2); perbarui tiap ganti aturan
rp = t0.rp; rp.load(REPO, DATA_DIR); sb = rp.sb
wib = lambda t: (dt.datetime.fromtimestamp(t, dt.timezone.utc) + dt.timedelta(hours=7)).strftime("%a %d %b %H:%M")
now = dt.datetime.now(dt.timezone.utc).timestamp()
versi = dt.datetime.fromisoformat(VERSI_SEJAK).timestamp()

live = []
for f in sorted(glob.glob(os.path.join(REPO, "jurnal", "crypto-*.json"))):
    live += json.load(open(f))
live = [x for x in live if x["t1"] >= versi]
for x in live: x["coin"] = x["sym"].replace("USDT", "")
t0.lengkapi_hl(versi - 10 * 86400)      # funding HL (sumber bot live) sejak versi - 10 hari
rep = t0.add_costs(t0.run_replay(fund_fn=t0.funding_hl_dulu)[0])
rep = rep[rep.year >= 2020].copy()


def label_of(coin, d, t_fill, e, sl):
    tc = (int(t_fill) // 14400) * 14400 - 3600
    return sb.conviction(rp.DATA, coin, tc, d, e, sl) or "NA"


def btc_rel(t, d):
    B = rp.DATA["BTC"]; j = bisect.bisect_right(B["T"], t) - 2
    return "searah" if rp.REG["BTC"][j] * d > 0 else "lawan" if rp.REG["BTC"][j] * d < 0 else "netral"


rep["label"] = [label_of(r.coin, r.d, r.t_fill, r.e, r.sl0) for r in rep.itertuples()]
rep["btc"] = [btc_rel(r.t_fill, r.d) for r in rep.itertuples()]
rep["sl"] = (rep.R_KOTOR <= -0.9) & ~rep.why.str.contains("stagnan")
hist = rep[rep.t_exit < versi]
grp = hist.groupby(["d", "label", "btc"]).sl.agg(["mean", "count"])

# --- kesehatan: live = replay?
def cocok(x):
    m = rep[(rep.coin == x["coin"]) & (rep.d == x["d"]) & ((rep.t_fill - x["t0"]).abs() <= 3600)]
    if m.empty: return None
    return m.iloc[0]

beda = []
for x in live:
    m = cocok(x)
    if m is None or abs(m.R_KOTOR - x["R"]) > 0.05: beda.append((x, m))
rv = rep[(rep.t_exit >= versi)]
print(f"KESEHATAN sejak {wib(versi)}: live {len(live)} trade {sum(x['R'] for x in live):+.2f}R kotor · replay {len(rv)} trade "
      f"{rv.R_KOTOR.sum():+.2f}R kotor ({rv.R_REAL.sum():+.2f}R bersih) · live tanpa pasangan/beda R: {len(beda)}")
for x, m in beda:
    ket = "tidak ada di replay" + (" (HYPE: data replay kurang)" if x["coin"] == "HYPE" else "") if m is None else f"R replay {m.R_KOTOR:+.2f}"
    print(f"  - {x['coin']} {'BUY' if x['d'] == 1 else 'SELL'} tutup {wib(x['t1'])} R live {x['R']:+.2f} → {ket}")
lr = rv[~rv.apply(lambda r: any(x["coin"] == r.coin and x["d"] == r.d and abs(x["t0"] - r.t_fill) <= 3600 for x in live), axis=1)]
if len(lr):
    print("  replay tanpa pasangan live:", ", ".join(f"{r.coin} {'BUY' if r.d == 1 else 'SELL'} {wib(r.t_exit)} {r.R_KOTOR:+.2f}" for r in lr.itertuples()))

# --- news & kejadian
nt = []
try:
    nt = [(dt.datetime.fromisoformat(e["date"]).timestamp(), e.get("title", "")) for e in http_json(NEWS_URL, tries=2)
          if e.get("country") == "USD" and e.get("impact") == "High"]
except Exception as e:
    print("Kalender news gagal diambil:", e)
kj = json.load(open(os.path.join(REPO, "riset", "crypto", "kejadian.json")))["kejadian"]
kj = [(dt.datetime.fromisoformat(a).replace(tzinfo=dt.timezone.utc).timestamp() - 86400,
       dt.datetime.fromisoformat(b).replace(tzinfo=dt.timezone.utc).timestamp() + 2 * 86400, k) for a, b, k in kj]


def atr_at(coin, t):
    D = rp.DATA.get(coin)
    if not D: return None, None
    i = bisect.bisect_right(D["T"], t) - 1
    return (D["H"][i] - D["L"][i]) / D["A"][i - 1] if i > 0 and D["A"][i - 1] > 0 else None, i


batas = now - HARI * 86400
minggu = [x for x in live if x["t1"] >= batas]
sl = [x for x in minggu if x["alasan"] == "kena SL" and x["R"] <= -0.9]
stag = [x for x in minggu if "stagnan" in x["alasan"]]
print(f"\nPENYEBAB SL {HARI} hari terakhir: trade {len(minggu)} ({sum(x['R'] for x in minggu):+.2f}R) · SL {len(sl)} · cut-loss stagnan {len(stag)}")
kat_n = {}
for x in sl:
    coin, d, t1 = x["coin"], x["d"], x["t1"]
    m = cocok(x); kat, ket = None, ""
    if m is None or abs(m.R_KOTOR - x["R"]) > 0.05:
        kat = "DATA"; ket = "beda dengan replay" + (" (HYPE: tidak di replay)" if coin == "HYPE" else "")
    if kat is None:
        ada = [nm for t, nm in nt if t1 - 3 * 3600 <= t <= t1] + [k for a, b, k in kj if a <= t1 <= b]
        if ada: kat, ket = "NEWS", "; ".join(ada)
    if kat is None:
        rel, i = atr_at(coin, t1); relb, _ = atr_at("BTC", t1)
        if rel is not None and rel >= 2.5:
            kat = "LONJAKAN"; ket = f"candle SL {rel:.1f} ATR" + (f", BTC {relb:.1f} ATR (pasar)" if relb and relb >= 2.5 else "")
    if kat is None:
        kat = "CELAH"
        lab = x.get("label") or (m.label if m is not None else "NA"); b = btc_rel(x["t0"], d)
        D = rp.DATA.get(coin); i0 = bisect.bisect_right(D["T"], x["t0"]) - 2 if D else None
        arel = D["A"][i0] / np.median(D["A"][max(0, i0 - 720):i0 + 1]) if D else float("nan")
        g = grp.loc[(d, lab, b)] if (d, lab, b) in grp.index else None
        ket = (f"{'BUY' if d == 1 else 'SELL'} {lab}, BTC {b}, ATR rel {arel:.2f}, umur {(t1 - x['t0']) / 3600:.0f} jam"
               + (f" · historis kelompok ini: SL {g['mean'] * 100:.0f}% dari {int(g['count'])} trade" if g is not None else ""))
    kat_n[kat] = kat_n.get(kat, 0) + 1
    print(f"- {coin} {'BUY' if d == 1 else 'SELL'} entry {x['entry']} SL {wib(t1)} {x['R']:+.2f}R → {kat}: {ket}")
print("Ringkasan:", ", ".join(f"{k} {v}" for k, v in kat_n.items()) or "tidak ada SL")

# --- CELAH berulang 28 hari (kelompok arah × label × BTC)
b28 = [x for x in live if x["t1"] >= now - 28 * 86400]
rows = {}
for x in b28:
    k = (x["d"], x.get("label") or "NA", btc_rel(x["t0"], x["d"]))
    n, s = rows.get(k, (0, 0)); rows[k] = (n + 1, s + (x["alasan"] == "kena SL" and x["R"] <= -0.9))
print("\nKelompok 28 hari (arah, label, BTC): SL/trade live vs historis · P binomial (≥ k SL bila normal)")
for k, (n, s) in sorted(rows.items(), key=lambda z: -z[1][1]):
    p = grp.loc[k]["mean"] if k in grp.index else float("nan")
    pb = sum(math.comb(n, j) * p ** j * (1 - p) ** (n - j) for j in range(s, n + 1)) if p == p else float("nan")
    flag = "  ← CELAH BERULANG: buka ide" if s >= 2 and p == p and s / n > p and pb < 0.10 else ""
    print(f"  {'BUY' if k[0] == 1 else 'SELL'} {k[1]:<6} BTC {k[2]:<6} {s}/{n} vs {p * 100:4.0f}% · P {pb:.2f}{flag}")
print("Tindakan: NEWS = aman; LONJAKAN = catat; DATA & CELAH = analisa di laporan; CELAH berulang → ide baru di ide.md.")
