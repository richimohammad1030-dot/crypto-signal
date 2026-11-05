"""Unduh open interest (OI) futures USDT-M Binance dari arsip harian `metrics` data.binance.vision (data 5 menit, mulai ±Sep 2020).
Disimpan per jam (nilai terakhir tiap jam, dalam koin) ke <data>/oi/<COIN>.json: [[t_s_awal_jam, oi], ...].
Inkremental: hari yang sudah ada dilewati. Hari tanpa arsip (koin belum listing / 404) dicatat agar tidak diulang.
Pemakaian: python unduh_oi.py <data_dir> "<BTC ETH ...>" [mulai=2020-09-01]"""
import csv, datetime as dt, io, json, os, sys, time, zipfile, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

DATA = sys.argv[1]
COINS = sys.argv[2].split()
START = dt.date.fromisoformat(sys.argv[3]) if len(sys.argv) > 3 else dt.date(2020, 9, 1)
FUT = {"SHIB": "1000SHIBUSDT", "PEPE": "1000PEPEUSDT"}
END = dt.datetime.utcnow().date() - dt.timedelta(days=2)       # arsip harian biasanya tersedia H+1
os.makedirs(f"{DATA}/oi", exist_ok=True)


def get(url, tries=4):
    for t in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return b""
            time.sleep(2 * (t + 1))
        except Exception:
            time.sleep(2 * (t + 1))
    return None          # gagal jaringan (berbeda dari 404)


def day(sym, d):
    b = get(f"https://data.binance.vision/data/futures/um/daily/metrics/{sym}/{sym}-metrics-{d}.zip")
    if b is None:
        return d, None
    if not b:
        return d, []
    z = zipfile.ZipFile(io.BytesIO(b)); hrs = {}
    for r in csv.reader(io.TextIOWrapper(z.open(z.namelist()[0]))):
        if not r or not r[0][:1].isdigit():
            continue
        try:
            t = int(dt.datetime.strptime(r[0], "%Y-%m-%d %H:%M:%S").replace(tzinfo=dt.timezone.utc).timestamp())
            oi = float(r[2])
        except Exception:
            continue
        hrs[t // 3600 * 3600] = oi              # nilai terakhir dalam jam itu
    return d, sorted(hrs.items())


def first_day(sym):
    """Cari hari pertama yang punya arsip (pencarian biner bulanan lalu linear), agar koin baru tidak memicu ribuan 404."""
    d = START
    while d <= END:
        _, rows = day(sym, d.isoformat())
        if rows:
            return d
        d = (d.replace(day=1) + dt.timedelta(days=32)).replace(day=1)
    return None


for coin in COINS:
    sym = FUT.get(coin, coin + "USDT")
    p, pm = f"{DATA}/oi/{coin}.json", f"{DATA}/oi/{coin}.meta.json"
    rows = {t: v for t, v in json.load(open(p))} if os.path.exists(p) else {}
    meta = json.load(open(pm)) if os.path.exists(pm) else {"done": []}
    done = set(meta["done"])
    if "none" in done:
        print(f"{coin:7s} tidak ada arsip metrics"); continue
    if not done:
        f = first_day(sym)
        if f is None:
            print(f"{coin:7s} tidak ada arsip metrics"); json.dump({"done": ["none"]}, open(pm, "w")); continue
        # bulan sebelum hari pertama yang ditemukan: cek mundur sampai awal bulan sebelumnya
        f = max(START, (f.replace(day=1) - dt.timedelta(days=1)).replace(day=1))
    else:
        f = START
    days = [(f + dt.timedelta(days=k)).isoformat() for k in range((END - f).days + 1)]
    days = [d for d in days if d not in done]
    fail = 0
    with ThreadPoolExecutor(32) as ex:
        for d, r in ex.map(lambda d: day(sym, d), days):
            if r is None:
                fail += 1; continue
            rows.update(dict(r)); done.add(d)
    json.dump(sorted(rows.items()), open(p, "w"))
    json.dump({"done": sorted(done)}, open(pm, "w"))
    t0 = min(rows) if rows else None
    print(f"{coin:7s} OI jam {len(rows):6d} mulai {dt.datetime.utcfromtimestamp(t0).date() if t0 else '-'} · hari gagal {fail}", flush=True)
