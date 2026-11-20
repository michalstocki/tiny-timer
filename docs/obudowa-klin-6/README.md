# Obudowa minutnika: wariant „klin 6”

Kolejna iteracja po [klinie 5](../obudowa-klin-5/README.md). Zmienia się kształt: **narożniki G2** (ciągła krzywizna) i **większe promienie** przy podstawie i na krawędziach trójkątnych boków. Najpierw powstał prototyp samej bryły i trzy warianty do porównania (etap 1, niżej). Wybrany został **wariant C** (20.11.2026). Etap 2 to pełny model do druku na tej bryle. Wnętrze, styki, płytki, zatrzaski, klapka i kapsle działają jak w klinie 5.

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --python tools/enclosure/build_wedge6.py                  # -> docs/obudowa-klin-6/
TT_NOHOOK=1 /Applications/Blender.app/Contents/MacOS/Blender --background --python tools/enclosure/build_wedge6.py      # wariant bez zaczepów (kontrola zdejmowania)
/Applications/Blender.app/Contents/MacOS/Blender --background docs/obudowa-klin-6/obudowa-klin-6.blend --python tools/enclosure/check_collisions_wedge.py
/Applications/Blender.app/Contents/MacOS/Blender --background docs/obudowa-klin-6/obudowa-klin-6-bez-zaczepow.blend --python tools/enclosure/check_assembly_wedge6.py
/Applications/Blender.app/Contents/MacOS/Blender --background docs/obudowa-klin-6/obudowa-klin-6.blend --python tools/enclosure/check_assembly_wedge6.py -- blokada
```

Skrypty: [`build_wedge6.py`](../../tools/enclosure/build_wedge6.py) (model, kopia `build_wedge5.py` ze zmianami opisanymi niżej), [`wedge6_geom.py`](../../tools/enclosure/wedge6_geom.py) (bryła C, skóry, układ narożnika; bez bpy), [`check_assembly_wedge6.py`](../../tools/enclosure/check_assembly_wedge6.py) (te same próby co w klinie 5). Układ wnętrza liczy bez zmian `wedge5_solver.py`.

Pliki do druku: `korpus.stl`, `pokrywa.stl`, `klapka.stl`, `kapsle.stl`.

## Etap 2: model do druku

**74,1 × 56,5 × 46,5 mm** (klin 5: 74,1 × 59,7 × 45,0), bok trójkąta 67,0. Bryła C: narożniki przekroju G2 R9 przy podstawie i R15 na wierzchołku (gładkość 0,9), krawędzie boków G2 R9 (gładkość 0,75). Ogniwa, styki, płytka główna, moduł wyświetlacza i głośnik leżą tam, gdzie w klinie 5.

### Bryła i ścianki

- Zewnętrzna powierzchnia i wszystkie powierzchnie odsunięte do środka („skóry”) powstają z pierścieni `wedge6_geom`. Skóra o grubości d to przekrój odsunięty o d, a przy bokach przekrój odsunięty według krzywej zaokrąglenia przesuniętej o d po normalnej.
- **Wnętrze idzie za zaokrągleniem boków.** Przy R9 krawędź boku na głębokości 3 mm (wewnętrzna płaszczyzna boku) jest wcięta o 1,1 mm. Przy wnętrzu jak w klinie 5 ścianka miałaby tam 0,5 mm na froncie. Teraz ma pełne 2,0 / 1,6 mm, a wnętrze przy bokach ma zaokrąglone narożniki (podłoga przy boku wznosi się do z 3,7 na x = 3).
- Zakładki boczne pokrywy (zewnętrzna warstwa 0,9 mm) i wcięcia w bokach korpusu (1,9 mm) są liczone od prawdziwej powierzchni, czyli po zaokrągleniu.
- W narożnikach G2 ścianka wychodzi do ok. 2,25 mm (przekrój odsunięty liczy trójkąt odsunięty z promieniami R − d). Wnętrze jest przez to trochę mniejsze, ale kolizji nie ma.

### Szwy pokrywy

- Szew leży na narożnikach podstawy jak w klinie 5, ale w układzie narożnika G2: punkt powierzchni o danym kącie normalnej, przesunięty po normalnej (`wedge6_geom.ang`), zamiast punktu na łuku R5 wokół środka.
- **Nosek kończy się na kącie 230° (był 238°).** Przy narożniku G2 nosek do 238° sięgałby do y 9,3, a ścianka koszyka ogniw stoi na y 9,15 i blokowałaby zdejmowanie pokrywy. Teraz nosek sięga do y 8,79. Zewnętrzna połowa szwu kończy się jak dotąd na 208°.

### Zatrzaski

- Podłoga w narożniku G2 i przy bokach się wznosi (na y 10, x 3,5 jest na z 4,3), więc **zatrzaski stoją na y 12,5** (było 10,5), a spód nogi to podłoga w najgorszym miejscu strefy + 0,4: **z 3,89** (było 2,4). Zaczep i półka przesuwają się razem z nogą.
- Wolna długość nogi 13,5 mm z przodu, 12,7 z tyłu. Odkształcenie przy zwalnianiu (ugięcie 0,8 mm): 0,80 / 0,90 %.
- Otwór na szpilkę w spodzie sięga lokalnej podłogi.

### Klapka częściowo na zaokrągleniu

- Płaskie dno zaczyna się 15,6 mm od krawędzi podstawy, a klapka (z przylgą) 9,3 mm, więc jej przedni brzeg leży na zaokrągleniu narożnika front/podstawa (render 13, 22).
- **Kołnierz** to zewnętrzna warstwa ścianki o grubości 1,0 mm po normalnej, w obrysie z przylgą, więc klapka jest równo z powierzchnią także na zaokrągleniu. **Czop** wypełnia otwór do 0,5 mm nad podłogą (z 3,25, bo przy froncie podłoga wznosi się do 2,8). Na płaskim dnie to dokładnie klapka klina 5 (kołyska, język, ucho, wymiary).
- Klapka nie wciska się do środka, bo kołnierz opiera się o wewnętrzną warstwę ścianki korpusu (także na zaokrągleniu). Otwiera się jak w klinie 5: przedni brzeg obraca się razem z resztą wokół lewego końca.
- **Ucho z wkrętem** leży w zaokrągleniu prawego boku (spód wznosi się tam od 0,03 do 0,78 mm). Ucho jest przycięte do powierzchni, a łeb wkrętu stoi na najniższym punkcie pod łbem (z 0,03), więc nigdzie nie wystaje. Od strony boku jest schowany do 0,75 mm, a ucho przy samym końcu ma tylko 0,4 mm (render 25).

### Przyciski i wierzchołek

- Wierzchołek jest wyższy o 1,5 mm (46,5). Płytka przycisków idzie w górę razem z nim, a grubość góry (4,4 mm) się nie zmienia.
- Górna powierzchnia kapsli biegnie po prawdziwym przekroju odsuniętym o 0,15 mm, a nie po walcu R13 (render 16).

### Budowanie

- Booleany robi solver **Manifold** (`bpyutil.SOLVER`, w klinie 6 domyślnie; `TT_SOLVER=EXACT` przywraca poprzedni). Solver EXACT psuł styki skór z płaszczyznami cięcia: zostawiał krawędzie zerowej długości. Klin 5 dalej buduje się solverem EXACT.
- Pierścienie skór leżące bliżej niż 0,05 mm płaszczyzny cięcia (szwy boków, zakładki, noski) są pomijane, a prawy wycinak zakładki to lustrzane odbicie lewego. W pierścieniach liczonych od prawego końca szum zmiennoprzecinkowy na granicy rzędu 1e-8 mm psuł booleany.

## Kontrola

- Wszystkie części są bryłami zamkniętymi (0 krawędzi nierozmaitościowych) i każda jest jedną bryłą. Ścianki gniazd i ścianki koszyka stoją na dnie (pasek 0,4 mm nad dnem wypełniony w 100%).
- `check_collisions_wedge.py`: **0 kolizji w 159 parach**, kontrola dodatnia testu 1,00 mm³.
- `check_assembly_wedge6.py` na wariancie bez zaczepów:
  - zdejmowanie pokrywy pionowo w górę z elektroniką: 0 kolizji;
  - klapka zamknięta: 0,03 mm³ z korpusem. To styk kołnierza z przylgą na zakrzywionej powierzchni (obie bryły mają tę samą skórę 1,0 mm), szum booleana, a nie wcisk;
  - otwieranie klapki (obrót i wysunięcie języka): 0 kolizji; klapka w górę 0,3 mm i w lewo 0,4 mm: zablokowana; w dół bez wkrętu: lewy koniec trzyma język;
  - wsuwanie płytek styków od góry: 0 kolizji; każde ogniwo wepchnięte w górę o 0,5 / 1 / 3 mm trafia w strop;
  - wkładanie ogniw od spodu: 0 kolizji.
- `check_assembly_wedge6.py -- blokada` (z zaczepami): w położeniu zamkniętym 0 mm³; w górę, w przód, w tył i podważenie każdej krawędzi o 1°: **wszystkie zablokowane**.
- Nie sprawdzałem wydruku, zatrzasków, wkrętu ani montażu na fizycznych częściach.

## Druk

- **Korpus:** podstawą do stołu, strop koszyka na podporach jak w klinie 5. Nowość: narożniki G2 przy podstawie zaczynają się stycznie do stołu, więc pierwsze warstwy narożnika (do ok. 1 mm wysokości) wiszą prawie poziomo. Zwykle drukuje się to bez podpór z lekko gorszą powierzchnią. Jeśli brzeg się podwija, pomogą podpory tylko od stołu.
- **Klapka:** spodem do stołu. Przedni brzeg na zaokrągleniu unosi się nad stół najwyżej o 0,9 mm na szerokości ok. 6 mm. Zwykle wychodzi bez podpór, przy kłopotach można dodać podpory od stołu pod sam brzeg.
- Pokrywa i kapsle: jak w klinie 5.

## Do sprawdzenia i ryzyka

1. Wszystkie ryzyka klina 5 (grubość blachy styków, wcisk zadziorów, średnica sprężyny, zatrzaski, wkręt w PETG) zostają.
2. **Nosek pokrywy a ścianka koszyka:** luz w poziomie tylko 0,36 mm (nosek do y 8,79, ścianka od 9,15). Zdejmowanie przechodzi na modelu, ale przy wydruku z nadmiarem materiału może trzeć.
3. **Ucho klapki** przy prawym końcu jest cienkie (0,4 mm na samym końcu, 0,6 mm pod łbem jak w klinie 5).
4. Ścianki w narożnikach G2 są do 0,25 mm grubsze niż nominalne (przybliżenie odsunięcia), co nie przeszkadza.

## Etap 1: prototyp bryły

Kolejna iteracja po [klinie 5](../obudowa-klin-5/README.md). Dwie zmiany kształtu:

1. **Narożniki G2** (ciągła krzywizna): krzywizna rośnie od zera, przechodzi w łuk i znów maleje do zera, zamiast skoczyć od zera do 1/R na styku łuku ze ścianą.
2. **Dwa razy większe promienie** przy podstawie (R5 → R10) i na krawędziach trójkątnych boków (R3 → R6).

Zmiana jest duża, dlatego najpierw powstaje sama bryła (bez klapek, zatrzasków, przycisków i wnętrza) do oceny i eksperymentów. Szczegóły z klina 5 przeniosę dopiero na zatwierdzony kształt (etap 2).

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background docs/obudowa-klin-5/obudowa-klin-5.blend --python tools/enclosure/proto_wedge6.py
TT_RA=16 TT_OUT=docs/obudowa-klin-6/prototyp/wariant-B /Applications/Blender.app/Contents/MacOS/Blender --background docs/obudowa-klin-5/obudowa-klin-5.blend --python tools/enclosure/proto_wedge6.py
TT_RB=9 TT_RA=15 TT_RE=9 TT_SM=0.9 TT_SME=0.75 TT_OUT=docs/obudowa-klin-6/prototyp/wariant-C /Applications/Blender.app/Contents/MacOS/Blender --background docs/obudowa-klin-5/obudowa-klin-5.blend --python tools/enclosure/proto_wedge6.py
python3 tools/enclosure/make_klin6_viewer.py
```

