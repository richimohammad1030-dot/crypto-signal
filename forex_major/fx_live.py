"""MESIN HARIAN BOT FX MAJOR — dipakai bersama oleh bot live (fx_bot.py), replay kesetaraan, dan riset.
Memakai fungsi backtest yang sama persis (riset_putaran6/7), jadi sinyal live = backtest.

Strategi live (disetujui pemilik 20 Nov 2026, riset putaran 7; rincian riset/fx/STRATEGI.md), 7 pair, risiko 0,75%/posisi:
  UTAMA   07:00 WIB Selasa-Jumat: buy stop di high minggu lalu & sell stop di low minggu lalu (OCO per pair), SL 0,3 ATR(14) D1,
          TP 0,6 ATR, SL ke entry di +0,5R. Berlaku s/d 14:00 WIB. Maks 2 posisi/hari, 1/pair, maks 2 searah USD.
  SUSULAN pair yang UTAMA-nya tidak terisi: candle close 15:00 WIB -> pasang ulang level yang belum tertembus hari itu (OCO),
          SL 0,3 ATR, TP 0,8 ATR, berlaku s/d 23:00 WIB.
  LANJUT  setelah UTAMA/SUSULAN kena TP (sebelum 20:00 WIB): market searah di candle berikutnya, SL 0,4 ATR, TP 0,3 ATR.
  Semua ditutup 23:00 WIB."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import backtest as B
import riset_putaran4 as R4
import riset_putaran6 as P6          # memasang spread asli Exness Standard Cent
import riset_putaran7 as P7

PAIRS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD"]
UK = dict(dist=9.0, vol="none", dow="mon", slm=0.3, tpm=0.6, be=0.5, exp=7)
SK = dict(sl=0.3, tp=0.8, senin=False, at=0, um="mon")
B3K = dict(on="tp", dir="searah", entry="market", sl=0.4, tp=0.3)
RISK_PCT = 0.75
NAMA = {"N3": "UTAMA", "SUS": "SUSULAN", "B3": "LANJUT"}


def _sim(P, lst, d):
    return R4.simulate_be(P, lst, d) if lst and lst[0].get("be") else B.simulate_pair(P, lst, d)


def day(data, d):
    """Semua order & trade satu hari (UTC day d = 07:00 WIB s.d. 23:00 WIB) memakai data yang ada (boleh hari berjalan).
    Return dict: orders{bot: {pair: [order]}}, raw_utama (sebelum kuota), trades{bot: [trade]}."""
    out = dict(orders={"N3": {}, "SUS": {}, "B3": {}}, trades={})
    raw = []
    for P in data:
        lst = P6.utama_gen(UK)(P).get(d)
        if lst: out["orders"]["N3"][P.name] = lst; raw += _sim(P, lst, d)
    B.MAX_DAY = 2
    try: main = B.portfolio(raw)
    finally: B.MAX_DAY = 4
    out["raw_utama"] = raw; out["trades"]["N3"] = main
    filled = {(t["pair"], t["t"] // 86400) for t in main}; sus = []
    for P in data:
        lst = P7.sus_gen(SK, filled, UK["exp"])(P).get(d)
        if lst: out["orders"]["SUS"][P.name] = lst; sus += _sim(P, lst, d)
    out["trades"]["SUS"] = sus; b3 = []
    for P in data:
        lst = P7.bot3_gen(B3K, main + sus)(P).get(d)
        if lst: out["orders"]["B3"][P.name] = lst; b3 += _sim(P, lst, d)
    out["trades"]["B3"] = b3
    return out


def all_days(data):
    """Seluruh trade (semua bot) untuk semua hari di data — untuk replay & riset."""
    days = sorted({int(x) for P in data for x in P.days})
    tr = []
    for d in days:
        r = day(data, d)
        for k, v in r["trades"].items(): tr += v
    return sorted(tr, key=lambda x: x["t"])
