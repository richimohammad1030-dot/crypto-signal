"""
Bot sinyal "Gold Daily Straddle" (XAUUSD) -> channel Telegram khusus XAU.

Aturan (versi MULTI-STRATEGI, live mulai 2 Nov 2026; chart H1; riset/xau/STRATEGI.md). Jam sinyal 07:00 & tutup 23:00 WIB
= aturan tetap pemilik. Maksimal 1 posisi per hari, dipilih jam 07:00:
A) MEAN REVERSION (prioritas): RSI(2) H1 close 07:00 <= MR_BUY (43,76) -> BUY market; >= MR_SELL (85) -> SELL market (masuk di open candle
   berikutnya). SL = 3 x ATR(14) H1, tanpa TP, ditutup 23:00 WIB.
B) BREAKOUT SEARAH TREN (K6), bila RSI(2) tidak ekstrem:
- 07:00 WIB (candle H1 yang close 07:00): range = high & low 3 candle H1 terakhir.
- Tren = close 07:00 vs EMA200 H1. Tren naik -> ORDER UTAMA BUY STOP di high range, BATAS BATAL di low range;
  tren turun -> ORDER UTAMA SELL STOP di low range, BATAS BATAL di high range.
- Jika harga menyentuh batas batal lebih dulu, order utama dibatalkan dan hari itu tidak ada trade (riset: ide #22 "K6",
  sama persis dengan OCO 2 sisi yang melewati hari bila sisi lawan tren terisi duluan).
- SL = 1,5 x ATR(14) dari entry. TP = 4R (6 x ATR).
- 23:00 WIB: order yang belum terisi dibatalkan, posisi yang masih terbuka ditutup.
HIBRIDA (ide #42b, live mulai 6 Nov 2026): tren harian = close H1 07:00 vs SMA 100 close 07:00 terakhir (TREND_D1_N).
   Tren NAIK (atau riwayat < 100 hari) -> ambang A di atas. Tren TURUN -> cermin: SELL bila RSI(2) >= MR_SELL_TURUN (70),
   BUY hanya bila RSI(2) <= MR_BUY_TURUN (15). Riwayat close 07:00 disimpan di state["c07"] (bibit gold_c07_seed.json).
C) SUSULAN (ide #37, live mulai 6 Nov 2026), hanya pada hari K6 dilewati (batas batal tersentuh): di candle pertama yang close
   09:00/11:00/.../21:00 WIB sejak batas batal tersentuh, RSI(2) H1 <= SUS_BUY -> BUY market; >= SUS_SELL -> SELL market
   (masuk di open candle berikutnya). Tidak ekstrem -> hari itu tetap tanpa trade (hanya 1 kali keputusan).
   SL = 3 x ATR(14) H1, TP = 1R, ditutup 23:00 WIB. Live: keputusan yang baru diproses >= 1 jam setelah candle close
   tidak dikirim & tidak dicatat (harga masuk sudah lewat).
Bot hanya membaca data publik & mengirim pesan; tidak punya akses ke akun broker.
"""
import json, os, sys, time, urllib.request, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(HERE, "gold_state.json")
CRYPTO_STATE = os.path.join(HERE, "state.json")       # tempat id channel XAU disimpan oleh pemroses perintah
RANGE_N, SL_ATR, RR, ATR_N = 3, 1.5, 4.0, 14
TREND_EMA = 200        # EMA close H1 penentu arah order utama (K6)
MR_N, MR_BUY, MR_SELL, MR_SL_ATR = 2, 43.76, 85.0, 3.0   # MR_SELL 71,22 -> 85 sejak 6 Nov 2026 (ide #40): RSI 71-85 -> K6
TREND_D1_N, MR_SELL_TURUN, MR_BUY_TURUN = 100, 70.0, 15.0   # hibrida ide #42b (cermin Connors saat tren harian turun)
C07_SEED = os.path.join(HERE, "gold_c07_seed.json")          # riwayat close 07:00 WIB Setra (bibit SMA 100 hari)
STALE_S = 2 * 3600     # data dianggap macet bila candle H1 terakhir yang close lebih tua dari 2 jam (hari bursa)
LATE_S = 3 * 3600      # sinyal 07:00 dianggap TERLAMBAT bila baru diproses >= 10:00 WIB (close candle + 3 jam): tidak dicatat
SUS_BUY, SUS_SELL, SUS_SL_ATR, SUS_TP_R = 25.41, 77.10, 3.0, 1.0   # susulan: kuantil 35%/65% RSI(2) jam keputusan 2015-2021
SUS_JAM_UTC = (1, 3, 5, 7, 9, 11, 13)   # jam BUKA candle H1 (UTC) yang close 09:00, 11:00, ..., 21:00 WIB
SUS_LATE_S = 3600      # keputusan susulan TERLAMBAT bila diproses >= 1 jam setelah candle keputusan close
PLACE_HOUR_UTC = 23     # jam BUKA candle H1 (UTC) yang close 07:00 WIB
CLOSE_HOUR_UTC = 15     # jam BUKA candle H1 (UTC) yang close 23:00 WIB
SYM = "XAUUSD"
LINE = "━━━━━━━━━━━━━━━━━━"

