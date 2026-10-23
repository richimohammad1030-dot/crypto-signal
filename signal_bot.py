"""
Bot sinyal "Crypto Futures Trend" -> notifikasi Telegram.

Aturan (sama dengan versi terbaik hasil backtest 2020-2026):
- Data: candle H1 (harga spot Binance), dicek setiap 4 jam pada candle yang sudah close
  (03:00, 07:00, 11:00, 15:00, 19:00, 23:00 WIB).
- Trend naik : close > EMA200 dan EMA100 > EMA200  -> BUY STOP di high 480 candle (20 hari)
- Trend turun: close < EMA200 dan EMA100 < EMA200  -> SELL STOP di low 480 candle,
               HANYA jika funding rata-rata 72 jam terakhir > 0
- SL awal 8 x ATR(14) = 1R. Rugi maksimum 1R per trade.
- TP sebagian: 25% posisi ditutup saat harga mencapai entry ± 1R (dicek setiap candle). Sisa 75% tanpa TP.
- Setiap cek: SL digeser ke low 72 candle (long) / high 72 candle (short), hanya ke arah untung.
- Cut-loss stagnan: setiap cek, posisi yang sudah >= 2 hari dan R berjalan < -0,2R ditutup di harga close.
- Maksimal 10 slot (posisi terbuka + order pending). Prioritas sesuai peringkat market cap.
- Risiko default 1% modal per trade (variable RISK_PCT).
Versi 24 Okt 2026 (riset 23 Okt): cut-loss stagnan + TP 25% di 1R, replay penuh 2019-2026.

Bot ini hanya membaca data publik dan mengirim pesan. Bot TIDAK punya akses ke akun exchange.
"""
import json, os, sys, time, urllib.request, urllib.parse, datetime as dt

# 50 koin teratas CoinMarketCap (tanpa stablecoin/token emas) yang aktif di Binance, urut market cap
COINS = "BTC ETH BNB XRP SOL TRX HYPE ZEC DOGE LINK ADA NEAR XLM BCH LTC UNI AVAX SUI GRAM HBAR TAO SHIB ENA AAVE QNT ONDO PUMP ASTER DOT WLD WLFI SKY PEPE ICP ARB MORPHO ETC JST ALGO POL JUP RENDER ATOM FIL INJ AERO ZRO CAKE APT NIGHT".split()
HL_NAME = {"SHIB": "kSHIB", "PEPE": "kPEPE"}            # nama koin di Hyperliquid (sumber funding)
K, SL_ATR, TRAIL, EMA_F, EMA_S, ATR_N = 480, 8.0, 72, 100, 200, 14
CHECK_HOURS_UTC = {3, 7, 11, 15, 19, 23}  # jam BUKA candle H1 (UTC); candle close = 03,07,11,15,19,23 WIB
MAX_SLOTS = 10
TP1_R, TP1_FRAC = 1.0, 0.25          # TP sebagian: 25% posisi di entry ± 1R
STAG_DAYS, STAG_R = 2.0, -0.2        # cut-loss stagnan: umur >= 2 hari dan R berjalan < -0,2R
DEFAULT_RISK_PCT = "1"
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

def fetch_klines(coin, n=1000):
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

NEWS_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"   # kalender ekonomi ForexFactory (publik)
NEWS_WINDOW_H = 3   # peringatan untuk event dalam 3 jam ke depan (bot berjalan tiap 2 jam)

def upcoming_news(now_ts, window_h=NEWS_WINDOW_H):
    """Event USD berdampak tinggi dalam window_h jam ke depan: list (t, judul, forecast, previous). [] jika gagal."""
    try:
        d = http_json(NEWS_URL, tries=2)
    except Exception as e:
        print("Kalender news gagal diambil:", e)
        return []
    out = []
    for e in d:
        if e.get("country") != "USD" or e.get("impact") != "High":
            continue
        try:
            t = dt.datetime.fromisoformat(e["date"]).timestamp()
        except Exception:
            continue
        if now_ts < t <= now_ts + window_h * 3600:
            out.append((int(t), e.get("title", ""), e.get("forecast", ""), e.get("previous", "")))
    return sorted(out)

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


