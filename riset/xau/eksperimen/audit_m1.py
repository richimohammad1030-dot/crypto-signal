"""Audit XAU: pastikan sisi yang terisi lebih dulu pada candle H1 ambigu (menyentuh high DAN low range) memakai
candle M1 Dukascopy (BID). Unduh hanya hari yang ambigu (cache /tmp/data/m1/). Hasil: /tmp/data/ambigu_sisi.json
{t_candle: 1 (BUY duluan) | -1 (SELL duluan) | 0 (tetap ambigu dalam 1 menit)}.
Pemakaian: python audit_m1.py <xau_sambung.json> [mulai YYYY-MM-DD]"""
import sys, os, json, lzma, struct, time, urllib.request, urllib.error, datetime as dt
import numpy as np
import audit_mesin as m

CACHE = "/tmp/data/m1"; os.makedirs(CACHE, exist_ok=True)


def get(u):
    for t in range(10):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404: return b""
            time.sleep(5 * (t + 1))
        except Exception:
            time.sleep(5 * (t + 1))
    return None


def m1_hari(day):
    p = f"{CACHE}/{day:%Y-%m-%d}.json"
    if os.path.exists(p): return json.load(open(p))
    b = get(f"https://datafeed.dukascopy.com/datafeed/XAUUSD/{day.year}/{day.month - 1:02d}/{day.day:02d}/BID_candles_min_1.bi5")
    if b is None: raise RuntimeError(f"gagal {day}")
    rows = []
    if b:
        raw = lzma.decompress(b); d0 = dt.datetime(day.year, day.month, day.day, tzinfo=dt.timezone.utc).timestamp()
        for i in range(len(raw) // 24):
            t, o, c, l, h, v = struct.unpack(">5if", raw[i * 24:(i + 1) * 24])
            rows.append([int(d0 + t), o / 1000, h / 1000, l / 1000, c / 1000])
    json.dump(rows, open(p, "w")); time.sleep(0.5)
    return rows


D = m.muat(sys.argv[1]); T, O, H, L, C = D
tr = m.replay(D)
out = {}
amb = [x for x in tr if H[x["i0"]] >= H[x["ip"] - 2:x["ip"] + 1].max() and L[x["i0"]] <= L[x["ip"] - 2:x["ip"] + 1].min()]
amb = sorted(amb, key=lambda x: -x["t0"])          # terbaru dulu (Setra, lalu periode uji)
batas = m.ts(sys.argv[2]) if len(sys.argv) > 2 else 0  # opsional: hanya hari sejak tanggal ini
amb = [x for x in amb if x["t0"] >= batas]
for k, x in enumerate(amb):
    i, ip = x["i0"], x["ip"]; hi, lo = H[ip - 2:ip + 1].max(), L[ip - 2:ip + 1].min()
    day = dt.datetime.fromtimestamp(int(T[i]), dt.timezone.utc).date()
    rows = [r for r in m1_hari(day) if T[i] <= r[0] < T[i] + 3600]
    side = 0
    for r in rows:
        up, dn = r[2] >= hi, r[3] <= lo
        if up and dn: side = 0; break
        if up: side = 1; break
        if dn: side = -1; break
    out[int(T[i])] = side
    if k % 10 == 0:
        print(k, len(amb), day, flush=True); json.dump(out, open("/tmp/data/ambigu_sisi.json", "w"))
json.dump(out, open("/tmp/data/ambigu_sisi.json", "w"))
v = list(out.values()); print("BUY duluan", v.count(1), "SELL duluan", v.count(-1), "tetap ambigu", v.count(0))
