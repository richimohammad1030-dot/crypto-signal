"""Review risiko GABUNGAN bot swing + intraday (channel & modal yang sama). Dipakai di review bulanan.
Masukan : CSV trade swing (backtest_crypto.py) dan CSV trade intraday (backtest_intraday.py).
Pertanyaan: apakah keduanya rugi di hari yang sama? Berapa drawdown gabungan? Berapa risiko terbuka maksimum bersamaan?
Catatan: R swing = R kotor (perhitungan bot), R intraday = R bersih. Risiko per trade sama (default 1% keduanya).
Pemakaian: python riset/risiko_gabungan.py <trades_swing.csv> <trades_intraday.csv> [risiko_swing%] [risiko_intraday%] [mulai YYYY-MM-DD]"""
import calendar, collections, csv, sys, time
import numpy as np

SW, IN = sys.argv[1:3]
RS = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
RI = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
START = calendar.timegm(time.strptime(sys.argv[5], "%Y-%m-%d")) if len(sys.argv) > 5 else 1583020800
DAY = 86400

sw = [dict(t0=int(float(r["t0"])), t1=int(float(r["t1"])), R=float(r["R"]), c=r["coin"], d=int(r["d"])) for r in csv.DictReader(open(SW))]
it = [dict(t0=int(float(r["t_fill"])), t1=int(float(r["t_exit"])), R=float(r["R"]), c=r["c"], d=int(r["d"])) for r in csv.DictReader(open(IN))]
sw = [x for x in sw if x["t1"] >= START]; it = [x for x in it if x["t1"] >= START]
d0 = START // DAY; d1 = max(x["t1"] for x in sw + it) // DAY + 1
days = np.arange(d0, d1)
def daily(tr):
    a = np.zeros(len(days))
    for x in tr: a[x["t1"] // DAY - d0] += x["R"]
    return a
S, I = daily(sw) * RS, daily(it) * RI           # % ekuitas per hari (tanpa compounding)
G = S + I
def dd(a):
    c = np.cumsum(a); return float((np.maximum.accumulate(np.concatenate([[0], c]))[1:] - c).max())
act = (S != 0) & (I != 0)
corr = float(np.corrcoef(S[act], I[act])[0, 1]) if act.sum() > 30 else float("nan")
both_loss = int(((S < 0) & (I < 0)).sum()); both_act = int(act.sum())
print(f"Periode {time.strftime('%Y-%m-%d', time.gmtime(START))} s.d. {time.strftime('%Y-%m-%d', time.gmtime(d1 * DAY))} · risiko swing {RS}% · intraday {RI}%")
print(f"Trade: swing {len(sw)} · intraday {len(it)}")
print(f"Total (% ekuitas, tanpa compounding): swing {S.sum():+.0f}% · intraday {I.sum():+.0f}% · gabungan {G.sum():+.0f}%")
print(f"Drawdown maks: swing {dd(S):.1f}% · intraday {dd(I):.1f}% · gabungan {dd(G):.1f}%  (jika independen sempurna ±{np.sqrt(dd(S)**2 + dd(I)**2):.1f}%)")
print(f"Korelasi hasil harian (hari keduanya ada trade tutup): {corr:+.2f}  ({both_act} hari)")
print(f"Hari keduanya rugi: {both_loss} dari {both_act} hari aktif bersama ({both_loss / max(both_act, 1) * 100:.0f}%)")
k = np.argsort(G)[:5]
print("5 hari gabungan terburuk:", ", ".join(f"{time.strftime('%Y-%m-%d', time.gmtime((d0 + j) * DAY))} {G[j]:+.1f}% (S {S[j]:+.1f} / I {I[j]:+.1f})" for j in k))
# bulan
mon = collections.defaultdict(lambda: [0.0, 0.0])
for j, d in enumerate(days):
    m = time.strftime("%Y-%m", time.gmtime(d * DAY)); mon[m][0] += S[j]; mon[m][1] += I[j]
mv = np.array(list(mon.values()))
print(f"Bulan: swing rugi {np.mean(mv[:, 0] < 0) * 100:.0f}% · intraday rugi {np.mean(mv[:, 1] < 0) * 100:.0f}% · "
      f"keduanya rugi {np.mean((mv[:, 0] < 0) & (mv[:, 1] < 0)) * 100:.0f}% · gabungan rugi {np.mean(mv.sum(1) < 0) * 100:.0f}%")
# risiko terbuka bersamaan (jumlah posisi terbuka x risiko)
ev = [(x["t0"], RS) for x in sw] + [(x["t1"], -RS) for x in sw] + [(x["t0"], RI) for x in it] + [(x["t1"], -RI) for x in it]
cur = mx = 0.0
for t, v in sorted(ev, key=lambda e: (e[0], e[1])): cur += v; mx = max(mx, cur)
print(f"Risiko terbuka maksimum bersamaan: {mx:.0f}% ekuitas (swing maks 10 posisi, intraday maks 3)")
same = sum(1 for a in it for b in sw if a["c"] == b["c"] and b["t0"] <= a["t0"] < b["t1"])
opp = sum(1 for a in it for b in sw if a["c"] == b["c"] and b["t0"] <= a["t0"] < b["t1"] and a["d"] != b["d"])
print(f"Trade intraday di koin yang sedang dipegang swing: {same} ({opp} berlawanan arah)")
