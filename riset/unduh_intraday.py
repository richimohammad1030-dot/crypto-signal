"""Unduh candle 15 menit spot Binance (2020-01 s.d. sekarang) untuk bot intraday. Inkremental.
Output: <data>/k15m/<COIN>.json ([[open_s, o, h, l, c], ...]). Candle H1 + funding diunduh unduh_crypto.py.
Pemakaian: python unduh_intraday.py <data_dir> "<BTC ETH ...>" """
import calendar, csv, io, json, os, sys, time, urllib.request, zipfile
from concurrent.futures import ThreadPoolExecutor

DATA, COINS = sys.argv[1], sys.argv[2].split()
OUT = f"{DATA}/k15m"; os.makedirs(OUT, exist_ok=True)
_now = time.gmtime()
_last = f"{_now.tm_year}-{_now.tm_mon - 1:02d}" if _now.tm_mon > 1 else f"{_now.tm_year - 1}-12"
MONTHS = [f"{y}-{m:02d}" for y in range(2020, _now.tm_year + 1) for m in range(1, 13) if "2020-01" <= f"{y}-{m:02d}" <= _last]

def get(u, tries=4):
    for t in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=90) as r: return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404: return None
            time.sleep(2 * (t + 1))
        except Exception: time.sleep(2 * (t + 1))

def ts(x): x = int(x); return x // 1_000_000 if x > 10**14 else x // 1000

def month(c, m):
    b = get(f"https://data.binance.vision/data/spot/monthly/klines/{c}USDT/15m/{c}USDT-15m-{m}.zip")
    if not b: return []
    z = zipfile.ZipFile(io.BytesIO(b))
    return [[ts(r[0]), float(r[1]), float(r[2]), float(r[3]), float(r[4])] for r in csv.reader(io.TextIOWrapper(z.open(z.namelist()[0]))) if r and r[0].isdigit()]

def recent(c):
    out, start = [], calendar.timegm((_now.tm_year, _now.tm_mon, 1, 0, 0, 0)) * 1000
    while True:
        b = get(f"https://data-api.binance.vision/api/v3/klines?symbol={c}USDT&interval=15m&limit=1000&startTime={start}")
        d = json.loads(b) if b else []
        out += [[k[0] // 1000, float(k[1]), float(k[2]), float(k[3]), float(k[4])] for k in d if k[6] < time.time() * 1000]
        if len(d) < 1000: return out
        start = d[-1][0] + 1

def coin(c):
    p = f"{OUT}/{c}.json"
    try: old = json.load(open(p))
    except Exception: old = []
    months = MONTHS
    if old:
        last = time.strftime("%Y-%m", time.gmtime(old[-1][0] - 32 * 86400)); months = [m for m in MONTHS if m >= last]
    with ThreadPoolExecutor(6) as ex: rows = old + sum(ex.map(lambda m: month(c, m), months), [])
    rows += recent(c)
    rows = sorted({r[0]: r for r in rows}.values())
    json.dump(rows, open(p, "w"))
    print(f"{c:<7} candle 15m {len(rows):>7}", flush=True)

with ThreadPoolExecutor(3) as ex: list(ex.map(coin, COINS))
