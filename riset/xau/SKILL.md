# Status kurikulum skill · XAU (riset/KURIKULUM_SKILL.md)
Diperbarui riset Jumat setiap langkah skill (file ini ikut tersalin ke main oleh workflow laporan; KURIKULUM_SKILL.md di
riset/ tidak tersalin, jadi status XAU dicatat di sini).

| Skill | Tahap | Tanggal | Hasil singkat |
|---|---|---|---|
| 1 · SNR | 0 · definisi mesin | 13 Nov 2026 | **LULUS**. `eksperimen/skill_snr.py`: swing fraktal 2/3/5 H4 & D1 (zona digabung ≤ 0,25 ATR D1, lebar maks 0,5 ATR D1, tiap penggabungan = versi baru), PDH/PDL & PWH/PWL (blok 07-07 WIB), angka bulat 10/25/50/100, supply-demand H4 & D1 (dasar 1-3 candle ≤ 0,5 ATR + impuls close ≥ 2 ATR, status segar). Cek tanpa-masa-depan 0/2.218. Sentuhan ±77/hari bursa |
| 1 · SNR | 1 · PAHAM (putaran 1/3) | 20 Nov 2026 | **BELUM LULUS**. `eksperimen/skill_snr_t1.py`: 548.400 sentuhan 2004-2026 vs level acak (waktu acak tahun sama, jarak & lebar zona sama, cocok 96,7%). Peluang pantul (≥ 1 ATR sebelum tembus 0,5 ATR, 12 jam) nyata ≈ acak: semua 55,0/53,6/50,1/50,2% vs 54,9/53,2/50,5/50,0%. 0 dari 18 jenis-tf lulus 4 sel. Terdekat: SUPPLY H4 (lift +4,6/+1,9/+4,9/+3,3 poin, P 1,00/0,81/0,99/0,95) dan SUPDEM (P 0,57/0,95/0,93/0,89). PDH/PDL & angka bulat ≤ acak; BULAT100 support lebih sering TEMBUS (-3,5 poin). Tembus zona kuat TIDAK diikuti lanjutan lebih sering dari acak |
| 1 · SNR | 1 · PAHAM (putaran 2/3) | berikutnya: Jumat 27 Nov 2026 | definisi baru: fokus supply-demand (H4/D1, segar, impuls 1,5-3 ATR), sentuhan pertama saja, konfluensi ≥ 2 jenis, horizon 3-6 jam & pantul 0,5 ATR; tetap vs level acak + P ≥ 0,90 di 4 sel |
