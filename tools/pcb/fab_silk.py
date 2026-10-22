"""Opisy (silkscreen) płytki głównej: oznaczenia elementów, polaryzacja, nazwy pól przewodów, nazwa płytki.

Dwie warstwy opisów:
  F (strona elementów): oznaczenia elementów (R1, C3...), polaryzacja, wyprowadzenia Q1, nazwy grup przewodów. Teksty nie mogą
     leżeć pod korpusem elementu (po montażu byłyby niewidoczne), na polach lutowniczych, na obrysach ani na sobie.
  B (strona lutowania, tu się lutuje i mierzy): oznaczenia elementów, nazwy pól przewodów i numery pinów U1, nazwa płytki.
     Teksty na B są w widoku od strony lutowania (czytelne po odwróceniu płytki).
Współrzędne tekstów zawsze w widoku od strony elementów (jak wszystko w tym pakiecie); tekst wyśrodkowany w (x, y).
Wysokość 1,0 mm, kreska 0,15 mm: wartości na dolnej granicy czytelności typowych fabryk (minimum ok. 0,8 / 0,15).
"""
import math

import fab  # musi być pierwszy: ustawia wariant klin3 przed importem board
import board as B  # noqa: E402
import fab_drc

H = fab.RULES["silk_height"]
CHAR_W = 0.62                         # szerokość znaku w proporcji do wysokości (czcionka kreskowa KiCada ok. 0,6)

REFS = ["U1", "R1", "R2", "R3", "R4", "R5", "R6", "C1", "C2", "C3", "D1", "Q1"]
GROUPS = {"KEY": "KEY", "DISP": "DISP", "BAT": "BAT", "SPK": "SPK"}
# Opisy pinów w grupach "wszystko albo nic": jeśli nie zmieszczą się wszystkie, zostaje nazwa grupy (albo nic).
F_GROUPS = {"C3": [("+", "+")], "Q1": [("C", "C"), ("B", "B"), ("E", "E")], "D1": [("A", "A"), ("K", "K")],
            "BAT": [("1", "+"), ("2", "-")]}
B_GROUPS = {"KEY": [("1", "GND"), ("2", "PB3"), ("3", "PB4"), ("4", "S3")],
            "DISP": [("1", "SDA"), ("2", "SCL"), ("3", "VCC"), ("4", "GND")],
            "BAT": [("1", "+"), ("2", "-")], "Q1": [("C", "C"), ("B", "B"), ("E", "E")]}
TITLE = "TT-MAIN v1.0"


def text_box(x, y, s, h=H):
    w = CHAR_W * h * len(s)
    return (x - w / 2 - 0.1, y - h / 2 - 0.1, x + w / 2 + 0.1, y + h / 2 + 0.1)


def box_hits_circle(b, cx, cy, r):
    dx = max(b[0] - cx, 0, cx - b[2])
    dy = max(b[1] - cy, 0, cy - b[3])
    return math.hypot(dx, dy) < r


def box_hits_box(a, b):
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


def box_hits_seg(b, x0, y0, x1, y1):
    if b[0] <= x0 <= b[2] and b[1] <= y0 <= b[3]:
        return True
    if b[0] <= x1 <= b[2] and b[1] <= y1 <= b[3]:
        return True
    edges = [((b[0], b[1]), (b[2], b[1])), ((b[2], b[1]), (b[2], b[3])), ((b[2], b[3]), (b[0], b[3])), ((b[0], b[3]), (b[0], b[1]))]
    return any(fab_drc.seg_seg((x0, y0), (x1, y1), e0, e1) < 0.12 for e0, e1 in edges)


def body_boxes():
    """Obrysy korpusów elementów w widoku od strony elementów (z board.py, odbite x' = W - x)."""
    out = {}
    for ref in B.PARTS:
        b = B.body_rect(ref)
        if b is not None and B.FP[B.PARTS[ref]["fp"]]["height"] > 0:
            out[ref] = (fab.W - b[2], b[1], fab.W - b[0], b[3])
    return out


