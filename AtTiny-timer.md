# Minutnik na ATtiny13A: brief dla agenta

Oct 17, 2026 · @Michał Stocki

Agent pisze firmware w C dla ATtiny13A i dostarcza użytkownikowi instrukcję montażu minutnika na płytce stykowej: krok po kroku, ze współrzędnymi otworów i testami po każdym etapie.

## Zakres i rezultaty

Agent dostarcza pięć rzeczy; żaden z punktów nie jest opcjonalny, poza zaznaczonymi jako "nice to have".

1. **Firmware w czystym C** (`avr-gcc -Os`, bez Arduino IDE i bibliotek): pliki źródłowe, `Makefile`, plik `.hex` i raport `avr-size` z realnym zużyciem flash i RAM.
2. **Schemat połączeń** w postaci tekstowej listy (netlista: element, pin, do czego) i mapa pinów ATtiny13A.
3. **Instrukcja montażu na płytce stykowej**, krok po kroku, w formacie z sekcji "Instrukcja montażu" poniżej.
4. **Instrukcja programowania**: Arduino UNO jako programator ISP, ustawienie fuse'ów, wgranie `.hex`, weryfikacja.
5. **Procedura kalibracji czasu** (OSCCAL) i procedura testów odbiorczych.

Język wszystkich materiałów dla użytkownika: **polski**. Kod i komentarze w kodzie mogą być po angielsku.

Zasady pracy agenta:

- Nie zmyśla parametrów. Rozmiaru kodu nie podaje z pamięci: jeśli nie może uruchomić `avr-gcc` w swoim środowisku, mówi to wprost i oznacza kod jako **niezweryfikowany kompilacją**.
- Pyta użytkownika tylko wtedy, gdy coś blokuje pracę. W pozostałych sprawach przyjmuje domyślne wartości z tego dokumentu i opisuje, co przyjął.
- Jeśli coś w dokumencie wygląda na błąd (np. wynik obliczeń się nie zgadza), zgłasza to użytkownikowi, zamiast po cichu poprawiać.

## Sprzęt: co jest, czego brakuje

Użytkownik ma wszystkie potrzebne elementy, w tym tranzystor **BC547A** do sterowania głośnikiem; jedynym dodatkiem jest opcjonalna dioda zabezpieczająca (wystarczy dioda LED).

| Element | Status | Rola i uwagi |
| --- | --- | --- |
| ATtiny13A | jest | Zakładamy obudowę DIP-8 (pasuje do płytki). Jeśli użytkownik ma SOIC-8, agent mu o tym mówi i prosi o potwierdzenie. |
| Arduino UNO | jest | Programator ISP (szkic ArduinoISP). |
| OLED 128×32, SSD1306, I2C, 4 piny | jest | Zwykle adres 0x3C. Agent każe sprawdzić opis na module i multimetrem, czy są pull-upy SDA i SCL (rzędu 4,7–10 kΩ do VCC); jeśli ich nie ma, dodać po 4,7 kΩ. |
| Przyciski tact (3 szt.) | jest | "run", "+", "−". Agent opisuje, jak rozpoznać orientację styków multimetrem przed wsadzeniem w płytkę. |
| Koszyk na 3×AAA | jest | 4,5 V (alkaliczne, świeże do ok. 4,8 V), do ok. 3,3 V przy zużytych. |
| Głośnik z zabawki | jest | Rezystancja zmierzona multimetrem: **6,4 Ω**. Moc znamionowa nieznana, zakładamy małą (rzędu 0,25 W). |
| Rezystory i kondensatory | jest, dowolne | Potrzebne: 2× 10 kΩ, 470 Ω, 47 kΩ, 33 Ω (najlepiej ½ W, albo 2× 68 Ω równolegle), 2× 100 nF, 100 µF elektrolit, 10 µF (tylko do programatora). |
| Tranzystor BC547A | jest | Wyprowadzenia C-B-E (płaska strona do Ciebie, nóżki w dół). Prąd ciągły 100 mA, szczytowy 200 mA; z rezystorem 33 Ω pracuje w specyfikacji. Dźwięk będzie raczej cichy, co jest świadomym kompromisem. |
| Dioda LED (lub 1N4148) | jest (LED) | Opcjonalna, równolegle do głośnika (zabezpieczenie przed przepięciem z cewki). Nadaje się dowolna dioda LED. |
| Płytka stykowa i przewody | nie wymienione | Agent potwierdza rozmiar płytki. Układ ma się zmieścić na płytce 400 otworów (30 kolumn). |
| Wyłącznik zasilania | niepotrzebny | Zastępuje go długie przytrzymanie "run" (głębokie uśpienie). |

