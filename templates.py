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


def signal_bubble(ev, t, fmt):
    """ev: dict dengan list 'new', 'upd', 'cancel'. Return teks atau None jika kosong."""
    if not (ev["new"] or ev["upd"] or ev["cancel"]):
        return None
    L = [f"📡 <b>SINYAL CRYPTO FUTURES</b>", f"🕐 {_wib(t)}", BAR]
    if ev["new"]:
        L.append(f"🆕 <b>ORDER BARU</b> · {len(ev['new'])}")
        rows = []
        for sym, d, e, sl, lev in ev["new"]:
            rows += [f"{sym:<10}{'BUY STOP' if d == 1 else 'SELL STOP'}",
                     f"  Entry : {fmt(e)}",
                     f"  SL    : {fmt(sl)}  ({_pct(e, sl):.1f}%)",
                     f"  Lev   : maks {lev}x", ""]
        L.append(_pre(rows[:-1]))
    if ev["upd"]:
        if ev["new"]:
            L.append(SUB)
        L.append(f"♻️ <b>UPDATE ORDER</b> (belum terisi, harga entry berubah) · {len(ev['upd'])}")
        rows = []
        for sym, d, e, sl, oe, osl, lev in ev["upd"]:
            rows += [f"{sym:<10}{'BUY STOP' if d == 1 else 'SELL STOP'}",
                     f"  Entry : {fmt(oe)} → {fmt(e)}",
                     f"  SL    : {fmt(osl)} → {fmt(sl)}",
                     f"  Lev   : maks {lev}x", ""]
        L.append(_pre(rows[:-1]))
    if ev["cancel"]:
        if ev["new"] or ev["upd"]:
            L.append(SUB)
        L.append(f"❌ <b>BATALKAN ORDER</b> · {len(ev['cancel'])}")
        L.append(_pre([f"{sym:<10}{reason}" for sym, reason in ev["cancel"]]))
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
