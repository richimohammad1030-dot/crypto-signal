"""Evaluasi mingguan INTRADAY (pemilik, 11 Nov 2026; pola riset/xau/sebab_sl.py): PENYEBAB tiap SL bot intraday live.
Kategori (urutan cek):
  DATA     = trade live beda dengan replay data final (koin/waktu isi/modul/arah/alasan keluar) -> WAJIB dianalisa sebagai bug.
  NEWS     = event USD berdampak tinggi antara 60 menit sebelum isi s.d. SL (CPI, FOMC, NFP ...) -> aman, bukan celah.
  LONJAKAN = candle 15m saat SL bergerak >= 2,5 ATR(14) 15m tanpa news (kejadian ekstrem; ditandai "pasar" bila BTC ikut >= 2 ATR).
  CELAH    = selain itu -> WAJIB dianalisa: modul (A-long / B-long / B-short), tren BTC H1 vs arah, ATR relatif koin, jam ke SL,
             dan pembanding historis = porsi SL modul itu di kondisi sama (backtest daftar koin bot, 2020-sekarang).
CELAH berulang (>= 2 SL modul & kondisi sama dalam 28 hari, porsi > historis) -> buka ide baru di riset/intraday/ide.md.
Kalender news = ForexFactory minggu berjalan saja -> jalankan tiap Jumat untuk minggu itu (hari=7).
Pemakaian: python riset/intraday/sebab_sl.py <repo> <data_dir> [hari=7]"""
import calendar, collections, datetime as dt, json, os, sys, time
REPO, DATA = sys.argv[1:3]; HARI = int(sys.argv[3]) if len(sys.argv) > 3 else 7
sys.path.insert(0, REPO); sys.path.insert(0, os.path.join(REPO, "riset"))
import numpy as np
import backtest_intraday as bi, signal_bot as sb

VERSI_SEJAK = "2026-10-30T09:00"   # UTC; juara v3 live (30 Okt 16:00 WIB). Perbarui tiap aturan bot berubah.
v0 = calendar.timegm(time.strptime(VERSI_SEJAK, "%Y-%m-%dT%H:%M"))
wib = lambda t: (dt.datetime.fromtimestamp(t, dt.timezone.utc) + dt.timedelta(hours=7)).strftime("%a %d %b %H:%M")
grup = lambda m, d: "A-long" if m == "A" else ("B-long" if d == 1 else "B-short")

hist = json.load(open(os.path.join(REPO, "intraday_state.json"))).get("hist", [])
now = time.time(); batas = now - HARI * 86400
semua = [h for h in hist if h[4] >= batas]
sl = [h for h in semua if h[8] == "SL"]
print(f"Trade live tutup {HARI} hari terakhir: {len(semua)} · SL: {len(sl)} · total {sum(h[7] for h in semua):+.2f}R")

# ------------------------------------------------------------------ replay data final (daftar koin bot = mesin live)
P, sent, ref = bi.run(REPO, DATA)
H1, M15 = bi.load(DATA, sb.COINS)
rep = {(o["c"], o["t_fill"]): o for o in ref}
btc = bi.btc_regime_fn(H1)
def atr_rel(c, t):
    D = M15.get(c)
    if D is None: return None
    i = int(np.searchsorted(D["T"], t)) - 1
    return float(D["A"][i] / np.median(D["A"][max(0, i - 500):i + 1])) if i > 50 else None
bucket = lambda x: "n/a" if x is None else ("rendah" if x < 0.8 else "tinggi" if x >= 1.5 else "normal")
def kondisi(m, d, t_sig, c):
    tr = btc(t_sig); tren = "searah" if tr == d else ("lawan" if tr == -d else "netral")
    return grup(m, d), tren, bucket(atr_rel(c, t_sig))
# pembanding historis: porsi SL per (modul, tren BTC, ATR rel)
hist_k = collections.defaultdict(lambda: [0, 0])
for o in ref:
    if o["t"] >= v0: continue
    k = kondisi(o["m"], o["d"], o["t"], o["c"]); hist_k[k][0] += 1; hist_k[k][1] += o["why"] == "SL"
base_m = collections.defaultdict(lambda: [0, 0])
for k, (n, s) in hist_k.items(): base_m[k[0]][0] += n; base_m[k[0]][1] += s

# ------------------------------------------------------------------ cek DATA untuk SEMUA trade live sejak versi ini
live_v = [h for h in hist if h[3] >= v0 and h[4] < now - 1800]
beda = []
for h in live_v:
    r = rep.get((h[0], int(h[3])))
    if r is None or r["m"] != h[1] or r["d"] != h[2] or r["why"] != h[8] or abs(r["R"] - h[7]) > 0.02:
        beda.append((h, r))
