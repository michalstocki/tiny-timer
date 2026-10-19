#!/usr/bin/env python3
"""Generates docs/obudowa/specyfikacja-dla-agenta.md from the PCB data."""
import os

import board as B


def f(v, n=1):
    return ("%." + str(n) + "f") % v


def build():
    W, H, T = B.P["W"], B.P["H"], B.P["thickness"]
    o = B.body_rect("OLED")
    gx0 = B.D["oled_pin_x"] + B.P["glass_to_pin"]
    gy0 = B.D["oled_cy"] - B.P["glass_h"] / 2
    KL = B.VARIANT == "klin"
    DIR = "docs/pcb-klin" if KL else "docs/pcb"
    L = []
    w = L.append
    wb = (lambda *a, **k: None) if KL else w       # button text only in the base variant
    w("# Specyfikacja techniczna płytki dla agenta projektującego obudowę (%s)" % (
        "wariant „klin”: płytka główna bez przycisków" if KL else "iteracja 1"))
    w("")
    w("Dokument opisuje wyłącznie **fizyczne i mechaniczne** wymagania płytki: wymiary, położenie elementów, wysokości, strefy zakazane, tolerancje. "
      "Wygląd obudowy, głośnik i koszyk baterii zostaną dodane przez właściciela projektu w osobnych sekcjach (patrz „Miejsce na wizję właściciela”).")
    w("")
    if KL:
        w("**To jest wariant równoległy** do podstawowej płytki z `docs/pcb/` (tam przyciski są na płytce głównej). Tu przyciski są na **osobnej małej płytce** "
          "(52 × 16 mm, patrz `pcb-layout.json`, klucz `button_board`), a płytka główna jest krótsza. Oba warianty rozwijamy osobno. Źródłem prawdy są pliki w tym katalogu, "
          "w katalogu `%s/`, generowane poleceniem `python3 tools/pcb/build.py --variant klin`:" % DIR)
    else:
        w("**To jest pierwsza iteracja.** Wymiary płytki i położenia elementów mogą się zmienić w kolejnych iteracjach. Źródłem prawdy są pliki w tym katalogu, "
          "w katalogu `docs/pcb/`, generowane skryptem `tools/pcb/build.py`:")
    w("")
    w("| Plik | Do czego |")
    w("| --- | --- |")
    w("| `pcb-layout.json` | wszystkie współrzędne (mm): zarys, otwory, elementy, pady, wysokości, sieci |")
    w("| `pcb_params.scad` | te same wartości jako zmienne OpenSCAD (zarys, otwory, prostokąty elementów z wysokościami) |")
    w("| `pcb-przod.svg`, `pcb-tyl.svg` | podgląd płytki z przodu i od tyłu (z wstępnym trasowaniem) |")
    w("| `pcb-przekroj.svg` | wysokości elementów w przekroju bocznym |")
    w("| `podglad-3d.html` | interaktywny podgląd 3D (przeglądarka, wymaga internetu dla three.js) |")
    w("")
    w("Zalecany sposób pracy: parametryczny model (OpenSCAD albo CadQuery) czytający wartości z `pcb-layout.json` / `pcb_params.scad`, "
      "tak aby kolejna iteracja płytki wymagała tylko podmiany pliku. Wynik: STL i STEP dla każdego wariantu obudowy.")
    w("")
    w("## 1. Układ współrzędnych")
    w("")
    w("- Jednostki: **milimetry**.")
    w("- Widok **z przodu** (strona TOP, strona użytkownika): początek `(0, 0)` w **lewym dolnym rogu** zarysu płytki, **+x w prawo**, **+y w górę**.")
    w("- **+z** prowadzi od płytki w stronę użytkownika (przód). Górna powierzchnia laminatu to `z = 0`, dolna `z = -%s`." % f(T))
    w("- Środek płytki: `(%s, %s)`. %s" % (f(B.D["cx"]), f(B.D["cy"]), "Wyświetlacz jest wyśrodkowany na płytce." if KL else
      "Wszystkie elementy frontu (wyświetlacz, przyciski) są rozmieszczone symetrycznie względem tego środka w poziomie."))
    w("")
    w("## 2. Płytka")
    w("")
    w("| Parametr | Wartość |")
    w("| --- | --- |")
    w("| Zarys | prostokąt **%s × %s mm**, narożniki zaokrąglone R%s |" % (f(W), f(H), f(B.P["corner_r"])))
    w("| Grubość laminatu | %s mm (FR-4) |" % f(T))
    w("| Otwory montażowe | 4 × Ø%s mm (śruby M2,5), środki: %s |" % (
        f(B.P["mount_d"]), ", ".join("(%s, %s)" % (f(x), f(y)) for x, y in B.mount_holes())))
    w("| Strefa wokół otworu montażowego (bez elementów i miedzi sygnałowej) | promień %s mm |" % f(B.P["mount_keepout_r"]))
    w("| Tolerancja zarysu płytki | ±0,2 mm (typowo u producenta); obudowa musi przyjąć ±0,3 mm |")
    w("")
    w("Płytka jest dwustronna z metalizowanymi otworami. **Jest to wersja robocza (%s), jeszcze nie do zamówienia.**" % ("wariant „klin”" if KL else "iteracja 1"))
    w("")
    w("## 3. Przód (TOP): elementy widoczne dla użytkownika")
    w("")
    w("### 3.1 Moduł OLED (SSD1306 128×32, I2C, 0,91″)")
    w("")
    w("| Parametr | Wartość | Źródło |")
    w("| --- | --- | --- |")
    w("| Zarys modułu (laminat) | x %s…%s, y %s…%s (%s × %s mm) | **szacunek** ze zdjęcia, zmierzyć |" % (
        f(o[0]), f(o[2]), f(o[1]), f(o[3]), f(o[2] - o[0]), f(o[3] - o[1])))
    w("| Szkło (obszar obrazu wraz z ramką szkła) | x %s…%s, y %s…%s (%s × %s mm) | wymiar od właściciela |" % (
        f(gx0), f(gx0 + B.P["glass_w"]), f(gy0), f(gy0 + B.P["glass_h"]), f(B.P["glass_w"]), f(B.P["glass_h"])))
    w("| Aktywny obszar wyświetlacza | zwykle ok. 22,4 × 5,6 mm, środek zbliżony do środka szkła | **typowy dla 0,91″, sprawdzić** |")
    w("| Grubość modułu (bez pinów) | %s mm | wymiar od właściciela |" % f(B.P["oled_thickness"]))
    w("| Piny | 4 szt., rozstaw 2,54 mm w pionie, w kolumnie x = %s; od góry: SDA, SCK, VCC, GND | od właściciela |" % f(B.D["oled_pin_x"]))
    w("| Środek pinów od lewej krawędzi szkła | %s mm | od właściciela |" % f(B.P["glass_to_pin"]))
    w("| Wysokość górnej powierzchni modułu nad płytką | **%s mm** (przy plastikowej listwie pinów 2,5 mm pod modułem) | założenie: listwa 2,5 mm; przy skróconej listwie wartość spada |" % f(B.P["oled_thickness"] + B.P["oled_standoff"]))
    w("")
    w("Moduł wlutowany jest piny w płytkę; piny przycina się po stronie tyłu. Szkło jest **wyśrodkowane w poziomie** na środku płytki (z dokładnością do siatki 2,54 mm pinów: przesunięcie %s mm)." % f(abs((gx0 + B.P["glass_w"] / 2) - B.D["cx"]), 2))
    w("")
    wb("### 3.2 Przyciski (3 × Omron B3F-4055)")
    wb("")
    wb("Dane z karty katalogowej Omron B3F-4050/4055/5050/5051 dostarczonej przez właściciela:")
    wb("")
    wb("| Parametr | Wartość |")
    wb("| --- | --- |")
    wb("| Korpus | **12 × 12 mm** (±0,2) |")
    wb("| Wysokość całkowita nad płytką (góra trzpienia) | **7,3 mm** (±0,2) |")
    wb("| Wysokość korpusu | 4,3 mm (±0,2) |")
    wb("| Trzpień (plunger) | kwadrat **3,8 × 3,8 mm** (±0,1), wystaje 1,8 mm ponad okrągłą podstawę |")
    wb("| Podstawa trzpienia | okrągła, Ø7,1 mm |")
    wb("| Rozstaw wyprowadzeń | 12,5 (±0,1) × 5,0 (±0,1) mm; otwory Ø1,2 mm |")
    wb("| Dwa trzpienie pozycjonujące | otwory Ø1,8 mm, odległość 9,0 mm, w osi między kolumnami wyprowadzeń |")
    wb("| Wyprowadzenia pod korpusem | ok. 3,5 mm (przechodzą przez płytkę 1,6 mm i wystają ok. 1,9 mm z tyłu) |")
    wb("")
    wb("Położenia (środki korpusów, od lewej): ")
    wb("")
    wb("| Przycisk | Funkcja | Środek (x, y) |")
    wb("| --- | --- | --- |")
    for ref, name in (() if KL else (("S3", "−"), ("S1", "run"), ("S2", "+"))):
        wb("| %s | %s | (%s, %s) |" % (ref, name, f(B.PARTS[ref]["x"]), f(B.PARTS[ref]["y"])))
    wb("")
    wb("Odstęp między korpusami przycisków w poziomie: %s mm; odstęp w pionie między dolną krawędzią modułu OLED a górną krawędzią przycisków: %s mm. "
      "Wyświetlacz leży **powyżej** poziomej osi symetrii płytki (y = %s), przyciski **poniżej**, symetrycznie (środek wyświetlacza i środki przycisków są w tej samej odległości od osi)." % (
          f(B.P["btn_gap_x"]), f(B.P["group_gap_y"]), f(B.D["cy"])))
    wb("")
    wb("Skok przycisku nie jest podany w otrzymanym fragmencie karty katalogowej; **przyjąć dodatkowy luz na ruch trzpienia 0,3–0,5 mm** i nie wspierać nakładek na korpusie.")
    w("")
    if KL:
        w("### 3.2 Przyciski: poza tą płytką")
        w("")
        w("Trzy przyciski Omron B3F-4055 (S3 „−”, S1 „run”, S2 „+”) leżą na **osobnej płytce 52 × 16 mm** (środki x = 8, 26, 44, y = 8, rozstaw 18 mm, otwory montażowe M2 w x = 16 i 36). "
          "Łączy ją z tą płytką **4 przewody** wlutowane w pola KEY (patrz sekcja 4): GND, PB3 (run), PB4 („+” i „−”), dolna strona „−” (do R6, który zostaje na tej płytce). "
          "Wymiary przycisków i skok: jak w płytce podstawowej (karta Omron B3F-4050/4055/5050/5051: korpus 12 × 12 mm, góra trzpienia 7,3 mm nad płytką).")
        w("")
    w("### 3.3 Pozostała strona przednia")
    w("")
    if KL:
        w("Poza modułem OLED na froncie nie ma wysokich elementów. W pasach nad i pod modułem OLED z przodu **wystają końce nóżek elementów z tyłu** "
          "(przycięte, z cyną): **wysokość do 2,0 mm** nad laminatem. Wewnętrzna powierzchnia panelu przedniego powinna być co najmniej 2,5 mm nad płytką w tych pasach "
          "(a nad szkłem wyświetlacza wynika to z wysokości modułu).")
    else:
        w("Poza modułem OLED i przyciskami na froncie nie ma wysokich elementów. W pasach nad modułem OLED i pod przyciskami z przodu **wystają końce nóżek elementów z tyłu** "
          "(przycięte, z cyną): **wysokość do 2,0 mm** nad laminatem. Wewnętrzna powierzchnia panelu przedniego powinna być co najmniej 2,5 mm nad płytką w tych pasach "
          "(a nad przyciskami i szkłem wyświetlacza wynika to z wysokości elementów).")
    w("")
    w("## 4. Tył (BOTTOM): elementy przewlekane")
    w("")
    w("Wszystkie elementy poza wyświetlaczem%s są po tylnej stronie. Obwiednia wysokości tylnej strony: **%s mm** poniżej dolnej powierzchni laminatu." % ("" if KL else " i przyciskami", f(B.P["bottom_height"])))
    w("")
    w("| Ozn. | Element | Prostokąt zajmowany (x0, y0, x1, y1) | Wysokość nad dolną powierzchnią płytki [mm] |")
    w("| --- | --- | --- | --- |")
    for ref in B.REFS_BOTTOM:
        p = B.PARTS[ref]
        b = B.body_rect(ref)
        h = B.FP[p["fp"]]["height"]
        if ref == "U1":
            h = 8.5
        if ref == "KEY":
            w("| %s | pola lutownicze 4 przewodów do płytki przycisków (Ø1,2 mm otwór, pad Ø2,3 mm, rozstaw 3,5 mm; kolejność od lewej na widoku z przodu: patrz `pcb-przod.svg`) | (%s, %s, %s, %s) | 0 |" % (ref, f(b[0]), f(b[1]), f(b[2]), f(b[3])))
        elif ref in ("SPK", "BAT"):
            w("| %s | pola lutownicze na przewody (Ø1,2 mm otwór, 2 pady) | (%s, %s, %s, %s) | 0 |" % (ref, f(b[0]), f(b[1]), f(b[2]), f(b[3])))
        else:
            w("| %s | %s | (%s, %s, %s, %s) | %s |" % (ref, p["value"], f(b[0]), f(b[1]), f(b[2]), f(b[3]), f(h)))
    w("")
    w("### Układ ATtiny13A w podstawce DIP-8")
    w("")
    w("- Podstawka DIP-8 (wysokość 4,5 mm, wymiar od właściciela). Układ w podstawce razem sięga ok. **8,5 mm** poniżej płytki (**szacunek**, zmierzyć).")
    notch = "**górnej krawędzi płytki (+y)**"
    if KL:      # direction of the end with pins 1 and 8 (the notch) in the front-view frame
        pp = B.pad_positions("U1")
        ex = [(pp["1"][i] + pp["8"][i]) / 2 - sum(v[i] for v in pp.values()) / len(pp) for i in (0, 1)]
        notch = ("**górnej krawędzi płytki (+y)**" if ex[1] > abs(ex[0]) else "**dolnej krawędzi płytki (−y)**" if -ex[1] > abs(ex[0])
                 else "**prawej krawędzi płytki (+x)**" if ex[0] > 0 else "**lewej krawędzi płytki (−x)**")
        notch += " na widoku z przodu"
    w("- **Układ jest wymienny**: właściciel programuje go poza obwodem i wkłada z powrotem. Obudowa musi umożliwiać dostęp do podstawki od tyłu (zdejmowana pokrywa lub otwór) "
      "i wyciągnięcie układu wyciągaczem DIP lub cienkim śrubokrętem z obu stron podstawki. Wcięcie (pin 1) układu jest skierowane do %s." % notch)
    w("- Elektrolit 100 µF (Ø5 × 8 mm) stoi pionowo; dioda LED jest 5 mm (wysokość do ok. 8,7 mm) lub 3 mm (mniejsza): do potwierdzenia.")
    w("")
    w("## 5. Strefy zakazane i wymagania dla obudowy")
    w("")
    w("1. **Okno na szkło** wyświetlacza, współrzędne szkła z 3.1; okno nie może zakrywać aktywnego obszaru; sugerowany luz 0,3 mm na stronę.")
    if KL:
        w("2. **Przyciski** są na osobnej płytce (3.2): ich otwory i kapsle projektuje się względem tamtej płytki, nie względem tej.")
    else:
        w("2. **Trzy otwory na przyciski** (korpus 12 × 12 mm nie przechodzi przez panel, trzpień i okrągła podstawa tak): środki z 3.2; otwory o średnicy co najmniej Ø7,1 + luz FDM, "
          "albo zewnętrzne nakładki (kapsle) opierające się na trzpieniu 3,8 × 3,8 mm. Górna płaszczyzna trzpienia: 7,3 mm nad płytką.")
    w("3. **Słupki montażowe** pod 4 otwory M2,5 (Ø2,7 mm); strefa wolna r = %s mm wokół." % f(B.P["mount_keepout_r"]))
    if KL:
        w("4. **Nie opierać** panelu na module OLED w sposób dociskający go do płytki; panel opiera się na słupkach montażowych.")
    else:
        w("4. **Nie opierać** panelu na korpusach przycisków ani na module OLED w sposób dociskający trzpień; panel opiera się na słupkach montażowych.")
    w("5. Z tyłu: obwiednia %s mm; w obszarze prostokątów z tabeli w sekcji 4 nic nie może wchodzić." % f(B.P["bottom_height"]))
    if KL:
        w("6. **Przewody** głośnika i baterii wchodzą na dwie pary pól lutowniczych (2 pady na parę, pad Ø2,3 mm, otwór Ø1,2 mm), a przewody płytki przycisków na cztery pola KEY: "
          "położenie w tabeli w sekcji 4 (SPK, BAT, KEY). Zostawić prowadzenie przewodów i odciążenie (zacisk lub opaska).")
    else:
        w("6. **Przewody** głośnika i baterii wchodzą na dwie pary pól lutowniczych (2 pady na parę, pad Ø2,3 mm, otwór Ø1,2 mm): położenie w tabeli w sekcji 4 (SPK, BAT). "
          "Zostawić prowadzenie przewodów i odciążenie (zacisk lub opaska).")
    w("")
    w("## 6. Tolerancje i druk 3D (FDM)")
    w("")
    w("- Luz na pasowania ruchome i wsuwane: **0,2–0,3 mm** na stronę, otwory na śruby +0,2 mm.")
    w("- Minimalna ścianka: 1,2 mm (3 obrysy przy dyszy 0,4 mm); minimalne detale okna: 0,8 mm.")
    wb("- Kapsle przycisków muszą dawać luz od krawędzi otworu co najmniej 0,3 mm i mieć ogranicznik wysuwu.")
    w("- Zakładać, że elementy mają tolerancje: %społożenie modułu OLED ±0,3 (lutowany ręcznie)." % ("" if KL else "korpus przycisku ±0,2, wysokość 7,3 ±0,2, "))
    w("")
    w("## 7. Elementy niepewne (szacunki do zmierzenia)")
    w("")
    w("| Wielkość | Przyjęto | Dlaczego niepewna |")
    w("| --- | --- | --- |")
    w("| Długość i położenie zarysu modułu OLED | 38 × 12 mm, pin 1,5 mm od lewej krawędzi | tylko zdjęcie |")
    w("| Wysokość listwy pinów pod modułem | 2,5 mm | typowa, do pomiaru |")
    w("| Wysokość ATtiny w podstawce | 8,5 mm | typowa dla DIP-8 |")
    w("| Dioda LED | Ø5 mm, 8,7 mm wysokości | właściciel ma „dowolną” LED |")
    wb("| Skok przycisku B3F | nie podany w otrzymanym fragmencie | brak danych |")
    wb("| Które nóżki B3F-4055 są połączone na stałe | wg karty: 12,5 mm od siebie (4–3 i 2–1); wg pomiaru właściciela: 5 mm | **sprzeczność do wyjaśnienia testem na przycisku**; dotyczy schematu płytki, nie obudowy |")
    w("")
    w("## 8. Miejsce na wizję właściciela")
    w("")
    w("### Głośnik")
    w("")
    w("Dane od właściciela: **średnica 26,5 mm, wysokość ramki 4 mm, wysokość całego głośnika 9 mm**. Pozostałe (położenie, mocowanie, otwory dźwiękowe) uzupełni właściciel.")
    w("")
    w("_Do uzupełnienia._")
    w("")
    w("### Koszyk na baterie 3 × AAA")
    w("")
    w("Wymiary koszyka, sposób wyjmowania baterii, położenie względem płytki: _do uzupełnienia przez właściciela._")
    w("")
    w("### Wygląd i rozmieszczenie")
    w("")
    w("_Do uzupełnienia przez właściciela._")
    w("")
    w("## 9. Warianty do zbadania w kolejnych iteracjach")
    w("")
    w("Właściciel przewiduje kilka iteracji i wybór finalnego wariantu. Obudowa powinna być parametryczna, tak aby można było łatwo zmienić: grubość ścianek, "
      "typ nakładek na przyciski (zlicowane z panelem, wystające, wpuszczone), sposób mocowania płytki (słupki od frontu lub tyłu), dostęp do układu ATtiny (pokrywa lub otwór), "
      "sposób zamykania (śruby, zatrzaski), orientację (głośnik z przodu, z tyłu lub z boku).")
    return "\n".join(L) + "\n"


