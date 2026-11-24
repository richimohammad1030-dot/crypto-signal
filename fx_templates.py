"""Templat pesan Telegram bot FX MAJOR — gaya sama dengan bot swing/intraday/XAU (judul bertag, garis, blok <pre> per pair,
label conviction 🟢 HIGH · 🟡 MEDIUM · 🔴 LOW)."""
import datetime as dt, html

TAG = "🟣 <b>FX MAJOR</b>"          # pembeda di channel yang sama (🔵 SWING · 🟠 INTRADAY · 🥇 XAU)
LINE = "────────────────────"
HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
BULAN = ["", "Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
DOT = {"HIGH": "🟢", "MEDIUM": "🟡", "LOW": "🔴"}
CONV_TXT = {"HIGH": "High Conviction", "MEDIUM": "Medium Conviction", "LOW": "Low Conviction"}
RANK = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, None: 3}
LEGEND = "Label: 🟢 HIGH · 🟡 MEDIUM · 🔴 LOW (kualitas historis setup)"
PIP = {"USDJPY": 0.01}


def _w(ts):
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc) + dt.timedelta(hours=7)


def wib(ts):
    w = _w(ts)
    return f"🕐 {HARI[w.weekday()]}, {w.day:02d} {BULAN[w.month]} {w.year} · {w:%H:%M} WIB"


def jam(ts):
    return f"{_w(ts):%H:%M} WIB"


def px(pair, v):
    return f"{v:.{3 if pair.endswith('JPY') else 5}f}"


def pip(pair, a, b, sign=True):
    p = (a - b) / PIP.get(pair, 0.0001)
    return (f"{p:+.1f}" if sign else f"{abs(p):.1f}").replace(".", ",") + " pip"


def _pre(lines):
    return "<pre>" + html.escape("\n".join(lines)) + "</pre>"


def _head(conv, pair, right):
    dot = DOT.get(conv, "⚪")
    return f"{dot} {pair:<7} {right:<14}| {CONV_TXT.get(conv, '-')}"


def _title(name, t):
    return [f"{TAG} · <b>{name}</b>", wib(t), LINE]


def _rp(r):
    return str(r).replace(".", ",")


def signal(name, t, orders, now_px, conv, berlaku, catatan, risk):
    """orders {pair: [order]}; now_px {pair: harga}; conv {(pair, side): label}."""
    L = _title(name, t)
    pairs = sorted(orders, key=lambda p: (min(RANK[conv.get((p, o["side"]))] for o in orders[p]), p))
    rows, satu, langsung = [], [], []
    for p in pairs:
        lst = sorted(orders[p], key=lambda o: -o["side"]); oco = len(lst) > 1
        if not oco: satu.append(p)
        for o in lst:
            s = o["side"]; jenis = ("BUY " if s > 0 else "SELL ") + {"stop": "STOP", "limit": "LIMIT", "market": "MARKET"}[o["kind"]]
            rows.append(_head(conv.get((p, s)), p, jenis + (" ·OCO" if oco else "")))
            if o is lst[0]: rows.append(f"   Harga : {px(p, now_px[p])}  (sekarang)")
            rows += [f"   Entry : {px(p, o['price'])}  ({pip(p, o['price'], now_px[p])} dari harga)",
                     f"   SL    : {px(p, o['sl'])}  (-{pip(p, o['price'], o['sl'], False)})",
                     f"   TP    : {px(p, o['tp'])}  (+{pip(p, o['tp'], o['price'], False)}, {_rp(round(abs(o['tp'] - o['price']) / abs(o['price'] - o['sl']), 1))}R)"]
            if (s > 0 and now_px[p] >= o["price"]) or (s < 0 and now_px[p] <= o["price"]): langsung.append(f"{p} {jenis}")
        rows.append("")
    L.append(_pre(rows[:-1]))
    if langsung: L.append("⚠️ Harga sudah melewati level: " + ", ".join(langsung) + " → langsung terisi di harga pasar.")
    L += [LINE,
          "🔗 Pair dengan 2 order = <b>OCO</b>: satu terisi → batalkan pasangannya"]
    if satu: L.append(f"ℹ️ {', '.join(satu)}: hanya 1 order karena level sisi lain sudah tertembus kemarin (tidak berlaku)")
    L += catatan + [f"⏰ Berlaku s.d. <b>{berlaku}</b> · semua ditutup <b>23:00 WIB</b>",
                    f"⚖️ Risiko saran {_rp(risk)}% modal per order", LEGEND]
    return "\n".join(L)


