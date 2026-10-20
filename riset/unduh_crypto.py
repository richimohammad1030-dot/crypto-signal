"""Unduh candle H1 spot Binance (2019-10 s.d. sekarang) dan funding rate futures Binance untuk koin bot.
Inkremental: jika file sudah ada, hanya bulan terakhir yang diunduh ulang lalu digabung.
Output: <data>/klines/<COIN>.json ([[open_s, o, h, l, c, close_ms], ...]) dan <data>/funding/<COIN>.json ([[t_s, rate], ...])
Pemakaian: python unduh_crypto.py <data_dir> "<BTC ETH ...>" """
import csv, io, json, os, sys, time, zipfile, urllib.request
from concurrent.futures import ThreadPoolExecutor

DATA = sys.argv[1]
COINS = sys.argv[2].split()
FUT = {"SHIB": "1000SHIBUSDT", "PEPE": "1000PEPEUSDT"}
_now = time.gmtime()
_last = f"{_now.tm_year}-{_now.tm_mon - 1:02d}" if _now.tm_mon > 1 else f"{_now.tm_year - 1}-12"   # bulan lengkap terakhir
MONTHS = [f"{y}-{m:02d}" for y in range(2019, _now.tm_year + 1) for m in range(1, 13) if "2019-10" <= f"{y}-{m:02d}" <= _last]
for _d in ("klines", "funding", "funding_hl"):
    os.makedirs(f"{DATA}/{_d}", exist_ok=True)

def get(url, tries=4):
    for t in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(2 * (t + 1))
        except Exception:
            time.sleep(2 * (t + 1))
    return None

def ts_s(x):
    x = int(x)
    return x // 1_000_000 if x > 10**14 else x // 1000      # data 2025+ memakai mikrodetik

def klines_month(coin, m):
    b = get(f"https://data.binance.vision/data/spot/monthly/klines/{coin}USDT/1h/{coin}USDT-1h-{m}.zip")
    if not b:
        return []
    z = zipfile.ZipFile(io.BytesIO(b)); rows = []
    for r in csv.reader(io.TextIOWrapper(z.open(z.namelist()[0]))):
        if not r or not r[0].isdigit():
            continue
        rows.append([ts_s(r[0]), float(r[1]), float(r[2]), float(r[3]), float(r[4]), ts_s(r[6]) * 1000])
    return rows

def klines_recent(coin):
    out, start = [], int(__import__("calendar").timegm((_now.tm_year, _now.tm_mon, 1, 0, 0, 0))) * 1000
    while True:
        b = get(f"https://data-api.binance.vision/api/v3/klines?symbol={coin}USDT&interval=1h&limit=1000&startTime={start}")
        d = json.loads(b) if b else []
        out += [[k[0] // 1000, float(k[1]), float(k[2]), float(k[3]), float(k[4]), k[6]] for k in d]
        if len(d) < 1000:
            return out
        start = d[-1][0] + 1

def funding_month(coin, m):
    sym = FUT.get(coin, coin + "USDT")
    b = get(f"https://data.binance.vision/data/futures/um/monthly/fundingRate/{sym}/{sym}-fundingRate-{m}.zip")
    if not b:
        return []
    z = zipfile.ZipFile(io.BytesIO(b)); rows = []
    for r in csv.reader(io.TextIOWrapper(z.open(z.namelist()[0]))):
        if not r or not r[0].isdigit():
            continue
        rows.append([ts_s(r[0]), float(r[2])])
    return rows

def _old(path):
    try:
        return json.load(open(path))
    except Exception:
        return []

HL_NAME = {"SHIB": "kSHIB", "PEPE": "kPEPE"}

def hl_funding(coin, start_s):
    """Funding per jam dari Hyperliquid sejak start_s: [[t_s, rate], ...]."""
    out, start = [], start_s * 1000
    for _ in range(40):
        body = json.dumps({"type": "fundingHistory", "coin": HL_NAME.get(coin, coin), "startTime": start}).encode()
        try:
            req = urllib.request.Request("https://api.hyperliquid.xyz/info", data=body, headers={"Content-Type": "application/json"})
            d = json.load(urllib.request.urlopen(req, timeout=60))
        except Exception:
            break
        if not d:
            break
        out += [[x["time"] // 1000, float(x["fundingRate"])] for x in d]
        if len(d) < 500:
            break
        start = d[-1]["time"] + 1
    return out

def do_coin(coin):
    kp, fp = f"{DATA}/klines/{coin}.json", f"{DATA}/funding/{coin}.json"
    old_k, old_f = _old(kp), _old(fp)
    months = MONTHS
    if old_k:   # inkremental: unduh ulang mulai bulan sebelum data terakhir
        last = time.strftime("%Y-%m", time.gmtime(old_k[-1][0] - 32 * 86400))
        months = [m for m in MONTHS if m >= last]
    with ThreadPoolExecutor(12) as ex:
        kl = old_k + sum(ex.map(lambda m: klines_month(coin, m), months), [])
        fu = old_f + sum(ex.map(lambda m: funding_month(coin, m), months), [])
    kl += klines_recent(coin)
    kl = sorted({r[0]: r for r in kl}.values())
    fu = sorted({r[0]: r for r in fu}.values())
    json.dump(kl, open(kp, "w"))
    json.dump(fu, open(fp, "w"))
    # Funding Hyperliquid (sumber bot live) untuk periode setelah arsip Binance terakhir
    hl = hl_funding(coin, (fu[-1][0] if fu else int(time.time()) - 60 * 86400) - 3 * 86400)
    json.dump(hl, open(f"{DATA}/funding_hl/{coin}.json", "w"))
    first = time.strftime("%Y-%m", time.gmtime(kl[0][0])) if kl else "-"
    print(f"{coin:<7} candle {len(kl):>6} (mulai {first}) · funding {len(fu):>5}", flush=True)

with ThreadPoolExecutor(3) as ex:
    list(ex.map(do_coin, COINS))
