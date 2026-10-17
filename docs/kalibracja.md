# Kalibracja czasu (OSCCAL), Etap 8

Wewnętrzny oscylator RC ATtiny13A jest dokładny tylko do kilku procent i zależy od egzemplarza, napięcia i temperatury (dokładnych granic nie podaję z pamięci; sprawdź w nocie katalogowej). Cel: **błąd poniżej 1% na 10 minutach (poniżej 6 s)**.
Minutnik liczy czas w całkowitych tykach 8 ms z Timera0 (125 tyków = 1 s, bez dryfu), więc cały błąd pochodzi z częstotliwości oscylatora. Rejestr `OSCCAL` ją koryguje.

Wartości liczbowe poniżej (krok OSCCAL, wpływ napięcia) **zmierzysz sam** — nie podaję ich z pamięci.

## Procedura

1. Zasilanie: **bateria** (tej samej klasy, w jakiej będzie pracował minutnik, czyli ok. 4,5 V). Napięcie wpływa na częstotliwość, dlatego nie kalibruj na 5 V z UNO.
2. Wgraj program kalibracyjny: `make flash PROG=calib PORT=...` (potem przejdź na baterię).
3. Ekran pokazuje `:NNN` — aktualną wartość OSCCAL (po resecie jest to wartość fabryczna ATtiny; **zapisz ją**: ______).
4. Przygotuj stoper w telefonie. Naciśnij **„run”** i w chwili puszczenia przycisku uruchom stoper. Ekran liczy w górę od 0:00; po **10:00** program piszczy 1 s i wraca do ekranu OSCCAL.
   Do szybkich prób możesz zbudować krótszy test: `make clean && make calib CAL_MIN=2` (2 minuty).
5. W chwili piknięcia zatrzymaj stoper. Zapisz czas telefonu T.
6. Oblicz błąd: **e = (T − 600 s) / 600 s**.
   - T > 600 s: układ idzie **za wolno** → zwiększ OSCCAL („+”).
   - T < 600 s: układ idzie **za szybko** → zmniejsz OSCCAL („−”).
7. Zmień OSCCAL klawiszami „+” / „−” (zmiana jest od razu zastosowana, ekran pokazuje nową wartość) i powtórz od punktu 4. Szukaj wartości, dla której |T − 600| < 6 s. Zapisuj w tabeli:

| OSCCAL | T (telefon) | błąd [s] | błąd [%] |
| --- | --- | --- | --- |
| ___ | ______ | ___ | ___ |
| ___ | ______ | ___ | ___ |
| ___ | ______ | ___ | ___ |

   Jak bardzo jeden krok OSCCAL zmienia częstotliwość, wyjdzie z Twoich pomiarów (porównaj dwa sąsiednie kroki); nie zakładam z góry tej wartości. Jeśli dwa sąsiednie kroki dają błąd o przeciwnych znakach, wybierz ten o mniejszym module.
8. Wpisz wynik do firmware i wgraj go:
   ```bash
   make clean
   make flash PROG=timer OSCCAL_VAL=<wartość dziesiętna lub 0x..> PORT=...
   ```
   Uwaga: stała powiększa kod o ok. 4 B (1016 → 1020 B z 1024).
9. **Test końcowy:** timer 10:00 ze stoperem. Wynik zapisz w [testy-odbiorcze.md](testy-odbiorcze.md) (test 7). Wymagane: różnica poniżej 6 s.

## Uwagi

- Kalibracja jest ważna dla napięcia i temperatury, przy których ją zrobiono. W całym zakresie baterii (4,8 → 3,3 V) oscylator RC przesunie się o ułamek procenta do kilku procent; jeśli to ma znaczenie, kalibruj przy napięciu pośrednim (ok. 4,0–4,2 V, czyli lekko zużyte baterie) i podaj mi odczyty dla świeżych i zużytych.
- Pomiar stoperem z reakcją człowieka ma błąd ok. ±0,3 s: dla 600 s to 0,05%, więc 10 minut wystarcza.
- Program kalibracyjny używa tej samej podstawy czasu (`timebase.h`) co minutnik, więc wynik przenosi się 1:1.
