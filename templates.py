"""
Templat pesan Telegram — maksimal 2 bubble per cek:
  1) SINYAL  : order baru, update order, order dibatalkan
  2) UPDATE  : order terisi, geser SL, posisi ditutup, ringkasan posisi terbuka
Bagian monospace (<pre>) membuat angka sejajar dan mudah dibaca.
"""
import datetime as dt
import html

BAR = "━━━━━━━━━━━━━━━━━━━━"
SUB = "┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄"


BULAN = ["", "Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


def _wib(ts):
    w = dt.datetime.fromtimestamp(ts, dt.timezone.utc) + dt.timedelta(hours=7)
    return f"{w.day:02d} {BULAN[w.month]} {w.year} · {w:%H:%M} WIB"


def _durasi(t0, t1):
    s = max(0, int(t1 - t0))
    d, h = s // 86400, (s % 86400) // 3600
    return f"{d} hari {h} jam" if d else f"{h} jam"


def _pct(a, b):
    return abs(a - b) / a * 100


def _pre(lines):
    return "<pre>" + html.escape("\n".join(lines)) + "</pre>"


def _sl_tag(d, e, sl, r0):
    lock = (sl - e) * d / r0 if r0 else 0.0
    if lock <= -0.9:
        return f"SL awal ({lock:+.2f}R)"
    if lock < -0.15:
        return f"SL ketat ({lock:+.2f}R)"
    if lock < 0.15:
        return f"SL+ impas ({lock:+.2f}R)"
    return f"SL+ terkunci {lock:+.2f}R"


def _hasil(R):
    if R <= -0.9:
        return "❌ SL"
    if R < -0.15:
        return "⚠️ rugi"
    if R < 0.15:
        return "🟡 impas"
    return "✅ untung"


def signal_bubble(ev, t, fmt, pending, day):
    """Satu bubble berisi SEMUA order yang belum terisi.
    ev      : kejadian run ini ('new', 'upd', 'cancel'); bubble hanya dikirim jika ada perubahan.
    pending : order aktif saat ini, list (sym, d, entry, sl, lev), urut peringkat market cap.
    day     : catatan hari ini (WIB): {'new': [sym], 'upd': {sym: [entry_awal, sl_awal]}, 'cancel': [[sym, alasan]]}.
    Kelompok: order baru hari ini, update order hari ini, order aktif lain (tidak berubah), dibatalkan hari ini."""
    if not (ev["new"] or ev["upd"] or ev["cancel"]):
        return None
    new_today = set(day.get("new", []))
    upd_today = day.get("upd", {})
    baru = [p for p in pending if p[0] in new_today]
    upd = [p for p in pending if p[0] not in new_today and p[0] in upd_today]
    aktif = [p for p in pending if p[0] not in new_today and p[0] not in upd_today]
    batal = [c for c in day.get("cancel", []) if c[0] not in {p[0] for p in pending}]

    def order_rows(group, show_old=False):
        rows = []
        for sym, d, e, sl, lev in group:
            rows.append(f"{sym:<10}{'BUY STOP' if d == 1 else 'SELL STOP'}")
            if show_old:
                oe, osl = upd_today[sym]
                rows += [f"  Entry : {fmt(oe)} → {fmt(e)}",
                         f"  SL    : {fmt(osl)} → {fmt(sl)}"]
            else:
                rows += [f"  Entry : {fmt(e)}",
                         f"  SL    : {fmt(sl)}  ({_pct(e, sl):.1f}%)"]
            rows += [f"  Lev   : maks {lev}x", ""]
        return _pre(rows[:-1])

    L = [f"📡 <b>SINYAL CRYPTO FUTURES</b>", f"🕐 {_wib(t)}", BAR,
         f"📋 <b>ORDER BELUM TERISI</b> · {len(pending)} aktif"]
    parts = []
    if baru:
        parts.append([f"🆕 <b>ORDER BARU</b> hari ini · {len(baru)}", order_rows(baru)])
    if upd:
        parts.append([f"♻️ <b>UPDATE ORDER</b> hari ini (harga entry berubah) · {len(upd)}", order_rows(upd, True)])
    if aktif:
        parts.append([f"⏳ <b>ORDER AKTIF</b> (tidak berubah) · {len(aktif)}", order_rows(aktif)])
    if not pending:
        parts.append(["<i>Tidak ada order aktif.</i>"])
    if batal:
        parts.append([f"❌ <b>DIBATALKAN</b> hari ini · {len(batal)}",
                      _pre([f"{sym:<10}{reason}" for sym, reason in batal])])
    for i, p in enumerate(parts):
        if i:
            L.append(SUB)
        L += p
    L += [BAR,
          "📌 Order: <b>Stop Market</b> · SL reduce-only · <b>tanpa TP</b>",
          "📌 Margin <b>Isolated</b> · leverage ≤ angka Lev"]
    return "\n".join(L)


def update_bubble(ev, open_rows, t, fmt):
    """ev: list 'fill', 'trail', 'exit'. open_rows: (sym, d, entry, sl, r0, harga, t0). Return teks atau None."""
    if not (ev["fill"] or ev["trail"] or ev["exit"] or open_rows):
        return None
    L = [f"📊 <b>UPDATE POSISI</b>", f"🕐 {_wib(t)}", BAR]
    first = True
    def sep():
        nonlocal first
        if not first:
            L.append(SUB)
        first = False
    if ev["fill"]:
        sep(); L.append(f"✅ <b>TERISI</b> · pastikan SL terpasang")
        L.append(_pre([f"{sym:<10}{'BUY ' if d == 1 else 'SELL'} @ {fmt(e)}\n  SL    : {fmt(sl)}" for sym, d, e, sl in ev["fill"]]))
    if ev["trail"]:
        sep(); L.append(f"🔁 <b>GESER SL</b> · ubah SL di exchange")
        L.append(_pre([f"{sym:<10}{fmt(old)} → {fmt(sl)}\n  {_sl_tag(d, e, sl, r0)}" for sym, d, e, old, sl, r0 in ev["trail"]]))
    if ev["exit"]:
        sep(); L.append(f"🏁 <b>POSISI DITUTUP</b>")
        L.append(_pre([f"{sym:<10}{'BUY ' if d == 1 else 'SELL'} {_hasil(R)}\n  {fmt(e)} → {fmt(ex)}  {R:+.2f}R · {_durasi(t0, t1)}"
                       for sym, d, e, ex, R, t0, t1 in ev["exit"]]))
    if open_rows:
        sep()
        tot = 0.0
        rows = []
        for sym, d, e, sl, r0, px, t0 in open_rows:
            R = (px - e) * d / r0 if r0 else 0.0
            tot += R
            rows += [f"{sym:<10}{'BUY ' if d == 1 else 'SELL'} · {_durasi(t0, t)}",
                     f"  Entry : {fmt(e)}",
                     f"  Kini  : {fmt(px)}  ({(px - e) * d / e * 100:+.2f}%)",
                     f"  Hasil : {R:+.2f}R berjalan",
                     f"  SL    : {fmt(sl)} · {_sl_tag(d, e, sl, r0)}", ""]
        L.append(f"📂 <b>POSISI TERBUKA</b> · {len(open_rows)} · Σ <b>{tot:+.2f}R</b>")
        L.append(_pre(rows[:-1]))
    L.append(BAR)
    return "\n".join(L)


def news_bubble(news, open_rows, n_pend, now, fmt):
    """Peringatan event USD berdampak tinggi. news: list (t, judul, forecast, previous).
    open_rows: (sym, d, entry, sl, r0, harga, t0). Netral: tidak menyuruh menutup posisi."""
    L = ["⚠️ <b>PERINGATAN NEWS</b> · USD dampak tinggi", f"🕐 {_wib(now)}", BAR,
         f"📅 <b>JADWAL</b> · {len(news)} event"]
    rows = []
    for t, title, fc, prev in news:
        m = max(0, int(t - now) // 60)
        rows.append(f"{_wib(t).split(' · ')[1]} · {m // 60} jam {m % 60} mnt lagi" if m >= 60 else f"{_wib(t).split(' · ')[1]} · {m} mnt lagi")
        rows.append(f"  {title}")
        info = " · ".join(x for x in (f"Forecast {fc}" if fc else "", f"Sebelumnya {prev}" if prev else "") if x)
        if info:
            rows.append(f"  {info}")
        rows.append("")
    L.append(_pre(rows[:-1]))
    L.append(SUB)
    if open_rows:
        tot, prs = 0.0, []
        for sym, d, e, sl, r0, px, t0 in open_rows:
            R = (px - e) * d / r0 if r0 else 0.0
            tot += R
            prs += [f"{sym:<10}{'BUY ' if d == 1 else 'SELL'} · {R:+.2f}R",
                    f"  SL    : {fmt(sl)} · {_sl_tag(d, e, sl, r0)}"]
        L.append(f"📂 <b>POSISI TERBUKA</b> · {len(open_rows)} · Σ <b>{tot:+.2f}R</b>")
        L.append(_pre(prs))
    else:
        L.append("📂 Tidak ada posisi terbuka.")
    if n_pend:
        L.append(f"⏳ Order pending: <b>{n_pend}</b> (bisa terisi saat news)")
    L += [BAR,
          "ℹ️ Volatilitas tinggi diperkirakan. Pastikan <b>SL sudah terpasang</b> di exchange.",
          "Keputusan menutup posisi atau membatalkan order ada di tangan masing-masing."]
    return "\n".join(L)


def split_message(text, limit=3900):
    """Pecah pesan panjang di batas blok agar tidak melebihi batas Telegram (4096)."""
    if len(text) <= limit:
        return [text]
    parts, cur = [], ""
    for block in text.split("\n"):
        if len(cur) + len(block) + 1 > limit:
            if cur.count("<pre>") > cur.count("</pre>"):
                cur += "</pre>"; block = "<pre>" + block
            parts.append(cur); cur = "<i>(lanjutan)</i>\n"
        cur += block + "\n"
    parts.append(cur)
    return parts
