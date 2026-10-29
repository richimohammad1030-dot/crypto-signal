"""I-02: kadaluarsa order modul B 4/6/8/10/12(juara)/16 jam. Replay penuh lewat bi.portfolio().
Pemakaian: python3 i02_kadaluarsa_b.py /tmp/data"""
import json, sys
from _umum import bi, sb, orders_mod, ringkas, keputusan, baris
D = sys.argv[1]
A = orders_mod(D, {}, "A")
res = {}
for jam in [4, 6, 8, 10, 12, 16]:
    B = orders_mod(D, {"B_VALID_JAM": jam}, "B")
    sent, taken = bi.portfolio(A + B, sb.COINS, bi.PARAM["CAP"], bi.PARAM["PEND"])
    res[jam] = ringkas(sent, taken)
base = res[12]
for jam, s in res.items():
    print(baris(f"B_VALID {jam}j" + (" *" if jam == 12 else ""), s, None if jam == 12 else keputusan(base, s)))
json.dump({str(k): v for k, v in res.items()}, open(sys.argv[2] if len(sys.argv) > 2 else "/tmp/i02.json", "w"))
