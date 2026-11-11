"""VONIS APA ADANYA juara intraday v3 di data yang BELUM PERNAH dipakai merancang: Mar 2018 - Feb 2020 (pemilik 11 Nov 2026,
pola Langkah 1 PEMBAGIAN DATA XAU). Parameter juara TIDAK diubah; mesin = tahap0_semua_tahun_2026-11-06.py (replay penuh).
Data: eksperimen/unduh_2018.py (Binance spot 2017-08+, snapshot CMC 2018-01+). Pemanasan indikator: sinyal mulai 1 Mar 2018.
Keterbatasan: funding futures Binance baru ada Sep 2019 → sebelum itu biaya funding 0 & B-short tidak aktif (syarat funding > 0).
Setelah skrip ini dijalankan sekali (11 Nov 2026), periode 2018-2019 hanya boleh dipakai sebagai KONFIRMASI ide yang sudah lolos.
Pemakaian: python riset/intraday/eksperimen/vonis_2018_2026-11-11.py <repo> <data18> <out_dir>"""
import calendar, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
import importlib.util
spec = importlib.util.spec_from_file_location("t0", os.path.join(HERE, "tahap0_semua_tahun_2026-11-06.py"))
M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)
START, AKHIR = calendar.timegm((2018, 3, 1, 0, 0, 0)), calendar.timegm((2020, 3, 1, 0, 0, 0))
OUT = sys.argv[3]; os.makedirs(OUT, exist_ok=True)
f = open(f"{OUT}/vonis_2018.txt", "w")
class Tee:
    def write(self, s): f.write(s); sys.stdout.write(s)
    def flush(self): f.flush(); sys.stdout.flush()
tee = Tee()
for nama, pm, st in (("PIT 2018-Feb 2020 biaya juara", True, False), ("TETAP (koin bot) 2018-Feb 2020", False, False),
                     ("PIT 2018-Feb 2020 STRES eksekusi", True, True)):
    s, t = M.jalankan(pm, st, {"START": START})
    s = [o for o in s if o["t"] < AKHIR]; t = [o for o in t if o["t"] < AKHIR]
    print(f"\nkoin terpakai: {len({o['c'] for o in t})} · trade {len(t)}", file=tee)
    if t: M.laporan(nama, s, t, tee)
