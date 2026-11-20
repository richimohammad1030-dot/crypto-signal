"""RUTINITAS HARIAN riset (pemilik, 20 Nov 2026): dijalankan GitHub Actions (.github/workflows/riset-harian.yml) tiap hari, supaya
sesi riset Claude tidak menghabiskan waktu untuk unduh data, replay, kesehatan, penyebab SL, dan bayangan. Sesi riset cukup
MEMBACA hasilnya di riset/harian/<bot>.md lalu memakai seluruh waktunya untuk menguji ide.

Per bot (urutan; satu langkah gagal tidak menghentikan langkah lain, kegagalan ditulis di keluaran):
  xau      : unduh Setra + Dukascopy (bibit riset/data diperbarui otomatis tiap bulan penuh baru) -> replay_xau (wajib IDENTIK)
             -> sebab_sl 7 hari -> bayangan
  crypto   : unduh H1 + funding koin bot -> sebab_sl 7 hari -> bayangan
  intraday : unduh 15 menit koin bot -> sebab_sl 7 hari -> bayangan
  fx       : riset/fx/harian_fx.py (replay IDENTIK, penyebab SL 7 hari + kesehatan, bayangan)
Keluaran: riset/harian/<bot>.md (terbaru) + riset/harian/arsip/<bot>-YYYY-MM-DD.md (disimpan 21 hari),
          riset/harian/PERINGATAN.txt bila ada replay BEDA / langkah gagal (workflow mengirimnya ke Telegram pribadi pemilik).
Pemakaian: python riset/harian.py <repo> <data_dir> [xau crypto intraday]"""
import datetime as dt, glob, gzip, json, os, subprocess, sys, time

REPO, DATA = os.path.abspath(sys.argv[1]), sys.argv[2]
BOTS = sys.argv[3:] or ["xau", "crypto", "intraday"]
OUT = os.path.join(REPO, "riset", "harian"); ARSIP = os.path.join(OUT, "arsip")
os.makedirs(ARSIP, exist_ok=True); os.makedirs(DATA, exist_ok=True)
now = dt.datetime.now(dt.timezone(dt.timedelta(hours=7)))
TGL = now.strftime("%Y-%m-%d")
PY = sys.executable
peringatan = []


def jalan(judul, args, batas=1800):
    t0 = time.time()
    try:
        p = subprocess.run([PY, *args], cwd=REPO, capture_output=True, text=True, timeout=batas)
        teks, ok = (p.stdout + ("\n" + p.stderr[-3000:] if p.returncode else "")).strip(), p.returncode == 0
    except subprocess.TimeoutExpired:
        teks, ok = f"WAKTU HABIS setelah {batas} detik", False
    menit = (time.time() - t0) / 60
    return f"### {judul} {'OK' if ok else 'GAGAL'} ({menit:.1f} mnt)\n```\n{teks[-12000:]}\n```\n", ok


def coins():
    sys.path.insert(0, REPO)
    import signal_bot as s
    return " ".join(s.COINS)


def xau():
    bag = []
    r, ok = jalan("Unduh Setra", ["riset/unduh_xau.py", DATA], 900); bag.append(r)
    if not ok: peringatan.append("XAU: unduh Setra gagal")
    r, okd = jalan("Unduh Dukascopy", ["riset/unduh_xau_panjang.py", DATA, "2015"], 1800); bag.append(r)
    if not okd:
        peringatan.append("XAU: unduh Dukascopy gagal (dipakai bibit riset/data + cache)")
        rows = []
        for p in sorted(glob.glob(f"{DATA}/dukascopy/*.json")): rows += json.load(open(p))
        rows = sorted({x[0]: x for x in rows if not (x[1] == x[2] == x[3] == x[4])}.values())
        if rows: json.dump(rows, open(f"{DATA}/xau_panjang.json", "w"))
    else:
        perbarui_bibit()
    # data sambung (Dukascopy < Feb 2025 + Setra) dan 2004-skrg
    sys.path.insert(0, os.path.join(REPO, "riset", "xau", "eksperimen"))
    try:
        import audit_mesin as m
        S = m.sambung(m.muat(f"{DATA}/xau_panjang.json"), m.muat(f"{DATA}/xau.json"))
        json.dump([[int(S[0][i]), *(float(S[k][i]) for k in range(1, 5))] for i in range(len(S[0]))], open(f"{DATA}/xau_sambung.json", "w"))
    except Exception as e:
        bag.append(f"### Rakit xau_sambung GAGAL: {e}\n"); peringatan.append("XAU: rakit data sambung gagal")
    r, _ = jalan("Gabung 2004-skrg", ["riset/gabung_xau_lama.py", f"{DATA}/xau_sambung.json", f"{DATA}/xau_2004.json"]); bag.append(r)
    # replay hanya pada hari yang sudah ditutup (23:00 WIB); posisi hari berjalan yang masih terbuka bukan beda mesin
    src = f"{DATA}/xau.json"
    if now.hour < 23:
        batas = now.replace(hour=7, minute=0, second=0, microsecond=0).timestamp()
        json.dump([x for x in json.load(open(src)) if x[0] < batas], open(f"{DATA}/xau_replay.json", "w")); src = f"{DATA}/xau_replay.json"
    r, ok = jalan("Replay kesetaraan (wajib IDENTIK)", ["riset/replay_xau.py", ".", src, f"{DATA}/xau_panjang.json"]); bag.append(r)
    if not ok or "BEDA" in r: peringatan.append("XAU: replay TIDAK IDENTIK / gagal — cek riset/harian/xau.md")
    r, ok = jalan("Penyebab SL 7 hari", ["riset/xau/sebab_sl.py", ".", f"{DATA}/xau.json", "7", f"{DATA}/xau_2004.json"]); bag.append(r)
    if not ok: peringatan.append("XAU: sebab_sl gagal")
    r, ok = jalan("Bayangan (live vs menu)", ["riset/xau/bayangan.py", ".", f"{DATA}/xau.json", f"{DATA}/xau_panjang.json"]); bag.append(r)
    if not ok: peringatan.append("XAU: bayangan gagal")
    return bag


