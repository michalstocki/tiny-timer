# Programowanie ATtiny13A przez Arduino UNO (ISP)

Wszystkie komendy w tym dokumencie są **nieprzetestowane na Twoim sprzęcie** (agent nie ma dostępu do płytki): `make -n` potwierdza tylko, że składają się poprawnie. Wynik każdej komendy podaj mi, jeśli różni się od opisanego.

## 1. Co jest potrzebne

- Arduino UNO + kabel USB, Arduino IDE (jest u Ciebie zainstalowane; zawiera `avrdude`).
- Zbudowane pliki `.hex`: gotowe w katalogu `dist/attiny13a/`, albo `make` w katalogu `firmware/`.
- `avrdude`: `make` sam znajdzie `avrdude` z PATH, a jeśli go brak, użyje tego z Arduino IDE:
  `~/Library/Arduino15/packages/arduino/tools/avrdude/6.3.0-arduino17/bin/avrdude` z plikiem konfiguracji `.../etc/avrdude.conf`.

### Nazwa portu (parametr `-P` i `PORT=`)

macOS: `/dev/cu.usbmodemXXXX`. Sprawdź po podłączeniu UNO: `ls /dev/cu.usbmodem*`. (Na innych systemach byłoby to `COM3` w Windows lub `/dev/ttyACM0` w Linuksie, ale po Twojej odpowiedzi instrukcja zostaje przy macOS.)

## 2. Arduino UNO jako programator (jednorazowo)

1. Podłącz UNO kablem USB. **Na razie nic więcej nie jest do niego podłączone** (zwłaszcza kondensator 10 µF).
2. Arduino IDE → *Plik → Przykłady → 11.ArduinoISP → ArduinoISP*.
3. Narzędzia → Płytka: *Arduino Uno*, Port: ten z UNO. Kliknij *Wgraj*.
4. Po wgraniu odłącz kabel USB.
5. Dopiero teraz wpnij kondensator 10 µF (krok z Etapu 1 w [instrukcji montażu](instrukcja-montazu.md)): **+** do RESET UNO, **−** do GND. Zapobiega on automatycznemu resetowaniu UNO przy otwarciu portu przez `avrdude`. Żeby wgrać ArduinoISP ponownie, kondensator trzeba wyjąć.

## 3. Okablowanie i odczyt sygnatury (Etap 1)

| Arduino UNO | ATtiny13A | Funkcja |
| --- | --- | --- |
| D10 | pin 1 (RESET) | RESET |
| D11 | pin 5 (PB0) | MOSI |
| D12 | pin 6 (PB1) | MISO |
| D13 | pin 7 (PB2) | SCK |
| 5V | pin 8 (VCC) | zasilanie (przez szynę plus) |
| GND | pin 4 (GND) | masa |

Adresy otworów są w Etapie 1 instrukcji montażu. **Bateria odłączona.** Na czas programowania wyjmij też żółty przewód z b12, zielony z b14 i jedną nóżkę R2 (później, gdy te elementy będą już wmontowane).

```bash
cd firmware
make sig PORT=/dev/cu.usbmodemXXXX
```

(równoważne: `avrdude -c stk500v1 -p t13 -P PORT -b 19200 -v`). Oczekiwany wynik: `Device signature = 0x1e9007`.

Opis flag: `-c stk500v1` protokół ArduinoISP, `-p t13` układ ATtiny13(A), `-P` port szeregowy, `-b 19200` prędkość portu UNO (zgodna ze szkicem ArduinoISP), `-v` więcej informacji.

**Gdy sygnatura to 0x000000 lub 0xFFFFFF:** zob. [diagnostyka.md](diagnostyka.md) (zwykle zły kabel/zamienione MOSI/MISO, brak masy, brak pull-upu RESET lub kondensatora 10 µF).

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

## 6. Przejście na zasilanie z baterii

1. Odłącz kabel USB od UNO.
2. Wyjmij z płytki **wszystkie** przewody programatora (D10–D13, 5V, GND, RESET UNO, kondensator 10 µF).
3. Wpięty ma być OLED (żółty b12, zielony b14), R2 włożony na miejsce.
4. Dopiero teraz wpnij baterię (T+30, T−30). **Nigdy jednocześnie bateria i 5 V z UNO.**

## Lista kontrolna trybu programowania

- [ ] bateria wyjęta, USB wpięte
- [ ] kondensator 10 µF wpięty (ArduinoISP już wgrany)
- [ ] 6 przewodów ISP wpiętych zgodnie z tabelą
- [ ] żółty przewód OLED wyjęty z b12, zielony z b14, jedna nóżka R2 wyjęta (jeśli już są)
- [ ] `make sig` zwraca `0x1e9007`