Skrypty: [`g2geom.py`](../../tools/enclosure/g2geom.py) (narożniki G2 i pierścienie bryły, bez bpy), [`proto_wedge6.py`](../../tools/enclosure/proto_wedge6.py) (bryła, STL, rendery porównawcze, kontrola wnętrza; parametry `TT_RB`, `TT_RA`, `TT_RE`, `TT_SM`, `TT_SME`, `TT_SIDE`, `TT_LEN`), [`klin6_viewer.html`](../../tools/enclosure/klin6_viewer.html) (przeglądarka z suwakami, ta sama geometria w JS).

### Jak zdefiniowany jest narożnik G2

- **Promień nominalny R** jak w zaokrągleniu „curvature continuous” w CAD: narożnik zaczyna się w tym samym miejscu co łuk R (cofnięcie od wierzchołka R · tan(kąt/2)). Dzięki temu R10 G2 zajmuje na ścianach tyle samo miejsca co R10 kołowy.
- **Gładkość** 0…1 to udział przejść klotoidalnych w kącie skrętu. 0 = zwykły łuk (klin 5), 1 = same przejścia. Przy tym samym R środek narożnika robi się ciaśniejszy (r min) i leży bliżej ostrego wierzchołka.
- Krawędzie boków: przekrój w odległości u od płaszczyzny boku to przekrój podstawowy odsunięty o e(u), a (u, e) leży na narożniku G2 90°. Powierzchnia jest gładka wszędzie, także na styku z płaszczyzną boku.

