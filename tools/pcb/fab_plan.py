"""Rysunki do instrukcji montażu płytki głównej: plan montażu (strona elementów) i plan pomiarów (strona lutowania)."""
import math

import fab
import fab_render as FR

S = 32.0     # px/mm
M = 40

VALUES = {"U1": "ATtiny13A + gniazdo DIP-8", "R1": "15 k", "R2": "470", "R3": "47 k", "R4": "33 Ω ½ W", "R5": "8,2 k", "R6": "8,2 k",
          "C1": "100 nF", "C2": "100 nF", "C3": "100 µF", "D1": "LED", "Q1": "BC547", "SPK": "głośnik", "BAT": "bateria", "KEY": "przyciski",
          "DISP": "wyświetlacz"}
GROUP_PINS = {("KEY", "1"): "GND", ("KEY", "2"): "PB3", ("KEY", "3"): "PB4", ("KEY", "4"): "S3",
              ("DISP", "1"): "SDA", ("DISP", "2"): "SCL", ("DISP", "3"): "VCC", ("DISP", "4"): "GND",
              ("BAT", "1"): "+", ("BAT", "2"): "−"}
STEP = {"U1": 1, "R1": 2, "R2": 2, "R3": 2, "R4": 2, "R5": 2, "R6": 2, "C1": 3, "C2": 3, "D1": 4, "Q1": 5, "C3": 6,
        "KEY": 7, "DISP": 7, "SPK": 7, "BAT": 7}
STEP_COL = {1: "#ffd166", 2: "#ef8354", 3: "#06d6a0", 4: "#c77dff", 5: "#4cc9f0", 6: "#f72585", 7: "#adb5bd"}


def _esc(t):
    return t.replace("&", "&amp;")


class Canvas:
    def __init__(self, mirror=False):
        self.mirror = mirror
        self.w = int(fab.W * S + 2 * M)
        self.h = int(fab.H * S + 2 * M + 44)
        self.o = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" font-family="Helvetica, Arial, sans-serif">'
                  % (self.w, self.h, self.w, self.h), '<rect width="100%" height="100%" fill="#fff"/>']
        self.boxes = []

    def X(self, x):
        return M + ((fab.W - x) if self.mirror else x) * S

    def Y(self, y):
        return M + (fab.H - y) * S

    def label(self, x, y, text, size=12, weight="bold", fill="#111", bg="#ffffffd0", anchor="middle"):
        w = 0.6 * size * len(text) + 6
        h = size + 4
        px, py = self.X(x), self.Y(y)
        self.o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="3" fill="%s"/>' % (px - w / 2, py - h / 2, w, h, bg))
        self.o.append('<text x="%.1f" y="%.1f" font-size="%d" font-weight="%s" fill="%s" text-anchor="middle">%s</text>'
                      % (px, py + size * 0.36, size, weight, fill, _esc(text)))
        self.boxes.append((px - w / 2, py - h / 2, px + w / 2, py + h / 2))

    def free_spot(self, x, y, text, size, radii, avoid_pads=True):
        """Pierwsze miejsce w pobliżu (x, y) bez nakładania na inne etykiety i pola; zwraca (x, y) w mm."""
        w = 0.6 * size * len(text) + 6
        h = size + 4
        for r in radii:
            for a in ([0] if r == 0 else (90, 270, 0, 180, 45, 135, 225, 315)):
                cx = x + r * math.cos(math.radians(a))
                cy = y + r * math.sin(math.radians(a))
                px, py = self.X(cx), self.Y(cy)
                b = (px - w / 2, py - h / 2, px + w / 2, py + h / 2)
                if b[0] < 4 or b[2] > self.w - 4 or b[1] < 4 or b[3] > self.h - 50:
                    continue
                if any(not (b[2] <= q[0] or q[2] <= b[0] or b[3] <= q[1] or q[3] <= b[1]) for q in self.boxes):
                    continue
                if avoid_pads and any(math.hypot(self.X(p["x"]) - min(max(self.X(p["x"]), b[0]), b[2]),
                                                 self.Y(p["y"]) - min(max(self.Y(p["y"]), b[1]), b[3])) < p["d"] / 2 * S + 2
                                      for p in fab.PADS):
                    continue
                return cx, cy
        return x, y

    def board(self, design, side):
        o = self.o
        o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%.1f" fill="%s" stroke="%s" stroke-width="2"/>'
                 % (M, M, fab.W * S, fab.H * S, fab.CORNER_R * S, FR.COL["board"], FR.COL["edge"]))
        first, second = (0, 1) if side == "F" else (1, 0)
        for L, alpha in ((second, 0.25), (first, 0.9)):
            c = FR.COL["f"] if L == 0 else FR.COL["b"]
            for (net, l, a, b_) in design["tracks"]:
                if l == L:
                    o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-opacity="%.2f" stroke-width="%.1f" '
                             'stroke-linecap="round"/>' % (self.X(a[0]), self.Y(a[1]), self.X(b_[0]), self.Y(b_[1]), c, alpha,
                                                           fab.RULES["track"] * S))
        for (net, x, y) in design["vias"]:
            o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s"/><circle cx="%.1f" cy="%.1f" r="%.1f" fill="#fff"/>'
                     % (self.X(x), self.Y(y), fab.RULES["via_d"] / 2 * S, FR.COL["pad"], self.X(x), self.Y(y), fab.RULES["via_drill"] / 2 * S))
        for p in fab.PADS:
            if p["shape"] == "rect":
                h = p["d"] / 2 * S
                o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s"/>' % (self.X(p["x"]) - h, self.Y(p["y"]) - h, 2 * h, 2 * h,
                                                                                         FR.COL["pad"]))
            else:
                o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s"/>' % (self.X(p["x"]), self.Y(p["y"]), p["d"] / 2 * S, FR.COL["pad"]))
            o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="#fff"/>' % (self.X(p["x"]), self.Y(p["y"]), p["drill"] / 2 * S))
        for (mx, my) in fab.HOLES:
            o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="#fff" stroke="%s" stroke-width="1.5"/>'
                     % (self.X(mx), self.Y(my), fab.MOUNT_D / 2 * S, FR.COL["edge"]))
            self.boxes.append((self.X(mx) - 40, self.Y(my) - 40, self.X(mx) + 40, self.Y(my) + 40))

    def silk(self):
        for (_, x0, y0, x1, y1) in fab.silk_lines():
            self.o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#f4f4f0" stroke-width="2.2" stroke-linecap="round"/>'
                          % (self.X(x0), self.Y(y0), self.X(x1), self.Y(y1)))

    def finish(self, caption):
        self.o.append('<text x="%d" y="%d" font-size="14" fill="#222">%s</text>' % (M, self.h - 16, _esc(caption)))
        self.o.append("</svg>")
        return "\n".join(self.o)


