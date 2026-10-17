#!/usr/bin/env python3
"""Generates docs/instrukcja-montazu.md from design.py.

All hole addresses in the manual come from the data in design.py; every
continuity/resistance statement in the "Sprawdzenie" blocks is checked
against the electrical model while the manual is generated (a wrong
statement makes this script fail), so the text cannot drift away from the
drawings and the verified netlist."""
import os
import sys
from collections import Counter, OrderedDict

import design as d
from render_svg import RES_BANDS, step_labels

PL_COLOUR = d.COLOURS
RAIL_PL = {"T+": "T+ (górna zewnętrzna)", "T-": "T− (górna wewnętrzna)",
           "B+": "B+ (dolna wewnętrzna)", "B-": "B− (dolna zewnętrzna)"}
EXT_PIN = {  # name of the pin / lead as used in sentences
    "UNO:RESET": "RESET", "UNO:5V": "5V", "UNO:GND": "GND", "UNO:D10": "D10",
    "UNO:D11": "D11", "UNO:D12": "D12", "UNO:D13": "D13",
    "OLED:VCC": "VCC", "OLED:GND": "GND", "OLED:SDA": "SDA", "OLED:SCL": "SCL",
}
RES_PL = {"10k": "10 kΩ", "470": "470 Ω", "47k": "47 kΩ", "33": "33 Ω", "4.7k": "4,7 kΩ"}
COL_PL = {"0": "czarny", "1": "brązowy", "2": "czerwony", "3": "pomarańczowy", "4": "żółty",
          "5": "zielony", "6": "niebieski", "7": "fioletowy", "8": "szary", "9": "biały"}


def H(h):
    if ":" in h:
        return EXT_PL[h]
    for r in d.RAILS:
        if h.startswith(r):
            return "**%s%s**" % (r.replace("-", "−"), h[len(r):])
    return "**%s**" % h


def bands(val):
    return "-".join(COL_PL[c] for c in RES_BANDS[val])


def ref_name(ref):
    return d.PARTS[ref][2]


def step_text(it):
    """Polish text of one step (without number)."""
    if it["kind"] == "wire":
        col = PL_COLOUR[it["colour"]]
        a, b = it["a"], it["b"]
        ext, brd = (a, b) if ":" in a else (b, a)
        if ":" not in ext:
            return "Przewód **%s**: z %s do %s." % (col, H(a), H(b))
        dev = ext.split(":")[0]
        pin = ext.split(":")[1]
        if dev == "UNO":
            where = ("złącze zasilania" if pin in ("5V", "GND", "RESET") else "złącze cyfrowe")
            if ext == "UNO:GND":
                where = "złącze zasilania (dowolny GND)"
            return ("Przewód **%s** (męsko-męski): jeden koniec w pin **%s** Arduino UNO (%s), drugi w %s." %
                    (col, pin, where, H(brd)))
        if dev == "OLED":
            return ("Przewód **%s** (żeńsko-męski): żeński koniec na pin **%s** modułu OLED "
                    "(czytaj nazwę z nadruku modułu), męski koniec w %s." % (col, pin, H(brd)))
        if dev == "SPK":
            side = ("od strony kolektora" if pin == "2" else "od strony rezystora 33 Ω")
            return "Wyprowadzenie głośnika **%s** (przedłużone przewodem): koniec w %s." % (side, H(brd))
        if dev == "BAT":
            return "**%s** przewód koszyka baterii (%s): koniec w %s." % (
                "Czerwony" if pin == "+" else "Czarny", "plus" if pin == "+" else "minus", H(brd))
    ref = it["ref"]
    kind = d.PARTS[ref][0]
    pins = it["pins"]
    if ref == "U1":
        return ("**ATtiny13A** w rowek środkowy, wcięcie (kropka przy pinie 1) po **lewej** stronie: "
                "pin 1 → %s, pin 2 → %s, pin 3 → %s, pin 4 → %s, pin 5 → %s, pin 6 → %s, pin 7 → %s, pin 8 → %s. "
                "Dociśnij równo, nie zginając nóżek." % tuple(H(pins[str(i)]) for i in range(1, 9)))
    if kind == "res":
        val = d.PARTS[ref][1]
        txt = "Rezystor **%s** (%s) %s: nóżki w %s i %s." % (RES_PL[val], bands(val), ref, H(pins["1"]), H(pins["2"]))
        if ref == "R4":
            txt = txt.replace("nóżki", "ŁĄCZNIE ½ W; nóżki", 1).replace("ŁĄCZNIE ½ W; ", "½ W, ")
        return txt
    if kind == "cap":
        return "Kondensator ceramiczny **100 nF** (oznaczenie „104”) %s, bez polaryzacji: nóżki w %s i %s." % (
            ref, H(pins["1"]), H(pins["2"]))
    if kind == "elco":
        val = {"100u": "100 µF", "10u": "10 µF"}[d.PARTS[ref][1]]
        return ("Kondensator elektrolityczny **%s** %s, **polaryzacja!**: długa nóżka (+) w %s, "
                "nóżka przy białym pasku (−) w %s." % (val, ref, H(pins["+"]), H(pins["-"])))
    if kind == "led":
        return ("Dioda **LED** D1, **polaryzacja!**: dłuższa nóżka (anoda, A) w %s, krótsza nóżka "
                "(katoda, K, płaski brzeg obudowy) w %s." % (H(pins["A"]), H(pins["K"])))
    if kind == "npn":
        return ("Tranzystor **BC547A** Q1 **płaską stroną do siebie** (do rzędu j), nóżkami w dół: "
                "lewa nóżka = kolektor (C) → %s, środkowa = baza (B) → %s, prawa = emiter (E) → %s. "
                "Sprawdź nadruk BC547A." % (H(pins["C"]), H(pins["B"]), H(pins["E"])))
    if kind == "sw":
        name = d.PARTS[ref][1].replace("-", "−")
        return ("Przycisk **„%s”** %s: wciśnij w rowek środkowy; styki górne w %s i %s, dolne w %s i %s "
                "(najpierw kontrola z punktu 0.2)." % (
                    name, ref, H(pins["A1"]), H(pins["A2"]), H(pins["B1"]), H(pins["B2"])))
    return ref


