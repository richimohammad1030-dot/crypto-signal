"""
Bot sinyal FX MAJOR (EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, USDCHF, NZDUSD) -> Telegram, label [FX MAJOR].
3 bot saling menutup celah (pemilik, 20 Nov 2026; riset forex_major/ putaran 1-7; strategi: riset/fx/STRATEGI.md):
  UTAMA   07:00 WIB (Selasa-Jumat): breakout level minggu lalu, OCO per pair, berlaku s/d 14:00 WIB, maks 2 posisi/hari.
  SUSULAN 15:00 WIB: pasang ulang level untuk pair yang UTAMA-nya tidak terisi, berlaku s/d 23:00 WIB.
  LANJUT  setelah UTAMA/SUSULAN kena TP: market searah.
  Semua ditutup 23:00 WIB. Risiko 0,75%/posisi.
Mesin = forex_major/fx_live.py (fungsi backtest yang sama -> live identik dengan riset). Tiap run: unduh H1 Setra 7 pair,
hitung ulang hari ini dari awal, kirim kejadian yang belum pernah dikirim (kunci di fx_state.json["sent"]).
Tujuan pesan: FX_TUJUAN=kanal (bawaan workflow sejak 20 Nov 2026) -> channel XAU (state.json gold_channel_id); selain itu chat pribadi.
Bot hanya membaca data publik & mengirim pesan; tidak punya akses ke akun broker.
"""
import datetime as dt, json, os, sys, time, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "forex_major"))
import fx_live as F
import backtest as B
from signal_bot import tg_send, http_json
import commands