def build_k3():
    """Short spec of the klin3 board (parts table); the full machine-readable data is in pcb-layout.json."""
    L = ["# Płytka główna wariantu „klin 3” (bez wyświetlacza i przycisków): %s × %s mm" % (f(B.P["W"]), f(B.P["H"])), "",
         "Wersja robocza, jeszcze nie do zamówienia. Dane maszynowe: `pcb-layout.json` (generowany `python3 tools/pcb/build.py --variant klin3`).",
         "Układ współrzędnych: widok od strony TOP (od strony ścianki obudowy), początek w lewym dolnym rogu, +x w prawo, +y w górę, "
         "+y wskazuje wierzchołek obudowy. Laminat %s mm; elementy stoją po stronie BOTTOM (do wnętrza obudowy), "
         "po stronie TOP są tylko lut i końcówki nóżek (do 2,0 mm)." % f(B.P["thickness"]), "",
         "Otwory montażowe M2,5 (Ø%s): %s." % (f(B.P["mount_d"]), ", ".join("(%s; %s)" % (f(x), f(y)) for x, y in B.mount_holes())), "",
         "| Ozn. | Element | Prostokąt (x0, y0, x1, y1) | Wysokość [mm] |", "| --- | --- | --- | --- |"]
    for ref in B.REFS_BOTTOM:
        b = B.body_rect(ref)
        h = 8.5 if ref == "U1" else B.FP[B.PARTS[ref]["fp"]]["height"]
        L.append("| %s | %s | (%s) | %s |" % (ref, B.PARTS[ref]["value"], ", ".join(f(v) for v in b), f(h)))
    L += ["", "Pola przewodów (wlutowane od strony elementów): DISP 1..4 = SDA, SCL, VCC, GND modułu wyświetlacza (żeńskie przewody "
          "Dupont na listwie pinów modułu); KEY 1..4 = GND, PB3, PB4, dolna strona S3 (płytka przycisków); SPK głośnik; BAT bateria."]
    return "\n".join(L) + "\n"


def write(out):
    os.makedirs(out, exist_ok=True)
    if B.K3:
        open(os.path.join(out, "specyfikacja-plytki.md"), "w").write(build_k3())
        return
    open(os.path.join(out, "specyfikacja-obudowy-dla-agenta.md"), "w").write(build())