# Label conviction (hasil backtest 2020-2026, divalidasi in-sample 2020-2023 vs out-of-sample 2024-2026).
# Skor = jarak SL % (kecil +1, besar -1) + jarak harga dari EMA200 dalam ATR (dekat +1, jauh -1)
#      + peringkat market cap (top 7 +1, di luar 15 besar -1) + tren BTC (searah +1, berlawanan -1).
# HIGH skor >= 2 · MEDIUM 0..1 · LOW <= -1. Semua sinyal tetap sah; label hanya kualitas historis setup.
CONV_SL, CONV_EXT, CONV_RANK = (7.88, 12.63), (4.23, 5.55), (7, 15)

def _regime(D, i):
    C, EF, ES = D["C"][i], D["EF"][i], D["ES"][i]
    return 1 if (C > ES and EF > ES) else -1 if (C < ES and EF < ES) else 0

def conviction_detail(data, coin, t, d, entry, sl):
    """(label, faktor) untuk order di candle cek t. label None jika data tidak cukup.
    faktor dicatat di jurnal agar bisa dianalisis ulang di review bulanan."""
    import bisect
    D = data.get(coin)
    if not D:
        return None, {}
    i = bisect.bisect_right(D["T"], t) - 1
    if i < 0 or D["A"][i] <= 0:
        return None, {}
    A = D["A"][i]
    f = dict(slpct=round(abs(entry - sl) / entry * 100, 3),
             ext=round(d * (D["C"][i] - D["ES"][i]) / A, 3),
             trend=round(d * (D["EF"][i] - D["ES"][i]) / A, 3),
             dist=round(abs(entry - D["C"][i]) / A, 3),
             mom20=round(d * (D["C"][i] / D["C"][i - 480] - 1) * 100, 3) if i >= 480 else None,
             rank=COINS.index(coin), btc=0)
    B = data.get("BTC")
    if B:
        j = bisect.bisect_right(B["T"], t) - 1
        if j >= 0:
            f["btc"] = _regime(B, j) * d
    pts = lambda x, ab: 1 if x < ab[0] else -1 if x > ab[1] else 0
    s = pts(f["slpct"], CONV_SL) + pts(f["ext"], CONV_EXT) + pts(f["rank"], CONV_RANK) + f["btc"]
    f["skor"] = s
    return ("HIGH" if s >= 2 else "LOW" if s <= -1 else "MEDIUM"), f

def conviction(data, coin, t, d, entry, sl):
    """Label HIGH / MEDIUM / LOW untuk order di candle cek t. None jika data tidak cukup."""
    return conviction_detail(data, coin, t, d, entry, sl)[0]

def mfe_mae_safe(D, t0, t1, d, e, r0):
    import jurnal
    try:
        return jurnal.mfe_mae(D.get("T", []), D.get("H", []), D.get("L", []), t0, t1, d, e, r0)
    except Exception:
        return None, None

def safe_lev(entry, sl):
    """Leverage maksimal agar harga likuidasi (isolated) jauh di luar SL: <= 50% jarak likuidasi, maks 5x."""
    dist = abs(entry - sl) / entry
    return max(1, min(5, int(0.5 / dist))) if dist > 0 else 1

def pos_ext(p):
    """Info tambahan posisi (elemen ke-6): {'part': porsi TP sebagian, 'partR': R porsi itu, 'partPx', 'partT'}."""
    return p[5] if len(p) > 5 and isinstance(p[5], dict) else {}

def pos_r0(p):
    return p[4] if len(p) > 4 else abs(p[1] - p[2])

def blended_R(p, px):
    """R gabungan posisi di harga px: porsi TP sebagian (jika sudah diambil) + sisa posisi."""
    d, e, r0, ext = p[0], p[1], pos_r0(p), pos_ext(p)
    rest = (px - e) * d / r0 if r0 else 0.0
    part = ext.get("part", 0.0)
    return part * ext.get("partR", 0.0) + (1 - part) * rest

def tp1_price(d, e, r0):
    return e + d * TP1_R * r0

