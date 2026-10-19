# Obudowa minutnika: wariant „klin” (leżący graniastosłup, bok = trójkąt równoboczny)

Wariant oparty na szkicu właściciela: **leżący graniastosłup o podstawie trójkąta równobocznego**, wszystkie krawędzie zaokrąglone. Wyświetlacz jest na pochyłej ściance frontowej, przyciski na zaokrąglonym wierzchołku (górnej krawędzi), głośnik w trójkątnym boku, koszyk 3×AAA od spodu. Model parametryczny w Blenderze 5.2 (mm), budowany skryptem [`tools/enclosure/build_wedge.py`](../../tools/enclosure/build_wedge.py) (funkcje wspólne w [`bpyutil.py`](../../tools/enclosure/bpyutil.py)) z danych płytki wariantu „klin”: [`docs/pcb-klin/pcb-layout.json`](../pcb-klin/pcb-layout.json) (48 × 36 mm, bez przycisków, patrz [README płytki](../pcb-klin/README.md)). Iteracja 2 (płaski stos, [`docs/obudowa/`](../obudowa/README.md)) i jej płytka podstawowa ([`docs/pcb/`](../pcb/README.md)) zostają bez zmian i rozwijają się osobno.

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --python tools/enclosure/build_wedge.py
/Applications/Blender.app/Contents/MacOS/Blender --background docs/obudowa-klin/obudowa-klin.blend \
    --python tools/enclosure/check_collisions_wedge.py
# inna płytka lub katalog wyjściowy:
TT_LAYOUT=docs/pcb/pcb-layout.json TT_OUT=docs/obudowa-klin-48x50 \
    /Applications/Blender.app/Contents/MacOS/Blender --background --python tools/enclosure/build_wedge.py
