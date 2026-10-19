# Obudowa minutnika: wariant „klin 2” (ogniwa w układzie trójkąta)

Ta sama bryła i te same przyciski co w [`docs/obudowa-klin/`](../obudowa-klin/README.md) (leżący graniastosłup o podstawie trójkąta równobocznego, przyciski na zaokrąglonym wierzchołku, osobna płytka przycisków, zdejmowana pokrywa z elektroniką), ale **trzy ogniwa AAA leżą w układzie 2 + 1** zamiast w rzędzie, a baterie wkłada się **od prawego boku**, nie od spodu. Budowane tym samym skryptem [`tools/enclosure/build_wedge.py`](../../tools/enclosure/build_wedge.py) z przełącznikiem `TT_BATTERY`, z danych płytki wariantu „klin” ([`docs/pcb-klin/`](../pcb-klin/README.md)). Wariant 1 (rząd) zostaje bez zmian.

```bash
TT_BATTERY=triangle /Applications/Blender.app/Contents/MacOS/Blender --background \
    --python tools/enclosure/build_wedge.py                       # -> docs/obudowa-klin-2/
/Applications/Blender.app/Contents/MacOS/Blender --background docs/obudowa-klin-2/obudowa-klin.blend \
    --python tools/enclosure/check_collisions_wedge.py
```

## Dlaczego trójkąt, a nie płasko na tylnej ściance

Policzyłem oba układy tym samym solverem co przekrój (najmniejszy równoboczny trójkąt, w którym mieści się cała zawartość), dla płytki 48 × 36 mm:

| Układ ogniw | Najmniejszy bok trójkąta |
| --- | --- |
| rząd na podstawie, od spodu (wariant 1) | 80,0 mm |
| płasko na tylnej ściance (kosz równolegle do tyłu) | 80,0 mm (bez zysku) |
| **trójkąt 2 + 1 na podstawie** | **77,5 mm** |
| bez baterii w ogóle (dolna granica) | 77,5 mm |

Układ „płasko na tylnej ściance” nic nie daje, bo kosz 39,4 mm musiałby leżeć na płaskim odcinku tyłu (między zaokrągleniami wierzchołka i podstawy), a ten w trójkącie o boku 80 mm ma tylko ok. 40 mm. Układ trójkątny schodzi do **dolnej granicy**, czyli rozmiaru, jaki wymusza sama elektronika. Dalej baterie już niczego nie ograniczają.

**Ważne:** o rozmiarze (77,5 mm) decyduje teraz nie koszyk, tylko **płytka przycisków przy wierzchołku** w połączeniu z górą płytki głównej. Sama płytka główna zmieściłaby się w trójkącie o boku 68,5 mm. Co to zmienia, z tego samego solvera (bok bez baterii):

| Promień wierzchołka RA | głębokość płytki przycisków 16 mm | 14 mm | 12 mm |
| --- | --- | --- | --- |
| 10 mm | 75,0 | 74,5 | 73,5 |
| 13 mm (jak w modelu) | 77,5 | 77,0 | 76,5 |
| 16 mm | 80,0 | 79,5 | 79,0 |

Czyli dalsze zmniejszenie obudowy wymaga zmiany wierzchołka (mniejszy promień zaokrąglenia) albo układu elementów przy górnej krawędzi płytki głównej, nie ogniw.

## Wymiary i kształt

**77,4 × 70,2 × 54,1 mm** (dł. × szer. × wys.; bok trójkąta 77,5 mm, wysokość z zaokrągleniem 54,1 mm). Wariant 1 ma 77,4 × 72,7 × 56,3 mm, czyli o 2,5 mm niższy i węższy. Zaokrąglenia, przyciski, głośnik, płytka główna i płytka przycisków jak w wariancie 1.

## Układ ogniw