def exit_label(R, why=""):
    if "stagnan" in (why or ""):
        return f"✂️ Cut-loss stagnan ({R:+.2f}R)"
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
        self.checked = False   # True jika ada candle cek (setiap 4 jam) yang diproses di run ini

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
                self.notify("fill", coin, d=d, entry=fill, sl=sl, t=T, r0=abs(fill - sl))
                # Batas slot tercapai -> order pending koin lain dibatalkan
                if self.open_count() >= MAX_SLOTS:
                    for c2, st2 in self.s["coins"].items():
                        if st2.get("pend"):
                            st2["pend"] = None
                            self.notify("cancel", c2, reason="batas 10 posisi tercapai")
                if (d == 1 and L <= sl) or (d == -1 and H >= sl):
                    self.close(coin, sl, T, "SL di candle yang sama")
        elif cs.get("pos") is not None and cs["pos"][3] < T:
            p = cs["pos"]
            d, e, sl, t0 = p[:4]
            if (d == 1 and L <= sl) or (d == -1 and H >= sl):     # SL dicek lebih dulu (konservatif)
                ex = min(sl, O) if d == 1 else max(sl, O)
                self.close(coin, ex, T, "kena SL")
                return
            r0 = pos_r0(p)
            if r0 and not pos_ext(p).get("part"):
                lvl = tp1_price(d, e, r0)
                if (d == 1 and H >= lvl) or (d == -1 and L <= lvl):
                    px = max(lvl, O) if d == 1 else min(lvl, O)
                    while len(p) < 5:
                        p.append(r0)
                    info = {"part": TP1_FRAC, "partR": (px - e) * d / r0, "partPx": px, "partT": T}
                    if len(p) > 5 and isinstance(p[5], dict):
                        p[5].update(info)
                    else:
                        p.append(info)
                    self.notify("partial", coin, d=d, entry=e, px=px, t=T, R=info["partR"], frac=TP1_FRAC, sl=sl, r0=r0)

    def close(self, coin, ex, T, why):
        cs = self.s["coins"][coin]
        p = cs["pos"]
        d, e, sl, t0 = p[:4]
        r0, ext = pos_r0(p), pos_ext(p)
        self.trades.append((coin, d, t0, T, e, ex))
        cs["pos"] = None
        R = blended_R(p, ex)
        self.s.setdefault("hist", []).append([coin, d, t0, T, e, ex, round(R, 3)])
        self.notify("exit", coin, d=d, entry=e, exit=ex, t=T, why=why, R=R, t0=t0, sl=sl, r0=r0,
                    part=ext.get("part", 0.0), partR=ext.get("partR"))

    def step_check(self, coin, i, D, allow_new):
        """Langkah 3 di candle cek (setiap 4 jam): trailing SL / order baru."""
        cs = self.s["coins"].setdefault(coin, {"pend": None, "pos": None})
        C, H, L, A, EF, ES, T = D["C"], D["H"], D["L"], D["A"], D["EF"], D["ES"], D["T"][i]
        if cs.get("pos") is not None:
            d, e, sl, t0 = cs["pos"][:4]
            r0 = pos_r0(cs["pos"])
            # Cut-loss stagnan: posisi >= 2 hari yang masih rugi > 0,2R ditutup di harga close candle cek
            if r0 and (T - t0) / 86400 >= STAG_DAYS and (C[i] - e) * d / r0 < STAG_R:
                self.close(coin, C[i], T, "cut-loss stagnan")
                return
            if d == 1:
                v = min(L[i - TRAIL + 1:i + 1])
                if v > sl:
                    cs["pos"][2] = v; self.notify("trail", coin, d=d, sl=v, old=sl, t=T, entry=e, r0=(cs["pos"][4] if len(cs["pos"]) > 4 else abs(e - sl)))
            else:
                v = max(H[i - TRAIL + 1:i + 1])
                if v < sl:
                    cs["pos"][2] = v; self.notify("trail", coin, d=d, sl=v, old=sl, t=T, entry=e, r0=(cs["pos"][4] if len(cs["pos"]) > 4 else abs(e - sl)))
            return
        old = cs.get("pend")
        new = None
        reason = "trend sudah tidak searah (EMA)"
        if C[i] > ES[i] and EF[i] > ES[i]:
            en = max(H[i - K + 1:i + 1]); new = [1, en, en - SL_ATR * A[i]]
        elif C[i] < ES[i] and EF[i] < ES[i]:
            f = self.funding_fn(coin, T)
            if f is not None and f > 0:
                en = min(L[i - K + 1:i + 1]); new = [-1, en, en + SL_ATR * A[i]]
            else:
                reason = "funding rate tidak positif (filter SELL)"
        if new and not allow_new(coin, old):
            new = None; reason = "slot penuh (maks 10 posisi/order)"
        if old and not new:
            self.notify("cancel", coin, reason=reason)
        elif new and (not old or abs(new[1] - old[1]) > 1e-12 or abs(new[2] - old[2]) > 1e-12 or new[0] != old[0]):
            self.notify("order", coin, d=new[0], entry=new[1], sl=new[2], t=T, replace=bool(old), old=old, price=C[i])
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
                self.checked = True
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

