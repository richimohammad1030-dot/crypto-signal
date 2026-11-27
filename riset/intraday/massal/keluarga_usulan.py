"""USULAN keluarga baru untuk bank saringan massal riset/massal/intraday.py (ATURAN_BERSAMA F.2c), sesi 25 Nov 2026.
Sesi riset intraday hanya boleh menulis di riset/intraday/ -> keluarga ini DITITIPKAN di sini; salin ke riset/massal/intraday.py
(dan tambahkan ke KELUARGA) dari chat project bila disetujui.
Celah yang diserang: T2 (monitor edge). Uji sesi 25 Nov (eksperimen/sesi_2026-11-25.py) menunjukkan monitor 365 hari tingkat bot
tidak pernah aktif pada juara (PF 365 hari selalu > 1) -> T2 terpenuhi sebagai PENGAMAN, bukan penambah edge. Keluarga ini
memetakan seberapa sensitif monitor per modul/koin terhadap jendela & bobot (tetangga parameter) agar desain T2 dipilih dari
dataran yang stabil, bukan satu angka."""
import itertools
import inti


def IM006_monitor_modul(M):
    """Monitor PF per strategi (A / B) dengan bobot turun bertingkat; w > 0 tidak mengubah slot (pasca-trade = tepat)."""
    base = M.trades()
    for hari, amb, w in itertools.product((120, 180, 270, 365, 540), (0.95, 1.0, 1.05), (0.25, 0.5, 0.75)):
        yield f"IM006 monitorPF modul {hari}h <{amb} w{w}", inti.monitor_pf(base, hari, amb, w, 20, "strat")


# ============================================================== sesi 28 Nov 2026 (review bulanan)
# Keluarga di bawah membutuhkan arah trade (d) dan limit -> trade dihitung ulang dari BI.orders + BI.portfolio (daftar koin bot,
# sama dengan juara di saringan malam). Bobot w > 0 tidak mengubah slot (pasca-trade = tepat); w = 0 hanya saringan kasar.
import numpy as np, bisect as _bis
_CACHE = {}

def _trade_lengkap(M):
    if "tr" not in _CACHE:
        import backtest_intraday as BI, signal_bot as sb
        P = dict(BI.PARAM)
        _, taken = BI.portfolio(BI.orders(M.H1, M.M15, P), sb.COINS, P["CAP"], P["PEND"])
        _CACHE["tr"] = sorted(taken, key=lambda o: o["t_exit"])
    return _CACHE["tr"]

def _struktur(M):
    """Skill 2 STRUKTUR (definisi tahap 0, 25 Nov): pivot fraktal n=3 H1, NAIK = HH+HL, TURUN = LH+LL; peristiwa BOS/CHoCH."""
    if "st" in _CACHE: return _CACHE["st"]
    out = {}
    for c, G in M.H1.items():
        H, L, C = G["H"], G["L"], G["C"]; n = len(C); m = 3
        ph = np.zeros(n, bool); pl = np.zeros(n, bool)
        if n > 2 * m + 1:
            w = np.lib.stride_tricks.sliding_window_view
            ph[m:n - m] = H[m:n - m] >= w(H, 2 * m + 1).max(axis=1); pl[m:n - m] = L[m:n - m] <= w(L, 2 * m + 1).min(axis=1)
        state = np.zeros(n, np.int8); ev = np.zeros(n, np.int8); sh = [np.nan, np.nan]; sl = [np.nan, np.nan]; s = 0
        for k in range(n):
            i = k - m
            if i >= m:
                if ph[i]: sh = [sh[1], H[i]]
                if pl[i]: sl = [sl[1], L[i]]
                if sh[0] == sh[0] and sl[0] == sl[0]:
                    s = 1 if (sh[1] > sh[0] and sl[1] > sl[0]) else (-1 if (sh[1] < sh[0] and sl[1] < sl[0]) else 0)
            if k > 0 and sh[1] == sh[1] and sl[1] == sl[1]:
                up = C[k] > sh[1] >= C[k - 1]; dn = C[k] < sl[1] <= C[k - 1]
                if s == 1: ev[k] = 2 if up else (-1 if dn else 0)
                elif s == -1: ev[k] = -2 if dn else (1 if up else 0)
            state[k] = s
        out[c] = (G["T"], state, ev)
    _CACHE["st"] = out
    return out

