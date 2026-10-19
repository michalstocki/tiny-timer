# Obudowa minutnika: wariant „klin” (alternatywa dla płaskiego stosu)

Wariant oparty na szkicu właściciela: bryła w kształcie klina, wyświetlacz na pochyłej ściance frontowej, trzy przyciski na płaskim grzbiecie, głośnik w trójkątnym boku, koszyk 3×AAA od spodu. Model parametryczny w Blenderze 5.2 (mm), budowany skryptem [`tools/enclosure/build_wedge.py`](../../tools/enclosure/build_wedge.py) (funkcje wspólne w [`bpyutil.py`](../../tools/enclosure/bpyutil.py)) z danych płytki **wariantu „klin”**: [`docs/pcb-klin/pcb-layout.json`](../pcb-klin/pcb-layout.json) (48 × 36 mm, bez przycisków, patrz [README płytki](../pcb-klin/README.md)). Iteracja 2 (płaski stos, [`docs/obudowa/`](../obudowa/README.md)) i jej płytka podstawowa ([`docs/pcb/`](../pcb/README.md)) zostają bez zmian i rozwijają się osobno.

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --python tools/enclosure/build_wedge.py
/Applications/Blender.app/Contents/MacOS/Blender --background docs/obudowa-klin/obudowa-klin.blend \
    --python tools/enclosure/check_collisions_wedge.py
# inna płytka lub katalog wyjściowy:
TT_LAYOUT=docs/pcb/pcb-layout.json TT_OUT=docs/obudowa-klin-48x50 \
    /Applications/Blender.app/Contents/MacOS/Blender --background --python tools/enclosure/build_wedge.py
