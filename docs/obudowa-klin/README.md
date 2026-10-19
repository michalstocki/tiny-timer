# Obudowa minutnika: wariant „klin” (alternatywa dla płaskiego stosu)

Wariant oparty na szkicu właściciela: bryła w kształcie klina, wyświetlacz na pochyłej ściance frontowej, trzy przyciski na płaskim grzbiecie, głośnik w trójkątnym boku, koszyk 3×AAA od spodu. Model parametryczny w Blenderze 5.2 (mm), budowany skryptem [`tools/enclosure/build_wedge.py`](../../tools/enclosure/build_wedge.py) (funkcje wspólne w [`bpyutil.py`](../../tools/enclosure/bpyutil.py)) z danych płytki [`docs/pcb/pcb-layout.json`](../pcb/pcb-layout.json). Iteracja 2 (płaski stos, [`docs/obudowa/`](../obudowa/README.md)) zostaje bez zmian.

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --python tools/enclosure/build_wedge.py
/Applications/Blender.app/Contents/MacOS/Blender --background docs/obudowa-klin/obudowa-klin.blend \
    --python tools/enclosure/check_collisions_wedge.py
```

## Co wynika ze szkicu

| Szkic | W modelu |
| --- | --- |
| Klin leży wzdłuż dłuższej krawędzi, bok jest trójkątem | Przekrój poprzeczny to ścięty trójkąt (trapez): skos frontu 60°, tył 80°, grzbiet płaski 38 mm. Boki trójkątne są zaokrąglone R2 |
| Wyświetlacz na pochyłym froncie | Płytka główna leży **równolegle do skosu** (60°), okno OLED z półkolistymi końcami jak w iteracji 2 |
| Przyciski na grzbiecie, w innej płaszczyźnie niż ekran | **Osobna płytka przycisków** (48 × 16 mm), pozioma, pod grzbietem. Kapsle wystają ponad grzbiet o 1,4 mm |
| Środkowy przycisk niżej, w drobnym wklęsłym obszarze | Kulisty wklęsły wycinek Ø20 × 2,0 mm wokół środkowego przycisku. Kapsel „run” siedzi 2,0 mm niżej niż „−” i „+” i 0,6 mm poniżej otaczającego grzbietu. Grzbiet ma 3,6 mm, więc pod zagłębieniem zostaje 1,6 mm |
| Dół: koszyk z trzema ogniwami w rzędzie, wcięcie z boku | Trzy kanały 11 × 11 mm wzdłuż klina, klapka we wpuście, wycięcie pod palec przy prawym końcu |
| Głośnik w trójkątnym boku (propozycja) | Ø26,5 za lewym bokiem, 23 otwory Ø2,0 w wzorze koncentrycznym. Największe koło wpisane w przekrój ma r = 26,7 mm, więc głośnik (r = 13,5) mieści się swobodnie |

## Wymiary

**74,4 × 83,3 × 60,3 mm** (dł. × głęb. × wys.). To dużo więcej niż iteracja 2 (76 × 57 × 33,8 mm), bo płaska płytka 48 × 50 mm położona na skosie wymaga przekroju ok. 83 × 60 mm, a nad koszykiem nie może wisieć żaden element. Rozmiar wylicza solver w skrypcie (`solve_profile`) dla kątów `ALPHA`, `BETA` i danych z `pcb-layout.json`.

Z czego wynika przekrój:

- płytka główna z elementami od tyłu (do 8,7 mm) jest nachylona o 60°, jej dolna krawędź leży 14 mm (po skosie) od krawędzi podstawy, bo elementy tylne nie mogą wejść w podłogę,
- koszyk (39,4 × 14,2 mm w przekroju) leży z tyłu podstawy, za elementami płytki,
- płytka przycisków (16 mm w głąb) leży za górnym końcem płytki głównej, więc grzbiet ma 38 mm,
- na styk pokrywy z korpusem na grzbiecie zostaje pas 4 mm.

### Co da krótsza płytka główna

Po wyniesieniu przycisków z płytki głównej jej pas y ≈ 12–28 mm jest z tyłu pusty (tam były pola przycisków). Gdyby przesunąć górną grupę elementów w dół o 14 mm i skrócić płytkę do ok. 36 mm, z mojego solvera wychodzi **ok. 12 mm mniejsza wysokość** (60 → ok. 48 mm) i kilka mm mniejsza głębokość. To zmiana płytki, nie obudowy, ale skrypt przyjmie ją bez zmian, bo czyta `pcb-layout.json`. Model nadal używa płytki 48 × 50 mm z iteracji 1.

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

## Płytka przycisków (propozycja do następnej iteracji PCB)

| Parametr | Wartość |
| --- | --- |
| Wymiary | 48 × 16 mm, laminat 1,6 mm, narożniki R2 |
| Przyciski | 3 × Omron B3F-4055, środki x = 8, 24, 40 mm, y = 8 mm (rozstaw 16 mm, jak na płytce głównej) |
| Mocowanie | 2 otwory Ø2,2 w x = 16 i 32 mm (M2, słupki Ø3,6 w pokrywie) |
| Przewody do płytki głównej | 3 przewody: GND, PB3 (run), PB4 (drabinka „+”/„−”), jeśli R6 (8,2 kΩ dla „−”) przeniesie się na płytkę przycisków. Jeśli R6 zostaje na płytce głównej: 4 przewody |
| Wysokość | laminat leży 10,4 mm pod zewnętrzną powierzchnią grzbietu, trzpienie przycisków kończą się 3,1 mm pod nią |

Na płytce głównej S1–S3 trzeba zastąpić polami lutowniczymi (lub złączem) na wymienione przewody. Model **nie zawiera** przycisków na płytce głównej.

## Kontrola

- Wszystkie części są bryłami zamkniętymi (0 krawędzi nierozmaitościowych).
- [`check_collisions_wedge.py`](../../tools/enclosure/check_collisions_wedge.py): objętość wspólna korpusu, pokrywy i klapki z płytkami, elementami, ogniwami, stykami, głośnikiem i kapslami wynosi 0 we wszystkich 147 parach, korpus z pokrywą i klapką na siebie nie zachodzą (test ma kontrolę dodatnią: 1,00 mm³).
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
