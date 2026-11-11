"""Data KONFIRMASI crypto (11 Nov 2026): candle H1 spot Binance Agu 2017 - Sep 2019 (belum pernah dipakai merancang bot).
1) snapshot CMC 200 teratas tanggal 1 tiap bulan 2017-08..2019-09, digabung dengan snapshot 2019-10+ (riset/unduh_pit.py),
2) koin = 70 teratas tiap bulan (aturan riset/pit.py) yang punya pair USDT spot Binance, + daftar bot,
3) candle bulanan 2017-08..2019-09 digabung dengan candle 2019-10+ yang sudah ada; funding & funding_hl disalin.
Funding futures belum ada sebelum Sep 2019 (perlakuan di tahap0_lama.py).
Pemakaian: python unduh_lama.py <repo> <data_baru (hasil unduh_crypto + unduh_pit)> <data_lama_out>"""
import csv, io, json, os, shutil, sys, time, urllib.request, zipfile
from concurrent.futures import ThreadPoolExecutor
REPO, NEW, OUT = sys.argv[1:4]
sys.path.insert(0, os.path.join(REPO, "riset")); sys.path.insert(0, REPO)
MONTHS = [f"{y}-{m:02d}" for y in (2017, 2018, 2019) for m in range(1, 13) if "2017-08" <= f"{y}-{m:02d}" <= "2019-09"]


def get(url, tries=5, js=None):
    for t in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404: return None
            time.sleep(2 * (t + 1))
        except Exception:
            time.sleep(2 * (t + 1))
    return None


os.makedirs(f"{OUT}/pit", exist_ok=True); os.makedirs(f"{OUT}/klines", exist_ok=True)
for d in ("funding", "funding_hl"):
    if not os.path.exists(f"{OUT}/{d}"): shutil.copytree(f"{NEW}/{d}", f"{OUT}/{d}")
shutil.copy(f"{NEW}/pit/binance_spot_usdt.json", f"{OUT}/pit/binance_spot_usdt.json")
snap = json.load(open(f"{NEW}/pit/cmc_snapshots.json"))
p = f"{OUT}/pit/cmc_snapshots.json"
if os.path.exists(p): snap.update(json.load(open(p)))
for m in MONTHS:
    if m in snap: continue
    b = get(f"https://api.coinmarketcap.com/data-api/v3/cryptocurrency/listings/historical?date={m}-01&start=1&limit=200&convertId=2781")
    d = json.loads(b)
    snap[m] = sorted([dict(rank=x["cmcRank"], sym=x["symbol"], slug=x["slug"], name=x["name"], tags=x.get("tags", []))
                      for x in d["data"]], key=lambda r: r["rank"])
    json.dump(snap, open(p, "w")); time.sleep(1.2)
json.dump(snap, open(p, "w"))
import pit, signal_bot as sb
cand = sorted({c for m in MONTHS for c in pit.ranked(OUT, m)[:70]} | set(sb.COINS))
SYM = {"BCH": ["BCHABC", "BCC", "BCH"], "VET": ["VEN", "VET"], "BSV": ["BCHSV", "BSV"]}   # ticker lama di Binance


def klines_month(sym, m):
    b = get(f"https://data.binance.vision/data/spot/monthly/klines/{sym}USDT/1h/{sym}USDT-1h-{m}.zip")
    if not b: return []
    z = zipfile.ZipFile(io.BytesIO(b)); rows = []
    for r in csv.reader(io.TextIOWrapper(z.open(z.namelist()[0]))):
        if r and r[0].isdigit():
            rows.append([int(r[0]) // 1000, float(r[1]), float(r[2]), float(r[3]), float(r[4]), int(r[6])])
    return rows


def one(c):
    rows = []
    for m in MONTHS:
        for s in SYM.get(c, [c]):
            x = klines_month(s, m)
            if x: rows += x; break
    newp = f"{NEW}/klines/{c}.json"
    cur = json.load(open(newp)) if os.path.exists(newp) else []
    t_first = cur[0][0] if cur else 1 << 62
    rows = [r for r in rows if r[0] < t_first] + cur
    if rows: json.dump(rows, open(f"{OUT}/klines/{c}.json", "w"))
    lama = sum(1 for r in rows if r[0] < 1569888000)
    return c, lama, len(rows)


with ThreadPoolExecutor(8) as ex:
    res = list(ex.map(one, cand))
ada = [(c, n) for c, n, _ in res if n > 0]
print(f"snapshot {len(snap)} bulan · kandidat {len(cand)} · punya candle sebelum Okt 2019: {len(ada)}")
print(" ".join(f"{c}:{n}" for c, n in sorted(ada, key=lambda z: -z[1])))
