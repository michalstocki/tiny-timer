#!/usr/bin/env python3
"""Draws the breadboard (top view) after each stage as SVG, from design.py."""
import math
import os
import sys

import design as d

P = 26            # hole pitch in px
X0 = 78           # x of column 1
Y_TOP = 130       # y of the T+ rail
W = X0 * 2 + (d.COLS - 1) * P
H = 640

# row positions in units of the pitch, measured from the T+ rail
ROW_Y = {"T+": 0, "T-": 1, "a": 2.7, "b": 3.7, "c": 4.7, "d": 5.7, "e": 6.7,
         "f": 8.7, "g": 9.7, "h": 10.7, "i": 11.7, "j": 12.7, "B+": 14.4, "B-": 15.4}

WIRE_RGB = {"red": "#d32f2f", "black": "#212121", "green": "#2e9e3e", "yellow": "#e6b800",
            "orange": "#ef7d00", "blue": "#1e66d0", "violet": "#8e44ad", "gray": "#8a8a8a",
            "white": "#f4f4f4"}
BAND = {"0": "#111", "1": "#7a4a21", "2": "#d32f2f", "3": "#ef7d00", "4": "#e6c800",
        "5": "#2e9e3e", "6": "#1e66d0", "7": "#8e44ad", "8": "#888", "9": "#fff"}
# resistor colour codes (digit, digit, multiplier digit)
RES_BANDS = {"10k": "103", "15k": "153", "8.2k": "822", "470": "471"[:2] + "1", "47k": "473"[:2] + "3", "33": "330"[:2] + "0",
             "4.7k": "472"[:2] + "2"}
RES_BANDS["470"] = "471"  # yellow violet brown
RES_BANDS["47k"] = "473"
RES_BANDS["33"] = "330"
RES_BANDS["4.7k"] = "472"


def hxy(h):
    """Pixel position of a hole address."""
    for r in d.RAILS:
        if h.startswith(r):
            col = int(h[len(r):])
            return X0 + (col - 1) * P, Y_TOP + ROW_Y[r] * P
    row, col = h[0], int(h[1:])
    return X0 + (col - 1) * P, Y_TOP + ROW_Y[row] * P


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def step_labels():
    """Step number of every item: '3.1', '3.2', ... in file order."""
    counters = {}
    out = []
    for it in d.ITEMS:
        n = counters.get(it["stage"], 0) + 1
        counters[it["stage"]] = n
        out.append("%d.%d" % (it["stage"], n))
    return out


class Svg:
    def __init__(self):
        self.parts = []

    def add(self, s):
        self.parts.append(s)

    def text(self, x, y, s, size=11, fill="#222", anchor="middle", weight="normal", extra=""):
        self.add('<text x="%.1f" y="%.1f" font-size="%d" fill="%s" text-anchor="%s" '
                 'font-weight="%s" %s>%s</text>' % (x, y, size, fill, anchor, weight, extra, esc(s)))


def draw_board(svg):
    # board body
    x1, x2 = X0 - 34, X0 + (d.COLS - 1) * P + 34
    yb1, yb2 = Y_TOP - 24, Y_TOP + ROW_Y["B-"] * P + 24
    svg.add('<rect x="%d" y="%d" width="%d" height="%d" rx="8" fill="#ece6d6" stroke="#b9ae93"/>' % (x1, yb1, x2 - x1, yb2 - yb1))
    # centre groove
    yg = Y_TOP + (ROW_Y["e"] + ROW_Y["f"]) / 2 * P
    svg.add('<rect x="%d" y="%.1f" width="%d" height="10" fill="#cfc7b1"/>' % (x1, yg - 5, x2 - x1))
    # rail tints
    for r, colr in (("T+", "#f3c9c9"), ("T-", "#c9d9f3"), ("B+", "#f3c9c9"), ("B-", "#c9d9f3")):
        y = Y_TOP + ROW_Y[r] * P
        svg.add('<rect x="%d" y="%.1f" width="%d" height="%d" rx="6" fill="%s"/>' % (x1 + 14, y - 12, x2 - x1 - 28, 24, colr))
        svg.text(x1 + 7, y + 4, r.replace("-", "−"), 11, "#a00" if "+" in r else "#006", "middle", "bold")
        svg.text(x2 - 7, y + 4, r.replace("-", "−"), 11, "#a00" if "+" in r else "#006", "middle", "bold")
    # holes + row letters
    for r in d.RAILS:
        for c in range(1, d.COLS + 1):
            x, y = hxy("%s%d" % (r, c))
            svg.add('<circle cx="%.1f" cy="%.1f" r="3.2" fill="#2b2b2b"/>' % (x, y))
    for r in "abcdefghij":
        y = Y_TOP + ROW_Y[r] * P
        svg.text(X0 - 20, y + 4, r, 11, "#555")
        svg.text(X0 + (d.COLS - 1) * P + 20, y + 4, r, 11, "#555")
        for c in range(1, d.COLS + 1):
            x = X0 + (c - 1) * P
            svg.add('<circle cx="%.1f" cy="%.1f" r="3.2" fill="#2b2b2b"/>' % (x, y))
    for c in range(1, d.COLS + 1):
        x = X0 + (c - 1) * P
        bold = "bold" if c % 5 == 0 or c == 1 else "normal"
        svg.text(x, Y_TOP + ROW_Y["a"] * P - 16, str(c), 10, "#555", "middle", bold)
        svg.text(x, Y_TOP + ROW_Y["j"] * P + 24, str(c), 10, "#555", "middle", bold)


