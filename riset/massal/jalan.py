"""Jalankan saringan massal satu bot: python riset/massal/jalan.py <bot> <data_dir> [menit_maks] [--semua]
Keluarga yang sudah diuji < 7 hari dilewati (kecuali --semua); juara & penantang lama selalu dinilai ulang di data terbaru.
Keluaran: riset/<bot>/massal/{hasil-TGL.md, terbaru.md, penantang.json, sudah.json} + /tmp/saringan_<bot>.txt (ringkasan Telegram)."""
import datetime as dt, importlib, importlib.util, json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import inti

bot, data_dir = sys.argv[1], sys.argv[2]
menit = float(sys.argv[3]) if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else 90
semua = "--semua" in sys.argv
B = importlib.import_module(bot)
# Keluarga usulan sesi riset (pemilik, 26 Nov 2026): sesi bot hanya boleh menulis riset/<bot>/, jadi bank ini otomatis
# memuat riset/<bot>/massal/keluarga_usulan.py — setiap fungsi bernama <KODE><3 digit>_... = satu keluarga baru.
import re as _re
_p = os.path.join(REPO, "riset", bot, "massal", "keluarga_usulan.py")
if os.path.exists(_p):
    try:
        _spec = importlib.util.spec_from_file_location(f"usulan_{bot}", _p); _u = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_u)
        _ada = {k.__name__ for k in B.KELUARGA}
        B.KELUARGA = list(B.KELUARGA) + [f for n, f in sorted(vars(_u).items()) if callable(f) and _re.match(r"^[A-Z]+\d{3}_", n) and n not in _ada]
        print("keluarga usulan:", [f.__name__ for f in B.KELUARGA if f.__name__ not in _ada])
    except Exception as e:
        print("⚠️ keluarga_usulan gagal dimuat:", e)
folder = os.path.join(REPO, "riset", bot, "massal"); os.makedirs(folder, exist_ok=True)
p_sudah = os.path.join(folder, "sudah.json")
sudah = json.load(open(p_sudah)) if os.path.exists(p_sudah) else {}
hari_ini = dt.datetime.now(inti.WIB).date()
t_mulai = time.time()

M = B.Mesin(*B.muat(data_dir))
(a_is, b_is), (a_o, b_o) = B.PERIODE
STRES = getattr(B, "STRES", 0.03)
def nilai3(tr):
    tr_s = [dict(x, r=x["r"] - STRES) for x in tr]
    st = inti.nilai(tr_s, B.RISIKO, a_o, b_o, B.MINGGU_MIN), inti.nilai(tr_s, B.RISIKO, a_is, None, B.MINGGU_MIN)
    hasil = (inti.nilai(tr, B.RISIKO, a_is, b_is, B.MINGGU_MIN), inti.nilai(tr, B.RISIKO, a_o, b_o, B.MINGGU_MIN),
            inti.nilai(tr, B.RISIKO, a_is, None, B.MINGGU_MIN))
    if hasil[1] is not None and st[0] is not None: hasil[1]["stres"] = dict(pf=st[0]["pf"], minus=st[0]["minus"], rthn=st[0]["rthn"])
    if hasil[2] is not None and st[1] is not None: hasil[2]["stres"] = dict(pf=st[1]["pf"], minus=st[1]["minus"], persen=st[1]["persen"])
    return hasil
nj, tj = B.juara(M); juara = (nj, *nilai3(tj))
hasil, habis = [], False
for kel in B.KELUARGA:
    kid = kel.__name__
    if not semua and kid in sudah and (hari_ini - dt.date.fromisoformat(sudah[kid])).days < 7:
        continue
    n0 = len(hasil)
    for nama, tr in kel(M):
        hasil.append((nama, *nilai3(tr)))
        if time.time() - t_mulai > menit * 60: habis = True; break
    if habis:
        print(f"Waktu habis di {kid} ({len(hasil) - n0} varian); sisanya malam berikutnya"); break
    sudah[kid] = hari_ini.isoformat(); print(f"{kid}: {len(hasil) - n0} varian")
json.dump(sudah, open(p_sudah, "w"), indent=1)
ring, pen = inti.tulis(bot, folder, hasil, juara, B.PERIODE,
                       f"Durasi {(time.time() - t_mulai) / 60:.1f} mnt. Keluarga baru/kedaluwarsa saja (lihat sudah.json).")
open(f"/tmp/saringan_{bot}.txt", "w").write(ring)
print(ring)
