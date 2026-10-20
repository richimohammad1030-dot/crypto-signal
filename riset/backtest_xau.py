"""Replay strategi XAU memakai GoldEngine asli dari gold_bot.py. Argumen: <repo> <xau.json> <out_csv>"""
import sys, json, csv
REPO, SRC, OUT = sys.argv[1:4]
sys.path.insert(0, REPO)
import gold_bot as gb
rows = json.load(open(SRC))
trades = []
def notify(kind, **k):
    if kind == "exit":
        trades.append(dict(d=k["d"], t0=k["t0"], t1=k["t"], e=k["entry"], ex=k["exit"], R=k["R"], why=k["why"]))
state = {"last_ts": 0, "replay": True}
gb.GoldEngine(state, notify).run(rows, 0)
with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(trades[0])); w.writeheader(); w.writerows(trades)
print("trade selesai:", len(trades))