## Funkcje i logika

Minutnik ma cztery stany; po zakończeniu odliczania, zatrzymaniu i wybudzeniu zawsze wraca do 2:00, bez zapamiętywania ostatnio ustawionego czasu.

&#91;embedded content: diagram stanów minutnika · 4 stany\]

Szczegóły, których diagram nie pokazuje:

- **Format wyświetlania:** M:SS (np. 2:00), od 10 minut MM:SS (np. 60:00).
- **"run" krótko (poniżej 2 s):** akcja następuje po puszczeniu przycisku. W gotowości uruchamia odliczanie, w odliczaniu zatrzymuje je i przywraca 2:00 (to stop, nie pauza).
- **"+" i "−":** zmiana o 1 minutę na kliknięcie, zakres 1–60 min, bez zawijania (na granicy przycisk nic nie robi). Nieaktywne w odliczaniu i podczas sygnału. Auto-powtarzanie przy przytrzymaniu to dodatek o niskim priorytecie.
- **Start odliczania:** ekran pokazuje ustawiony czas (2:00), po 1 s 1:59 itd.; 0:00 pojawia się dokładnie po upływie ustawionego czasu.
- **Sygnał:** po osiągnięciu 0:00 jeden sygnał dźwiękowy (domyślnie ok. 1 s, stała łatwa do zmiany), na ekranie ikona dzwonka, potem 2:00.
- **Pasek postępu (nice to have):** ramka o szerokości 1 px na krawędzi ekranu, 316 pikseli (2·(128+32)−4). Liczba zapalonych pikseli = zaokrąglenie w górę z 316 · pozostały czas / czas całkowity. Znika w jednym kierunku od ustalonego punktu; agent opisuje wybrany punkt i kierunek.
- **Ikona dzwonka (nice to have):** co najmniej 16×16 px, widoczna tylko w czasie sygnału.
- **Uśpienie:** przytrzymanie "run" przez co najmniej 2 s w gotowości lub w odliczaniu. Firmware wyłącza OLED (komendy 0xAE, potem 0x8D z 0x10), ustawia pin głośnika na niski, wyłącza ADC i przechodzi w tryb Power-down. Wybudzenie: przerwanie pin change na przycisku "run". Naciśnięcie, które wybudziło układ, nie startuje odliczania (firmware czeka na puszczenie przycisku).
- **Automatyczne uśpienie po 60 s bezczynności** (tylko w gotowości): opcjonalne, implementowane na końcu i tylko jeśli zmieści się we flash.

## Schemat i mapa pinów

