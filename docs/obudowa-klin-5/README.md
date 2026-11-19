# Obudowa minutnika: wariant „klin 5”

Kolejna iteracja po [klinie 4](../obudowa-klin-4/README.md). Trzy zmiany: **gniazda pod prawdziwe styki** (zmierzone na częściach, zamiast wymiarów z katalogu Keystone), **klapka w dnie na wkręt** (ogniwa wymienia się od spodu, bez otwierania obudowy) i **zamknięty koszyk**: strop i ścianki boczne nad ogniwami, żeby przy otwartej klapce ogniwa nie dało się wepchnąć do wnętrza obudowy. Klin 4 zostaje bez zmian. Reszta (zatrzaski pokrywy, szwy, kapsle, płytka przycisków, płytka główna) jest taka jak w klinie 4.

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --python tools/enclosure/build_wedge5.py                 # -> docs/obudowa-klin-5/
TT_NOHOOK=1 /Applications/Blender.app/Contents/MacOS/Blender --background --python tools/enclosure/build_wedge5.py     # wariant bez zaczepów (kontrola zdejmowania)
/Applications/Blender.app/Contents/MacOS/Blender --background docs/obudowa-klin-5/obudowa-klin-5.blend --python tools/enclosure/check_collisions_wedge.py
/Applications/Blender.app/Contents/MacOS/Blender --background docs/obudowa-klin-5/obudowa-klin-5-bez-zaczepow.blend --python tools/enclosure/check_assembly_wedge5.py
```

Skrypty: [`build_wedge5.py`](../../tools/enclosure/build_wedge5.py) (model), [`wedge5_solver.py`](../../tools/enclosure/wedge5_solver.py) (przekrój), [`check_assembly_wedge5.py`](../../tools/enclosure/check_assembly_wedge5.py) (zdejmowanie pokrywy, klapka, wsuwanie płytek styków, strop, wkładanie ogniw).

Pliki do druku: `korpus.stl`, `pokrywa.stl`, `klapka.stl`, `kapsle.stl`.

## Wymiary

**74,1 × 59,7 × 45,0 mm** (dł. × szer. × wys.), bok trójkąta **67,0 mm**. Klin 4 miał 74,2 × 60,2 × 45,5 mm. Obudowa zmalała o 0,5 mm, bo styki podwójne mają mniejszy rozstaw (ogniwa leżą co 10,8 zamiast 11,5 mm), a płytki są niższe (oś ogniw na 7,4 zamiast 7,8 mm).

Teraz przekrój wyznacza klapka. Otwór z przylgą musi leżeć na płaskim dnie, przed zaokrągleniem narożnika (R5, czyli od 8,66 mm od krawędzi podstawy). Dlatego oś ogniwa przy froncie jest 15,7 mm od krawędzi (warunek: co najmniej 15,46 mm). Bez ogniw bok wynosiłby 65,0 mm.

## 1. Styki (zmierzone)

Wymiary ze szkicu z pomiarami (19.11.2026):

| Styk | Płytka | Styki na płytce | Blaszka lutownicza | Gdzie |
| --- | --- | --- | --- | --- |
| pojedynczy, sprężyna (−) | 9,9 × 9,1 | sprężyna na środku | 2 × 7, na środku górnej krawędzi | prawy koniec, ogniwo A (przy froncie): **BAT−** |
| pojedynczy, przycisk (+) | 9,9 × 9,1 | przycisk na środku | 2 × 7, na środku | lewy koniec, ogniwo C (przy tyle): **BAT+** |
| podwójny z blaszką | 20,1 × 9,1 | przycisk i sprężyna, **10,3 mm** oś-oś, na środku wysokości | 3 × 6, na środku (nieużywana) | lewy koniec: przycisk A, sprężyna B |
| podwójny bez blaszki | 20,1 × 9,1 | sprężyna i przycisk, 10,3 mm | brak | prawy koniec: przycisk B, sprężyna C |

- Przycisk (+): Ø6, 1,5 mm razem z blachą. Sprężyna: 8 mm swobodna, 3 mm najbardziej ściśnięta, wokół 1 mm wolnego miejsca. Średnicy sprężyny nie było w pomiarach: z proporcji na zdjęciu wychodzi ok. Ø6.
- **Ogniwa co 10,8 mm** (Ø10,5 największego AAA + 0,3). Styk podwójny leży na środku między dwoma ogniwami, więc każdy jego styk jest 0,25 mm poza osią ogniwa. Przy przycisku Ø6 i sprężynie Ø6 nie ma to znaczenia.
- **Odległość płytek: 49,6 mm** (od strony ogniw): ogniwo 44,5 + przycisk 1,1 nad blachą + sprężyna 4,0. Przy najdłuższym ogniwie (44,5) sprężyna ma 1 mm zapasu do pełnego ściśnięcia. Ogniwa krótsze, nawet 41 mm, są jeszcze dociskane.
- Szereg: BAT− (sprężyna A, prawy koniec) → A → lewa płytka podwójna (przycisk A, sprężyna B) → B → prawa płytka podwójna (przycisk B, sprężyna C) → C → przycisk C (lewy koniec) = BAT+. Płytka podwójna z blaszką ma blaszkę do góry, więc tylko przy lewym końcu przycisk wypada od strony frontu. Płytka bez blaszki idzie na prawy koniec. Można ją obrócić o 180°, bo nic nie wyznacza jej góry.
- **Blaszek nie trzeba zaginać.** Blaszka BAT− przy pochyłej ścianie frontu stoi prosto w górę i mieści się (w klinie 4 była zaginana). Przewody lutuje się do otworów w blaszkach od środka, więc otwieranie klapki ich nie rusza.

### Gniazdo

- Ścianka 2,8 mm na każdym końcu, wysoka do z = 13,7 (tyle co strop koszyka): tył 1,0 mm, **szczelina 0,9 mm**, wargi 0,9 mm. Wargi zachodzą 0,8 mm na boczne brzegi płytki (render 11, 19). Dolnej wargi nie ma: okno między wargami sięga dna szczeliny, żeby sprężyna miała dookoła 1 mm luzu. Zapas w oknie wynosi tylko 0,10 mm, więc większa sprężyna się nie zmieści.
- Płytki wsuwa się **od góry, od środka korpusu, raz przy montażu** (przed założeniem pokrywy). Spodem stoją na dnie szczeliny. Szczeliny są otwarte od góry, a nad sprężynami w stropie są wycięcia, więc strop nie przeszkadza (punkt 3).
- Blaszki lutownicze wystają 4…5 mm ponad ścianki gniazd, z otworem na przewód przy końcu. Lutuje się od góry, przy zdjętej pokrywie.
- **Trzymanie:** przy otwartej klapce i obudowie odwróconej do góry dnem płytki mogłyby wypaść ze szczelin do środka. Trzymają je zadziory na bocznych krawędziach (1 mm szerokości, 1,0…1,3 mm razem z blachą) wbite w szczelinę 0,9 mm. Wcisk wynosi od 0,1 do 0,4 mm, niezależnie od tego, w którą stronę zadziory są odgięte. Dochodzą jeszcze przylutowane przewody.

## 2. Klapka

Renderowana na szaroniebiesko (render 21–25), drukuje się ją z tego samego materiału co korpus.

- **Otwór** w dnie między końcami warg obu ścianek gniazd (x 17,0…63,8) i w poprzek trzech ogniw (5,25 + 0,3 luzu od osi skrajnych ogniw): 46,8 × 32,7 mm. Z przylgą klapka ma 48,8 × 34,3 mm i leży równo ze spodem (render 22). Szczelina dookoła wynosi 0,15 mm.
- **Przylga:** od spodu otwór jest większy o 1,0 mm na końcach i 0,8 mm na bokach, do wysokości 1,0 mm. Kołnierz klapki opiera się o korpus, więc klapki nie da się wcisnąć do środka (sprawdzone: ruch o 0,3 mm w górę jest zablokowany).
- **Kołyska:** od środka klapka ma trzy korytka r 5,4 (do 3 mm pod osią ogniw). Ogniwa w nich leżą, a żeberka między nimi trzymają je na boki. Pod ogniwem klapka ma 2,0 mm.
- **Lewy koniec: język** 14 × 2 × 0,8 mm w kieszeni pod lewą ścianką gniazd (render 24). Język leży nad dnem korpusu, więc lewego końca nie da się opuścić. Kieszeń ma 2,3 mm wysokości, żeby klapka mogła się obrócić. Dno szczelin jest 0,55 mm nad kieszenią.
- **Prawy koniec: ucho z wkrętem** (render 25). Ucho 7 mm szerokości, 1,4 mm grubości, sięga pod prawą ściankę gniazd. **Wkręt M2 × 6 z łbem stożkowym, samogwintujący do tworzyw** (ten sam rozmiar co przy płytce przycisków): w uchu otwór Ø2,4 z pogłębieniem 90° pod łeb Ø4, w korpusie tuleja w strefie zatrzasków z otworem pilotowym Ø1,7 do 7,2 mm. Wkręt wchodzi w korpus na ok. 4,6 mm.
- **Podważanie:** obok ucha jest wnęka 1,6 × 6 × 0,8 mm na paznokieć albo śrubokręt.
- **Wymiana ogniw:** obudowa do góry dnem, wykręcić wkręt, unieść prawy koniec klapki i wysunąć język w prawo. Ogniwo wkłada się ujemnym końcem do sprężyny, dociska ją i opuszcza drugi koniec. Przy zamykaniu język wsunąć w kieszeń, opuścić klapkę i wkręcić wkręt.

## 3. Strop koszyka

Koszyk jest zamknięty z pięciu stron: od dołu klapka, na końcach ścianki gniazd, wzdłuż boków ścianki 1 mm na krawędziach otworu klapki, od góry strop (render 26, 27, 10). Ogniwo wepchnięte przy otwartej klapce opiera się o strop po 0,25 mm (sprawdzone dla każdego ogniwa: przesunięcie w górę o 0,5 mm daje kolizję z korpusem).

- **Łuki zamiast płaskiej płyty.** Nad ogniwami jest mało miejsca: od góry ogniwa (z = 12,65) do najniższych elementów pokrywy zostaje 1,0…2,3 mm. Najniżej są listewki modułu wyświetlacza nad ogniwem A (od 13,7) i elementy płytki głównej nad ogniwem C (14,1). Płaska płyta 0,8 mm miałaby górę na z = 13,7 na całej szerokości. Łuk ma tę wysokość tylko na grzbiecie, nad osią ogniwa. Wnętrze łuku ma r 5,5 (luz 0,25 do ogniwa Ø10,5), zewnętrze r 6,3. Najmniejszy odstęp w pionie od części pokrywy wynosi 0,32 mm (listewka modułu wyświetlacza nad ogniwem A, zmierzone na modelu).
- **Przegrody** między ogniwami schodzą do 3 mm nad osią i są tam ścięte płasko (1,5 mm szerokości).
- **Żebra** 1,6 mm na przegrodach i nad środkowym ogniwem, do z = 17. W środkowej strefie wolne miejsce sięga 19…30 mm. Żebra usztywniają strop na rozpiętości 47 mm między ściankami gniazd.
- **Ścianki boczne** idą od dna do spodu stropu (z = 10,45). Wyżej się nie da, bo przy tyle nad ścianką jest dioda D1 płytki głównej (spód 10,84).
- **Wycięcia na sprężyny** 7 × 8,5 mm w stropie, przy trzech sprężynach. Wsuwana płytka ma sprężynę rozprężoną (8 mm), która przechodzi przez strop. Wycięcie jest węższe od ogniwa (7 wobec 10,5 mm), więc ogniwo przez nie nie przejdzie. Środkowe żebro kończy się przed wycięciem przy lewym końcu.

## Kontrola

- Wszystkie części są bryłami zamkniętymi (0 krawędzi nierozmaitościowych), każda jest jedną bryłą.
- **Styk ze dnem:** pasek 0,4 mm tuż nad dnem pod każdą ścianką gniazd i pod obiema ściankami bocznymi koszyka jest wypełniony w 100%. Skrypt przerywa budowanie, jeśli wypełnienie spadnie poniżej 98%. W pierwszej wersji stropu ścianki wisiały 0,5 mm nad dnem: przycinałem je do wnętrza odsuniętego o 0,5 mm od ścian pokrywy, a ten obrys był odsunięty także od podłogi. Liczba brył tego nie wykazała, bo ścianki łączyły się z korpusem przez tuleję wkrętu i strop.
- [`check_collisions_wedge.py`](../../tools/enclosure/check_collisions_wedge.py): **0 kolizji w 159 parach** (z klapką i płytkami styków z blaszkami). Kontrola dodatnia testu: 1,00 mm³.
- [`check_assembly_wedge5.py`](../../tools/enclosure/check_assembly_wedge5.py) na wariancie bez zaczepów:
  - zdejmowanie pokrywy pionowo w górę (0,5…48 mm) z elektroniką: 0 kolizji (z klapką, ogniwami, stykami);
  - klapka zamknięta: 0 mm³ z korpusem; **otwieranie** (obrót wokół dolnej krawędzi lewego końca kołnierza, 1…30°) i wysunięcie języka w prawo: 0 kolizji;
  - klapka w górę o 0,3 mm i w lewo o 0,4 mm: zablokowane; w dół bez wkrętu: lewy koniec trzyma język;
  - **wsuwanie płytek styków od góry** (pokrywa zdjęta, ogniwa wyjęte): każda płytka z przyciskami i sprężynami rozprężonymi do 8 mm przesuwana w górę do 30 mm: 0 kolizji z korpusem;
  - **strop:** każde ogniwo przesunięte w górę o 0,5 / 1 / 3 mm przy zdjętej klapce trafia w korpus;
  - **wkładanie ogniw od spodu**, każde osobno przy pozostałych na miejscu: ogniwo przesunięte o 0,8 mm w stronę sprężyny i opuszczane pionowo: 0 kolizji z korpusem, stykami i ogniwami.
- Nie sprawdzałem wydruku, wcisku zadziorów, wkrętu ani montażu na fizycznych częściach.

## Druk

- **Korpus:** podstawą do stołu. **Strop koszyka wymaga podpór**: spód łuków i płaskie spody przegród wiszą na wysokości 10…13 mm. Podpory stoją na stole w otworze klapki i wyjmuje się je przez ten otwór (warto włączyć warstwę styku podpór, żeby spód łuków był gładki dla ogniw). Półka przylgi (nawis 0,8…1,0 mm dookoła otworu), sufit kieszeni języka (most 2,3 mm) i sufit wnęki ucha (most 7 mm) drukują się bez podpór.
- **Klapka:** spodem do stołu. Język wystaje 1,15 mm poza kołnierz na wysokości 1,0 mm, a pogłębienie pod łeb jest od strony stołu. Oba drukują się bez podpór.
- Pokrywa i kapsle: jak w klinie 4.

## Do sprawdzenia i ryzyka

1. **Grubość blachy styków nie była mierzona.** Model przyjmuje 0,4 mm (`PL_T`). Szczelina 0,9 mm mieści blachę 0,3…0,5. Przy innej grubości trzeba zmienić `PL_T` (zmienia się też wysokość przycisku nad blachą, a więc odległość płytek).
2. **Wcisk zadziorów:** szczelina 0,9 mm przy zadziorach 1,0…1,3 mm. Drukarka zwykle robi szczeliny o 0,1…0,2 mm węższe, więc wcisk może wyjść większy. Warto wydrukować próbkę ścianki z jedną szczeliną (`CW_SLOT`).
3. **Średnica sprężyny** (Ø6) jest odczytana ze zdjęcia. W oknie gniazda zostaje 0,10 mm zapasu przy 1 mm luzu wokół sprężyny.
4. **Klapka:** język i kieszeń sprawdzone tylko na modelu sztywnym. Parametry: `TONGUE_L`, `TONGUE_T`, `POCKET_TOP`, `RAB_X`, `RAB_T`. Jeśli wkręt samogwintujący nie trzyma w PETG, można wtopić tuleję mosiężną M2 (tuleja w korpusie ma 7 × 4,5 mm, więc trzeba by ją poszerzyć).
5. **Strop:** do listewki wyświetlacza zostaje 0,32 mm, do diody D1 0,39 mm. Przy wyższych elementach na płytce głównej albo grubszym module trzeba to sprawdzić (`ROOF_CLR`, `ROOF_T`, `RIB_TOP`).
6. Pozostałe jak w klinie 4: zatrzaski pokrywy nieprzetestowane, przewody wyświetlacza wlutowane w moduł, rowek kapsli, RA 16 do decyzji.
