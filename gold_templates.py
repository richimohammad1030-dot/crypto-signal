"""
Templat pesan Telegram bot XAU — maksimal 2 bubble per run:
  1) SINYAL : order hari ini (07:00 WIB) / pembatalan order (23:00 WIB)
  2) UPDATE : order terisi, posisi ditutup, posisi berjalan
"""
import datetime as dt
import html

SYM = "XAUUSD"
BAR = "━━━━━━━━━━━━━━━━━━━━"
SUB = "┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄"
BULAN = ["", "Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]


def fmt(p):
    return f"{p:,.2f}"


def _w(ts):
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc) + dt.timedelta(hours=7)


def _wib(ts):
    w = _w(ts)
    return f"{HARI[w.weekday()]}, {w.day:02d} {BULAN[w.month]} {w.year} · {w:%H:%M} WIB"


def _jam(ts):
    return f"{_w(ts):%H:%M} WIB"


def _durasi(t0, t1):
    s = max(0, int(t1 - t0))
    h, m = s // 3600, (s % 3600) // 60
    return f"{h} jam {m} menit" if h else f"{m} menit"


def _pre(lines):
    return "<pre>" + html.escape("\n".join(lines)) + "</pre>"


def _hasil(R):
    if R >= 3.5:
        return "🎯 KENA TP"
    if R >= 0.15:
        return "✅ UNTUNG"
    if R > -0.15:
        return "🟡 IMPAS"
    if R <= -0.9:
        return "❌ KENA SL"
    return "⚠️ RUGI SEBAGIAN"


def new_events():
    return {"order": None, "expire": False, "fill": [], "exit": [], "skip": []}


def make_notifier(ev):
    def notify(kind, **k):
        if kind == "order":
            ev["order"] = k
        elif kind == "expire":
            ev["expire"] = True
        elif kind == "fill":
            ev["fill"].append(k)
        elif kind == "exit":
            ev["exit"].append(k)
        elif kind == "skip":
            ev["skip"].append(k)
    return notify