### Warianty

| | Klin 5 | **A** | **B** | **C (wybrany 20.11.2026)** |
| --- | --- | --- | --- | --- |
| R podstawy / wierzchołka / boków | 5 / 13 / 3, łuki | 10 / 13 / 6, G2 0,5 | 10 / **16** / 6, G2 0,5 | 9 / 15 / 9, G2 0,9 (boki 0,75) |
| r min (podstawa / wierzch. / boki) | 5 / 13 / 3 | 7,4 / 9,7 / 4,2 | 7,4 / 11,9 / 4,2 | 5,4 / 9,0 / 5,5 |
| Wymiary dł × szer × wys | 74,1 × 59,7 × 45,0 | 74,1 × 54,9 × **47,5** | 74,1 × 54,9 × 45,0 | 74,1 × 56,5 × 46,5 |
| Wnętrze klina 5 przy boku 67 | | brak 0,6 mm (styki) | brak 0,6 mm (styki) | **mieści się** |
| Płaska klapka klina 5 | mieści się | brak 8,1 mm | brak 8,1 mm | brak 6,4 mm |
| Ścianka przy krawędzi boku (front / podstawa, tył) | 1,6 / 2,0 | 1,27 / 1,67 | 1,27 / 1,67 | **0,51 / 0,91** |

