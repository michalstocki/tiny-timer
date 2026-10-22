# Płytka główna (klin 4): projekt do zamówienia

Dwuwarstwowa płytka **40 × 24 mm** z elementami THT dla obudowy [klin 4](../obudowa-klin-4/README.md). Rozmieszczenie, zarys, otwory M2,5 i wysokości są z [`pcb-klin3`](../pcb-klin3/README.md) i **nie zostały zmienione**, więc model obudowy pozostaje ważny. Nowe jest trasowanie, stopki produkcyjne, opisy i pliki do fabryki.

**Status: Gerbery wyeksportowane i sprawdzone w KiCadzie 10.0.7** (DRC KiCada bez błędów, także z regułą odstępu 0,25 mm; Gerbery obejrzane w GerbView). Do fabryki wysyłasz [`produkcja/tt-main-gerber.zip`](produkcja/tt-main-gerber.zip). Przed zamówieniem zmierz jeszcze wysokość C3 (ryzyko 2).

## Pliki

| Plik | Co to |
| --- | --- |
| [`tt-main.kicad_pcb`](tt-main.kicad_pcb) | projekt dla KiCada (format v7, sprawdzony w KiCadzie 10.0.7): obrys, otwory, stopki, sieci, ścieżki, opisy |
| [`trasowanie.json`](trasowanie.json) | zapisane trasowanie (źródło dla pliku KiCada) |
| [`plytka-strona-elementow.svg`](plytka-strona-elementow.svg), [`plytka-strona-lutowania.svg`](plytka-strona-lutowania.svg) | podglądy obu stron z miedzią i opisami |
| [`plan-montazu.svg`](plan-montazu.svg), [`plan-pomiarow.svg`](plan-pomiarow.svg) | rysunki do instrukcji |
| [`instrukcja-montazu.md`](instrukcja-montazu.md) | montaż krok po kroku z kontrolami |
| [`bom.csv`](bom.csv) | lista części |
| [`produkcja/tt-main-gerber.zip`](produkcja/tt-main-gerber.zip) | **plik do wysłania do fabryki**: 7 warstw Gerber, wiercenia PTH i NPTH (Excellon, mm), plik zadania `.gbrjob` |
| `produkcja/` (reszta) | wynik `export_fab.sh`: rozpakowane Gerbery (`gerber/`), raporty DRC KiCada (`drc-kicad.txt`, `drc-kicad-bledy.txt`), mapy wierceń (`mapa-wiercen/`, poza zipem), podglądy `kicad-F.svg` i `kicad-B.svg` |

## Parametry do zamówienia (typowa fabryka 2-warstwowa, np. JLCPCB lub PCBWay)

| Parametr | Wartość |
| --- | --- |
| Warstwy / materiał | 2, FR-4, 1,6 mm, miedź 1 oz (35 µm) |
| Wymiary | 40 × 24 mm, narożniki R3, tolerancja zarysu ±0,2 mm (obudowa przyjmuje ±0,3) |
| Wykończenie pól | HASL bezołowiowy (do lutowania ręcznego wystarczy; ENIG droższy, bez zalet tutaj) |
| Maska, opis | domyślna zielona maska i biały opis |
| Najmniejsza ścieżka / odstęp | 0,30 / 0,28 mm w projekcie (fabryki dają 0,127 mm, więc duży zapas) |
| Najmniejsze wiercenie | 0,4 mm (przelotka, 1 szt.), pola 0,8…1,2 mm, otwór M2,5: 2,7 mm niemetalizowany |
| Liczba sztuk | najmniejsza oferowana (zwykle 5); wystarczy do próby i zapasu |
| Pozostałe opcje | domyślne; fabryka może dodać numer zamówienia na płytce (w miejscu bez miedzi), na ogół można go wyłączyć za dopłatą |

Nazwy opcji w formularzach fabryk różnią się, ale wszystkie powyższe wartości są standardowe. **Zamów kilka sztuk**: płytka jest mała i tania, a pierwsza wersja zawsze może wymagać poprawki.

## Co sprawdziłem