STATE_FILE = os.path.join(HERE, "fx_state.json")
CRYPTO_STATE = os.path.join(HERE, "state.json")
HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
BULAN = ["", "Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
BAR = "━━━━━━━━━━━━━━━━━━━━"
TAG = "🌐 <b>[FX MAJOR]</b>"
HIST_DAYS = 420          # riwayat H1 yang diunduh (>= 210 hari bursa: EMA200 D1 untuk label conviction)


def fetch(pair, days=HIST_DAYS):
    """Candle H1 Setra yang SUDAH close, [open_s, o, h, l, c]."""
    sym = f"{pair[:3]}%2F{pair[3:]}"; rows = {}; now = time.time()
    start = int((now - days * 86400) * 1000)
    for _ in range(20):
        d = http_json(f"https://setra.id/api/md/candles?symbol={sym}&tf=1h&limit=1000&start={start}").get("data", [])
        if not d: break
        for c in d: rows[c["t"] // 1000] = [c["t"] // 1000, c["o"], c["h"], c["l"], c["c"]]
        nxt = d[-1]["t"] + 3600 * 1000
        if nxt <= start or len(d) < 2: break
        start = nxt
    return [rows[k] for k in sorted(rows) if k + 3600 <= now]


def digits(pair):
    return 3 if pair.endswith("JPY") else 5


def px(pair, v):
    return f"{v:.{digits(pair)}f}"


def wib(ts, fmt="%H:%M"):
    return (dt.datetime.fromtimestamp(ts, dt.timezone.utc) + dt.timedelta(hours=7)).strftime(fmt) + " WIB"


def tanggal(d):
    w = dt.datetime.fromtimestamp(d * 86400, dt.timezone.utc)
    return f"{HARI[w.weekday()]}, {w.day} {BULAN[w.month]} {w.year}"


def arah(side):
    return "BUY" if side > 0 else "SELL"


def key(t):
    return f"{t['strat']}|{t['pair']}|{t['t']}"


def exit_px(t):
    risk = abs(t["entry"] - t["sl"])
    return t["entry"] + t["side"] * (t["R"] + B.SPREAD[t["pair"]] * B.PIP[t["pair"]] / risk) * risk


def be_aktif(P, t, last_t):
    """UTAMA: harga sudah mencapai +0,5R setelah terisi (SL dipindah ke entry)?"""
    trig = t["entry"] + t["side"] * 0.5 * abs(t["entry"] - t["sl"]); H = P.h1
    for i in range(len(H["t"])):
        if H["t"][i] < t["t"] or H["t"][i] > last_t: continue
        if (t["side"] > 0 and H["h"][i] >= trig) or (t["side"] < 0 and H["l"][i] <= trig): return int(H["t"][i])
    return None


def msg_signal(judul, orders, d, catatan):
    L = [BAR, f"{TAG} {judul}", f"🗓 {tanggal(d)}", BAR]
    for pair, lst in sorted(orders.items()):
        L.append(f"<b>{pair}</b>")
        for o in sorted(lst, key=lambda o: -o["side"]):
            jenis = {"stop": "STOP", "limit": "LIMIT", "market": "MARKET"}[o["kind"]]
            L.append(f"  {'🟢' if o['side'] > 0 else '🔴'} {arah(o['side'])} {jenis} <code>{px(pair, o['price'])}</code>"
                     f" · SL <code>{px(pair, o['sl'])}</code> · TP <code>{px(pair, o['tp'])}</code>")
    L += [BAR] + catatan
    return "\n".join(L)


def run():
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
    risk = float(os.environ.get("FX_RISK_PCT") or F.RISK_PCT)
    state = json.load(open(STATE_FILE)) if os.path.exists(STATE_FILE) else {}
    cstate = json.load(open(CRYPTO_STATE)) if os.path.exists(CRYPTO_STATE) else {}
    target = cstate.get("gold_channel_id") if os.environ.get("FX_TUJUAN") == "kanal" else None
    sent_l = list(state.get("sent", [])); sent = set(sent_l); out = []
    diam = not state            # run pertama: tandai kejadian hari ini sebagai terkirim tanpa mengirim (uji maju mulai bersih)
    def send(k, text):
        if k in sent: return
        sent.add(k); sent_l.append(k); out.append(text)
        if not diam: tg_send(text, chat=target)

    data, gagal = [], []
    for p in F.PAIRS:
        try:
            rows = fetch(p)
            if len(rows) < 2000: raise RuntimeError(f"data kurang ({len(rows)} candle)")
            data.append(B.Pair(p, rows))
        except Exception as e:
            gagal.append(f"{p}: {e}")
    if gagal:
        tag = "|".join(gagal)
        if state.get("warn") != tag: tg_send("⚠️ Bot FX MAJOR gagal mengambil data Setra:\n" + "\n".join(gagal)); state["warn"] = tag
        if len(data) < len(F.PAIRS):
            json.dump(dict(state, sent=sent_l[-3000:]), open(STATE_FILE, "w"), indent=1); sys.exit(1)
    else:
        state.pop("warn", None)
    last = max(int(P.t[-1]) for P in data)                 # open candle H1 terakhir yang sudah close
    d = last // 86400
    w = (d + 3) % 7                                        # 0 = Senin
    stale = time.time() - (last + 3600) > 2 * 3600
    if stale and w < 5 and 0 <= (time.time() % 86400) // 3600 < 16:
        if state.get("stale") != last:
            tg_send(f"⚠️ Data FX Setra macet: candle terakhir close {wib(last + 3600, '%a %d %b %H:%M')}."); state["stale"] = last
    r = F.day(data, d)
    selesai = last >= d * 86400 + 15 * 3600              # candle 22:00-23:00 WIB sudah close
    Pm = {P.name: P for P in data}

    import fx_templates as T
    now_px = {P.name: float(P.c[-1]) for P in data}
    conv = {}
    for bot in ("N3", "SUS", "B3"):
        for p, lst in r["orders"][bot].items():
            for o in lst: conv.setdefault((p, o["side"]), F.conviction(Pm[p], d, o["side"])[0])
    cv = lambda t: conv.get((t["pair"], t["side"]))
    # 1) sinyal UTAMA (sekali per hari)
    if r["orders"]["N3"]:
        send(f"SIG|N3|{d}", T.signal("SINYAL UTAMA · 07:00", d * 86400, r["orders"]["N3"], now_px, conv, "14:00 WIB",
             ["🛡 Untung +0,5R → geser SL ke entry",
              "📦 Maks <b>2 posisi</b>/hari · 1 per pair · maks 2 searah USD"], risk))
    # 2) terisi + kuota
    for bot in ("N3", "SUS", "B3"):
        for t in r["trades"][bot]:
            send(f"FILL|{key(t)}", T.fill(F.NAMA[bot], t, cv(t)))
    if len(r["trades"]["N3"]) >= 2:
        send(f"KUOTA|{d}", T.info("KUOTA UTAMA PENUH", last + 3600, ["🔒 2 posisi UTAMA hari ini sudah terisi → <b>batalkan semua order UTAMA lain</b>"]))
    blok = [t for t in r["raw_utama"] if key(t) not in {key(x) for x in r["trades"]["N3"]}]
    for t in blok:
        if len(r["trades"]["N3"]) < 2:
            send(f"BLOK|{key(t)}", T.info("ORDER TIDAK DIAMBIL", last + 3600, [f"⛔ {t['pair']} {arah(t['side'])} (UTAMA): sudah ada 2 posisi searah USD → batalkan order {t['pair']}"]))
    # 3) kadaluarsa UTAMA 14:00 WIB
    if r["orders"]["N3"] and last >= d * 86400 + 6 * 3600:
        isi = {t["pair"] for t in r["trades"]["N3"]}
        sisa = [p for p in r["orders"]["N3"] if p not in isi]
        if sisa: send(f"EXP|N3|{d}", T.info("ORDER UTAMA KADALUARSA", d * 86400 + 7 * 3600,
                      [f"⌛ Batalkan order UTAMA yang belum terisi: <b>{', '.join(sorted(sisa))}</b>", "🔁 Sinyal susulan dikirim setelah candle 15:00 WIB"]))
    # 4) sinyal SUSULAN (15:00 WIB)
    if r["orders"]["SUS"]:
        send(f"SIG|SUS|{d}", T.signal("SINYAL SUSULAN · 15:00", d * 86400 + 8 * 3600, r["orders"]["SUS"], now_px, conv, "23:00 WIB",
             ["🔁 Pengganti order UTAMA yang tidak terisi (level minggu lalu dipasang ulang)"], risk))
    # 5) LANJUT (market setelah TP)
    for pair, lst in r["orders"]["B3"].items():
        for o in lst:
            send(f"SIG|B3|{pair}|{o['t_on']}", T.lanjut(dict(o), o["t_on"], now_px[pair], conv.get((pair, o["side"])), risk))
    # 6) BE, keluar, tutup 23:00
    hist = state.setdefault("hist", [])
    for bot in ("N3", "SUS", "B3"):
        for t in r["trades"][bot]:
            if bot == "N3":
                tb = be_aktif(Pm[t["pair"]], t, min(last, t["t_exit"]) if t["why"] != "close" or selesai else last)
                if tb is not None and (t["why"] == "close" or t["t_exit"] > tb):
                    send(f"BE|{key(t)}", T.be(F.NAMA[bot], t, tb + 3600))
            if t["why"] == "close" and not selesai: continue          # masih terbuka
            k = f"EXIT|{key(t)}"
            if k not in sent and not diam:
                hist.append([t["pair"], t["side"], t["t"], t["t_exit"], round(float(t["entry"]), 6), round(float(exit_px(t)), 6), round(float(t["R"]), 3), bot])
            send(k, T.keluar(F.NAMA[bot], t, exit_px(t), risk))
    if selesai and any(r["trades"].values()):
        send(f"TUTUP|{d}", T.info("TUTUP HARIAN", d * 86400 + 16 * 3600, ["🔚 Semua order & posisi FX MAJOR hari ini ditutup"]))
    # 7) rekap mingguan Jumat 23:00 (+ cadangan Senin) & bulanan
    now_wib = dt.datetime.now(commands.WIB)
    this_wk, _ = commands.period_bounds("minggu", now_wib); wk, _ = commands.period_bounds("minggu", now_wib, previous=True)
    if w == 4 and selesai and state.get("recap_week") != this_wk.isoformat():
        tg_send(commands.build_recap(state, "minggu", True, risk, now_wib + dt.timedelta(days=3), lambda x: f"{x:g}").replace("REKAP", "REKAP FX MAJOR"), chat=target)
        state["recap_week"] = this_wk.isoformat()
    elif now_wib.weekday() == 0 and state.get("recap_week") not in (wk.isoformat(), this_wk.isoformat()) and hist:
        tg_send(commands.build_recap(state, "minggu", True, risk, now_wib, lambda x: f"{x:g}").replace("REKAP", "REKAP FX MAJOR"), chat=target)
        state["recap_week"] = wk.isoformat()
    mo, _ = commands.period_bounds("bulan", now_wib, previous=True)
    if now_wib.day <= 3 and state.get("recap_month") != mo.isoformat() and hist:
        tg_send(commands.build_recap(state, "bulan", True, risk, now_wib, lambda x: f"{x:g}").replace("REKAP", "REKAP FX MAJOR"), chat=target)
        state["recap_month"] = mo.isoformat()
    state["sent"] = sent_l[-3000:]; state["last"] = last
    state["live_start"] = state.get("live_start") or int(time.time())
    json.dump(state, open(STATE_FILE, "w"), indent=1)
    print(*out, sep="\n\n")


if __name__ == "__main__":
    run()
