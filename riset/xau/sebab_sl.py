"""Evaluasi mingguan (pemilik, 11 Nov 2026): PENYEBAB tiap SL bot XAU live dalam N hari terakhir.
Kategori (urutan cek): DATA = trade live beda dengan replay data final (salah data/eksekusi, wajib dianalisa);
NEWS = event USD berdampak tinggi antara 60 menit sebelum masuk s.d. jam SL (aman, bukan celah);
LONJAKAN = candle SL bergerak >= 2,5 ATR tanpa news (kejadian ekstrem, catat);
CELAH = selain itu -> wajib dianalisa: komponen, arah vs tren H1/harian, ATR relatif, dan pembanding historis (porsi SL
komponen itu di kondisi sama 2005-2026). Pola CELAH berulang (>= 2 SL komponen & kondisi sama dalam 4 minggu) -> buka ide baru.
Catatan: kalender news = ForexFactory minggu berjalan saja -> jalankan tiap Jumat untuk minggu itu (hari=7).
Pemakaian: python riset/xau/sebab_sl.py <repo> <xau_setra.json> [hari=7] [xau_2004.json]"""
import sys, os, json, datetime as dt
import numpy as np
VERSI_SEJAK = "2026-11-10T23:00"   # waktu (UTC) aturan bot terakhir berubah; cek DATA hanya untuk trade sesudahnya (perbarui tiap ganti aturan)
REPO, SETRA = sys.argv[1:3]; HARI = int(sys.argv[3]) if len(sys.argv) > 3 else 7
PANJANG = sys.argv[4] if len(sys.argv) > 4 else None
sys.path.insert(0, REPO); sys.path.insert(0, os.path.join(REPO, "riset", "xau", "eksperimen"))
import gold_bot as gb, audit_mesin as m, multi_mesin as mm
from signal_bot import http_json, NEWS_URL
wib = lambda t: (dt.datetime.fromtimestamp(t, dt.timezone.utc) + dt.timedelta(hours=7)).strftime("%a %d %b %H:%M")
hist = json.load(open(os.path.join(REPO, "gold_state.json"))).get("hist", [])
batas = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=HARI)).timestamp()
sl = [h for h in hist if h[2] >= batas and h[6] <= -0.9]
semua = [h for h in hist if h[2] >= batas]
print(f"Trade {HARI} hari terakhir: {len(semua)} · SL: {len(sl)} · total {sum(h[6] for h in semua):+.2f}R")
if not sl: sys.exit(0)
# replay data final
D = m.muat(SETRA); T, O, H, L, C = D
A = np.array(m.atr(list(H), list(L), list(C), 14)); F = m.fitur(D, A)
rep = {int(x["t0"]): x for x in mm.baseline(D, A, F)}
E = np.array(gb.ema(list(C), 200)); idx = {int(t): i for i, t in enumerate(T)}
try:
    news = [e for e in http_json(NEWS_URL, tries=2) if e.get("country") == "USD" and e.get("impact") == "High"]
except Exception as e:
    news = []; print("Kalender news gagal diambil:", e)
nt = []
for e in news:
    try: nt.append((dt.datetime.fromisoformat(e["date"]).timestamp(), e.get("title", "")))
    except Exception: pass
hist_bt = None
if PANJANG:
    Dp = m.muat(PANJANG); Ap = np.array(m.atr(list(Dp[2]), list(Dp[3]), list(Dp[4]), 14)); Fp = m.fitur(Dp, Ap)
    hist_bt = [x for x in mm.baseline(Dp, Ap, Fp) if x["t0"] >= m.ts("2005-01-01")]
    Ep = np.array(gb.ema(list(Dp[4]), 200))
kat_n = {}
for h in sl:
    _, d, t0, t1, e, ex, R, st = (h + [""])[:8]
    i0 = idx.get(int(t0)); i1 = idx.get(int(t1))
    r = rep.get(int(t0)); kat, ket = None, ""
    if t0 >= dt.datetime.fromisoformat(VERSI_SEJAK).replace(tzinfo=dt.timezone.utc).timestamp() and (r is None or r["d"] != d or r.get("strat") != st):
        kat = "DATA"; ket = f"replay: {'tidak ada trade' if r is None else ('BUY' if r['d'] == 1 else 'SELL') + ' ' + r.get('strat', '')}"
    if kat is None:
        ada = [(t, nm) for t, nm in nt if t0 - 3600 <= t <= t1]
        if ada: kat = "NEWS"; ket = "; ".join(f"{wib(t)} {nm}" for t, nm in ada)
    if kat is None and i1 is not None and (H[i1] - L[i1]) >= 2.5 * A[i1]:
        kat = "LONJAKAN"; ket = f"candle SL {H[i1] - L[i1]:.1f} USD = {(H[i1] - L[i1]) / A[i1]:.1f} ATR"
    if kat is None:
        kat = "CELAH"
        if i0 is not None:
            ip = i0 - 1; tren = "searah" if (C[ip] > E[ip]) == (d == 1) else "lawan"
            atr_rel = A[ip] / np.median(A[max(0, ip - 500):ip + 1]); jam = (t1 - t0) / 3600
            ket = f"{st} {'BUY' if d == 1 else 'SELL'} {tren} tren H1, ATR rel {atr_rel:.2f}, kena SL setelah {jam:.0f} jam"
            if hist_bt:
                sama = [x for x in hist_bt if x["strat"] == st and ((Dp[4][x["ip"]] > Ep[x["ip"]]) == (x["d"] == 1)) == (tren == "searah")]
                if sama:
                    p = np.mean([x["R"] <= -0.99 for x in sama])
                    ket += f" · historis {st} {tren} tren: SL {p * 100:.0f}% dari {len(sama)} trade"
    kat_n[kat] = kat_n.get(kat, 0) + 1
    print(f"- {wib(t0)} {st} {'BUY' if d == 1 else 'SELL'} entry {e:.2f} SL {wib(t1)} {R:+.2f}R → {kat}: {ket}")
print("Ringkasan penyebab SL:", ", ".join(f"{k} {v}" for k, v in kat_n.items()))
print("Tindakan: NEWS = aman; LONJAKAN = catat; DATA & CELAH = wajib dianalisa di laporan (pola berulang -> ide baru).")
