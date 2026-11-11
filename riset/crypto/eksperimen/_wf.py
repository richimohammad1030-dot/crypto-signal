"""WALK-FORWARD BERLABUH per 2 tahun (pemilik, 11 Nov 2026) untuk crypto swing, seluruh data Nov 2017 - skrg.
Daftar koin SESUAI MASANYA (snapshot CMC bulanan, logika riset/pit.py) — satu-satunya daftar yang adil untuk 2018-2019.
Funding: arsip Binance / HL; sebelum arsip ada (sblm Sep 2019) funding dianggap > 0 (SELL diizinkan; aturan B di tahap0_lama.py)
dan biaya funding long = proksi 0,01%/8 jam. Biaya REAL.
Jendela: pilih <= 2019 → uji 2020-21 · <= 2021 → 2022-23 · <= 2023 → 2024-25 · <= 2025 → 2026-27. Tahun uji 2020-skrg
SEMUANYA hasil uji. Aturan pilih tiap jendela (sama untuk semua ide): tahun minus paling sedikit di periode pilih, lalu R/thn;
varian terpilih wajib punya tetangga parameter yang juga lolos (diperiksa pemanggil, laporkan).
Pemakaian modul (data dari eksperimen/unduh_lama.py):
    import _wf; _wf.load(repo, data_lama)
    df = _wf.run(gate=None, ubah={"TRAIL": 96})        # replay penuh + biaya; gate(coin,i,D,d,en,sl,t) opsional
    hasil = _wf.walk({"juara": df0, "var A": dfA, ...})  # pilih per jendela, sambung hasil uji
Skrip: python _wf.py <repo> <data_lama>  → tabel sistem dasar (juara) per tahun 2018-skrg."""
import json, os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
JENDELA = [(2019, (2020, 2021)), (2021, (2022, 2023)), (2023, (2024, 2025)), (2025, (2026, 2027))]
MULAI = 2018
t0 = rp = sb = pit = None
UNI = None


def load(repo, data):
    global t0, rp, sb, pit, UNI
    sys.argv = [sys.argv[0], repo, data]
    import tahap0_semua_tahun as _t0
    t0 = _t0; rp = t0.rp
    sys.path.insert(0, repo); sys.path.insert(0, os.path.join(repo, "riset"))
    import signal_bot as _sb, pit as _pit
    sb, pit = _sb, _pit; rp.sb = sb
    pit._load(data)
    now = time.time() * 1000
    for fn in os.listdir(f"{data}/klines"):
        c = fn[:-5]
        rows = [r[:5] for r in json.load(open(f"{data}/klines/{fn}")) if r[5] < now]
        if len(rows) < sb.K + 1350: continue
        rp.DATA[c] = sb.prep(rows)
        rp.IDX[c] = {t: i for i, t in enumerate(rp.DATA[c]["T"])}
        rp.REG[c] = [sb._regime(rp.DATA[c], i) for i in range(len(rp.DATA[c]["T"]))]
        f = json.load(open(f"{data}/funding/{c}.json")) if os.path.exists(f"{data}/funding/{c}.json") else []
        h = json.load(open(f"{data}/funding_hl/{c}.json")) if os.path.exists(f"{data}/funding_hl/{c}.json") else []
        rp.FUND[c] = ([x[0] for x in f], [x[1] for x in f]); rp.FUND_HL[c] = ([x[0] for x in h], [x[1] for x in h])
    first = {c: int(d["T"][sb.K + 1300]) for c, d in rp.DATA.items()}
    UNI = pit.universe_fn(data, lambda c, t: c in first and first[c] <= t)


def fund_b(c, t):
    f = rp.funding_fn(c, t)
    if f is not None: return f
    ts = rp.FUND.get(c, ([], []))[0]
    return 1e-4 if (not ts or t < ts[0]) else None      # sebelum arsip ada: dianggap positif; sesudahnya: tidak ada = blok


