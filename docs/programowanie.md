# Programowanie ATtiny13A przez Arduino UNO (ISP)

Wszystkie komendy w tym dokumencie są **nieprzetestowane na Twoim sprzęcie** (agent nie ma dostępu do płytki): `make -n` potwierdza tylko, że składają się poprawnie. Wynik każdej komendy podaj mi, jeśli różni się od opisanego.

## 1. Co jest potrzebne

- Arduino UNO + kabel USB, Arduino IDE (jest u Ciebie zainstalowane; zawiera `avrdude`).
- Zbudowane pliki `.hex`: gotowe w katalogu `dist/attiny13a/`, albo `make` w katalogu `firmware/`.
- `avrdude`: `make` sam znajdzie `avrdude` z PATH, a jeśli go brak, użyje tego z Arduino IDE:
  `~/Library/Arduino15/packages/arduino/tools/avrdude/6.3.0-arduino17/bin/avrdude` z plikiem konfiguracji `.../etc/avrdude.conf`.

### Nazwa portu (parametr `-P` i `PORT=`)

macOS: `/dev/cu.usbmodemXXXX`. Sprawdź po podłączeniu UNO: `ls /dev/cu.usbmodem*`. (Na innych systemach byłoby to `COM3` w Windows lub `/dev/ttyACM0` w Linuksie, ale po Twojej odpowiedzi instrukcja zostaje przy macOS.)

## 2. Programator: Twoja płytka z gniazdem DIP-8

Masz gotowy układ: Arduino UNO z wgranym ArduinoISP, gniazdo DIP-8 na ATtiny oraz kondensator 10 µF RESET–GND na UNO. **ATtiny programujesz poza płytką stykową**, więc na płytce stykowej nie ma żadnych przewodów programatora ani kondensatora 10 µF.

Sprawdź jednorazowo, że gniazdo jest połączone z UNO tak:

| Arduino UNO | Pin ATtiny13A | Funkcja |
| --- | --- | --- |
| D10 | 1 (RESET) | RESET |
| D11 | 5 (PB0) | MOSI |
| D12 | 6 (PB1) | MISO |
| D13 | 7 (PB2) | SCK |
| 5V | 8 (VCC) | zasilanie |
| GND | 4 (GND) | masa |

Kondensator 10 µF: **+** do RESET UNO, **−** do GND. Przy ponownym wgrywaniu szkicu ArduinoISP do UNO kondensator trzeba odłączyć.

### Procedura wymiany układu (za każdym razem)

1. **Odłącz baterię** od płytki stykowej (czerwony przewód z T+30).
2. Wyjmij ATtiny z płytki stykowej równo (wyciągacz DIP albo mały śrubokręt podważany naprzemiennie z obu stron).
3. Włóż go do gniazda programatora **wcięciem w stronę oznaczoną na gnieździe** (pin 1 = strona RESET/D10). Jeśli gniazdo jest ZIF, zamknij dźwignię.
4. Podłącz UNO kablem USB, zaprogramuj (sekcje 3–5).
5. Odłącz USB, wyjmij ATtiny z gniazda i włóż go do płytki stykowej: **wcięcie po lewej, pin 1 w f11**.
6. Dopiero teraz wpnij baterię.

Nigdy nie trzymaj ATtiny jednocześnie w płytce stykowej z baterią i w gnieździe z USB (dwa źródła zasilania). Powtarzane wkładanie zagina nóżki: prostuj je i nie używaj układu po złamaniu nóżki.

## 3. Odczyt sygnatury (Etap 1, w gnieździe)

```bash
cd firmware
make sig PORT=/dev/cu.usbmodemXXXX
```

(równoważne: `avrdude -c stk500v1 -p t13 -P PORT -b 19200 -v`). Oczekiwany wynik: `Device signature = 0x1e9007`.

Opis flag: `-c stk500v1` protokół ArduinoISP, `-p t13` układ ATtiny13(A), `-P` port szeregowy, `-b 19200` prędkość portu UNO (zgodna ze szkicem ArduinoISP), `-v` więcej informacji.

