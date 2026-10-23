# Riset bot

Riset crypto dan XAU dipisah karena strateginya berbeda total. Masing-masing punya routine, prosedur,
daftar ide, jurnal riset, laporan, dan branch sendiri.

| | Crypto | XAU |
|---|---|---|
| Routine | "Riset Bot Crypto", Jumat 00:59 WIB | "Riset Bot XAU", Jumat 00:18 WIB |
| Prosedur | `riset/crypto/PROSEDUR.md` | `riset/xau/PROSEDUR.md` |
| Daftar ide | `riset/crypto/ide.md` | `riset/xau/ide.md` |
| Jurnal riset | `riset/crypto/log.md` | `riset/xau/log.md` |
| Laporan | `riset/laporan/crypto/` | `riset/laporan/xau/` |
| Branch | `claude/riset-crypto-YYYY-MM-DD` | `claude/riset-xau-YYYY-MM-DD` |

Bersama: skrip unduh & backtest (`riset/*.py`) dan laporan angka bulanan otomatis dari GitHub Actions
(`riset/laporan/angka-YYYY-MM.*`, tanggal 1).
