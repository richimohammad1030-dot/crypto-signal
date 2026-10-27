"""
Templat pesan Telegram — maksimal 2 bubble per cek:
  1) SINYAL  : order baru, update order, order dibatalkan
  2) UPDATE  : order terisi, geser SL, posisi ditutup, ringkasan posisi terbuka
Bagian monospace (<pre>) membuat angka sejajar dan mudah dibaca.
"""
import datetime as dt
import html

try:   # aturan versi optimal (satu sumber: signal_bot.py)
    from signal_bot import TP1_R, TP1_FRAC, STAG_DAYS, STAG_R
except Exception:
    TP1_R, TP1_FRAC, STAG_DAYS, STAG_R = 1.0, 0.25, 2.0, -0.2


def _tp1(d, e, r0):
    return e + d * TP1_R * r0


def _blend(d, e, r0, px, ext):
    rest = (px - e) * d / r0 if r0 else 0.0
    part = (ext or {}).get("part", 0.0)
    return part * (ext or {}).get("partR", 0.0) + (1 - part) * rest



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


CONV = {"HIGH": "🟢 HIGH", "MEDIUM": "🟡 MEDIUM", "LOW": "🔴 LOW"}
DOT = {"HIGH": "🟢", "MEDIUM": "🟡", "LOW": "🔴"}
LEGEND = "Label: 🟢 HIGH · 🟡 MEDIUM · 🔴 LOW (kualitas historis setup)"


def _conv(c):
    return f"  Label : {CONV[c]}" if c in CONV else None


CONV_TXT = {"HIGH": "High Conviction", "MEDIUM": "Medium Conviction", "LOW": "Low Conviction"}


CONV_SHORT = {"HIGH": "High", "MEDIUM": "Medium", "LOW": "Low"}


def _head(conv, sym, right):
    """Judul koin: titik warna + simbol + arah + conviction di kolom kanan yang sejajar untuk semua koin."""
    dot = DOT.get(conv)
    if not dot:
        return f"   {sym:<11}{right}"
    return f"{dot} {sym:<11}{right} | {CONV_TXT[conv]}"


def _pre(lines):
    return "<pre>" + html.escape("\n".join(lines)) + "</pre>"


def _sl_tag(d, e, sl, r0):
    lock = (sl - e) * d / r0 if r0 else 0.0
    if lock <= -0.9:
        return "risiko penuh -1R"
    if lock < -0.15:
        return f"risiko {lock:.2f}R"
    if lock < 0.15:
        return "impas"
    return f"profit terkunci {lock:+.2f}R"


def _hasil(R, why=""):
    if "stagnan" in (why or ""):
        return "Cut-loss stagnan"
    if R <= -0.9:
        return "Kena SL"
    if R < -0.15:
        return "Rugi"
    if R < 0.15:
        return "Impas"
    return "Untung"


LINE = "────────────────────"


TAG = "🔵 <b>SWING</b>"   # pembeda dengan bot intraday (🟠 INTRADAY) di channel yang sama


def _title(name, t):
    return [f"{TAG} · <b>{name}</b>", _wib(t), LINE]


def _sec(L, name, n=None):
    if L and L[-1] not in ("", LINE):
        L.append("")
    L.append(f"<b>{name}</b>")
    L.append(LINE)


