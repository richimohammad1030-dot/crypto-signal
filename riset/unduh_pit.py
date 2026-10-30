"""Unduh bahan daftar koin SESUAI MASANYA (riset/pit.py): snapshot CoinMarketCap tanggal 1 tiap bulan (200 teratas)
dan daftar semua pair USDT spot yang pernah ada di arsip Binance (termasuk yang sudah delisting). Inkremental.
Lalu cetak daftar koin tambahan (di luar daftar bot) yang perlu diunduh candle-nya.
Pemakaian: python riset/unduh_pit.py <data_dir>
Sesudahnya: python riset/unduh_crypto.py <data_dir> "$(cat <data_dir>/pit/extra.txt)"   (H1 + funding, swing)
            python riset/unduh_intraday.py <data_dir> "$(cat <data_dir>/pit/extra.txt)" (15m, intraday)"""
import json, os, re, sys, time, urllib.request
DATA = sys.argv[1]; OUT = f"{DATA}/pit"; os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
def get(u, tries=6):
    for t in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=60) as r: return r.read()
        except Exception: time.sleep(3 * (t + 1))
    raise RuntimeError(u)
now = time.gmtime()
months = [f"{y}-{m:02d}" for y in range(2019, now.tm_year + 1) for m in range(1, 13) if "2019-10" <= f"{y}-{m:02d}" <= f"{now.tm_year}-{now.tm_mon:02d}"]
p = f"{OUT}/cmc_snapshots.json"; snap = json.load(open(p)) if os.path.exists(p) else {}
for m in months:
    if m in snap: continue
    d = json.loads(get(f"https://api.coinmarketcap.com/data-api/v3/cryptocurrency/listings/historical?date={m}-01&start=1&limit=200&convertId=2781"))
    snap[m] = sorted([dict(rank=x["cmcRank"], sym=x["symbol"], slug=x["slug"], name=x["name"], tags=x.get("tags", []))
                      for x in d["data"]], key=lambda r: r["rank"])
    json.dump(snap, open(p, "w")); time.sleep(1.5)
syms, marker = set(), ""
while True:
    x = get("https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?delimiter=/&prefix=data/spot/monthly/klines/" + (f"&marker={marker}" if marker else "")).decode()
    syms |= set(re.findall(r"<Prefix>data/spot/monthly/klines/([A-Z0-9]+)/</Prefix>", x))
    if "<IsTruncated>true</IsTruncated>" not in x: break
    marker = re.findall(r"<NextMarker>(.*?)</NextMarker>", x)[0]
json.dump(sorted(s[:-4] for s in syms if s.endswith("USDT")), open(f"{OUT}/binance_spot_usdt.json", "w"))
import pit
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import signal_bot as sb
cand = sorted({c for m in snap for c in pit.ranked(DATA, m)[:70]} - set(sb.COINS))
open(f"{OUT}/extra.txt", "w").write(" ".join(cand))
print(f"snapshot {len(snap)} bulan · pair USDT {len(syms)} · koin tambahan {len(cand)} -> {OUT}/extra.txt")