- Trzy kanały r = 5,5 mm wzdłuż X, osie w odległości 12,6 mm (ścianka między kanałami 1,6 mm). Dwa dolne ogniwa leżą na podłodze (osie na z = 7,1), trzecie nad nimi (z = 18,0), zestaw jest wyśrodkowany w y = 41,6.
- Kosz to otoczka tych trzech kół (r = 7,1) dolepiona do podłogi. Solver pilnuje, żeby żaden element płytki nie zbliżył się do niej bliżej niż do tej otoczki.
- Ogniwa są połączone szeregowo jak w wariancie 1 (środkowe odwrócone): płytki styków w kształcie „pastylek” r = 4,5 mm, płytka łącząca ogniwa 2 i 3 przy lewym końcu, płytka łącząca ogniwa 1 i 2 przy prawym, szczeliny w przegrodach pod te płytki. Styki Keystone jak w iteracji 2, model uproszczony.
- Przewody baterii wychodzą otworami Ø3 nad lewym końcem ogniwa 1 (−) i prawym końcem ogniwa 3 (+).

## Wkładanie baterii: pokrywka w prawym boku

Trzy ogniwa w trójkącie nie dadzą się włożyć od spodu (trzecie nie ma jak przejść między dwoma dolnymi), więc ogniwa wsuwa się wzdłuż osi, od **prawego boku trójkątnego**:

1. W boku jest otwór w kształcie zaokrąglonego trójkąta (otoczka kół r = 6,3 mm), większy od ogniw, więc ogniwa wchodzą przez niego do kanałów ([06-prawy-bok-ogniwa.png](renders/06-prawy-bok-ogniwa.png)).
2. Zamyka go **pokrywka** (`pokrywka-baterii.stl`): wtyczka w kształcie tego samego zaokrąglonego trójkąta (r = 6,0 mm, luz 0,3 mm), długa na 12 mm, z wypukłością licowaną z zaokrągleniem krawędzi boku ([05b-prawy-bok-pokrywka.png](renders/05b-prawy-bok-pokrywka.png)). Na jej wewnętrznej ściance siedzą płytki styków prawego końca.
3. Trzyma ją **jedna śruba M2 × 16** w środku zestawu (otwór Ø2,2 z zagłębieniem Ø4,4 w pokrywce, otwór prowadzący Ø1,7 w żebrze między kanałami).

Dolna powierzchnia obudowy jest teraz gładka, bez klapki i wycięcia (patrz [05-spod.png](renders/05-spod.png)).

## Kontrola

- Wszystkie części są bryłami zamkniętymi (0 krawędzi nierozmaitościowych).
- [`check_collisions_wedge.py`](../../tools/enclosure/check_collisions_wedge.py): 0 kolizji we wszystkich 147 parach (kontrola dodatnia testu 1,00 mm³). Pierwsze podejście miało 4 kolizje płytek styków (kwadraty 9 × 9 mm wchodziły w ścianki okrągłych kanałów), poprawione.
- Wariant 1 po zmianach skryptu: objętości wszystkich części takie same jak przed zmianami (kolejność trójkątów w STL może się różnić).
- Nie sprawdzałem wytrzymałości, wydruku ani montażu na fizycznych częściach.

## Do uzupełnienia

1. **Żebro pod śrubę pokrywki** to najsłabsze miejsce: między trzema kanałami zostaje tylko ok. 3,5 mm średnicy materiału, czyli ścianka ok. 0,9 mm wokół otworu prowadzącego Ø1,7. Do wydruku warto zwiększyć rozstaw osi albo dać dwa zatrzaski zamiast śruby.
2. **Przewód od pokrywki.** Dodatni biegun jest przy prawym końcu, więc przewód z płytki styku na pokrywce idzie do płytki głównej na stałe: potrzebny zapas, żeby zdjęcie pokrywki nie wyrwało lutu. Alternatywa: pokrywka bez styków i przewód przez kanał.
3. **Dół otworu** w prawym boku leży 0,8 mm nad podstawą (r otworu 6,3 przy osi 7,1), więc przy końcu podłoga jest cienka i wchodzi w zaokrąglenie krawędzi boku. Bezpieczniej podnieść zestaw o ok. 1 mm (solver to pozwala), kosztem ok. 1 mm wysokości.
4. Kolejność wkładania ogniw przy zamkniętym zestawie (ogniwa 1, 2 od lewego końca; styk sprężynowy po stronie ujemnej) trzeba sprawdzić na wydruku. Wymiary styków i sprężyn Keystone: jak w README iteracji 2.
5. Pozostałe punkty jak w README wariantu 1 (orientacja druku, dioda D1, głośnik, kapsle).
