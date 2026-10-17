# Minutnik na ATtiny13A

Firmware w czystym C (`avr-gcc -Os`, bez Arduino core), instrukcja montażu na płytce stykowej, programowanie przez Arduino UNO, kalibracja i testy odbiorcze. Materiały dla użytkownika są po polsku. Pełne podsumowanie, w tym co jest sprawdzone, a co nie: **[docs/raport-koncowy.md](docs/raport-koncowy.md)**.

| Co | Gdzie |
| --- | --- |
| Instrukcja montażu (kroki, adresy otworów, rysunki, sprawdzenia) | [docs/instrukcja-montazu.md](docs/instrukcja-montazu.md) |
| Programowanie: ArduinoISP, fuse'y, wgrywanie | [docs/programowanie.md](docs/programowanie.md) |
| Kalibracja czasu (OSCCAL) | [docs/kalibracja.md](docs/kalibracja.md) |
| Testy odbiorcze (tabela do wypełnienia) | [docs/testy-odbiorcze.md](docs/testy-odbiorcze.md) |
| Diagnostyka | [docs/diagnostyka.md](docs/diagnostyka.md) |
| Plan B: ATtiny25/45/85 z ramką i dzwonkiem | [docs/plan-b.md](docs/plan-b.md) |
| Netlista i mapa pinów | [docs/schemat.md](docs/schemat.md) |
| Gotowe pliki `.hex` i raport `avr-size` | `dist/` |
| Źródła firmware i `Makefile` | `firmware/` |
| Generator rysunków/instrukcji i weryfikacja sieci | `tools/breadboard/` |
| Symulacja logiki firmware na komputerze | `tools/sim/` |

## Szybki start

```bash
cd firmware
make                                    # buduje i drukuje rozmiary (avr-gcc z PATH lub z Arduino IDE)
make sig   PORT=/dev/cu.usbmodemXXXX    # Etap 1: sygnatura 0x1e9007 (ATtiny w gnieździe programatora)
make fuses PORT=/dev/cu.usbmodemXXXX    # Etap 2
make flash PROG=test_tone PORT=...      # Etapy 3-5: test_tone, test_display, test_buttons
make flash PROG=timer PORT=...          # Etap 6
```

Weryfikacja bez sprzętu:

```bash
tools/sim/run.sh                                 # logika minutnika (ATtiny13A)
SIM_FLAGS="-DFEATURE_BAR=1 -DFEATURE_BELL=1" tools/sim/run.sh   # plan B
SIM_TARGET=calib tools/sim/run.sh                # program kalibracyjny
cd tools/breadboard && python3 design.py && python3 test_design.py
```