ref_v = [o for o in ref if o["t_fill"] >= v0 and o["t_exit"] < now - 1800]
hanya_bt = [o for o in ref_v if not any(h[0] == o["c"] and int(h[3]) == o["t_fill"] for h in live_v)]
print(f"Kesetaraan sejak {VERSI_SEJAK} UTC: live {len(live_v)} trade ({sum(h[7] for h in live_v):+.2f}R) · replay {len(ref_v)} trade "
      f"({sum(o['R'] for o in ref_v):+.2f}R) · beda {len(beda)} · hanya replay {len(hanya_bt)}")
for h, r in beda[:8]:
    print(f"  BEDA {h[0]} {grup(h[1], h[2])} isi {wib(h[3])} live {h[8]} {h[7]:+.2f}R · replay {'tidak ada' if r is None else r['why'] + f' {r[chr(82)]:+.2f}R'}")
for o in hanya_bt[:8]:
    print(f"  HANYA REPLAY {o['c']} {grup(o['m'], o['d'])} isi {wib(o['t_fill'])} {o['why']} {o['R']:+.2f}R")
if not sl: sys.exit(0)

# ------------------------------------------------------------------ news
try:
    news = [e for e in sb.http_json(sb.NEWS_URL, tries=2) if e.get("country") == "USD" and e.get("impact") == "High"]
except Exception as e:
    news = []; print("Kalender news gagal diambil:", e)
nt = []
for e in news:
    try: nt.append((dt.datetime.fromisoformat(e["date"]).timestamp(), e.get("title", "")))
    except Exception: pass

kat_n = collections.Counter(); celah = []
for h in sl:
    c, m, d, tf, tx, fill, px, R, why = h[:9]
    r = rep.get((c, int(tf))); kat, ket = None, ""
    if tf >= v0 and (r is None or r["m"] != m or r["d"] != d or r["why"] != why):
        kat = "DATA"; ket = "replay: " + ("tidak ada trade" if r is None else f"{grup(r['m'], r['d'])} {r['why']} {r['R']:+.2f}R")
    if kat is None:
        ada = [(t, nm) for t, nm in nt if tf - 3600 <= t <= tx]
        if ada: kat = "NEWS"; ket = "; ".join(f"{wib(t)} {nm}" for t, nm in ada)
    D = M15.get(c); j = int(np.searchsorted(D["T"], tx - 900)) if D is not None else None
    if kat is None and D is not None and j < len(D["T"]) and (D["H"][j] - D["L"][j]) >= 2.5 * D["A"][j - 1]:
        B = M15["BTC"]; jb = int(np.searchsorted(B["T"], tx - 900))
        pasar = jb < len(B["T"]) and (B["H"][jb] - B["L"][jb]) >= 2.0 * B["A"][jb - 1]
        kat = "LONJAKAN"; ket = f"candle SL {(D['H'][j] - D['L'][j]) / D['A'][j - 1]:.1f} ATR" + (" · BTC ikut (pasar)" if pasar else " · khusus koin")
    if kat is None:
        kat = "CELAH"
        t_sig = r["t"] if r else int(tf)
        k = kondisi(m, d, t_sig, c); n_h, s_h = hist_k.get(k, (0, 0)); nb, sb_ = base_m[k[0]]
        ket = (f"{k[0]}, BTC {k[1]}, ATR rel {k[2]}, SL setelah {(tx - tf) / 3600:.1f} jam · historis kondisi sama: SL {s_h / max(n_h, 1) * 100:.0f}% "
               f"dari {n_h} (modul {sb_ / max(nb, 1) * 100:.0f}%) → " + ("NORMAL" if n_h >= 20 and s_h / n_h <= sb_ / nb * 1.25 else "PERLU DICEK"))
        celah.append((tx, k))
    kat_n[kat] += 1
    print(f"- {c} {grup(m, d)} isi {wib(tf)} @ {fill:.6g} SL {wib(tx)} {R:+.2f}R → {kat}: {ket}")
print("Ringkasan penyebab SL:", ", ".join(f"{k} {v}" for k, v in kat_n.items()))
# CELAH berulang 28 hari (memakai semua SL live 28 hari terakhir)
sl28 = [h for h in hist if h[4] >= now - 28 * 86400 and h[8] == "SL"]
cnt = collections.Counter(kondisi(h[1], h[2], int(h[3]), h[0]) for h in sl28)
ber = [(k, n) for k, n in cnt.items() if n >= 2 and hist_k.get(k, (0, 0))[0] >= 1]
if ber:
    tot28 = collections.Counter(kondisi(h[1], h[2], int(h[3]), h[0]) for h in hist if h[4] >= now - 28 * 86400)
    for k, n in ber:
        nh, sh = hist_k[k]; p_live = n / tot28[k]; p_h = sh / nh
        print(f"CELAH berulang 28 hari: {k} · {n} SL dari {tot28[k]} trade ({p_live * 100:.0f}%) vs historis {p_h * 100:.0f}% (n {nh}) → "
              + ("BUKA IDE BARU" if p_live > p_h * 1.25 else "masih dalam batas historis"))
print("Tindakan: NEWS = aman; LONJAKAN = catat; DATA & CELAH = wajib dianalisa di laporan (pola berulang -> ide baru).")
