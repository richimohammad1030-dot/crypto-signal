# Riset bot

Riset crypto (swing), XAU, dan intraday dipisah karena strateginya berbeda total. Masing-masing punya routine, prosedur,
daftar ide, jurnal riset, laporan, dan branch sendiri.

| | Crypto | XAU | Intraday |
|---|---|---|---|
| Routine | "Riset Bot Crypto", Jumat 00:59 WIB | "Riset Bot XAU", Jumat 00:18 WIB | "Riset Bot Intraday", Jumat 01:37 WIB |
| Prosedur | `riset/crypto/PROSEDUR.md` | `riset/xau/PROSEDUR.md` | `riset/intraday/PROSEDUR.md` |
| Daftar ide | `riset/crypto/ide.md` | `riset/xau/ide.md` | `riset/intraday/ide.md` |
| Jurnal riset | `riset/crypto/log.md` | `riset/xau/log.md` | `riset/intraday/log.md` |
| Laporan | `riset/laporan/crypto/` | `riset/laporan/xau/` | `riset/laporan/intraday/` |
| Branch | `claude/riset-crypto-YYYY-MM-DD` | `claude/riset-xau-YYYY-MM-DD` | `claude/riset-intraday-YYYY-MM-DD` |

Bersama: skrip unduh & backtest (`riset/*.py`) dan laporan angka bulanan otomatis dari GitHub Actions
(`riset/laporan/angka-YYYY-MM.*`, tanggal 1).

Intraday belum live: strategi terkunci di `riset/intraday/STRATEGI.md`, mesin backtest `riset/backtest_intraday.py`
(data 15 menit dari `riset/unduh_intraday.py`).
