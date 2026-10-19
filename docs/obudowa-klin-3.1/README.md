# Obudowa minutnika: wariant „klin 3.1”

Poprawki do [klina 3](../obudowa-klin-3/README.md) po uwagach właściciela (plik koncepcyjny [`obudowa-klin-3.1-concept.blend`](../obudowa-klin-3/obudowa-klin-3.1-concept.blend)). Klin 3 zostaje bez zmian.

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --python tools/enclosure/build_wedge31.py     # -> docs/obudowa-klin-3.1/
/Applications/Blender.app/Contents/MacOS/Blender --background docs/obudowa-klin-3.1/obudowa-klin-3.1.blend \
    --python tools/enclosure/check_collisions_wedge.py                                                      # kolizje części
```

Skrypt [`build_wedge31.py`](../../tools/enclosure/build_wedge31.py) czyta tę samą płytkę (`docs/pcb-klin3/`) i liczy przekrój solverem [`wedge3_solver.py`](../../tools/enclosure/wedge3_solver.py). Zmienna `TT_DELTA` (domyślnie 3 mm) ustawia przesunięcie okna i przycisków, patrz punkt 1.

## Wymiary

**73,0 × 63,7 × 48,5 mm** (dł. × szer. × wys.), bok trójkąta **71,0 mm**.

| | klin 3 | klin 3.1 |
| --- | --- | --- |
| Bok trójkąta | 72,0 mm | **71,0 mm** |
| Wysokość | 49,4 mm | **48,5 mm** |
| Długość | 69,4 mm | 73,0 mm |
| Szerokość bryły (bez łapki) | 64,7 mm | 63,7 mm (zatrzask jest teraz zlicowany, nic nie wystaje) |
| Objętość prostopadłościanu opisanego | 222 cm³ (bez łapki) | 226 cm³ |

Obudowa jest niższa o 0,9 mm i dłuższa o 3,6 mm. Objętość opisana wychodzi więc mniej więcej tak samo (+2%).

## 1. Dłuższa i niższa obudowa

Zauważone w koncepcie: ogniwa mijają się z wtyczkami wyświetlacza, jeśli obudowa jest nieco dłuższa. Policzyłem to solverem: wtyczki (x ≈ 14,7…17,3 mm) leżą teraz **poza zasięgiem ogniw** (ogniwa od x = 19,0), więc w przekroju nie trzeba ich omijać. Przekrój się zmniejsza, ale mniej, niż można by się spodziewać:

| Wariant | Bok | Wysokość |
| --- | --- | --- |
| klin 3 (wtyczki nad ogniwami) | 72,0 | 49,4 |
| wtyczki poza zasięgiem ogniw (bez dodatkowych ograniczeń) | 70,5 | 48,1 |
| **klin 3.1** (jw. + zakładka zatrzasku na prostym odcinku tyłu) | **71,0** | **48,5** |
| jw. z promieniem wierzchołka RA 10 zamiast 13 mm | 69,0 | 49,8 (wyższy szczyt przy ostrzejszym wierzchołku, mniejsza podstawa) |

Układ w X: lewy bok 3 mm, głośnik, **strefa wtyczek**, przegroda, ogniwa 51 mm, prawy bok 3 mm. Żeby nie wydłużać obudowy bardziej, okno wyświetlacza i przyciski są **przesunięte o 3 mm w lewo** względem środka długości (wtyczki są przy lewym końcu modułu). Przy przesunięciu 0 mm obudowa miałaby 79 mm, przy 4,8 mm (maksimum) 69,4 mm.

## 2. Zatrzask: U-shaped snap fit i druk 3D

Przeanalizowałem trzy układy dla zatrzasku z tyłu (PETG ok. 1,2…1,5 GPa, dopuszczalne odkształcenie przy wielokrotnym zginaniu ok. 2% dla PETG i 1…1,5% dla PLA; odkształcenie belki prostokątnej ε = 1,5 · t · δ / L², t grubość, δ ugięcie na końcu, L długość):

| Układ | t | δ | L | ε | Uwagi |
| --- | --- | --- | --- | --- | --- |
| A. język jak w klinie 3 (belka po ściance) | 1,2 | 0,9 | 10 | 1,6% | PLA na granicy. **Wykryłem błąd w klinie 3:** język 10 mm wystawał ok. 3 mm poza prosty odcinek tyłu (ten kończy się 8,7 mm od narożnika podstawy), czyli w zaokrąglenie. |
| B. szpilka „U” w przekroju bocznym (dwa ramiona jedno nad drugim) | 1,0 + 1,0 | | 2 × 9 | ok. 0,4% | Wymaga ok. 3 mm w poprzek ścianki, a ścianka ma 2 mm. Zaczep byłby na zewnętrznym ramieniu, a ręka dosięga tylko jego. Odpada. |
| **C. język w kształcie U-szczeliny, belka wzdłuż X** | 1,4 | 1,0 | **21** | **0,5%** | **Zastosowany.** Szczelina U (górna i na wolnym końcu) wycina w tylnej ściance pokrywy język 21 × 8 mm, zamocowany po lewej stronie. Szczelina U jest tu wycięciem wokół języka, a nie zagiętą sprężyną. |

Szczegóły układu C (rendery 07, 08, 15):
- Język leży po lewej stronie tyłu, poza płytką główną (jej x zaczyna się od 28 mm). Odciążenie od wnętrza (grubość 1,4 mm zamiast 2,0) zmniejsza ugięcie przy zginaniu, a przy zamocowaniu jest pełne 2,0 mm.
- Przy dolnej krawędzi pokrywy język przechodzi w **wargę** 1,0 mm (5 mm po ściance), leżącą we wpuście korpusu, zlicowaną z powierzchnią. Warga niesie zaczep 0,8 mm (płaska ścianka 90° od góry, rampa od dołu), który zaskakuje w rowek w korpusie. Tylna ścianka korpusu jest tam pogrubiona od wnętrza o 1,4 mm (rendery 15).
- **Zwalnianie palcem:** nacisnąć język w pobliżu wolnego końca (x ≈ 20…26 mm) do środka, zaczep wychodzi z rowka (ugięcie ok. 1 mm, siła ok. 1…2 N), pokrywa idzie w górę. Zamknięcie: pokrywa pionowo w dół, rampa odgina język i zaczep zaskakuje.
- Płaska ścianka zaczepu trzyma pokrywę niezależnie od sztywności języka. Orientacyjnie nośność zaczepu na ścinanie (powierzchnia ok. 2 × 6,5 mm, wytrzymałość PETG wzdłuż warstw ok. 25 MPa) to setki niutonów, wielokrotnie więcej niż potrzeba.

**Orientacja druku (to jest warunek, żeby zatrzask działał):** język jest belką wzdłuż X, a FDM jest słaby w kierunku Z. Dlatego pokrywę trzeba drukować **leżącą na tylnej ściance** (płasko), a **nie** stojącą na boku (wtedy oś języka byłaby w kierunku Z i pękałby między warstwami). Płasko na tylnej ściance: język i warga leżą w płaszczyźnie warstw (naprężenia wzdłuż włókien), słupki płytki stoją pionowo, a ścianka frontu jest pochylona 30° od pionu, więc nie wymaga podpór. Podpór wymagają tylko końcówki frontu (nosek i języczki, patrz niżej), bo zakręcają się do wnętrza.
Korpus drukuje się podstawą do dołu.

## 3. Krawędź styku od frontu

- **Szew przeniesiony na narożnik** frontu z podstawą (zaokrąglenie R5, szew na ok. 208° normalnej, czyli tuż nad stołem, rendery 01, 18). Cały front i górna część narożnika to teraz pokrywa, a korpus od frontu to płytka taca (podłoga, narożnik, boki). Ogniwa wkłada się więc swobodnie od góry i z przodu.
- **Dwa języczki** (8 × 0,8 mm, w x = 25,5 i 50,5 mm) schodzą z pokrywy pod noskiem w szczeliny w podłodze korpusu (render 19). Trzymają przednią krawędź przed poprzecznym podważaniem i przesuwaniem. **Nie trzymają jej przed podniesieniem do góry**: do tego służy zatrzask z tyłu. Jeśli podniesienie przedniej krawędzi paznokciem ma być zablokowane, można dać języczkom zadziory (wtedy pokrywę zdejmuje się wolniej, z lekkim oporem), ale tego nie robiłem bez Twojej decyzji.

## 4. Szpary i zakładki

- **Front i tył:** zakładka połówkowa na całej długości szwu. Na froncie wewnętrzna połowa ścianki (nosek, ok. 30°) schodzi pod zewnętrzną połowę korpusu i opiera się na ramieniu korpusu (luz nominalny 0,05 mm), więc pokrywa **leży na korpusie** na całej długości; zewnętrzna szczelina ma 0,25 mm. Na tyle zewnętrzna warga pokrywy (1,0 mm, 5 mm po ściance) leży we wpuście korpusu na całej szerokości, a dolna krawędź pokrywy siada na ramieniu korpusu (luz 0,05 mm).
- **Boki:** zewnętrzna połowa ścianki pokrywy (0,9 mm) wchodzi o 1 mm w wycięcie w bocznych ściankach i zasłania szczelinę 0,25 mm. Zakładka boczna jest tylko tam, gdzie zdejmowanie w górę jest swobodne (od frontu do normalnej 172°). Na ostatnich kilku milimetrach narożnika frontu zostaje zwykła szczelina 0,25 mm bez zakładki, bo zewnętrzna zakładka na dolnej stronie zaokrąglenia blokowałaby zdejmowanie pokrywy.
- Korpus ma teraz przegrodę (1,2 mm) między strefą wtyczek a ogniwami i podłogę z dwoma korytkami; górne ogniwo leży w dolince jak w klinie 3.

## Kontrola

- Wszystkie części są bryłami zamkniętymi (0 krawędzi nierozmaitościowych).
- [`check_collisions_wedge.py`](../../tools/enclosure/check_collisions_wedge.py): **0 kolizji w 106 parach**, kontrola dodatnia testu 1,00 mm³. Od tej wersji test liczy objętość wspólną w obu kolejnościach (dokładne booleany bywają asymetryczne przy stykających się powierzchniach: jeden rząd dawał 0, drugi 5 mm³). Ponowne przeliczenie klina 3 też daje 0.
- [`check_assembly_wedge3.py`](../../tools/enclosure/check_assembly_wedge3.py) na wariancie bez zaczepu: **zdejmowanie pokrywy pionowo w górę** (0,5…48 mm) i **wkładanie ogniw** po kolei wzdłuż frontu: 0 kolizji. Pierwsze podejście miało kolizje: zewnętrzna zakładka boczna na dolnej stronie zaokrąglenia (zablokowałaby pokrywę), przegroda przecinająca tor noska, języczek stykający się z przegrodą i podłogą. Poprawione.
- Nie sprawdzałem wytrzymałości, wydruku, ugięcia zatrzasku ani montażu na fizycznych częściach.

## Do uzupełnienia i ryzyka

1. **Język zatrzasku nieprzetestowany.** Obliczenie ugięcia 0,5% jest szacunkowe (ugięcie 1,0 mm, jednolita belka). Warto wydrukować sam tył pokrywy w PETG leżąc na tylnej ściance. Parametry do zmiany w skrypcie: `TAB_X0/TAB_X1` (długość języka), `TAB_H`, `HOOK`, odciążenie `relief`.
2. **Zakładki o grubości 0,7…0,9 mm** (nosek, zewnętrzna połowa boków) są cienkie jak na FDM z dyszą 0,4 mm. Drukować ostrożnie, najlepiej drobniejszą warstwą.
3. **Okno i przyciski przesunięte o 3 mm** względem środka długości. Przy `TT_DELTA = 0` obudowa miałaby 79 mm.
4. Pozostałe punkty jak w klinie 3 (przewody do pokrywy i złącza, górne ogniwo bez zamocowania, płytka przycisków 50 × 16 mm, wymiary wtyczek wyświetlacza).