def run(gate=None, ubah=None):
    """Replay penuh (daftar sesuai masanya) + biaya. ubah = {konstanta signal_bot: nilai} sementara."""
    asli = {k: getattr(sb, k) for k in (ubah or {})}
    for k, v in (ubah or {}).items(): setattr(sb, k, v)
    base = rp.make_engine_cls()

    class E(base):
        def run(self, data_, since_ts, univ=None):
            times = sorted({t for d in data_.values() for t in d["T"] if t > since_ts})
            idx = rp.IDX
            for t in times:
                U = univ(t); order = U + [c for c in data_ if c not in U]
                for coin in order:
                    i = idx[coin].get(t)
                    if i is not None and i >= max(sb.K, 1300): self.step_fill_exit(coin, i, data_[coin])
                if (t // 3600) % 24 in sb.CHECK_HOURS_UTC:
                    for coin in order:
                        i = idx[coin].get(t)
                        if i is None or i < max(sb.K, 1300): continue
                        cs = self.s["coins"].setdefault(coin, {"pend": None, "pos": None})
                        if coin not in U and not cs.get("pos"):
                            if cs.get("pend"): cs["pend"] = None
                            continue
                        allow = lambda c, old: self.slots_used() - (1 if self.s["coins"][c].get("pend") else 0) < sb.MAX_SLOTS
                        self.step_check(coin, i, data_[coin], allow)
    cur, rows = {}, []

    def notify(kind, coin, **k):
        if kind == "fill":
            cur[coin] = dict(coin=coin, d=k["d"], t_fill=k["t"], e=k["entry"], r0=k["r0"], sl0=k["sl"], t_part=None, px_part=None)
        elif kind == "partial": cur[coin].update(t_part=k["t"], px_part=k["px"])
        elif kind == "exit":
            x = cur.pop(coin); x.update(t_exit=k["t"], ex=k["exit"], why=k["why"], R=k["R"]); rows.append(x)
    eng = E({"coins": {}, "last_ts": 0, "replay": True}, fund_b, notify)
    eng.gate = gate
    eng.run(rp.DATA, 0, UNI)
    df = t0.add_costs(pd.DataFrame(rows))
    f0 = {c: (rp.FUND[c][0][0] if rp.FUND[c][0] else 1e18) for c in df.coin.unique()}
    hold8 = (np.minimum(df.t_exit, df.coin.map(f0)) - df.t_fill).clip(lower=0) / 28800
    prox = df.d * 0.0001 * hold8 * df.e / df.r0
    for k in ("REAL", "KONS"): df[f"R_{k}"] -= prox
    for k, v in asli.items(): setattr(sb, k, v)
    return df[df.year >= MULAI].reset_index(drop=True)


def per_tahun(df, col="R_REAL"):
    return df.groupby("year")[col].sum()


def skor(df, y_max):
    t = per_tahun(df[df.year <= y_max])
    return (int((t < 1).sum()), -float(t.mean()))           # tahun < +1R paling sedikit, lalu R/thn terbesar


def walk(varian, col="R_REAL"):
    """varian: {nama: df}. Return (tabel per tahun uji, pilihan per jendela, df uji tersambung)."""
    pilih, uji = [], []
    for y_max, (a, b) in JENDELA:
        nm = min(varian, key=lambda k: skor(varian[k], y_max))
        pilih.append((y_max, nm))
        uji.append(varian[nm][(varian[nm].year >= a) & (varian[nm].year <= b)])
    u = pd.concat(uji).sort_values("t_exit")
    return per_tahun(u, col), pilih, u


if __name__ == "__main__":
    load(sys.argv[1], sys.argv[2])
    df = run()
    df.to_csv(f"{sys.argv[2]}/wf_juara.csv", index=False)
    t = t0.year_table(df, "R_REAL")
    print(f"SISTEM DASAR (juara v2, sesuai masanya, {MULAI}-skrg): trade {len(df)} · {df.R_REAL.sum():+.1f}R · DD {t0.maxdd(df.R_REAL.values):.1f}R")
    print(t.round(2).to_string())
    print("tahun < +1R:", [y for y, v in t.R.items() if v < 1] or "tidak ada")
