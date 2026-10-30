"""Unduh candle H1 XAU/USD dari Dukascopy (harga BID) sejak 2015 untuk riset jangka panjang. Inkremental per bulan.
Bot live tetap memakai Setra (riset/unduh_xau.py). Dukascopy vs Setra (Mar 2025): selisih close per jam ±0,22 USD
(bid vs mid), rentang candle hampir identik. Candle akhir pekan yang datar (o=h=l=c) dibuang.
Bibit data sampai bulan sebelumnya disimpan di riset/data/xau_dukascopy_h1.json.gz (hanya sisa bulan yang diunduh).
Pemakaian: python unduh_xau_panjang.py <data_dir> [tahun_mulai]  -> <data_dir>/xau_panjang.json ([[open_s, o, h, l, c], ...])"""
import datetime as dt, json, lzma, os, struct, sys, time, urllib.request

DATA = sys.argv[1]; Y0 = int(sys.argv[2]) if len(sys.argv) > 2 else 2015
CACHE = f"{DATA}/dukascopy"; os.makedirs(CACHE, exist_ok=True)

def get(u):
    for t in range(8):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=60) as r: return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404: return b""
            time.sleep(5 * (t + 1))          # 429 = dibatasi, tunggu lalu ulang
        except Exception:
            time.sleep(5 * (t + 1))
    return None

def month(y, m):
    """Candle H1 satu bulan (m = 1..12)."""
    p = f"{CACHE}/{y}-{m:02d}.json"
    now = dt.datetime.now(dt.timezone.utc)
    current = (y, m) == (now.year, now.month)
    if os.path.exists(p) and not current: return json.load(open(p))
    base = dt.datetime(y, m, 1, tzinfo=dt.timezone.utc).timestamp()
    rows = []
    if current:                          # bulan berjalan belum punya file bulanan: pakai file harian
        d = dt.date(y, m, 1)
        while d <= now.date():
            b = get(f"https://datafeed.dukascopy.com/datafeed/XAUUSD/{y}/{m - 1:02d}/{d.day:02d}/BID_candles_min_1.bi5")
            if b:
                raw = lzma.decompress(b); day0 = dt.datetime(y, m, d.day, tzinfo=dt.timezone.utc).timestamp(); hrs = {}
                for i in range(len(raw) // 24):
                    t, o, c, l, h, v = struct.unpack(">5if", raw[i * 24:(i + 1) * 24])
                    k = int(day0 + t) // 3600 * 3600
                    if k not in hrs: hrs[k] = [k, o / 1000, h / 1000, l / 1000, c / 1000]
                    else: x = hrs[k]; x[2] = max(x[2], h / 1000); x[3] = min(x[3], l / 1000); x[4] = c / 1000
                rows += [hrs[k] for k in sorted(hrs)]
            d += dt.timedelta(days=1); time.sleep(0.3)
    else:
        b = get(f"https://datafeed.dukascopy.com/datafeed/XAUUSD/{y}/{m - 1:02d}/BID_candles_hour_1.bi5")
        if b is None: raise RuntimeError(f"gagal {y}-{m}")
        if b:
            raw = lzma.decompress(b)
            for i in range(len(raw) // 24):
                t, o, c, l, h, v = struct.unpack(">5if", raw[i * 24:(i + 1) * 24])
                rows.append([int(base + t), o / 1000, h / 1000, l / 1000, c / 1000])
        if not current: json.dump(rows, open(p, "w"))
    return rows

now = dt.datetime.now(dt.timezone.utc); out = []
# bibit dari repo (riset/data/xau_dukascopy_h1.json.gz): bulan yang sudah ada tidak diunduh ulang
SEED = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "xau_dukascopy_h1.json.gz")
if os.path.exists(SEED):
    import gzip
    seed = json.load(gzip.open(SEED, "rt")); bym = {}
    for r in seed: bym.setdefault(time.strftime("%Y-%m", time.gmtime(r[0])), []).append(r)
    cur = f"{now.year}-{now.month:02d}"; last_full = max(bym) if bym else ""
    for m, rs in bym.items():
        if m < last_full and m != cur and not os.path.exists(f"{CACHE}/{m}.json"): json.dump(rs, open(f"{CACHE}/{m}.json", "w"))
for y in range(Y0, now.year + 1):
    for m in range(1, 13):
        if (y, m) > (now.year, now.month): break
        out += month(y, m); time.sleep(0.5)
out = [r for r in out if not (r[1] == r[2] == r[3] == r[4]) and r[0] + 3600 <= time.time()]
out = sorted({r[0]: r for r in out}.values())
json.dump(out, open(f"{DATA}/xau_panjang.json", "w"))
print("XAU Dukascopy candle:", len(out), "mulai", time.strftime("%Y-%m-%d", time.gmtime(out[0][0])), "s.d.", time.strftime("%Y-%m-%d %H:%M", time.gmtime(out[-1][0])))