def signal_bubble(ev, t, fmt, pending, day):
    """Satu bubble berisi SEMUA order yang belum terisi.
    ev      : kejadian run ini ('new', 'upd', 'cancel'); bubble hanya dikirim jika ada perubahan.
    pending : order aktif saat ini, list (sym, d, entry, sl, lev, label), urut peringkat market cap.
    day     : catatan hari ini (WIB): {'new': [sym], 'upd': {sym: [entry_awal, sl_awal]}, 'cancel': [[sym, alasan]]}."""
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
        for sym, d, e, sl, lev, conv in group:
            rows.append(_head(conv, sym, "BUY STOP" if d == 1 else "SELL STOP"))
            tp = _tp1(d, e, abs(e - sl))
            if show_old:
                oe, osl = upd_today[sym]
                rows += [f"   Entry : {fmt(oe)} → {fmt(e)}",
                         f"   SL    : {fmt(osl)} → {fmt(sl)}",
                         f"   TP 25%: {fmt(_tp1(d, oe, abs(oe - osl)))} → {fmt(tp)}"]
            else:
                rows += [f"   Entry : {fmt(e)}",
                         f"   SL    : {fmt(sl)}  ({_pct(e, sl):.1f}%)",
                         f"   TP 25%: {fmt(tp)}  (+1R, tutup 25%)"]
            rows += [f"   Lev   : {lev}x", ""]
        return _pre(rows[:-1])

    L = _title("SINYAL CRYPTO FUTURES", t)
    if baru:
        _sec(L, "ORDER BARU", len(baru)); L.append(order_rows(baru))
    if upd:
        _sec(L, "UPDATE ORDER", len(upd)); L.append("Harga order berubah, ganti order lama di exchange."); L.append(order_rows(upd, True))
    if aktif:
        _sec(L, "ORDER MENUNGGU", len(aktif))
        L.append(f"Total order belum terisi: <b>{len(pending)}</b>")
        L.append(order_rows(aktif))
    if batal:
        _sec(L, "DIBATALKAN HARI INI", len(batal)); L.append("Hapus order ini di exchange.")
        L.append(_pre([f"   {sym:<10}{reason}" for sym, reason in batal]))
    return "\n".join(L)


def update_bubble(ev, open_rows, t, fmt):
    """Urutan: posisi terbuka, terisi, geser SL, posisi ditutup.
    ev: list 'fill', 'trail', 'exit'. open_rows: (sym, d, entry, sl, r0, harga, t0, label). Return teks atau None."""
    partial = ev.get("partial", [])
    if not (ev["fill"] or ev["trail"] or ev["exit"] or partial or open_rows):
        return None
    L = _title("POSISI CRYPTO FUTURES", t)
    if open_rows:
        tot = 0.0
        rows = []
        for sym, d, e, sl, r0, px, t0, conv, *rest in open_rows:
            ext = rest[0] if rest else {}
            R = _blend(d, e, r0, px, ext)
            tot += R
            tp_txt = (f"sudah diambil ({ext.get('partR', 0):+.2f}R)" if ext.get("part")
                      else f"{fmt(_tp1(d, e, r0))}  (belum)")
            t_cut = t0 + STAG_DAYS * 86400
            cut_txt = (f"aktif · tutup jika < {STAG_R:.1f}R" if t >= t_cut
                       else f"aktif mulai {_wib(t_cut).split(' · ')[0]} {_wib(t_cut).split(' · ')[1][:5]}")
            rows += [_head(conv, sym, "BUY" if d == 1 else "SELL"),
                     f"   Durasi: {_durasi(t0, t)}",
                     f"   Entry : {fmt(e)}",
                     f"   Kini  : {fmt(px)}  ({(px - e) * d / e * 100:+.2f}%)",
                     f"   Hasil : {R:+.2f}R",
                     f"   SL    : {fmt(sl)}  ({_sl_tag(d, e, sl, r0)})",
                     f"   TP 25%: {tp_txt}",
                     f"   Cut   : {cut_txt}", ""]
        _sec(L, "POSISI TERBUKA", len(open_rows)); L.append(f"Total berjalan: <b>{tot:+.2f}R</b>")
        L.append(_pre(rows[:-1]))
    else:
        _sec(L, "POSISI TERBUKA"); L.append("Tidak ada posisi terbuka.")
    if ev["fill"]:
        _sec(L, "ORDER TERISI", len(ev["fill"]))
        L.append("Order sudah menjadi posisi. Pastikan SL terpasang, lalu pasang TP 25% (reduce-only, 25% ukuran posisi).")
        rows = []
        for sym, d, e, sl, c in ev["fill"]:
            rows += [_head(c, sym, "BUY" if d == 1 else "SELL"), f"   Entry : {fmt(e)}", f"   SL    : {fmt(sl)}",
                     f"   TP 25%: {fmt(_tp1(d, e, abs(e - sl)))}  (+1R)", ""]
        L.append(_pre(rows[:-1]))
    if partial:
        _sec(L, "AMBIL PROFIT 25%", len(partial))
        L.append("Harga sudah menyentuh +1R. Jika TP 25% belum terisi otomatis, tutup 25% posisi sekarang. Sisa 75% tetap jalan dengan SL.")
        rows = []
        for sym, d, e, px, R, frac, sl, r0, c in partial:
            rows += [_head(c, sym, "BUY" if d == 1 else "SELL"), f"   Entry : {fmt(e)}",
                     f"   TP 25%: {fmt(px)}  ({R:+.2f}R untuk porsi {frac * 100:.0f}%)", f"   SL    : {fmt(sl)}  (sisa 75%)", ""]
        L.append(_pre(rows[:-1]))
    if ev["trail"]:
        _sec(L, "GESER SL", len(ev["trail"])); L.append("Ubah SL di exchange ke angka baru.")
        rows = []
        for sym, d, e, old, sl, r0, c in ev["trail"]:
            why = "ikut harga tertinggi 3 hari" if d == -1 else "ikut harga terendah 3 hari"
            rows += [_head(c, sym, "BUY" if d == 1 else "SELL"), f"   SL    : {fmt(old)} → {fmt(sl)}",
                     f"   Status: {_sl_tag(d, e, sl, r0)}", f"   Alasan: {why}", ""]
        L.append(_pre(rows[:-1]))
    if ev["exit"]:
        _sec(L, "POSISI DITUTUP", len(ev["exit"]))
        stag = [x for x in ev["exit"] if len(x) > 8 and "stagnan" in (x[8] or "")]
        if stag:
            batas = f"{abs(STAG_R):.1f}".replace(".", ",")
            L.append(f"✂️ Cut-loss stagnan ({', '.join(x[0] for x in stag)}): posisi ≥ {STAG_DAYS:.0f} hari masih rugi > "
                     f"{batas}R. <b>Tutup posisi di harga pasar sekarang</b> dan hapus SL/TP-nya.")
        rows = []
        for sym, d, e, ex, R, t0, t1, c, *rest in ev["exit"]:
            why = rest[0] if rest else ""
            part = rest[1] if len(rest) > 1 else 0
            rows += [_head(c, sym, "BUY" if d == 1 else "SELL"),
                     f"   Entry : {fmt(e)}", f"   Keluar: {fmt(ex)}", f"   Hasil : {R:+.2f}R · {_hasil(R, why)}"]
            if part:
                rows.append(f"   Catat : termasuk TP {part * 100:.0f}% di +1R")
            rows += [f"   Durasi: {_durasi(t0, t1)}", ""]
        L.append(_pre(rows[:-1]))
    return "\n".join(L)