def signal_bubble(ev, t, risk_pct, live_px=None):
    if not ev["order"] and not ev["expire"]:
        return None
    L = [f"🥇 <b>SINYAL {SYM}</b> · Gold Daily Straddle", f"🕐 {_wib(t)}", BAR]
    if ev["order"] and ev["order"]["pend"].get("main"):
        p = ev["order"]["pend"]; d = p["main"]
        o = p["buy"] if d == 1 else p["sell"]
        batal = p["sell"][0] if d == 1 else p["buy"][0]
        arah = "BUY STOP" if d == 1 else "SELL STOP"
        L.append(f"🌅 <b>ORDER HARI INI · {arah}</b> (searah tren)")
        L.append(_pre([
            f"Range 04:00–07:00 : {fmt(p['lo'])} – {fmt(p['hi'])}",
            f"Tren H1 (EMA200 {fmt(p['ema'])}) : {'NAIK' if d == 1 else 'TURUN'}",
            "",
            arah,
            f"  Entry : {fmt(o[0])}",
            f"  SL    : {fmt(o[1])}  (-{fmt(abs(o[0] - o[1]))})",
            f"  TP    : {fmt(o[2])}  (+{fmt(abs(o[2] - o[0]))})",
            "",
            f"BATAS BATAL : {fmt(batal)}",
        ]))
        if live_px is not None and (live_px - o[0]) * d >= 0:
            L.append(f"⚠️ Harga terakhir {fmt(live_px)} sudah melewati {arah} → order langsung terisi di harga pasar.")
        if live_px is not None and (batal - live_px) * d >= 0:
            L.append(f"⚠️ Harga terakhir {fmt(live_px)} sudah di batas batal → <b>jangan pasang</b> order hari ini.")
        L += [BAR,
              f"🚫 Harga menyentuh <b>{fmt(batal)}</b> sebelum {arah} terisi → <b>batalkan</b> order, hari ini tanpa trade",
              "🔔 Saran: pasang price alert di batas batal",
              "🎯 TP = 4R · ⏰ berlaku s.d. <b>23:00 WIB</b>",
              f"⚖️ Risiko saran {risk_pct}% modal"]
    elif ev["order"]:
        p = ev["order"]["pend"]
        b, s = p["buy"], p["sell"]
        L.append("🌅 <b>ORDER HARI INI</b> (OCO)")
        L.append(_pre([
            f"Range 04:00–07:00 : {fmt(p['lo'])} – {fmt(p['hi'])}",
            "",
            "BUY STOP",
            f"  Entry : {fmt(b[0])}",
            f"  SL    : {fmt(b[1])}  (-{fmt(b[0] - b[1])})",
            f"  TP    : {fmt(b[2])}  (+{fmt(b[2] - b[0])})",
            "",
            "SELL STOP",
            f"  Entry : {fmt(s[0])}",
            f"  SL    : {fmt(s[1])}  (-{fmt(s[1] - s[0])})",
            f"  TP    : {fmt(s[2])}  (+{fmt(s[0] - s[2])})",
        ]))
        warn = []
        if live_px is not None and live_px >= b[0]:
            warn.append(f"⚠️ Harga terakhir {fmt(live_px)} sudah di atas BUY STOP → order BUY langsung terisi di harga pasar.")
        if live_px is not None and live_px <= s[0]:
            warn.append(f"⚠️ Harga terakhir {fmt(live_px)} sudah di bawah SELL STOP → order SELL langsung terisi di harga pasar.")
        L += warn
        L += [BAR,
              "🔗 Satu terisi → <b>batalkan</b> order lainnya",
              "🎯 TP = 4R · ⏰ berlaku s.d. <b>23:00 WIB</b>",
              f"⚖️ Risiko saran {risk_pct}% modal per order"]
    if ev["expire"]:
        if ev["order"]:
            L.append(SUB)
        L += ["⏰ <b>23:00 WIB · ORDER TIDAK TERISI</b>",
              "👉 <b>Batalkan</b> order XAU yang masih aktif.",
              BAR]
    return "\n".join(L)