**Gdy sygnatura to 0x000000 lub 0xFFFFFF:** zob. [diagnostyka.md](diagnostyka.md) (zwykle układ krzywo w gnieździe, odwrócony, złe okablowanie gniazda albo brak kondensatora 10 µF).

## 4. Fuse'y (Etap 2)

Domyślnie ATtiny13A pracuje z 9,6 MHz dzielonym przez 8 (1,2 MHz). Firmware wymaga **9,6 MHz bez dzielnika**.

```bash
make fuses PORT=/dev/cu.usbmodemXXXX
```

wykonuje `avrdude ... -U lfuse:w:0x7A:m` i odczytuje oba bajty (`-U lfuse:r:-:h -U hfuse:r:-:h`).

Wartości i znaczenie bitów (zgodnie z `avr/iotn13a.h` z avr-libc; bit zaprogramowany = 0):

| Bajt | Fabrycznie | Po zmianie | Zmiana |
| --- | --- | --- | --- |
| `lfuse` | **0x6A** | **0x7A** | CKDIV8 (bit 4) z 0 na 1 = dzielnik wyłączony |
| `hfuse` | **0xFF** | **0xFF** | bez zmian |

`lfuse` 0x7A = `0111 1010`:

| Bit | Nazwa | Wartość | Znaczenie |
| --- | --- | --- | --- |
| 7 | SPIEN | 0 (zaprogramowany) | programowanie ISP włączone — musi tak zostać |
| 6 | EESAVE | 1 | EEPROM kasowany przy kasowaniu układu |
| 5 | WDTON | 1 | watchdog nie jest włączony na stałe |
| 4 | CKDIV8 | **1** | **brak dzielenia zegara przez 8 → 9,6 MHz** |
| 3,2 | SUT1,SUT0 | 1,0 | start 14 CK + 64 ms |
| 1,0 | CKSEL1,CKSEL0 | 1,0 | wewnętrzny oscylator 9,6 MHz |

`hfuse` 0xFF = `1111 1111`: RSTDISBL (bit 0) = 1 (**pin RESET zostaje RESET-em; nigdy go nie programuj**: układ przestałby być programowalny bez programatora wysokonapięciowego), BODLEVEL1:0 (bity 2:1) = 11 → **BOD wyłączony** (mniejszy pobór), DWEN (bit 3) = 1 (debugWIRE wyłączony), SELFPRGEN (bit 4) = 1 (wyłączony).

Weryfikacja: odczyt musi dać `lfuse = 0x7a`, `hfuse = 0xff`; potem ponownie `make sig` — sygnatura musi się dalej odczytywać.

## 5. Wgrywanie programu

```bash
make                       # buduje wszystko do firmware/build/ i drukuje avr-size
make flash PROG=test_tone PORT=/dev/cu.usbmodemXXXX     # Etap 3
make flash PROG=test_display PORT=...                    # Etap 4
make flash PROG=test_buttons PORT=...                    # Etap 5
make flash PROG=timer PORT=...                           # Etap 6, firmware docelowy
make flash PROG=calib PORT=...                           # Etap 8
```

`make flash` wykonuje `avrdude -c stk500v1 -b 19200 -p t13 -P PORT -U flash:w:build/<PROG>.hex:i` (zapis + automatyczna weryfikacja). Komunikat `verified` oznacza zgodność.

Parametry przekazywane przy budowie: `make flash PROG=timer TONE_HZ=2500 OSCCAL_VAL=0x5A BEEP_MS=800 PORT=...` (po zmianie parametrów zrób `make clean`).

## 6. Po programowaniu

Wróć do procedury wymiany układu (sekcja 2): ATtiny z powrotem w płytkę stykową, wcięcie po lewej, na końcu bateria.

## Lista kontrolna przed programowaniem

- [ ] bateria odłączona od płytki stykowej
- [ ] ATtiny w gnieździe programatora, wcięcie zgodnie z gniazdem
- [ ] UNO z ArduinoISP, kondensator 10 µF wpięty, USB wpięte
- [ ] `make sig` zwraca `0x1e9007`