# ----------------------------------------------------------------- checks ----
def through(mode, p, q, ref, upto, pressed=None):
    """p and q are connected only through the part `ref` (a resistor)."""
    if d.connected(mode, p, q, upto, pressed):
        return False
    it = next(i for i in d.ITEMS if i["kind"] == "part" and i["ref"] == ref)
    n1, n2 = (d.hole_node(it["pins"][k]) for k in ("1", "2"))
    dsu, pin_node, _ = d.build_nets(mode, True, upto)
    if pressed:
        sw = next(i for i in d.ITEMS if i["kind"] == "part" and i["ref"] == pressed)
        dsu.union(d.hole_node(sw["pins"]["A1"]), d.hole_node(sw["pins"]["B1"]))
    a, b, c = dsu.find(d.hole_node(p)), dsu.find(d.hole_node(q)), (dsu.find(n1), dsu.find(n2))
    return (a, b) == c or (b, a) == c


class Check:
    def __init__(self, kind, a, b, expect, text, ref=None, pressed=None):
        self.kind, self.a, self.b, self.expect, self.text = kind, a, b, expect, text
        self.ref, self.pressed = ref, pressed

    def run(self, mode, upto):
        if self.kind == "cont":
            return d.connected(mode, self.a, self.b, upto, self.pressed) == self.expect
        if self.kind == "res":
            return through(mode, self.a, self.b, self.ref, upto, self.pressed)
        raise ValueError(self.kind)


def cont(a, b, text, mode_exp=True, pressed=None):
    return Check("cont", a, b, mode_exp, text, pressed=pressed)


def res(a, b, ref, text, pressed=None):
    return Check("res", a, b, True, text, ref=ref, pressed=pressed)


def render_checks(checks, mode, upto):
    out = []
    for c in checks:
        if not c.run(mode, upto):
            raise SystemExit("check does not match the model: %s %s-%s (%s)" % (c.kind, c.a, c.b, c.text))
        if c.kind == "cont":
            who = "**piszczy**" if c.expect else "**NIE piszczy**"
            if c.pressed:
                who = "przy wciśniętym przycisku " + who
            out.append("- [ ] %s ↔ %s: %s (%s)" % (H(c.a), H(c.b), who, c.text))
        else:
            pre = "przy wciśniętym przycisku " if c.pressed else ""
            out.append("- [ ] %s ↔ %s: %srezystancja %s (%s)" % (H(c.a), H(c.b), pre, c.text.split("|")[0], c.text.split("|")[1]))
    return out


