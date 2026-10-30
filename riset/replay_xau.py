"""Uji kesetaraan mesin bot XAU live (gold_bot.GoldEngine, via backtest_xau.py) vs mesin riset K6
(riset/xau/eksperimen/audit_mesin.py, OCO 2 sisi, hari dilewati bila sisi lawan tren EMA200 H1 terisi duluan; urutan candle
ambigu = asumsi bot, BUY duluan). Wajib IDENTIK sebelum perubahan bot XAU dipasang.
Pemakaian: python riset/replay_xau.py <repo> <xau.json> [<xau_lain.json> ...]"""
import sys, os, json, subprocess
REPO = sys.argv[1]
sys.path.insert(0, os.path.join(REPO, "riset", "xau", "eksperimen"))
import numpy as np
import audit_mesin as m
ok = True
for src in sys.argv[2:]:
    out = "/tmp/_replay_xau.csv"
    subprocess.run([sys.executable, os.path.join(REPO, "riset", "backtest_xau.py"), REPO, src, out], check=True, capture_output=True)
    D = m.muat(src); A = np.array(m.atr(list(D[2]), list(D[3]), list(D[4]), 14)); F = m.fitur(D, A)
    k6 = m.potong(m.jalankan({"tren_lawan_w": ("ema200", 0.0)}, D, A, F))
    hasil = m.cek_identik(out, k6)
    print(f"{os.path.basename(src)}: bot {sum(1 for _ in open(out)) - 1} trade vs riset K6 {len(k6)} -> {hasil}")
    ok &= hasil == "IDENTIK"
print("KESIMPULAN:", "mesin bot = riset K6" if ok else "BEDA - jangan pasang")
sys.exit(0 if ok else 1)
