# Plan B: ATtiny25 / 45 / 85 (ramka postępu i ikona dzwonka)

## Dlaczego

Na ATtiny13A (1024 B flash) mieszczą się priorytety 1–2 (**1016 B** zmierzone przez `avr-size`). Funkcje opcjonalne **nie** mieszczą się (pomiar, ten sam kod, `avr-gcc` 7.3.0 `-Os`):

| Wariant (ATtiny13A) | Flash [B] | Mieści się w 1024 B? |
| --- | --- | --- |
| priorytety 1–2 (domyślny) | 1016 | tak |
| + ikona dzwonka | 1118 | nie |
| + ramka (pasek postępu) | 1318 | nie |
| + ramka i dzwonek | > 1024 (nie linkuje się) | nie |
| + auto-uśpienie po 60 s | 1034 | nie |

Brief każe w takiej sytuacji nie wycinać funkcji po cichu, tylko zgłosić to i zaproponować ATtiny25/45/85. Domyślny firmware na ATtiny13A jest kompletny dla priorytetów 1–2.

## Co dostajesz

Ten sam kod (`firmware/src`) buduje się dla ATtiny25/45/85 z włączoną ramką i dzwonkiem: `make planb MCU_B=attiny85` (gotowe pliki w `dist/planb-attiny25|45|85/`).

| Układ | Flash [B] | RAM statyczny [B] |
| --- | --- | --- |
| ATtiny25 | 1420 z 2048 | 15 |
| ATtiny45 | 1424 z 4096 | 15 |
| ATtiny85 | 1424 z 8192 | 15 |

Wyprowadzenia i okablowanie są **identyczne** jak dla ATtiny13A (DIP-8, te same funkcje pinów), więc płytka z instrukcji montażu się nie zmienia. Zmieniają się tylko:

- zegar: wewnętrzny oscylator **8 MHz** (nie 9,6 MHz), firmware dobiera tyk 8 ms automatycznie (`F_CPU=8000000`);
- fuse'y: `lfuse` = **0xE2** (8 MHz, bez dzielnika; fabrycznie 0x62), `hfuse` bez zmian **0xDF** (RSTDISBL i DWEN nie zmieniać; BOD wyłączony: BODLEVEL = 111), `efuse` 0xFF;
- `avrdude -p t25` / `t45` / `t85` (sygnatury: 0x1E 0x91 0x08, 0x1E 0x92 0x06, 0x1E 0x93 0x0B);
- wgrywanie: użyj gotowych plików z `dist/planb-attiny85/` (po `make planb` pliki są też w `firmware/build-attiny85/`), np.:
  `avrdude -c stk500v1 -b 19200 -p t85 -P PORT -U flash:w:dist/planb-attiny85/timer.hex:i`.

## Weryfikacja

- Kompiluje się (pomiary powyżej).
- Logika i obraz ramki/dzwonka sprawdzone symulacją na komputerze (`SIM_FLAGS="-DFEATURE_BAR=1 -DFEATURE_BELL=1" tools/sim/run.sh`): liczba zapalonych pikseli ramki = ⌈316 · pozostały czas / czas całkowity⌉ w każdej sekundzie, ramka pusta na 0:00, dzwonek tylko podczas sygnału.
- **Nie** sprawdzone na sprzęcie (agent nie ma ATtiny25/45/85). Układ pinów OC0B, ADC2 i PCINT3 jest taki sam jak w ATtiny13A wg dokumentacji; wynik testów odbiorczych 10 i 11 musisz podać Ty.
- Ramka: numerowanie pikseli zgodnie z ruchem wskazówek od lewego górnego rogu; gaśnie od lewego górnego rogu zgodnie z ruchem wskazówek (zapalone są piksele o największych numerach).
