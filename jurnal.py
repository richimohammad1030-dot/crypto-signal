"""Lapis 1 - jurnal trade.
Setiap trade yang selesai disimpan beserta kondisinya ke jurnal/<bot>-YYYY-MM.json (bulan WIB saat posisi ditutup).
Dipakai untuk cek kesehatan (Lapis 2) dan review/riset bulanan (Lapis 3)."""
import bisect, datetime as dt, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(HERE, "jurnal")
WIB = dt.timezone(dt.timedelta(hours=7))


def mfe_mae(T, H, L, t0, t1, d, e, r0):
    """Untung tertinggi (MFE) dan rugi terdalam (MAE) dalam R selama posisi terbuka, dari candle t0 s.d. t1."""
    if not r0 or not T:
        return None, None
    a, b = bisect.bisect_left(T, t0), bisect.bisect_right(T, t1)
    if a >= b:
        return None, None
    hi, lo = max(H[a:b]), min(L[a:b])
    best, worst = (hi - e, lo - e) if d == 1 else (e - lo, e - hi)
    return round(best / r0, 3), round(worst / r0, 3)


def load(bot, month=None):
    """Semua entri jurnal bot (atau satu bulan 'YYYY-MM')."""
    out = []
    if not os.path.isdir(DIR):
        return out
    for f in sorted(os.listdir(DIR)):
        if f.startswith(bot + "-") and f.endswith(".json") and (month is None or f == f"{bot}-{month}.json"):
            try:
                out += json.load(open(os.path.join(DIR, f)))
            except Exception:
                pass
    return out


def append(bot, entry):
    """Tambah satu trade. Kunci unik: (sym, t0) - run ganda tidak membuat entri dobel."""
    os.makedirs(DIR, exist_ok=True)
    month = dt.datetime.fromtimestamp(entry["t1"], WIB).strftime("%Y-%m")
    path = os.path.join(DIR, f"{bot}-{month}.json")
    rows = json.load(open(path)) if os.path.exists(path) else []
    if any(r.get("sym") == entry.get("sym") and r.get("t0") == entry.get("t0") for r in rows):
        return
    entry = {"waktu_tutup_wib": dt.datetime.fromtimestamp(entry["t1"], WIB).strftime("%Y-%m-%d %H:%M"), **entry}
    rows.append(entry)
    json.dump(rows, open(path, "w"), indent=1)
