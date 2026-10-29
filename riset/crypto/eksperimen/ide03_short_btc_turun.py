"""Ide #3 · Filter short lebih ketat: SELL hanya jika tren BTC juga turun (replay penuh).
A: SELL hanya jika regime BTC = turun (close < EMA200 dan EMA100 < EMA200).
B: SELL diblokir jika regime BTC = naik (netral tetap boleh)."""
from _common import setup
rp, champ, _ = setup()
res = {}
res["A · SELL hanya saat BTC turun"] = rp.replay(lambda c, i, D, d, en, sl, t: d == 1 or rp.btc_regime(t) == -1)[0]
res["B · SELL diblokir saat BTC naik"] = rp.replay(lambda c, i, D, d, en, sl, t: d == 1 or rp.btc_regime(t) != 1)[0]
print(rp.HEADER)
print(rp.fmt_compare("Juara", rp.compare(champ, champ)))
for k, v in res.items():
    print(rp.fmt_compare(k, rp.compare(champ, v)))
for k, v in res.items():
    c = rp.compare(champ, v)
    print(k, "rasio per tahun:", {y: (round(a["rasio"], 1), round(b["rasio"], 1)) for y, (a, b) in c["yr"].items()})
    s = v[v.d == -1]; s0 = champ[champ.d == -1]
    print("  SELL juara", len(s0), round(s0.R.sum(), 1), "· SELL varian", len(s), round(s.R.sum(), 1),
          "· BUY juara", len(champ) - len(s0), round(champ[champ.d == 1].R.sum(), 1), "· BUY varian", len(v) - len(s), round(v[v.d == 1].R.sum(), 1))
