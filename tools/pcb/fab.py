"""Projekt produkcyjny płytki głównej (klin 3 / klin 4, 40 x 24 mm, 2 warstwy, elementy THT).

Źródła: board.py (rozmieszczenie, sieci, stopki), layout_klin3.py (położenia). Tu: stopki produkcyjne (średnice pól,
otwory), opis miedzi i opisów (silk) w WIDOKU OD STRONY ELEMENTÓW, czyli tak, jak płytkę widzi osoba, która ją lutuje.

Warstwy: "F" = strona elementów (w obudowie: do wnętrza, w KiCadzie F.Cu), "B" = strona lutowania (w obudowie: przy
ściance pokrywy, w KiCadzie B.Cu). Widok od strony elementów = odbicie x względem widoku z przodu z pcb-layout.json
(x' = W - x), y bez zmian. Początek (0, 0) w lewym dolnym rogu zarysu.
"""
import math
import os
import sys

os.environ["PCB_VARIANT"] = "klin3"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import board as B   # noqa: E402
import layout  # noqa: E402,F401  (wypełnia B.LAYOUT położeniami klina 3)

W, H = B.P["W"], B.P["H"]
CORNER_R = B.P["corner_r"]
THICKNESS = B.P["thickness"]
MOUNT_D = B.P["mount_d"]                 # M2,5: otwór nieszczelinowy Ø2,7 (bez metalizacji)
MOUNT_KEEPOUT = B.P["mount_keepout_r"]   # promień wolny od miedzi wokół otworu (łeb wkrętu)

# ---------------------------------------------------------------- reguły (konserwatywne, z zapasem do typowych możliwości 2-warstwowych fabryk)
RULES = dict(
    track=0.30,          # szerokość ścieżki
    clearance=0.28,      # odstęp miedź-miedź przyjęty przez router (DRC wymaga >= clearance_min)
    clearance_min=0.25,
    via_d=0.80, via_drill=0.40,
    edge_clearance=0.50,     # miedź (z krawędzią ścieżki) od krawędzi płytki
    min_annular=0.30,
    hole_to_hole=0.50,
    silk_width=0.15, silk_height=1.0,
    mask_margin=0.05,
)

# ---------------------------------------------------------------- stopki produkcyjne
# Zmiany względem board.py: C3 (Ø5 mm) ma rozstaw nóżek 2,0 mm; pola przewodów Ø2,0 mm (Ø2,3 dawało tylko 0,24 mm
# odstępu na rozstawie 2,54 mm). Obrysy (body) bez zmian, więc obudowa klin 4 się nie zmienia.
B.FP["elco5"]["pads"] = {"+": (0.0, 0.0), "-": (2.0, 0.0)}
B.FP["wire2"]["pad"] = 2.0
B.FP["wire4"]["pad"] = 2.0
B.place_all()

SQUARE_PADS = {("U1", "1"), ("C3", "+"), ("D1", "A"), ("BAT", "1"), ("KEY", "1"), ("DISP", "1")}   # pin 1 / plus: pole kwadratowe


def to_comp(ref, lx, ly):
    """Punkt (lx, ly) układu lokalnego stopki -> widok od strony elementów (x' = W - x)."""
    part = B.PARTS[ref]
    r = math.radians(part["rot"])
    x = part["x"] + (-lx) * math.cos(r) - ly * math.sin(r)
    y = part["y"] + (-lx) * math.sin(r) + ly * math.cos(r)
    return W - x, y


def pad_table():
    """Lista pól: dict(ref, pin, net, x, y, d, drill, shape) w widoku od strony elementów."""
    net_of = {}
    for net, pins in B.NETS.items():
        for ref, pin in pins:
            net_of[(ref, pin)] = net
    out = []
    for ref, part in B.PARTS.items():
        fp = B.FP[part["fp"]]
        for pin, (lx, ly) in fp["pads"].items():
            x, y = to_comp(ref, lx, ly)
            out.append(dict(ref=ref, pin=pin, net=net_of.get((ref, pin)), x=x, y=y, d=fp["pad"], drill=fp["hole"],
                            shape="rect" if (ref, pin) in SQUARE_PADS else "circle"))
    return out


def mount_holes():
    return [(W - x, y) for x, y in B.mount_holes()]


def net_names():
    return list(B.NETS)


PADS = pad_table()
HOLES = mount_holes()

