"""Review bulanan XAU: statistik juara (per kuartal, BUY vs SELL, alasan keluar) dan live vs backtest
sejak LIVE_START XAU. Argumen: <repo> <xau.json>"""
import sys, json, os, datetime as dt, umum as u
REPO, SRC = sys.argv[1:3]
sys.path.insert(0, REPO)
from kesehatan import LIVE_START
T, O, H, L, C = u.muat(SRC)
tr = u.replay(T, O, H, L, C)
J = u.ringkas("juara", tr)
print("## Juara per kuartal (bersih biaya)\n" + u.HDR)
for q, s in J["kuartal"].items(): print(u.baris(q, s))
print("\n## BUY vs SELL\n" + u.HDR)
for d, nm in ((1, "BUY"), (-1, "SELL")):
    for key in ("P1 2025", "P2 2026"):
        print(u.baris(f"{nm} {key}", u.stat([t for t in tr if t["d"] == d and u.paruh(t) == key])))
print("\n## Alasan keluar\n| Alasan | Trade | Porsi | R kotor rata-rata | Total R bersih |\n|---|---|---|---|---|")
for w in ("SL", "TP", "23:00"):
    x = [t for t in tr if t["why"] == w]
    print(f"| {w} | {len(x)} | {len(x)/len(tr)*100:.0f}% | {sum(t['R'] for t in x)/len(x):+.2f} | {u.net(x).sum():+.1f} |")

ls = LIVE_START["xau"]
st = json.load(open(os.path.join(REPO, "gold_state.json")))
live = sorted([h for h in st.get("hist", []) if h[3] >= ls], key=lambda h: h[2])
bt = [t for t in tr if t["t1"] >= ls]
bmap = {t["t0"]: t for t in bt}
lmap = {h[2]: h for h in live}
print(f"\n## Live vs backtest sejak {u.wib(ls):%d %b %Y} WIB\n| Tanggal entry (WIB) | Sisi live | R live | Sisi backtest | R backtest | Cocok |\n|---|---|---|---|---|---|")
for k in sorted(set(bmap) | set(lmap)):
    h, b = lmap.get(k), bmap.get(k)
    ok = h and b and h[1] == b["d"] and abs(h[6] - b["R"]) < 0.01
    print(f"| {u.wib(k):%a %d %b %H:%M} | {('BUY' if h[1]==1 else 'SELL') if h else '-'} | {h[6]:+.2f} | " if h else f"| {u.wib(k):%a %d %b %H:%M} | - | - | ", end="")
    print(f"{('BUY' if b['d']==1 else 'SELL') if b else '-'} | {b['R']:+.2f} | {'ya' if ok else 'TIDAK'} |" if b else "- | - | TIDAK |")
sl = sum(h[6] for h in live); sb = sum(t["R"] for t in bt)
print(f"\nLive: {len(live)} trade, total {sl:+.2f}R kotor. Backtest: {len(bt)} trade, total {sb:+.2f}R kotor. Selisih {sl-sb:+.2f}R.")