```

Ostatnia komenda buduje obudowę na płytce podstawowej 48 × 50 mm (jej przyciski S1–S3 są ignorowane, bo w tym wariancie są na osobnej płytce): trójkąt wychodzi wtedy większy.

## Kształt

| Szkic | W modelu |
| --- | --- |
| Bok to trójkąt równoboczny z zaokrąglonymi rogami | Przekrój poprzeczny: trójkąt równoboczny (`THETA` = 60°, oba skosy po 60°), bok 80 mm, rogi zaokrąglone: **R13 przy wierzchołku** (górna krawędź) i **R5 przy podstawie** |
| Wszystkie krawędzie zaokrąglone | Trzy długie krawędzie zaokrąglone jak wyżej, a obwód obu boków trójkątnych R3 (`R_END`). Płaska jest tylko podstawa, ścianka frontowa i tylna |
| Wyświetlacz na pochyłym froncie | Płytka główna leży **równolegle do skosu** (60°), okno OLED z półkolistymi końcami jak w iteracji 2 |
| Przyciski na górnej krawędzi, w innej płaszczyźnie niż ekran | **Osobna płytka przycisków** (52 × 16 mm), pozioma, pod wierzchołkiem (rozstaw przycisków 18 mm) |
| „−” i „+” wypukłe, bo zlicowane z zaokrągleniem krawędzi | Kapsle Ø9,6, których górna powierzchnia jest fragmentem walca R12,85 współosiowego z wierzchołkiem (0,15 mm pod zewnętrzną powierzchnią). Wypukłość to po prostu krzywizna krawędzi, symbole „−” i „+” są wygrawerowane |
| Środkowy: tabletka, lekko wypukły, w obniżeniu | Kapsel „run” to **tabletka 14 × 9,5 mm** z kopułą (R25, wypukłość ok. 0,5–1 mm), jej szczyt leży 0,6 mm pod szczytem wierzchołka. Siedzi w wydłużonym, gładkim **obniżeniu** (elipsoida 22 × 12 mm na powierzchni, głębokość 2 mm), więc nad dnem obniżenia wystaje 1,4 mm |
| Głośnik na trójkątnym boku (propozycja) | Ø26,5 za lewym bokiem, 23 otwory Ø2,0 we wzorze koncentrycznym. Największe koło wpisane w przekrój ma r = 21,2 mm, głośnik z pierścieniem oporowym (r = 15,4) mieści się z zapasem |

Wierzchołek ma pod przyciskami grubą masę (4,4 mm: 2,4 mm pod obniżeniem + 2,0 mm jego głębokości), więc kapsle prowadzą się w otworach przez całą grubość, a nad płytką przycisków jest płaski sufit.

## Wymiary

**77,4 × 72,7 × 56,3 mm** (dł. × szer. × wys.; po zaokrągleniu, bok trójkąta 80 mm, wysokość ostrego wierzchołka 69,3 mm, szczyt po zaokrągleniu 56,3 mm). Iteracja 2 (płaski stos) ma 76 × 57 × 33,8 mm: trójkąt równoboczny jest wyraźnie większy, bo zawartość układa się według skosów, a nie prostokąta. Rozmiar wylicza solver w skrypcie (`solve_side`) dla `THETA`, `RA`, `RB` i danych z `pcb-layout.json`: najmniejszy bok, w którym mieszczą się płytka z elementami od tyłu, koszyk i płytka przycisków.

Z czego wynika bok 80 mm:

- płytka główna z elementami od tyłu (do 8,7 mm) jest nachylona o 60°, jej dolna krawędź leży 11 mm (po skosie) od krawędzi podstawy, bo elementy tylne nie mogą wejść w podłogę,
- koszyk (39,4 × 14,2 mm w przekroju) leży z tyłu podstawy (y = 30,0…69,4), nad nim nic nie wisi,
- płytka przycisków (16 mm w głąb) leży w wierzchołku, nad nią sufit jest 6,8 mm nad laminatem.

Dla porównania: ten sam trójkąt na płytce 48 × 50 mm miałby bok ok. 82 mm i wysokość z zaokrągleniem ok. 59 mm. Mniejsze rogi (R12 przy wierzchołku, R4 przy podstawie) zmniejszają bok tylko o ok. 2 mm. Płytka główna jest już najkrótszą, jaką da się rozmieścić (patrz README płytki), a o rozmiarze decyduje głównie koszyk 39,4 mm i płytka przycisków. Układ ogniw w trójkąt (2 + 1) albo koszyk przy tylnej ściance dałby mniejszy trójkąt, ale to inna koncepcja niż szkic (koszyk od spodu).

## Konstrukcja i montaż

| Część | Zawartość |
| --- | --- |
| `korpus` | tył, podstawa z koszykiem 3×AAA, dwa boki trójkątne R3 (grubość 3 mm), dolny pas frontu, pierścień oporowy głośnika |
| `pokrywa` | front (1,6 mm) + wierzchołek (masa 4,4 mm) + górny pas tyłu. Niesie **obie** płytki: 4 słupki płytki głównej i 2 słupki płytki przycisków |
| `klapka-baterii` | wpust 0,8 mm + wtyk + dwa języki zatrzaskowe, jak w iteracji 2 |
| `kapsle` | „−” i „+” (Ø9,6, zlicowane z łukiem) oraz „run” (tabletka, pomarańczowa z ▶) |

Pokrywa leży między bokami trójkątnymi (x = 3,25 … 74,15), poza zaokrągleniem ich krawędzi, więc zaokrąglenia boków są nieprzerwane.

1. Pokrywa trzyma się czterema wkrętami **M2,5 × 8** z boków trójkątnych (po dwa na bok, w zagłębieniach Ø4,8, widoczne na rendererze 04). Wkręcają się w bosy pokrywy (otwór prowadzący Ø2,1). Szczelina między pokrywą a korpusem to 0,25 mm.
2. Po wykręceniu wkrętów pokrywę **podnosi się pionowo** razem z elektroniką ([08-pokrywa-zdjeta.png](renders/08-pokrywa-zdjeta.png)); obejmuje wierzchołek, więc w bok ani do przodu nie zejdzie. Do korpusu idą tylko przewody baterii (przepusty Ø3 w suficie koszyka) i głośnika. Elektronika jest odsłonięta od strony elementów, więc dostęp do podstawki ATtiny jest pełny ([09-pokrywa-od-tylu.png](renders/09-pokrywa-od-tylu.png)).
3. Płytka główna: 4 × M2,5 × 6 od tyłu w słupki Ø5,8. Płytka przycisków: 2 × M2 × 6 (otwory Ø2,2 w x = 16 i 36 mm, między przyciskami).
4. Baterie wsuwa się od spodu przez okno w podłodze, klapka zatrzaskuje się we wpuście.

Kierunek wyświetlacza zostaje jak na płytce (górna krawędź płytki ku wierzchołkowi), więc **firmware bez zmian** (`OLED_FLIP` domyślnie 1).

## Płytka przycisków

Nie jest osobnym projektem PCB, tylko danymi w `pcb-layout.json` (klucz `button_board`) i modelem w obudowie. Opis, schemat połączeń i pola KEY na płytce głównej: [README płytki](../pcb-klin/README.md).

| Parametr | Wartość |
| --- | --- |
| Wymiary | 52 × 16 mm, laminat 1,6 mm, narożniki R2 |
| Przyciski | 3 × Omron B3F-4055, środki x = 8, 26, 44 mm, y = 8 mm (rozstaw 18 mm) |
| Mocowanie | 2 otwory Ø2,2 w x = 16 i 36 mm (M2, słupki Ø3,6 w pokrywie) |
| Przewody do płytki głównej | **4**: GND, PB3 (run), PB4 („+” i „−”), dolna strona „−” (do R6, który zostaje na płytce głównej) |
| Wysokość | laminat leży 11,2 mm pod szczytem wierzchołka, trzpienie przycisków kończą się 3,9 mm pod nim |

## Kontrola

- Wszystkie części są bryłami zamkniętymi (0 krawędzi nierozmaitościowych).
- [`check_collisions_wedge.py`](../../tools/enclosure/check_collisions_wedge.py): objętość wspólna korpusu, pokrywy i klapki z płytkami, elementami, ogniwami, stykami, głośnikiem i kapslami wynosi 0 we wszystkich 147 parach, korpus z pokrywą i klapką na siebie nie zachodzą (kontrola dodatnia testu: 1,00 mm³).
- Pierwsze podejście miało jeden błąd: kołnierz tabletki dotykał słupka płytki przycisków (2 mm³). Słupki są teraz w x = 16 i 36, kołnierz węższy.
- `TT_DEBUG=1` wypisuje liczbę krawędzi nierozmaitościowych po każdym etapie korpusu, `TT_DEBUG=2` ich położenie.
- Nie sprawdzałem wytrzymałości, wydruku ani montażu na fizycznych częściach. Kształt kapsli, tabletki i obniżenia oceniłem tylko po renderach.

## Pliki

| Plik | Zawartość |
| --- | --- |
| `obudowa-klin.blend` | pełna scena (korpus, pokrywa, klapka, kapsle, styki, ogniwa, obie płytki z elementami, głośnik) w osobnych kolekcjach |
| `korpus.stl`, `pokrywa.stl`, `klapka-baterii.stl`, `kapsle.stl` | części do wydruku, w mm, w układzie montażowym (nie w orientacji drukowania) |
| `renders/` | iso z przodu, widok prostopadły do skosu, z góry, bok z głośnikiem (kształt trójkąta), spód z klapką i bez, tył, pokrywa zdjęta i od tyłu, przekrój poprzeczny, przekrój przez przycisk „+”, zbliżenie przycisków z ukosa i z góry |

## Do uzupełnienia

1. **Orientacja druku.** Pokrywę najlepiej drukować frontem do dołu (skos płasko na stole, obrót o 60° wokół X), korpus podstawą do dołu. STL są w układzie montażowym.
2. **Dioda D1** jest na tylnej stronie płytki i zasłonięta. Trzeba zdecydować, gdzie ma świecić (światłowód w pokrywie albo okno).
3. **Przewody.** Długość zapasu przy zdjętej pokrywie (ok. 40–50 mm) i odciążenie. Przepusty w suficie koszyka są na lewym końcu kanału 1 (−) i prawym kanału 3 (+).
4. **Głośnik** trzyma pierścień Ø31 × 5,5 mm przy lewym boku. Jest potrzebna kropla kleju lub kawałek pianki od tyłu, bo nic nie dociska go do boku.
5. Zęby zatrzasków klapki są prostokątne (jak w iteracji 2), potrzebują skosów wejściowych.
6. **Kapsle.** Wygląd „−” i „+” (owalny kontur wynika z przecięcia walca z walcem) i tabletki warto ocenić na wydruku. Tabletka siedzi w otworze z luzem 0,3 mm, jej kołnierz od spodu jest ogranicznikiem wysuwu. Skok przycisku B3F nie jest znany (karta nie podaje), luz na ruch trzpienia przyjęty 0,5 mm.
7. Wysokość układu w podstawce (8,5 mm), grubość modułu OLED (4,0 mm) i styki Keystone: jak w README iteracji 2.
8. Jeśli ten kształt okaże się za duży, najpierw sprawdzić układ ogniw (patrz Wymiary), bo na niego wpływa najwięcej.
