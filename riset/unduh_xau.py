"""Unduh candle H1 XAU/USD dari Setra (sumber yang sama dengan bot), inkremental.
Pemakaian: python unduh_xau.py <data_dir>   -> <data_dir>/xau.json  ([[open_s, o, h, l, c], ...])"""
import json, os, sys, time, urllib.request, datetime as dt
DATA = sys.argv[1]; os.makedirs(DATA, exist_ok=True)
path = f"{DATA}/xau.json"
rows = {r[0]: r for r in (json.load(open(path)) if os.path.exists(path) else [])}
start = (max(rows) - 7 * 86400) * 1000 if rows else int(dt.datetime(2018, 1, 1, tzinfo=dt.timezone.utc).timestamp() * 1000)
while True:
    url = f"https://setra.id/api/md/candles?symbol=XAU%2FUSD&tf=1h&limit=1000&start={start}"
    d = None
    for t in range(4):
        try:
            d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60)).get("data", [])
            break
        except Exception:
            time.sleep(3 * (t + 1))
    if not d:
        break
    for c in d:
        rows[c["t"] // 1000] = [c["t"] // 1000, c["o"], c["h"], c["l"], c["c"]]
    nxt = d[-1]["t"] + 3600 * 1000
    if nxt <= start or len(d) < 2 or d[-1]["t"] / 1000 > time.time() - 7200:
        break
    start = nxt
now = time.time()
out = [rows[k] for k in sorted(rows) if k + 3600 <= now]
json.dump(out, open(path, "w"))
print("XAU candle:", len(out), "mulai", time.strftime("%Y-%m-%d", time.gmtime(out[0][0])), "s.d.", time.strftime("%Y-%m-%d %H:%M", time.gmtime(out[-1][0])))
