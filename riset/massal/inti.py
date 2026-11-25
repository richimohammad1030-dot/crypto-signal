"""SARINGAN MASSAL · inti bersama semua bot (pemilik, 24 Nov 2026; riset/MILESTONE_2026.md).
GitHub Actions menguji ratusan-ribuan varian tiap malam TANPA token; sesi Claude cukup membaca peringkat & memutuskan.

Satuan bersama: trade = dict(t0, t1, r) dengan r = R BERSIH biaya, sudah dikali bobot (w). Persen = r x risiko%.
Penilaian terhadap target milestone (T1 tahun minus, T3 PF, T4 WR, T5 %/thn, T6 DD, T7 kalah beruntun, T8 frekuensi) di IS
dan OOS terpisah. Varian = PENANTANG bila (1) di IS lebih baik dari juara pada kunci peringkat, (2) OOS tidak lebih buruk
(PF OOS > 1,1, tidak ada tahun minus OOS baru, rasio OOS ≥ 0,8 x juara). Penantang BUKAN usulan live: sesi riset mengujinya
dengan walk-forward + P_rasio (ATURAN_BERSAMA) lalu bayangan.
Catatan jujur: makin banyak varian, makin banyak yang lolos karena kebetulan -> gerbang akhir tidak boleh dilonggarkan."""
import bisect, datetime as dt, hashlib, json, os
import numpy as np

WIB = dt.timezone(dt.timedelta(hours=7))
TARGET = dict(pf=1.10, wr=0.40, persen=10.0, dd=20.0, beruntun=10)


def tahun(t):
    return dt.datetime.fromtimestamp(int(t), WIB).year


def ts(s):
    return dt.datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=WIB).timestamp()


# ---------------- T2: monitor edge (adaptif) — tanpa melihat masa depan ----------------
def monitor_pf(trades, hari=365, ambang=1.0, w_turun=0.5, min_n=20, kunci=None):
    """Bobot trade dikali w_turun bila PF trade yang SUDAH TUTUP (t1 < t0) dalam `hari` terakhir < ambang (min_n trade).
    kunci=None -> seluruh bot; kunci='strat' -> per strategi (strategi yang edge-nya hilang diperkecil/dimatikan sendiri).
    trades: dict(t0,t1,r,...) r BERSIH tanpa bobot monitor. Mengembalikan daftar baru (w_turun=0 -> trade dibuang)."""
    grup = {}
    for x in trades: grup.setdefault(x.get(kunci) if kunci else 0, []).append(x)
    out = []
    for g in grup.values():
        tutup = sorted(g, key=lambda x: x["t1"]); t1s = [x["t1"] for x in tutup]
        pos = np.cumsum([max(x["r"], 0) for x in tutup]); neg = np.cumsum([max(-x["r"], 0) for x in tutup])
        for x in g:
            j = bisect.bisect_left(t1s, x["t0"]); i = bisect.bisect_left(t1s, x["t0"] - hari * 86400)
            n = j - i; k = 1.0
            if n >= min_n:
                p = pos[j - 1] - (pos[i - 1] if i else 0); q = neg[j - 1] - (neg[i - 1] if i else 0)
                if q > 0 and p / q < ambang: k = w_turun
            if k > 0: out.append(dict(x, r=x["r"] * k, w=x.get("w", 1.0) * k))
    return sorted(out, key=lambda x: x["t1"])


def monitor_ekuitas(trades, n=20, w_turun=0.5):
    """Filter kurva ekuitas: bobot turun bila jumlah r n trade terakhir yang sudah tutup < 0."""
    tutup = sorted(trades, key=lambda x: x["t1"]); t1s = [x["t1"] for x in tutup]; cs = np.cumsum([x["r"] for x in tutup])
    out = []
    for x in trades:
        j = bisect.bisect_left(t1s, x["t0"]); k = 1.0
        if j >= n and cs[j - 1] - (cs[j - n - 1] if j > n else 0) < 0: k = w_turun
        if k > 0: out.append(dict(x, r=x["r"] * k, w=x.get("w", 1.0) * k))
    return sorted(out, key=lambda x: x["t1"])


def jeda_beruntun(trades, k=5, sampai="menang_bayangan"):
    """T7: setelah k kalah berturut-turut (trade yang sudah tutup), trade berikutnya DILEWATI sampai satu trade bayangan
    (yang dilewati tetap dihitung di belakang layar) menang. Tanpa melihat masa depan: status dihitung dari trade tutup < t0."""
    semua = sorted(trades, key=lambda x: x["t0"]); tutup = sorted(semua, key=lambda x: x["t1"])
    out, ambil, j, runtun, jeda = [], set(), 0, 0, False
    for x in semua:
        while j < len(tutup) and tutup[j]["t1"] < x["t0"]:
            y = tutup[j]; j += 1
            if id(y) in ambil:
                runtun = runtun + 1 if y["r"] < 0 else 0
                if runtun >= k: jeda = True
            elif jeda and y["r"] > 0:
                jeda, runtun = False, 0
        if not jeda: ambil.add(id(x)); out.append(x)
    return sorted(out, key=lambda x: x["t1"])


