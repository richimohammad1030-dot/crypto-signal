"""PORTOFOLIO 3 bot (pemilik, 20 Nov 2026; ATURAN_BERSAMA E.4): apakah tahun minus satu bot tertutup bot lain?
"Tidak ada tahun minus" dinilai juga di level gabungan, dengan risiko per trade sesuai bot live.
Masukan: CSV trade dari backtest_crypto.py (swing), backtest_intraday.py (intraday), backtest_xau.py (XAU; pakai data 2004-skrg).
Catatan R: swing = R kotor (perhitungan bot), intraday = R bersih, XAU = R kotor dikurangi biaya 0,40 USD / jarak SL
(jarak SL diturunkan dari entry, exit, R; trade dengan |R| ≤ 0,05 memakai 0,04R).
Keluaran: % per tahun kalender per bot & gabungan, jumlah tahun minus, tahun terburuk, DD gabungan (%, harian, sederhana),
korelasi bulanan antar bot. Sumbangan kandidat baru: jalankan ulang dengan CSV kandidat menggantikan/menambah bot.
Pemakaian: python riset/portofolio.py swing=<csv>:1 intraday=<csv>:1 xau=<csv>:0.5 [lain=<csv>:<risiko%> ...]"""
import collections, csv, sys, time
import numpy as np

BOT = {}
for a in sys.argv[1:]:
    nama, sisa = a.split("=", 1); path, risk = sisa.rsplit(":", 1); BOT[nama] = (path, float(risk))


def baca(path):
    out = []
    for r in csv.DictReader(open(path)):
        t1 = r.get("t1") or r.get("t_exit"); R = float(r["R"])
        if "strat" in r and "why" in r:                       # XAU (backtest_xau.py): biaya 0,40 USD / jarak SL
            gerak = abs(float(r["ex"]) - float(r["e"]))
            R -= 0.40 / (gerak / abs(R)) if abs(R) > 0.05 and gerak > 0 else 0.04
        out.append((int(float(t1)), R))
    return out


tahun = collections.defaultdict(lambda: collections.defaultdict(float))
bulan = collections.defaultdict(lambda: collections.defaultdict(float))
hari = collections.defaultdict(lambda: collections.defaultdict(float))
awal = {}
for nama, (path, risk) in BOT.items():
    tr = baca(path); awal[nama] = min(t for t, _ in tr)
    for t, R in tr:
        g = time.gmtime(t + 7 * 3600)
        tahun[g.tm_year][nama] += R * risk; bulan[(g.tm_year, g.tm_mon)][nama] += R * risk; hari[(t + 7 * 3600) // 86400][nama] += R * risk
mulai_bersama = max(awal.values())
th_b = time.gmtime(mulai_bersama + 7 * 3600).tm_year
print("Awal data:", ", ".join(f"{n} {time.strftime('%Y-%m', time.gmtime(t))}" for n, t in awal.items()),
      f"· periode bersama mulai {th_b} (tahun pertama bisa parsial)")
nama = list(BOT)
print("\n% per tahun (risiko: " + ", ".join(f"{n} {BOT[n][1]}%" for n in nama) + ")")
print("tahun " + "".join(f"{n:>10}" for n in nama) + "  GABUNGAN")
minus = collections.Counter(); terburuk = {}
for y in sorted(tahun):
    if y < th_b: continue
    v = [tahun[y].get(n, 0.0) for n in nama]; g = sum(v)
    for n, x in zip(nama + ["GABUNGAN"], v + [g]):
        minus[n] += x < 0; terburuk[n] = min(terburuk.get(n, 1e9), x)
    print(f"{y} " + "".join(f"{x:>+10.1f}" for x in v) + f"  {g:>+8.1f}")
n_th = sum(1 for y in tahun if y >= th_b)
print("tahun minus " + " · ".join(f"{n} {minus[n]}/{n_th}" for n in nama + ["GABUNGAN"]))
print("terburuk    " + " · ".join(f"{n} {terburuk[n]:+.1f}%" for n in nama + ["GABUNGAN"]))
# DD gabungan harian (penjumlahan sederhana % per hari, tanpa bunga majemuk)
d = sorted(k for k in hari if k * 86400 >= mulai_bersama)
eq = np.cumsum([sum(hari[k].values()) for k in d]); dd = float(np.max(np.maximum.accumulate(eq) - eq)) if len(eq) else 0.0
dds = {}
for n in nama:
    e = np.cumsum([hari[k].get(n, 0.0) for k in d]); dds[n] = float(np.max(np.maximum.accumulate(e) - e)) if len(e) else 0.0
print("DD (%)      " + " · ".join(f"{n} {dds[n]:.1f}" for n in nama) + f" · GABUNGAN {dd:.1f}")
# korelasi bulanan
bk = sorted(k for k in bulan if k[0] >= th_b)
M = np.array([[bulan[k].get(n, 0.0) for n in nama] for k in bk])
if len(bk) > 6:
    C = np.corrcoef(M.T)
    print("korelasi bulanan: " + " · ".join(f"{nama[i]}-{nama[j]} {C[i, j]:+.2f}" for i in range(len(nama)) for j in range(i + 1, len(nama))))
    print(f"bulan semua bot rugi: {int(np.sum(np.all(M < 0, axis=1)))}/{len(bk)}")