STAGE_CHECKS = {
    1: ("isp", [
        cont("T+9", "T-9", "między szynami plus i minus nie może być zwarcia", False),
        cont("d11", "T+9", "pin 8 ATtiny jest połączony z plusem"),
        cont("i14", "T-9", "pin 4 ATtiny ma połączenie z minusem górnej szyny"),
        cont("T+9", "B+9", "szyny plus są połączone długim czerwonym przewodem"),
        cont("T-9", "B-9", "szyny minus są połączone długim czarnym przewodem"),
        cont("i8", "T+9", "dolny pasek plusa w kolumnie 8 jest połączony z plusem"),
        res("g11", "T+9", "R1", "≈ 10 kΩ|pin 1 (RESET) przez R1 do plusa; układ scalony może obniżyć odczyt"),
        cont("g11", "T-9", "RESET nie jest zwarty z masą", False),
    ]),
    3: ("work", [
        cont("T+9", "T-9", "plus nie jest zwarty z minusem", False),
        cont("d20", "T-9", "baza nie jest zwarta z masą", False),
        res("d20", "T-9", "R3", "≈ 47 kΩ|baza do masy przez R3"),
        cont("d13", "d20", "PB1 nie jest zwarte z bazą (jest 470 Ω)", False),
        res("d13", "d20", "R2", "≈ 470 Ω|pin 6 (PB1) do bazy przez szary przewód i R2; układ scalony może obniżyć odczyt"),
        cont("a21", "T-9", "emiter (kolumna 21) jest połączony z masą"),
        cont("a22", "T+9", "kolumna 22 jest połączona z plusem"),
        res("e22", "e27", "R4", "≈ 33 Ω|plus do strony głośnika przez R4"),
        cont("d19", "d26", "kolektor (kolumna 19) jest połączony z kolumną 26 białym przewodem"),
        cont("d19", "d27", "kolektor nie jest zwarty ze stroną rezystora 33 Ω", False),
    ]),
    4: ("work", [
        cont("T+9", "T-9", "plus nie jest zwarty z minusem", False),
        cont("i20", "T+9", "pin VCC modułu jest połączony z plusem"),
        cont("i23", "b12", "pin SCL modułu jest połączony z pinem 7 ATtiny (kolumna 12)"),
        cont("i26", "b14", "pin SDA modułu jest połączony z pinem 5 ATtiny (kolumna 14)"),
        cont("i23", "i26", "SCL nie jest zwarte z SDA", False),
        cont("i20", "i23", "VCC nie jest zwarte z SCL", False),
        cont("i20", "i26", "VCC nie jest zwarte z SDA", False),
    ]),
    5: ("work", [
        cont("T+9", "T-9", "plus nie jest zwarty z minusem", False),
        cont("h12", "T-9", "„run” puszczony: PB3 nie jest zwarte z masą", False),
        cont("h12", "T-9", "„run” wciśnięty: PB3 zwarte z masą", True, pressed="S1"),
        cont("h13", "T-9", "„+” i „−” puszczone: PB4 nie jest zwarte z masą", False),
        cont("h13", "T-9", "„+” wciśnięty: PB4 zwarte z masą", True, pressed="S2"),
        res("h13", "T-9", "R6", "≈ 10 kΩ|„−” wciśnięty: PB4 do masy przez R6", pressed="S3"),
        res("h13", "i8", "R5", "≈ 10 kΩ|PB4 do plusa przez R5; układ scalony może obniżyć odczyt"),
    ]),
    6: ("work", [
        cont("T+30", "T-30", "plus baterii nie jest zwarty z minusem", False),
        cont("T+30", "d11", "plus baterii dochodzi do pinu 8 ATtiny"),
        cont("T-30", "i14", "minus baterii dochodzi do pinu 4 ATtiny"),
    ]),
}


# ------------------------------------------------------------- text parts ----
def label_of(ref=None, a=None, b=None):
    """Step label ('1.9') of a part (by ref) or of a wire (by its ends)."""
    labels = step_labels()
    for i, it in enumerate(d.ITEMS):
        if ref and it["kind"] == "part" and it["ref"] == ref:
            return labels[i]
        if a and it["kind"] == "wire" and it["a"] == a and it["b"] == b:
            return labels[i]
    raise KeyError((ref, a, b))


def isp_only_labels():
    labels = step_labels()
    return [labels[i] for i, it in enumerate(d.ITEMS) if it["modes"] == d.ISP]


def stage_items(stage):
    labels = step_labels()
    return [(labels[i], it) for i, it in enumerate(d.ITEMS) if it["stage"] == stage]


def isp_note(it):
    if d.ISP == it["modes"]:
        return " *(tylko na czas programowania; zdejmij przy zasilaniu z baterii)*"
    if d.WORK == it["modes"] and it["stage"] <= 5 and it["kind"] == "part" and it["ref"] == "R2":
        return " *(na czas programowania wyjmij jedną nóżkę z płytki)*"
    if d.WORK == it["modes"] and it["stage"] == 4:
        return " *(na czas programowania wyjmij)*"
    return ""


def steps_md(stage):
    out = []
    for label, it in stage_items(stage):
        txt = step_text(it)
        if it.get("optional"):
            txt = "**(opcjonalnie)** " + txt
        note = it.get("note", "")
        if note:
            txt += " — %s." % note.rstrip(".")
        out.append("- [ ] **%s** %s%s" % (label, txt, isp_note(it)))
    return "\n".join(out)


