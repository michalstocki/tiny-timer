# Specyfikacja techniczna płytki dla agenta projektującego obudowę (iteracja 1)

Dokument opisuje wyłącznie **fizyczne i mechaniczne** wymagania płytki: wymiary, położenie elementów, wysokości, strefy zakazane, tolerancje. Wygląd obudowy, głośnik i koszyk baterii zostaną dodane przez właściciela projektu w osobnych sekcjach (patrz „Miejsce na wizję właściciela”).

**To jest pierwsza iteracja.** Wymiary płytki i położenia elementów mogą się zmienić w kolejnych iteracjach. Źródłem prawdy są pliki w tym katalogu, w katalogu `docs/pcb/`, generowane skryptem `tools/pcb/build.py`:

| Plik | Do czego |
| --- | --- |
| `pcb-layout.json` | wszystkie współrzędne (mm): zarys, otwory, elementy, pady, wysokości, sieci |
| `pcb_params.scad` | te same wartości jako zmienne OpenSCAD (zarys, otwory, prostokąty elementów z wysokościami) |
| `pcb-przod.svg`, `pcb-tyl.svg` | podgląd płytki z przodu i od tyłu (z wstępnym trasowaniem) |
| `pcb-przekroj.svg` | wysokości elementów w przekroju bocznym |
| `podglad-3d.html` | interaktywny podgląd 3D (przeglądarka, wymaga internetu dla three.js) |

Zalecany sposób pracy: parametryczny model (OpenSCAD albo CadQuery) czytający wartości z `pcb-layout.json` / `pcb_params.scad`, tak aby kolejna iteracja płytki wymagała tylko podmiany pliku. Wynik: STL i STEP dla każdego wariantu obudowy.

## 1. Układ współrzędnych

- Jednostki: **milimetry**.
- Widok **z przodu** (strona TOP, strona użytkownika): początek `(0, 0)` w **lewym dolnym rogu** zarysu płytki, **+x w prawo**, **+y w górę**.
- **+z** prowadzi od płytki w stronę użytkownika (przód). Górna powierzchnia laminatu to `z = 0`, dolna `z = -1.6`.
- Środek płytki: `(24.0, 25.0)`. Wszystkie elementy frontu (wyświetlacz, przyciski) są rozmieszczone symetrycznie względem tego środka w poziomie.

## 2. Płytka

| Parametr | Wartość |
| --- | --- |
| Zarys | prostokąt **48.0 × 50.0 mm**, narożniki zaokrąglone R3.0 |
| Grubość laminatu | 1.6 mm (FR-4) |
| Otwory montażowe | 4 × Ø2.7 mm (śruby M2,5), środki: (3.5, 3.5), (44.5, 3.5), (3.5, 46.5), (44.5, 46.5) |
| Strefa wokół otworu montażowego (bez elementów i miedzi sygnałowej) | promień 3.2 mm |
| Tolerancja zarysu płytki | ±0,2 mm (typowo u producenta); obudowa musi przyjąć ±0,3 mm |

Płytka jest dwustronna z metalizowanymi otworami. **Jest to wersja robocza (iteracja 1), jeszcze nie do zamówienia.**

## 3. Przód (TOP): elementy widoczne dla użytkownika

### 3.1 Moduł OLED (SSD1306 128×32, I2C, 0,91″)

| Parametr | Wartość | Źródło |
| --- | --- | --- |
| Zarys modułu (laminat) | x 5.0…43.0, y 26.5…38.5 (38.0 × 12.0 mm) | **szacunek** ze zdjęcia, zmierzyć |
| Szkło (obszar obrazu wraz z ramką szkła) | x 11.5…36.5, y 27.5…37.5 (25.0 × 10.0 mm) | wymiar od właściciela |
| Aktywny obszar wyświetlacza | zwykle ok. 22,4 × 5,6 mm, środek zbliżony do środka szkła | **typowy dla 0,91″, sprawdzić** |
| Grubość modułu (bez pinów) | 4.0 mm | wymiar od właściciela |
| Piny | 4 szt., rozstaw 2,54 mm w pionie, w kolumnie x = 6.5; od góry: SDA, SCK, VCC, GND | od właściciela |
| Środek pinów od lewej krawędzi szkła | 5.0 mm | od właściciela |
| Wysokość górnej powierzchni modułu nad płytką | **6.5 mm** (przy plastikowej listwie pinów 2,5 mm pod modułem) | założenie: listwa 2,5 mm; przy skróconej listwie wartość spada |

Moduł wlutowany jest piny w płytkę; piny przycina się po stronie tyłu. Szkło jest **wyśrodkowane w poziomie** na środku płytki (z dokładnością do siatki 2,54 mm pinów: przesunięcie 0.00 mm).

### 3.2 Przyciski (3 × Omron B3F-4055)

