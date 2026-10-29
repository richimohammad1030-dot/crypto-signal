"""Ide #13: hanya pasang sisi OCO yang searah tren (close 07:00 WIB vs EMA200 H1), atau dua sisi
dengan sisi melawan tren risiko 1/2. Replay penuh (sisi yang tidak dipasang bisa mengubah order terisi).
Cek sensitivitas dengan EMA50 dan EMA100. Argumen: <xau.json>"""
import sys, umum as u

T, O, H, L, C = u.muat(sys.argv[1])
J = u.ringkas("juara", u.replay(T, O, H, L, C))
hasil = {}
for n in (200, 100, 50):
    E = u.ema(C, n)
    def satu_sisi(i, ctx, hi, lo, a, E=E):
        up = C[i] > E[i]; return {"buy": up, "sell": not up}
    def setengah(i, ctx, hi, lo, a, E=E):
        up = C[i] > E[i]; return {"buy": True, "sell": True, "w_buy": 1 if up else 0.5, "w_sell": 0.5 if up else 1}
    hasil[f"EMA{n} satu sisi"] = u.ringkas("", u.replay(T, O, H, L, C, plan=satu_sisi))
    hasil[f"EMA{n} lawan tren 1/2"] = u.ringkas("", u.replay(T, O, H, L, C, plan=setengah))
print("## Perbandingan (bersih biaya; R sudah dikali bobot risiko)\n" + u.HDR)
print(u.baris("Juara", J["semua"]))
for nama, V in hasil.items(): print(u.baris(nama, V["semua"]))
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
