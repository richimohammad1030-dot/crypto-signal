"""
Bot sinyal "Crypto Futures Trend" -> notifikasi Telegram.

Aturan (sama dengan versi terbaik hasil backtest 2020-2026):
- Data: candle H1 (harga spot Binance), dicek setiap 4 jam pada candle yang sudah close
  (03:00, 07:00, 11:00, 15:00, 19:00, 23:00 WIB).
- Trend naik : close > EMA200 dan EMA100 > EMA200  -> BUY STOP di high 480 candle (20 hari)
- Trend turun: close < EMA200 dan EMA100 < EMA200  -> SELL STOP di low 480 candle,
               HANYA jika funding rata-rata 72 jam terakhir > 0
- SL awal 8 x ATR(14). Tanpa TP.
- Setiap cek: SL digeser ke low 72 candle (long) / high 72 candle (short), hanya ke arah untung.
- Maksimal 10 slot (posisi terbuka + order pending). Prioritas sesuai peringkat market cap.

Bot ini hanya membaca data publik dan mengirim pesan. Bot TIDAK punya akses ke akun exchange.
"""
import json, os, sys, time, urllib.request, urllib.parse, datetime as dt

COINS = "BTC ETH BNB XRP SOL TRX ZEC DOGE LINK ADA NEAR XLM BCH LTC UNI AVAX SUI HBAR TAO SHIB ENA QNT AAVE ONDO".split()
HL_NAME = {"SHIB": "kSHIB"}            # nama koin di Hyperliquid (sumber funding)
K, SL_ATR, TRAIL, EMA_F, EMA_S, ATR_N = 480, 8.0, 72, 100, 200, 14
CHECK_HOURS_UTC = {3, 7, 11, 15, 19, 23}  # jam BUKA candle H1 (UTC); candle close = 03,07,11,15,19,23 WIB
MAX_SLOTS = 10
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state.json")

# ---------------------------------------------------------------- utilitas
def http_json(url, data=None, tries=5):
    for t in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as e:
            err = e
            time.sleep(3 * (t + 1))
    raise RuntimeError(f"Gagal mengambil data: {url} ({err})")

def fetch_klines(coin, n=1800):
    """Candle H1 spot Binance (data publik). Return list [open_time_s, o, h, l, c] candle yang SUDAH close."""
    sym = coin + "USDT"
    out = []
    end = None
    while len(out) < n:
        url = f"https://data-api.binance.vision/api/v3/klines?symbol={sym}&interval=1h&limit=1000" + (f"&endTime={end}" if end else "")
        d = http_json(url)
        if not d:
            break
        rows = [[k[0] // 1000, float(k[1]), float(k[2]), float(k[3]), float(k[4]), k[6]] for k in d]
        out = rows + out
        end = d[0][0] - 1
        if len(d) < 1000:
            break
    now_ms = int(time.time() * 1000)
    out = [r[:5] for r in out if r[5] < now_ms]          # buang candle yang belum close
    dedup = {r[0]: r for r in out}
    return [dedup[k] for k in sorted(dedup)]

def fetch_funding_avg(coin, t_end):
    """Rata-rata funding 72 jam terakhir (Hyperliquid, per jam). None jika tidak tersedia."""
    name = HL_NAME.get(coin, coin)
    try:
        d = http_json("https://api.hyperliquid.xyz/info", json.dumps({"type": "fundingHistory", "coin": name, "startTime": (t_end - 72 * 3600) * 1000}).encode())
    except Exception:
        return None
    rates = [float(x["fundingRate"]) for x in d if x["time"] // 1000 <= t_end]
    return sum(rates) / len(rates) if len(rates) >= 24 else None

def ema(src, n):
    a = 2 / (n + 1); o = [src[0]]
    for v in src[1:]:
        o.append(a * v + (1 - a) * o[-1])
    return o

def atr(H, L, C, n=ATR_N):
    tr = [H[0] - L[0]] + [max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1])) for i in range(1, len(C))]
    o = [tr[0]]
    for v in tr[1:]:
        o.append((o[-1] * (n - 1) + v) / n)
    return o

def fmt(p):
    if p >= 1000: return f"{p:,.1f}"
    if p >= 1: return f"{p:,.4f}"
    return f"{p:.6g}"

def wib(ts):
    return (dt.datetime.fromtimestamp(ts, dt.timezone.utc) + dt.timedelta(hours=7)).strftime("%d %b %H:%M WIB")


def safe_lev(entry, sl):
    """Leverage maksimal agar harga likuidasi (isolated) jauh di luar SL: <= 50% jarak likuidasi, maks 5x."""
    dist = abs(entry - sl) / entry
    return max(1, min(5, int(0.5 / dist))) if dist > 0 else 1