Dane z karty katalogowej Omron B3F-4050/4055/5050/5051 dostarczonej przez właściciela:

| Parametr | Wartość |
| --- | --- |
| Korpus | **12 × 12 mm** (±0,2) |
| Wysokość całkowita nad płytką (góra trzpienia) | **7,3 mm** (±0,2) |
| Wysokość korpusu | 4,3 mm (±0,2) |
| Trzpień (plunger) | kwadrat **3,8 × 3,8 mm** (±0,1), wystaje 1,8 mm ponad okrągłą podstawę |
| Podstawa trzpienia | okrągła, Ø7,1 mm |
| Rozstaw wyprowadzeń | 12,5 (±0,1) × 5,0 (±0,1) mm; otwory Ø1,2 mm |
| Dwa trzpienie pozycjonujące | otwory Ø1,8 mm, odległość 9,0 mm, w osi między kolumnami wyprowadzeń |
| Wyprowadzenia pod korpusem | ok. 3,5 mm (przechodzą przez płytkę 1,6 mm i wystają ok. 1,9 mm z tyłu) |

Położenia (środki korpusów, od lewej): 

| Przycisk | Funkcja | Środek (x, y) |
| --- | --- | --- |
| S3 | − | (8.0, 17.5) |
| S1 | run | (24.0, 17.5) |
| S2 | + | (40.0, 17.5) |

Odstęp między korpusami przycisków w poziomie: 4.0 mm; odstęp w pionie między dolną krawędzią modułu OLED a górną krawędzią przycisków: 3.0 mm. Wyświetlacz leży **powyżej** poziomej osi symetrii płytki (y = 25.0), przyciski **poniżej**, symetrycznie (środek wyświetlacza i środki przycisków są w tej samej odległości od osi).

Skok przycisku nie jest podany w otrzymanym fragmencie karty katalogowej; **przyjąć dodatkowy luz na ruch trzpienia 0,3–0,5 mm** i nie wspierać nakładek na korpusie.

### 3.3 Pozostała strona przednia

Poza modułem OLED i przyciskami na froncie nie ma wysokich elementów. W pasach nad modułem OLED i pod przyciskami z przodu **wystają końce nóżek elementów z tyłu** (przycięte, z cyną): **wysokość do 2,0 mm** nad laminatem. Wewnętrzna powierzchnia panelu przedniego powinna być co najmniej 2,5 mm nad płytką w tych pasach (a nad przyciskami i szkłem wyświetlacza wynika to z wysokości elementów).

## 4. Tył (BOTTOM): elementy przewlekane

Wszystkie elementy poza wyświetlaczem i przyciskami są po tylnej stronie. Obwiednia wysokości tylnej strony: **9.0 mm** poniżej dolnej powierzchni laminatu.

| Ozn. | Element | Prostokąt zajmowany (x0, y0, x1, y1) | Wysokość nad dolną powierzchnią płytki [mm] |
| --- | --- | --- | --- |
| U1 | ATtiny13A in DIP-8 socket | (9.5, 1.2, 19.9, 11.5) | 8.5 |
| R1 | 15 k | (20.2, 8.5, 25.7, 11.5) | 7.5 |
| R2 | 470 | (25.5, 38.3, 28.5, 43.8) | 7.5 |
| R3 | 47 k | (35.8, 38.3, 41.3, 41.3) | 7.5 |
| R4 | 33, 1/2 W | (16.0, 43.5, 25.1, 47.5) | 4.0 |
| R5 | 8.2 k | (26.7, 4.2, 29.7, 9.8) | 7.5 |
| R6 | 8.2 k | (3.3, 8.7, 8.8, 11.7) | 7.5 |
| C1 | 100 nF | (20.3, 3.5, 26.4, 8.0) | 6.0 |
| C2 | 100 nF | (1.4, 28.4, 5.8, 34.5) | 6.0 |
| C3 | 100 uF | (19.8, 37.4, 24.8, 42.6) | 8.0 |
| D1 | LED | (32.2, 41.7, 37.6, 46.9) | 8.7 |
| Q1 | BC547B | (29.6, 36.1, 34.8, 41.1) | 5.5 |
| SPK | pola lutownicze na przewody (Ø1,2 mm otwór, 2 pady) | (29.5, 41.6, 31.9, 46.6) | 0 |
| BAT | pola lutownicze na przewody (Ø1,2 mm otwór, 2 pady) | (14.4, 38.9, 19.4, 41.3) | 0 |

### Układ ATtiny13A w podstawce DIP-8

