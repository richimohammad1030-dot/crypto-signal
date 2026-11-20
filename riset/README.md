# Riset bot

Riset crypto (swing), XAU, intraday, dan FX MAJOR dipisah karena strateginya berbeda total. Masing-masing punya routine, prosedur,
daftar ide, jurnal riset, laporan, dan branch sendiri.

| | Crypto | XAU | Intraday | FX MAJOR |
|---|---|---|---|---|
| Routine | "Riset Bot Crypto", Jumat 00:59 WIB | "Riset Bot XAU", Jumat 00:18 WIB | "Riset Bot Intraday", Jumat 01:37 WIB | "Riset Bot FX", Minggu 03:17 WIB |
| Prosedur | `riset/crypto/PROSEDUR.md` | `riset/xau/PROSEDUR.md` | `riset/intraday/PROSEDUR.md` | `riset/fx/PROSEDUR.md` |
| Daftar ide | `riset/crypto/ide.md` | `riset/xau/ide.md` | `riset/intraday/ide.md` | `riset/fx/ide.md` |
| Jurnal riset | `riset/crypto/log.md` | `riset/xau/log.md` | `riset/intraday/log.md` | `riset/fx/log.md` |
| Laporan | `riset/laporan/crypto/` | `riset/laporan/xau/` | `riset/laporan/intraday/` | `riset/laporan/fx/` |
| Branch | `claude/riset-crypto-YYYY-MM-DD` | `claude/riset-xau-YYYY-MM-DD` | `claude/riset-intraday-YYYY-MM-DD` | `claude/riset-fx-YYYY-MM-DD` |

Bersama: skrip unduh & backtest (`riset/*.py`) dan laporan angka bulanan otomatis dari GitHub Actions
(`riset/laporan/angka-YYYY-MM.*`, tanggal 1).

Intraday belum live: strategi terkunci di `riset/intraday/STRATEGI.md`, mesin backtest `riset/backtest_intraday.py`
(data 15 menit dari `riset/unduh_intraday.py`).

FX MAJOR (live uji maju sejak 20 Nov 2026): strategi `riset/fx/STRATEGI.md`, mesin `forex_major/fx_live.py`, bot `fx_bot.py`,
rutinitas harian `riset/fx/harian_fx.py` (bagian dari `riset/harian.py`).