Wszystkie pięć użytecznych pinów ATtiny13A jest zajętych, a RESET zostaje wolny do programowania ISP (nie wolno ustawiać fuse'a RSTDISBL, bo bez programatora wysokonapięciowego układ przestałby być programowalny).

| Pin | Port | Funkcja w minutniku | Połączenie | Rola przy programowaniu ISP |
| --- | --- | --- | --- | --- |
| 1 | PB5 / RESET | wolny | 10 kΩ do VCC | RESET (UNO D10) |
| 2 | PB3 | przycisk "run" | przycisk do GND, wewnętrzny pull-up; PCINT3 budzi z uśpienia | niezwiązany |
| 3 | PB4 (ADC2) | przyciski "+" i "−" | drabinka rezystorowa (niżej) | niezwiązany |
| 4 | GND | masa | minus baterii | GND |
| 5 | PB0 | SDA (I2C programowy) | SDA OLED | MOSI (UNO D11) |
| 6 | PB1 (OC0B) | głośnik | 470 Ω do bazy tranzystora NPN | MISO (UNO D12) |
| 7 | PB2 | SCL (I2C programowy) | SCL OLED | SCK (UNO D13) |
| 8 | VCC | zasilanie | plus baterii (4,5 V) | 5 V z UNO |

**Drabinka przycisków na PB4.** Rezystor 10 kΩ z PB4 do VCC. Przycisk "+" łączy PB4 bezpośrednio z GND, przycisk "−" łączy PB4 z GND przez 10 kΩ. Napięcie na PB4: brak naciśnięcia = 100% VCC, "−" = 50% VCC, "+" = 0%. Naciśnięcie obu naraz daje 0% (odczyt jak "+"), czego firmware nie musi obsługiwać. Progi: poniżej 25% VCC "+", 25–75% "−", powyżej 75% nic. ADC z odniesieniem VCC, więc progi działają przy każdym napięciu baterii.

**Zasilanie i filtrowanie.** Bateria 3×AAA zasila szyny płytki. Kondensator 100 nF między pinami 8 i 4 jak najbliżej układu, drugi 100 nF przy wejściu zasilania OLED, 100 µF elektrolitycznie na szynach (kreska ujemna do GND), żeby głośnik nie resetował mikrokontrolera.

**I2C.** Linie SDA i SCL steruje firmware programowo (otwarty dren: niski przez wyjście, wysoki przez pull-up modułu). Jeśli moduł nie ma pull-upów, dodaje się po 4,7 kΩ do VCC.

**Uwaga na ISP.** Piny 5, 6 i 7 są jednocześnie liniami programatora. Na czas programowania instrukcja każe odłączyć baterie oraz wyjąć przewody SDA, SCL i rezystor bazy tranzystora (albo cały OLED), żeby programator nie walczył z podłączonymi elementami.

## Głośnik 6,4 Ω: obliczenia i dobór elementów

Głośnik jest sterowany tranzystorem BC547A z rezystorem szeregowym 33 Ω; bez niego prąd z baterii (ok. 670 mA) dawałby w głośniku około 1,4 W, czyli kilkakrotnie więcej, niż zniesie głośnik z zabawki, i przekroczyłby 200 mA szczytowych dopuszczalnych dla BC547A. Głośnika nie wolno też podpinać bezpośrednio do pinu mikrokontrolera (limit pinu to 20–40 mA). Dźwięk będzie z natury cichy (kilkadziesiąt mW w głośniku); poprawia go dopiero trafienie w częstotliwość rezonansową (test tonów poniżej).

| Element | Wartość | Połączenie |
| --- | --- | --- |
| Rezystor bazy | 470 Ω | PB1 (pin 6) do bazy tranzystora |
| Rezystor baza–masa | 47 kΩ | baza do GND; tranzystor jest wyłączony w uśpieniu i podczas resetu |
| Tranzystor NPN | BC547A | emiter do GND, kolektor do głośnika (C-B-E, płaska strona do Ciebie) |
| Rezystor szeregowy | 33 Ω, ½ W (lub 2× 68 Ω równolegle) | VCC do jednego wyprowadzenia głośnika |
| Głośnik | 6,4 Ω | drugie wyprowadzenie do kolektora |
| Dioda LED lub 1N4148 (opcjonalnie) | dowolna | równolegle do głośnika: anoda do wyprowadzenia od strony kolektora, katoda do wyprowadzenia od strony rezystora szeregowego |

Punkty pracy przy zasilaniu z baterii, przyjęto U\_CE(sat) = 0,3 V (BC547A przy ok. 100 mA) i wypełnienie 50%:

| Napięcie baterii | Prąd szczytowy | Moc w głośniku | Moc w rezystorze |
| --- | --- | --- | --- |
| 4,8 V (świeże) | 114 mA | 42 mW | 215 mW |
| 4,5 V (nominalne) | 107 mA | 36 mW | 188 mW |
| 3,3 V (zużyte) | 76 mA | 19 mW | 96 mW |

Prąd bazy przy 4,5 V to ok. 8 mA, więc pin PB1 jest dalek od limitu 20 mA.

**Dioda zabezpieczająca.** Zamiast 1N4148 można użyć dowolnej diody LED, włączonej równolegle do samego głośnika (nie do całego odcinka z rezystorem), bo dioda LED wytrzymuje napięcie wsteczne tylko ok. 5 V. Spadek napięcia na LED to ok. 2 V zamiast 0,7 V, co przy BC547A (wytrzymałość 45 V) wystarcza; LED może słabo błysnąć przy przełączaniu.

Polecenia dla agenta:

- **Częstotliwość tonu** to stała w kodzie (zakres 500–4000 Hz), generowana sprzętowo przez Timer0 na pinie OC0B (PB1). Rezonans głośnika z zabawki jest nieznany, więc agent dostarcza **osobny, mały firmware testowy**: krótkie tony 500, 1000, 1500, 2000, 2500, 3000 i 4000 Hz po 0,5 s. Użytkownik mówi, który brzmi najgłośniej, i agent wpisuje tę wartość do stałej.
- Jeśli głośność jest za cicha, agent może zmniejszyć rezystor szeregowy, ale **nie poniżej 27 Ω** (prąd szczytowy ok. 126 mA to maksimum rozsądne dla BC547A, który ma limit ciągły 100 mA i szczytowy 200 mA).
- Jeśli głośnik grzeje się albo rezystor jest ciepły po kilkunastu sygnałach, agent zwiększa rezystor lub skraca sygnał.

## Ograniczenia firmware

ATtiny13A ma **1024 B flash i 64 B RAM**, dlatego agent buduje firmware etapami i po każdym etapie podaje wynik `avr-size`; żaden etap nie może przekroczyć 1024 B flash ani zostawić mniej niż 12 B RAM na stos.

| Priorytet | Funkcja | Szacunek flash |
| --- | --- | --- |
| 1 (musi być) | Inicjalizacja OLED, programowy I2C, wyświetlanie cyfr M:SS | ok. 400–500 B |
| 1 | Logika stanów, odliczanie (Timer0), przyciski (run, ADC dla "+" i "−") | ok. 150–250 B |
| 1 | Sygnał dźwiękowy | ok. 30–50 B |
| 2 | Uśpienie długim "run" i wybudzenie | ok. 40–60 B |
| 3 (nice to have) | Znikająca ramka (pasek postępu) | ok. 80–120 B |
| 3 (nice to have) | Ikona dzwonka | ok. 40–80 B |
| 4 (opcja) | Auto-uśpienie po 60 s | ok. 15 B |

Szacunki są orientacyjne; agent zastępuje je zmierzonymi wartościami.

Technika i narzędzia:

- C, `avr-gcc -Os -mmcu=attiny13a`, `avr-libc`, `avrdude`, `Makefile`. Bez Arduino core i bibliotek.
- **Brak framebuffera** (512 B nie zmieści się w 64 B RAM): obraz jest liczony w locie i strumieniowany do OLED-a kolumna po kolumnie, strona po stronie (128×32 to 4 strony po 128 bajtów). Cyfry, ramka i dzwonek składane są per kolumna.
- Czcionka 5×7 tylko dla znaków 0–9 i dwukropka (ok. 55 B), skalowana programowo x3 (każdy bit kolumny powtarzany trzykrotnie w pionie). Cyfry mają wysokość co najmniej 20 px.
- Zegar: **9,6 MHz bez dzielnika** (fuse CKDIV8 wyłączony), wartość OSCCAL jako stała po kalibracji. Praca pełnym zegarem jest bezpieczna przy napięciu od 2,7 V, a bateria nie spada poniżej ok. 3,3 V w użyciu.
- Podstawą czasu jest Timer0 z oscylatora RC; **nie** watchdog (jego generator 128 kHz jest zbyt niedokładny). Podczas sygnału Timer0 służy tylko do tonu, bo odliczanie jest już skończone.
- Odliczanie bez dryfu: reszta z dzielenia zegara (liczyć całkowite tyki, nie zaokrąglać w każdej sekundzie). Cel: błąd poniżej 1% po kalibracji.
- Debounce przycisków programowo (ok. 20–30 ms), bez dodatkowych kondensatorów.
- Fuse'y: BOD wyłączony (mniejszy pobór w uśpieniu), SPIEN włączony, RSTDISBL i DWEN **pozostają niezmienione**. Agent podaje pełną wartość `lfuse` i `hfuse` wraz z komendą i wyjaśnieniem każdego bitu.

**Plan B.** Jeśli po wdrożeniu priorytetów 1–2 flash jest za ciasny, agent zgłasza to użytkownikowi i proponuje ATtiny25/45/85 (ten sam układ wyprowadzeń, to samo okablowanie; zmienia się tylko `-mmcu` i parametr `-p` w avrdude). Nie wycina po cichu funkcji.

## Kolejność prac i testy

Agent prowadzi użytkownika przez montaż **etapami**, a każdy etap kończy test z jednoznacznym wynikiem "działa / nie działa"; następny etap zaczyna się dopiero po przejściu poprzedniego, żeby błąd dawał się zlokalizować.

| Etap | Co robi agent i użytkownik | Test przejścia |
| --- | --- | --- |
| 0. Środowisko | Agent sprawdza, czy ma `avr-gcc`, `avr-libc`, `avrdude`; zadaje pytania blokujące (obudowa DIP-8, rozmiar płytki, tranzystor). | Kompilacja pustego programu dla attiny13a przechodzi, albo agent zgłasza brak narzędzi. |
| 1. Programator ISP | UNO z szkicem ArduinoISP, kondensator 10 µF RESET–GND na UNO, okablowanie do ATtiny na płytce. | `avrdude` odczytuje sygnaturę 0x1E 0x90 0x07. |
| 2. Fuse'y | Ustawienie 9,6 MHz bez dzielnika, BOD wyłączony; zapis. | Odczyt fuse'ów zgadza się z zaplanowanymi; ponowny odczyt sygnatury działa. |
| 3. Dźwięk | Montaż tranzystora, rezystorów i głośnika; wgranie firmware'u testowego tonu. | Użytkownik słyszy 7 tonów i wskazuje najgłośniejszy; tranzystor i rezystor nie grzeją się po 20 s ciągłego tonu. |
| 4. Wyświetlacz | Montaż OLED; firmware testowy inicjalizuje SSD1306 i rysuje "2:00" z ramką. | Obraz jest czytelny, nieodwrócony, bez przesunięcia. Jeśli nie, agent zmienia parametry inicjalizacji (konfiguracja pinów COM, multipleksowanie, odbicie segmentów). |
| 5. Przyciski | Montaż trzech przycisków i drabinki; firmware testowy pokazuje na ekranie odczyt ADC i stan "run". | Trzy przyciski są rozróżnialne; agent zapisuje zmierzone wartości ADC i dobiera progi. |
| 6. Firmware pełny, priorytety 1–2 | Odliczanie, "+" i "−", sygnał, uśpienie. | Wszystkie punkty z sekcji Kryteria odbioru, bez ramki i dzwonka. |
| 7. Nice to have | Ramka (pasek postępu), ikona dzwonka, opcjonalnie auto-uśpienie. | Jak wyżej, plus raport `avr-size` poniżej 1024 B; jeśli nie mieści się, patrz Plan B. |
| 8. Kalibracja czasu | Agent daje wersję z krótkim odliczaniem testowym; użytkownik porównuje je ze stoperem w telefonie, agent zmienia OSCCAL. | Błąd poniżej 1% na 10 minutach (poniżej 6 s). |
| 9. Dokumentacja końcowa | Kompletna instrukcja montażu, programowania, testów i diagnostyki. | Użytkownik potrafi zbudować układ od zera tylko z tej instrukcji. |

## Instrukcja montażu: wymagany format

Instrukcja jest pisana dla hobbysty z multimetrem, który nie zna układu: każdy krok to **jedna czynność z podanym adresem otworu**, a po każdym etapie jest sprawdzenie multimetrem lub test na urządzeniu.

Wymagania wobec instrukcji:

1. **Układ współrzędnych** opisany na początku: kolumny numerowane od lewej, rzędy a–e nad rowkiem środkowym i f–j pod nim, szyny zasilania opisane (plus, minus). Układ ma się zmieścić na płytce 400 otworów (30 kolumn).
2. **Lista zakupów i elementów** z ilościami i wartościami; dla każdego rezystora kod kolorów (np. 10 kΩ: brązowy-czarny-pomarańczowy) i polecenie zmierzenia go multimetrem przed wsadzeniem. Kondensator elektrolityczny i dioda: wyraźnie opisana polaryzacja.
3. **Każdy krok** w formacie: numer, element, z którego otworu do którego, kolor przewodu (czerwony = VCC, czarny = GND, pozostałe kolory stale przypisane do sygnałów), pole do odhaczenia. Bez opisów typu "w pobliżu" albo "obok układu".
4. **Rysunek płytki z góry po każdym etapie** (SVG lub PNG, z opisanymi kolumnami i rzędami), zgodny z adresami w krokach. Agent obejrzy wygenerowany rysunek, zanim go odda.
5. **Weryfikacja programowa**: agent buduje z listy kroków sieci połączeń (np. skryptem) i porównuje je ze schematem z sekcji Schemat i mapa pinów; wykrywa też dwa elementy w jednym otworze. Wynik (zgodne / lista różnic) trafia do raportu końcowego.
6. **Punkty kontrolne** po każdym etapie: ciągłość (które dwa punkty mają piszczeć), oczekiwane napięcia (np. 4,5 V między pinami 8 i 4, brak zwarcia między VCC i GND przed podłączeniem baterii) i co zrobić, gdy wynik jest inny.
7. **Ostrzeżenia** przy krokach ryzykownych, w szczególności:
   - kolejność pinów OLED: **VCC i GND różnią się między modułami**, więc użytkownik czyta opis na swoim module, a instrukcja nie zakłada kolejności z pamięci;
   - wyprowadzenia tranzystora BC547A to C-B-E (patrząc na płaską stronę, nóżkami w dół); agent każe sprawdzić nadruk na obudowie;
   - nigdy jednocześnie bateria i 5 V z Arduino;
   - przycisk tact: orientacja styków sprawdzona multimetrem przed wsadzeniem (w typowym przycisku połączone są styki po tej samej stronie), a przycisk łapi rowek środkowy;
   - ATtiny13A: pin 1 przy wcięciu na obudowie.
8. **Programowanie**: tabela połączeń UNO z ATtiny (z sekcji Schemat), kolejność czynności (wgranie ArduinoISP, kondensator 10 µF, wyjęcie przewodów SDA, SCL i bazy), gotowe komendy `avrdude` z opisem każdej flagi, nazwy portu dla Windows (COMx), Linuksa (/dev/ttyACM0) i macOS (/dev/cu.usbmodem\*), oraz powrót do zasilania baterią.
9. **Diagnostyka**: tabela "objaw, prawdopodobna przyczyna, co zmierzyć lub zmienić", co najmniej dla: odczyt sygnatury 0x00 lub 0xFF, pusty OLED, obraz lustrzany, brak dźwięku, przyciski reagują losowo, reset przy dźwięku, układ nie budzi się z uśpienia.
10. **Możliwość kontroli zdjęciem**: agent prosi użytkownika o zdjęcie płytki po ważnych etapach (po zasilaniu i ATtiny, po OLED) i porównuje je z rysunkiem.

Przykład formatu jednego etapu (adresy otworów poniżej to tylko ilustracja; agent wylicza własne):

```markdown
### Etap 3: głośnik
**Cel:** podłączyć głośnik przez tranzystor.
**Potrzebujesz:** tranzystor BC547A, rezystor 470 Ω (żółty-fioletowy-brązowy), rezystor 47 kΩ (żółty-fioletowy-pomarańczowy), rezystor 33 Ω (pomarańczowy-pomarańczowy-czarny), głośnik.

- [ ] 3.1 Tranzystor BC547A, płaska strona do Ciebie: nóżki w g20 (kolektor), g21 (baza), g22 (emiter).
- [ ] 3.2 Rezystor 470 Ω: od g6 (ta sama kolumna co pin 6 ATtiny, który siedzi w f6) do h21 (baza).
- [ ] 3.3 Przewód czarny: z j22 (emiter) do szyny minus.
- [ ] ...

**Sprawdzenie (bateria odłączona):** multimetr w trybie ciągłości, jedna sonda w j22, druga na szynie minus: musi piszczeć. Między szyną plus i minus nie może piszczeć.
```

## Kryteria odbioru

Projekt jest gotowy, gdy użytkownik przejdzie wszystkie poniższe testy na zmontowanym urządzeniu zasilanym z baterii 3×AAA, a agent dołączy raport z wynikami (tabela "test, wynik, uwagi").

| # | Test | Oczekiwany wynik |
| --- | --- | --- |
| 1 | Włożenie baterii lub wybudzenie | Ekran pokazuje 2:00 w ciągu 1 s. |
| 2 | Krótkie "run" w gotowości | Odliczanie rusza; co sekundę widoczne 1:59, 1:58, ... |
| 3 | "+" i "−" w trakcie odliczania | Brak jakiejkolwiek reakcji. |
| 4 | Krótkie "run" w trakcie odliczania | Odliczanie staje, ekran pokazuje 2:00 i nie rusza sam. |
| 5 | Pełny cykl 2:00 | Po ok. 120 s jeden sygnał (ok. 1 s), potem ekran 2:00. |
| 6 | "+" i "−" w gotowości | Każde kliknięcie zmienia o 1 minutę; zakres 1:00–60:00; "+" na 60:00 i "−" na 1:00 bez zmiany. |
| 7 | Odliczanie 10 minut ze stoperem | Różnica poniżej 6 s (1%). |
| 8 | Przytrzymanie "run" 2 s | OLED gaśnie, minutnik śpi. Pobór w uśpieniu zmierzony multimetrem i zapisany w raporcie (cel poniżej 100 µA; jeśli więcej, agent wskazuje, który element jest przyczyną). |
| 9 | Wybudzenie przyciskiem "run" | Ekran 2:00; to naciśnięcie nie uruchamia odliczania. |
| 10 | Ramka (nice to have) | Pełna na starcie, znika równomiernie, na 0:00 pusta. |
| 11 | Ikona dzwonka (nice to have) | Widoczna tylko w czasie sygnału. |
| 12 | Raport `avr-size` | Flash co najwyżej 1024 B, statyczny RAM co najwyżej 52 B (reszta to stos). |
| 13 | Instrukcja montażu | Weryfikacja sieci połączeń z listy kroków zgodna ze schematem. |

## Ryzyka i decyzje otwarte

Poniższe założenia agent przyjmuje domyślnie i opisuje w instrukcji; użytkownik może je zmienić w dowolnym momencie.

| Temat | Założenie domyślne | Gdy się nie sprawdzi |
| --- | --- | --- |
| Pamięć flash | Priorytety 1–2 mieszczą się w 1 KB, nice to have prawdopodobnie też. | Agent zgłasza wynik `avr-size` i proponuje ATtiny25/45/85 (ten sam układ pinów). |
| Moduł OLED | Adres 0x3C, 128×32, typowa inicjalizacja. | Etap 4 testuje obraz; agent koryguje adres, konfigurację COM i odbicie segmentów. |
| Moc głośnika | Mała (ok. 0,25 W). | Agent zostaje przy rezystorze 33 Ω i skraca sygnał lub zwiększa rezystor, jeśli element się grzeje. |
| Tranzystor BC547A | Użytkownik używa BC547A (prąd ciągły 100 mA, szczytowy 200 mA). | Jeśli dźwięk jest za cichy, agent obniża rezystor szeregowy najwyżej do 27 Ω; dalej pomaga już tylko trafienie w częstotliwość rezonansową (test tonów). |
| Czas sygnału | Jeden sygnał ok. 1 s ("krótki"). | Stała w kodzie; użytkownik podaje inną długość lub wzorzec (np. trzy krótkie). |
| Minimalny czas | 1:00 (użytkownik podał tylko maksimum 60 minut). | Użytkownik zmienia dolny zakres. |
| Start odliczania | Ekran pokazuje 2:00, po 1 s 1:59. | Zmiana jednej stałej. |
| Auto-uśpienie po 60 s | Opcjonalne, na końcu, o ile zmieści się we flash. | Użytkownik potwierdza lub rezygnuje. |
| Obudowa ATtiny13A i rozmiar płytki | DIP-8, płytka 400 otworów. | Agent prosi o potwierdzenie przed rysunkami. |
| System użytkownika | Nieznany, więc instrukcja podaje porty dla Windows, Linuksa i macOS. | Po odpowiedzi agent zostawia jedną wersję. |
| Brak dostępu do sprzętu | Agent nie może uruchomić układu. | Wszystkie testy wykonuje użytkownik i przekazuje wyniki; agent nie deklaruje, że coś "działa", dopóki nie ma wyniku testu. |