def new_events():
    return {"new": [], "upd": [], "cancel": [], "fill": [], "trail": [], "exit": [], "partial": []}

def make_notifier(ev, risk_pct, modal, priv=None):
    """ev: kumpulan kejadian (disusun menjadi 2 bubble). priv: ukuran posisi pribadi pemilik (MODAL_USDT)."""
    def notify(kind, coin, **k):
        sym = coin + "USDT"
        if kind == "order":
            lev = safe_lev(k["entry"], k["sl"])
            if k.get("old"):
                o = k["old"]
                # Hanya laporkan update jika harga entry atau arah berubah (SL final diberikan saat order TERISI)
                if not (abs(k["entry"] - o[1]) / k["entry"] > 1e-9 or k["d"] != o[0]):
                    return
                ev["upd"].append((sym, k["d"], k["entry"], k["sl"], o[1], o[2], lev))
            else:
                ev["new"].append((sym, k["d"], k["entry"], k["sl"], lev))
            if modal and priv is not None:
                risk_usd = modal * risk_pct / 100
                qty = risk_usd / abs(k["entry"] - k["sl"])
                tp = tp1_price(k["d"], k["entry"], abs(k["entry"] - k["sl"]))
                priv.append(f"• {sym} {'BUY' if k['d']==1 else 'SELL'} STOP {fmt(k['entry'])}: ±{qty:.6g} koin (±{qty*k['entry']:,.0f} USDT, risiko {risk_usd:,.2f} USDT)"
                            f" · TP 25%: ±{qty * TP1_FRAC:.6g} koin di {fmt(tp)}")
        elif kind == "cancel":
            ev["cancel"].append((sym, k["reason"]))
        elif kind == "fill":
            ev["fill"].append((sym, k["d"], k["entry"], k["sl"], k.get("conv")))
        elif kind == "trail":
            ev["trail"].append((sym, k["d"], k["entry"], k["old"], k["sl"], k["r0"], k.get("conv")))
        elif kind == "exit":
            ev["exit"].append((sym, k["d"], k["entry"], k["exit"], k["R"], k["t0"], k["t"], k.get("conv"),
                               k.get("why", ""), k.get("part", 0.0)))
        elif kind == "partial":
            ev["partial"].append((sym, k["d"], k["entry"], k["px"], k["R"], k["frac"], k["sl"], k["r0"], k.get("conv")))
    return notify

# ---------------------------------------------------------------- main
def send_health(state, start, end, jenis):
    """Lapis 2: cek kesehatan strategi ke chat pribadi pemilik (bukan channel)."""
    try:
        import jurnal, kesehatan
        labels = {(j["sym"], j["t0"]): j.get("label") for j in jurnal.load("crypto")}
        hist = state.get("hist", [])
        per = [h[6] for h in hist if start.timestamp() <= h[3] < end.timestamp()]
        last = end - dt.timedelta(days=1)
        judul = f"{jenis} {start:%d %b} - {last:%d %b %Y}" if jenis == "Minggu" else f"{jenis} {start:%B %Y}"
        txt = kesehatan.build("crypto", hist, labels, judul, per)
        if txt:
            tg_send(txt)
    except Exception as e:
        print("Cek kesehatan gagal:", e)