def news_bubble(news, open_rows, n_pend, now, fmt):
    """Peringatan event USD berdampak tinggi. news: list (t, judul, forecast, previous).
    open_rows: (sym, d, entry, sl, r0, harga, t0, label). Netral: tidak menyuruh menutup posisi."""
    L = _title("PERINGATAN NEWS USD", now)
    _sec(L, "JADWAL", len(news))
    rows = []
    for t, title, fc, prev in news:
        m = max(0, int(t - now) // 60)
        jam = _wib(t).split(" · ")[1]
        rows.append(f"   {jam} · {m // 60} jam {m % 60} mnt lagi" if m >= 60 else f"   {jam} · {m} mnt lagi")
        rows.append(f"   {title}")
        info = " · ".join(x for x in (f"Forecast {fc}" if fc else "", f"Sebelumnya {prev}" if prev else "") if x)
        if info:
            rows.append(f"   {info}")
        rows.append("")
    L.append(_pre(rows[:-1]))
    if open_rows:
        tot, prs = 0.0, []
        for sym, d, e, sl, r0, px, t0, conv, *rest in open_rows:
            R = _blend(d, e, r0, px, rest[0] if rest else {})
            tot += R
            prs += [_head(conv, sym, "BUY" if d == 1 else "SELL"), f"   Hasil : {R:+.2f}R", f"   SL    : {fmt(sl)}"]
        _sec(L, "POSISI TERBUKA", len(open_rows)); L.append(f"Total berjalan: <b>{tot:+.2f}R</b>")
        L.append(_pre(prs))
    else:
        _sec(L, "POSISI TERBUKA"); L.append("Tidak ada.")
    if n_pend:
        L.append(f"Order belum terisi: <b>{n_pend}</b> (bisa terisi saat news)")
    L += ["", LINE, "Volatilitas tinggi diperkirakan. Pastikan SL sudah terpasang. "
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
