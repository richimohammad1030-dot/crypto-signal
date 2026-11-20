"""Rutinitas harian bot FX MAJOR (dipanggil riset/harian.py). Tiga bagian, sama dengan bot XAU/crypto/intraday:
  replay   : hitung ulang semua hari sejak live dari data Setra segar dengan mesin forex_major/fx_live.py, bandingkan dengan
             catatan live fx_state.json["hist"] -> wajib IDENTIK (pair, bot, arah, jam isi sama; R selisih <= 0,05).
  sebab_sl : evaluasi setiap trade yang kena SL penuh N hari terakhir: MFE sebelum SL, jarak waktu ke SL, apakah harga lalu
             mencapai TP di hari yang sama (SL terlalu ketat / stop hunt), breakout palsu (balik menembus level dalam 2 jam).
             + kesehatan: live vs ekspektasi backtest per bot.
  bayangan : MENU varian yang tidak live dihitung pada hari yang sama sejak live (uji maju gratis).
Pemakaian: python riset/fx/harian_fx.py <repo> [hari_sebab_sl=7]"""
import datetime as dt, json, os, sys, time
REPO = os.path.abspath(sys.argv[1]); N = int(sys.argv[2]) if len(sys.argv) > 2 else 7
sys.path.insert(0, REPO); sys.path.insert(0, os.path.join(REPO, "forex_major"))
import numpy as np
import fx_live as F, backtest as B, riset_putaran6 as P6
from fx_bot import fetch

# ekspektasi backtest Dukascopy 2015-2026 (riset putaran 7, spread Exness): R rata-rata/trade & win rate per bot
EKSPEKTASI = {"N3": (0.07, 0.22), "SUS": (0.12, 0.48), "B3": (0.14, 0.66)}
MENU = {   # bayangan: nama -> (UK, SK, pakai_susulan, pakai_lanjut, balas)
    "LIVE (juara)": (F.UK, F.SK, True, True, None),
    "Tanpa pecah (UTAMA s/d 23:00, tanpa susulan)": (dict(F.UK, exp=16), F.SK, False, True, None),
    "Dengan Senin": (dict(F.UK, dow="none"), F.SK, True, True, None),
    "LIVE + BALAS (balik, SL/TP 0,15/0,3 ATR)": (F.UK, F.SK, True, True, dict(dir="balik", entry="market", atr="d1", sl=0.15, tp=0.3)),
}

st = json.load(open(os.path.join(REPO, "fx_state.json"))) if os.path.exists(os.path.join(REPO, "fx_state.json")) else {}
hist = st.get("hist", []); start = st.get("live_start", int(time.time()))
data = [B.Pair(p, fetch(p, 400)) for p in F.PAIRS]
last = max(int(P.t[-1]) for P in data)
d0, d1 = int(start) // 86400, last // 86400
done = [d for d in range(d0, d1 + 1) if last >= d * 86400 + 15 * 3600 and (d + 3) % 7 < 5]
print(f"Live sejak {time.strftime('%d %b %Y', time.gmtime(start))} · {len(done)} hari bursa selesai · trade live tercatat {len(hist)}\n")

# ---------- 1) replay ----------
print("## 1. Replay kesetaraan (wajib IDENTIK)")
rep = []
for d in done:
    for bot, tr in F.day(data, d)["trades"].items(): rep += [dict(t, bot=bot) for t in tr]
