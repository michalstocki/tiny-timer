# Schemat połączeń (netlista) i mapa pinów

## Mapa pinów ATtiny13A (DIP-8, wcięcie po lewej)

| Pin | Port | Funkcja w minutniku | Połączenie | Rola w gnieździe programatora |
| --- | --- | --- | --- | --- |
| 1 | PB5 / RESET | wolny | 15 kΩ (R1) do VCC | RESET (UNO D10) |
| 2 | PB3 | przycisk „run” | przycisk do GND, wewnętrzny pull-up; PCINT3 budzi z uśpienia | — |
| 3 | PB4 (ADC2) | przyciski „+” i „−” | drabinka: R5 8,2 kΩ do VCC; „+” do GND; „−” przez R6 8,2 kΩ do GND (R5 = R6) | — |
| 4 | GND | masa | minus baterii | GND |
| 5 | PB0 | SDA (I2C programowy) | SDA modułu OLED | MOSI (UNO D11) |
| 6 | PB1 (OC0B) | głośnik | R2 470 Ω do bazy Q1 | MISO (UNO D12) |
| 7 | PB2 | SCL (I2C programowy) | SCL modułu OLED | SCK (UNO D13) |
| 8 | VCC | zasilanie | plus baterii (4,5 V) | 5 V z UNO |

## Netlista (element, pin, do czego)

| Sieć | Piny |
| --- | --- |
| VCC | U1.8, R1.2, R5.2, R4.2, C1.+, C2.+, C3.+, OLED VCC, bateria + (opcj.: R7.2, R8.2) |
| GND | U1.4, Q1.E, R3.2, S1 (para górna), S2 (para górna), R6.2, C1.−, C2.−, C3.−, OLED GND, bateria − |
| RESET (pin 1) | U1.1, R1.1 |
| PB3 (pin 2) | U1.2, S1 (para dolna) |
| PB4 (pin 3) | U1.3, R5.1, S2 (para dolna), S3 (para dolna) |
| „−” do masy | S3 (para górna), R6.1 |
| SDA (pin 5) | U1.5, OLED SDA (opcj.: R7.1) |
| SCL (pin 7) | U1.7, OLED SCL (opcj.: R8.1) |
| PB1 (pin 6) | U1.6, R2.1 |
| baza | R2.2, Q1.B, R3.1 (47 kΩ do GND) |
| kolektor | Q1.C, głośnik (wyprowadzenie B), D1.A (anoda) |
| strona rezystora | głośnik (wyprowadzenie A), D1.K (katoda), R4.1 (33 Ω) |

Elementy: R1 = 15 kΩ; R5, R6 = 8,2 kΩ (jednakowe); R2 = 470 Ω; R3 = 47 kΩ; R4 = 33 Ω ½ W; R7, R8 = 4,7 kΩ (tylko gdy moduł OLED nie ma pull-upów); C1, C2 = 100 nF; C3 = 100 µF; C4 = 10 µF (tylko dla UNO jako ISP); Q1 = BC547A; D1 = dioda LED; S1 = „run”, S2 = „+”, S3 = „−”.

Netlista jest zapisana maszynowo w `tools/breadboard/design.py` (`REF_WORK`, `REF_ISP`) i porównywana z krokami montażu.

## Obliczenia głośnika (sprawdzone ponownie)

Prąd szczytowy `(U − 0,3 V) / (6,4 Ω + 33 Ω)`, moc przy wypełnieniu 50%:

| U | I szczyt | P głośnik | P rezystor |
| --- | --- | --- | --- |
| 4,8 V | 114 mA | 42 mW | 215 mW |
| 4,5 V | 107 mA | 36 mW | 188 mW |
| 3,3 V | 76 mA | 19 mW | 96 mW |

Wartości z briefu się zgadzają. Uwaga: „27 Ω → ok. 126 mA” dotyczy 4,5 V; przy świeżych bateriach 4,8 V wychodzi ok. 135 mA.