def pin_xy(it, pin):
    return hxy(it["pins"][pin])


def draw_resistor(svg, it, hi):
    ref = it["ref"]
    val = d.PARTS[ref][1]
    (x1, y1), (x2, y2) = pin_xy(it, "1"), pin_xy(it, "2")
    ang = math.atan2(y2 - y1, x2 - x1)
    length = math.hypot(x2 - x1, y2 - y1)
    body = min(36.0, max(20.0, length - 14))
    if ref == "R4":
        body = min(46.0, length - 12)
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    svg.add('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#9a9a9a" stroke-width="2.2"/>' % (x1, y1, x2, y2))
    g = ['<g transform="translate(%.1f %.1f) rotate(%.1f)">' % (mx, my, math.degrees(ang))]
    g.append('<rect x="%.1f" y="-6" width="%.1f" height="12" rx="5" fill="#e8d3a6" stroke="#8d7a4a"/>' % (-body / 2, body))
    bands = RES_BANDS.get(val, "000")
    n = len(bands)
    for k, ch in enumerate(bands):
        bx = -body / 2 + body * (0.18 + 0.17 * k)
        g.append('<rect x="%.1f" y="-6" width="3.2" height="12" fill="%s"/>' % (bx, BAND[ch]))
    g.append('<rect x="%.1f" y="-6" width="3.2" height="12" fill="#c9a227"/>' % (body / 2 - body * 0.18))
    g.append('</g>')
    svg.add("".join(g))
    return mx, my


def draw_cap(svg, it, hi):
    ref = it["ref"]
    kind = d.PARTS[ref][0]
    pins = list(it["pins"])
    (x1, y1), (x2, y2) = pin_xy(it, pins[0]), pin_xy(it, pins[1])
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    svg.add('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#9a9a9a" stroke-width="2.2"/>' % (x1, y1, x2, y2))
    if kind == "cap":
        svg.add('<rect x="%.1f" y="%.1f" width="16" height="16" rx="4" fill="#d8a63a" stroke="#8a6a1c"/>' % (mx - 8, my - 8))
        svg.text(mx, my + 4, "104", 8, "#222")
    else:
        # electrolytic: blue can with a light stripe on the minus side
        svg.add('<circle cx="%.1f" cy="%.1f" r="11" fill="#243b6b" stroke="#111"/>' % (mx, my))
        sx = (x2 - x1)
        sy = (y2 - y1)
        # minus side stripe
        mxp, myp = pin_xy(it, "-")
        dx, dy = mxp - mx, myp - my
        nrm = math.hypot(dx, dy) or 1
        svg.add('<circle cx="%.1f" cy="%.1f" r="4.5" fill="#cfd8e8"/>' % (mx + dx / nrm * 7, my + dy / nrm * 7))
        svg.text(mx - dx / nrm * 4, my - dy / nrm * 4 + 3, "+", 10, "#fff", "middle", "bold")
        svg.text(mx + dx / nrm * 7, my + dy / nrm * 7 + 3, "−", 10, "#222", "middle", "bold")
    return mx, my