- Podstawka DIP-8 (wysokość 4,5 mm, wymiar od właściciela). Układ w podstawce razem sięga ok. **8,5 mm** poniżej płytki (**szacunek**, zmierzyć).
- **Układ jest wymienny**: właściciel programuje go poza obwodem i wkłada z powrotem. Obudowa musi umożliwiać dostęp do podstawki od tyłu (zdejmowana pokrywa lub otwór) i wyciągnięcie układu wyciągaczem DIP lub cienkim śrubokrętem z obu stron podstawki. Wcięcie (pin 1) układu jest skierowane do **górnej krawędzi płytki (+y)**.
- Elektrolit 100 µF (Ø5 × 8 mm) stoi pionowo; dioda LED jest 5 mm (wysokość do ok. 8,7 mm) lub 3 mm (mniejsza): do potwierdzenia.

## 5. Strefy zakazane i wymagania dla obudowy

1. **Okno na szkło** wyświetlacza, współrzędne szkła z 3.1; okno nie może zakrywać aktywnego obszaru; sugerowany luz 0,3 mm na stronę.
2. **Trzy otwory na przyciski** (korpus 12 × 12 mm nie przechodzi przez panel, trzpień i okrągła podstawa tak): środki z 3.2; otwory o średnicy co najmniej Ø7,1 + luz FDM, albo zewnętrzne nakładki (kapsle) opierające się na trzpieniu 3,8 × 3,8 mm. Górna płaszczyzna trzpienia: 7,3 mm nad płytką.
3. **Słupki montażowe** pod 4 otwory M2,5 (Ø2,7 mm); strefa wolna r = 3.2 mm wokół.
4. **Nie opierać** panelu na korpusach przycisków ani na module OLED w sposób dociskający trzpień; panel opiera się na słupkach montażowych.
5. Z tyłu: obwiednia 9.0 mm; w obszarze prostokątów z tabeli w sekcji 4 nic nie może wchodzić.
6. **Przewody** głośnika i baterii wchodzą na dwie pary pól lutowniczych (2 pady na parę, pad Ø2,3 mm, otwór Ø1,2 mm): położenie w tabeli w sekcji 4 (SPK, BAT). Zostawić prowadzenie przewodów i odciążenie (zacisk lub opaska).

## 6. Tolerancje i druk 3D (FDM)

- Luz na pasowania ruchome i wsuwane: **0,2–0,3 mm** na stronę, otwory na śruby +0,2 mm.
- Minimalna ścianka: 1,2 mm (3 obrysy przy dyszy 0,4 mm); minimalne detale okna: 0,8 mm.
- Kapsle przycisków muszą dawać luz od krawędzi otworu co najmniej 0,3 mm i mieć ogranicznik wysuwu.
- Zakładać, że elementy mają tolerancje: korpus przycisku ±0,2, wysokość 7,3 ±0,2, położenie modułu OLED ±0,3 (lutowany ręcznie).

## 7. Elementy niepewne (szacunki do zmierzenia)

| Wielkość | Przyjęto | Dlaczego niepewna |
| --- | --- | --- |
| Długość i położenie zarysu modułu OLED | 38 × 12 mm, pin 1,5 mm od lewej krawędzi | tylko zdjęcie |
| Wysokość listwy pinów pod modułem | 2,5 mm | typowa, do pomiaru |
| Wysokość ATtiny w podstawce | 8,5 mm | typowa dla DIP-8 |
| Dioda LED | Ø5 mm, 8,7 mm wysokości | właściciel ma „dowolną” LED |
| Skok przycisku B3F | nie podany w otrzymanym fragmencie | brak danych |
| Które nóżki B3F-4055 są połączone na stałe | wg karty: 12,5 mm od siebie (4–3 i 2–1); wg pomiaru właściciela: 5 mm | **sprzeczność do wyjaśnienia testem na przycisku**; dotyczy schematu płytki, nie obudowy |

## 8. Miejsce na wizję właściciela

### Głośnik

Dane od właściciela: **średnica 26,5 mm, wysokość ramki 4 mm, wysokość całego głośnika 9 mm**. Pozostałe (położenie, mocowanie, otwory dźwiękowe) uzupełni właściciel.

_Do uzupełnienia._

### Koszyk na baterie 3 × AAA

Wymiary koszyka, sposób wyjmowania baterii, położenie względem płytki: _do uzupełnienia przez właściciela._

### Wygląd i rozmieszczenie

_Do uzupełnienia przez właściciela._

## 9. Warianty do zbadania w kolejnych iteracjach

Właściciel przewiduje kilka iteracji i wybór finalnego wariantu. Obudowa powinna być parametryczna, tak aby można było łatwo zmienić: grubość ścianek, typ nakładek na przyciski (zlicowane z panelem, wystające, wpuszczone), sposób mocowania płytki (słupki od frontu lub tyłu), dostęp do układu ATtiny (pokrywa lub otwór), sposób zamykania (śruby, zatrzaski), orientację (głośnik z przodu, z tyłu lub z boku).
