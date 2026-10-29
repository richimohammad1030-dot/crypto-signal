"""Ide #5: lewati hari saat lebar range 04:00-07:00 WIB terlalu sempit/lebar dibanding ATR(14).
Ambang diambil dari kuantil paruh pertama (2025) saja, lalu dinilai di kedua paruh (P2 = out-of-sample).
Argumen: <xau.json>"""
import sys, numpy as np, umum as u

T, O, H, L, C = u.muat(sys.argv[1])
juara_tr = u.replay(T, O, H, L, C)
J = u.ringkas("juara", juara_tr)

# rasio lebar range / ATR per hari (dicatat lewat hook tanpa mengubah apa pun)
rasio = {}
def catat(i, ctx, hi, lo, a):
    rasio[T[i]] = (hi - lo) / a
    return {"buy": True, "sell": True}
u.replay(T, O, H, L, C, plan=catat)
p1 = np.array([v for k, v in rasio.items() if u.wib(k).year == 2025])
q = {p: float(np.quantile(p1, p / 100)) for p in (20, 80)}

# distribusi hasil juara per kuintil rasio (ambang kuintil P1)
qq = [float(np.quantile(p1, x)) for x in (0.2, 0.4, 0.6, 0.8)]
def bucket(ts):
    # hari pemasangan = candle 07:00 terakhir sebelum t0
    k = max(k for k in rasio if k <= ts); return int(np.searchsorted(qq, rasio[k]))
print("## Kuintil rasio range/ATR (ambang P1:", ", ".join(f"{x:.2f}" for x in qq), ")")
print("| Kuintil | Paruh | Trade | Total R bersih | R/trade |\n|---|---|---|---|---|")
for b in range(5):
    for key in ("P1 2025", "P2 2026"):
        s = u.stat([t for t in juara_tr if bucket(t["t0"]) == b and u.paruh(t) == key])
        print(f"| K{b+1} | {key} | {s['n']} | {s['tot']:+.1f} | {s['avg']:+.3f} |")

varian = {
    f"lewati sempit (<{q[20]:.2f} ATR)": lambda r: r < q[20],
    f"lewati lebar (>{q[80]:.2f} ATR)": lambda r: r > q[80],
    "lewati sempit dan lebar": lambda r: r < q[20] or r > q[80],
}
print("\n## Perbandingan (bersih biaya)\n" + u.HDR)
print(u.baris("Juara", J["semua"]))
hasil = {}
for nama, skip in varian.items():
    tr = u.replay(T, O, H, L, C, plan=lambda i, ctx, hi, lo, a, s=skip: None if s((hi - lo) / a) else {"buy": True, "sell": True})
    hasil[nama] = V = u.ringkas(nama, tr)
    print(u.baris(nama, V["semua"]))
for key in ("P1 2025", "P2 2026"):
    print(f"\n### {key}\n" + u.HDR); print(u.baris("Juara", J[key]))
    for nama, V in hasil.items(): print(u.baris(nama, V[key]))
qs = sorted(J["kuartal"])[-7:]
print("\n### Total R per kuartal\n| Varian | " + " | ".join(qs) + " |\n|---|" + "---|" * len(qs))
print("| Juara | " + " | ".join(f"{J['kuartal'][x]['tot']:+.1f}" for x in qs) + " |")
for nama, V in hasil.items():
    print(f"| {nama} | " + " | ".join(f"{V['kuartal'].get(x, u.stat([]))['tot']:+.1f}" for x in qs) + " |")
print("\n### Keputusan per varian")
for nama, V in hasil.items():
    k, al, nb = u.nilai(J, V); print(f"- {nama}: **{k}** ({'; '.join(al) or 'semua kriteria terpenuhi'})")
