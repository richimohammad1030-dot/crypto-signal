"""Unduh M5 BID Dukascopy (dari file M1 harian) untuk SATU pair & SATU tahun -> forex_major/data_m5/<PAIR>_m5_<tahun>.json.gz.
Lambat (Dukascopy membatasi), jadi dijalankan di latar belakang lewat workflow fx-data-m5.yml (job paralel per pair-tahun).
Pemakaian: python forex_major/unduh_m5.py <PAIR> <tahun>"""
import datetime as dt, gzip, json, lzma, os, struct, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
ROOT = os.path.dirname(os.path.abspath(__file__)); OUT = f"{ROOT}/data_m5"; os.makedirs(OUT, exist_ok=True)
PAIR, Y = sys.argv[1], int(sys.argv[2]); NOW = dt.datetime.now(dt.timezone.utc)
DIV = 1000 if PAIR.endswith("JPY") else 100000

def get(u):
    for t in range(8):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=45) as r: return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404: return b""
            time.sleep(3 * (t + 1))
        except Exception: time.sleep(3 * (t + 1))
    return None

def day(d):
    b = get(f"https://datafeed.dukascopy.com/datafeed/{PAIR}/{d.year}/{d.month - 1:02d}/{d.day:02d}/BID_candles_min_1.bi5")
    if not b: return [] if b == b"" else None
    raw = lzma.decompress(b); d0 = int(dt.datetime(d.year, d.month, d.day, tzinfo=dt.timezone.utc).timestamp()); bars = {}
    for i in range(len(raw) // 24):
        t, o, c, l, h, v = struct.unpack(">5if", raw[i * 24:(i + 1) * 24])
        if v <= 0 and o == c == l == h: continue
        k = (d0 + t) // 300 * 300
        if k not in bars: bars[k] = [k, o / DIV, h / DIV, l / DIV, c / DIV]
        else: x = bars[k]; x[2] = max(x[2], h / DIV); x[3] = min(x[3], l / DIV); x[4] = c / DIV
    return [bars[k] for k in sorted(bars)]

days = []; d = dt.date(Y, 1, 1)
while d.year == Y and d <= NOW.date():
    if d.weekday() != 5: days.append(d)
    d += dt.timedelta(days=1)
with ThreadPoolExecutor(16) as ex: res = list(ex.map(day, days))
rows = [b for r in res if r for b in r]; nd = 3 if PAIR.endswith("JPY") else 5
rows = [[r[0]] + [round(v, nd) for v in r[1:]] for r in rows]
with gzip.open(f"{OUT}/{PAIR}_m5_{Y}.json.gz", "wt") as f: json.dump(rows, f, separators=(",", ":"))
print(PAIR, Y, len(rows), "bar, gagal", sum(r is None for r in res), "hari")
