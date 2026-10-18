# Diagnostyka

Tabela: objaw → prawdopodobna przyczyna → co zmierzyć lub zmienić. Adresy otworów dotyczą [instrukcji montażu](instrukcja-montazu.md).

| Objaw | Prawdopodobna przyczyna | Co zmierzyć / zmienić |
| --- | --- | --- |
| `avrdude`: sygnatura **0x000000** | układ krzywo lub odwrotnie w gnieździe programatora, zagięta nóżka, zła obudowa (SOIC-8) | Wyjmij i włóż ATtiny ponownie (wcięcie zgodnie z gniazdem), sprawdź nóżki. Zmierz 5,0 V między pinami 8 i 4 w gnieździe. Sprawdź okablowanie gniazda względem tabeli w programowanie.md. |
| Sygnatura **0xFFFFFF** | brak połączenia MISO (D12→pin 6) albo RESET (D10→pin 1) w gnieździe | Piszczenie D12→pin 6 i D10→pin 1 gniazda. Zmierz napięcie na pinie 1 w trakcie odczytu. |
| `not in sync` / `programmer is not responding` | w UNO nie ma szkicu ArduinoISP, zły port, brak kondensatora 10 µF RESET–GND | Sprawdź `-P` (`ls /dev/cu.usbmodem*`). Kondensator ma być wpięty przy programowaniu, a odpięty tylko przy wgrywaniu ArduinoISP do UNO. |
| Sygnatura OK, a po zapisie fuse'ów nie odpowiada | błędny `lfuse` (np. zewnętrzny zegar) | Nie zapisuj innych wartości niż 0x7A. Układ można odzyskać tylko zegarem zewnętrznym na pinie 2. Nigdy nie programuj RSTDISBL. |
| **Pusty OLED** | zły adres (0x3D), VCC/GND zamienione, SDA/SCL zamienione, brak zasilania, niewłożone przewody b12/b14 | Zmierz 4,5–5 V na VCC modułu. Sprawdź piszczeniem i23→b12 i i26→b14. Zbuduj z `OLED_ADDR=0x3D`. Przejrzyj kolejność pinów modułu z nadruku. |
| Obraz **lustrzany / do góry nogami** | inny kierunek skanowania modułu | `make OLED_FLIP=0` |
| Co druga linia / obraz „rozciągnięty” | konfiguracja COM pins | `make OLED_COM_CFG=0x12` |
| Obraz przesunięty | moduł z kontrolerem SH1106 lub 128×64 w obudowie 128×32 | Napisz, co widzisz (zdjęcie); dobiorę inicjalizację. |
| Pomiar baza–masa pokazuje ok. 0 Ω przy włożonym tranzystorze | złącze baza–emiter przewodzi przy czerwonej sondzie na bazie (to nie zwarcie) | Zmierz z czerwoną sondą na T−, albo przy wyjętym Q1: ma być ok. 47 kΩ. Tranzystor sprawdź w trybie diody (instrukcja, etap 3). |
| **Brak dźwięku** | tranzystor odwrotnie (C-B-E), R2 nie włożony, głośnik nie w c26/c27, nie wgrany `test_tone` | Piszczenie d13↔d20 ≈ 470 Ω, d20↔T− ≈ 47 kΩ, e22↔e27 ≈ 33 Ω. Napięcie DC na kolektorze w trakcie tonu: wartość pośrednia. |
| Dźwięk bardzo cichy | częstotliwość poza rezonansem głośnika; mały głośnik | Wybierz najgłośniejszy ton z testu; można zmniejszyć R4 nie niżej niż 27 Ω (prąd szczytowy ok. 126 mA przy 4,5 V). |
| Tranzystor / rezystor gorący | zbyt długi sygnał, zły R4, zwarcie | Skróć `BEEP_MS`, sprawdź R4 = 33 Ω. |
| **Przyciski reagują losowo** | para styków przycisku w poprzek rowka, brak R5, kontakt w płytce | Piszczenie wg Etapu 5; zmierz napięcie na pinie 3 (kolumna 13, np. h13): ok. 4,5 V bez nacisku, ok. połowy przy „−”, 0 przy „+”. `test_buttons` pokaże odczyt ADC. |
| „+” działa jak „−” lub odwrotnie | R6 w złej kolumnie / zamienione przewody | Zmierz R6 (b3↔b6) i przewód g3↔g13. |
| **Reset przy dźwięku** (ekran gaśnie, restart) | spadek napięcia przy prądzie głośnika, słabe baterie, brak 100 µF | Sprawdź C3 (T+24/T−24, polaryzacja), świeże baterie. Zmierz napięcie baterii podczas tonu (nie niżej niż 3,3 V). Zwiększ R4. |
| **Nie budzi się z uśpienia** | przycisk „run” nie dochodzi do pinu 2, GIMSK/PCINT, zbyt słaba bateria | Piszczenie g9↔h12 i h12↔pin 2 (f12). Zmierz napięcie na pinie 2 w uśpieniu: ok. 4,5 V (pull-up wewnętrzny). |
| Budzi się natychmiast / od razu usypia | drgania styków przy puszczaniu | Opisane i obsłużone w firmware (30 ms stabilnego puszczenia); jeśli się powtarza, zmierz R1/R5 i szukaj kontaktu pośredniego w przycisku. |
| Pobór w uśpieniu > 100 µA | moduł OLED nie ma trybu niskiego poboru, dioda na module, LED w układzie | Odłączaj po kolei: OLED (VCC), potem inne; patrz test 8. |
| Czas odmierza za szybko/wolno | oscylator RC | [kalibracja.md](kalibracja.md). |
| Ekran „sypie się” podczas odliczania | zbyt długie przewody SDA/SCL, brak pull-upów | Zamontuj R7/R8 (4,7 kΩ); skróć przewody. |
