# Płytka drukowana: wstępny projekt (iteracja 1)

Wersja robocza do pracy nad obudową. **Brak plików produkcyjnych (Gerber, KiCad)**: celowo, to pierwsza iteracja.

| Plik | Zawartość |
| --- | --- |
| [specyfikacja-obudowy-dla-agenta.md](specyfikacja-obudowy-dla-agenta.md) | wymagania mechaniczne dla agenta projektującego obudowę (wymiary, strefy zakazane, tolerancje, miejsca na wizję) |
| [pcb-przod.svg](pcb-przod.svg), [pcb-tyl.svg](pcb-tyl.svg) | płytka z przodu i od tyłu, z wstępnym trasowaniem ścieżek |
| [pcb-przekroj.svg](pcb-przekroj.svg) | rzut z boku: wysokości elementów |
| [podglad-3d.html](podglad-3d.html) | interaktywny podgląd 3D (otwórz w przeglądarce) |
| [pcb-layout.json](pcb-layout.json), [pcb_params.scad](pcb_params.scad) | współrzędne i wymiary dla modelowania obudowy |

Generowane przez `python3 tools/pcb/build.py` z jednego źródła (`tools/pcb/board.py`, `layout.py`). Rozmieszczenie elementów z tyłu wyznacza `tools/pcb/optimize.py` (wyżarzanie symulowane z regułami geometrii); trasowanie `router.py` sprawdza wykonalność.
