# Obudowa minutnika: iteracja 2

Model parametryczny w Blenderze 5.2, w milimetrach (1 jednostka = 1 mm), zbudowany skryptem [`tools/enclosure/build_enclosure.py`](../../tools/enclosure/build_enclosure.py) z danych płytki [`docs/pcb/pcb-layout.json`](../pcb/pcb-layout.json). Zmiana płytki w kolejnej iteracji wymaga tylko podmiany tego pliku i ponownego uruchomienia skryptu.

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --python tools/enclosure/build_enclosure.py
```

Pierwsza i druga iteracja dotyczą wyglądu zewnętrznego, przycisków, koszyka na baterie i podziału na dwie części. Szczegóły konstrukcyjne (zatrzaski, ścianki pod druk) są uproszczone.

## Zmiany względem iteracji 1

1. **Bez studni dla ATtiny.** Dostęp do układu jest po rozkręceniu obudowy.
2. **Dwie części i wkręty.** Przednia czara trzyma płytkę, tylny blok trzyma koszyk i głośnik. Cztery wkręty M2,5 × 20 idą od tyłu. Po wykręceniu blok zdejmuje się, a tył płytki z gniazdem ATtiny jest w pełni odsłonięty ([07-otwarta-plytka.png](renders/07-otwarta-plytka.png), [08-rozlozona.png](renders/08-rozlozona.png)).
3. **Margines klapki.** Klapka ma 3,5 mm od krawędzi obudowy po obu stronach w y i 8,2 mm od lewej krawędzi w x (wcześniej dochodziła prawie do krawędzi).
4. **Zaokrąglenia.** Góra (front) R3,0, dół (tył) R1,5, narożniki pionowe R6. Mniejszy promień na dole zostawia płaskie pole pod klapkę i łby wkrętów.
5. **Obrót układu o 90°.** Wyświetlacz jest równoległy do dłuższej krawędzi (76 mm). Ogniwa AAA leżą w poprzek wyświetlacza (wzdłuż krótszej krawędzi), kanały koszyka stoją obok siebie wzdłuż dłuższej krawędzi, a głośnik leży obok koszyka.

## Koncepcja: płaski stos

Wymiary zewnętrzne: **76,0 × 57,0 × 33,8 mm** (dł. × szer. × głęb.). Od frontu do tyłu:

| Część | z [mm] | Co |
| --- | --- | --- |
| Czara przednia | 8,4 … −11,2 | panel 1,6 mm z oknem OLED (szkło + 0,3 mm luzu), 3 otwory Ø10,2 pod kapsle, napis „TINY TIMER” (grawer 0,4 mm), komora elektroniki, 4 słupki płytki (Ø5,8, otwór prowadzący Ø2,1), 4 słupki pod wkręty łączące (Ø6) |
| Blok tylny | −11,2 … −25,4 | przegroda 1,6 mm z przepustami przewodów, koszyk 3×AAA, głośnik Ø27, ścianka tylna 1,6 mm, wypust centrujący 2 mm wchodzący do czary |

Ścianki boczne 2,0 mm. Luz płytki do ścianki komory 1,5 mm z każdej strony.

## Wkręty łączące

- Cztery wkręty M2,5 × 20 z łbem Ø4,6 w zagłębieniu Ø4,8 × 3,5 mm od tyłu, w pozycjach (x, y) = (−9,7; 5), (−9,7; 45), (57,7; 5), (57,7; 45).
- W czarze słupki Ø6 z otworem prowadzącym Ø2,1 × 9,5 mm (wkręt wkręca się w plastik). W bloku otwór przelotowy Ø2,7.
- Z lewej strony lita ściana bloku ma 8,8 mm, bo mieści zagłębienia na łby i margines klapki. Z prawej wkręty siedzą w narożnikach pasa głośnika, poza kieszenią głośnika.
- Wkręty płytki (M2,5 od tyłu przez płytkę w słupki czary) są niezależne i dostępne po zdjęciu bloku.

## Przyciski

Trzy kapsle (Ø9,6, kołnierz Ø11,8) osadzone na trzpieniach 3,8 × 3,8 mm przycisków B3F-4055 (gniazdo 4,0 × 4,0 mm). Wystają 1,4 mm ponad panel. Kołnierz pod panelem jest ogranicznikiem wysuwu. Symbole wygrawerowane: − (ciemny), ▶ (pomarańczowy, start), + (ciemny).

## Koszyk 3×AAA (zintegrowany z blokiem)

- Trzy kanały 11,0 × 11,0 mm, dzielniki 1,2 mm, długość wnęki 51 mm (ogniwo 44,5 mm plus styki). Otwarte do tyłu.
- Ogniwa połączone szeregowo: ogniwo 2 odwrócone. Łączniki między kanałami przechodzą przez szczeliny w dzielnikach.
- Klapka (osobna część, 36,6 × 50,0 mm): płyta 0,8 mm we wpuście plus wtyk 0,8 mm w oknie, dwa elastyczne języki z zębami wchodzą w gniazda w bocznych ścianach koszyka. Wyżłobienie pod palec przy wysokim końcu y.
- Okno jest szersze niż ogniwo (48,5 mm), więc ogniwo wkłada się z góry i dosuwa do sprężyny.
- Widok: [04-tyl-koszyk-otwarty.png](renders/04-tyl-koszyk-otwarty.png), [03-tyl-iso.png](renders/03-tyl-iso.png).

### Styki

| Rola | Wybrana część | Uwagi |
| --- | --- | --- |
| Ujemny, sprężynowy | Keystone **5204** (lutowany, AAA/AAAA/N), alternatywnie 5203 | [Farnell](https://uk.farnell.com/keystone/5204/battery-neg-spring/dp/1650702), [Newark 5203](https://www.newark.com/keystone/5203/negative-spring-battery-contact/dp/90B2547) |
| Dodatni, płytka z przyciskiem | Keystone **5226** (AAA/AAAA/N) | [Farnell](https://at.farnell.com/en-AT/keystone/5226/battery-pos-tab-2a-4a-n/dp/1650705); wymiary z bazy części: ok. 9,2 × 9,2 mm, grubość 0,5 mm |

Model styków jest uproszczony (płytka 9 × 9 × 0,5 mm i stożek sprężyny Ø6 → Ø3,3, ściśnięty ok. 5,5 mm). **Nie znalazłem rysunków producenta z wymiarami**, więc przed drukiem trzeba je sprawdzić w karcie katalogowej Keystone. Referencja gotowego koszyka 3×AAA: Keystone 2479 (52,7 × 37,5 × 13 mm wg [Rapid](https://www.rapidonline.com/keystone-2479-thm-battery-holder-for-3-x-aaa-18-3684)).

## Głośnik

Głośnik Ø26,5 × 9 mm w kieszeni Ø27 w bloku tylnym (prawa część), otwory dźwiękowe Ø2,0 (23 szt.) w ściance tylnej, przewody przez przepust w przegrodzie.

## Pliki

| Plik | Zawartość |
| --- | --- |
| `obudowa.blend` | pełna scena (czara, blok, klapka, kapsle, styki, ogniwa, płytka z elementami, głośnik) w osobnych kolekcjach |
| `obudowa-przod.stl`, `obudowa-tyl.stl`, `klapka-baterii.stl`, `kapsle.stl` | części do wydruku, w mm, ustawione jak w montażu (czarę drukuje się panelem do dołu, blok i klapkę ścianką tylną do dołu) |
| `renders/` | przód, tył z klapką i bez, bok, płytka po otwarciu, widok rozłożony, przekroje przez koszyk i poprzeczny |

Blender nie eksportuje STEP. Jeśli potrzebny będzie STEP, trzeba przepuścić STL przez inne narzędzie albo zbudować model w CadQuery.

## Kontrola

- Wszystkie części są bryłami zamkniętymi (0 krawędzi nierozmaitościowych).
- [`tools/enclosure/check_collisions.py`](../../tools/enclosure/check_collisions.py): objętość wspólna czary, bloku i klapki z płytką, elementami, ogniwami, stykami, głośnikiem i kapslami wynosi 0 dla wszystkich par, a czara z blokiem na siebie nie zachodzą (test ma kontrolę dodatnią).
- Sprawdzone ręcznie: położenie zagłębień wkrętów względem wpustu klapki (1,25 mm litej ścianki w x) i względem zaokrąglenia R1,5.

## Do uzupełnienia w kolejnych iteracjach

1. Wymiary styków Keystone z kart katalogowych, miejsce na lutowane wyprowadzenia styków i przewody.
2. Dioda D1 jest na tylnej stronie płytki i zasłonięta przez przegrodę. Trzeba zdecydować, gdzie ma świecić (światłowód, okno z przodu).
3. Zęby zatrzasków klapki są prostokątne. Przed drukiem warto dać im skosy wejściowe i sprawdzić sprężystość na wydruku.
4. Wysokość układu w podstawce (8,5 mm) i grubość modułu OLED (4,0 mm) to wartości ze specyfikacji, do zmierzenia.
5. Po bokach wyświetlacza i przycisków zostają szerokie pasy panelu (ok. 14 mm), bo dłuższa krawędź wynika z koszyka i głośnika, a nie z płytki. Można je zagospodarować (otwór na smycz, wgłębienie na magnes) albo zmniejszyć, przesuwając głośnik do komory elektroniki.
6. Przewody baterii i głośnika między blokiem a płytką potrzebują zapasu na długości, żeby otwarcie nie wyrywało lutów.