def bom_md():
    cnt = Counter()
    for it in d.ITEMS:
        if it["kind"] == "part" and it["ref"] not in ("U1",):
            kind, val, _ = d.PARTS[it["ref"]]
            if kind == "res":
                cnt[("R", val, it.get("optional", False))] += 1
    wires = Counter()
    for it in d.ITEMS:
        if it["kind"] == "wire":
            wires[it["colour"]] += 1
    rows = []
    rows.append("| Element | Ilość | Wartość / uwagi | Oznaczenia na schemacie |")
    rows.append("| --- | --- | --- | --- |")
    rows.append("| ATtiny13A, obudowa DIP-8 | 1 | DIP-8 (nie SOIC-8) | U1 |")
    for val, refs in (("10k", "R1, R5, R6"), ("470", "R2"), ("47k", "R3"), ("33", "R4")):
        n = sum(v for (k, vv, o), v in cnt.items() if vv == val and not o)
        extra = "; ½ W" if val == "33" else ""
        rows.append("| Rezystor %s | %d | %s%s; zmierz multimetrem przed włożeniem | %s |" % (
            RES_PL[val], n, bands(val), extra, refs))
    rows.append("| Rezystor 4,7 kΩ | 2 (opcjonalnie) | %s; tylko jeśli moduł OLED nie ma pull-upów | R7, R8 |" % bands("4.7k"))
    rows.append("| Kondensator ceramiczny 100 nF („104”) | 2 | bez polaryzacji | C1, C2 |")
    rows.append("| Kondensator elektrolityczny 100 µF, min. 10 V | 1 | **polaryzacja**: długa nóżka = plus | C3 |")
    rows.append("| Kondensator elektrolityczny 10 µF, min. 6,3 V | 1 | tylko dla Arduino ISP; **polaryzacja** | C4 |")
    rows.append("| Tranzystor BC547A | 1 | wyprowadzenia C-B-E | Q1 |")
    rows.append("| Dioda LED, dowolna | 1 | **polaryzacja**: długa nóżka = anoda | D1 |")
    rows.append("| Przycisk tact (4 nóżki) | 3 | „run”, „+”, „−” | S1, S2, S3 |")
    rows.append("| Głośnik 6,4 Ω z zabawki | 1 | dwa przewody do przedłużenia | SPK |")
    rows.append("| Moduł OLED 128×32, SSD1306, I2C, 4 piny | 1 | adres 0x3C | OLED |")
    rows.append("| Koszyk 3×AAA z przewodami | 1 | 4,5 V | BAT |")
    rows.append("| Arduino UNO + kabel USB | 1 | programator ISP | UNO |")
    rows.append("| Płytka stykowa 400 otworów (30 kolumn) | 1 | szyny po obu stronach | |")
    rows.append("")
    rows.append("**Przewody połączeniowe** (liczby z tej instrukcji):")
    rows.append("")
    rows.append("| Kolor | Ilość | Znaczenie |")
    rows.append("| --- | --- | --- |")
    meaning = {"red": "VCC (plus)", "black": "GND (minus)", "green": "SDA / MOSI (PB0)",
               "yellow": "SCL / SCK (PB2)", "orange": "PB3 („run”)", "blue": "PB4 (przyciski „+” i „−”)",
               "violet": "RESET", "gray": "PB1 / MISO / RESET Arduino", "white": "głośnik i kolektor"}
    for c in ("red", "black", "green", "yellow", "orange", "blue", "violet", "gray", "white"):
        rows.append("| %s | %d | %s |" % (PL_COLOUR[c], wires[c], meaning[c]))
    rows.append("")
    rows.append("Dwa długie przewody (czerwony i czarny, ok. 10 cm) łączą górne i dolne szyny; "
                "do wtyków OLED potrzebne są 4 przewody żeńsko-męskie, do Arduino męsko-męskie.")
    return "\n".join(rows)


def checks_md(stage):
    mode, checks = STAGE_CHECKS[stage]
    return "\n".join(render_checks(checks, mode, stage))


