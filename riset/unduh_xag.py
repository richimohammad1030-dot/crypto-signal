"""Unduh candle H1 XAG/USD (perak) Dukascopy BID, Jan 2015 s.d. bulan lalu, satu file per bulan (validasi silang riset XAU,
ide #40). Pemakaian: python riset/unduh_xag.py <dir_keluaran>   (lalu riset/xau/eksperimen/uji_xag.py)"""
import datetime as dt, json, lzma, struct, sys, time, urllib.request, os
from concurrent.futures import ThreadPoolExecutor
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
def get(u):
    for t in range(8):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=60) as r: return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404: return b""
            time.sleep(5 * (t + 1))
        except Exception: time.sleep(5 * (t + 1))
    return None
def month(ym):
    y, m = ym; p = f"{OUT}/{y}-{m:02d}.json"
    if os.path.exists(p): return
    b = get(f"https://datafeed.dukascopy.com/datafeed/XAGUSD/{y}/{m - 1:02d}/BID_candles_hour_1.bi5")
    if b is None: print("gagal", ym, flush=True); return
    base = dt.datetime(y, m, 1, tzinfo=dt.timezone.utc).timestamp(); rows = []
    if b:
        raw = lzma.decompress(b)
        for i in range(len(raw) // 24):
            t, o, c, l, h, v = struct.unpack(">5if", raw[i * 24:(i + 1) * 24])
            rows.append([int(base + t), o / 1000, h / 1000, l / 1000, c / 1000])
    json.dump(rows, open(p, "w"))
ms = [(y, m) for y in range(2015, 2027) for m in range(1, 13) if (y, m) < (dt.date.today().year, dt.date.today().month)]
with ThreadPoolExecutor(4) as ex: list(ex.map(month, ms))
print("selesai", len(os.listdir(OUT)))
