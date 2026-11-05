"""Ide #36 (6 Nov 2026, permintaan pemilik): saran lot otomatis dari XAU_MODAL_USD. TIDAK mengubah strategi.
Rumus (1 lot XAU = 100 oz, 0,01 lot = 1 oz -> rugi di SL per 0,01 lot = jarak SL dalam USD):
  lot_ideal = modal x risiko% / (jarak_SL + biaya) / 100 ; lot_saran = dibulatkan KE BAWAH ke 0,01
  lot_saran < 0,01 -> PERINGATAN: lot minimum 0,01 berisiko (jarak_SL + biaya) / modal (pemilik: lewati / terima).
Skrip ini mengukur, pada trade bot live (BASELINE hibrida) di data Setra Feb 2025 - skrg dan 2026 saja:
  1) sebaran jarak SL per strategi (USD per 0,01 lot) -> modal minimum agar 0,01 lot <= 0,5%;
  2) untuk beberapa modal contoh: porsi sinyal yang memicu peringatan, risiko nyata (median / p90 / maks) bila 0,01 diterima,
     dan pertumbuhan modal (simulasi lot dibulatkan ke bawah, majemuk, lewati vs terima saat lot < 0,01) vs ideal 0,5%.
Pemakaian: python ide36_lot.py <xau_setra.json> <xau_panjang.json>"""
import sys, math
import numpy as np
import audit_mesin as m, multi_mesin as mm

BIAYA = 0.40          # USD/oz (spread + komisi), sama dengan riset
OZ_PER_LOT = 100.0
RISK = 0.005


def saran_lot(modal, jarak_sl, risk=RISK, biaya=BIAYA, oz=OZ_PER_LOT, lot_min=0.01, langkah=0.01):
    """Usulan fungsi untuk bot (gold_templates/gold_bot). Return dict(lot, risiko_usd, risiko_pct, peringatan, lot_ideal)."""
    rugi_per_lot = (jarak_sl + biaya) * oz
    ideal = modal * risk / rugi_per_lot
    lot = math.floor(ideal / langkah + 1e-9) * langkah
    warn = lot < lot_min
    if warn: lot = lot_min
    usd = lot * rugi_per_lot
    return dict(lot=round(lot, 2), lot_ideal=ideal, risiko_usd=usd, risiko_pct=usd / modal * 100, peringatan=warn)


def main():
    D = m.sambung(m.muat(sys.argv[2]), m.muat(sys.argv[1]))
    A = np.array(m.atr(list(D[2]), list(D[3]), list(D[4]), 14)); F = m.fitur(D, A)
    TR = mm.baseline(D, A, F)
    for lbl, a in (("Setra Feb 2025 - skrg", "2025-02-01"), ("2026 saja", "2026-01-01")):
        tr = m.potong(TR, a)
        print(f"\n=== {lbl}: {len(tr)} trade")
        print("Jarak SL (USD per 0,01 lot) per strategi: median / p75 / p90 / maks -> modal min 0,01 lot @0,5% (median / p90)")
        for st in ("MR", "K6", "SUS", "SEMUA"):
            d = np.array([x["r0"] for x in tr if st == "SEMUA" or x["strat"] == st]) + BIAYA
            if not len(d): continue
            q = np.percentile(d, [50, 75, 90]); print(f"  {st:<6} n {len(d):>3}: {q[0]:6.1f} / {q[1]:6.1f} / {q[2]:6.1f} / {d.max():6.1f}"
                                                       f"  -> modal {q[0] / RISK:8,.0f} / {q[2] / RISK:8,.0f} USD")
        print("Modal contoh: % sinyal peringatan | risiko nyata 0,01 lot (median/p90/maks) | lot saran median | "
              "simulasi majemuk: ideal 0,5% · bulat-bawah+terima · bulat-bawah+lewati (lewati = n trade)")
        r_net = m.net(tr)
        for modal in (1000, 2000, 5000, 10000, 20000, 50000):
            S = [saran_lot(modal, x["r0"]) for x in tr]
            pw = np.mean([s["peringatan"] for s in S]) * 100
            rp = np.array([s["risiko_pct"] for s in S if s["peringatan"]])
            lots = np.median([s["lot"] for s in S])
            # simulasi majemuk: lot dihitung ulang dari modal berjalan tiap trade
            eq_i = eq_t = eq_s = float(modal); dd = {"t": 0, "s": 0}; pk = {"t": modal, "s": modal}; skip = 0
            for x, rn in zip(tr, r_net):
                rug = (x["r0"] + BIAYA) * OZ_PER_LOT       # USD per 1 lot di SL (termasuk biaya)
                hasil_per_lot = rn * x["r0"] * OZ_PER_LOT  # USD per 1 lot, bersih biaya
                eq_i += eq_i * RISK * rn
                s = saran_lot(eq_t, x["r0"]); eq_t += s["lot"] * hasil_per_lot
                s2 = saran_lot(eq_s, x["r0"])
                if s2["peringatan"]: skip += 1
                else: eq_s += s2["lot"] * hasil_per_lot
                for k, e in (("t", eq_t), ("s", eq_s)):
                    pk[k] = max(pk[k], e); dd[k] = max(dd[k], 1 - e / pk[k])
            rtxt = f"{np.median(rp):4.1f}/{np.percentile(rp, 90):4.1f}/{rp.max():4.1f}%" if len(rp) else "      -       "
            print(f"  {modal:>6,} USD: {pw:5.1f}% | {rtxt} | lot {lots:.2f} | {eq_i / modal * 100 - 100:+6.1f}% · "
                  f"{eq_t / modal * 100 - 100:+6.1f}% (DD {dd['t'] * 100:4.1f}%) · {eq_s / modal * 100 - 100:+6.1f}% (DD {dd['s'] * 100:4.1f}%, lewati {skip})")
    print("\nContoh pesan (modal 1.500 dan 15.000 USD, SL 56 USD):")
    for modal in (1500, 15000):
        print(" ", modal, saran_lot(modal, 56.0))


if __name__ == "__main__":
    main()