def fill(bot, t, conv):
    p = t["pair"]; s = t["side"]
    L = _title(f"ORDER TERISI · {bot}", t["t"])
    L.append(_pre([_head(conv, p, "BUY" if s > 0 else "SELL"),
                   f"   Entry : {px(p, t['entry'])}  ({jam(t['t'])})",
                   f"   SL    : {px(p, t['sl'])}  (-{pip(p, t['entry'], t['sl'], False)})",
                   f"   TP    : {px(p, t['tp'])}  (+{pip(p, t['tp'], t['entry'], False)})"]))
    if bot != "LANJUT": L.append(f"↪️ Batalkan order pasangan (OCO) di <b>{p}</b>")
    if bot == "UTAMA": L.append("🛡 Untung +0,5R → geser SL ke entry (bot mengirim pengingat)")
    return "\n".join(L)


def lanjut(o, t_ref, now_px, conv, risk):
    p = o["pair"]; s = o["side"]
    L = _title("SINYAL LANJUT · MARKET", t_ref)
    L.append(_pre([_head(conv, p, "BUY MARKET" if s > 0 else "SELL MARKET"),
                   f"   Harga : {px(p, now_px)}  (sekarang)",
                   f"   SL    : {pip(p, o['price'], o['sl'], False)} dari entry  (acuan {px(p, o['sl'])})",
                   f"   TP    : {pip(p, o['tp'], o['price'], False)} dari entry  (acuan {px(p, o['tp'])})"]))
    L += [LINE, "🔁 Posisi sebelumnya di pair ini kena TP → masuk lagi searah di harga pasar",
          "👉 Pasang SL & TP sesuai jarak pip di atas dari harga entry Anda",
          f"⚖️ Risiko saran {_rp(risk)}% modal", LEGEND]
    return "\n".join(L)


def be(bot, t, ts):
    p = t["pair"]
    return "\n".join(_title("GESER SL KE ENTRY", ts) + [_pre([f"   {p:<8}{'BUY' if t['side'] > 0 else 'SELL'} ({bot})",
                     f"   Entry : {px(p, t['entry'])}", f"   SL    : {px(p, t['sl'])} → {px(p, t['entry'])}"]),
                     "🛡 Untung sudah +0,5R → SL dipindah ke harga entry (posisi bebas risiko)"])


def keluar(bot, t, exit_px, risk):
    p = t["pair"]; R = t["R"]
    hasil = ("🎯 KENA TP" if t["why"] == "tp" else "❌ KENA SL" if R <= -0.5 else "🟡 IMPAS (SL di entry)" if t["why"] == "sl"
             else "⏹ DITUTUP 23:00")
    L = _title(f"POSISI DITUTUP · {bot}", t["t_exit"] + (3600 if t["why"] == "close" else 0))
    L.append(_pre([f"   {p:<8}{'BUY' if t['side'] > 0 else 'SELL'}",
                   f"   Entry : {px(p, t['entry'])}  ({jam(t['t'])})",
                   f"   Exit  : {px(p, exit_px)}  ({pip(p, (exit_px - t['entry']) * t['side'] + 0, 0)})",
                   f"   Hasil : {_rp(f'{R:+.2f}')}R  (≈ {_rp(f'{R * risk:+.2f}')}%)"]))
    L.append(hasil)
    return "\n".join(L)


def info(name, t, lines):
    return "\n".join(_title(name, t) + lines)


def berjalan(ts, posisi, risk):
    """posisi: list (bot, trade, harga_sekarang, sl_sekarang)."""
    L = _title("UPDATE POSISI BERJALAN", ts); rows = []; tot = 0.0
    for bot, t, now, sl in posisi:
        p = t["pair"]; s = t["side"]; r0 = abs(t["entry"] - t["sl"]); R = s * (now - t["entry"]) / r0; tot += R
        rows += [f"{'🟢' if R >= 0 else '🔴'} {p:<7} {('BUY' if s > 0 else 'SELL') + ' · ' + bot:<14}",
                 f"   Entry : {px(p, t['entry'])}  ({jam(t['t'])})",
                 f"   Harga : {px(p, now)}  ({pip(p, (now - t['entry']) * s, 0)})",
                 f"   SL    : {px(p, sl)}{'  (di entry)' if abs(sl - t['entry']) < 1e-9 else ''} · TP {px(p, t['tp'])}",
                 f"   Float : {_rp(f'{R:+.2f}')}R  (≈ {_rp(f'{R * risk:+.2f}')}%)", ""]
    L.append(_pre(rows[:-1]))
    L += [LINE, f"📊 Total berjalan: <b>{_rp(f'{tot:+.2f}')}R</b> · ⏰ ditutup paling lambat 23:00 WIB"]
    return "\n".join(L)