sys.path.insert(0, HERE)
from signal_bot import tg_send, http_json, atr, upcoming_news          # pakai fungsi yang sama dengan bot crypto
import commands


def ema(x, n):
    """EMA sederhana (nilai awal = data pertama); sama dengan riset/xau/eksperimen/audit_mesin.ema."""
    out, k, e = [], 2 / (n + 1), None
    for v in x:
        e = v if e is None else e + k * (v - e)
        out.append(e)
    return out


def rsi(x, n):
    """RSI Wilder rekursif (alpha 1/n, awal 0); sama dengan riset/xau/eksperimen/multi_mesin.rsi."""
    out, au, ad, a, prev = [], 0.0, 0.0, 1 / n, None
    for v in x:
        if prev is not None:
            d = v - prev
            au += a * ((d if d > 0 else 0.0) - au); ad += a * ((-d if d < 0 else 0.0) - ad)
        prev = v
        out.append(100 - 100 / (1 + au / max(ad, 1e-12)))
    return out


def fmt(p):
    return f"{p:,.2f}"


def wib(ts):
    return (dt.datetime.fromtimestamp(ts, dt.timezone.utc) + dt.timedelta(hours=7)).strftime("%a %d %b %H:%M WIB")


def fetch_xau(n=1000):
    """Candle H1 XAU/USD (Setra/MT5). Return list [open_time_s, o, h, l, c] yang SUDAH close."""
    d = http_json(f"https://setra.id/api/md/candles?symbol=XAU%2FUSD&tf=1h&limit={n}")
    rows = [[c["t"] // 1000, c["o"], c["h"], c["l"], c["c"]] for c in d.get("data", [])]
    now = time.time()
    rows = [r for r in rows if r[0] + 3600 <= now]          # buang candle yang belum close
    dedup = {r[0]: r for r in rows}
    return [dedup[k] for k in sorted(dedup)]


def _duka_get(url, timeout=60, coba=6):
    for k in range(coba):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return b""
            print("Dukascopy HTTP", e.code, url[-45:]); time.sleep(2 * (k + 1))
        except Exception as e:
            print("Dukascopy gagal:", e, url[-45:]); time.sleep(2 * (k + 1))
    return None


def _pasar_buka(k):
    """Jam UTC (open candle k) di mana emas bisa diperdagangkan: tutup Jumat >= 22:00 UTC s.d. Minggu < 21:00 UTC."""
    w = dt.datetime.fromtimestamp(k, dt.timezone.utc)
    return not (w.weekday() == 5 or (w.weekday() == 6 and w.hour < 21) or (w.weekday() == 4 and w.hour >= 22))


def _tepi_pekan(k):
    """Jam yang bisa kosong karena pembukaan/penutupan pasar berganti musim (Minggu 21-22 UTC, Jumat 21 UTC)."""
    w = dt.datetime.fromtimestamp(k, dt.timezone.utc)
    return (w.weekday() == 6 and w.hour in (21, 22)) or (w.weekday() == 4 and w.hour == 21)


def fetch_dukascopy(after_ts):
    """CADANGAN saat Setra macet: candle H1 XAU/USD Dukascopy (harga BID) yang sudah close dan open > after_ts.
    Hanya jam pasar buka yang diminta. Hari dengan > 8 jam dibutuhkan (dan sudah lewat) memakai file M1 harian, selain itu
    file tick per jam. Berhenti di unduhan pertama yang gagal agar tidak ada candle yang terlewat (lubang)."""
    import lzma, struct
    now = time.time(); out = {}
    today = dt.datetime.fromtimestamp(now, dt.timezone.utc).date()
    need = [k for k in range(int(after_ts) // 3600 * 3600 + 3600, int(now) // 3600 * 3600, 3600) if k + 3600 <= now and _pasar_buka(k)]
    per_hari = {}
    for k in need:
        per_hari.setdefault(dt.datetime.fromtimestamp(k, dt.timezone.utc).date(), []).append(k)
    try:
        for day in sorted(per_hari):
            base = f"https://datafeed.dukascopy.com/datafeed/XAUUSD/{day.year}/{day.month - 1:02d}/{day.day:02d}"
            d0 = dt.datetime(day.year, day.month, day.day, tzinfo=dt.timezone.utc).timestamp()
            if day < today and len(per_hari[day]) > 8:
                b = _duka_get(f"{base}/BID_candles_min_1.bi5")
                if b is None:
                    break
                raw = lzma.decompress(b) if b else b""
                for i in range(len(raw) // 24):
                    t, o, c, l, h, v = struct.unpack(">5if", raw[i * 24:(i + 1) * 24])
                    k = int(d0 + t) // 3600 * 3600
                    if k not in out: out[k] = [k, o / 1000, h / 1000, l / 1000, c / 1000]
                    else: x = out[k]; x[2] = max(x[2], h / 1000); x[3] = min(x[3], l / 1000); x[4] = c / 1000
                continue
            gagal = False
            for k in per_hari[day]:
                b = _duka_get(f"{base}/{(k - int(d0)) // 3600:02d}h_ticks.bi5")
                if b is None and _tepi_pekan(k):
                    continue                 # jam tepi akhir pekan (bisa kosong) gagal -> lewati, bukan lubang data
                if b is None:
                    gagal = True
                    break
                raw = lzma.decompress(b) if b else b""
                bid = [struct.unpack(">3i2f", raw[i * 20:(i + 1) * 20])[2] / 1000 for i in range(len(raw) // 20)]
                if bid: out[k] = [k, bid[0], max(bid), min(bid), bid[-1]]
            if gagal:
                break
    except Exception as e:
        print("Cadangan Dukascopy gagal:", e)
    return [out[k] for k in sorted(out) if k > after_ts and k + 3600 <= now and not (out[k][1] == out[k][2] == out[k][3] == out[k][4])]


class GoldEngine:
    """Urutan per candle sama persis dengan backtest:
       1) order terisi?  2) posisi kena SL/TP?  3) jam tutup 23:00  4) jam pasang 07:00"""
    def __init__(self, state, notify, now=None):
        self.s, self.notify = state, notify
        self.trades = []
        self.now = now          # waktu nyata (live); None = replay/backtest (tidak ada aturan terlambat)

    def record(self, d, e, ex, r0, t0, t1, why, strat="K6"):
        R = (ex - e) * d / r0 if r0 else 0.0
        self.trades.append((t0, t1, d, e, ex, r0, strat))
        self.s.setdefault("hist", []).append(["XAU", d, t0, t1, e, ex, round(R, 3), strat])
        self.notify("exit", d=d, entry=e, exit=ex, R=R, t0=t0, t=t1, why=why, r0=r0, strat=strat)

    def step(self, i, T, O, H, L, C, A):
        s = self.s
        t, hr = T[i], (T[i] // 3600) % 24
        pend, pos = s.get("pend"), s.get("pos")
        # 1a) mean reversion / susulan: masuk market di open candle pertama setelah sinyal
        if pos is None and pend and pend.get("mode") in ("MR", "SUS"):
            d, st = pend["d"], pend["mode"]; fill = O[i]; slp = fill - d * pend["dist"]
            tpp = fill + d * SUS_TP_R * pend["dist"] if st == "SUS" else None
            s["pend"] = None
            s["pos"] = {"d": d, "e": fill, "sl": slp, "tp": tpp, "r0": pend["dist"], "t0": t, "strat": st}
            self.notify("fill", d=d, entry=fill, sl=slp, tp=tpp, t=t, strat=st)
            if (d == 1 and L[i] <= slp) or (d == -1 and H[i] >= slp):
                s["pos"] = None
                self.record(d, fill, slp, pend["dist"], t, t, "kena SL di candle yang sama", st)
        # 1b) order stop K6 terisi? (BUY STOP dicek lebih dulu)
        elif pos is None and pend:
            b, sl_ = pend["buy"], pend["sell"]
            hit = None
            if H[i] >= b[0]:
                hit = (1, max(b[0], O[i]), b[1], b[2])
            elif L[i] <= sl_[0]:
                hit = (-1, min(sl_[0], O[i]), sl_[1], sl_[2])
            if hit and pend.get("main", hit[0]) != hit[0]:
                # K6: batas batal (sisi lawan tren) tersentuh lebih dulu -> order utama dibatalkan, hari dilewati
                s["pend"] = None
                self.notify("skip", d=hit[0], level=(b if hit[0] == 1 else sl_)[0], main=pend["main"], t=t)
                s["sus_wait"] = True          # C) tunggu jam keputusan susulan berikutnya
                hit = None
            if hit:
                d, fill, slp, tpp = hit
                r0 = abs(fill - slp)
                s["pend"] = None
                s["pos"] = {"d": d, "e": fill, "sl": slp, "tp": tpp, "r0": r0, "t0": t}
                self.notify("fill", d=d, entry=fill, sl=slp, tp=tpp, t=t, strat="K6")
                if (d == 1 and L[i] <= slp) or (d == -1 and H[i] >= slp):
                    s["pos"] = None
                    self.record(d, fill, slp, r0, t, t, "kena SL di candle yang sama")
        # 2) kelola posisi (SL dicek lebih dulu dari TP)
        elif pos is not None and pos["t0"] < t:
            d, st = pos["d"], pos.get("strat", "K6")
            if (d == 1 and L[i] <= pos["sl"]) or (d == -1 and H[i] >= pos["sl"]):
                s["pos"] = None; self.record(d, pos["e"], pos["sl"], pos["r0"], pos["t0"], t, "kena SL", st)
            elif pos.get("tp") is not None and ((d == 1 and H[i] >= pos["tp"]) or (d == -1 and L[i] <= pos["tp"])):
                s["pos"] = None; self.record(d, pos["e"], pos["tp"], pos["r0"], pos["t0"], t, "kena TP", st)
        # 3) jam tutup 23:00 WIB
        if hr == CLOSE_HOUR_UTC:
            s.pop("sus_wait", None)
            if s.get("pend"):
                s["pend"] = None
                self.notify("expire")
            if s.get("pos"):
                p = s["pos"]; s["pos"] = None
                self.record(p["d"], p["e"], C[i], p["r0"], p["t0"], t, "ditutup jam 23:00", p.get("strat", "K6"))
        # 4) jam pasang 07:00 WIB
        if hr == PLACE_HOUR_UTC and s.get("pos") is None and self.now is not None and self.now - (t + 3600) >= LATE_S:
            # live: data candle 07:00 baru tersedia >= 10:00 WIB -> sinyal hari ini tidak dikirim & tidak dicatat
            self.notify("late", t=t)
        elif hr == PLACE_HOUR_UTC and s.get("pos") is None:
            hi, lo, a = max(H[i - RANGE_N + 1:i + 1]), min(L[i - RANGE_N + 1:i + 1]), A[i]
            r2 = self.R2[i]
            ma = self.MA.get(t)
            turun = ma is not None and C[i] <= ma
            b_, s_ = (MR_BUY_TURUN, MR_SELL_TURUN) if turun else (MR_BUY, MR_SELL)
            if r2 <= b_ or r2 >= s_:                   # A) mean reversion diprioritaskan; K6 tidak dipasang hari ini
                if MR_SL_ATR * a > 0.5:
                    d = 1 if r2 <= b_ else -1
                    s["pend"] = {"mode": "MR", "d": d, "dist": MR_SL_ATR * a, "t": t, "rsi": round(r2, 1),
                                 "px": C[i], "a": a, "tren": 1 if C[i] > self.E[i] else -1,
                                 "d1": -1 if turun else 1, "ma": round(ma, 2) if ma is not None else None}
                    self.notify("order", pend=s["pend"], t=t, price=C[i])
            elif abs(hi - (hi - SL_ATR * a)) > 0.5:    # B) K6; sama dengan backtest: abaikan order dengan SL < 0,5 USD
                tren = 1 if C[i] > self.E[i] else -1
                s["pend"] = {"buy": [hi, hi - SL_ATR * a, hi + RR * SL_ATR * a],
                             "sell": [lo, lo + SL_ATR * a, lo - RR * SL_ATR * a],
                             "t": t, "hi": hi, "lo": lo, "main": tren, "ema": round(self.E[i], 2), "rsi": round(r2, 1)}
                self.notify("order", pend=s["pend"], t=t, price=C[i])
        # 5) susulan: satu kali keputusan di jam keputusan pertama setelah batas batal K6 tersentuh
        if s.get("sus_wait") and hr in SUS_JAM_UTC and s.get("pos") is None and s.get("pend") is None:
            s.pop("sus_wait", None)
            r2, a = self.R2[i], A[i]
            if (r2 <= SUS_BUY or r2 >= SUS_SELL) and SUS_SL_ATR * a > 0.5:
                if self.now is not None and self.now - (t + 3600) >= SUS_LATE_S:
                    self.notify("late", t=t, strat="SUS")
                else:
                    d = 1 if r2 <= SUS_BUY else -1
                    s["pend"] = {"mode": "SUS", "d": d, "dist": SUS_SL_ATR * a, "t": t, "rsi": round(r2, 1),
                                 "px": C[i], "a": a, "tren": 1 if C[i] > self.E[i] else -1}
                    self.notify("order", pend=s["pend"], t=t, price=C[i])

    def run(self, rows, since):
        T = [r[0] for r in rows]; O = [r[1] for r in rows]; H = [r[2] for r in rows]; L = [r[3] for r in rows]; C = [r[4] for r in rows]
        A = atr(H, L, C, ATR_N)
        self.E = ema(C, TREND_EMA)
        self.R2 = rsi(C, MR_N)
        # SMA 100 close 07:00 WIB (hibrida #42b): riwayat tersimpan (state/bibit) + candle 07:00 di rows; replay = rows saja
        c07 = {} if self.s.get("replay") else {int(k): v for k, v in (self.s.get("c07") or {}).items()}
        if not self.s.get("replay") and os.path.exists(C07_SEED):
            c07 = {**{int(k): v for k, v in json.load(open(C07_SEED)).items()}, **c07}
        for k in range(len(rows)):
            if (T[k] // 3600) % 24 == PLACE_HOUR_UTC: c07[int(T[k])] = C[k]
        ts_ = sorted(c07); vals = [c07[k] for k in ts_]; self.MA = {}
        for k in range(TREND_D1_N - 1, len(ts_)):
            self.MA[ts_[k]] = sum(vals[k - TREND_D1_N + 1:k + 1]) / TREND_D1_N
        if not self.s.get("replay"):
            self.s["c07"] = {str(k): c07[k] for k in ts_[-150:]}
        start = 250 if self.s.get("replay") else 50
        for i in range(start, len(rows)):
            if T[i] > since:
                self.step(i, T, O, H, L, C, A)
                self.s["last_ts"] = T[i]
        return C[-1] if C else None


# Templat pesan ada di gold_templates.py


# ---------------------------------------------------------------- main
def send_health(state, start, end, jenis):
    """Lapis 2: cek kesehatan strategi XAU ke chat pribadi pemilik (bukan channel)."""
    try:
        import kesehatan
        hist = state.get("hist", [])
        per = [h[6] for h in hist if start.timestamp() <= h[3] < end.timestamp()]
        last = end - dt.timedelta(days=1)
        judul = f"{jenis} {start:%d %b} - {last:%d %b %Y}" if jenis == "Minggu" else f"{jenis} {start:%B %Y}"
        txt = kesehatan.build("xau", hist, None, judul, per)
        if txt:
            tg_send(txt)
    except Exception as e:
        print("Cek kesehatan gagal:", e)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    risk_pct = float(os.environ.get("XAU_RISK_PCT") or "0.5")
    state = json.load(open(STATE_FILE)) if os.path.exists(STATE_FILE) else {"last_ts": 0}
    cstate = json.load(open(CRYPTO_STATE)) if os.path.exists(CRYPTO_STATE) else {}
    target = cstate.get("gold_channel_id")      # None -> kirim ke chat pribadi pemilik
    try:
        rows = fetch_xau()
    except Exception as e:
        tg_send(f"⚠️ Bot XAU gagal mengambil data harga Setra: {e}"); rows = []
    # data macet? (hari bursa: Senin 07:00 s.d. Jumat 23:00 WIB; bot hanya dijadwalkan di jam itu)
    now_ = time.time()
    last_ok = rows[-1][0] + 3600 if rows else 0
    w_now = dt.datetime.fromtimestamp(now_, dt.timezone.utc) + dt.timedelta(hours=7)
    hari_bursa = w_now.weekday() < 5 and w_now.hour >= 7
    if hari_bursa and now_ - last_ok > STALE_S and rows:
        cad = fetch_dukascopy(rows[-1][0])
        rows = rows + cad
        tag = f"{last_ok}|{bool(cad)}"          # kirim peringatan sekali per kejadian macet / perubahan status cadangan
        if state.get("stale_warn") != tag:
            akhir = (dt.datetime.fromtimestamp(last_ok, dt.timezone.utc) + dt.timedelta(hours=7)).strftime("%a %d %b %H:%M WIB")
            tg_send("⚠️ <b>DATA XAU SETRA MACET</b>\n"
                    f"Candle terakhir Setra close {akhir}.\n" +
                    (f"Bot memakai data cadangan Dukascopy (BID, selisih ±0,3 USD) untuk {len(cad)} candle sampai Setra pulih."
                     if cad else "Data cadangan Dukascopy juga belum tersedia. Sinyal bisa terlambat atau tidak terkirim."))
            state["stale_warn"] = tag
    elif state.get("stale_warn") and now_ - last_ok <= STALE_S:
        tg_send("✅ Data XAU Setra sudah pulih. Bot kembali memakai Setra.")
        state.pop("stale_warn", None)
    if len(rows) < 100:
        tg_send("⚠️ Bot XAU: data harga tidak cukup."); sys.exit(1)
    first = state.get("last_ts", 0) == 0
    if first:
        # run pertama: mulai dari jam tutup (23:00 WIB) terakhir agar order/posisi hari ini ikut terbentuk
        closes = [r[0] for r in rows if (r[0] // 3600) % 24 == CLOSE_HOUR_UTC]
        since = closes[-1] if closes else rows[-1][0] - 1
    else:
        since = state["last_ts"]
    import gold_templates as gt
    ev = gt.new_events()
    base_notify = gt.make_notifier(ev)
    import jurnal
    T_, H_, L_ = [r[0] for r in rows], [r[2] for r in rows], [r[3] for r in rows]
    def notify(kind, **k):
        if kind == "order":   # faktor saat order dipasang (dipakai riset)
            p = k["pend"]
            if p.get("mode") in ("MR", "SUS"):
                state["feat"] = dict(strat=p["mode"], rsi=p["rsi"], atr=round(p["a"], 3),
                                     hari=dt.datetime.fromtimestamp(p["t"], commands.WIB).strftime("%a"))
            else:
                a = abs(p["buy"][0] - p["buy"][1]) / SL_ATR
                state["feat"] = dict(strat="K6", range=round(p["hi"] - p["lo"], 3), atr=round(a, 3),
                                     range_atr=round((p["hi"] - p["lo"]) / a, 3) if a else None, rsi=p.get("rsi"),
                                     hari=dt.datetime.fromtimestamp(p["t"], commands.WIB).strftime("%a"))
        if kind == "exit":    # Lapis 1: catat trade selesai ke jurnal
            r0 = k.get("r0")
            try:
                mfe, mae = jurnal.mfe_mae(T_, H_, L_, k["t0"], k["t"], k["d"], k["entry"], r0)
                jurnal.append("xau", dict(sym=SYM, d=k["d"], t0=k["t0"], t1=k["t"], entry=k["entry"], exit=k["exit"],
                                          R=round(k["R"], 3), alasan=k.get("why"), r0=round(r0, 3) if r0 else None,
                                          mfe=mfe, mae=mae, **(state.get("feat") or {})))
            except Exception as e:
                print("Jurnal gagal ditulis:", e)
        base_notify(kind, **k)
    eng = GoldEngine(state, notify, now=time.time())
    px = eng.run(rows, since)
    t_last = rows[-1][0] + 3600
    # Maksimal 2 bubble: (1) SINYAL order/pembatalan, (2) UPDATE terisi/ditutup/posisi berjalan
    buf = []
    # Peringatan news: event USD berdampak tinggi dalam 3 jam ke depan dan sebelum tutup 23:00 WIB
    # (setelah itu bot tidak punya posisi/order). Dikirim sekali per event, sebelum bubble lain.
    now = time.time()
    w = dt.datetime.fromtimestamp(now, dt.timezone.utc) + dt.timedelta(hours=7)
    close_ts = (w.replace(hour=23, minute=0, second=0, microsecond=0) - dt.timedelta(hours=7)).replace(tzinfo=dt.timezone.utc).timestamp()
    sent = state.get("news_sent", [])
    news = [n for n in upcoming_news(now) if n[0] <= close_ts and f"{n[0]}|{n[1]}" not in sent]
    if news:
        nb = gt.news_bubble(news, state.get("pos"), state.get("pend"), px, now)
        buf.append(nb)
        tg_send(nb, chat=target)
        state["news_sent"] = (sent + [f"{n[0]}|{n[1]}" for n in news])[-50:]
    bub = [gt.signal_bubble(ev, t_last, risk_pct, live_px=px if state.get("pend") else None, now=time.time()),
           gt.update_bubble(ev, state.get("pos"), px, t_last) if state.get("last_ts", 0) > since or ev["fill"] or ev["exit"] or ev["skip"] else None]
    if ev["skip"]:
        bub.reverse()            # "hari ini dilewati" tampil sebelum sinyal susulan di run yang sama
    for b in bub:
        if b:
            buf.append(b)
            tg_send(b, chat=target)
    # rekap otomatis mingguan: Jumat malam setelah candle tutup 23:00 WIB diproses (hasil Senin-Jumat lengkap).
    # Cadangan: jika rekap Jumat terlewat, dikirim di run pertama hari Senin. Bulanan tetap tanggal 1.
    now_wib = dt.datetime.now(commands.WIB)
    wk, _ = commands.period_bounds("minggu", now_wib, previous=True)        # minggu lalu
    this_wk, _ = commands.period_bounds("minggu", now_wib)                   # minggu ini
    fri_close = this_wk + dt.timedelta(days=4, hours=22)                     # candle Jumat 22:00-23:00 WIB
    if (now_wib.weekday() == 4 and state.get("last_ts", 0) >= fri_close.timestamp()
            and state.get("recap_week") != this_wk.isoformat()):
        # now = Senin depan + previous=True -> periode minggu ini, tanpa label "(berjalan)"
        tg_send(commands.build_recap(state, "minggu", True, risk_pct, now_wib + dt.timedelta(days=3), fmt).replace("REKAP", "REKAP XAU"), chat=target)
        state["recap_week"] = this_wk.isoformat()
        send_health(state, this_wk, this_wk + dt.timedelta(days=7), "Minggu")
    elif now_wib.weekday() == 0 and state.get("recap_week") != wk.isoformat():
        tg_send(commands.build_recap(state, "minggu", True, risk_pct, now_wib, fmt).replace("REKAP", "REKAP XAU"), chat=target)
        state["recap_week"] = wk.isoformat()
        send_health(state, wk, wk + dt.timedelta(days=7), "Minggu")
    mo, _ = commands.period_bounds("bulan", now_wib, previous=True)
    # bot XAU hanya jalan Senin-Jumat: jika tanggal 1 jatuh di akhir pekan, rekap bulanan dikirim di run pertama bulan itu
    if now_wib.day <= 3 and state.get("recap_month") != mo.isoformat():
        tg_send(commands.build_recap(state, "bulan", True, risk_pct, now_wib, fmt).replace("REKAP", "REKAP XAU"), chat=target)
        state["recap_month"] = mo.isoformat()
        send_health(state, mo, commands.period_bounds("bulan", now_wib)[0], "Bulan")
    json.dump(state, open(STATE_FILE, "w"), indent=1)
    print(*buf, sep="\n\n")


if __name__ == "__main__":
    main()
