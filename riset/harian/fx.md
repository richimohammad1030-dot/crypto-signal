# Rutinitas harian FX · Sat 28 Nov 2026 07:15 WIB
Dibuat otomatis oleh riset/harian.py (GitHub Actions). Sesi riset: baca ini, JANGAN ulangi langkahnya kecuali ada GAGAL.

### Replay · penyebab SL · kesehatan · bayangan OK (1.2 mnt)
```
Live sejak 20 Nov 2026 · 6 hari bursa selesai · trade live tercatat 4

## 1. Replay kesetaraan (wajib IDENTIK)
live 4 trade · replay 3 trade -> BEDA
  BEDA ('AUDUSD', 'B3', -1, 1795590000) live 0.692 replay None
  BEDA ('AUDUSD', 'B3', -1, 1795597200) live None replay 0.6894137459632795
  BEDA ('AUDUSD', 'N3', -1, 1795575600) live 1.922 replay None
  BEDA ('AUDUSD', 'N3', -1, 1795582800) live None replay 1.919218327951121
  BEDA ('EURUSD', 'SUS', -1, 1795784400) live 0.695 replay None
  BEDA ('NZDUSD', 'N3', -1, 1795737600) live -3.321 replay None
  BEDA ('NZDUSD', 'N3', -1, 1795748400) live None replay -3.3211926116219352

## 2. Penyebab SL 7 hari terakhir
- Fri 27 Nov 10:00 WIB NZDUSD SELL [UTAMA] MFE +0.79R · 3 jam ke SL · Sempat untung >= 0,5R lalu berbalik

Ringkas: {'Sempat untung >= 0,5R lalu berbalik': 1}
Celah berulang (>= 3 kali kategori sama dalam 7 hari) = kandidat ide riset mingguan.

### Kesehatan live vs ekspektasi backtest
- UTAMA: 2 trade · -0.700R/trade (backtest +0.07) · WR 50% (backtest 22%) · total -1.40R
- SUSULAN: 1 trade · +0.695R/trade (backtest +0.12) · WR 100% (backtest 48%) · total +0.69R
- LANJUT: 1 trade · +0.692R/trade (backtest +0.14) · WR 100% (backtest 66%) · total +0.69R
- Total: 4 trade · -0.01R · DD 3.3R (backtest DD maks 36R = batas peringatan)

## 3. Live vs bayangan (sejak live, hari yang sama)
- LIVE (juara): 3 trade · -0.71R · WR 67%
- Tanpa pecah (UTAMA s/d 23:00, tanpa susulan): 2 trade · -1.40R · WR 50%
- Dengan Senin: 3 trade · -0.71R · WR 67%
- LIVE + BALAS (balik, SL/TP 0,15/0,3 ATR): 4 trade · -2.00R · WR 50%
```
