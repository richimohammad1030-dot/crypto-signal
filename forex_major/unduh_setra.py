"""Unduh candle forex major dari Setra (sumber yang sama dengan bot XAU), semua riwayat yang tersedia.
Riwayat Setra pendek (cek 20 Nov 2026): H1 sejak ~Jan-Mar 2025, M15 ~6 bulan, M5 ~2 bulan.
Keluaran: forex_major/data_setra/<PAIR>_<tf>.json.gz  isi [[open_s, o, h, l, c], ...] (UTC).
Pemakaian: python forex_major/unduh_setra.py [tf ...]   (default 1h 15m)"""
import gzip, json, os, sys, time, urllib.request
ROOT = os.path.dirname(os.path.abspath(__file__)); OUT = f"{ROOT}/data_setra"; os.makedirs(OUT, exist_ok=True)
PAIRS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]; TFS = sys.argv[1:] or ["1h", "15m"]
STEP = {"5m": 300, "15m": 900, "1h": 3600}

def get(u):
    for t in range(5):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=60)).get("data", [])
        except Exception: time.sleep(3 * (t + 1))
    return None

for tf in TFS:
    for pair in PAIRS:
        sym = f"{pair[:3]}%2F{pair[3:]}"; rows = {}; start = 946684800000
        while True:
            d = get(f"https://setra.id/api/md/candles?symbol={sym}&tf={tf}&limit=1000&start={start}")
            if not d: break
            for c in d: rows[c["t"] // 1000] = [c["t"] // 1000, c["o"], c["h"], c["l"], c["c"]]
            nxt = d[-1]["t"] + STEP[tf] * 1000
            if nxt <= start or len(d) < 2: break
            start = nxt; time.sleep(0.2)
        r = [rows[k] for k in sorted(rows)]
        with gzip.open(f"{OUT}/{pair}_{tf}.json.gz", "wt") as f: json.dump(r, f, separators=(",", ":"))
        print(tf, pair, len(r), "bar", time.strftime("%Y-%m-%d", time.gmtime(r[0][0])) if r else "-", "s/d",
              time.strftime("%Y-%m-%d", time.gmtime(r[-1][0])) if r else "-", flush=True)
