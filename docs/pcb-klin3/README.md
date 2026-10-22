# Płytka drukowana: wariant „klin 3” (bez wyświetlacza i przycisków, 40 × 24 mm)

Wariant **równoległy** do [podstawowego](../pcb/README.md) i do [„klina”](../pcb-klin/README.md) (48 × 36 mm). Tamte zostają bez zmian i rozwijają się osobno. Ten jest dla obudowy [klin 3](../obudowa-klin-3/README.md): moduł wyświetlacza i przyciski są poza płytką, więc zostaje tylko elektronika. Wersja robocza, **brak plików produkcyjnych**.

```bash
python3 tools/pcb/build.py --variant klin3      # -> docs/pcb-klin3/ (pcb-layout.json, pcb-przod.svg, pcb-tyl.svg, specyfikacja-plytki.md)
PCB_VARIANT=klin3 python3 tools/pcb/optimize.py 40 24 16000 3    # ponowne rozmieszczenie (szer., wys., iteracje, ziarno)
```

Zmienne `PCB_W`, `PCB_H` zmieniają rozmiar płytki, `PCB_TALL` (−1…1) przesuwa wysokie elementy ku niskim lub wysokim y. Podstawowa płytka i wariant „klin” są po zmianach generatora **bajt w bajt takie same** jak przed nimi (sprawdzone porównaniem plików w `docs/pcb/` i `docs/pcb-klin/`).

## Co się różni

| | „klin” | „klin 3” |
| --- | --- | --- |
| Zarys | 48 × 36 mm (1728 mm²) | **40 × 24 mm (960 mm², −44%)** |
| Otwory montażowe | 4 × M2,5 w narożnikach | **2 × M2,5 na przekątnej** (3,5; 3,5) i (36,5; 20,5) |
| Przód (TOP) | moduł OLED | nic: tylko pola i lut |
| Moduł OLED | wlutowany w płytkę | osobno, 4 przewody do pól **DISP** |
| Przyciski | osobna płytka, 4 przewody do pól KEY | to samo (płytka przycisków 50 × 16 mm) |
| Elementy | U1, R1…R6, C1…C3, D1, Q1, SPK, BAT, KEY | te same + **DISP** |

Pola **DISP 1…4**: SDA, SCL, VCC, GND (kolejność listwy modułu), pad Ø2,3 mm, otwór Ø1,2 mm, rozstaw 3,5 mm, jak KEY. Pola KEY: GND, PB3, PB4, dolna strona S3 (jak w „klinie”). R6 zostaje na płytce głównej.

## Montaż w obudowie

Płytka leży elementami do wnętrza na tylnej ściance pokrywy, laminat 2,5 mm od ścianki (na lut i końcówki nóżek do 2,0 mm). Widok od strony TOP (od ścianki): **+y wskazuje wierzchołek obudowy**, +x w stronę lewego (głośnikowego) boku. Wysokości elementów: jak w płytce podstawowej (U1 w podstawce 8,5 mm, D1 8,7 mm, C3 8,0 mm).

## Rozmieszczenie i kontrola

- Rozmieszczenie z `tools/pcb/optimize.py` (wyżarzanie symulowane, 16 000 iteracji, **ziarno 3**), zapisane w [`tools/pcb/layout_klin3.py`](../../tools/pcb/layout_klin3.py). Do funkcji celu doszły: pola DISP i KEY przy górnej krawędzi (ku wierzchołkowi), głośnik po stronie +x, bateria nisko, C2 przy U1.
- **Rozmiar:** z 8 ziaren dla 40 × 24 mm dwa dają 0 naruszeń (1 i 3), dla 38 × 24 jedno (4), dla 36 × 26 i 48 × 20 żadne. Wąskie gardło to ta sama reguła co wcześniej: nóżki wszystkich elementów muszą leżeć w wolnych strefach, a pola przewodów (12 padów) i dwa otwory zajmują sporo miejsca.
- Przekrój obudowy nie zależy tu od konkretnego ziarna: 16 rozmieszczeń o rozmiarach 38 × 24 … 46 × 22 daje ten sam bok trójkąta (72 mm), bo wymiarowa jest obwiednia, nie układ.
- Kontrola w `build.py`: **0 naruszeń rozmieszczenia, 0 sieci niepołączonych** w sprawdzeniu trasowania (242 odcinki, 1 przelotka, 43 piny). To sprawdzenie wykonalności prostym routerem siatkowym, nie finalna miedź.

## Do sprawdzenia przed zamówieniem

1. Płytka **przycisków** ma tu 50 × 16 mm (przyciski w x = 7,22, 25,00, 42,78, czyli co 17,78 mm = 7 oczek rastra 2,54; otwory M2 w (16,11; 2,92) i (33,89; 13,08)), czyli inaczej niż 52 × 16 mm w „klinie”. Projektu PCB nie ma: rozstaw dobrany tak, żeby wystarczyła płytka uniwersalna, opis montażu w [README klina 4](../obudowa-klin-4/README.md#5-płytka-przycisków-na-płytce-uniwersalnej), szablon 1:1, schemat i instrukcja w [`docs/plytka-przyciskow/`](../plytka-przyciskow/README.md). Do klina 4 przyciski były co 18 mm (pliki klina 3 i 3.1 są z tym rozstawem).
2. **Orientacja ATtiny** i dostęp do podstawki: wymiana układu wyciągaczem od wnętrza obudowy po zdjęciu pokrywy.
3. Wysokości elementów (8,5 mm dla U1 w podstawce), wymiary modułu OLED i listwy pinów: szacunki do zmierzenia, jak w pozostałych płytkach.
4. Trasowanie jest jedynie próbą wykonalności. Przewody do pól DISP, KEY, SPK i BAT trzeba poprowadzić z odciążeniem.
