"""Uji kesetaraan mesin bot XAU live (gold_bot.GoldEngine, via backtest_xau.py) vs mesin riset baseline multi-strategi
(riset/xau/eksperimen/multi_mesin.baseline; urutan candle ambigu = asumsi bot, BUY duluan). Wajib IDENTIK sebelum dipasang.
Pemakaian: python riset/replay_xau.py <repo> <xau.json> [<xau_lain.json> ...]"""
import sys, os, csv, subprocess
REPO = sys.argv[1]
sys.path.insert(0, os.path.join(REPO, "riset", "xau", "eksperimen"))
import numpy as np
import audit_mesin as m
import multi_mesin as mm
ok = True
for src in sys.argv[2:]:
    out = "/tmp/_replay_xau.csv"
    subprocess.run([sys.executable, os.path.join(REPO, "riset", "backtest_xau.py"), REPO, src, out], check=True, capture_output=True)
    bot = list(csv.DictReader(open(out)))
    D = m.muat(src); A = np.array(m.atr(list(D[2]), list(D[3]), list(D[4]), 14)); F = m.fitur(D, A)
    ref = mm.baseline(D, A, F)
    beda = sum(1 for b, r in zip(bot, ref) if int(float(b["t0"])) != int(r["t0"]) or int(b["d"]) != r["d"]
               or abs(float(b["R"]) - r["R"]) > 1e-9 or b.get("strat", r["strat"]) != r["strat"]) + abs(len(bot) - len(ref))
    nmr = sum(1 for r in ref if r["strat"] == "MR")
    print(f"{os.path.basename(src)}: bot {len(bot)} trade vs riset {len(ref)} (MR {nmr}, K6 {len(ref) - nmr}) -> {'IDENTIK' if beda == 0 else f'BEDA {beda}'}")
    ok &= beda == 0
print("KESIMPULAN:", "mesin bot = riset baseline" if ok else "BEDA - jangan pasang")
sys.exit(0 if ok else 1)
