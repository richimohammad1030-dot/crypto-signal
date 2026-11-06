"""Gabung bibit XAU H1 Dukascopy 2004-2014 (riset/data/xau_dukascopy_h1_2004_2014.json.gz, diunduh 6 Nov 2026) dengan data
2015-sekarang (mis. /tmp/data/xau_sambung.json atau xau_panjang.json) -> satu file JSON [[open_s, o, h, l, c], ...].
Pemakaian: python riset/gabung_xau_lama.py <xau_2015_skrg.json> <keluaran.json>"""
import gzip, json, os, sys
lama = json.load(gzip.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "xau_dukascopy_h1_2004_2014.json.gz"), "rt"))
baru = json.load(open(sys.argv[1]))
mulai = baru[0][0]
rows = [r for r in lama if r[0] < mulai] + baru
json.dump(rows, open(sys.argv[2], "w"))
print(f"{len(rows)} candle (lama {sum(1 for r in lama if r[0] < mulai)} + baru {len(baru)})")