def draw_led(svg, it, hi):
    (xa, ya), (xk, yk) = pin_xy(it, "A"), pin_xy(it, "K")
    mx, my = (xa + xk) / 2, (ya + yk) / 2 - 15
    svg.add('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#9a9a9a" stroke-width="2"/>' % (xa, ya, xa, my + 6))
    svg.add('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#9a9a9a" stroke-width="2"/>' % (xk, yk, xk, my + 6))
    svg.add('<circle cx="%.1f" cy="%.1f" r="9" fill="#ff5a5a" stroke="#a02020"/>' % (mx, my))
    svg.text(xa, ya - 3, "A", 8, "#900", "middle", "bold")
    svg.text(xk, yk - 3, "K", 8, "#900", "middle", "bold")
    return mx, my


def draw_q1(svg, it, hi):
    xs = [pin_xy(it, p)[0] for p in "CBE"]
    y = pin_xy(it, "C")[1]
    cx = xs[1]
    top = y - 36
    # TO-92 seen from above: round body, flat side towards the user (bottom)
    svg.add('<path d="M %.1f %.1f A 22 22 0 1 1 %.1f %.1f Z" fill="#2b2b2b" stroke="#000"/>' % (cx - 17, y - 7, cx + 17, y - 7))
    svg.text(cx, y - 24, "BC547A", 7, "#eee")
    for x, p in zip(xs, "CBE"):
        svg.add('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#9a9a9a" stroke-width="2"/>' % (x, y, x, y - 8))
    # labels below the row
    return cx, top


def draw_ic(svg, it, hi):
    x1, _ = pin_xy(it, "1")
    x4, _ = pin_xy(it, "4")
    ye = hxy("e9")[1]
    yf = hxy("f9")[1]
    xl, xr = x1 - 16, x4 + 16
    svg.add('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="3" fill="#2f2f33" stroke="#000"/>' % (xl, ye - 9, xr - xl, yf - ye + 18))
    svg.add('<path d="M %.1f %.1f a 6 6 0 0 0 0 12" fill="#111" stroke="#777"/>' % (xl, (ye + yf) / 2 - 6))
    svg.text((xl + xr) / 2 + 4, (ye + yf) / 2 + 3, "ATtiny13A", 10, "#ddd", "middle", "bold")
    for pin in "1234":
        x, y = pin_xy(it, pin)
        svg.add('<circle cx="%.1f" cy="%.1f" r="6.5" fill="#aaa"/>' % (x, y))
        svg.text(x, y + 3, pin, 9, "#000", "middle", "bold")
    for pin in "5678":
        x, y = pin_xy(it, pin)
        svg.add('<circle cx="%.1f" cy="%.1f" r="6.5" fill="#aaa"/>' % (x, y))
        svg.text(x, y + 3, pin, 9, "#000", "middle", "bold")
    return (xl + xr) / 2, ye - 12


def draw_switch(svg, it, hi):
    pts = [pin_xy(it, p) for p in ("A1", "A2", "B1", "B2")]
    cx = sum(p[0] for p in pts) / 4
    cy = sum(p[1] for p in pts) / 4
    ref = it["ref"]
    svg.add('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="6" fill="#4a4a50" stroke="#111"/>' % (cx - 62, cy - 62, 124, 124))
    svg.add('<circle cx="%.1f" cy="%.1f" r="30" fill="#1c1c20" stroke="#000"/>' % (cx, cy))
    for (x, y) in pts:
        svg.add('<circle cx="%.1f" cy="%.1f" r="4" fill="#cfcfcf"/>' % (x, y))
    # contacts of one pair are linked inside the switch
    for a, b in ((0, 1), (2, 3)):
        svg.add('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#e0e0e0" stroke-width="2" stroke-dasharray="3 2"/>' % (pts[a][0], pts[a][1], pts[b][0], pts[b][1]))
    svg.text(cx, cy + 6, d.PARTS[ref][1].replace("-", "−"), 20, "#fff", "middle", "bold")
    return cx, cy - 70


def wire_path(a, b, bulge):
    (x1, y1), (x2, y2) = a, b
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    dx, dy = x2 - x1, y2 - y1
    ln = math.hypot(dx, dy) or 1
    nx, ny = -dy / ln, dx / ln
    off = min(22.0, ln * 0.12) * bulge
    cx, cy = mx + nx * off, my + ny * off
    return "M %.1f %.1f Q %.1f %.1f %.1f %.1f" % (x1, y1, cx, cy, x2, y2), (cx * 0.5 + mx * 0.5, cy * 0.5 + my * 0.5)


