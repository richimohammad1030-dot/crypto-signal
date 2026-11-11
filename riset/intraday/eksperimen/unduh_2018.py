"""Data KONFIRMASI intraday yang belum pernah dipakai merancang: Binance spot 2017-08 s.d. 2019-12 (semua riset intraday mulai Mar 2020).
Membuat direktori data baru <dst> = salinan <src> (data 2020+) yang DIPERPANJANG ke belakang:
  - pit/cmc_snapshots.json ditambah snapshot CMC tanggal 1 tiap bulan 2018-01 s.d. 2019-09 (200 teratas)
  - klines/<COIN>.json (H1) & k15m/<COIN>.json (15m) untuk koin 70 teratas sesuai masanya 2018-2019 + daftar bot, digabung dengan data <src>
  - funding & funding_hl = tautan ke <src> (futures Binance baru ada Sep 2019 -> sebelum itu funding tidak ada: biaya funding 0
    dan modul B-short tidak bisa aktif karena syarat funding 72 jam > 0; dicatat sebagai keterbatasan).
Tidak mengubah unduh_intraday.py / unduh_crypto.py (juara terkunci).
Pemakaian: python riset/intraday/eksperimen/unduh_2018.py <repo> <src_data> <dst_data>"""
import csv, io, json, os, sys, time, urllib.request, zipfile
from concurrent.futures import ThreadPoolExecutor
REPO, SRC, DST = sys.argv[1:4]
sys.path.insert(0, REPO); sys.path.insert(0, os.path.join(REPO, "riset"))
import pit, signal_bot as sb

def get(u, tries=4):
    for t in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=90) as r: return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404: return None
            time.sleep(2 * (t + 1))
        except Exception: time.sleep(2 * (t + 1))
for d in ("klines", "k15m", "pit"): os.makedirs(f"{DST}/{d}", exist_ok=True)
for d in ("funding", "funding_hl"):
    if not os.path.exists(f"{DST}/{d}"): os.symlink(os.path.abspath(f"{SRC}/{d}"), f"{DST}/{d}")
snap = json.load(open(f"{SRC}/pit/cmc_snapshots.json"))
months_old = [f"{y}-{m:02d}" for y in (2018, 2019) for m in range(1, 13) if f"{y}-{m:02d}" <= "2019-09"]
p18 = f"{DST}/pit/cmc_snapshots.json"; old = json.load(open(p18)) if os.path.exists(p18) else {}
for m in months_old:
    if m in old: snap[m] = old[m]; continue
    d = json.loads(get(f"https://api.coinmarketcap.com/data-api/v3/cryptocurrency/listings/historical?date={m}-01&start=1&limit=200&convertId=2781"))
    snap[m] = sorted([dict(rank=x["cmcRank"], sym=x["symbol"], slug=x["slug"], name=x["name"], tags=x.get("tags", [])) for x in d["data"]], key=lambda r: r["rank"])
    time.sleep(1.2)
json.dump(snap, open(p18, "w"))
import shutil; shutil.copy(f"{SRC}/pit/binance_spot_usdt.json", f"{DST}/pit/binance_spot_usdt.json")
pit._SNAP = None; pit._load(DST)
coins = sorted({c for m in snap if m <= "2019-12" for c in pit.ranked(DST, m)[:70]} | set(sb.COINS) | {"BTC"})
MON = [f"{y}-{m:02d}" for y in (2017, 2018, 2019) for m in range(1, 13) if "2017-08" <= f"{y}-{m:02d}" <= "2019-12"]
def ts(x): x = int(x); return x // 1_000_000 if x > 10**14 else x // 1000
def month(c, tf, m):
    b = get(f"https://data.binance.vision/data/spot/monthly/klines/{c}USDT/{tf}/{c}USDT-{tf}-{m}.zip")
    if not b: return []
    z = zipfile.ZipFile(io.BytesIO(b)); rows = []
    for r in csv.reader(io.TextIOWrapper(z.open(z.namelist()[0]))):
        if r and r[0].isdigit():
            row = [ts(r[0]), float(r[1]), float(r[2]), float(r[3]), float(r[4])]
            if tf == "1h": row.append(int(r[6]) if int(r[6]) < 10**14 else int(r[6]) // 1000)
            rows.append(row)
    return rows
def coin(c):
    out = []
    for tf, d in (("1h", "klines"), ("15m", "k15m")):
        dst = f"{DST}/{d}/{c}.json"
        if os.path.exists(dst): continue
        lama = [r for m in MON for r in month(c, tf, m)]
        try: baru = json.load(open(f"{SRC}/{d}/{c}.json"))
        except Exception: baru = []
        seen = {r[0] for r in baru}
        rows = sorted([r for r in lama if r[0] not in seen] + baru, key=lambda r: r[0])
        if rows: json.dump(rows, open(dst, "w"))
        out.append(f"{tf} {len(lama)}+{len(baru)}")
    return c, out
with ThreadPoolExecutor(8) as ex:
    for c, o in ex.map(coin, coins): print(c, *o, flush=True)
print(f"SELESAI · {len(coins)} koin · snapshot {len(snap)} bulan")
