"""Lengkapi funding Hyperliquid yang kosong setelah riset/unduh_crypto.py (unduhan HL bisa gagal diam-diam,
mis. kena batas permintaan, lalu tersimpan sebagai list kosong). Mencoba ulang dengan jeda.
Argumen: <data_dir>. Koin yang memang tidak ada di Hyperliquid (respons null) dicatat, bukan dianggap gagal."""
import json, os, sys, time, urllib.request
DATA = sys.argv[1]
HL_NAME = {"SHIB": "kSHIB", "PEPE": "kPEPE"}

def fetch(coin, start_s):
    out, start = [], start_s * 1000
    for _ in range(40):
        body = json.dumps({"type": "fundingHistory", "coin": HL_NAME.get(coin, coin), "startTime": start}).encode()
        for k in range(6):
            try:
                req = urllib.request.Request("https://api.hyperliquid.xyz/info", data=body, headers={"Content-Type": "application/json"})
                d = json.load(urllib.request.urlopen(req, timeout=60)); break
            except Exception as e:
                err = e; time.sleep(5 * (k + 1))
        else:
            raise RuntimeError(f"{coin}: {err}")
        if d is None:
            return None
        if not d:
            break
        out += [[x["time"] // 1000, float(x["fundingRate"])] for x in d]
        if len(d) < 500:
            break
        start = d[-1]["time"] + 1
    return out

for fn in sorted(os.listdir(f"{DATA}/klines")):
    c = fn[:-5]
    p = f"{DATA}/funding_hl/{c}.json"
    if os.path.exists(p) and json.load(open(p)):
        continue
    fu = json.load(open(f"{DATA}/funding/{c}.json")) if os.path.exists(f"{DATA}/funding/{c}.json") else []
    start = (fu[-1][0] if fu else int(time.time()) - 60 * 86400) - 3 * 86400
    try:
        hl = fetch(c, start)
    except Exception as e:
        print("GAGAL", e); continue
    if hl is None:
        print(f"{c:7s} tidak ada di Hyperliquid (bot live juga tidak bisa SELL koin ini)"); continue
    json.dump(hl, open(p, "w")); print(f"{c:7s} funding HL dilengkapi: {len(hl)} titik")