class Tags:
    """Free-standing end points (UNO, OLED, speaker, battery) at the margins."""

    def __init__(self):
        self.up, self.down = [], []

    def place(self, item_end_xy, name, above):
        (self.up if above else self.down).append([item_end_xy[0], name])

    def layout(self):
        res = {}
        for lst, y in ((self.up, 34), (self.down, H - 70)):
            lst.sort()
            ws = [8 * len(EXT_LABEL.get(e[1], e[1])) * 0.62 + 14 for e in lst]
            xs = [e[0] for e in lst]
            for i in range(1, len(xs)):
                xs[i] = max(xs[i], xs[i - 1] + (ws[i - 1] + ws[i]) / 2 + 6)
            over = (xs[-1] + ws[-1] / 2 - (W - 10)) if xs else 0
            if over > 0:
                xs = [x - over for x in xs]
                for i in range(len(xs) - 2, -1, -1):
                    xs[i] = min(xs[i], xs[i + 1] - (ws[i] + ws[i + 1]) / 2 - 6)
            for (x0, name), x in zip(lst, xs):
                res[name] = (x, y)
        return res


EXT_LABEL = {
    "UNO:RESET": "UNO RESET", "UNO:5V": "UNO 5V", "UNO:GND": "UNO GND", "UNO:D10": "UNO D10",
    "UNO:D11": "UNO D11", "UNO:D12": "UNO D12", "UNO:D13": "UNO D13",
    "OLED:VCC": "OLED VCC", "OLED:GND": "OLED GND", "OLED:SDA": "OLED SDA", "OLED:SCL": "OLED SCL",
    "SPK:1": "głośnik (str. 33 Ω)", "SPK:2": "głośnik (str. kolektora)",
    "BAT:+": "bateria +", "BAT:-": "bateria −",
}