def news_bubble(news, pos, pend, px, now):
    """Peringatan event USD berdampak tinggi untuk XAU. news: list (t, judul, forecast, previous).
    Netral: tidak menyuruh menutup posisi."""
    L = ["⚠️ <b>PERINGATAN NEWS</b> · USD dampak tinggi", f"🕐 {_wib(now)}", BAR,
         f"📅 <b>JADWAL</b> · {len(news)} event"]
    rows = []
    for t, title, fc, prev in news:
        m = max(0, int(t - now) // 60)
        rows.append(f"{_jam(t)} · {m // 60} jam {m % 60} mnt lagi" if m >= 60 else f"{_jam(t)} · {m} mnt lagi")
        rows.append(f"  {title}")
        info = " · ".join(x for x in (f"Forecast {fc}" if fc else "", f"Sebelumnya {prev}" if prev else "") if x)
        if info:
            rows.append(f"  {info}")
        rows.append("")
    L.append(_pre(rows[:-1]))
    L.append(SUB)
    if pos:
        R = (px - pos["e"]) * pos["d"] / pos["r0"] if pos.get("r0") and px else 0.0
        L.append(f"📂 <b>POSISI {SYM} · {'BUY' if pos['d'] == 1 else 'SELL'}</b> · {R:+.2f}R")
        L.append(_pre([f"Entry : {fmt(pos['e'])}"] + ([f"Kini  : {fmt(px)}"] if px else []) +
                      [f"SL    : {fmt(pos['sl'])}", f"TP    : {fmt(pos['tp'])}"]))
    elif pend and pend.get("main"):
        d = pend["main"]
        L.append(f"⏳ <b>ORDER AKTIF</b> · bisa terisi saat news")
        L.append(_pre([f"{'BUY STOP ' if d == 1 else 'SELL STOP'}   : {fmt((pend['buy'] if d == 1 else pend['sell'])[0])}",
                       f"BATAS BATAL : {fmt((pend['sell'] if d == 1 else pend['buy'])[0])}"]))
    elif pend:
        L.append(f"⏳ <b>ORDER OCO AKTIF</b> · bisa terisi saat news")
        L.append(_pre([f"BUY STOP  : {fmt(pend['buy'][0])}", f"SELL STOP : {fmt(pend['sell'][0])}"]))
    else:
        L.append("📂 Tidak ada posisi atau order aktif.")
    L += [BAR,
          "ℹ️ Emas biasanya bergerak tajam saat news USD. Pastikan <b>SL sudah terpasang</b>.",
          "Keputusan menutup posisi atau membatalkan order ada di tangan masing-masing."]
    return "\n".join(L)


def update_bubble(ev, pos, px, t):
    if not (ev["fill"] or ev["exit"] or ev.get("skip") or pos):
        return None
    L = [f"📊 <b>UPDATE {SYM}</b>", f"🕐 {_wib(t)}", BAR]
    first = True
    def sep():
        nonlocal first
        if not first:
            L.append(SUB)
        first = False
    for k in ev.get("skip", []):
        sep()
        arah = "BUY STOP" if k["main"] == 1 else "SELL STOP"
        L.append("🚫 <b>HARI INI DILEWATI</b>")
        L.append(_pre([f"Batas batal {fmt(k['level'])} tersentuh lebih dulu ({_jam(k['t'])})"]))
        L.append(f"👉 <b>Batalkan {arah}</b> yang masih aktif. Tidak ada trade sampai sinyal besok 07:00 WIB.")
    for k in ev["fill"]:
        sep()
        arah = "BUY" if k["d"] == 1 else "SELL"
        lawan = "SELL STOP" if k["d"] == 1 else "BUY STOP"
        L.append(f"✅ <b>TERISI · {arah}</b>")
        L.append(_pre([f"Entry : {fmt(k['entry'])}  ({_jam(k['t'])})",
                       f"SL    : {fmt(k['sl'])}",
                       f"TP    : {fmt(k['tp'])}"]))
        L.append(f"👉 Hapus alert batas batal. Pastikan tidak ada order XAU lain yang aktif (mis. {lawan}).")
    for k in ev["exit"]:
        sep()
        arah = "BUY" if k["d"] == 1 else "SELL"
        L.append(f"🏁 <b>DITUTUP · {arah}</b> · {_hasil(k['R'])}")
        L.append(_pre([f"Entry  : {fmt(k['entry'])}",
                       f"Keluar : {fmt(k['exit'])}  ({k['why']})",
                       f"Gerak  : {(k['exit'] - k['entry']) * k['d']:+.2f} USD",
                       f"Hasil  : {k['R']:+.2f}R",
                       f"Lama   : {_durasi(k['t0'], k['t'])}"]))
        if "23:00" in k["why"]:
            L.append("👉 Jika masih terbuka di akun Anda, <b>tutup sekarang</b>.")
    if pos:
        sep()
        d, e = pos["d"], pos["e"]
        R = (px - e) * d / pos["r0"] if pos["r0"] else 0.0
        tanda = "🟢" if R > 0 else "🔴" if R < 0 else "⚪"
        L.append(f"📂 <b>POSISI BERJALAN · {'BUY' if d == 1 else 'SELL'}</b> · {tanda} <b>{R:+.2f}R</b>")
        L.append(_pre([f"Entry : {fmt(e)}",
                       f"Kini  : {fmt(px)}  ({(px - e) * d:+.2f} USD)",
                       f"SL    : {fmt(pos['sl'])}",
                       f"TP    : {fmt(pos['tp'])}",
                       f"Lama  : {_durasi(pos['t0'], t)}"]))
        L.append("⏰ Ditutup paling lambat <b>23:00 WIB</b>")
    L.append(BAR)
    return "\n".join(L)