def exit_label(R):
    if R <= -0.9:
        return f"❌ Kena SL awal ({R:+.2f}R)"
    if abs(R) < 0.15:
        return f"🟡 SL+ impas ({R:+.2f}R)"
    if R > 0:
        return f"✅ SL+ untung ({R:+.2f}R)"
    return f"⚠️ Rugi sebagian ({R:+.2f}R)"

# ---------------------------------------------------------------- mesin strategi
class Engine:
    """Memproses candle satu per satu, sama persis dengan urutan di backtest.
       state per koin: {"pend": [dir, entry, sl] | None, "pos": [dir, entry, sl, bar_time] | None}"""
    def __init__(self, state, funding_fn, notify):
        self.s = state
        self.funding_fn = funding_fn
        self.notify = notify
        self.trades = []

    def open_count(self):
        return sum(1 for c in self.s["coins"].values() if c.get("pos"))

    def slots_used(self):
        return sum(1 for c in self.s["coins"].values() if c.get("pos") or c.get("pend"))

    def step_fill_exit(self, coin, i, D):
        """Langkah 1-2 di satu candle: cek order terisi / posisi kena SL."""
        cs = self.s["coins"].setdefault(coin, {"pend": None, "pos": None})
        T, O, H, L = D["T"][i], D["O"][i], D["H"][i], D["L"][i]
        if cs.get("pos") is None and cs.get("pend"):
            d, en, sl = cs["pend"]
            if (d == 1 and H >= en) or (d == -1 and L <= en):
                fill = max(en, O) if d == 1 else min(en, O)
                cs["pend"] = None
                cs["pos"] = [d, fill, sl, T, abs(fill - sl)]
                self.notify("fill", coin, d=d, entry=fill, sl=sl, t=T)
                # Batas slot tercapai -> order pending koin lain dibatalkan
                if self.open_count() >= MAX_SLOTS:
                    for c2, st2 in self.s["coins"].items():
                        if st2.get("pend"):
                            st2["pend"] = None
                            self.notify("cancel", c2, reason="batas 10 posisi tercapai")
                if (d == 1 and L <= sl) or (d == -1 and H >= sl):
                    self.close(coin, sl, T, "SL di candle yang sama")
        elif cs.get("pos") is not None and cs["pos"][3] < T:
            d, e, sl, t0 = cs["pos"][:4]
            if (d == 1 and L <= sl) or (d == -1 and H >= sl):
                ex = min(sl, O) if d == 1 else max(sl, O)
                self.close(coin, ex, T, "kena SL")

    def close(self, coin, ex, T, why):
        cs = self.s["coins"][coin]
        d, e, sl, t0 = cs["pos"][:4]
        r0 = cs["pos"][4] if len(cs["pos"]) > 4 else abs(e - sl)
        self.trades.append((coin, d, t0, T, e, ex))
        cs["pos"] = None
        R = (ex - e) * d / r0 if r0 else 0.0
        self.s.setdefault("hist", []).append([coin, d, t0, T, e, ex, round(R, 3)])
        self.notify("exit", coin, d=d, entry=e, exit=ex, t=T, why=why, R=R)

    def step_check(self, coin, i, D, allow_new):
        """Langkah 3 di candle cek (setiap 4 jam): trailing SL / order baru."""
        cs = self.s["coins"].setdefault(coin, {"pend": None, "pos": None})
        C, H, L, A, EF, ES, T = D["C"], D["H"], D["L"], D["A"], D["EF"], D["ES"], D["T"][i]
        if cs.get("pos") is not None:
            d, e, sl, t0 = cs["pos"][:4]
            if d == 1:
                v = min(L[i - TRAIL + 1:i + 1])
                if v > sl:
                    cs["pos"][2] = v; self.notify("trail", coin, d=d, sl=v, old=sl, t=T)
            else:
                v = max(H[i - TRAIL + 1:i + 1])
                if v < sl:
                    cs["pos"][2] = v; self.notify("trail", coin, d=d, sl=v, old=sl, t=T)
            return
        old = cs.get("pend")
        new = None
        if C[i] > ES[i] and EF[i] > ES[i]:
            en = max(H[i - K + 1:i + 1]); new = [1, en, en - SL_ATR * A[i]]
        elif C[i] < ES[i] and EF[i] < ES[i]:
            f = self.funding_fn(coin, T)
            if f is not None and f > 0:
                en = min(L[i - K + 1:i + 1]); new = [-1, en, en + SL_ATR * A[i]]
        if new and not allow_new(coin, old):
            new = None
        if old and not new:
            self.notify("cancel", coin, reason="trend/filter tidak lagi terpenuhi atau slot penuh")
        elif new and (not old or abs(new[1] - old[1]) > 1e-12 or abs(new[2] - old[2]) > 1e-12 or new[0] != old[0]):
            self.notify("order", coin, d=new[0], entry=new[1], sl=new[2], t=T, replace=bool(old))
        cs["pend"] = new

    def run(self, data, since_ts):
        """Proses semua candle yang sudah close setelah since_ts, urut waktu lintas koin."""
        times = sorted({t for D in data.values() for t in D["T"] if t > since_ts})
        idx = {c: {t: i for i, t in enumerate(D["T"])} for c, D in data.items()}
        last = since_ts
        for t in times:
            for coin in COINS:
                if coin in data and t in idx[coin]:
                    i = idx[coin][t]
                    if i >= max(K, 1300 if self.s.get("replay") else K):
                        self.step_fill_exit(coin, i, data[coin])
            if (t // 3600) % 24 in CHECK_HOURS_UTC:
                # alokasi slot: prioritas peringkat market cap
                for coin in COINS:
                    if coin in data and t in idx[coin]:
                        i = idx[coin][t]
                        if i >= max(K, 1300 if self.s.get("replay") else K):
                            def allow(c, old, coin=coin):
                                used = self.slots_used() - (1 if self.s["coins"][c].get("pend") else 0)
                                return used < MAX_SLOTS
                            self.step_check(coin, i, data[coin], allow)
            last = t
        self.s["last_ts"] = last

def prep(rows):
    T = [r[0] for r in rows]; O = [r[1] for r in rows]; H = [r[2] for r in rows]; L = [r[3] for r in rows]; C = [r[4] for r in rows]
    return dict(T=T, O=O, H=H, L=L, C=C, A=atr(H, L, C), EF=ema(C, EMA_F), ES=ema(C, EMA_S))

# ---------------------------------------------------------------- Telegram
def tg_send(text, chat=None, pin=False):
    """Kirim pesan. chat=None -> chat pribadi pemilik. pin=True -> sematkan pesan (butuh izin admin)."""
    tok = os.environ.get("TELEGRAM_TOKEN")
    chat = chat or os.environ.get("TELEGRAM_CHAT_ID")
    if not tok or not chat:
        print("[TELEGRAM belum diatur]\n" + text); return None
    data = urllib.parse.urlencode({"chat_id": chat, "text": text, "parse_mode": "HTML", "disable_web_page_preview": "true"}).encode()
    for t in range(3):
        try:
            with urllib.request.urlopen(f"https://api.telegram.org/bot{tok}/sendMessage", data=data, timeout=30) as r:
                msg = json.load(r).get("result", {})
            if pin and msg.get("message_id"):
                pdata = urllib.parse.urlencode({"chat_id": chat, "message_id": msg["message_id"], "disable_notification": "true"}).encode()
                try:
                    urllib.request.urlopen(f"https://api.telegram.org/bot{tok}/pinChatMessage", data=pdata, timeout=30)
                except Exception as e:
                    print("Gagal pin pesan:", e)
            return msg
        except Exception as e:
            time.sleep(3)
    print("Gagal kirim Telegram:", text)
    return None

def make_notifier(buf, risk_pct, modal, priv=None):
    """buf: pesan publik (channel). priv: ukuran posisi pribadi pemilik (dari MODAL_USDT), tidak dikirim ke channel."""
    def size_line(entry, sl):
        dist = abs(entry - sl) / entry * 100
        return f"Jarak SL {dist:.1f}% · leverage maks aman {safe_lev(entry, sl)}× (isolated)"
    def notify(kind, coin, **k):
        sym = coin + "USDT"
        if kind == "order":
            arah = "🟢 BUY STOP" if k["d"] == 1 else "🔴 SELL STOP"
            buf.append(f"{'♻️ GANTI ' if k['replace'] else '🆕 '}<b>{sym}</b> {arah} <b>{fmt(k['entry'])}</b>\nSL {fmt(k['sl'])} · tanpa TP\n{size_line(k['entry'], k['sl'])}")
            if modal and priv is not None:
                risk_usd = modal * risk_pct / 100
                qty = risk_usd / abs(k["entry"] - k["sl"])
                priv.append(f"• {sym} {'BUY' if k['d']==1 else 'SELL'} STOP {fmt(k['entry'])}: ukuran ±{qty:.6g} koin (nilai ±{qty*k['entry']:,.0f} USDT, risiko {risk_usd:,.2f} USDT)")
        elif kind == "cancel":
            buf.append(f"❌ <b>{sym}</b> batalkan order pending ({k['reason']})")
        elif kind == "fill":
            buf.append(f"✅ <b>{sym}</b> order {'BUY' if k['d']==1 else 'SELL'} kemungkinan TERISI di ±{fmt(k['entry'])} ({wib(k['t'])}). Pastikan SL {fmt(k['sl'])} terpasang.")
        elif kind == "trail":
            buf.append(f"⬆️ <b>{sym}</b> geser SL {'BUY' if k['d']==1 else 'SELL'}: {fmt(k['old'])} → <b>{fmt(k['sl'])}</b>")
        elif kind == "exit":
            buf.append(f"🏁 <b>{sym}</b> posisi {'BUY' if k['d']==1 else 'SELL'} selesai di ±{fmt(k['exit'])} ({k['why']})\n{exit_label(k['R'])}")
    return notify

# ---------------------------------------------------------------- main
def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    risk_pct = float(os.environ.get("RISK_PCT") or "0.67")
    modal = float(os.environ.get("MODAL_USDT") or 0)
    if os.path.exists(STATE_FILE):
        state = json.load(open(STATE_FILE))
    else:
        state = {"coins": {}, "last_ts": 0}

    # 1) Perintah Telegram dari pemilik (/status, /terisi, /tidak, /tutup, /panduan)
    import commands
    def last_price(coin):
        try:
            d = http_json(f"https://data-api.binance.vision/api/v3/ticker/price?symbol={coin}USDT")
            return float(d["price"])
        except Exception:
            return None
    for text in commands.fetch_commands(state):
        try:
            reply = commands.handle(state, text, last_price, fmt, exit_label, wib)
        except Exception as e:
            reply = f"⚠️ Gagal memproses perintah: {e}"
        if reply == "/_kirim_panduan":
            ok = tg_send(commands.PANDUAN_ANGGOTA, chat=state["channel_id"], pin=True)
            reply = "📌 Panduan anggota sudah diposting & di-pin di channel." if ok else "⚠️ Gagal posting panduan. Pastikan bot admin channel dengan izin Post & Pin Messages."
        tg_send(reply)
    if os.environ.get("MODE") == "cmd":
        json.dump(state, open(STATE_FILE, "w"), indent=1)
        return

    # 2) Cek sinyal (setiap 4 jam)
    data = {}
    errors = []
    for c in COINS:
        try:
            rows = fetch_klines(c)
            if len(rows) > K + 50:
                data[c] = prep(rows)
        except Exception as e:
            errors.append(f"{c}: {e}")
    if not data:
        tg_send("⚠️ Bot sinyal gagal mengambil data harga. " + "; ".join(errors[:3])); sys.exit(1)
    newest = max(D["T"][-1] for D in data.values())
    first_run = state["last_ts"] == 0
    since = state["last_ts"] if not first_run else newest - 3600   # run pertama: hanya candle terakhir
    fcache = {}
    def funding(coin, t):
        key = (coin, t)
        if key not in fcache:
            fcache[key] = fetch_funding_avg(coin, t)
        return fcache[key]
    buf, priv = [], []
    eng = Engine(state, funding, make_notifier(buf, risk_pct, modal, priv))
    if first_run:
        # Run pertama: bentuk order awal di candle cek terakhir agar langsung ada daftar order
        last_check = max(t for t in data["BTC"]["T"] if (t // 3600) % 24 in CHECK_HOURS_UTC)
        since = last_check - 1
    eng.run(data, since)
    json.dump(state, open(STATE_FILE, "w"), indent=1)
    head = f"📊 <b>Sinyal Crypto Futures</b> · candle s.d. {wib(newest + 3600)}\nPosisi terbuka: {eng.open_count()} · order pending: {sum(1 for c in state['coins'].values() if c.get('pend'))} (maks {MAX_SLOTS})"
    # Sinyal publik -> channel (jika bot sudah admin channel), jika belum -> chat pribadi pemilik
    target = state.get("channel_id")
    if errors:
        tg_send("⚠️ Data gagal diambil untuk: " + ", ".join(e.split(':')[0] for e in errors))
    if buf:
        msgs, cur = [], head
        for line in buf:
            if len(cur) + len(line) > 3500:
                msgs.append(cur); cur = ""
            cur += "\n\n" + line
        msgs.append(cur)
        for m in msgs:
            tg_send(m, chat=target)
    elif os.environ.get("SEND_EMPTY", "0") == "1":
        tg_send(head + "\n\nTidak ada perubahan.", chat=target)
    # Ukuran posisi pribadi (MODAL_USDT) hanya ke chat pemilik
    if priv:
        tg_send("🔒 <b>Ukuran posisi Anda</b> (modal " + f"{modal:,.0f} USDT, risiko {risk_pct}%)\n" + "\n".join(priv))
    print(head, *buf, *priv, sep="\n\n")

if __name__ == "__main__":
    main()
