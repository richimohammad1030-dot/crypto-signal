"""Unduh candle H1 (harga BID) forex major untuk riset bot FX MAJOR.
Sumber Dukascopy file H1 bulanan (M1 harian terlalu lambat: ~50 menit/pair-tahun, 20 Nov 2026); bulan berjalan dari M1 harian.
Keluaran: forex_major/data/<PAIR>_h1_<tahun>.json.gz  isi [[open_s, o, h, l, c], ...] (UTC).
Tahun yang sudah lengkap tidak diunduh ulang; tahun berjalan selalu diperbarui.
Pemakaian: python forex_major/unduh_data.py [tahun_mulai] [PAIR ...]"""
import datetime as dt, gzip, json, lzma, os, struct, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.abspath(__file__)); OUT = f"{ROOT}/data"; os.makedirs(OUT, exist_ok=True)
Y0 = int(sys.argv[1]) if len(sys.argv) > 1 else 2015
PAIRS = sys.argv[2:] or ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]
NOW = dt.datetime.now(dt.timezone.utc)

def get(u, tries=8):
    for t in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404: return b""
            time.sleep(4 * (t + 1))
        except Exception:
            time.sleep(4 * (t + 1))
    return None

def parse(raw, base, div, sec):
    bars = {}
    for i in range(len(raw) // 24):
        t, o, c, l, h, v = struct.unpack(">5if", raw[i * 24:(i + 1) * 24])
        if v <= 0 and o == c == l == h: continue          # candle tanpa transaksi (akhir pekan)
        k = (base + t) // sec * sec
        if k not in bars: bars[k] = [k, o / div, h / div, l / div, c / div]
        else: x = bars[k]; x[2] = max(x[2], h / div); x[3] = min(x[3], l / div); x[4] = c / div
    return [bars[k] for k in sorted(bars)]

def month(pair, y, m):
    div = 1000 if pair.endswith("JPY") else 100000
    if (y, m) != (NOW.year, NOW.month):
        b = get(f"https://datafeed.dukascopy.com/datafeed/{pair}/{y}/{m - 1:02d}/BID_candles_hour_1.bi5")
        if b is None: return None
        return parse(lzma.decompress(b), int(dt.datetime(y, m, 1, tzinfo=dt.timezone.utc).timestamp()), div, 3600) if b else []
    rows = []; d = dt.date(y, m, 1)
    while d <= NOW.date():
        b = get(f"https://datafeed.dukascopy.com/datafeed/{pair}/{y}/{m - 1:02d}/{d.day:02d}/BID_candles_min_1.bi5")
        if b: rows += parse(lzma.decompress(b), int(dt.datetime(y, m, d.day, tzinfo=dt.timezone.utc).timestamp()), div, 3600)
        d += dt.timedelta(days=1)
    return rows

def year(pair, y):
    p = f"{OUT}/{pair}_h1_{y}.json.gz"
    if os.path.exists(p) and y < NOW.year: return f"{pair} {y}: sudah ada"
    ms = [m for m in range(1, 13) if (y, m) <= (NOW.year, NOW.month)]
    with ThreadPoolExecutor(12) as ex: res = list(ex.map(lambda m: month(pair, y, m), ms))
    gagal = sum(r is None for r in res); rows = [b for r in res if r for b in r]
    if not rows: return f"{pair} {y}: KOSONG"
    nd = 3 if pair.endswith("JPY") else 5
    rows = [[r[0]] + [round(v, nd) for v in r[1:]] for r in rows]
    with gzip.open(p, "wt") as f: json.dump(rows, f, separators=(",", ":"))
    return f"{pair} {y}: {len(rows)} bar (gagal {gagal} bulan)"

for pair in PAIRS:
    for y in range(Y0, NOW.year + 1):
        print(year(pair, y), flush=True)
print("selesai")