# -------------------------------------------------------------- the manual ----
def build():
    L = []
    w = L.append
    w("# Minutnik ATtiny13A: instrukcja montażu na płytce stykowej")
    w("")
    w("*Plik wygenerowany skryptem `tools/breadboard/manual.py` z tych samych danych, z których powstały "
      "rysunki i weryfikacja sieci połączeń (`tools/breadboard/design.py`). Nie edytuj go ręcznie.*")
    w("")
    w("## Jak korzystać z instrukcji")
    w("")
    w("1. Pracuj etapami. **Każdy etap kończy się sprawdzeniem** (multimetrem lub testem na urządzeniu). "
      "Następny etap zaczynaj dopiero po wyniku „działa”. Dzięki temu błąd da się zlokalizować.")
    w("2. Każdy krok to jedna czynność z adresem otworu. Odhaczaj pola `[ ]`.")
    w("3. Rysunki (katalog `img/`) pokazują płytkę z góry **po** danym etapie. Numer w kółku to numer kroku, "
      "turkusowy = nowy w tym etapie.")
    w("4. Programowanie (Arduino UNO jako ISP, fuse'y, wgrywanie) opisuje osobny dokument: "
      "[programowanie.md](programowanie.md). Etap 2 (fuse'y) jest tam.")
    w("")
    w("## Układ współrzędnych")
    w("")
    w("![Płytka z opisem współrzędnych](img/plansza.svg)")
    w("")
    w("- **Kolumny** numerowane od lewej: 1 … 30. Pięć otworów jednej kolumny po jednej stronie rowka jest "
      "połączonych ze sobą.")
    w("- **Rzędy**: a–e leżą nad rowkiem środkowym, f–j pod nim. Adres otworu to rząd i kolumna, np. **e11** "
      "(rząd e, kolumna 11). Kolumna w górnej połowie (a–e) **nie jest** połączona z tą samą kolumną w dolnej (f–j).")
    w("- **Szyny zasilania** (poziome linie, każda połączona na całej długości). W tej instrukcji mają stałe "
      "nazwy, **niezależnie od kolorowych nadruków na płytce** (nadruki bywają różne):")
    w("  - **T+** = górna szyna zewnętrzna (przy krawędzi płytki), plus;")
    w("  - **T−** = górna szyna wewnętrzna (bliżej rzędu a), minus;")
    w("  - **B+** = dolna szyna wewnętrzna (bliżej rzędu j), plus;")
    w("  - **B−** = dolna szyna zewnętrzna (przy krawędzi), minus.")
    w("  - Adres szyny zawiera numer kolumny, przy której leży otwór, np. **T+11** = otwór szyny T+ na wysokości kolumny 11.")
    w("- Układ mieści się w 30 kolumnach. Wszystkie kolumny podane w krokach są liczone od lewej strony płytki.")
    w("- **Przed zaczęciem sprawdź ciągłość szyn**: multimetr na piszczenie, jedna sonda przy kolumnie 1, "
      "druga przy kolumnie 30 tej samej szyny. Jeśli szyna jest przerwana w środku (zdarza się w dłuższych "
      "płytkach), połącz obie połówki przewodem.")
    w("- Orientacja: płytka leży przed Tobą, rząd a jest **dalej** od Ciebie (u góry rysunku), rząd j **bliżej**.")
    w("")
    w("### Kolory przewodów (stałe w całej instrukcji)")
    w("")
    w("| Kolor | Sygnał |")
    w("| --- | --- |")
    w("| czerwony | VCC (plus zasilania) |")
    w("| czarny | GND (masa) |")
    w("| zielony | SDA / MOSI (PB0, pin 5) |")
    w("| żółty | SCL / SCK (PB2, pin 7) |")
    w("| pomarańczowy | przycisk „run” (PB3, pin 2) |")
    w("| niebieski | przyciski „+” i „−” (PB4, pin 3) |")
    w("| fioletowy | RESET (pin 1) |")
    w("| szary | PB1 / MISO (pin 6); RESET płytki Arduino |")
    w("| biały | głośnik i kolektor tranzystora |")
    w("")
    w("## Lista zakupów i elementów")
    w("")
    w(bom_md())
    w("")
    w("> **Uwaga do briefu:** w tabeli elementów briefu są „2× 10 kΩ”, a układ potrzebuje **trzech** rezystorów "
      "10 kΩ (R1 RESET, R5 pull-up PB4, R6 przycisk „−”). Ta instrukcja zakłada 3 sztuki.")
    w("")
    w("## Etap 0: przygotowanie (bez wkładania czegokolwiek w płytkę)")
    w("")
    w("### 0.1 Rezystory: zmierz każdy przed wsadzeniem")
    w("")
    w("Multimetr na zakres Ω. Odczyt powinien być w granicach tolerancji (±5%) wartości z tabeli. Zapisz odczyty.")
    w("")
    w("| Rezystor | Kod kolorów | Odczyt |")
    w("| --- | --- | --- |")
    for val, refs in (("10k", "R1, R5, R6 (3 szt.)"), ("470", "R2"), ("47k", "R3"), ("33", "R4, ½ W"), ("4.7k", "R7, R8 (opcjonalnie)")):
        w("| %s %s | %s | ______ |" % (RES_PL[val], refs, bands(val)))
    w("")
    w("### 0.2 Przyciski: orientacja styków (multimetr na piszczenie)")
    w("")
    w("Przycisk tact ma 4 nóżki. W typowym przycisku nóżki po tej samej stronie są połączone na stałe, a wciśnięcie łączy obie pary.")
    w("")
    w("1. Sprawdzaj piszczeniem kolejne pary nóżek **bez** wciskania przycisku, aż znajdziesz dwie pary, które piszczą "
      "(to połączenia stałe w środku przycisku).")
    w("2. Sprawdź, że nóżki z **różnych** par nie piszczą, dopóki nie wciśniesz przycisku; po wciśnięciu piszczą wszystkie.")
    w("3. Włóż przycisk tak, aby **każda para leżała po jednej stronie rowka** (a nie w poprzek rowka). "
      "Gdyby para leżała w poprzek, przycisk zwierałby rowek na stałe.")
    w("4. Przycisk „łapie” rowek środkowy: dwie nóżki w rzędzie e, dwie w rzędzie f, w kolumnach odległych o 2.")
    w("")
    w("### 0.3 Moduł OLED")
    w("")
    w("- Przeczytaj nadruk przy 4 pinach modułu. **VCC i GND mają różną kolejność w różnych modułach** "
      "(np. GND-VCC-SCL-SDA albo VCC-GND-SCL-SDA). Instrukcja nie zakłada żadnej kolejności: "
      "każdy przewód łączysz z pinem o odpowiedniej **nazwie**.")
    w("- Zapisz, co jest na module: ______ ______ ______ ______ (pin 1 … pin 4).")
    w("- Zmierz pull-upy (zasilanie odłączone): multimetr Ω, jedna sonda na pinie VCC modułu, druga kolejno na SDA i SCL. "
      "Odczyt **4,7–10 kΩ** = moduł ma pull-upy (nie montuj R7 i R8). Odczyt „OL” / nieskończoność = brak pull-upów: "
      "zamontuj R7 i R8 (krok w etapie 4).")
    w("")
    w("### 0.4 Tranzystor BC547A")
    w("")
    w("Trzymaj tranzystor **płaską stroną do siebie, nóżkami w dół**: od lewej **C – B – E** (kolektor, baza, emiter). "
      "Sprawdź nadruk BC547A na obudowie. Wyprowadzenia innych tranzystorów (np. 2N2222 w metalowej obudowie) są inne.")
    w("")
    w("### 0.5 ATtiny13A")
    w("")
    w("Układ ma być w obudowie **DIP-8** (dwa rzędy po 4 nóżki), pasującej do rowka płytki. Jeśli masz SOIC-8 "
      "(płaska, płaskie nóżki) — **zatrzymaj się i napisz**: potrzebny będzie adapter.")
    w("Pin 1 jest przy wcięciu (lub kropce) na obudowie. Wcięcie ma być po **lewej** stronie.")
    w("")
    w("### 0.6 Głośnik")
    w("")
    w("Do dwóch wyprowadzeń głośnika dolutuj odcinki drutu (lub przewody połączeniowe) tak, aby dały się włożyć w otwory "
      "płytki; połączenia zaizoluj taśmą. Jeśli nie lutujesz: mocne skręcenie z końcówką przewodu męskiego i taśma. "
      "Głośnik nie ma polaryzacji.")
    w("")
    w("### Ostrzeżenia (obowiązują cały czas)")
    w("")
    w("- **Nigdy jednocześnie bateria i 5 V z Arduino.** Zasilanie z UNO tylko w trybie programowania, "
      "bateria wpięta tylko w trybie pracy. Przed wpięciem jednego odłącz drugie.")
    w("- Układ scalony wkładaj i wyjmuj bez zasilania.")
    w("- Elektrolity i LED mają polaryzację: odwrotne włożenie może je uszkodzić.")
    w("- Zero zwarć: po każdym etapie sprawdź piszczeniem, że plus nie jest połączony z minusem.")
    w("")

    # --- stage 1
    w("## Etap 1: zasilanie, ATtiny13A i programator ISP")
    w("")
    w("**Cel:** ATtiny13A zasilany z Arduino UNO, połączony tak, żeby `avrdude` odczytał jego sygnaturę.")
    w("")
    w("**Zanim zaczniesz:** wgraj do Arduino UNO szkic **ArduinoISP** (opis w [programowanie.md](programowanie.md), "
      "sekcja 2) **zanim** wpniesz kondensator 10 µF z kroku %s." % label_of(ref="C4"))
    w("")
    w("![Etap 1](img/etap-1.svg)")
    w("")
    w(steps_md(1))
    w("")
    w("**Sprawdzenie (Arduino i bateria odłączone, multimetr na piszczenie):**")
    w("")
    w(checks_md(1))
    w("")
    w("**Sprawdzenie napięcia (UNO podłączone do USB, kable programatora wpięte):**")
    w("")
    w("- [ ] Między %s a %s: **ok. 5,0 V**." % (H("T+9"), H("T-9")))
    w("- [ ] Między %s (pin 8) a %s (pin 4): **ok. 5,0 V**." % (H("d11"), H("i14")))
    w("")
    w("**Gdy wynik jest inny:** brak napięcia → sprawdź przewody 5V i GND z UNO (kroki %s i %s) oraz długie przewody "
      "łączące górne i dolne szyny (%s i %s); napięcie poniżej 4 V → port USB o małej wydajności albo zwarcie; "
      "plus zwarty z minusem → rozłącz UNO i szukaj zwarcia: dotykające się końcówki przewodów lub nóżki kondensatorów." % (
          label_of(a="UNO:5V", b="T+27"), label_of(a="UNO:GND", b="T-27"),
          label_of(a="T+15", b="B+15"), label_of(a="T-16", b="B-16")))
    w("")
    w("**Test przejścia:** komenda `make sig` (lub `avrdude -v`) odczytuje sygnaturę **0x1E 0x90 0x07** "
      "(patrz [programowanie.md](programowanie.md), sekcja 3).")
    w("")
    w("**Zdjęcie kontrolne #1:** po etapie 1 zrób zdjęcie płytki z góry (cała płytka w kadrze, rzędy i kolumny czytelne) "
      "i porównaj z rysunkiem Etapu 1. Zwróć uwagę: wcięcie ATtiny po lewej, pin 1 w f11, czerwony przewód w a11.")
    w("")

    # --- stage 2
    w("## Etap 2: fuse'y")
    w("")
    w("Bez zmian na płytce. Komendy i wyjaśnienie bitów: [programowanie.md](programowanie.md), sekcja 4.")
    w("")

    # --- stage 3
    w("## Etap 3: głośnik")
    w("")
    w("**Cel:** podłączyć głośnik przez tranzystor i wybrać najgłośniejszy ton.")
    w("")
    w("![Etap 3: tryb pracy](img/etap-3.svg)")
    w("")
    w("Rysunek pokazuje stan z włożonym R2 (470 Ω). **Na czas wgrywania programu nóżkę R2 (a17 lub a20) wyjmij z płytki**; "
      "tak wygląda tryb programowania:")
    w("")
    w("![Etap 3: tryb programowania](img/etap-3-isp.svg)")
    w("")
    w("Bulwiaste części (tranzystor, dioda LED, elektrolity) zasłaniają sąsiednie otwory: **nie wkładaj w otwory pod "
      "ich obudową niczego innego** (instrukcja tego nie wymaga; to samo sprawdza skrypt weryfikacji).")
    w("")
    w(steps_md(3))
    w("")
    w("**Sprawdzenie (bez zasilania, multimetr na piszczenie lub Ω):**")
    w("")
    w(checks_md(3))
    w("")
    w("**Test na urządzeniu:**")
    w("")
    w("1. R2 wyjęty. Wgraj `test_tone.hex` (`make flash PROG=test_tone`). Włóż R2 z powrotem (a17 i a20). Zasilanie nadal z UNO (5 V).")
    w("2. Program gra 7 tonów w kolejności: 500, 1000, 1500, 2000, 2500, 3000, 4000 Hz, po 0,5 s, z przerwami 0,5 s, "
      "potem 3 s ciszy i od nowa. **Powiedz, który (numer 1–7) brzmi najgłośniej** — wpiszę jego częstotliwość do stałej `TONE_HZ`.")
    w("3. Test cieplny: wgraj `test_heat_2000Hz.hex` (`make heat FREQ=<najgłośniejszy ton>` zbuduje wersję na Twoją częstotliwość). "
      "Po 20 s ciągłego tonu dotknij palcem tranzystora, rezystora 33 Ω i diody: **nie mogą być gorące** (ledwo ciepłe jest OK).")
    w("")
    w("**Gdy brak dźwięku:** sprawdź kolejność nóżek tranzystora (C-B-E), biały przewód b19–d26, "
      "czy R2 jest włożony, czy głośnik jest w c26 i c27 oraz czy program na pewno się wgrał (`make sig`). "
      "Zmierz napięcie DC na kolektorze (d19) względem T− w trakcie tonu: ma pokazywać wartość pośrednią, "
      "a nie stałe 0 V ani stałe 4,5 V. Odwrócona dioda LED nie wycisza dźwięku, ale przestaje chronić tranzystor.")
    w("")

    # --- stage 4
    w("## Etap 4: wyświetlacz OLED")
    w("")
    w("**Cel:** zasilić OLED i podłączyć magistralę I2C.")
    w("")
    w("![Etap 4](img/etap-4.svg)")
    w("")
    w("**Ostrzeżenie:** nazwy pinów modułu (VCC, GND, SCL, SDA) czytaj z nadruku na **swoim** module. "
      "Przewód czerwony ma trafić na pin **VCC**, a czarny na pin **GND**. Odwrócenie VCC i GND uszkodzi moduł.")
    w("")
    w(steps_md(4))
    w("")
    w("**Sprawdzenie (bez zasilania):**")
    w("")
    w(checks_md(4))
    w("")
    w("**Pull-upy:** jeśli w kroku 0.3 stwierdziłeś brak pull-upów na module, zamontuj opcjonalne kroki %s i %s (R7, R8). "
      "Po zamontowaniu zmierz: między **i26** (SDA) a **i20** (VCC) oraz między **i23** (SCL) a **i20** ok. 4,7 kΩ." % (
          label_of(ref="R7"), label_of(ref="R8")))
    w("")
    w("**Test na urządzeniu:** na czas programowania wyjmij z płytki **żółty przewód z b12 (krok %s) i zielony z b14 (krok %s)** "
      "oraz jedną nóżkę R2. Wgraj `test_display.hex`, wpnij przewody z powrotem (R2 też) i zasilaj dalej z UNO. "
      "Wyświetlacz pokazuje kolejno 2:00, 60:00, 8:88, 1:23, 9:59." % (label_of(a="h23", b="b12"), label_of(a="h26", b="b14")))
    w("")
    w("- [ ] Obraz jest czytelny, nieodwrócony, bez przesunięcia i bez brakujących linii.")
    w("")
    w("Jeśli nie: `make OLED_FLIP=0` (obraz do góry nogami lub lustrzany), `make OLED_COM_CFG=0x12` "
      "(co druga linia widoczna), `make OLED_ADDR=0x3D` (pusty ekran; adres bywa 0x3D). "
      "Powiedz, co widzisz, a dobiorę parametry.")
    w("")
    w("**Zdjęcie kontrolne #2:** zrób zdjęcie płytki po etapie 4 (z podłączonym OLED, ale z widocznym ATtiny) "
      "i porównaj z rysunkiem Etapu 4.")
    w("")

    # --- stage 5
    w("## Etap 5: przyciski")
    w("")
    w("**Cel:** trzy przyciski i drabinka rezystorowa na PB4.")
    w("")
    w("![Etap 5](img/etap-5.svg)")
    w("")
    w("Przed wsadzeniem każdego przycisku wykonaj kontrolę z punktu 0.2.")
    w("")
    w(steps_md(5))
    w("")
    w("**Sprawdzenie (bez zasilania):**")
    w("")
    w(checks_md(5))
    w("")
    w("**Test na urządzeniu:** wgraj `test_buttons.hex` (OLED wpięty; na czas programowania wyjmij przewody OLED jak w etapie 4). "
      "Ekran pokazuje `R:AAA`, gdzie R = 1 przy wciśniętym „run”, a AAA = odczyt ADC pinu PB4 (0–255).")
    w("")
    w("| Stan | Oczekiwany odczyt AAA | Twój odczyt |")
    w("| --- | --- | --- |")
    w("| nic nie wciśnięte | ok. 255 | ____ |")
    w("| „−” | ok. 128 | ____ |")
    w("| „+” | ok. 0 | ____ |")
    w("| „run” (R = 1) | AAA ok. 255 | ____ |")
    w("")
    w("Zapisane wartości przekaż dalej: progi w firmware (<64 → „+”, 64–191 → „−”, ≥192 → nic) dobiorę do nich.")
    w("")

    # --- stage 6
    w("## Etap 6: pełny firmware i zasilanie z baterii")
    w("")
    w("**Cel:** minutnik działa samodzielnie na 3×AAA.")
    w("")
    w("1. Wgraj `timer.hex` (patrz programowanie.md, sekcja 5). Na czas programowania OLED i R2 według tabeli trybu programowania.")
    isp = isp_only_labels()
    w("2. **Odłącz od płytki wszystkie przewody programatora i Arduino** (kroki oznaczone „tylko na czas programowania”: "
      "%s–%s) oraz kabel USB." % (isp[0], isp[-1]))
    w("3. Włóż w koszyk świeże baterie. Zmierz napięcie koszyka (multimetr DC): **4,5–4,8 V**.")
    w("")
    w("![Tryb pracy (bateria)](img/tryb-praca.svg)")
    w("")
    w(steps_md(6))
    w("")
    w("**Sprawdzenie:**")
    w("")
    w(checks_md(6))
    w("")
    w("- [ ] Napięcie między %s a %s: **4,5–4,8 V**." % (H("T+9"), H("T-9")))
    w("- [ ] Napięcie między pinami 8 i 4 (%s i %s): **4,5–4,8 V**." % (H("d11"), H("i14")))
    w("")
    w("**Test na urządzeniu:** po wpięciu baterii ekran pokazuje 2:00 w ciągu 1 s. Dalej: testy odbiorcze z [testy-odbiorcze.md](testy-odbiorcze.md).")
    w("")
    w("### Tryby: co jest wpięte")
    w("")
    w("| | Tryb programowania (UNO) | Tryb pracy (bateria) |")
    w("| --- | --- | --- |")
    w("| Zasilanie | 5 V z UNO (T+27, T−27) | bateria (T+30, T−30) |")
    w("| Przewody UNO (D10–D13, RESET, kondensator 10 µF) | **wpięte** | **wyjęte** |")
    w("| OLED: żółty przewód w b12 i zielony w b14 | **wyjęte** | wpięte |")
    w("| R2 (470 Ω) | **jedna nóżka wyjęta** | włożony |")
    w("")
    w("![Tryb programowania](img/tryb-programowanie.svg)")
    w("")
    w("## Etap 7: funkcje opcjonalne (ramka postępu, ikona dzwonka)")
    w("")
    w("Na ATtiny13A **nie mieszczą się** (patrz raport rozmiaru): ramka kosztuje ok. 302 B (razem 1318 B), ikona ok. 102 B (razem 1118 B), a pełny firmware "
      "z priorytetów 1–2 zajmuje 1016 z 1024 B (auto-uśpienie po 60 s: 1034 B). Wariant „Plan B” z ATtiny25/45/85 (to samo rozmieszczenie pinów, "
      "to samo okablowanie) opisano w [plan-b.md](plan-b.md).")
    w("")
    w("## Etap 8: kalibracja czasu")
    w("")
    w("Bez zmian na płytce: [kalibracja.md](kalibracja.md).")
    w("")
    w("## Weryfikacja sieci połączeń (wynik skryptu)")
    w("")
    w("Skrypt `tools/breadboard/design.py` odtwarza sieci połączeń z kroków powyżej (wszystkie przewody, nóżki i paski "
      "płytki), porównuje je ze schematem z briefu, wykrywa dwa elementy w jednym otworze i sprawdza geometrię "
      "(rozstaw rezystorów, obudowy zasłaniające otwory). Wynik:")
    w("")
    w("```")
    import io
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        d.main()
    w(buf.getvalue().rstrip())
    w("```")
    w("")
    w("Testy mutacyjne (`tools/breadboard/test_design.py`) potwierdzają, że weryfikator wykrywa typowe pomyłki "
      "(zamienione C i E, odwrócona LED, zwarcie przycisku, przewód o kolumnę obok, dwa elementy w jednym otworze).")
    w("")
    return "\n".join(L)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "../../docs/instrukcja-montazu.md"
    md = build()
    with open(out, "w") as f:
        f.write(md + "\n")
    print("wrote", out, "(%d lines)" % md.count("\n"))


if __name__ == "__main__":
    main()
