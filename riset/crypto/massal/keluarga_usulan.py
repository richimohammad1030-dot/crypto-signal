"""Keluarga usulan sesi riset CRYPTO SWING (dimuat otomatis riset/massal/jalan.py; fungsi <KODE><3 digit>_... = satu keluarga).
Ditambahkan 27 Nov 2026 (sesi riset crypto) — fokus milestone T7 (kalah beruntun <= 10) + mitigasi penyebab SL terbesar.

Temuan analisis SL/runtun 27 Nov (eksperimen/runtun_sl.py, juara daftar tetap 2020-skrg, R_REAL):
  kalah = 743 cut-loss stagnan (-272R) + 550 rugi kecil trailing (-228R) + 171 SL penuh (-172R) dari 2.452 trade.
  20 runtun >= 11; isinya ±55% stagnan, tersebar 5-12 hari (bukan satu hari pembalikan) → batas posisi searah / jeda tidak
  cukup; dihitung per HARI pun runtun masih 15. Agar runtun <= 10 dengan ±2.400 trade, WR harus ±55%+ → yang perlu diubah
  adalah STRUKTUR KELUAR (trade yang sempat untung jangan berakhir rugi), bukan filter entry.

Keluarga di sini = REPLAY MESIN ASLI (daftar tetap, ±10 dtk/varian) dengan konstanta/aturan keluar diubah sementara.
Anti-optimis (ATURAN_BERSAMA G): SL dicek sebelum TP di candle yang sama (mesin asli); SL pindah ke impas baru berlaku candle
BERIKUTNYA setelah TP sebagian terisi; biaya REAL + stres 0,03R dari jalan.py."""
import os, sys, itertools

_RP = None


def _siap():
    """Muat mesin replay sekali (data_dir = argumen ke-2 jalan.py)."""
    global _RP
    if _RP is not None: return _RP
    repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    data = sys.argv[2]
    eks = os.path.join(repo, "riset", "crypto", "eksperimen"); sys.path.insert(0, eks)
    simpan = sys.argv[:]; sys.argv = [sys.argv[0], repo, data]
    try:
        import tahap0_semua_tahun as t0
    finally:
        sys.argv = simpan
    if not t0.rp.DATA: t0.rp.load(repo, data)
    _RP = t0
    return t0


def _jalan(ubah=None, impas=None, kecil=None):
    """Replay juara dengan konstanta signal_bot diubah (ubah) dan/atau SL pindah ke entry + impas*r0 setelah TP sebagian.
    kecil = (R_picu, R_kunci): setelah harga close candle cek >= R_picu, SL minimal di entry + R_kunci*r0 (tanpa TP)."""
    t0 = _siap(); sb = t0.rp.sb
    asli = {k: getattr(sb, k) for k in (ubah or {})}
    for k, v in (ubah or {}).items(): setattr(sb, k, v)
    f_asli, c_asli = sb.Engine.step_fill_exit, sb.Engine.step_check

    def fe(self, coin, i, D):
        f_asli(self, coin, i, D)
        p = (self.s["coins"].get(coin) or {}).get("pos")
        if impas is not None and p is not None and sb.pos_ext(p).get("part") and p[3] < D["T"][i]:
            d, e = p[0], p[1]; lv = e + d * impas * sb.pos_r0(p)
            if (lv - p[2]) * d > 0: p[2] = lv

    def ck(self, coin, i, D, allow):
        p = (self.s["coins"].get(coin) or {}).get("pos")
        if kecil is not None and p is not None:
            d, e = p[0], p[1]; r0 = sb.pos_r0(p)
            if r0 and (D["C"][i] - e) * d / r0 >= kecil[0]:
                lv = e + d * kecil[1] * r0
                if (lv - p[2]) * d > 0: p[2] = lv
        return c_asli(self, coin, i, D, allow)

    sb.Engine.step_fill_exit, sb.Engine.step_check = fe, ck
    try:
        df, _ = t0.run_replay()
        df = t0.add_costs(df)
    finally:
        sb.Engine.step_fill_exit, sb.Engine.step_check = f_asli, c_asli
        for k, v in asli.items(): setattr(sb, k, v)
    return [dict(t0=int(r.t_fill), t1=int(r.t_exit), r=float(r.R_REAL), w=1.0, strat="BUY" if r.d == 1 else "SELL", koin=r.coin)
            for r in df.itertuples()]


def CM005_keluar_t7(M):
    """T7 + mitigasi 'rugi kecil trailing': TP sebagian lebih awal/lebih besar + SL impas setelah TP sebagian.
    Trade yang sudah menyentuh TP sebagian tidak bisa lagi berakhir rugi → WR naik, runtun kalah memendek.
    (#67 lama hanya TP 25%@1R + impas dan dinilai dari rasio; di sini dinilai terhadap T7 + semua target.)"""
    for tr, fr, be in itertools.product((0.5, 0.75, 1.0), (0.25, 0.5), (None, 0.0, 0.1)):
        if (tr, fr, be) == (1.0, 0.25, None): continue
        yield f"CM005 TP{fr:g}@{tr:g}R impas{'-' if be is None else f'+{be:g}R'}", _jalan(dict(TP1_R=tr, TP1_FRAC=fr), impas=be)


def CM006_stagnan(M):
    """Mitigasi penyebab SL terbesar (cut-loss stagnan: 743 trade, -272R): ubah umur/ambang cut-loss.
    Stagnan memotong rugi tetapi juga menambah jumlah 'kalah' → diuji apakah runtun & PF lebih baik bila lebih longgar/ketat."""
    for hari, amb in itertools.product((1.0, 2.0, 3.0, 4.0, 99.0), (-0.1, -0.2, -0.35, -0.5)):
        if (hari, amb) == (2.0, -0.2) or (hari == 99.0 and amb != -0.2): continue
        yield f"CM006 stagnan {hari:g}h <{amb:g}R" if hari < 99 else "CM006 tanpa stagnan", _jalan(dict(STAG_DAYS=hari, STAG_R=amb))


def CM007_kunci_untung(M):
    """T7: kunci untung kecil tanpa TP — begitu close candle cek >= picu R, SL minimal di entry + kunci R."""
    for picu, kunci in ((0.5, 0.05), (0.75, 0.1), (1.0, 0.1), (1.0, 0.25), (1.5, 0.25), (1.5, 0.5), (2.0, 0.5)):
        yield f"CM007 kunci +{kunci:g}R setelah close >= {picu:g}R", _jalan(kecil=(picu, kunci))


def CM008_tp_awal_jeda(M):
    """Lanjutan CM005 (27 Nov): TP sebagian AWAL tanpa impas (terbaik T7 di CM005: TP50%@0,5R → runtun 12/13, PF IS 2,00 OOS 1,56)
    + kombinasi dengan jeda setelah k kalah beruntun (inti.jeda_beruntun, pasca-proses: slot yang kosong TIDAK diisi sinyal lain
    = konservatif untuk jumlah trade, tetapi wajib replay penuh bila lolos)."""
    import inti
    for tr, fr in itertools.product((0.3, 0.4, 0.5, 0.6), (0.5, 0.67, 0.75)):
        dasar = _jalan(dict(TP1_R=tr, TP1_FRAC=fr))
        yield f"CM008 TP{fr:g}@{tr:g}R", dasar
        for k in (5, 6, 7):
            yield f"CM008 TP{fr:g}@{tr:g}R + jeda {k} kalah", inti.jeda_beruntun(dasar, k)
