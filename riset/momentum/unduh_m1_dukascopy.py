"""Unduh candle M1 XAU/USD (BID) Dukascopy satu tahun -> riset/data/m1/xau_m1_<tahun>.csv.gz
Format baris: unix_detik,open,high,low,close (harga x1000 sebagai integer, hemat ukuran).
Dipakai riset strategi Momentum Candle (M5 dirakit dari M1). Tidak dipakai bot live.
Pemakaian: python unduh_m1_dukascopy.py <tahun> <folder_keluar>"""
import datetime as dt, gzip, lzma, os, struct, sys, time, urllib.request, urllib.error

Y = int(sys.argv[1]); OUT = sys.argv[2]; os.makedirs(OUT, exist_ok=True)

def get(u):
    for t in range(8):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404: return b""
            time.sleep(5 * (t + 1))
        except Exception:
            time.sleep(5 * (t + 1))
    return None

today = dt.datetime.now(dt.timezone.utc).date()
d = dt.date(Y, 1, 1); rows = []; gagal = []
while d.year == Y and d < today:
    if d.weekday() != 5:  # Sabtu pasar tutup
        b = get(f"https://datafeed.dukascopy.com/datafeed/XAUUSD/{d.year}/{d.month - 1:02d}/{d.day:02d}/BID_candles_min_1.bi5")
        if b is None: gagal.append(str(d))
        elif b:
            raw = lzma.decompress(b); day0 = int(dt.datetime(d.year, d.month, d.day, tzinfo=dt.timezone.utc).timestamp())
            for i in range(len(raw) // 24):
                t, o, c, l, h, v = struct.unpack(">5if", raw[i * 24:(i + 1) * 24])
                if o == h == l == c and v == 0: continue
                rows.append(f"{day0 + t},{o},{h},{l},{c}")
        time.sleep(0.2)
    d += dt.timedelta(days=1)
with gzip.open(f"{OUT}/xau_m1_{Y}.csv.gz", "wt") as f: f.write("\n".join(rows))
print(Y, "candle M1:", len(rows), "hari gagal:", len(gagal), gagal[:10])
if gagal: sys.exit(1)
