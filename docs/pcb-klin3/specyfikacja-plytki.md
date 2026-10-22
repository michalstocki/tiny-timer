# Płytka główna wariantu „klin 3” (bez wyświetlacza i przycisków): 40.0 × 24.0 mm

Wersja robocza, jeszcze nie do zamówienia. Dane maszynowe: `pcb-layout.json` (generowany `python3 tools/pcb/build.py --variant klin3`).
Układ współrzędnych: widok od strony TOP (od strony ścianki obudowy), początek w lewym dolnym rogu, +x w prawo, +y w górę, +y wskazuje wierzchołek obudowy. Laminat 1.6 mm; elementy stoją po stronie BOTTOM (do wnętrza obudowy), po stronie TOP są tylko lut i końcówki nóżek (do 2,0 mm).

Otwory montażowe M2,5 (Ø2.7): (3.5; 3.5), (36.5; 20.5).

| Ozn. | Element | Prostokąt (x0, y0, x1, y1) | Wysokość [mm] |
| --- | --- | --- | --- |
| U1 | ATtiny13A in DIP-8 socket | (10.4, 12.7, 20.8, 23.0) | 8.5 |
| R1 | 15 k | (7.8, 3.7, 13.2, 6.7) | 7.5 |
| R2 | 470 | (21.4, 18.8, 26.9, 21.8) | 7.5 |
| R3 | 47 k | (21.8, 8.9, 27.3, 11.9) | 7.5 |
| R4 | 33, 1/2 W | (23.7, 3.0, 32.8, 7.0) | 4.0 |
| R5 | 8.2 k | (14.1, 1.5, 19.6, 4.5) | 7.5 |
| R6 | 8.2 k | (30.5, 10.7, 33.5, 16.1) | 7.5 |
| C1 | 100 nF | (15.1, 5.0, 21.1, 9.4) | 6.0 |
| C2 | 100 nF | (3.8, 9.0, 8.2, 15.1) | 6.0 |
| C3 | 100 uF | (4.5, 15.4, 9.7, 20.4) | 8.0 |
| D1 | LED | (33.9, 5.5, 39.3, 10.8) | 8.7 |
| Q1 | BC547B | (22.2, 12.7, 27.1, 17.9) | 5.5 |
| SPK | speaker leads | (33.9, 11.1, 36.3, 16.1) | 0.0 |
| BAT | battery leads | (9.1, 7.1, 14.1, 9.5) | 0.0 |
| KEY | button board leads | (27.7, 8.8, 30.1, 21.6) | 0.0 |
| DISP | display module leads | (8.6, 10.0, 21.4, 12.3) | 0.0 |

Pola przewodów (wlutowane od strony elementów): DISP 1..4 = SDA, SCL, VCC, GND modułu wyświetlacza (żeńskie przewody Dupont na listwie pinów modułu); KEY 1..4 = GND, PB3, PB4, dolna strona S3 (płytka przycisków); SPK głośnik; BAT bateria.
