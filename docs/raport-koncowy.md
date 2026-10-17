# Raport końcowy

Stan: kod i dokumentacja gotowe; **żaden test na sprzęcie nie został wykonany** (agent nie ma dostępu do płytki). Poniżej jest to, co jest zweryfikowane na komputerze, i to, co musisz sprawdzić Ty.

## 1. Rozmiar firmware (zmierzony `avr-size`, avr-gcc 7.3.0 z Arduino IDE, `-Os -flto`)

| Program | ATtiny13A flash [B] | RAM statyczny [B] | Limit |
| --- | --- | --- | --- |
| `timer` (priorytety 1–2) | **1016** | **6** | 1024 / 52 |
| `timer` z `OSCCAL_VAL` | 1020 | 6 | 1024 / 52 |
| `test_tone` | 150 | 0 | |
| `test_display` | 672 | 6 | |
| `test_buttons` | 598 | 6 | |
| `calib` | 1018 | 6 | |

Pełny raport: `dist/avr-size.txt`. Stos ma ok. 58 B (64 − 6).

**Funkcje, które nie mieszczą się w 1024 B (decyzja Plan B z briefu, nie wycięte po cichu):** ikona dzwonka (+102 B → 1118), ramka postępu (+302 B → 1318), oba razem (nie linkuje się), auto-uśpienie po 60 s (1034 B). Dla nich: `docs/plan-b.md` (ATtiny25/45/85, ten sam układ pinów: 1420–1424 B, kompilacja zmierzona).

## 2. Co jest zweryfikowane

| Obszar | Jak | Wynik |
| --- | --- | --- |
| Kompilacja wszystkich programów (13A i plan B) | `make`, `tools/make_dist.sh` | przechodzi, bez ostrzeżeń |
| Logika minutnika | `tools/sim/run.sh`: kod firmware kompilowany bez zmian na komputerze, 7 scenariuszy, 54 sprawdzenia | wszystkie OK (start 2:00, ±, granice 1:00–60:00, odliczanie 120 kroków bez pominięć, sygnał 1 s, stop, uśpienie i wybudzenie także przy drganiu styków, 10:00 = 600,000 s dla idealnego zegara) |
| Protokół I2C | ta sama symulacja: dekodowanie START/STOP, bajtów, obrazu (OCR pikseli) | OK; piny SDA/SCL tylko jako otwarty dren |
| Plan B (ramka, dzwonek) | ta sama symulacja z `FEATURE_BAR/BELL` | OK |
| Program kalibracyjny | symulacja | OK |
| Sieć połączeń z kroków montażu = schemat z briefu | `tools/breadboard/design.py` (z elementami opcjonalnymi i bez) | **ZGODNE**, brak podwójnie zajętych otworów, geometria rezystorów i obudów poprawna |
| Czułość weryfikatora | 14 testów mutacyjnych (`test_design.py`) | wszystkie wykrywają błąd |
| Rysunki | wygenerowane z tych samych danych; obejrzane w przeglądarce | zgodne z adresami w krokach |

## 3. Czego NIE sprawdzono (do wykonania przez Ciebie)

Prawdziwa dokładność oscylatora, działanie OLED (inicjalizacja SSD1306 to typowa sekwencja, parametry `OLED_FLIP`, `OLED_COM_CFG`, `OLED_ADDR` są do dobrania w Etapie 4), głośność i grzanie, rzeczywisty prąd uśpienia, zachowanie przycisków i progów ADC, I2C na realnych pull-upach (magistrala ok. 220 kHz wg zliczenia cykli, nie z pomiaru), komendy `avrdude` z Twoją płytką programatora (zgodność okablowania gniazda z tabelą w programowanie.md). Wszystkie testy odbiorcze: [testy-odbiorcze.md](testy-odbiorcze.md) (kolumna „Wynik” pusta).

## 4. Błędy i niejasności w briefie (zgłoszone, nie poprawiane po cichu)

1. **Rezystory 10 kΩ:** brief wymienia „2× 10 kΩ”, a układ potrzebuje **3** (RESET, pull-up PB4, szereg przycisku „−”). Instrukcja zakłada 3.
2. **27 Ω ↔ 126 mA:** to wartość dla 4,5 V; przy 4,8 V wychodzi ok. 135 mA (dalej poniżej 200 mA szczytowo, ale powyżej „100 mA ciągłych” przy 100% wypełnienia; przy 50% średnio ok. 68 mA).
3. **Szacunki flash z briefu są zbyt optymistyczne:** priorytet 1–2 zajmuje 1016 B (brief: ok. 620–860 B). Sam zapas jest minimalny: kolejne zmiany w kodzie 13A mogą przekroczyć 1024 B.
4. **Fuse'y:** w briefie „RSTDISBL i DWEN pozostają niezmienione”; zgodnie z avr-libc dla ATtiny13A to bity 0 i 3 bajtu `hfuse` (nie bajtu low). Wymagany jest tylko `lfuse` 0x7A; `hfuse` zostaje 0xFF.
5. „Tranzystor pracuje w specyfikacji”: dotyczy wartości średniej (50% wypełnienia); prąd szczytowy 107–114 mA przekracza 100 mA „ciągłe” w impulsie, ale mieści się w 200 mA szczytowych.

## 5. Przyjęte założenia (zmień, jeśli nie pasują)

- ATtiny13A w obudowie **DIP-8** i płytka 400 otworów (30 kolumn): **potwierdzone przez użytkownika.**
- Adres OLED 0x3C, 128×32; sygnał 1 s na 2000 Hz (do wyboru testem tonów); minimalny czas 1:00; start odliczania: ekran 2:00, po 1 s 1:59.
- System: **macOS** (potwierdzone); instrukcja programowania zostaje przy portach `/dev/cu.usbmodem*`.
- **Programowanie poza układem:** użytkownik ma płytkę programatora z gniazdem DIP-8, UNO z ArduinoISP i kondensatorem 10 µF. Na płytce stykowej nie ma przewodów ISP, kondensatora 10 µF ani zasilania z UNO; zasilanie od Etapu 1 jest z baterii; po każdej zmianie programu ATtiny przechodzi między gniazdem a płytką (procedura w programowanie.md).
- Kolory przewodów i nazwy szyn (T+, T−, B+, B−) nadaje instrukcja; nadruki na płytce nie mają znaczenia.
- Progi przycisków: <25% VCC „+”, 25–75% „−”, powyżej „nic”; debounce 24 ms; długie przytrzymanie 2,0 s.

## 6. Zmiany względem szkicu briefu, wynikające z pomiarów

- Tyk Timera0 to **8 ms** (9,6 MHz / 1024 / 75), a nie 1 ms: dokładnie 125 tyków = 1 s, wszystkie liczniki 8-bitowe (oszczędność flash).
- OLED w trybie adresowania pionowego (strumień kolumnami), cyfry ×3 z fontu 5×7, centrowane; czas jest przechowywany jako cyfry dziesiętne (bez dzielenia).
- Zmienne gorące w rejestrach r2–r9 (`-ffixed-r2..r9`), kompilacja z `-flto -fno-split-wide-types` itp. — bez tego kod nie mieści się w 1 KB.

## 7. Co dalej

1. Zbuduj etapami wg instrukcji; po Etapie 1 i 4 pokaż zdjęcia płytki (porównam z rysunkami).
2. Podaj najgłośniejszy ton, odczyty ADC, wynik kalibracji; wpiszę stałe (`TONE_HZ`, progi, `OSCCAL_VAL`).
3. Jeśli chcesz ramkę i dzwonek: plan B (inny układ, to samo okablowanie).