class Placer:
    def __init__(self, avoid_bodies, avoid_silk):
        self.pads = [(p["x"], p["y"], p["d"] / 2 * (1.42 if p["shape"] == "rect" else 1.0) + 0.25) for p in fab.PADS]
        self.silk = [s[1:] for s in fab.silk_lines()] if avoid_silk else []
        self.bodies = list(body_boxes().values()) if avoid_bodies else []
        self.placed = []
        self.warns = []

    def ok(self, b):
        if b[0] < 0.6 or b[1] < 0.6 or b[2] > fab.W - 0.6 or b[3] > fab.H - 0.6:
            return False
        if any(box_hits_circle(b, mx, my, fab.MOUNT_KEEPOUT - 0.4) for mx, my in fab.HOLES):
            return False
        if any(box_hits_circle(b, cx, cy, r) for cx, cy, r in self.pads):
            return False
        if any(box_hits_box(b, pb) for _, pb in self.placed):
            return False
        if any(box_hits_seg(b, *s) for s in self.silk):
            return False
        if any(box_hits_box(b, bb) for bb in self.bodies):
            return False
        return True

    def place(self, label, cx, cy, radii, angles=(90, 270, 0, 180, 45, 135, 225, 315), h=H, name=None):
        for rad in radii:
            for a in ([0] if rad == 0 else angles):
                x, y = cx + rad * math.cos(math.radians(a)), cy + rad * math.sin(math.radians(a))
                b = text_box(x, y, label, h)
                if self.ok(b):
                    self.placed.append(((label, round(x, 3), round(y, 3), h), b))
                    return True
        self.warns.append("%s: brak miejsca na opis „%s”" % (name or "", label))
        return False

    def place_scan(self, label, h=H, name=None):
        """Pierwsze wolne miejsce na planie płytki (od dołu, od lewej)."""
        y = 1.3
        while y < fab.H - 1.0:
            x = 1.5
            while x < fab.W - 1.5:
                b = text_box(x, y, label, h)
                if self.ok(b):
                    self.placed.append(((label, round(x, 3), round(y, 3), h), b))
                    return True
                x += 0.5
            y += 0.5
        self.warns.append("%s: brak miejsca na opis „%s”" % (name or "", label))
        return False

    def place_group(self, ref, items, radii, name):
        """Wszystkie opisy pinów grupy albo żaden. Zwraca True, gdy się udało."""
        n0, w0 = len(self.placed), len(self.warns)
        for pin, txt in items:
            if not self.place(txt, *pad_xy(ref, pin), radii=radii, name="%s.%s" % (name, pin)):
                del self.placed[n0:]
                del self.warns[w0:]
                self.warns.append("%s: pełny opis pinów się nie mieści (%s)" % (name, ", ".join(t for _, t in items)))
                return False
        return True

    def texts(self):
        return [t for t, _ in self.placed]


def centre(ref):
    pts = [(p["x"], p["y"]) for p in fab.PADS if p["ref"] == ref]
    return sum(x for x, _ in pts) / len(pts), sum(y for _, y in pts) / len(pts)


def pad_xy(ref, pin):
    p = next(q for q in fab.PADS if q["ref"] == ref and q["pin"] == pin)
    return p["x"], p["y"]


def layout_f():
    pl = Placer(avoid_bodies=True, avoid_silk=True)
    for ref, items in F_GROUPS.items():
        pl.place_group(ref, items, radii=(1.6, 1.9, 2.1), name="F " + ref)
    for ref in REFS:
        pl.place(ref, *centre(ref), radii=(0.0, 1.6, 2.2, 2.8, 3.4, 4.2, 5.0, 6.0), name="F " + ref)
    for ref, txt in GROUPS.items():
        pl.place(txt, *centre(ref), radii=(2.3, 2.9, 3.5), name="F " + ref)
    return pl.texts(), pl.warns


def layout_b():
    pl = Placer(avoid_bodies=False, avoid_silk=False)
    for ref, items in B_GROUPS.items():
        if not pl.place_group(ref, items, radii=(1.6, 1.9, 2.1), name="B " + ref) and ref in GROUPS:
            pl.place(GROUPS[ref], *centre(ref), radii=(2.3, 2.9, 3.5), name="B " + ref)
    pl.place("SPK", *centre("SPK"), radii=(2.3, 2.9, 3.5), name="B SPK")
    for ref in REFS:
        pl.place(ref, *centre(ref), radii=(0.0, 1.6, 2.2, 2.8, 3.4, 4.2, 5.0, 6.0), name="B " + ref)
    for pin in ("1", "4", "5", "8"):
        pl.place(pin, *pad_xy("U1", pin), radii=(1.6, 1.9, 2.1), name="B U1." + pin)
    pl.place_scan(TITLE, name="B tytuł")
    return pl.texts(), pl.warns


if __name__ == "__main__":
    for side, fn in (("F", layout_f), ("B", layout_b)):
        t, w = fn()
        print(side, len(t), "tekstów")
        for x in t:
            print("  ", x)
        print("  ostrzeżenia:", w)