def render(upto, mode, highlight, title, out_path):
    labels = step_labels()
    svg = Svg()
    svg.add('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
            'font-family="Helvetica, Arial, sans-serif">' % (W, H, W, H))
    svg.add('<rect width="%d" height="%d" fill="#ffffff"/>' % (W, H))
    svg.text(W / 2, 20, title, 15, "#111", "middle", "bold")
    draw_board(svg)

    items = [(i, it) for i, it in enumerate(d.ITEMS) if it["stage"] <= upto and mode in it["modes"]]
    if mode == "isp":
        pass
    tags = Tags()
    # collect external tags first
    for i, it in items:
        if it["kind"] == "wire":
            for end, other in (("a", "b"), ("b", "a")):
                if ":" in it[end]:
                    bx, by = hxy(it[other])
                    above = by < Y_TOP + ROW_Y["e"] * P + 8
                    tags.place((bx, by), it[end], above)
    pos = tags.layout()

    def marker(x, y, label, new, optional=False):
        col = "#0b7285" if new else "#7a7a7a"
        svg.add('<circle cx="%.1f" cy="%.1f" r="9.5" fill="%s" stroke="#fff" stroke-width="1.5"/>' % (x, y, col))
        svg.text(x, y + 3.3, label, 8, "#fff", "middle", "bold")

    # draw order: parts under wires
    marks = []
    for i, it in items:
        new = it["stage"] == highlight if highlight else False
        if it["kind"] == "part":
            kind = d.PARTS[it["ref"]][0]
            if kind == "res":
                m = draw_resistor(svg, it, new)
            elif kind in ("cap", "elco"):
                m = draw_cap(svg, it, new)
            elif kind == "led":
                m = draw_led(svg, it, new)
            elif kind == "npn":
                m = draw_q1(svg, it, new)
            elif kind == "ic":
                m = draw_ic(svg, it, new)
            elif kind == "sw":
                m = draw_switch(svg, it, new)
            else:
                continue
            marks.append((m, labels[i], new, it))
    for i, it in items:
        if it["kind"] != "wire":
            continue
        new = it["stage"] == highlight if highlight else False
        a, b = it["a"], it["b"]
        if ":" in a or ":" in b:
            ext, brd = (a, b) if ":" in a else (b, a)
            pa = pos[ext]
            pb = hxy(brd)
            # tag box
            svg.add('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#222" stroke-width="5.2" stroke-linecap="round"/>' % (pa[0], pa[1], pb[0], pb[1]))
            svg.add('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="3.4" stroke-linecap="round"/>' % (pa[0], pa[1], pb[0], pb[1], WIRE_RGB[it["colour"]]))
            lab = EXT_LABEL.get(ext, ext)
            tw = 8 * len(lab) * 0.62 + 10
            svg.add('<rect x="%.1f" y="%.1f" width="%.1f" height="18" rx="4" fill="#fff" stroke="#444"/>' % (pa[0] - tw / 2, pa[1] - 9, tw))
            svg.text(pa[0], pa[1] + 4, lab, 9, "#111")
            mid = ((pa[0] * 2 + pb[0]) / 3, (pa[1] * 2 + pb[1]) / 3)
            marks.append((mid, labels[i], new, it))
        else:
            pa, pb = hxy(a), hxy(b)
            path, mid = wire_path(pa, pb, 1)
            svg.add('<path d="%s" fill="none" stroke="#222" stroke-width="5.4" stroke-linecap="round"/>' % path)
            svg.add('<path d="%s" fill="none" stroke="%s" stroke-width="3.6" stroke-linecap="round"/>' % (path, WIRE_RGB[it["colour"]]))
            marks.append((mid, labels[i], new, it))
    # end-point dots of leads inserted in holes
    for i, it in items:
        for h in ([it["a"], it["b"]] if it["kind"] == "wire" else list(it["pins"].values())):
            if ":" in h:
                continue
            x, y = hxy(h)
            svg.add('<circle cx="%.1f" cy="%.1f" r="2.6" fill="#f2f2f2" stroke="#111" stroke-width="0.8"/>' % (x, y))
    # pin function labels of the ATtiny (only when it is on the board)
    if any(it["kind"] == "part" and it["ref"] == "U1" for _, it in items):
        names = {"1": "RESET", "2": "PB3", "3": "PB4", "4": "GND", "5": "PB0", "6": "PB1", "7": "PB2", "8": "VCC"}
        u1 = next(it for _, it in items if it["kind"] == "part" and it["ref"] == "U1")
        for pin, nm in names.items():
            x, y = pin_xy(u1, pin)
            if int(pin) <= 4:
                svg.text(x, y + 26, nm, 8, "#555")
            else:
                svg.text(x, y - 20, nm, 8, "#555")
    # step badges on top
    for m, lab, new, it in marks:
        x, y = m
        if it["kind"] == "part" and d.PARTS[it["ref"]][0] == "sw":
            y -= 4
        marker(x, y, lab, new)
    # legend
    ly = H - 34
    x = 40
    for c in ("red", "black", "green", "yellow", "orange", "blue", "violet", "gray", "white"):
        svg.add('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#222" stroke-width="5.4" stroke-linecap="round"/>' % (x, ly, x + 22, ly))
        svg.add('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="3.6" stroke-linecap="round"/>' % (x, ly, x + 22, ly, WIRE_RGB[c]))
        meaning = {"red": "VCC", "black": "GND", "green": "SDA/MOSI", "yellow": "SCL/SCK", "orange": "PB3 run",
                   "blue": "PB4", "violet": "RESET", "gray": "PB1/MISO", "white": "głośnik"}[c]
        svg.text(x + 27, ly + 4, meaning, 9, "#333", "start")
        x += 88
    svg.text(40, ly + 20, "Numer w kółku = numer kroku w instrukcji (turkusowy: nowy w tym etapie). "
             "Kolumny 1–30 od lewej, rzędy a–e nad rowkiem, f–j pod rowkiem.", 9, "#555", "start")
    svg.add("</svg>")
    with open(out_path, "w") as f:
        f.write("\n".join(svg.parts))


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(out, exist_ok=True)
    jobs = [
        (0, "work", 0, "Płytka stykowa, 60 kolumn: układ współrzędnych", "plansza.svg"),
        (1, "work", 1, "Etap 1: zasilanie z baterii i ATtiny13A", "etap-1.svg"),
        (3, "work", 3, "Etap 3: głośnik", "etap-3.svg"),
        (4, "work", 4, "Etap 4: wyświetlacz OLED", "etap-4.svg"),
        (5, "work", 5, "Etap 5: przyciski (układ kompletny)", "etap-5.svg"),
    ]
    for upto, mode, hl, title, name in jobs:
        render(upto, mode, hl, title, os.path.join(out, name))
        print("wrote", os.path.join(out, name))


if __name__ == "__main__":
    main()
