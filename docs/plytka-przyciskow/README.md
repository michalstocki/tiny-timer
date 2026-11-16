# Płytka przycisków (obudowa klin 4)

Trzy przyciski Omron B3F-4055 (S3 „−”, S1 „run”, S2 „+”) i cztery przewody do pól KEY płytki głównej. Są dwie wersje o tym samym położeniu przycisków, otworów M2 i pól przewodów:

| Wersja | Dla kogo |
| --- | --- |
| **[Płytka drukowana TT-BTN](#płytka-drukowana-tt-btn-zamówienie-na-pcbway)** (54 × 16 mm, 2 warstwy) | zalecana: bez pracy warsztatowej, zamówienie razem z płytką główną |
| [Płytka uniwersalna](#płytka-przycisków-na-płytce-uniwersalnej) (50 × 16 mm, raster 2,54) | gdy masz płytkę uniwersalną pod ręką i nie chcesz czekać na fabrykę |

## Płytka drukowana TT-BTN (zamówienie na PCBWay)

| Plik | Co to |
| --- | --- |
| [`tt-buttons.kicad_pcb`](tt-buttons.kicad_pcb) | projekt dla KiCada (format v7, sprawdzony w KiCadzie 10.0.7): obrys, stopki, sieci, ścieżki, opisy |
| [`produkcja/tt-buttons-gerber.zip`](produkcja/tt-buttons-gerber.zip) | **plik do wysłania do fabryki**: 7 warstw Gerber, wiercenia PTH i NPTH (Excellon, mm), plik zadania `.gbrjob` |
| `produkcja/` (reszta) | rozpakowane Gerbery, raporty DRC KiCada, mapy wierceń (poza zipem), podglądy `kicad-F.svg` i `kicad-B.svg` |
| [`plytka-przyciskow-pcb-top.png`](plytka-przyciskow-pcb-top.png), [`plytka-przyciskow-pcb-bottom.png`](plytka-przyciskow-pcb-bottom.png) | render KiCada obu stron |

![strona elementów](plytka-przyciskow-pcb-top.png)

![strona lutowania](plytka-przyciskow-pcb-bottom.png)

### Zamówienie

Płytka główna ([`docs/plytka-glowna/`](../plytka-glowna/README.md)) i płytka przycisków to **dwa osobne projekty i dwa osobne zamówienia**, oba jako „Single pieces”. Wrzuć oba do jednego koszyka, wtedy wysyłka jest jedna.

| Parametr w formularzu PCBWay | Płytka przycisków | Płytka główna |
| --- | --- | --- |
| Board type | Single pieces | Single pieces |
| Different design in panel | 1 | 1 |
| Size | **54 × 16 mm** | 40 × 24 mm |
| Quantity | 5 | 5 |
| Layers / Material / Thickness | 2 / FR-4 / 1,6 mm | 2 / FR-4 / 1,6 mm |
| Pozostałe | domyślne (HASL, zielona maska, biały opis, miedź 1 oz) | jak w [README płytki głównej](../plytka-glowna/README.md#parametry-do-zamówienia-typowa-fabryka-2-warstwowa-np-jlcpcb-lub-pcbway) |

**Dlaczego nie jeden plik z obiema płytkami (panel).** Sprawdziłem w kalkulatorze PCBWay (15.11.2026, 2 warstwy, FR-4 1,6 mm, opcje domyślne, ceny bez wysyłki). Najniższa stawka obejmuje tylko 5 sztuk **jednego** projektu do 100 × 100 mm. Każde połączenie płytek w jednym pliku podnosi cenę:

| Wariant | Sztuk | Cena |
| --- | --- | --- |
| 1 projekt, Single pieces (40 × 24, 54 × 16 albo do 100 × 100 mm) | 5 | **5,00 USD** |
| to samo | 10 / 20 | 18,69 / 22,33 USD |
| 2 projekty w jednym pliku, Single pieces | 5 | 27,00 USD |
| panel klienta z mostkami, 1 zestaw (główna + przyciski) | 5 paneli | 36,10 USD |
| panel klienta, 2 zestawy, 100 × 50 mm | 5 paneli | 39,99 USD |
| panel klienta, 3 zestawy, 100 × 100 mm | 5 paneli | 47,04 USD |

Dwie osobne płytki to więc 10 USD za 5 kompletów. PCBWay nie nacina też płytek tak małych jak nasze: według jej zasad V-cut wymaga co najmniej 60 × 45 mm. Każdy panel trzeba by łączyć mostkami z otworami, a to ich formularz liczy jako panel klienta („Panel by Customer”, zob. [Confirm the panel way of the boards](https://www.pcbway.com/helpcenter/panel_issues/Confirm_the_panel_way_of_the_boards.html), [PCB Panel Creation](https://www.pcbway.com/pcb_prototype/PCB_Panel_Creation.html), [V-Scoring](https://www.pcbway.com/pcb_prototype/PCB_V_Scoring.html)). Ceny są orientacyjne: kalkulator zaznacza, że cenę ostateczną ustala PCBWay po weryfikacji, i ceny mogą się zmienić.

### Projekt

- **Zarys 54 × 16 mm** z narożnikami R2, o 2 mm szerszy z każdej strony niż płytka uniwersalna. Przy 50 mm otwory skrajnych nóżek (rozstaw 12,5 mm według karty) leżałyby 0,4 mm od krawędzi, a pola wychodziłyby poza płytkę. Przyciski, otwory M2 i pola przewodów są w tych samych miejscach względem obudowy, a w tabeli niżej współrzędne są przesunięte o 2 mm. Szerszy zarys sprawdziłem w modelu obudowy klin 4 (`TT_BB_EXTRA=2` w [`build_wedge4.py`](../../tools/enclosure/build_wedge4.py)): 0 kolizji w 104 parach, zdejmowanie pokrywy bez kolizji.
- **Stopka B3F-4055 według karty:** 4 pola Ø2,2 z otworem Ø1,2 w rozstawie 12,5 × 5,0 mm i dwa otwory **Ø1,8 bez metalizacji na kołki ustalające** (9,0 mm od siebie). Kołków nie trzeba ścinać.
- **Pola przewodów** Ø2,0 z otworem 1,2 mm, jak pola KEY na płytce głównej. Są w tych samych miejscach co oczka G4, G6, N4 i N2 na płytce uniwersalnej. KEY1 (GND) ma pole kwadratowe, tak jak na płytce głównej. Opisy K1…K4 są na obu stronach.
- **Ścieżki** 0,30 mm, ręcznie, pod kątem 45°. Strona lutowania (B.Cu): rzędy nóżek każdego przycisku, GND od S1 do S2 i odejścia do K1, K2 i K4. Strona elementów (F.Cu): jedna ścieżka PB4 od S3 przez K3, osią przycisków pod S1, do S2. Schemat jest ten sam co niżej, nie ma przewodów rozdzielczych.
- **Otwory M2** Ø2,2 bez metalizacji. Miedź trzyma się z daleka od łba wkręta (od strony lutowania) i od słupka pokrywy (od strony elementów): ścieżki co najmniej 2,3 mm od osi, pola 3,4 mm.
- Opisy: oznaczenia S1…S3 i symbole −, RUN, + na stronie elementów. Na stronie lutowania napis TT-BTN v1.0 i strzałka „glosnik ->” wskazująca stronę głośnika. Napisy „TOP” i „BOT” w miedzi, jak na płytce głównej (kontrola, czy warstwy nie są zamienione).

| Element | Położenie [mm] od lewego dolnego narożnika (widok od strony elementów) |
| --- | --- |
| S3 „−”, S1 „run”, S2 „+” (środki) | 9,22 / 27,00 / 44,78; y = 8,00 |
| otwory M2 Ø2,2 | (18,11; 2,92) i (35,89; 13,08) |
| K1 GND (kwadratowe), K2 PB3 | (35,89; 8,00), (35,89; 2,92) |
| K3 PB4, K4 do R6 | (18,11; 8,00), (18,11; 13,08) |

### Montaż

1. Sprawdź przyciski multimetrem (krok 0 niżej). Wynik decyduje o schemacie.
2. Włóż trzy przyciski od strony elementów (kołki wchodzą w otwory Ø1,8), dociśnij do laminatu i zalutuj od strony lutowania (12 lutów). Nie myj płytki z przyciskami.
3. Przewody KEY1…KEY4 przełóż od strony lutowania przez pola K1…K4 i zalutuj od strony elementów, z końcówką do 1 mm (nad płytką jest 6,8 mm do sufitu pokrywy). Kolory i pola płytki głównej jak w tabeli „Połączenia na płytce” niżej.
4. Kontrola multimetrem jak w kroku 10 niżej. Montaż w pokrywie: dwa wkręty M2 × 6 od strony lutowania, lewa krawędź (strzałka „glosnik ->”) od strony głośnika.

### Co sprawdziłem

- **Kontrola własna** ([`tools/pcb/fab_buttons.py`](../../tools/pcb/fab_buttons.py)): każda z 4 sieci w jednym kawałku, odstęp miedzi co najmniej 0,25 mm (najmniejszy jest **0,35 mm**), miedź co najmniej 0,5 mm od krawędzi, otwory kołków i M2 ze strefami wolnymi od miedzi. Test ujemny: usunięta ścieżka, ścieżka przy polu innej sieci i ścieżka przy M2 są wykrywane. Pierwsza wersja trasy przechodziła 0,13 mm od narożnika kwadratowego pola KEY1. Wykrył to DRC KiCada, bo moja kontrola liczyła pola jako okrągłe. Kontrola liczy teraz kwadraty jako kwadraty i na starej trasie podaje te same odległości co KiCad.
- **KiCad 10.0.7** ([`export_fab.sh`](../../tools/pcb/export_fab.sh)): DRC bez błędów, 0 niepołączonych pól. Zostało 9 ostrzeżeń o braku biblioteki `TT` (stopki są wbudowane w plik). Gerbery i wiercenia: PTH Ø1,2 (12 nóżek i 4 pola przewodów), NPTH Ø1,8 (6 kołków) i Ø2,2 (2 × M2).
- **Nie sprawdziłem** podglądu Gerberów w PCBWay (wymaga wgrania pliku na ich stronę) ani dopasowania na fizycznym B3F-4055. Po wgraniu zipa sprawdź, czy PCBWay rozpoznał 2 warstwy i wymiar 54 × 16 mm.

### Regeneracja

```bash
python3 tools/pcb/fab_buttons.py                                                                 # kontrola + tt-buttons.kicad_pcb
bash tools/pcb/export_fab.sh docs/plytka-przyciskow/tt-buttons.kicad_pcb docs/plytka-przyciskow/produkcja   # DRC KiCada, Gerbery, zip
```

## Płytka przycisków na płytce uniwersalnej

Trzy przyciski Omron B3F-4055 (S3 „−”, S1 „run”, S2 „+”) na kawałku jednostronnej płytki uniwersalnej **50 × 16 mm**, z czterema przewodami do pól KEY płytki głównej. Zarys, otwory M2 i rozstaw przycisków są zgodne z [obudową klin 4](../obudowa-klin-4/README.md#5-płytka-przycisków-na-płytce-uniwersalnej) (dane: [`pcb-layout.json`](../pcb-klin3/pcb-layout.json), klucz `button_board`).

**Do druku: [`plytka-przyciskow-szablon.pdf`](plytka-przyciskow-szablon.pdf)** (A4, 4 strony):

| Strona | Treść |
| --- | --- |
| 1 | **Szablon 1:1** od strony elementów: zarys z narożnikami R2, siatka oczek, otwory M2 Ø2,2, obrysy przycisków, tabela współrzędnych, linijka kontrolna 100 mm |
| 2 | **Połączenia** od strony lutowania w skali 3:1: adresy oczek, 6 przewodów rozdzielczych, 4 pola KEY, lista przewodów z kolorami i długościami |
| 3 | **Schemat elektryczny**, wnętrze przycisku wg karty, kontrola multimetrem |
| 4 | Lista części i narzędzi, kolejność montażu, najczęstsze pułapki |

Te same strony jako SVG: `plytka-przyciskow-{szablon,polaczenia,schemat,montaz}.svg`. Generator i kontrola projektu: [`tools/pcb/button_board.py`](../../tools/pcb/button_board.py).

```bash
python3 tools/pcb/button_board.py           # kontrola + PDF/SVG w tym katalogu (wymaga rsvg-convert)
python3 tools/pcb/button_board.py --check   # tylko kontrola
```

## Założenie: przycisk zgodny z kartą

Projekt przyjmuje budowę z karty Omron B3F (A070-E1-08, s. 6, model B3F-4055 „projected plunger, bez nóżki masy”):

| Co | Wartość z karty |
| --- | --- |
| Połączenia wewnętrzne (widok z góry) | **4–3 i 2–1 połączone na stałe**, wciśnięcie zwiera górny rząd z dolnym |
| Nóżki | 4 szt., **12,5 × 5,0 mm** (±0,1), otwory w płytce Ø1,2 (±0,05); blaszki ok. 1,0 × 0,3 mm (odczyt z rysunku), 3,5 mm pod korpusem |
| Kołki ustalające | 2 szt. Ø1,6 (otwory Ø1,8), **9,0 mm** od siebie, na osi między kolumnami nóżek |
| Korpus, wysokość, trzpień | 12 × 12 mm, 7,3 mm nad płytką (korpus 4,3), trzpień 3,8 × 3,8 mm |
| Siła, skok | 2,55 ±0,69 N, skok 0,3 mm; obciążenie 1…50 mA, 3…24 V; mycie niemożliwe |

To rozstrzyga sprzeczność z wcześniejszej specyfikacji (`docs/pcb/specyfikacja-obudowy-dla-agenta.md`, punkt 7: „wg pomiaru właściciela 5 mm”): **nóżki połączone na stałe dzieli 12,5 mm**, nie 5 mm. Numery nóżek nie są nadrukowane na obudowie przycisku, więc w projekcie rozróżnia się je po położeniu: para nóżek rozstawionych o 12,5 mm to jeden „rząd”.

Skoro założenie decyduje o schemacie, pierwszym krokiem montażu jest **sprawdzenie ciągłości na samych przyciskach** (strona 3 i 4 PDF). Jeśli wynik wyjdzie odwrotnie, nie lutuj dalej.

## Płytka uniwersalna

- Jednostronna FR4 **1,6 mm**, raster **2,54 mm**, **osobne pola lutownicze** (nie płytka paskowa: paski zwarłyby nóżki). Kawałek co najmniej 55 × 20 mm, wygodniej 70 × 30 mm.
- Przed zakupem lub użyciem sprawdź raster: skrajne oczka rzędu na płytce mają trafić w kropki A i T szablonu (19 odstępów = 48,26 mm). Płytki o rastrze 2,5 mm się nie nadają.
- Oczka Ø1,0 mogą być za ciasne dla blaszki 1,0 × 0,3 mm (przekątna ok. 1,05 mm): jeśli nóżka wchodzi z oporem, rozwierć oczko pod nóżkę do Ø1,2, zgodnie z kartą.

## Geometria i raster

Siatka oczek leży tak, że wszystkie nóżki przycisków trafiają w oczka. Adres oczka to **kolumna A…T + rząd 1…7** w widoku od strony elementów (x w prawo, y w górę), jak na szablonie.

| Element | Położenie [mm] od lewego dolnego narożnika | Oczko |
| --- | --- | --- |
| przycisk S3 „−” (środek) | 7,22; 8,00 | nóżki A3, F3 (dół), A5, F5 (góra) |
| przycisk S1 „run” | 25,00; 8,00 | H3, M3, H5, M5 |
| przycisk S2 „+” | 42,78; 8,00 | O3, T3, O5, T5 |
| otwór M2-1 Ø2,2 | 16,11; 2,92 | G2 |
| otwór M2-2 Ø2,2 | 33,89; 13,08 | N6 |

- Pierwsze oczko (A1) jest w (0,87; 0,38), ostatnie (T7) w (49,13; 15,62). Raster ma 20 kolumn × 7 rzędów, a środki przycisków leżą w połowie oczka (x) i na rzędzie 4 (y).
- Rozstaw oczek 12,70 mm kontra 12,50 mm w karcie: oczka są o 0,10 mm na każdą stronę dalej niż otwory zalecane, w granicach tolerancji karty (nóżki są sprężyste). Odchyłka w osi y to 0,04 mm. Generator sprawdza to przy każdym uruchomieniu.
- **Skrajne rzędy oczek (1 i 7) leżą 0,38 mm od krawędzi, więc linia cięcia przetnie ich oczka.** Nie są używane. Nie da się tego uniknąć bez zmiany obudowy: rzędy nóżek (y = 5,46 i 10,54) wyznaczają fazę rastra. Skrajne kolumny (A i T) są 0,87 mm od krawędzi i zostają prawie całe.
- Dwa otwory M2 leżą na oczkach, po przekątnej, pomiędzy przyciskami (słupki w pokrywie nie wchodzą w korpusy: sprawdzone wymiarowo).

## Schemat

![schemat](plytka-przyciskow-schemat.svg)

| Przycisk | Górny rząd (nóżki 4–3) | Dolny rząd (nóżki 2–1) | Zwiera |
| --- | --- | --- | --- |
| S1 „run” | KEY1 (GND) | KEY2 (PB3) | KEY1–KEY2 |
| S2 „+” | KEY1 (GND) | KEY3 (PB4) | KEY1–KEY3 |
| S3 „−” | KEY4 (do R6, potem GND) | KEY3 (PB4) | KEY3–KEY4 |

Zgodne z [`docs/schemat.md`](../schemat.md): PB3 ma wewnętrzny pull-up, PB4 ma R5 8,2 kΩ do VCC, a „−” przechodzi przez R6 8,2 kΩ do GND (R6 jest na płytce głównej). Kontrola w generatorze buduje sieć z rysunku (nóżki, przewody, wewnętrzne połączenia przycisku) i sprawdza wszystkie 8 kombinacji wciśniętych przycisków: puszczone dają cztery osobne pola, a każdy przycisk zwiera dokładnie swoją parę. Wykrywa to błędy typu przewód na złym rzędzie albo pole KEY w złym oczku (sprawdziłem na celowo zepsutych wariantach).

## Połączenia na płytce

Wszystko po stronie lutowania, widok na stronie 2 PDF (obrócony jak kartka wokół osi pionowej, więc kolumny idą T → A).

| Nr | Od | Do | Sieć | Kolor | Trasa |
| --- | --- | --- | --- | --- | --- |
| W1 | M5 (S1, nóżka 3) | N4 | GND | czarny | 3,6 mm |
| W2 | O5 (S2, nóżka 4) | N4 | GND | czarny | 3,6 mm |
| W3 | M3 (S1, nóżka 1) | N2 | PB3 | pomarańczowy | 3,6 mm |
| W4 | F3 (S3, nóżka 1) | G4 | PB4 | niebieski | 3,6 mm |
| W5 | O3 (S2, nóżka 2) | G4 | PB4 | niebieski | 22,9 mm, rowkiem między rzędami 3 i 4 |
| W6 | F5 (S3, nóżka 3) | G6 | KEY4 | zielony | 3,6 mm |
| KEY1 | N4 | płytka główna | GND | czarny | |
| KEY2 | N2 | płytka główna | PB3 | pomarańczowy | |
| KEY3 | G4 | płytka główna | PB4 | niebieski | |
| KEY4 | G6 | płytka główna | do R6 | zielony | |

- Pola przewodu leżą w dwóch kolumnach między przyciskami (G i N), poza korpusami, więc przewód można przewlec z oczka na stronę elementów. Dwa przewody idą do jednej kolumny, dwa do drugiej: kabel z płytki głównej wystarczy rozdzielić na pary.
- Pozostałe nóżki (np. H5, T3) są po prostu przylutowane: wewnętrzne połączenie przycisku łączy je z sąsiadką.
- Oczka N4 i G4 mają po trzy przewody (kabel + dwa rozdzielcze): użyj cienkich przewodów rozdzielczych Ø0,25 (wire-wrap AWG30).
- Przewód W5 biegnie 3,8 mm od osi wkręta M2 w G2 (łeb Ø4 ma promień 2 mm). Generator pilnuje, żeby trasy przewodów były co najmniej 2,3 mm, a używane oczka co najmniej 3,4 mm od osi M2.
- Kolory kabla do płytki głównej to propozycja. Ważne, żeby zapisać, który przewód jest którym polem KEY.

## Instrukcja montażu

**Części:** 3 × Omron B3F-4055 (nie B3F-4155: ma piątą nóżkę), płytka uniwersalna jak wyżej, 6 przewodów rozdzielczych w izolacji Ø0,25 (razem ok. 10 cm), 4 linki 0,14 mm² w kolorach z tabeli, 2 wkręty samogwintujące M2 × 6, cyna z topnikiem bezmyjnym. **Narzędzia:** wiertła Ø1,0 i Ø2,2 (opcjonalnie Ø1,2), imadło, piła do laminatu lub miniszlifierka, pilnik, nożyk, szczypce tnące, multimetr, lutownica z grotem 1…2 mm.

0. **Sprawdź przyciski** (przed czymkolwiek). Multimetrem w zakresie ciągłości: nóżki rozstawione o 12,5 mm w jednym rzędzie (4–3 oraz 2–1) mają ciągłość zawsze, a nóżki w tej samej kolumnie (4–2, 3–1; 5,0 mm) tylko po wciśnięciu. Jeśli jest odwrotnie, przycisk nie jest zgodny z kartą: zatrzymaj się i zmierz sześć par nóżek.
1. **Wydrukuj stronę 1 w skali 100 %** (w oknie drukowania „Rzeczywisty rozmiar”, bez „Dopasuj do strony”). Odcinek 100 mm i kwadrat 20 × 20 mm sprawdź linijką. Dokładność wydruku nie ma tu znaczenia dla oczek (te są na płytce), ale ma dla linii cięcia i otworów M2.
2. **Przyłóż szablon do płytki** tak, by kropki szablonu (także szare, poza zarysem) pokryły się z oczkami płytki; zamocuj kawałkiem taśmy lub klejem w sztyfcie. Środki M2 nakłuj igłą przez papier (krzyżyki wskazują środek), zdejmij szablon. Linię cięcia możesz odrysować rysikiem.
3. **Wywierć M2:** płytka w imadle na drewnianej podkładce, najpierw Ø1,0, potem Ø2,2 (otwór ma być 2,2, bo wkręt idzie przez niego do słupka pokrywy). Rób to przed cięciem, kiedy płytka jest jeszcze duża.
4. **Wytnij zarys** 50 × 16 mm (zostaw 0,2 mm na pilnik), opiłuj do linii, zaokrąglij narożniki R2, usuń zadziory pilnikiem lub papierem. Dopuszczalna odchyłka wymiaru ok. ±0,3 mm (kapsle mają w otworach pokrywy 0,3 mm luzu, a płytka trzyma się na słupkach, więc ważniejsze od zarysu jest położenie M2 i przycisków). Pył z laminatu: maska i przewiew.
5. **Kołki ustalające przycisków** odetnij nożykiem lub szczypcami równo z korpusem (od spodu). To zalecany wariant: kołki nie trafiają w oczka (leżą 0,58 mm od rzędu oczek), a cztery luty trzymają przycisk w zupełności. Alternatywa: wywierć Ø1,8 według tabeli na stronie 1 (zniszczy to też brzegi sąsiednich oczek, które i tak nie są używane).
6. **Przymierz nóżki** przycisków w oczkach (bez lutowania). Nóżki są sprężyste i lekko zbiegają się (12,5 mm kontra 12,7 mm oczek), ale powinny wejść bez wciskania na siłę. Jeśli nie: rozwierć oczka pod nóżki Ø1,2.
7. **Włóż trzy przyciski** od strony elementów, korpusem do laminatu, bokami równolegle do krawędzi płytki (dłuższy rozstaw nóżek 12,5 mm wzdłuż płytki). Zalutuj po jednej nóżce, sprawdź, czy korpus leży płasko i prosto (ew. przegrzej i popraw), dopiero potem pozostałe, razem 12 lutów. Lutuj krótko, kilka sekund na nóżkę. **Nie myj** płytki z przyciskami (karta: mycie niemożliwe), resztki topnika bezmyjnego zostaw.
8. **Przewody rozdzielcze W1…W6** wg tabeli: zdejmij 1,5 mm izolacji, przewlecz lub przyłóż końcówkę do pola, zalutuj. Przewód układaj płasko przy laminacie (po stronie lutowania wystają końcówki nóżek do 1,9 mm: przewody nie powinny sięgać wyżej niż one) i z dala od czerwonych okręgów M2 (łeb wkręta).
9. **Cztery przewody do płytki głównej** (KEY1…KEY4) wlutuj w pola N4, N2, G4, G6 (przewód od strony lutowania przez oczko, końcówka po stronie elementów max 1 mm i utnij ją równo z laminatem; nad płytką od tej strony jest 6,8 mm do sufitu pokrywy). Długość: do ustalenia po złożeniu pokrywy (przewody od strony lutowania zbieraj ku płytce głównej, z luzem 10…15 mm).
10. **Kontrola multimetrem** (strona 3): puszczone: wszystkie pary KEY rozwarte; S1 zwiera KEY1–KEY2, S2 zwiera KEY1–KEY3, S3 zwiera KEY3–KEY4, a przy żadnym z nich nie ma innych zwarć.
11. **Montaż w pokrywie:** płytkę dołóż od wnętrza do słupków i przykręć dwoma wkrętami M2 × 6 od strony lutowania (łeb wkręta nie może leżeć na lutach ani przewodach). Na trzpienie przycisków wciśnij kapsle. Przycisk powinien dać wyraźne „kliknięcie” przez kapsel.

## Zgodność z obudową

- Trzpienie 7,3 mm nad płytką, kapsle i gniazda są z [klina 4](../obudowa-klin-4/README.md#4-kapsle-przycisków-b3f-4055); płytka trzyma się na słupkach z otworem Ø1,7 (pod M2 × 6).
- Płytka jest elementami do pokrywy, lutami do wnętrza. Ta strona jest w obudowie widoczna na renderze `12-pokrywa-od-srodka.png`: otwory M2 są na nim w lewym górnym i prawym dolnym rogu, co zgadza się z odbiciem na stronie 2 PDF (M2-2 po lewej u góry, M2-1 po prawej na dole).
- Oś x płytki jest osią obudowy: lewa krawędź (x = 0) jest od strony głośnika. Przycisk „−” (S3) jest przy głośniku, „+” (S2) przy prawym boku. Obrócenie płytki o 180° zamieni przyciski miejscami względem kapsli.

## Czego nie sprawdziłem i ryzyka

1. **Prawdziwe części.** Wszystko wynika z karty i z modelu obudowy, nic nie jest zmierzone na fizycznym B3F-4055 ani na konkretnej płytce uniwersalnej. Krok 0 i przymiarka (krok 6) są po to, żeby to wyłapać zanim cokolwiek zalutujesz.
2. **Karta nie podaje warunków lutowania** (w pliku jest tylko „mycie niemożliwe”): lutuj krótko i bez przegrzewania. Parametry ogólne Omron dla przełączników dotykowych leżą w osobnym dokumencie „Safety Precautions”, którego nie sprawdzałem.
3. **Skrajne rzędy oczek** są przecięte linią cięcia (punkt wyżej): to wynika z geometrii obudowy i nie wpływa na działanie. Jeśli zależy Ci na czystym brzegu, trzeba by zmienić rozstaw przycisków albo wymiar obudowy.
4. **Przewody i luz w pokrywie:** wysokość lutów i przewodów po stronie lutowania nie była sprawdzana modelem 3D (przyjęto do 1,9 mm jak dla nóżek).
5. **Płytka główna** ma osobny projekt i pliki produkcyjne w [`docs/plytka-glowna/`](../plytka-glowna/README.md); wersja drukowana płytki przycisków jest opisana na początku tego pliku.