- **DRC własny** ([`tools/pcb/fab_drc.py`](../../tools/pcb/fab_drc.py)), na dokładnej geometrii: 0 błędów. Najmniejszy odstęp miedzi **0,28 mm** (wymagane 0,25), miedź ≥ 0,5 mm od krawędzi płytki, miedź ≥ 3,0 mm od osi otworów M2,5, pierścienie pól ≥ 0,4 mm, przelotka 0,8/0,4 (pierścień 0,2 mm), odstęp otworów ≥ 1,18 mm. Test ujemny: usunięta ścieżka, ścieżka w polu innej sieci i miedź przy krawędzi są wykrywane.
- **Łączność (LVS):** z geometrii miedzi wyliczona łączność jest zgodna z netlistą: każda z 12 sieci w jednym kawałku, 0 zwarć.
- **Netlista** zgodna z referencją z [`tools/breadboard/design.py`](../../tools/breadboard/design.py) (ta sama, z której powstała instrukcja na płytce stykowej), po pominięciu przycisków, modułu OLED i opcjonalnych R7/R8.
- **Zgodność z obudową:** żaden element nie został przesunięty, obrysy i wysokości są z `board.py`, więc wynik kolizji z [README klina 4](../obudowa-klin-4/README.md) pozostaje ważny. Zmienił się tylko rozstaw nóżek C3 (patrz niżej), w obrysie elementu.

- **KiCad 10.0.7** (`export_fab.sh`): plik wczytuje się bez błędów; DRC KiCada: 0 błędów, 0 niepołączonych pól. Zostały same dopuszczalne ostrzeżenia: 18 × brak biblioteki `TT` (stopki są wbudowane w plik), 32 × obrys elementu na polu (maska go przytnie), 4 × stykające się obrysy C2 i C3. Dodatkowo DRC z ostrzejszymi regułami (odstęp 0,25 mm, miedź–krawędź 0,5 mm, otwór–otwór 0,5 mm): 0 błędów; test ujemny z odstępem 0,29 mm wskazuje dwa miejsca z 0,28 mm przy U1.5, czyli KiCad liczy to samo co własny DRC.
- **Napisy w miedzi** (na prośbę fabryki, do kontroli, że warstwy nie są zamienione ani odbite): „TOP” na F.Cu w prawym górnym rogu strony elementów i „BOT” na B.Cu nad napisem TT-MAIN, lustrzany, więc czyta się od strony lutowania. Wysokość 1,2 mm, kreska 0,25 mm, bez sieci. Miejsce wybiera [`fab_cutext.py`](../../tools/pcb/fab_cutext.py): największy odstęp od miedzi, poza opisami i strefami otworów M2,5. DRC KiCada nie zgłasza ich nawet przy odstępie 0,4 mm; na renderze obu stron czytają się prosto.
- **Gerbery** obejrzane w GerbView (wszystkie warstwy razem) i sprawdzone w plikach: obrys 40 × 24 mm z R3, 43 pola, 1 przelotka i napis (TOP/BOT) na obu warstwach miedzi, 45 otworów w masce na każdej stronie (43 pola + 2 otwory M2,5; przelotka pod maską), opis B odbity poprawnie, wiercenia PTH Ø0,4 (przelotka), Ø0,8, Ø0,9, Ø1,2 i osobny plik NPTH z 2 × Ø2,7.
- **Poprawka po pierwszym eksporcie:** napis „TT-MAIN v1.0” wychodził 0,4 mm poza narożnik płytki, bo generator opisów zakładał zbyt wąską czcionkę (0,62 zamiast zmierzonych 0,83 wysokości na znak) i nie sprawdzał łuków narożników. Po poprawce w [`fab_silk.py`](../../tools/pcb/fab_silk.py) opisy przesunęły się o ułamki milimetra (napis DISP na stronie lutowania jest teraz pod polami), żaden nie zniknął; elementy, pola i ścieżki bez zmian.

## Zmiany względem projektu `pcb-klin3`