# ---------------- penilaian ----------------
def nilai(trades, risiko, a=None, b=None, minggu_min=0.0):
    tr = sorted([x for x in trades if (a is None or x["t0"] >= ts(a)) and (b is None or x["t0"] < ts(b))], key=lambda x: x["t1"])
    if len(tr) < 10:
        return None
    r = np.array([x["r"] for x in tr]); win, los = r[r > 0], r[r < 0]
    th = {}
    for x in tr: th[tahun(x["t1"])] = th.get(tahun(x["t1"]), 0.0) + x["r"]
    y0, y1 = min(th), max(th)
    for y in range(y0, y1 + 1): th.setdefault(y, 0.0)
    eq = np.cumsum(r); ddR = float(np.max(np.maximum.accumulate(np.concatenate([[0], eq]))[1:] - eq))
    e = np.cumprod(1 + risiko / 100 * r); ddp = float(np.max(1 - e / np.maximum.accumulate(np.concatenate([[1], e]))[1:])) * 100
    best = cur = 0
    for v in r:
        cur = cur + 1 if v < 0 else 0; best = max(best, cur)
    lama = max((tr[-1]["t1"] - tr[0]["t0"]) / (365.25 * 86400), 0.25)
    rthn = float(r.sum()) / lama
    s = dict(n=len(r), pf=float(win.sum() / -los.sum()) if len(los) else 99.0, wr=float((r > 0).mean()), rthn=rthn,
             persen=rthn * risiko, dd=ddp, ddR=ddR, beruntun=best, mgg=len(r) / (lama * 52.18),
             minus=sorted(y for y, v in th.items() if v < 0), thn={y: round(v * risiko, 1) for y, v in sorted(th.items())},
             rasio=rthn / ddR if ddR > 0 else 99.0)
    # risiko yang membuat DD tepat 20% (dibatasi 1%) dan %/thn pada risiko itu: ukuran efisiensi bebas skala
    s["risiko20"] = min(1.0, risiko * TARGET["dd"] / ddp) if ddp > 0 else 1.0
    s["persen20"] = rthn * s["risiko20"]
    lolos = {"T1": not s["minus"], "T3": s["pf"] > TARGET["pf"], "T4": s["wr"] >= TARGET["wr"], "T5": s["persen"] >= TARGET["persen"],
             "T6": s["dd"] <= TARGET["dd"], "T7": s["beruntun"] <= TARGET["beruntun"], "T8": s["mgg"] >= minggu_min}
    s["lolos"] = lolos; s["n_lolos"] = sum(lolos.values())
    return s


def kunci(s):
    """Peringkat (makin kecil makin baik): tahun minus, jumlah target gagal, lalu efisiensi (rasio R/thn : DD)."""
    return (len(s["minus"]), -s["n_lolos"], -s["rasio"])


def penantang(si, so, ji, jo):
    if not (si and so and ji and jo): return False
    lebih_baik = len(si["minus"]) < len(ji["minus"]) or (len(si["minus"]) == len(ji["minus"]) and si["rasio"] >= 1.25 * ji["rasio"])
    return (lebih_baik and si["n_lolos"] >= ji["n_lolos"] and so["pf"] > TARGET["pf"] and len(so["minus"]) <= len(jo["minus"])
            and so["rasio"] >= 0.8 * jo["rasio"])


def id_varian(nama):
    return hashlib.sha1(nama.encode()).hexdigest()[:10]


def baris(s):
    if not s: return "– | – | – | – | – | – | –"
    return (f"{len(s['minus'])} | {s['pf']:.2f} | {s['wr']*100:.0f}% | {s['persen']:+.1f}% | {s['dd']:.1f}% | {s['beruntun']} | "
            f"{s['rasio']:.2f} | {s['persen20']:+.1f}% @{s['risiko20']:.2f}% | {s['n_lolos']}/7")


