# Kurikulum skill · CRYPTO SWING (status)

Aturan umum & antrian skill: `riset/KURIKULUM_SKILL.md` (berlaku juga untuk crypto). Satu skill aktif, satu langkah per Jumat.
Skrip: `riset/crypto/eksperimen/skill_<nama>*.py`. Periode uji "paham" crypto = **2017-2019 DAN 2020-skrg** (padanan XAU
2004-2014 & 2015-2026); "bisa memakai" = memperbaiki sistem dasar di walk-forward (`eksperimen/_wf.py`) dengan P ≥ 0,90.

| Skill | Tahap | Tanggal | Catatan |
|---|---|---|---|
| 1 · SNR | **0 · definisi mesin selesai** | 11 Nov 2026 | `skill_snr.py`: 4 jenis (swing fraktal H4/D1 n=2/3/5 digabung ≤ 0,25 ATR D1 & lebar ≤ 0,5 ATR D1; high/low hari & minggu sebelumnya [hari 00:00 UTC = 07:00 WIB]; angka bulat relatif orde harga 10^k × 1/0,5/0,25; supply-demand H4 dasar ≤ 0,5 ATR + impuls ≥ 2 ATR ≤ 3 candle, segar/tersentuh). Tanpa melihat masa depan. Cek kewajaran BTC & SOL: 9 jenis zona terbentuk. |
| 1 · SNR | **1 · PAHAM: LULUS (PERIODE & SWING-D1)** | 13 Nov 2026 | `skill_snr_tahap1.py`, 11 koin (BTC ETH BNB XRP TRX ADA XLM BCH LTC ETC + 1) data spot sejak 2017-18. Efek KEBALIKAN teori klasik (sama dengan intraday): level lebih sering DITEMBUS daripada level acak. PERIODE (high/low hari & minggu sebelumnya) pantul 31-34% vs acak 36-37%, P(tembus lebih sering) >= 0,97 di 4 sel (2017-19 & 2020-26, support & resistance); SWING-D1 lift -1,2 s.d. -3,3 poin, P >= 0,90 di 4 sel (2017-19 resistance tipis 0,904). SWING-H4 kecil (±0,5 poin), 2017-19 resistance tidak nyata. BULAT tidak nyata. SD: pantul nyata hanya 2020-26 support (+5,6 poin, P 1,00), tidak di 2017-19 → belum. |
| 1 · SNR | 1b → 2 · BISA MEMAKAI (berikutnya) | Jumat 20 Nov 2026 | 1b: apakah tembusan PERIODE/SWING-D1 diikuti lanjutan (R maju 1-5 hari)? Lalu tahap 2 di walk-forward `_wf.py`: (i) mutu sinyal breakout yang entry-nya dekat/menembus PDH-PWH (BUY) / PDL-PWL (SELL) vs jauh, (ii) SL di balik level, (iii) prioritas slot. P >= 0,90. |

Penyesuaian crypto terhadap kurikulum XAU: pasar 24/7 (tidak ada jendela 07:00-23:00; keputusan di candle cek tiap 4 jam),
angka bulat relatif terhadap orde harga, banyak koin (hasil dilaporkan per koin besar & gabungan), dan Tahap 2 dinilai sebagai
filter/penempatan SL/keluar pada sistem breakout swing (bukan intraday).