Wszystkie warianty mają bok 67,0 jak klin 5, żeby porównanie było bezpośrednie. **A** to dosłownie „R×2 i G2”. Przy wierzchołku G2 z tym samym R13 wypycha górę o 2,5 mm. **B** ma większe R wierzchołka (16), dobrane tak, żeby wysokość została 45,0. Klin zwęża się o 4,8 mm, bo większe narożniki podstawy zabierają szerokość.

Pliki w `prototyp/wariant-A` i `prototyp/wariant-B`: `prototyp-klin6.stl` (pełna bryła, np. do wydruku próbnego w ręce), `prototyp-klin6.blend`, `raport.json`, `przekroj-porownanie.svg`, `renders/` (lewa połowa obrazka: klin 5, prawa: klin 6):

- `01` przód iso, `02` bok, `03` spód, `06` zbliżenie narożnika, `07` tył iso;
- `04`, `05` **zebra** (paski odbicia). Przy G1 paski łamią się na styku łuku ze ścianą, przy G2 przechodzą płynnie.

Przeglądarka: `prototyp/przegladarka-klin6.html` (opublikowana jako artefakt): suwaki promieni, gładkości, boku i długości; glina albo zebra, duch klina 5, elementy wnętrza z kolizjami na czerwono, przekrój z grzebieniem krzywizny, przycisk kopiujący parametry.

