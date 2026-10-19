# Płytka drukowana: wariant „klin” (bez przycisków, 48 × 36 mm)

Wariant **równoległy** do podstawowej płytki z [`docs/pcb/`](../pcb/README.md). Podstawowa płytka (48 × 50 mm, przyciski na płytce głównej, płaska obudowa z [`docs/obudowa/`](../obudowa/README.md)) zostaje bez zmian i rozwija się osobno. Ten wariant jest dla obudowy-klina ([`docs/obudowa-klin/`](../obudowa-klin/README.md)), w której przyciski są na **osobnej małej płytce** pod grzbietem. Tak samo jak wersja podstawowa: wersja robocza, **brak plików produkcyjnych**.

Generowanie (z jednego źródła `tools/pcb/`, wariant wybiera flaga):

```bash
python3 tools/pcb/build.py --variant klin      # -> docs/pcb-klin/
python3 tools/pcb/build.py                     # -> docs/pcb/ (podstawowy, bez zmian)
PCB_VARIANT=klin python3 tools/pcb/optimize.py 48 36 15000 4   # ponowne rozmieszczenie (szer., wys., iteracje, ziarno)
```

Pliki są te same co w wersji podstawowej: [`pcb-przod.svg`](pcb-przod.svg), [`pcb-tyl.svg`](pcb-tyl.svg), [`pcb-przekroj.svg`](pcb-przekroj.svg), [`podglad-3d.html`](podglad-3d.html), [`pcb-layout.json`](pcb-layout.json), [`pcb_params.scad`](pcb_params.scad), [`specyfikacja-obudowy-dla-agenta.md`](specyfikacja-obudowy-dla-agenta.md) (wersja dla tego wariantu). `pcb-layout.json` ma dodatkowo klucze `variant` i `button_board` (wymiary, przyciski i przewody płytki przycisków).

## Co się różni od płytki podstawowej

| | Podstawowa (`docs/pcb/`) | „klin” (`docs/pcb-klin/`) |
| --- | --- | --- |
| Zarys | 48 × 50 mm | **48 × 36 mm** (R3, 4 otwory M2,5 w narożnikach, jak wcześniej) |
| Przód | moduł OLED + 3 przyciski B3F-4055 | tylko moduł OLED, **wyśrodkowany** w pionie (y = 12…24, szkło y = 13…23) |
| Przyciski S1–S3 | na płytce | na osobnej płytce, połączone 4 przewodami |
| Tył | 14 elementów | te same elementy (U1, R1…R6, C1…C3, D1, Q1, SPK, BAT) + pola **KEY** na przewody; nowe rozmieszczenie |
| Sieci | S1–S3 w sieciach GND, PB3, PB4, S3LOW | S1–S3 poza płytką, sieci łączą się z polami KEY (patrz niżej) |

R6 (8,2 kΩ dla „−”) **zostaje na płytce głównej**, żeby płytka przycisków była płaska i miała same przyciski.

## Pola KEY (przewody do płytki przycisków)

4 pola lutownicze (otwór Ø1,2 mm, pad Ø2,3 mm, rozstaw 3,5 mm) w jednym rzędzie, współrzędne w układzie widoku z przodu:

| Pole | Sieć | Do czego na płytce przycisków | (x, y) |
| --- | --- | --- | --- |
| KEY1 | GND | wspólny biegun S1 i S2 | (35,95; 32,85) |
| KEY2 | PB3 | S1 „run” | (32,45; 32,85) |
| KEY3 | PB4 | S2 „+” i S3 „−” (drabinka z R5) | (28,95; 32,85) |
| KEY4 | S3LOW | dolna strona S3 „−”, na płytce głównej do R6 → GND | (25,45; 32,85) |

Płytka przycisków: 52 × 16 mm, 3 × B3F-4055 w x = 8, 26, 44 mm (rozstaw 18 mm), 2 otwory M2 w x = 16 i 36 mm. Jej układ (S1 „run”: KEY1–KEY2, S2 „+”: KEY1–KEY3, S3 „−”: KEY3–KEY4) wynika ze schematu z [`docs/schemat.md`](../schemat.md): tego układu nie rysowałem jako osobnego PCB.

## Rozmieszczenie i kontrola

- Rozmieszczenie z `tools/pcb/optimize.py` (wyżarzanie symulowane, 15 000 iteracji, wariant `klin`, **ziarno 4**), zapisane w [`tools/pcb/layout_klin.py`](../../tools/pcb/layout_klin.py).
- **36 mm to praktyczne minimum dla tej reguły.** Z 6 ziaren dla 36 mm trzy dają 0 naruszeń (ziarna 1, 3, 4), dla **34 mm żadne z 6** (najlepsze: 1 naruszenie). Wąskie gardło to pasy nad i pod modułem OLED, w których muszą leżeć wszystkie nóżki elementów tylnych (pod korpusem OLED nie wolno mieć pól lutowniczych), czyli tyle samo miejsca na pady co w płytce podstawowej.
- Kontrola w `build.py`: **0 naruszeń rozmieszczenia, 0 sieci niepołączonych** w sprawdzeniu trasowania (230 odcinków, 1 przelotka). To sprawdzenie wykonalności prostym routerem siatkowym, nie finalna miedź.
- Płytka podstawowa jest po zmianach generatora **bajt w bajt taka sama** jak przed nimi (sprawdzone porównaniem wszystkich generowanych plików z `docs/pcb/`).

## Do sprawdzenia przed zamówieniem

1. **Orientacja ATtiny.** U1 jest obrócony (wcięcie ku prawej krawędzi na widoku z przodu), w specyfikacji kierunek jest wyliczany z pozycji pinów. Wymiana układu wyciągaczem wymaga dostępu od tyłu, tak jak w podstawowej.
2. **Wysokość 8,5 mm dla U1**, wymiary modułu OLED i skok przycisków: jak w płytce podstawowej (szacunki do zmierzenia).
3. Moduł OLED leży teraz pośrodku w pionie, więc **w pasach nad i pod nim zostaje po ok. 11 mm** na nóżki z tyłu. Przy dalszym zmniejszaniu płytki trzeba by zmienić regułę (np. dopuścić nóżki pod korpusem modułu, jeśli moduł będzie wlutowany na listwie).
4. Trasowanie jest jedynie próbą wykonalności.
