"""Unduh M1 XAU/USD dari HistData (isi identik Dukascopy BID, dicek Feb 2020: selisih 0). Jam EST tanpa DST -> UTC.
Catatan: HistData 2023-02..07 banyak menit hilang di jam 10-23 UTC, bulan itu pakai Dukascopy.
Pemakaian: python unduh_m1_histdata.py <folder_keluar> 2020 2021 ... 2026/1 2026/2 ..."""
import re, sys, urllib.request, urllib.parse, http.cookiejar, io, zipfile, gzip, datetime as dt, os
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
cj = http.cookiejar.CookieJar(); op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
UA = {"User-Agent": "Mozilla/5.0"}
def fetch(path):
    url = f"https://www.histdata.com/download-free-forex-historical-data/?/ascii/1-minute-bar-quotes/xauusd/{path}"
    html = op.open(urllib.request.Request(url, headers=UA), timeout=60).read().decode("latin1")
    f = dict(re.findall(r'name="(tk|date|datemonth|platform|timeframe|fxpair)" id="\w+" value="([^"]*)"', html))
    req = urllib.request.Request("https://www.histdata.com/get.php", data=urllib.parse.urlencode(f).encode(),
                                 headers={**UA, "Referer": url, "Content-Type": "application/x-www-form-urlencoded"})
    z = zipfile.ZipFile(io.BytesIO(op.open(req, timeout=180).read()))
    csv = [n for n in z.namelist() if n.lower().endswith(".csv")][0]
    return z.read(csv).decode()
def convert(txt):
    # HistData: EST tanpa DST (UTC-5). Baris: 20200101 180000;o;h;l;c;v
    rows = []
    for ln in txt.splitlines():
        p = ln.split(";")
        if len(p) < 5: continue
        t = int((dt.datetime.strptime(p[0], "%Y%m%d %H%M%S") + dt.timedelta(hours=5)).replace(tzinfo=dt.timezone.utc).timestamp())
        rows.append((t, *[round(float(x) * 1000) for x in p[1:5]]))
    return rows
allr = {}
for path in sys.argv[2:]:
    rows = convert(fetch(path)); print(path, len(rows), flush=True)
    for r in rows: allr[r[0]] = r
rows = [allr[k] for k in sorted(allr)]
if True:
    bym = {}
    for r in rows: bym.setdefault(dt.datetime.fromtimestamp(r[0], dt.timezone.utc).strftime("%Y-%m"), []).append(r)
    for m, rs in bym.items():
        with gzip.open(f"{OUT}/xau_m1_{m}.csv.gz", "wt") as f: f.write("\n".join(",".join(map(str, r)) for r in rs))
    print('bulan', len(bym))