```

Ostatnia komenda buduje klin na płytce podstawowej 48 × 50 mm (jej przyciski S1–S3 są ignorowane, bo w tym wariancie są na osobnej płytce): przekrój wychodzi wtedy ok. 83 × 60 mm.

## Co wynika ze szkicu

| Szkic | W modelu |
| --- | --- |
| Klin leży wzdłuż dłuższej krawędzi, bok jest trójkątem | Przekrój poprzeczny to ścięty trójkąt (trapez): skos frontu 60°, tył 80°, grzbiet płaski 41 mm. Boki trójkątne są zaokrąglone R2 |
| Wyświetlacz na pochyłym froncie | Płytka główna leży **równolegle do skosu** (60°), okno OLED z półkolistymi końcami jak w iteracji 2 |
| Przyciski na grzbiecie, w innej płaszczyźnie niż ekran | **Osobna płytka przycisków** (48 × 16 mm), pozioma, pod grzbietem. Kapsle wystają ponad grzbiet o 1,4 mm |
| Środkowy przycisk niżej, w drobnym wklęsłym obszarze | Kulisty wklęsły wycinek Ø20 × 2,0 mm wokół środkowego przycisku. Kapsel „run” siedzi 2,0 mm niżej niż „−” i „+” i 0,6 mm poniżej otaczającego grzbietu. Grzbiet ma 3,6 mm, więc pod zagłębieniem zostaje 1,6 mm |
| Dół: koszyk z trzema ogniwami w rzędzie, wcięcie z boku | Trzy kanały 11 × 11 mm wzdłuż klina, klapka we wpuście, wycięcie pod palec przy prawym końcu |
| Głośnik w trójkątnym boku (propozycja) | Ø26,5 za lewym bokiem, 23 otwory Ø2,0 we wzorze koncentrycznym. Największe koło wpisane w przekrój ma r = 20,2 mm, więc głośnik (r = 13,5) mieści się z zapasem |

## Wymiary

**74,4 × 75,4 × 46,0 mm** (dł. × głęb. × wys.), płytka główna 48 × 36 mm. Iteracja 2 (płaski stos) ma 76 × 57 × 33,8 mm. Rozmiar wylicza solver w skrypcie (`solve_profile`) dla kątów `ALPHA`, `BETA` i danych z `pcb-layout.json`:

| Płytka główna | Wymiary klina (dł. × głęb. × wys.) |
| --- | --- |
| 48 × 50 mm (podstawowa, po wyjęciu przycisków) | 74,4 × 83,3 × 60,3 mm |
| **48 × 36 mm (wariant „klin”)** | **74,4 × 75,4 × 46,0 mm** |

Z czego wynika przekrój:

- płytka główna z elementami od tyłu (do 8,7 mm) jest nachylona o 60°, jej dolna krawędź leży 11,5 mm (po skosie) od krawędzi podstawy, bo elementy tylne nie mogą wejść w podłogę,
- koszyk (39,4 × 14,2 mm w przekroju) leży z tyłu podstawy (y = 30,2…69,6), za elementami płytki,
- płytka przycisków (16 mm w głąb) leży za górnym końcem płytki głównej (y = 40,5…56,5), więc grzbiet ma 41 mm,
- na styk pokrywy z korpusem na grzbiecie (y = 58,0) zostaje pas z tyłu.

Dalsze zmniejszanie: wysokość wynika głównie z długości płytki po skosie (36 mm), a głębokość z koszyka (39,4 mm) i płytki przycisków. Wyższy kąt skosu (`ALPHA`) zmniejsza głębokość kosztem wysokości, tył bardziej pochylony (`BETA` < 80°) wydłuża obrys w głębi.

## Konstrukcja i montaż

| Część | Zawartość |
| --- | --- |
| `korpus` | tył (80°), podstawa z koszykiem 3×AAA, dwa boki trójkątne, tylny pas grzbietu, pierścień oporowy głośnika |
| `pokrywa` | ścianka frontowa (1,6 mm) + grzbiet (3,6 mm). Niesie **obie** płytki: 4 słupki płytki głównej i 2 słupki płytki przycisków |
| `klapka-baterii` | wpust 0,8 mm + wtyk + dwa języki zatrzaskowe, jak w iteracji 2 |
| `kapsle` | trzy kapsle: „−” i „+” (5,8 mm), „run” (3,8 mm, pomarańczowy z ▶) |

1. Pokrywa trzyma się czterema wkrętami **M2,5 × 6** z boków trójkątnych (po dwa na bok, w zagłębieniach Ø4,8). Wkręcają się w bosy pokrywy (otwór prowadzący Ø2,1). Dolna krawędź pokrywy ma szczelinę 0,25 mm do korpusu, tak samo boki i tył grzbietu.
2. Po wykręceniu wkrętów pokrywa schodzi razem z elektroniką ([08-pokrywa-zdjeta.png](renders/08-pokrywa-zdjeta.png)). Do korpusu idą tylko przewody baterii (przepusty Ø3 w suficie koszyka) i głośnika. Cała elektronika jest odsłonięta od strony elementów, więc dostęp do podstawki ATtiny jest pełny ([09-pokrywa-od-tylu.png](renders/09-pokrywa-od-tylu.png)).
3. Płytka główna: 4 × M2,5 × 6 od tyłu w słupki Ø5,8. Płytka przycisków: 2 × M2 × 6 (otwory Ø2,2 w x = 16 i 32 mm, między przyciskami).
4. Baterie wsuwa się od spodu przez okno w podłodze, klapka zatrzaskuje się we wpuście.

Kierunek wyświetlacza zostaje jak na płytce (górna krawędź płytki ku grzbietowi), więc **firmware bez zmian** (`OLED_FLIP` domyślnie 1).

## Płytka przycisków

Nie jest osobnym projektem PCB, tylko danymi w `pcb-layout.json` (klucz `button_board`) i modelem w obudowie. Opis, schemat połączeń i pola KEY na płytce głównej: [README płytki](../pcb-klin/README.md).

| Parametr | Wartość |
| --- | --- |
| Wymiary | 48 × 16 mm, laminat 1,6 mm, narożniki R2 |
| Przyciski | 3 × Omron B3F-4055, środki x = 8, 24, 40 mm, y = 8 mm (rozstaw 16 mm) |
| Mocowanie | 2 otwory Ø2,2 w x = 16 i 32 mm (M2, słupki Ø3,6 w pokrywie) |
| Przewody do płytki głównej | **4**: GND, PB3 (run), PB4 („+” i „−”), dolna strona „−” (do R6, który zostaje na płytce głównej) |
| Wysokość | laminat leży 10,4 mm pod zewnętrzną powierzchnią grzbietu, trzpienie przycisków kończą się 3,1 mm pod nią |

## Kontrola

- Wszystkie części są bryłami zamkniętymi (0 krawędzi nierozmaitościowych).
- [`check_collisions_wedge.py`](../../tools/enclosure/check_collisions_wedge.py): objętość wspólna korpusu, pokrywy i klapki z płytkami, elementami, ogniwami, stykami, głośnikiem i kapslami wynosi 0 we wszystkich 147 parach, korpus z pokrywą i klapką na siebie nie zachodzą (kontrola dodatnia testu: 0,99 mm³ dla sześcianu 1 mm³).
- Przy przejściu na krótką płytkę trzeba było zmienić konstrukcję koszyka w skrypcie (blok odejmowany od wnętrza zamiast dokładany do gotowej powłoki, szczeliny zachodzące w kanały), bo wcześniejszy sposób dawał zdegenerowane krawędzie. `TT_DEBUG=1` wypisuje liczbę takich krawędzi po każdym etapie korpusu, `TT_DEBUG=2` ich położenie.
- Nie sprawdzałem wytrzymałości, wydruku ani montażu na fizycznych częściach.

## Pliki

| Plik | Zawartość |
| --- | --- |
| `obudowa-klin.blend` | pełna scena (korpus, pokrywa, klapka, kapsle, styki, ogniwa, obie płytki z elementami, głośnik) w osobnych kolekcjach |
| `korpus.stl`, `pokrywa.stl`, `klapka-baterii.stl`, `kapsle.stl` | części do wydruku, w mm, w układzie montażowym (nie w orientacji drukowania) |
| `renders/` | iso z przodu, widok prostopadły do skosu, z góry, bok z głośnikiem, spód z klapką i bez, tył, pokrywa zdjęta i od tyłu, przekrój poprzeczny, zbliżenie przycisków |

## Do uzupełnienia

1. **Orientacja druku.** Pokrywę najlepiej drukować frontem do dołu (skos płasko na stole, obrót o 60° wokół X), korpus podstawą do dołu. STL są w układzie montażowym.
2. **Dioda D1** jest na tylnej stronie płytki i zasłonięta. Trzeba zdecydować, gdzie ma świecić (światłowód w pokrywie albo okno).
3. **Przewody.** Długość zapasu przy zdjętej pokrywie (ok. 40–50 mm) i odciążenie. Przepusty w suficie koszyka są na lewym końcu kanału 1 (−) i prawym kanału 3 (+).
4. **Głośnik** trzyma pierścień Ø31 × 5,5 mm przy lewym boku. Jest potrzebna kropla kleju lub kawałek pianki od tyłu, bo nic nie dociska go do boku.
5. Zęby zatrzasków klapki są prostokątne (jak w iteracji 2), potrzebują skosów wejściowych.
6. Wymiary zagłębienia pod środkowy przycisk (Ø20 × 2,0 mm) i kapsli to wartości projektowe. Warto wydrukować samą pokrywę i sprawdzić wygląd i skok przycisków.
7. Wysokość układu w podstawce (8,5 mm), grubość modułu OLED (4,0 mm) i styki Keystone: jak w README iteracji 2.
