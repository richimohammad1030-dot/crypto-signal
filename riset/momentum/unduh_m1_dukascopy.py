"""Unduh candle M1 XAU/USD (BID) Dukascopy per bulan -> <folder>/xau_m1_YYYY-MM.csv.gz (bulan yang sudah ada dilewati).
Format baris: unix_detik,open,high,low,close (harga x1000, integer). Untuk riset Momentum Candle, tidak dipakai bot live.
Berhenti sendiri setelah BATAS_MENIT agar hasil sebagian tetap tersimpan; jalankan ulang untuk melanjutkan.
Pemakaian: python unduh_m1_dukascopy.py <tahun> <folder_keluar> [folder_data_repo]"""
import datetime as dt, gzip, lzma, os, struct, sys, time, urllib.request, urllib.error

Y = int(sys.argv[1]); OUT = sys.argv[2]; REPO = sys.argv[3] if len(sys.argv) > 3 else OUT
os.makedirs(OUT, exist_ok=True); T0 = time.time(); BATAS_MENIT = 75

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
for m in range(1, 13):
    first = dt.date(Y, m, 1)
    if first >= today.replace(day=1): break                      # hanya bulan yang sudah lengkap
    name = f"xau_m1_{Y}-{m:02d}.csv.gz"
    if os.path.exists(f"{REPO}/{name}"): continue
    if (time.time() - T0) / 60 > BATAS_MENIT: print("batas waktu, lanjut di run berikutnya"); break
    d = first; rows = []; gagal = []
    while d.month == m:
        if d.weekday() != 5:
            b = get(f"https://datafeed.dukascopy.com/datafeed/XAUUSD/{Y}/{m - 1:02d}/{d.day:02d}/BID_candles_min_1.bi5")
            if b is None: gagal.append(str(d))
            elif b:
                raw = lzma.decompress(b); day0 = int(dt.datetime(Y, m, d.day, tzinfo=dt.timezone.utc).timestamp())
                for i in range(len(raw) // 24):
                    t, o, c, l, h, v = struct.unpack(">5if", raw[i * 24:(i + 1) * 24])
                    if o == h == l == c and v == 0: continue
                    rows.append(f"{day0 + t},{o},{h},{l},{c}")
        d += dt.timedelta(days=1)
    if gagal: print(Y, m, "gagal", gagal); continue                # bulan tidak lengkap tidak disimpan
    with gzip.open(f"{OUT}/{name}", "wt") as f: f.write("\n".join(rows))
    print(name, len(rows), f"{(time.time() - T0) / 60:.1f} mnt", flush=True)
