"""Mitigasi SL (sesi 29 Nov 2026): penilaian penantang F013 (BE SUSULAN) & F014 (SUSULAN kadaluarsa lebih awal) dari
keluarga_usulan.py: signifikansi vs juara (penuh & OOS), per tahun, stres, dan validasi M5 (4 pair 2020-2026).
Pemakaian: python riset/fx/eksperimen/mitigasi_sl_2026_11_29.py"""
import os, sys, time, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path[:0] = [os.path.join(REPO, "riset", "massal"), os.path.join(REPO, "forex_major"), HERE, os.path.join(REPO, "riset")]
import numpy as np
import fx as BANK, inti, signifikansi as SG, backtest as B, fx_live as F
sp = importlib.util.spec_from_file_location("u", os.path.join(REPO, "riset", "fx", "massal", "keluarga_usulan.py"))
U = importlib.util.module_from_spec(sp); sp.loader.exec_module(U)


def tahun(tr):
    y = {}
    for x in tr: k = time.gmtime(x["t1"]).tm_year; y[k] = y.get(k, 0) + x["r"]
    return {k: round(v, 1) for k, v in sorted(y.items())}


def nilai(M, nm, tr, J):
    a = inti.nilai(tr, 0.75, *BANK.PERIODE[0]); b = inti.nilai(tr, 0.75, *BANK.PERIODE[1])
    print(f"{nm:<34} IS PF {a['pf']:.2f} {a['persen']:+.1f}%/th DD {a['dd']:.1f}% minus {a['minus']} | OOS PF {b['pf']:.2f} "
          f"{b['persen']:+.1f}%/th DD {b['dd']:.1f}% minus {b['minus']} runtun {b['beruntun']}")
    if J is not None:
        for lbl, m in (("penuh", 1433116800), ("OOS", 1672531200)):
            r = SG.banding([(x["t1"], x["r"]) for x in J], [(x["t1"], x["r"]) for x in tr], mulai=m)
            print(f"     {lbl}: P_rasio {r['P_rasio_lebih_baik']:.3f} P_R {r['P_R_lebih_baik']:.3f} R/thn {r['juara']['R_thn']}→{r['penantang']['R_thn']} DD {r['juara']['DD']}→{r['penantang']['DD']}")
        print("     per tahun:", tahun(tr))


if __name__ == "__main__":
    for lbl, env in (("H1 Dukascopy 2015-2026 (7 pair)", None), ("M5 Dukascopy 2020-2026 (4 pair)", "data_m5/{pair}_m5_*.json.gz")):
        if env: os.environ["FX_DATA"] = env
        data = [P for P in (B.load(p) for p in F.PAIRS) if P is not None]
        M = BANK.Mesin(data); print(f"\n== {lbl} ==")
        J = M.tiga(); print("juara per tahun:", tahun(J)); nilai(M, "JUARA", J, None)
        for nm, kw in (("F014 SUSULAN s/d 22:00", dict(off_wib=22)), ("F014 SUSULAN s/d 21:00", dict(off_wib=21)),
                       ("F013 SUSULAN BE 1,5R", dict(be=1.5)), ("F013 SUSULAN BE 1,0R", dict(be=1.0)),
                       ("F013+F014 BE 1,5R s/d 22:00", dict(be=1.5, off_wib=22))):
            nilai(M, nm, U._tiga_sus(M, **kw), J)