def _ke_inti(tr, w_fn):
    return sorted([dict(t0=o["t_fill"], t1=o["t_exit"], r=o["R"] * w_fn(o), w=1.0, strat=o["m"], koin=o["c"]) for o in tr if w_fn(o) > 0],
                  key=lambda x: x["t1"])

def IM007_struktur_bobot(M):
    """Skill 2 STRUKTUR tahap 2 sebagai BOBOT RISIKO: kecilkan order yang melawan struktur H1 (state berlawanan) atau yang
    didahului CHoCH berlawanan dalam N jam. Modul A / B / AB, w 0 / 0,25 / 0,5. Mencegah: entry melawan tren yang sebenarnya."""
    tr = _trade_lengkap(M); S = _struktur(M)
    def lawan(o, mode, jam):
        T, state, ev = S[o["c"]]; k = _bis.bisect_right(T, o["t"] - 3600) - 1
        if k < 50: return False
        if mode == "S": return int(state[k]) == -o["d"]
        if mode == "N": return int(state[k]) != o["d"]          # tidak searah (lawan atau acak)
        return bool(np.any(ev[max(0, k - jam + 1):k + 1] == -o["d"]))
    for mod in ("A", "B", "AB"):
        for mode, jam in (("S", 0), ("N", 0), ("C", 12), ("C", 24), ("C", 48)):
            for w in (0.0, 0.25, 0.5):
                f = lambda o, mod=mod, mode=mode, jam=jam, w=w: (w if (o["m"] in mod and lawan(o, mode, jam)) else 1.0)
                yield f"IM007 struktur {mode}{jam or ''} {mod} w{w}", _ke_inti(tr, f)

def IM008_snr_bobot(M):
    """Skill 1 SNR cara pakai baru (T10, 28 Nov): jarak limit ke level PERIODE (high/low hari & minggu sebelumnya) sebagai bobot
    risiko. Modul B / B-long / B-short / A, x 0,1-0,75 ATR, w 0 / 0,25 / 0,5 / 0,75."""
    tr = _trade_lengkap(M)
    if "lv" not in _CACHE:
        lv = {}
        for c, G in M.H1.items():
            d = G["T"] // 86400; wk = (d + 3) // 7; tab = []
            for key in (d, wk):
                u, inv = np.unique(key, return_inverse=True)
                mx = np.full(len(u), -np.inf); mn = np.full(len(u), np.inf); np.maximum.at(mx, inv, G["H"]); np.minimum.at(mn, inv, G["L"])
                tab.append((dict(zip(u.tolist(), mx.tolist())), dict(zip(u.tolist(), mn.tolist()))))
            lv[c] = tab
        _CACHE["lv"] = lv
    LV = _CACHE["lv"]
    def jarak(o):
        (dh, dl), (wh, wl) = LV[o["c"]]; d = o["t"] // 86400; wk = (d + 3) // 7
        G = M.H1[o["c"]]; k = _bis.bisect_right(G["T"], o["t"] - 3600) - 1; a = float(G["A"][k]); ent = o.get("entry", 0.0)
        lvs = [x for x in (dh.get(d - 1), dl.get(d - 1), wh.get(wk - 1), wl.get(wk - 1)) if x is not None]
        return min((abs(x - ent) / a for x in lvs), default=99.0)
    J = {id(o): jarak(o) for o in tr}
    for mod in ("B", "B1", "B-1", "A"):
        cocok = lambda o, mod=mod: (o["m"] == mod) if mod in ("A", "B") else (o["m"] == "B" and o["d"] == int(mod[1:]))
        for x in (0.1, 0.25, 0.5, 0.75):
            for w in (0.0, 0.25, 0.5, 0.75):
                yield f"IM008 snr-bobot {mod} x{x} w{w}", _ke_inti(tr, lambda o, x=x, w=w, cocok=cocok: w if (cocok(o) and J[id(o)] <= x) else 1.0)
