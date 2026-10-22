# Obudowa minutnika: wariant „klin 4”

Kolejna iteracja po przeglądzie [klina 3.1](../obudowa-klin-3.1/README.md). Wprowadza zmiany z przeglądu (szew tyłu na narożniku, wyświetlacz bez wtyczek, okno na środku) oraz trzy uwagi właściciela: gniazda styków zgodne z kartami Keystone, kapsle wciskane na trzpień B3F-4055 i zatrzask, którego nie da się otworzyć, ciągnąc przednią krawędź. Klin 3.1 zostaje bez zmian.

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --python tools/enclosure/build_wedge4.py                 # -> docs/obudowa-klin-4/
TT_NOHOOK=1 /Applications/Blender.app/Contents/MacOS/Blender --background --python tools/enclosure/build_wedge4.py     # wariant bez zaczepów (kontrola zdejmowania)
/Applications/Blender.app/Contents/MacOS/Blender --background docs/obudowa-klin-4/obudowa-klin-4.blend --python tools/enclosure/check_collisions_wedge.py
/Applications/Blender.app/Contents/MacOS/Blender --background docs/obudowa-klin-4/obudowa-klin-4-bez-zaczepow.blend --python tools/enclosure/check_assembly_wedge4.py
/Applications/Blender.app/Contents/MacOS/Blender --background docs/obudowa-klin-4/obudowa-klin-4.blend --python tools/enclosure/check_assembly_wedge4.py -- blokada
```

Skrypty: [`build_wedge4.py`](../../tools/enclosure/build_wedge4.py) (model), [`wedge4_solver.py`](../../tools/enclosure/wedge4_solver.py) (przekrój), [`check_assembly_wedge4.py`](../../tools/enclosure/check_assembly_wedge4.py) (zdejmowanie, ogniwa, blokada). Płytka główna bez zmian: [`docs/pcb-klin3/`](../pcb-klin3/README.md) (projekt do zamówienia i instrukcja montażu: [`docs/plytka-glowna/`](../plytka-glowna/README.md)) (40 × 24 mm, obrócona o 180° względem klina 3.1, więc pola DISP i KEY są przy dolnej krawędzi). Płytka przycisków ma nowy rozstaw pod płytkę uniwersalną (punkt 5).

## Wymiary

**74,2 × 60,2 × 45,5 mm** (dł. × szer. × wys.), bok trójkąta **67,5 mm**.

| | klin 3.1 | klin 4 |
| --- | --- | --- |
| Bok trójkąta | 71,0 mm | **67,5 mm** |
| Wysokość | 48,5 mm | **45,5 mm** (−3,0) |
| Szerokość | 63,7 mm | **60,2 mm** (−3,5) |
| Długość | 73,0 mm | 74,2 mm (+1,2) |
| Pole przekroju | 20,3 cm² | **18,2 cm²** (−10%) |
| Prostopadłościan opisany | 226 cm³ | **203 cm³** (−10%) |
| Front (dł. : wys.) | 1,51 | 1,63 |
| Okno i przyciski | 3 mm w lewo od środka | **na środku** |

Proporcje: front 74,2 × 45,5 mm ma stosunek boków 1,63 (blisko złotego podziału), więc obudowa wygląda na wyraźnie leżącą bryłę, a nie na sześcian. Długość wzrosła o 1,2 mm, bo zatrzaski po prawej stronie dostały własną strefę (punkt 2).

## 1. Przekrój

Solver [`wedge4_solver.py`](../../tools/enclosure/wedge4_solver.py) liczy najmniejszy bok przy tych samych zasadach co w klinie 3.1, z trzema zmianami:

- **Szew tyłu na narożniku tyłu** (lustrzanie do frontu). Płytka główna schodzi po tylnej ściance aż do zaokrąglenia. To główne źródło zysku: w klinie 3.1 wymiar wyznaczały płytka główna, płytka przycisków i warga zatrzasku na prostym odcinku tyłu (bez ogniw wychodziło tyle samo).
- **Ogniwa w rzędzie na podłodze**, oś-oś 11,5 mm. Układ 2 + 1 się nie mieści z prawdziwymi stykami: płytki 9,2 × 10,4 i 21,0 × 11,0 mm przy ogniwach oddalonych o 11,5 mm nachodziłyby na siebie. Rząd trzech ogniw z dwoma stykami podwójnymi to układ z rysunku montażowego Keystone (Fig. 2).
- **Wyświetlacz bez wtyczek.** Przewody wlutowane w moduł i położone płasko (ok. 3 mm). Moduł może wtedy leżeć nad ogniwami, nie potrzeba osobnej strefy wtyczek, a okno i przyciski są na środku długości.

Co ogranicza przekrój teraz (pełne warunki, siatka 0,5 mm):

| Zmiana | Bok | Wysokość |
| --- | --- | --- |
| **klin 4** | **67,5** | **45,5** |
| bez ogniw | 65,0 | 43,3 |
| bez płytki przycisków | 67,0 | 45,0 |
| bez wyświetlacza | 67,5 | 45,5 |
| bez płytki głównej | 58,0 | 37,2 |
| **promień wierzchołka RA 16 zamiast 13 mm** | 67,5 | **42,5** |

Ogniwo przy froncie trzyma się 15,0 mm od krawędzi podstawy. Górny róg płytki styku (5,5 mm nad osią ogniwa, 4,75 mm przed nią) nie może wejść w pochyłą ścianę frontu. To kosztuje ok. 1 mm boku. Kolejna dźwignia to **RA 16**: wysokość spada o 3 mm przy tej samej szerokości, ale wierzchołek jest wyraźnie bardziej zaokrąglony. Tego nie zmieniałem, bo to decyzja o wyglądzie.

## 2. Zatrzaski

**Czy da się otworzyć obudowę, ciągnąc przednią krawędź w przód lub w górę? Nie.** Sprawdziłem to na modelu ([`check_assembly_wedge4.py`](../../tools/enclosure/check_assembly_wedge4.py) `-- blokada`). Pokrywa w położeniu zamkniętym nie koliduje z korpusem (0 mm³), a każdy z pięciu ruchów daje kolizję, czyli jest zablokowany:

| Ruch pokrywy | Objętość wspólna z korpusem | |
| --- | --- | --- |
| w górę o 0,4 mm | 2,2 mm³ | zablokowane (zaczepy pod półkami) |
| w przód o 0,4 mm | 28,7 mm³ | zablokowane (nosek frontu w zakładce korpusu, nogi o półki) |
| w tył o 0,4 mm | 24,6 mm³ | zablokowane |
| przednia krawędź w górę o 1° (obrót wokół tylnego narożnika) | 4,1 mm³ | zablokowane |
| tylna krawędź w górę o 1° | 3,8 mm³ | zablokowane |

**Budowa** (rendery 14, 15, 06):
- **Cztery nogi zatrzasku** (dwie przy froncie, dwie przy tyle) w strefach na końcach: przy głośniku (x = 5,3 mm) i w strefie 4,5 mm przy prawym boku (x = 69,0 mm). Nie ma ich w strefie ogniw. Noga 1,2 mm przy narożniku w strefie ogniw kosztowałaby od 1,5 do 6 mm boku.
- Noga to pionowa płytka 3,5 × 1,2 mm, przyrośnięta do wewnętrznej strony ściany pokrywy. Wolna długość wynosi 11,5 mm z przodu i 10,7 mm z tyłu. Na dole ma **zaczep skierowany na zewnątrz** (0,8 mm), z poziomą górną ścianką i skośną (45°) dolną.
- Zaczep chwyta od dołu **poziomą półkę** w korpusie (1,0 mm, zachodzi 0,6 mm). Ciągnięcie pokrywy w górę dociska zaczep do półki płaską ścianką. Nie ma składowej, która odginałaby nogę. Siła na zaczepie działa na zewnątrz osi nogi, więc nacisk jeszcze bardziej ją dociska.
- Przód i tył zamykają się tak samo (lustrzane narożniki): **zakładka połówkowa z noskiem** jak na froncie klina 3.1. Zewnętrzna połowa ścianki korpusu zachodzi na nosek pokrywy, więc krawędzi nie da się odchylić na zewnątrz.
- Zamykanie: pokrywa pionowo w dół, skośna dolna ścianka zaczepu odgina nogę do środka i zaczep wskakuje pod półkę.
- Odkształcenie nogi przy zwalnianiu (ugięcie 0,8 mm): **1,1% z przodu, 1,3% z tyłu**. PETG to wytrzymuje (ok. 2%), PLA jest blisko granicy. Siła odgięcia wynosi ok. 1,5…2 N.
- Nośność (szacunek): ścinanie zaczepu i zginanie półki to po ok. 30 N na zatrzask, czyli razem ponad 100 N. Urządzenie z bateriami waży ok. 0,1 kg.

**Otwieranie:** w spodzie są cztery otwory Ø1,6 mm (render 06), po jednym pod każdym zaczepem. Wsunąć wyprostowany spinacz (Ø ≤ 1,2 mm) i nacisnąć: spinacz trafia w skośną dolną ściankę zaczepu, odgina nogę do środka i unosi róg. Zaczep powinien wtedy oprzeć się na górze półki, a róg zostać uniesiony o ok. 2 mm. Tak po kolei przy wszystkich czterech, potem zdjąć pokrywę. Żeby róg mógł się unieść, kiedy pozostałe trzymają, zakładki boczne mają w głąb wcięcia 1,0 mm luzu (w klinie 3.1 było 0,2). Luz jest schowany pod zakładką i nie zmienia szczeliny 0,25 mm widocznej z zewnątrz. Tego, czy róg zostaje na półce, nie da się sprawdzić na modelu sztywnym. Jeśli wraca, trzeba zwolnić oba zatrzaski jednej strony naraz.

**Uwaga do klina 3.1:** w jego zatrzasku zaczep jest skierowany do wnętrza, więc wciśnięcie języka (jak opisuje README) wciska zaczep głębiej w rowek. Zwolnić go można tylko, odciągając język na zewnątrz. Na pochyłej ściance „płaska” ścianka zaczepu działa jak skos 60° względem kierunku zdejmowania, a zatrzask jest tylko jeden, przy lewym końcu. Dlatego klin 4 ma zatrzaski przy podstawie.

## 3. Koszyk i styki Keystone

Wymiary z katalogu Keystone M65 (s. 16: rysunki styków, s. 37: rozmieszczenie): [katalog M65 (Keystone Europe)](https://keystone-europe.com/wp-content/uploads/catalog-keystone-europe.pdf), [karta styków z wymiarami (K75 s. 17)](https://www.keyelco.com/userAssets/file/K75p17.pdf).

| Styk | Kat. nr | Wymiary przyjęte w modelu | Gdzie |
| --- | --- | --- | --- |
| (−) sprężyna z blaszką | **5204** | płytka 9,2 × 10,4 × 0,51, środek sprężyny 5,5 od krawędzi z blaszką; blaszka 3,0 × 6,6 (17,0 razem z płytką), 1,5 od brzegu płytki | prawy koniec, ogniwo A (przy froncie): **BAT−** |
| (+) przycisk z blaszką | **5226** | jak 5204, przycisk Ø4,0 × 1,09 | lewy koniec, ogniwo C (przy tyle): **BAT+** |
| podwójny (sprężyna + przycisk) | **5213 / 5214** | płytka 21,0 × 11,0 × 0,51, środki co 11,5 mm, dwa zaczepy 1,5 mm pod płytką, środki 7,0 mm nad spodem zaczepów | lewy: przycisk A, sprężyna B; prawy: przycisk B, sprężyna C |

- **Odległość płytek: 49,5 mm** (Keystone dla AAA, para 5204 + 5226 i para 5213/5214 + 5203/5225). Sprężyna jest ściśnięta do ok. 3,9 mm.
- **Gniazdo:** ścianka 2,7 mm na każdym końcu: tył 1,0 mm, **szczelina 0,8 mm** na płytkę 0,51 (luz 0,25 mm na boki) i **wargi 0,9 mm**, które zachodzą 1,0 mm na pionowe i dolny brzeg płytki. Płytki wsuwa się od góry, a ogniwa dociskają je do tyłu szczeliny (render 19, 11).
- Płytka podwójna stoi na swoich zaczepach w szczelinie w dnie (0,8 mm dna pod spodem). Pojedyncze stoją odwrócone blaszką do góry, bo blaszka skierowana w dół wyszłaby pod spód obudowy. Blaszka 5226 (ogniwo C) wystaje prosto w górę. Blaszkę 5204 (ogniwo A, przy pochyłej ścianie frontu) trzeba **zagiąć o 90° w prawo 2 mm nad płytką**, w strefę zatrzasków.
- Szereg: BAT− (A, prawy) → A → lewy styk podwójny → B → prawy styk podwójny → C → BAT+ (C, lewy). Który z 5213 / 5214 trafia na który koniec, zależy od strony sprężyny. Przy lewym końcu sprężyna ma być od strony tyłu (ogniwo B), przy prawym też (ogniwo C). Sprawdzić na rysunku katalogowym przed zamówieniem.
- **Do sprawdzenia na prawdziwych stykach:** wysokość środka styku nad krawędzią płytki (5,5 i 7,0 mm odczytane z rysunków), położenie zaczepów płytki podwójnej i grubość blachy. Wszystko jest parametrami na początku skryptu (`SGL_*`, `DUAL_*`, `CW_*`, `L_CONT`).

## 4. Kapsle przycisków (B3F-4055)

- Trzpień B3F-4055 (karta Omron): kwadrat **3,8 × 3,8 mm**, od 5,5 do 7,3 mm nad płytką. Pod nim okrągła część Ø7,1 od 4,3 mm.
- Gniazdo w kapslu ma 4,0 × 4,0 mm (luz 0,1 mm na stronę). Na każdej ściance jest **żebro dociskowe** 0,6 mm. Odstęp między przeciwległymi żebrami wynosi **3,5 mm**, tyle samo co w oryginalnych nasadkach Omron B32 do przycisków 12 × 12 ([karta B32](https://datasheet.octopart.com/B32-1300-Omron-datasheet-5341631.pdf)). Na wejściu jest fazka 0,4 mm. Żebra trzymają kapsel na wcisk, bez luzu (render 18). Kolizja żeber z trzpieniem (ok. 0,4 mm³ na kapsel) jest zamierzona.
- Spód kapsla jest 0,3 mm nad okrągłą częścią, czyli więcej niż skok przycisku (0,25 mm). Trzpień wchodzi w gniazdo na 1,5 mm.
- **Rowek „na klik”:** na rysunku B3F-4055 ani na rysunku B32 nie ma rowka z wymiarami. Nasadki B32 to według dystrybutorów nasadki wsuwane (szczęki dociskowe i trzpień Ø1,8 w otwór na czubku). Jeśli rowek jest na trzpieniu, po zmierzeniu można dodać na dole żeber zgrubienie, które w niego wskoczy. Trzpienia w otwór nie dodawałem, bo nie dałoby się go wydrukować spodem do stołu.
- Kapsle drukować kołnierzem do stołu, żebra stoją wtedy pionowo.

## 5. Płytka przycisków na płytce uniwersalnej

**Szablon do druku 1:1, schemat połączeń i instrukcja montażu: [`docs/plytka-przyciskow/`](../plytka-przyciskow/README.md).** Projektu PCB płytki przycisków nie ma i nie jest potrzebny: dane są dobrane tak, żeby wystarczyła **jednostronna płytka uniwersalna 1,6 mm z rastrem 2,54 mm** (karta B3F podaje montaż na płytce jednostronnej 1,6 mm). Dane: `docs/pcb-klin3/pcb-layout.json`, klucz `button_board` (generuje je `tools/pcb/export.py`).

Wymiary od lewego dolnego narożnika płytki; x wzdłuż obudowy (lewy koniec przy głośniku), y w głąb (y = 0 od strony frontu), przyciski od góry:

| Element | Położenie (x; y) mm | Na rastrze |
| --- | --- | --- |
| zarys | 50 × 16 | przyciąć z dokładnością ok. ±0,3 |
| przycisk „−” (S3) | 7,22; 8,00 | środki co **17,78 mm = 7 oczek** |
| przycisk „run” (S1) | 25,00; 8,00 | |
| przycisk „+” (S2) | 42,78; 8,00 | |
| otwór M2 Ø2,2 | 16,11; 2,92 | na oczku, rozwiercić do 2,2 |
| otwór M2 Ø2,2 | 33,89; 13,08 | na oczku, rozwiercić do 2,2 |

- **Nóżki B3F-4055** (rozstaw 12,5 × 5,0 mm z karty) wchodzą w prostokąt 5 × 2 oczka (12,7 × 5,08 mm), dłuższym bokiem wzdłuż płytki. Nóżki są sprężyste, wchodzą z lekkim dociskiem. Środek przycisku leży wtedy w połowie oczka w osi x i na oczku w osi y. Dlatego rozstaw przycisków to 17,78 mm, a nie 18 mm jak wcześniej: przy 18 mm ostatni przycisk zszedłby o 0,44 mm z rastra, a kapsel ma w otworze pokrywy tylko 0,3 mm luzu.
- **Kołki ustalające B3F** (dwa Ø1,8 mm, co 9 mm, na osi przycisku w poprzek płytki, czyli w y = 3,5 i 12,5) nie trafiają w oczka. Dwie możliwości: nawiercić Ø1,8…2,0 mm (najprościej przyłożyć przycisk nóżkami w oczka i zaznaczyć kołki) albo ściąć kołki nożykiem. Wtedy przycisk trzymają same nóżki, co przy 4 lutach w zupełności wystarczy.
- **Otwory M2** leżą na oczkach (w połowie między przyciskami, 2 oczka od osi przycisków, po przekątnej). Przy osi przycisków słupki pokrywy wchodziłyby w kołnierz kapsla „run”. Słupki w pokrywie mają otwór Ø1,7 mm na głębokość 5,5 mm pod wkręt samogwintujący M2 × 6 (łeb od strony lutowania).
- **Połączenia** (luty od spodu, wystające końcówki do 1,9 mm): nóżki 1–2 i 3–4 każdego przycisku są połączone wewnątrz. Cztery przewody do pól KEY płytki głównej: KEY1 = GND (wspólny S1 i S2), KEY2 = PB3 (S1 „run”), KEY3 = PB4 (S2 „+” i S3 „−”), KEY4 = druga strona S3 (do R6 na płytce głównej). Mostki zrobić drutem od strony lutowania.
- Pliki klina 3 i 3.1 zostają z rozstawem 18 mm. Ich skrypty czytają te same dane, więc po ponownym przebudowaniu dostaną nowy rozstaw, ale słupki płytki przycisków stawiają na osi przycisków. Wymagałyby wtedy tej samej poprawki co tutaj (słupki w położeniu otworów, a nie na osi).

## Kontrola

- Wszystkie części są bryłami zamkniętymi (0 krawędzi nierozmaitościowych).
- [`check_collisions_wedge.py`](../../tools/enclosure/check_collisions_wedge.py): **0 kolizji w 104 parach**, kontrola dodatnia testu 1,00 mm³. Pierwsze podejście miało trzy kolizje: ścianka gniazd i górny róg płytki podwójnej przy ogniwie A wchodziły w pochyłą ścianę frontu, a zaczepy płytek podwójnych wchodziły w dno. Ściankę przycina teraz wnętrze z luzem 0,5 mm, solver trzyma róg płytki 0,5 mm od ściany, a szczeliny są wycięte także w dnie.
- [`check_assembly_wedge4.py`](../../tools/enclosure/check_assembly_wedge4.py) na wariancie bez zaczepów: **zdejmowanie pokrywy pionowo w górę** (0,5…48 mm) razem z elektroniką: 0 kolizji. **Wyjmowanie ogniw pionowo w górę**, każde osobno przy pozostałych na miejscu: 0 kolizji.
- Blokada pokrywy (wariant z zaczepami): 5 ruchów, wszystkie zablokowane (tabela w punkcie 2).
- Nie sprawdzałem wytrzymałości, wydruku, odginania nóg ani montażu na fizycznych częściach.

## Druk

- **Pokrywa:** leżąc na tylnej ściance, jak w klinie 3.1. Nogi zatrzasków biegną wtedy pod kątem 30° do stołu (warstwy prawie wzdłuż nogi) i potrzebują podpór, tak jak nosek frontu. Na stojąco (wierzchołek do góry) nogi byłyby pionowe i nie potrzebowałyby podpór. Wtedy jednak zginałyby się w poprzek warstw i łatwo pękały, a podpór wymagałyby słupki płytek i listewki modułu. Materiał: PETG.
- **Korpus:** podstawą do stołu. Półki zatrzasków mają nawis 0,8 mm. Szczeliny gniazd (0,8 mm) i otwory w spodzie są pionowe.

## Do uzupełnienia i ryzyka

1. **Zatrzaski nieprzetestowane.** Warto wydrukować sam narożnik: kawałek korpusu z półką i kawałek pokrywy z nogą. Sprawdzić siłę zamykania, zwalnianie spinaczem i to, czy róg zostaje na półce. Parametry: `LATCH_Y`, `LATCH_T`, `BARB`, `SHELF_T`, `SHELF_GRIP`, `RIM_CLR`.
2. **Styki:** wymiary z rysunków katalogowych, bez pomiaru (punkt 3). Blaszkę 5204 trzeba zagiąć.
3. **Przewody:** BAT+ (lewy koniec, przy głośniku) i BAT− (prawy, strefa zatrzasków) idą do płytki na pokrywie. Do tego głośnik i 4 + 4 przewody wyświetlacza i przycisków w pokrywie. Złącza JST na baterię i głośnik nadal są wskazane (jak w klinie 3).
4. **Wyświetlacz:** przewody wlutowane w moduł zamiast wtyczek. Moduł wymienia się wtedy z lutownicą.
5. **Kapsle:** rowek do zmierzenia (punkt 4).
6. **RA 16** (punkt 1): −3 mm wysokości, do decyzji.
7. **Płytka przycisków** na płytce uniwersalnej (punkt 5): sprawdzić, czy nóżki B3F wchodzą w raster 12,7 × 5,08 bez wyginania.
8. Pozostałe jak w klinie 3 i 3.1: wysokości elementów płytki głównej, wymiary modułu OLED.
