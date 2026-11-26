"""USULAN keluarga baru untuk bank saringan massal riset/massal/intraday.py (ATURAN_BERSAMA F.2c), sesi 25 Nov 2026.
Sesi riset intraday hanya boleh menulis di riset/intraday/ -> keluarga ini DITITIPKAN di sini; salin ke riset/massal/intraday.py
(dan tambahkan ke KELUARGA) dari chat project bila disetujui.
Celah yang diserang: T2 (monitor edge). Uji sesi 25 Nov (eksperimen/sesi_2026-11-25.py) menunjukkan monitor 365 hari tingkat bot
tidak pernah aktif pada juara (PF 365 hari selalu > 1) -> T2 terpenuhi sebagai PENGAMAN, bukan penambah edge. Keluarga ini
memetakan seberapa sensitif monitor per modul/koin terhadap jendela & bobot (tetangga parameter) agar desain T2 dipilih dari
dataran yang stabil, bukan satu angka."""
import itertools
import inti


def IM006_monitor_modul(M):
    """Monitor PF per strategi (A / B) dengan bobot turun bertingkat; w > 0 tidak mengubah slot (pasca-trade = tepat)."""
    base = M.trades()
    for hari, amb, w in itertools.product((120, 180, 270, 365, 540), (0.95, 1.0, 1.05), (0.25, 0.5, 0.75)):
        yield f"IM006 monitorPF modul {hari}h <{amb} w{w}", inti.monitor_pf(base, hari, amb, w, 20, "strat")
