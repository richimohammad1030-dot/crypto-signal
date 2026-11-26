"""Sesi 27 Nov 2026 · uji langsung keluarga usulan T7 (riset/crypto/massal/keluarga_usulan.py) dengan penilaian SAMA dengan
saringan malam (riset/massal/inti.nilai, IS 2020-2023 / OOS 2024-skrg, stres 0,03R). Tidak menulis berkas massal/.
Pemakaian: python sesi_2026_11_27_t7.py <repo> <data_dir> [keluarga ...]"""
import importlib.util, os, sys, pickle
REPO, DATA = os.path.abspath(sys.argv[1]), sys.argv[2]
pilih = sys.argv[3:]
sys.path.insert(0, os.path.join(REPO, "riset", "massal"))
import inti, crypto as B
spec = importlib.util.spec_from_file_location("ku", os.path.join(REPO, "riset", "crypto", "massal", "keluarga_usulan.py"))
ku = importlib.util.module_from_spec(spec); spec.loader.exec_module(ku)
(a_is, b_is), (a_o, b_o) = B.PERIODE


def nilai3(tr):
    s = [dict(x, r=x["r"] - B.STRES) for x in tr]
    h = [inti.nilai(tr, B.RISIKO, a_is, b_is), inti.nilai(tr, B.RISIKO, a_o, b_o), inti.nilai(tr, B.RISIKO, a_is, None)]
    h[1]["stres"] = dict(pf=inti.nilai(s, B.RISIKO, a_o, b_o)["pf"])
    return h


def baris(nm, h):
    i, o, a = h
    return (f"{nm:<38} | IS PF {i['pf']:.2f} WR {i['wr']*100:2.0f}% {i['persen']:+6.1f}%/th DD {i['dd']:4.1f}% run {i['beruntun']:2d} rasio {i['rasio']:5.2f} "
            f"| OOS PF {o['pf']:.2f} WR {o['wr']*100:2.0f}% {o['persen']:+6.1f}% DD {o['dd']:4.1f}% run {o['beruntun']:2d} stres {o['stres']['pf']:.2f} "
            f"| semua minus {a['minus']} run {a['beruntun']} {a['n_lolos']}/7")


sys.argv = [sys.argv[0], "crypto", DATA]          # keluarga_usulan membaca data_dir dari argv[2] (konvensi jalan.py)
out = {}
jr = ku._jalan(); out["JUARA"] = nilai3(jr); print(baris("JUARA (replay ulang)", out["JUARA"]), flush=True)
for nm, f in sorted(vars(ku).items()):
    if not (callable(f) and nm[:2] == "CM" and nm[2:5].isdigit()): continue
    if pilih and nm not in pilih: continue
    for v, tr in f(None):
        out[v] = nilai3(tr); print(baris(v, out[v]), flush=True)
pickle.dump(out, open(f"{DATA}/sesi_1127_t7.pkl", "wb"))
pen = [k for k, h in out.items() if k != "JUARA" and inti.penantang(h[0], h[1], out["JUARA"][0], out["JUARA"][1])]
print("PENANTANG (inti.penantang):", pen)
print("T7 <= 10 di IS & OOS:", [k for k, h in out.items() if h[0]["beruntun"] <= 10 and h[1]["beruntun"] <= 10])
