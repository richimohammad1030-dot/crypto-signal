"""Bangun data dashboard monitoring riset (pemilik, 24 Nov 2026). Dijalankan workflow dashboard.yml (tiap 30 menit + setelah
rutinitas/saringan/laporan) -> _site/data.json + halaman docs/index.html -> GitHub Pages.
Sumber: riset/milestone.json (global), riset/<bot>/status.json, RAPOR.md, massal/{ringkas,riwayat,penantang}.json,
riset/harian/<bot>.md, riset/laporan/<bot>/, git log.
Pemakaian: python riset/dashboard/bangun.py <repo> <out_dir>"""
import datetime as dt, glob, json, os, re, shutil, subprocess, sys

REPO, OUT = os.path.abspath(sys.argv[1]), sys.argv[2]
WIB = dt.timezone(dt.timedelta(hours=7))
BOTS = ["xau", "fx", "crypto", "intraday"]
now = dt.datetime.now(WIB)


def baca_json(p, bawaan=None):
    try: return json.load(open(p))
    except Exception: return bawaan


def rapor(b):
    p = os.path.join(REPO, "riset", b, "RAPOR.md"); rows = []
    if not os.path.exists(p): return rows
    hdr = None
    for ln in open(p):
        if not ln.startswith("|") or set(ln.strip()) <= set("|-"): continue
        sel = [c.strip() for c in ln.strip().strip("|").split("|")]
        if hdr is None: hdr = sel; continue
        rows.append(dict(zip(hdr, sel)))
    return rows


def harian(b):
    p = os.path.join(REPO, "riset", "harian", f"{b}.md")
    if not os.path.exists(p): return None
    teks = open(p).read(); judul = teks.splitlines()[0].lstrip("# ").strip() if teks else ""
    langkah = [dict(judul=m.group(1).strip(), ok=m.group(2) == "OK", menit=float(m.group(3)))
               for m in re.finditer(r"^### (.+?) (OK|GAGAL) \(([\d.]+) mnt\)", teks, re.M)]
    return dict(judul=judul, langkah=langkah)


def laporan(b):
    fs = sorted(glob.glob(os.path.join(REPO, "riset", "laporan", b, "riset-*.md")))
    if not fs: return None
    f = fs[-1]; teks = open(f).read()
    return dict(file=os.path.basename(f), tanggal=re.search(r"(\d{4}-\d{2}-\d{2})", f).group(1), jumlah=len(fs),
                cuplikan=teks[:1500])


def aktivitas():
    try:
        out = subprocess.run(["git", "log", "-300", "--pretty=%ct\x1f%s\x1f%an"], cwd=REPO, capture_output=True, text=True).stdout
    except Exception:
        return []
    akt = []
    for ln in out.splitlines():
        try: t, s, a = ln.split("\x1f")
        except ValueError: continue
        if re.search(r"\bstate\b", s) and len(s) < 40: continue
        sl = s.lower()
        jenis = ("sesi" if "laporan riset" in sl or sl.startswith("riset") else "saringan" if "saringan" in sl
                 else "harian" if "rutinitas harian" in sl else "bot" if any(k in sl for k in ("bot", "gold", "fx", "sinyal")) else "lain")
        akt.append(dict(t=int(t), pesan=s[:140], jenis=jenis, oleh=a))
        if len(akt) >= 40: break
    return akt


M = baca_json(os.path.join(REPO, "riset", "milestone.json"), {})
mulai = dt.date.fromisoformat(M.get("mulai", "2026-11-24")); tenggat = dt.date.fromisoformat(M.get("tenggat", "2026-12-31"))
hari_total = (tenggat - mulai).days + 1; hari_lewat = min(max((now.date() - mulai).days + 1, 0), hari_total)
data = dict(dibangun=now.isoformat(timespec="seconds"), milestone=M,
            waktu=dict(mulai=mulai.isoformat(), tenggat=tenggat.isoformat(), hari_total=hari_total, hari_lewat=hari_lewat,
                       sisa=max((tenggat - now.date()).days, 0), persen=round(100 * hari_lewat / hari_total, 1)),
            bot={}, aktivitas=aktivitas())
tot_var = tot_pen = 0; persen = []
for b in BOTS:
    st = baca_json(os.path.join(REPO, "riset", b, "status.json"), {})
    fol = os.path.join(REPO, "riset", b, "massal")
    ring = baca_json(os.path.join(fol, "ringkas.json")); riw = baca_json(os.path.join(fol, "riwayat.json"), [])
    pen = baca_json(os.path.join(fol, "penantang.json"), {})
    nv = sum(r.get("n_varian", 0) for r in riw) or (ring or {}).get("n_varian", 0)
    tot_var += nv; tot_pen += len(pen)
    # versi terbaik = penantang teratas (bila ada) selain juara; lolos T1,T3-T8 dari data penuh, T2/T9 dari status sesi
    terbaik = ((ring or {}).get("penantang") or [None])[0] or (ring or {}).get("juara")
    def lolos(v):
        s = (v or {}).get("semua") or {}
        l = dict(s.get("lolos") or {})
        l["T2"] = bool(st.get("t2")); l["T9"] = bool(st.get("t9"))
        return {k: bool(l.get(k)) for k in [f"T{i}" for i in range(1, 10)]}
    lj, lt = lolos((ring or {}).get("juara")), lolos(terbaik)
    p = round(100 * sum(lt.values()) / 9, 1); persen.append(p)
    data["bot"][b] = dict(status=st, rapor=rapor(b), massal=ring, riwayat=riw, n_varian_total=nv, n_penantang=len(pen),
                          penantang_nama=list(pen)[-10:], harian=harian(b), laporan=laporan(b), lolos_juara=lj, lolos_terbaik=lt,
                          terbaik_nama=(terbaik or {}).get("nama"), persen=p)
awal = M.get("awal_lolos", {}); a0 = sum(awal.get(b, 0) for b in BOTS); n_now = sum(sum(data["bot"][b]["lolos_terbaik"].values()) for b in BOTS)
data["ringkas"] = dict(lolos=n_now, lolos_awal=a0, lolos_maks=9 * len(BOTS),
                       kemajuan=round(100 * max(n_now - a0, 0) / max(9 * len(BOTS) - a0, 1), 1),varian_total=tot_var, penantang_total=tot_pen, persen=round(sum(persen) / len(persen), 1) if persen else 0,
                       blocker_menunggu=sum(1 for b in BOTS for x in data["bot"][b]["status"].get("blocker", []) if x.get("status") == "menunggu")
                       + sum(1 for x in M.get("blocker", []) if x.get("status") == "menunggu"))
os.makedirs(OUT, exist_ok=True)
json.dump(data, open(os.path.join(OUT, "data.json"), "w"), ensure_ascii=False, default=str)
for f in glob.glob(os.path.join(REPO, "docs", "*")):
    if os.path.isfile(f) and not f.endswith("data.json"): shutil.copy(f, OUT)
print(f"data.json: {len(json.dumps(data, default=str)) // 1024} KB · progres {data['ringkas']['persen']}% · varian {tot_var}")