L = {(h[0], h[7], h[1], h[2]): h[6] for h in hist if h[3] // 86400 in done}
Rr = {(t["pair"], t["bot"], t["side"], t["t"]): float(t["R"]) for t in rep}
beda = sorted(set(L) ^ set(Rr)) + [k for k in set(L) & set(Rr) if abs(L[k] - Rr[k]) > 0.05]
print(f"live {len(L)} trade · replay {len(Rr)} trade -> {'IDENTIK' if not beda else 'BEDA'}")
for k in beda[:20]: print("  BEDA", k, "live", L.get(k), "replay", Rr.get(k))

# ---------- 2) penyebab SL + kesehatan ----------
print(f"\n## 2. Penyebab SL {N} hari terakhir")
Pm = {P.name: P for P in data}; batas = time.time() - N * 86400
sl = [t for t in rep if t["R"] <= -0.5 and t["t_exit"] >= batas]
kat = {}
for t in sl:
    H = Pm[t["pair"]].h1; i0 = int(np.searchsorted(H["t"], t["t"])); i1 = int(np.searchsorted(H["t"], t["t_exit"]))
    r0 = abs(t["entry"] - t["sl"]); s = t["side"]
    mfe = max(((H["h"][i] - t["entry"]) if s > 0 else (t["entry"] - H["l"][i])) for i in range(i0, i1 + 1)) / r0
    end = int(np.searchsorted(H["t"], t["t"] // 86400 * 86400 + 16 * 3600))
    tp_lalu = any((H["h"][i] >= t["tp"]) if s > 0 else (H["l"][i] <= t["tp"]) for i in range(i1 + 1, end))
    cepat = (t["t_exit"] - t["t"]) <= 2 * 3600
    k = ("SL lalu TP tercapai (SL terlalu ketat / stop hunt)" if tp_lalu else
         "Breakout palsu (SL <= 2 jam, MFE < 0,3R)" if cepat and mfe < 0.3 else
         "Sempat untung >= 0,5R lalu berbalik" if mfe >= 0.5 else "Berbalik perlahan")
    kat.setdefault(k, []).append(t)
    print(f"- {time.strftime('%a %d %b %H:%M', time.gmtime(t['t'] + 7 * 3600))} WIB {t['pair']} {'BUY' if s > 0 else 'SELL'} "
          f"[{F.NAMA[t['bot']]}] MFE {mfe:+.2f}R · {(t['t_exit'] - t['t']) / 3600:.0f} jam ke SL · {k}")
if not sl: print("Tidak ada SL penuh.")
print("\nRingkas:", {k: len(v) for k, v in kat.items()} or "-")
print("Celah berulang (>= 3 kali kategori sama dalam 7 hari) = kandidat ide riset mingguan.")
print("\n### Kesehatan live vs ekspektasi backtest")
for bot, (avg, wr) in EKSPEKTASI.items():
    R = [h[6] for h in hist if h[7] == bot]
    if R: print(f"- {F.NAMA[bot]}: {len(R)} trade · {np.mean(R):+.3f}R/trade (backtest {avg:+.2f}) · WR {np.mean(np.array(R) > 0):.0%} (backtest {wr:.0%}) · total {sum(R):+.2f}R")
    else: print(f"- {F.NAMA[bot]}: belum ada trade")
Rall = [h[6] for h in sorted(hist, key=lambda h: h[3])]
if Rall:
    eq = np.cumsum(Rall); dd = float((np.maximum.accumulate(np.insert(eq, 0, 0))[1:] - eq).max())
    print(f"- Total: {len(Rall)} trade · {sum(Rall):+.2f}R · DD {dd:.1f}R (backtest DD maks 36R = batas peringatan)")
    if dd > 36: print("PERINGATAN: drawdown live melebihi drawdown terburuk backtest.")

# ---------- 3) bayangan ----------
print("\n## 3. Live vs bayangan (sejak live, hari yang sama)")
import riset_putaran7 as P7
for nama, (UK, SK, sus, lanjut, bal) in MENU.items():
    oUK, oSK = F.UK, F.SK; F.UK, F.SK = UK, SK
    try:
        tr = []
        for d in done:
            r = F.day(data, d); base = r["trades"]["N3"] + (r["trades"]["SUS"] if sus else [])
            tr += base + (r["trades"]["B3"] if lanjut and sus else [])
            if bal:
                for P in data:
                    lst = P6.balas_gen(bal, base)(P).get(d)
                    if lst: tr += B.simulate_pair(P, lst, d)
    finally:
        F.UK, F.SK = oUK, oSK
    R = [t["R"] for t in tr]
    print(f"- {nama}: {len(R)} trade · {sum(R):+.2f}R" + (f" · WR {np.mean(np.array(R) > 0):.0%}" if R else ""))