**C** to parametry wybrane w przeglądarce. Przy R9 i gładkości 0,9 środek narożnika podstawy jest ciaśniejszy (r min 5,4), więc wnętrze klina 5 mieści się bez powiększania boku. Duże R krawędzi boków (9) wcina się na głębokości wewnętrznej płaszczyzny boku (3 mm) o 1,09 mm, więc w etapie 2 wnętrze przy bokach musi iść za zaokrągleniem (pogrubienie od środka w narożnikach przy obu końcach). Na płaszczyźnie boku narożniki podstawy mają promień bliski zera (R podstawy 9 minus wcięcie 9), ale powierzchnia jest styczna do płaszczyzny, a zebra (render 05) przechodzi płynnie.

### Co wynika dla etapu 2 (liczone dla A i B)

Elementy wnętrza klina 5 sprawdzone względem nowej wewnętrznej ścianki (2,0 mm, front 1,6 mm). Wymagany luz każdego elementu to luz z klina 5, nie więcej niż 0,3 mm.

1. **Wnętrze prawie się mieści.** Brakuje miejsca tylko dolnemu przedniemu narożnikowi płytek styków przy ogniwie A (BAT− i płytka podwójna lewa, do 0,64 mm). Ogniwa mieszczą się (0,13 mm zamiast 0,15). Szacunek: **bok 68,3 mm** (+1,3) przy R10.
2. **Płaska klapka klina 5 się nie mieści.** Płaskie dno zaczyna się 17,3 mm od krawędzi (przy R5: 8,7 mm), a klapka z przylgą zaczyna się 9,5 mm od krawędzi. Brakuje 8,1 mm. Długość płaskiego dna zależy tylko od R podstawy, nie od gładkości. Przy płaskiej klapce bok musiałby urosnąć do 83 mm. Możliwości do wyboru w etapie 2:
   - klapka zachodząca na zaokrąglenie (wydrukowana z kawałkiem krzywizny narożnika, przylga dalej na płaskim): kształt bez zmian, klapka trudniejsza;
   - mniejsze R tylko na narożniku front/podstawa (asymetria przekroju);
   - inny układ ogniw albo ich wkładanie z innej strony.
3. **Ścianka przy krawędzi boku** cieńsza o wcięcie zaokrąglenia na głębokości 3 mm (0,33 mm przy R6): front 1,27 mm, podstawa i tył 1,67 mm. Do przyjęcia, ewentualnie pogrubić od środka.
4. **Szwy i zatrzaski** leżą na narożnikach podstawy (szew na kącie normalnej 208°, nogi zatrzasków 10,5 mm od krawędzi). Narożnik G2 R10 jest inny niż łuk R5, więc geometrię szwu i półek trzeba wyznaczyć od nowa.

### Ograniczenia

- Elementy wnętrza leżą tam, gdzie w klinie 5. Przy większym boku przesuwam je razem ze środkiem okręgu wpisanego (każda ścianka odsuwa się o tyle samo). To szacunek rozmiaru, nie nowy układ.
- Odsunięty przekrój to trójkąt odsunięty o d z promieniami R − d przy tej samej gładkości. Dla łuku to dokładne odsunięcie, dla G2 nie: przy d = 2 mm wewnętrzna powierzchnia w środku narożnika leży do 0,38 mm dalej od zewnętrznej niż przy dokładnym odsunięciu (gładkość 0,5), więc ścianka w narożniku wychodzi do 2,4 mm, a wnętrze jest trochę mniejsze. Sprawdzone na wariancie B z dokładnym odsunięciem o 2,0 mm: styk BAT− ma −0,48 mm zamiast −0,63, potrzebny bok 68,4 zamiast 68,3. W etapie 2 wnętrze trzeba liczyć dokładnym odsunięciem. Zewnętrzna powierzchnia jest zdefiniowana właśnie tak (pierścienie z rodziny R − e), więc tam to nie jest błąd, tylko sposób zaokrąglenia krawędzi boków.
- Nie sprawdzałem wydruku.