# ---------------------------------------------------------------- opisy (silk), współrzędne lokalne stopki
# Elementy: ("line", x0, y0, x1, y1) | ("circle", cx, cy, r) | ("arc", cx, cy, r, a0, a1) (stopnie, przeciwnie do ruchu zegara)
SILK_FP = {
    # DIP-8: pin 1 w (0, 0), piny 1-4 w dół (y malejące), 5-8 po prawej od dołu do góry; nacięcie przy pinie 1 (u góry)
    "dip8": [("line", -1.27, 1.27, 2.5, 1.27), ("arc", 3.81, 1.27, 1.3, 180, 360), ("line", 5.12, 1.27, 8.89, 1.27),
             ("line", 8.89, 1.27, 8.89, -8.89), ("line", 8.89, -8.89, -1.27, -8.89), ("line", -1.27, -8.89, -1.27, 1.27)],
    # rezystor stojący: okrąg przy nóżce 1 i kreska do nóżki 2
    "res_v": [("circle", 0.0, 0.0, 1.45), ("line", 1.45, 0.0, 2.54 - 0.85, 0.0)],
    # rezystor leżący 33 Ω 1/2 W, 12,7 mm: korpus 9,0 x 3,2
    "res_h": [("line", 1.85, 1.6, 10.85, 1.6), ("line", 10.85, 1.6, 10.85, -1.6), ("line", 10.85, -1.6, 1.85, -1.6),
              ("line", 1.85, -1.6, 1.85, 1.6), ("line", 0.95, 0.0, 1.85, 0.0), ("line", 10.85, 0.0, 11.75, 0.0)],
    # kondensator 100 nF, raster 5,08
    "cap5": [("line", -0.5, 2.1, 5.58, 2.1), ("line", 5.58, 2.1, 5.58, -2.1), ("line", 5.58, -2.1, -0.5, -2.1),
             ("line", -0.5, -2.1, -0.5, 2.1)],
    # elektrolit Ø5: okrąg środek między nóżkami, kreska ujemna po stronie nóżki "-"
    "elco5": [("circle", 1.0, 0.0, 2.6), ("line", 1.9, 2.0, 1.9, -2.0)],
    # LED Ø5: okrąg i płaskie ścięcie po stronie katody (K, x = 2,54)
    "led": [("arc", 1.27, 0.0, 2.6, 125, 235), ("arc", 1.27, 0.0, 2.6, 235, 485), ("line", 3.0, 1.5, 3.0, -1.5)],
    # TO-92: płaska ścianka z napisem (po stronie -y lokalnie), nóżki C B E od lewej
    "to92": [("line", -2.0, -1.3, 2.0, -1.3), ("arc", 0.0, 0.0, 2.4, 330, 570)],
}
# opisy stałe nad/obok pól: (ref, tekst, lx, ly) w układzie lokalnym stopki, rysowane w pionie (nieobrócone)
PIN_LABELS = {
    "C3": [("+", -1.9, 1.9)],
    "D1": [("A", -0.2, 1.9), ("K", 2.9, 1.9)],
    "Q1": [("C", -2.54, -2.3), ("B", 0.0, -2.3), ("E", 2.54, -2.3)],
}


def _poly(cx, cy, r, a0, a1, n=24):
    """Punkty łuku (stopnie, lokalnie) jako lista (x, y)."""
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n)))
            for i in range(n + 1)]


def silk_lines():
    """Opisy stopek jako odcinki w widoku od strony elementów: lista (ref, x0, y0, x1, y1). Okręgi i łuki są łamanymi."""
    out = []
    for ref, part in B.PARTS.items():
        for el in SILK_FP.get(part["fp"], []):
            if el[0] == "line":
                pts = [(el[1], el[2]), (el[3], el[4])]
            elif el[0] == "circle":
                pts = _poly(el[1], el[2], el[3], 0, 360, 32)
            else:
                pts = _poly(el[1], el[2], el[3], el[4], el[5], 24)
            pc = [to_comp(ref, x, y) for x, y in pts]
            out += [(ref, a[0], a[1], b_[0], b_[1]) for a, b_ in zip(pc, pc[1:])]
    return out


if __name__ == "__main__":
    print("płytka %.1f x %.1f, pól: %d, otwory M2,5: %s" % (W, H, len(PADS), HOLES))
    for p in PADS:
        print("%-5s %-3s %-6s (%.2f, %.2f) Ø%.1f/%.1f %s" % (p["ref"], p["pin"], p["net"], p["x"], p["y"], p["d"], p["drill"],
                                                             p["shape"]))