def centre(ref):
    pts = [(p["x"], p["y"]) for p in fab.PADS if p["ref"] == ref]
    return sum(x for x, _ in pts) / len(pts), sum(y for _, y in pts) / len(pts)


def plan_montazu(design):
    c = Canvas(mirror=False)
    c.board(design, "F")
    c.silk()
    # pola grup przewodów: nazwy pinów
    for (ref, pin), txt in GROUP_PINS.items():
        p = next(q for q in fab.PADS if q["ref"] == ref and q["pin"] == pin)
        x, y = c.free_spot(p["x"], p["y"], "%s %s" % (ref, pin) if False else txt, 11, (1.7, 2.1, 2.6, 3.2))
        c.label(x, y, txt, size=11, fill="#7a0019", bg="#ffe8ecee")
    # oznaczenia elementów: numer kroku, ref, wartość
    for ref in fab.B.PARTS:
        if ref in ("KEY", "DISP", "SPK", "BAT"):
            cx, cy = centre(ref)
            txt = "%s %s" % (ref, VALUES[ref])
            x, y = c.free_spot(cx, cy, txt, 12, (2.6, 3.4, 4.2, 5.0))
            c.label(x, y, txt, size=12, bg="#dee2e6ee")
            continue
        cx, cy = centre(ref)
        txt = "%s  %s" % (ref, VALUES[ref])
        x, y = c.free_spot(cx, cy, txt, 12, (0.0, 1.5, 2.2, 3.0, 3.8, 4.6), avoid_pads=True)
        c.label(x, y, "%d. %s" % (STEP[ref], txt), size=12, bg=STEP_COL[STEP[ref]] + "ee")
    return c.finish("Plan montażu: strona elementów (F). Numer przed oznaczeniem = etap montażu. Pola kwadratowe: pin 1 / plus / anoda.")


def plan_pomiarow(design):
    c = Canvas(mirror=True)
    c.board(design, "B")
    for p in fab.PADS:
        pin = p["pin"]
        txt = "%s.%s" % (p["ref"], pin)
        x, y = c.free_spot(p["x"], p["y"], txt, 10, (1.5, 1.9, 2.3, 2.8, 3.4))
        c.label(x, y, txt, size=10, bg="#ffffffee")
    return c.finish("Plan pomiarów: strona lutowania (B), widok odbity (lewa i prawa strona zamienione względem planu montażu).")