def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    risk_pct = float(os.environ.get("RISK_PCT") or DEFAULT_RISK_PCT)
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
        if reply.startswith("/_post_channel"):
            body = reply.split("\n", 1)[1]
            ok = tg_send(body, chat=state["channel_id"])
            reply = "📤 Rekap sudah diposting ke channel." if ok else "⚠️ Gagal posting rekap ke channel."
        if reply == "/_kirim_panduan_xau":
            ok = tg_send(commands.PANDUAN_XAU, chat=state["gold_channel_id"], pin=True)
            reply = "📌 Panduan XAU sudah diposting & di-pin di channel XAU." if ok else "⚠️ Gagal posting panduan XAU. Pastikan bot admin dengan izin Post & Pin Messages."
        if reply == "/_kirim_panduan":
            ok = tg_send(commands.PANDUAN_ANGGOTA, chat=state["channel_id"], pin=True)
            reply = "📌 Panduan anggota sudah diposting & di-pin di channel." if ok else "⚠️ Gagal posting panduan. Pastikan bot admin channel dengan izin Post & Pin Messages."
        tg_send(reply)
    if os.environ.get("MODE") == "cmd":
        json.dump(state, open(STATE_FILE, "w"), indent=1)
        return

    # Run ganda (cron-job.org + jadwal cadangan GitHub) untuk slot yang sama: jika candle H1 terakhir
    # yang sudah close sudah diproses, berhenti di sini tanpa mengambil data 50 koin (hemat menit Actions).
    latest_closed = int(time.time()) // 3600 * 3600 - 3600
    if state.get("last_ts", 0) >= latest_closed and os.environ.get("FORCE") != "1":
        json.dump(state, open(STATE_FILE, "w"), indent=1)
        print("Candle terakhir sudah diproses oleh run sebelumnya, tidak ada yang baru.")
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
    ev, priv = new_events(), []
    base_notify = make_notifier(ev, risk_pct, modal, priv)
    import jurnal
    def notify(kind, coin, **k):
        cs = state["coins"].setdefault(coin, {"pend": None, "pos": None})
        if kind == "order":
            cs["conv"], cs["feat"] = conviction_detail(data, coin, k["t"], k["d"], k["entry"], k["sl"])
            if k.get("d") == -1:
                cs["feat"]["fund"] = funding(coin, k["t"])
        elif kind in ("fill", "exit", "trail", "partial"):
            k["conv"] = cs.get("conv")
        if kind == "exit":   # Lapis 1: catat trade selesai ke jurnal
            D = data.get(coin, {})
            mfe, mae = mfe_mae_safe(D, k["t0"], k["t"], k["d"], k["entry"], k.get("r0"))
            try:
                jurnal.append("crypto", dict(sym=coin + "USDT", d=k["d"], t0=k["t0"], t1=k["t"], entry=k["entry"],
                                             exit=k["exit"], R=round(k["R"], 3), alasan=k.get("why"), label=cs.get("conv"),
                                             mfe=mfe, mae=mae, tp_sebagian=k.get("part") or 0,
                                             R_tp_sebagian=(round(k["partR"], 3) if k.get("partR") is not None else None),
                                             versi="v2-stagnan-tp25", **(cs.get("feat") or {})))
            except Exception as e:
                print("Jurnal gagal ditulis:", e)
        base_notify(kind, coin, **k)
    eng = Engine(state, funding, notify)
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
    # Maksimal 2 bubble: (1) SINYAL order, (2) UPDATE posisi. Hanya dikirim jika ada candle cek baru.
    import templates as tpl
    buf = []
    # Bot berjalan tiap 2 jam; strategi dicek tiap 4 jam. Run di antara cek hanya mengirim UPDATE
    # jika ada order terisi / posisi ditutup (dan SINYAL jika ada order yang harus dibatalkan).
    rows = []
    for c, v in state["coins"].items():
        p = v.get("pos")
        if p and c in data:
            r0 = p[4] if len(p) > 4 else abs(p[1] - p[2])
            if not v.get("conv"):   # posisi lama tanpa label: hitung dari SL awal di candle terisi
                v["conv"] = conviction(data, c, p[3], p[0], p[1], p[1] - p[0] * r0)
            rows.append((c + "USDT", p[0], p[1], p[2], r0, data[c]["C"][-1], p[3], v.get("conv"), pos_ext(p)))
    send_update = eng.checked or ev["fill"] or ev["exit"] or ev["trail"] or ev["partial"]
    # Catatan order hari ini (WIB): order baru, update (harga awal hari ini), dan pembatalan.
    today = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=7)).date().isoformat()
    day = state.get("day_log") or {}
    if day.get("date") != today:
        day = {"date": today, "new": [], "upd": {}, "cancel": []}
    for sym, *_ in ev["new"]:
        if sym not in day["new"]:
            day["new"].append(sym)
    for sym, d, e, sl, oe, osl, lev in ev["upd"]:
        day["upd"].setdefault(sym, [oe, osl])           # simpan harga sebelum update pertama hari ini
    for sym, reason in ev["cancel"]:
        day["cancel"] = [c for c in day["cancel"] if c[0] != sym] + [[sym, reason]]
    state["day_log"] = day
    for c in COINS:   # order lama tanpa label (dibuat sebelum fitur ini): beri label dari candle cek terakhir
        v = state["coins"].get(c) or {}
        if v.get("pend") and not v.get("conv") and c in data:
            v["conv"] = conviction(data, c, newest, *v["pend"])
    pending = [(c + "USDT", v["pend"][0], v["pend"][1], v["pend"][2], safe_lev(v["pend"][1], v["pend"][2]), v.get("conv"))
               for c in COINS for v in [state["coins"].get(c) or {}] if v.get("pend")]
    # Peringatan news: event USD berdampak tinggi dalam 3 jam ke depan, dikirim sekali per event.
    sent = state.get("news_sent", [])
    news = [n for n in upcoming_news(time.time()) if f"{n[0]}|{n[1]}" not in sent]
    if news:
        nb = tpl.news_bubble(news, rows, len(pending), time.time(), fmt)
        buf.append(nb)
        for part in tpl.split_message(nb):
            tg_send(part, chat=target)
        state["news_sent"] = (sent + [f"{n[0]}|{n[1]}" for n in news])[-50:]
    bubbles = [tpl.signal_bubble(ev, newest + 3600, fmt, pending, day),
               tpl.update_bubble(ev, rows, newest + 3600, fmt) if send_update else None]
    for b in bubbles:
        if b:
            buf.append(b)
            for part in tpl.split_message(b):
                tg_send(part, chat=target)
    if not buf and os.environ.get("SEND_EMPTY", "0") == "1":
        tg_send(head + "\n\nTidak ada perubahan.", chat=target)
    # Rekap otomatis: mingguan setiap Senin (minggu lalu), bulanan setiap tanggal 1 (bulan lalu)
    now_wib = dt.datetime.now(commands.WIB)
    wk_start, _ = commands.period_bounds("minggu", now_wib, previous=True)
    if now_wib.weekday() == 0 and state.get("recap_week") != wk_start.isoformat():
        tg_send(commands.build_recap(state, "minggu", True, risk_pct, now_wib, fmt), chat=target)
        state["recap_week"] = wk_start.isoformat()
        send_health(state, wk_start, wk_start + dt.timedelta(days=7), "Minggu")
    mo_start, _ = commands.period_bounds("bulan", now_wib, previous=True)
    if now_wib.day == 1 and state.get("recap_month") != mo_start.isoformat():
        tg_send(commands.build_recap(state, "bulan", True, risk_pct, now_wib, fmt), chat=target)
        state["recap_month"] = mo_start.isoformat()
        send_health(state, mo_start, commands.period_bounds("bulan", now_wib)[0], "Bulan")
    json.dump(state, open(STATE_FILE, "w"), indent=1)
    # Ukuran posisi pribadi (MODAL_USDT) hanya ke chat pemilik
    if priv:
        tg_send("🔒 <b>Ukuran posisi Anda</b> (modal " + f"{modal:,.0f} USDT, risiko {risk_pct}%)\n" + "\n".join(priv))
    print(head, *buf, *priv, sep="\n\n")

if __name__ == "__main__":
    main()
