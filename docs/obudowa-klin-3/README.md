# Obudowa minutnika: wariant „klin 3” (ciaśniejsze upakowanie)

Kolejna iteracja leżącego graniastosłupa o podstawie zaokrąglonego trójkąta równobocznego ([klin 1](../obudowa-klin/README.md), [klin 2](../obudowa-klin-2/README.md)). Cel: jak najmniejsze wymiary. Wariant powstał ze szkicu przekroju od właściciela, który potwierdził układ opisany niżej. Wcześniejsze warianty zostają bez zmian.

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --python tools/enclosure/build_wedge3.py   # -> docs/obudowa-klin-3/
/Applications/Blender.app/Contents/MacOS/Blender --background docs/obudowa-klin-3/obudowa-klin-3.blend \
    --python tools/enclosure/check_collisions_wedge.py                                                   # kolizje części
```

Dane wejściowe: płytka [`docs/pcb-klin3/`](../pcb-klin3/README.md) (40 × 24 mm, tylko elektronika). Rozmiar trójkąta liczy [`wedge3_solver.py`](../../tools/enclosure/wedge3_solver.py) (najmniejszy bok, w którym mieści się cała zawartość), model buduje [`build_wedge3.py`](../../tools/enclosure/build_wedge3.py).

## Wymiary

**69,4 × 67,0 × 49,4 mm** (dł. × szer. × wys.; szerokość razem z łapką zatrzasku 1,6 mm, sama bryła 64,7 mm). Bok trójkąta **72,0 mm**.

| | klin 2 | klin 3 |
| --- | --- | --- |
| Bok trójkąta | 77,5 mm | **72,0 mm** |
| Wymiary (dł. × szer. × wys.) | 77,4 × 70,2 × 54,1 | **69,4 × 67,0 × 49,4** |
| Objętość prostopadłościanu opisanego | 294 cm³ | **230 cm³** (−22%) |
| Płytka główna | 48 × 36 mm (z OLED) | **40 × 24 mm** |

Dłuższy wymiar skrócił się z 77,4 do 69,4 mm, bo zniknęła strefa wkrętów (8 mm) i klapka ogniw w prawym boku. Przekrój skurczył się o 14% (bok 72,0 zamiast 77,5 mm).

## Jak zrozumiałem szkic i co z niego wynika

1. **Wyświetlacz sam na froncie.** Moduł OLED (38 × 12 × 4 mm) jest wklejony szkłem do wewnętrznej strony panelu (klej na gorąco), ustalają go sześć listewek 1 mm (rendery 11, 14). Na jego listwie pinów siedzą cztery żeńskie wtyczki z przewodami do pól DISP na płytce głównej (na szkicu: „grzebień” przy froncie). Moduł jest wyśrodkowany w X, więc wtyczki są przy jego lewym końcu (x ≈ 17 mm).
2. **Płytka główna na tylnej ściance pokrywy**, elementami do wnętrza, w dolnej połowie tyłu (na szkicu: prostokąt po prawej). Leży równolegle do ścianki na dwóch słupkach (M2,5, odstęp 2,5 mm na lut i końcówki nóżek). U1 w podstawce jest dostępny od wewnątrz po zdjęciu pokrywy.
3. **Ogniwa 2 + 1 w korpusie, dostęp tylko od góry** po zdjęciu pokrywy: dwa w korytkach na podłodze, trzecie w dolince między nimi. Nie ma klapki, otworu w boku ani przegród między ogniwami. Styki jak w klinie 2 (płytki w kształcie „pastylek”, sprężyny z lewej).
4. **Zatrzask zamiast wkrętów**: z przodu zakładka, z tyłu elastyczny język z zaczepem, odblokowywany palcem (łapka na zewnątrz, rendery 08, 15). Boki są teraz gładkie.

## Układ

- **Oś X:** lewy bok 3 mm, głośnik (Ø26,5, strefa 11,2 mm), przegroda 1,2 mm, ogniwa 51 mm, prawy bok 3 mm. Głośnik jak wcześniej: pierścień oporowy i otwory dźwiękowe w trójkątnym boku po lewej.
- **Podział:** pokrywa to front (od `S_F` = 26,5 mm po skosie), wierzchołek z przyciskami i tył aż do `S_B` = 56,5 mm od ostrego wierzchołka. Niesie obie płytki, moduł i kapsle. Siedzi między bokami (szczeliny 0,25 mm) i schodzi **pionowo w górę** (kontrola poniżej). Korpus to podstawa z ogniwami, boki i dolne części frontu i tyłu.
- **Przegroda** za głośnikiem (1,2 mm, do cięciwy podziału) zamyka lewy koniec ogniw. Prawy koniec zamyka prawy bok.
- **Ogniwa:** dolne w korytkach r = 5,5 mm (żeberko 1,0 mm, brzegi 1,5 mm poniżej osi, żeby ogniwo dało się wyjąć w bok), górne leży w dolince z luzem 0,5 mm. Cała paczka jest przesunięta ku przodowi, a wolny róg z tyłu u dołu zostaje na przewody.
- **Zakładka frontu:** cienka warga pokrywy (1,0 mm, 6 mm) leży na zewnątrz korpusu we wpuście, a ścianka korpusu jest tam pogrubiona od wnętrza o 1 mm (render 18). Warga trzyma przód pokrywy i zlicowana jest z powierzchnią.
- **Zatrzask tyłu** (render 15): język 14 × 10 × 1,2 mm wychodzi z pokrywy w dół po zewnątrz korpusu (wpust zlicowany z powierzchnią), na końcu ma zaczep 0,9 mm z rampą od dołu i płaską ścianką od góry. Zaczep wchodzi w rowek w korpusie, a tylna ścianka jest tam pogrubiona od wnętrza o 1,4 mm. **Odblokowanie:** palcem podważyć łapkę na końcu języka na zewnątrz (1,6 mm wystaje poza obrys), potem pokrywa idzie w górę. Zamknięcie: dociśnięcie pokrywy pionowo, rampa odgina język i zaczep zaskakuje.
- **Przyciski, kapsle, płytka przycisków:** jak w klinie 2, ale płytka przycisków jest **50 × 16 mm** (przyciski w x = 7, 25, 43 mm, otwory M2 w x = 15 i 35), bo tyle mieści się między bokami.

## Co ogranicza rozmiar (orientacyjnie)

Solver z siatką 1 mm, najmniejszy bok dla podzbiorów zawartości (przed dodaniem warunków zakładki i języka):

| Zawartość | Bok |
| --- | --- |
| wszystko | 72,0 |
| bez ogniw | 65,0 |
| bez płytki głównej | 58,0 |
| bez wyświetlacza | 65,0 |
| tylko płytka główna + przyciski | 65,0 |
| tylko ogniwa + płytka główna | 58,0 |
| tylko wyświetlacz + przyciski | 54,0 |

Czyli ani ogniwa, ani płytka sama nie wymuszają 72 mm: wymusza je **upakowanie wszystkich czterech elementów w jednym przekroju**. Co jeszcze da się zyskać (ten sam solver, pełne ograniczenia):

| Zmiana | Bok |
| --- | --- |
| model bazowy | 72,0 |
| wtyczki proste zamiast kątowych (wysokość 16,5 zamiast 11 mm) | 72,0 (mieści się tak samo) |
| przewody wlutowane w moduł bez wtyczek (5 mm) | 70,5 |
| promień wierzchołka RA 10 zamiast 13 mm | 69,5 |
| masa pod wierzchołkiem T_TOP 3,4 zamiast 4,4 mm | 71,5 |

Najwięcej daje mniejszy promień wierzchołka (przyciski „−” i „+” są wtedy mniej wypukłe), potem rezygnacja z wtyczek.

## Kontrola

- Wszystkie części są bryłami zamkniętymi (0 krawędzi nierozmaitościowych).
- [`check_collisions_wedge.py`](../../tools/enclosure/check_collisions_wedge.py): **0 kolizji we wszystkich 106 parach** (korpus, pokrywa i kapsle względem płytek, modułu, wtyczek, ogniw, styków i głośnika), kontrola dodatnia testu 1,00 mm³.
- [`check_assembly_wedge3.py`](../../tools/enclosure/check_assembly_wedge3.py): **zdejmowanie pokrywy pionowo w górę** (0,5…48 mm) razem z elektroniką: 0 kolizji z korpusem, ogniwami, stykami i głośnikiem (liczone na wariancie bez zaczepu, bo zaczep ma wchodzić w rowek). **Wkładanie ogniw** po kolei 1, 2, 3 wzdłuż frontu w górę: 0 kolizji. Pierwsze podejście miało kolizje z brzegami korytek (brzegi były na wysokości osi) i z zakładką frontu (luz 0,03 mm), poprawione (brzegi niżej, luz 0,25 mm).
- Nie sprawdzałem wytrzymałości, wydruku ani montażu na fizycznych częściach.

## Do uzupełnienia i ryzyka

1. **Zatrzask nieprzetestowany.** Język 1,2 × 14 × 10 mm przy ugięciu ok. 0,9 mm daje odkształcenie ok. 1,6%: PETG powinien to znieść, PLA jest na granicy. Warto wydrukować wersję próbną samego tyłu pokrywy. Jeśli język okaże się za miękki lub za sztywny, zmienia się `LIP_B`, `T_LIP_B` i `HOOK` w skrypcie.
2. **Przód trzyma tylko warga i zatrzask z tyłu.** Brak oddzielnego zabezpieczenia przed podważeniem przedniej krawędzi.
3. **Wtyczki wyświetlacza.** Przyjąłem 4 żeńskie obudowy 2,54 mm o wysokości 11 mm nad tylną ścianką modułu (kątowe, przewód wychodzi bokiem). Proste (16,5 mm) też się mieszczą, ale wtedy przewody trzeba poprowadzić z dużym zapasem. Wymiary do sprawdzenia na własnych przewodach. Przewodów nie modelowałem.
4. **Przewody do pokrywy.** Z płytką na pokrywie idą do korpusu przewody baterii (2) i głośnika (2), a w środku także 4 przewody wyświetlacza i 4 przycisków. Dla serwisowania warto dać złącza (np. JST 2-pin) na baterię i głośnik, żeby pokrywę można było odłożyć całą.
5. **Górne ogniwo** leży w dolince bez osobnego zamocowania (trzymają je dolne ogniwa i styki na końcach). Po zdjęciu pokrywy może się przetoczyć. Jeśli to przeszkadza, można dołożyć żebro od pokrywy dociskające ogniwo.
6. **Płytka przycisków 50 × 16 mm** różni się od 52 × 16 mm z `docs/pcb-klin/`. To dane tego wariantu, osobnego PCB nie rysowałem.
7. Przewody ogniw (bateria +/−) prowadzą po wolnym rogu z tyłu u dołu. Nie modelowałem ich ani opaski odciążającej.
8. Kolejność wkładania ogniw, wymiary styków Keystone i pozostałe punkty jak w klinach 1 i 2.