def perbarui_bibit():
    """Simpan Dukascopy H1 s.d. akhir bulan penuh terakhir ke riset/data agar sesi riset tidak perlu mengunduh Dukascopy."""
    p = os.path.join(REPO, "riset", "data", "xau_dukascopy_h1.json.gz")
    rows = json.load(open(f"{DATA}/xau_panjang.json"))
    awal_bulan = dt.datetime(now.year, now.month, 1, tzinfo=dt.timezone.utc).timestamp()
    rows = [r for r in rows if r[0] < awal_bulan]
    lama = json.load(gzip.open(p, "rt")) if os.path.exists(p) else []
    if rows and (not lama or rows[-1][0] > lama[-1][0]):
        with gzip.open(p, "wt") as f: json.dump(rows, f)


def crypto(C):
    bag = []
    r, ok = jalan("Unduh H1 + funding", ["riset/unduh_crypto.py", DATA, C], 2400); bag.append(r)
    if not ok: peringatan.append("Crypto: unduh gagal")
    r, ok = jalan("Penyebab SL 7 hari + kesehatan", ["riset/crypto/sebab_sl.py", ".", DATA, "7"]); bag.append(r)
    if not ok: peringatan.append("Crypto: sebab_sl gagal")
    r, ok = jalan("Bayangan", ["riset/crypto/bayangan.py", ".", DATA]); bag.append(r)
    if not ok: peringatan.append("Crypto: bayangan gagal")
    return bag


def intraday(C):
    bag = []
    if not os.path.exists(f"{DATA}/klines"):
        r, _ = jalan("Unduh H1 + funding", ["riset/unduh_crypto.py", DATA, C], 2400); bag.append(r)
    r, ok = jalan("Unduh 15 menit", ["riset/unduh_intraday.py", DATA, C], 2400); bag.append(r)
    if not ok: peringatan.append("Intraday: unduh gagal")
    r, ok = jalan("Penyebab SL 7 hari + kesetaraan", ["riset/intraday/sebab_sl.py", ".", DATA, "7"]); bag.append(r)
    if not ok: peringatan.append("Intraday: sebab_sl gagal")
    r, ok = jalan("Bayangan", ["riset/intraday/bayangan.py", ".", DATA]); bag.append(r)
    if not ok: peringatan.append("Intraday: bayangan gagal")
    return bag


def fx():
    """Bot FX MAJOR (live 20 Nov 2026): replay kesetaraan + penyebab SL 7 hari + kesehatan + bayangan (riset/fx/harian_fx.py)."""
    r, ok = jalan("Replay · penyebab SL · kesehatan · bayangan", ["riset/fx/harian_fx.py", ".", "7"], 1800)
    if not ok: peringatan.append("FX: rutinitas harian gagal")
    elif "BEDA" in r: peringatan.append("FX: replay TIDAK IDENTIK — cek riset/harian/fx.md")
    if "PERINGATAN" in r: peringatan.append("FX: drawdown live melebihi backtest")
    return [r]


C = coins() if {"crypto", "intraday"} & set(BOTS) else ""
for bot in BOTS:
    bag = {"xau": xau, "crypto": lambda: crypto(C), "intraday": lambda: intraday(C), "fx": fx}[bot]()
    teks = (f"# Rutinitas harian {bot.upper()} · {now.strftime('%a %d %b %Y %H:%M')} WIB\n"
            f"Dibuat otomatis oleh riset/harian.py (GitHub Actions). Sesi riset: baca ini, JANGAN ulangi langkahnya kecuali ada GAGAL.\n\n"
            + "\n".join(bag))
    open(os.path.join(OUT, f"{bot}.md"), "w").write(teks)
    open(os.path.join(ARSIP, f"{bot}-{TGL}.md"), "w").write(teks)
batas = (now - dt.timedelta(days=21)).strftime("%Y-%m-%d")
for p in glob.glob(os.path.join(ARSIP, "*.md")):
    if os.path.basename(p).rsplit("-", 3)[-3:] and "-".join(os.path.basename(p)[:-3].split("-")[-3:]) < batas: os.remove(p)
pw = os.path.join(OUT, "PERINGATAN.txt")
if peringatan:
    open(pw, "w").write(f"⚠️ RUTINITAS HARIAN RISET {TGL}\n" + "\n".join("• " + x for x in peringatan) + "\nRincian: riset/harian/")
elif os.path.exists(pw):
    os.remove(pw)
print("Selesai.", "Peringatan:" if peringatan else "Tanpa peringatan.", *peringatan, sep="\n")