def tulis(bot, folder, hasil, juara, periode, catatan=""):
    """hasil: list (nama, s_is, s_oos, s_all). Menulis <folder>/hasil-TGL.md, terbaru.md, penantang.json."""
    os.makedirs(folder, exist_ok=True)
    tgl = dt.datetime.now(WIB).strftime("%Y-%m-%d")
    urut, jejak = [], set()
    for h in sorted([h for h in hasil if h[1]], key=lambda h: kunci(h[1])):     # buang varian kembar (statistik sama persis)
        f = (h[1]["n"], round(h[1]["rthn"], 4), round(h[1]["ddR"], 4))
        if f not in jejak: jejak.add(f); urut.append(h)
    pen = [h for h in urut if penantang(h[1], h[2], juara[1], juara[2])]
    hdr = "| Varian | minus IS | PF | WR | %/thn | DD | beruntun | rasio | %/thn @DD20 | target | OOS minus | PF | WR | %/thn | DD | beruntun | rasio | %/thn @DD20 | target |\n|" + "---|" * 19 + "\n"
    rows = lambda hs: "".join(f"| {h[0]} | {baris(h[1])} | {baris(h[2])} |\n" for hs_ in [hs] for h in hs_)
    teks = (f"# Saringan massal {bot.upper()} · {tgl}\n{catatan}\nIS {periode[0]} · OOS {periode[1]}. Varian diuji malam ini: {len(hasil)}. "
            f"PENANTANG: {len(pen)} (unik) (lolos syarat inti.penantang; belum usulan — wajib WF + P_rasio + bayangan).\n\n"
            f"## Juara\n{hdr}{rows([juara])}\n## Penantang (maks 20)\n{hdr}{rows(pen[:20])}\n## 20 teratas IS (semua)\n{hdr}{rows(urut[:20])}\n"
            f"Tahun minus juara (semua data): {juara[3]['minus'] if juara[3] else '-'}\n")
    for h in pen[:5]:
        teks += f"- {h[0]}: tahun minus {h[3]['minus'] if h[3] else '-'} · %/thn per tahun {h[3]['thn'] if h[3] else '-'}\n"
    open(os.path.join(folder, f"hasil-{tgl}.md"), "w").write(teks)
    open(os.path.join(folder, "terbaru.md"), "w").write(teks)
    lama = json.load(open(os.path.join(folder, "penantang.json"))) if os.path.exists(os.path.join(folder, "penantang.json")) else {}
    for h in pen[:10]:
        lama.setdefault(h[0], dict(sejak=tgl, is_=h[1]["rasio"], oos=h[2]["rasio"], minus=h[3]["minus"] if h[3] else None,
                                   status="penantang"))
    json.dump(lama, open(os.path.join(folder, "penantang.json"), "w"), indent=1, ensure_ascii=False)
    def kecil(h):
        return dict(nama=h[0], **{k: ({kk: vv for kk, vv in v.items() if kk != "thn"} if isinstance(v, dict) and v else v)
                                  for k, v in (("is_", h[1]), ("oos", h[2]))}, semua=h[3])
    # penantang terbaik DIGABUNG dengan run sebelumnya: malam yang hanya menguji keluarga baru tidak menghapus temuan lama
    p_ring = os.path.join(folder, "ringkas.json")
    lama_r = json.load(open(p_ring)) if os.path.exists(p_ring) else {}
    gab = {x["nama"]: x for x in (lama_r.get("penantang") or [])}
    for h in pen[:5]: gab[h[0]] = kecil(h)
    kunci2 = lambda x: (len(x["is_"]["minus"]), -x["is_"]["n_lolos"], -x["is_"]["rasio"]) if x.get("is_") else (99, 0, 0)
    json.dump(dict(tanggal=tgl, n_varian=len(hasil), n_penantang=len(pen), juara=kecil(juara),
                   penantang=sorted(gab.values(), key=kunci2)[:5], teratas=[kecil(h) for h in urut[:5]]),
              open(os.path.join(folder, "ringkas.json"), "w"), indent=1, default=float)
    p_riw = os.path.join(folder, "riwayat.json")
    riw = json.load(open(p_riw)) if os.path.exists(p_riw) else []
    best = urut[0] if urut else None
    riw.append(dict(tanggal=tgl, n_varian=len(hasil), n_penantang=len(pen),
                    terbaik=dict(nama=best[0], minus=len(best[3]["minus"]) if best[3] else None, pf=best[3]["pf"] if best[3] else None,
                                 rasio=best[3]["rasio"] if best[3] else None) if best else None))
    json.dump(riw[-120:], open(p_riw, "w"), indent=1, default=float)
    ring = (f"🔬 Saringan malam {bot.upper()}: {len(hasil)} varian · penantang baru {len(pen)}\n"
            f"Juara: {baris(juara[3]).split(' | ')[0]} thn minus, PF {juara[3]['pf']:.2f}, {juara[3]['persen']:+.1f}%/thn, DD {juara[3]['dd']:.0f}%\n")
    if pen:
        h = pen[0]; ring += f"Teratas: {h[0]}\n  semua: minus {len(h[3]['minus'])}, PF {h[3]['pf']:.2f}, WR {h[3]['wr']*100:.0f}%, {h[3]['persen']:+.1f}%/thn, DD {h[3]['dd']:.0f}%, beruntun {h[3]['beruntun']}\n"
    return ring, pen
