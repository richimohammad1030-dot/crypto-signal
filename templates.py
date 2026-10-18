"""
Templat pesan Telegram. Setiap kejadian = satu bubble yang berdiri sendiri.
"""
import datetime as dt

LINE = "━━━━━━━━━━━━━━━━━━"


def _arah(d):
    return ("🟢", "BUY / LONG") if d == 1 else ("🔴", "SELL / SHORT")


def _pct(a, b):
    return abs(a - b) / a * 100


def _durasi(t0, t1):
    s = max(0, int(t1 - t0))
    d, h = s // 86400, (s % 86400) // 3600
    return f"{d} hari {h} jam" if d else f"{h} jam"


def _wib(ts):
    return (dt.datetime.fromtimestamp(ts, dt.timezone.utc) + dt.timedelta(hours=7)).strftime("%d %b %H:%M WIB")


def _sl_status(d, e, sl, r0):
    """Status SL: berapa R yang terkunci jika SL kena."""
    lock = (sl - e) * d / r0 if r0 else 0.0
    if lock <= -0.9:
        return f"🛡️ SL awal · risiko {lock:+.2f}R"
    if lock < -0.15:
        return f"🛡️ SL dikencangkan · risiko tinggal {lock:+.2f}R"
    if lock < 0.15:
        return f"🟡 SL+ impas · terkunci {lock:+.2f}R"
    return f"✅ SL+ · terkunci {lock:+.2f}R"


def order_baru(sym, d, entry, sl, lev, fmt):
    ic, arah = _arah(d)
    jenis = "BUY STOP" if d == 1 else "SELL STOP"
    tunggu = "naik" if d == 1 else "turun"
    return (f"🆕 <b>SINYAL BARU</b> · {ic} <b>{arah}</b>\n"
            f"{LINE}\n"
            f"🪙 Pair      : <b>{sym}</b>\n"
            f"📍 Order     : <b>{jenis}</b> (Stop Market)\n"
            f"🎯 Entry     : <b>{fmt(entry)}</b>\n"
            f"🛑 Stop loss : <b>{fmt(sl)}</b> ({_pct(entry, sl):.1f}%)\n"
            f"🏁 Take profit: tidak ada (SL digeser)\n"
            f"⚙️ Leverage  : maks {lev}× · Isolated\n"
            f"{LINE}\n"
            f"⏳ Menunggu harga {tunggu} ke {fmt(entry)}.\n"
            f"👉 Pasang {jenis} + SL sesuai angka di atas.")


def order_update(sym, d, entry, sl, old, lev, fmt):
    ic, arah = _arah(d)
    jenis = "BUY STOP" if d == 1 else "SELL STOP"
    oe, osl = old[1], old[2]
    alasan = []
    if abs(entry - oe) > 1e-12:
        alasan.append(f"{'high' if d == 1 else 'low'} 20 hari bergeser")
    if abs(sl - osl) / entry > 0.002:
        alasan.append("volatilitas (ATR) berubah")
    return (f"♻️ <b>UPDATE ORDER</b> · {ic} {arah} · <b>{sym}</b>\n"
            f"{LINE}\n"
            f"Order Anda <b>belum terisi</b>, angkanya diperbarui:\n"
            f"🎯 Entry : {fmt(oe)} → <b>{fmt(entry)}</b>\n"
            f"🛑 SL    : {fmt(osl)} → <b>{fmt(sl)}</b> ({_pct(entry, sl):.1f}%)\n"
            f"⚙️ Leverage: maks {lev}× · Isolated\n"
            f"ℹ️ Alasan: {', '.join(alasan) or 'penyesuaian level'}\n"
            f"{LINE}\n"
            f"👉 Edit / pasang ulang {jenis} {sym} dengan angka baru.")


def order_batal(sym, reason):
    return (f"❌ <b>ORDER DIBATALKAN</b> · <b>{sym}</b>\n"
            f"{LINE}\n"
            f"ℹ️ Alasan: {reason}\n"
            f"👉 Cancel order pending {sym} (yang belum terisi).")


def posisi_terbuka(sym, d, entry, sl, t, r0, fmt):
    ic, arah = _arah(d)
    return (f"✅ <b>POSISI TERBUKA</b> · {ic} <b>{arah}</b>\n"
            f"{LINE}\n"
            f"🪙 Pair   : <b>{sym}</b>\n"
            f"🎯 Entry  : <b>{fmt(entry)}</b> (terisi ±{_wib(t)})\n"
            f"🛑 SL     : <b>{fmt(sl)}</b> ({_pct(entry, sl):.1f}% · risiko 1R)\n"
            f"🏁 TP     : tidak ada — SL akan digeser saat harga bergerak menguntungkan\n"
            f"{LINE}\n"
            f"👉 Pastikan SL {fmt(sl)} terpasang di exchange.")


def geser_sl(sym, d, entry, old, sl, r0, fmt):
    ic, arah = _arah(d)
    return (f"🔁 <b>GESER SL</b> · {ic} {arah} · <b>{sym}</b>\n"
            f"{LINE}\n"
            f"🎯 Entry  : {fmt(entry)}\n"
            f"🛑 SL     : {fmt(old)} → <b>{fmt(sl)}</b>\n"
            f"{_sl_status(d, entry, sl, r0)}\n"
            f"ℹ️ SL baru = {'low terendah' if d == 1 else 'high tertinggi'} 3 hari terakhir\n"
            f"{LINE}\n"
            f"👉 Ubah SL {sym} di exchange ke <b>{fmt(sl)}</b>.")


def posisi_tutup(sym, d, entry, ex, R, t0, t1, why, label, fmt):
    ic, arah = _arah(d)
    gerak = (ex - entry) * d / entry * 100
    return (f"🏁 <b>POSISI DITUTUP</b> · {ic} {arah} · <b>{sym}</b>\n"
            f"{LINE}\n"
            f"🎯 Entry  : {fmt(entry)}\n"
            f"🚪 Keluar : <b>{fmt(ex)}</b> ({why})\n"
            f"📈 Gerak  : {gerak:+.2f}% harga\n"
            f"⏱ Lama   : {_durasi(t0, t1)}\n"
            f"{LINE}\n"
            f"{label}")


def update_posisi(rows, fmt, now_ts):
    """rows: list (sym, d, entry, sl, r0, harga_sekarang, t0). Satu bubble untuk semua posisi terbuka."""
    L = [f"📊 <b>UPDATE POSISI TERBUKA</b> · {len(rows)} posisi", LINE]
    tot = 0.0
    for sym, d, e, sl, r0, px, t0 in rows:
        ic, arah = _arah(d)
        gerak = (px - e) * d / e * 100
        R = (px - e) * d / r0 if r0 else 0.0
        tot += R
        tanda = "🟢" if R > 0 else "🔴" if R < 0 else "⚪"
        L.append(f"{ic} <b>{sym}</b> {arah.split(' /')[0]} · {_durasi(t0, now_ts)}\n"
                 f"   Entry {fmt(e)} → kini {fmt(px)}\n"
                 f"   {tanda} {gerak:+.2f}% · {R:+.2f}R berjalan\n"
                 f"   SL {fmt(sl)} · {_sl_status(d, e, sl, r0)}")
    L.append(LINE)
    L.append(f"Σ Total berjalan: <b>{tot:+.2f}R</b>")
    return "\n".join(L)