| Zmiana | Po co |
| --- | --- |
| C3 (elektrolit Ø5 mm): rozstaw nóżek 2,0 mm zamiast 2,54 mm | taki masz kondensator; nóżki leżą teraz na polach bez odginania |
| Pola przewodów (DISP, KEY, SPK, BAT) Ø2,0 mm zamiast Ø2,3 mm, otwór 1,2 mm | Ø2,3 na rozstawie 2,54 mm zostawiało 0,24 mm przerwy między polami SPK i BAT |
| Kwadratowe pola: pin 1 U1, plus C3, anoda D1, **BAT+**, KEY1 (GND), DISP1 (SDA) | rozpoznanie polaryzacji i początku grupy bez opisu |
| Nowe trasowanie (czysty router 45°, 1 przelotka, 276 mm ścieżek) | poprzednie było tylko próbą wykonalności na siatce 0,25 mm |
| Opisy: oznaczenia i obrysy elementów (strona elementów), nazwy pól i numery pinów (strona lutowania) | ułatwienie montażu i pomiarów |
| Napisy „TOP” / „BOT” w miedzi | wymaganie fabryki: kontrola strony i odbicia warstw po wytrawieniu |

## Ryzyka i rzeczy do sprawdzenia przed zamówieniem

1. **Podgląd fabryki.** Pliki sprawdziłem w KiCadzie, ale nie w podglądzie Gerberów u fabryki (wymaga wgrania na jej stronę). Po wgraniu zipa sprawdź, czy fabryka rozpoznała 2 warstwy i wymiar 40 × 24 mm i czy obrazek zgadza się z `produkcja/kicad-F.svg`.
2. **Wysokość C3.** Model obudowy zakłada **8,0 mm** (to założenie z [specyfikacji płytki](../pcb-klin3/specyfikacja-plytki.md), nie pomiar). Typowy elektrolit 100 µF/16 V Ø5 mm ma 11 mm, więc ten, który masz, może nie mieścić się pod sufitem obudowy. Zmierz go suwmiarką przed zamówieniem płytki: jeśli ma 11 mm, potrzebna jest niższa wersja (Ø5 × 7 mm, o ile dostępna) albo sprawdzenie, ile miejsca naprawdę jest nad C3 w modelu obudowy.
3. **Opisy na gęstej płytce.** Nie wszystkie opisy pól się zmieściły (np. pełna lista pinów DISP i KEY, plus BAT). Zamiast urwanych napisów jest nazwa grupy albo nic, a kolejność pinów i kwadratowe pole = pin 1 opisuje [instrukcja](instrukcja-montazu.md) i `plan-pomiarow.svg`.
4. **Grubość opisu 0,15 mm i wysokość 1,0 mm** są na dolnej granicy czytelności u tanich fabryk. Jeśli opis wyjdzie nieczytelny, nie ma to wpływu na działanie.
5. **Brak zabezpieczenia przed odwrotną polaryzacją baterii.** Tak jest w schemacie projektu: kwadratowe pole BAT+ i opis w instrukcji mają to ograniczyć.
6. Pozostałe założenia (wymiary modułu OLED, wysokości elementów, położenie koszyka) są takie jak w [README klina 4](../obudowa-klin-4/README.md).

## Regeneracja

```bash
python3 tools/pcb/fab_build.py              # DRC/LVS, plik KiCada, podglądy, BOM (używa zapisanego trasowania)
python3 tools/pcb/fab_build.py --reroute    # trasuje od nowa (1-3 min) i nadpisuje trasowanie.json
bash tools/pcb/export_fab.sh                # (komputer z KiCadem 8-10) DRC KiCada + Gerbery + wiercenia + zip
```

Moduły: [`fab.py`](../../tools/pcb/fab.py) (stopki, pola, opisy), [`fab_router.py`](../../tools/pcb/fab_router.py), [`fab_drc.py`](../../tools/pcb/fab_drc.py), [`fab_silk.py`](../../tools/pcb/fab_silk.py), [`fab_cutext.py`](../../tools/pcb/fab_cutext.py) (napisy w miedzi), [`fab_kicad.py`](../../tools/pcb/fab_kicad.py), [`fab_render.py`](../../tools/pcb/fab_render.py), [`fab_plan.py`](../../tools/pcb/fab_plan.py).
