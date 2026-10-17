# Testy odbiorcze

Wszystkie testy wykonuje **użytkownik** na zmontowanym urządzeniu zasilanym z baterii 3×AAA. Kolumna „Wynik” jest pusta, dopóki nie podasz wyniku: agent nie ma dostępu do sprzętu i **nie deklaruje, że coś działa**, dopóki nie dostanie wyniku testu.
„Symulacja” = test logiki firmware na komputerze (`tools/sim/run.sh`): to nie jest dowód działania sprzętu (zegar, OLED, głośnik, przyciski).

| # | Test | Oczekiwany wynik | Symulacja (host) | Wynik | Uwagi |
| --- | --- | --- | --- | --- | --- |
| 1 | Włożenie baterii lub wybudzenie | Ekran pokazuje 2:00 w ciągu 1 s | OK: pierwsza ramka po ok. 111 ms | | |
| 2 | Krótkie „run” w gotowości | Odliczanie rusza; co sekundę 1:59, 1:58, … | OK: 120 ramek 1:59…0:00 bez pominięć | | |
| 3 | „+” i „−” w trakcie odliczania | Brak jakiejkolwiek reakcji | OK | | |
| 4 | Krótkie „run” w trakcie odliczania | Odliczanie staje, ekran 2:00 i nie rusza sam | OK | | |
| 5 | Pełny cykl 2:00 | Po ok. 120 s jeden sygnał (ok. 1 s), potem ekran 2:00 | OK (sygnał 1000 ms, jeden) | | |
| 6 | „+” i „−” w gotowości | Zmiana o 1 min; zakres 1:00–60:00; „+” na 60:00 i „−” na 1:00 bez zmiany | OK (61×„+” i 62×„−”) | | |
| 7 | Odliczanie 10 minut ze stoperem | Różnica poniżej 6 s (1%) | tylko dla idealnego zegara: 600,000 s | | po kalibracji ([kalibracja.md](kalibracja.md)) |
| 8 | Przytrzymanie „run” 2 s | OLED gaśnie, minutnik śpi; pobór w uśpieniu (cel < 100 µA) | OK: komendy 0xAE, 0x8D 0x10, ADC i Timer0 wyłączone, tylko PCINT3 | | zmierzony pobór: ______ µA |
| 9 | Wybudzenie przyciskiem „run” | Ekran 2:00; to naciśnięcie nie uruchamia odliczania | OK (także przy drganiu styków) | | |
| 10 | Ramka (opcjonalnie) | Pełna na starcie, znika równomiernie, na 0:00 pusta | **ATtiny13A: niedostępne** (brak miejsca); plan B: OK w symulacji | | |
| 11 | Ikona dzwonka (opcjonalnie) | Widoczna tylko w czasie sygnału | **ATtiny13A: niedostępne**; plan B: OK w symulacji | | |
| 12 | Raport `avr-size` | Flash ≤ 1024 B, statyczny RAM ≤ 52 B | OK: **1016 B** flash, **6 B** RAM (zmierzone) | | |
| 13 | Instrukcja montażu | Weryfikacja sieci z listy kroków zgodna ze schematem | OK: wynik w [instrukcja-montazu.md](instrukcja-montazu.md) | | |

## Jak zmierzyć pobór w uśpieniu (test 8)

1. Wyjmij jedną nóżkę baterii (np. przewód + z T+30), włącz między nią a szynę amperomierz (zakres µA lub mA, w zależności od multimetru).
2. Włącz urządzenie (amperomierz w obwodzie może zakłócać start: zmostkuj go na czas startu), potem przytrzymaj „run” 2 s i odczytaj prąd po ok. 5 s.
3. Jeśli prąd przekracza 100 µA, rozłącz kolejno i mierz: (a) moduł OLED (przewód VCC; wiele modułów ma w środku stały pobór regulatora/diody), (b) dioda LED, (c) R1, R5 (pull-upy nie pobierają prądu, ale sprawdź zwarcia). Z reguły to **moduł OLED** jest przyczyną.
