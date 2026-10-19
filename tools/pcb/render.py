#!/usr/bin/env python3
"""SVG previews of the preliminary PCB: front (top), back (bottom, mirrored as
seen when the board is turned over), and a side elevation with heights."""
import math

import board as B
import router as R

S = 14.0          # px per mm
M = 40            # margin px


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;")


class Canvas:
    def __init__(self, w, h, mirror=False):
        self.W, self.H, self.mirror = w, h, mirror
        self.p = []

    def X(self, x):
        return M + (B.P["W"] - x if self.mirror else x) * S

    def Y(self, y):
        return M + (B.P["H"] - y) * S

    def add(self, s):
        self.p.append(s)

    def text(self, x, y, t, size=9, fill="#222", anchor="middle", weight="normal", rot=0):
        tr = (' transform="rotate(%d %.1f %.1f)"' % (rot, self.X(x), self.Y(y))) if rot else ""
        self.add('<text x="%.1f" y="%.1f" font-size="%.1f" fill="%s" text-anchor="%s" font-weight="%s"%s>%s</text>'
                 % (self.X(x), self.Y(y) + size * 0.35, size, fill, anchor, weight, tr, esc(t)))

    def circle(self, x, y, r, fill="none", stroke="#000", sw=1, extra=""):
        self.add('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" stroke="%s" stroke-width="%.1f" %s/>'
                 % (self.X(x), self.Y(y), r * S, fill, stroke, sw, extra))

    def rect(self, x0, y0, x1, y1, fill="none", stroke="#000", sw=1, rx=0, extra=""):
        xa, xb = sorted([self.X(x0), self.X(x1)])
        ya, yb = sorted([self.Y(y0), self.Y(y1)])
        self.add('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%.1f" fill="%s" stroke="%s" stroke-width="%.1f" %s/>'
                 % (xa, ya, xb - xa, yb - ya, rx, fill, stroke, sw, extra))

    def line(self, x0, y0, x1, y1, stroke, sw, extra=""):
        self.add('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="%.1f" stroke-linecap="round" %s/>'
                 % (self.X(x0), self.Y(y0), self.X(x1), self.Y(y1), stroke, sw * S, extra))

    def svg(self):
        return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
                'font-family="Helvetica, Arial, sans-serif">' % (self.W, self.H, self.W, self.H) +
                '<rect width="100%" height="100%" fill="#ffffff"/>' + "".join(self.p) + "</svg>")


def outline(c):
    W, H, r = B.P["W"], B.P["H"], B.P["corner_r"]
    c.rect(0, 0, W, H, fill="#2f6b3a", stroke="#14391c", sw=2, rx=r * S)
    for (x, y) in B.mount_holes():
        c.circle(x, y, B.P["mount_d"] / 2, fill="#ffffff", stroke="#14391c", sw=1.5)
        c.circle(x, y, B.P["mount_keepout_r"], fill="none", stroke="#fff", sw=0.8, extra='stroke-dasharray="3 3" opacity="0.6"')


def pads(c, refs, label_net=True):
    pin_net = {}
    for net, lst in B.NETS.items():
        for (ref, pin) in lst:
            pin_net[(ref, pin)] = net
    for ref in refs:
        fp = B.FP[B.PARTS[ref]["fp"]]
        for pin, (x, y) in B.pad_positions(ref).items():
            sq = (ref == "U1" and pin == "1")
            if sq:
                c.rect(x - fp["pad"] / 2, y - fp["pad"] / 2, x + fp["pad"] / 2, y + fp["pad"] / 2, fill="#d9b44a", stroke="#7a5f10", sw=0.8)
            else:
                c.circle(x, y, fp["pad"] / 2, fill="#d9b44a", stroke="#7a5f10", sw=0.8)
            c.circle(x, y, fp["hole"] / 2, fill="#ffffff", stroke="#555", sw=0.6)
        for (bx, by) in fp.get("bosses", []):
            p = B.PARTS[ref]
            c.circle(p["x"] + bx, p["y"] + by, B.P["btn_boss_d"] / 2, fill="#ffffff", stroke="#555", sw=0.8)


def traces(c, res, layer, colour):
    segs = R.merge_segments(res["tracks"])
    for net, lst in segs.items():
        for (a, b, L) in lst:
            if L == layer:
                c.line(a[0], a[1], b[0], b[1], colour, B.P["track_w"])
    for net, pts in res["vias"].items():
        for (x, y) in pts:
            c.circle(x, y, B.P["via_d"] / 2, fill="#e8e8e8", stroke="#333", sw=0.8)
            c.circle(x, y, B.P["via_drill"] / 2, fill="#333", stroke="none", sw=0)


def labels(c, refs, size=8):
    for ref in refs:
        pp = B.pad_positions(ref)
        xs = [v[0] for v in pp.values()]
        ys = [v[1] for v in pp.values()]
        c.text(sum(xs) / len(xs), max(ys) + 1.8, ref, size, "#fff", "middle", "bold")


def dims(c):
    W, H = B.P["W"], B.P["H"]
    c.add('<text x="%d" y="22" font-size="12" font-weight="bold">%s</text>' % (M, esc(c.title)))
    c.add('<text x="%d" y="%d" font-size="10" fill="#444">%.0f × %.0f mm, grubość %.1f mm; widok od %s</text>'
          % (M, c.H - 12, W, H, B.P["thickness"], c.side_txt))


def top_view(res):
    W, H = B.P["W"], B.P["H"]
    c = Canvas(int(W * S + 2 * M), int(H * S + 2 * M + 30))
    c.title, c.side_txt = ("Przód (strona TOP): wyświetlacz i przyciski" if B.VARIANT == "base" else "Przód (strona TOP): wyświetlacz (przyciski na osobnej płytce)"), "przodu (osie: x w prawo, y w górę, początek w lewym dolnym rogu)"
    outline(c)
    traces(c, res, 0, "#c9423b")
    if B.K3:                        # no display and no buttons on this board: only pads/joints and the traces
        c.title = "Przód (strona TOP, od strony ścianki): same pola i lut, elementy są z tyłu"
        pads(c, B.PARTS.keys())
        c.text(B.P["W"] / 2, B.P["H"] + 1.7, "GÓRA (ku wierzchołkowi obudowy)", 8, "#555")
        dims(c)
        return c.svg()
    # bodies on top
    ox0, oy0, ox1, oy1 = B.body_rect("OLED")
    c.rect(ox0, oy0, ox1, oy1, fill="#16335f", stroke="#0a1a33", sw=1.5, rx=2)
    gx0 = B.D["oled_pin_x"] + B.P["glass_to_pin"]
    c.rect(gx0, B.D["oled_cy"] - B.P["glass_h"] / 2, gx0 + B.P["glass_w"], B.D["oled_cy"] + B.P["glass_h"] / 2, fill="#05070b", stroke="#6b7a96", sw=1)
    c.text(gx0 + B.P["glass_w"] / 2, B.D["oled_cy"], "szkło 25 × 10", 9, "#6b7a96")
    for ref in [r for r in ("S3", "S1", "S2") if r in B.PARTS]:
        p = B.PARTS[ref]
        c.rect(p["x"] - 6, p["y"] - 6, p["x"] + 6, p["y"] + 6, fill="#3a3a40", stroke="#111", sw=1.2, rx=3)
        c.circle(p["x"], p["y"], B.P["btn_cap_d"] / 2, fill="#202024", stroke="#000", sw=1)
        c.rect(p["x"] - 1.9, p["y"] - 1.9, p["x"] + 1.9, p["y"] + 1.9, fill="#555", stroke="#000", sw=0.8)
        c.text(p["x"], p["y"] - 8.2, {"S3": "−", "S1": "run", "S2": "+"}[ref], 11, "#222", "middle", "bold")
    pads(c, B.PARTS.keys())
    # top-side leads of back-side parts (joints appear here): mark pads only
    c.text(B.P["W"] / 2, B.P["H"] + 1.7, "GÓRA", 8, "#555")
    dims(c)
    return c.svg()


def bottom_view(res):
    W, H = B.P["W"], B.P["H"]
    c = Canvas(int(W * S + 2 * M), int(H * S + 2 * M + 30), mirror=True)
    c.title, c.side_txt = "Tył (strona BOTTOM): elementy na odwrocie", "tyłu (płytka obrócona wokół osi pionowej; lewo i prawo odbite)"
    outline(c)
    traces(c, res, 1, "#2a6fd6")
    for ref in B.REFS_BOTTOM:
        b = B.body_rect(ref)
        if b is None:
            continue
        fill = {"U1": "#2b2b30", "C3": "#243b6b", "D1": "#ff9a9a", "Q1": "#222"}.get(ref, "#e8d3a6")
        c.rect(b[0], b[1], b[2], b[3], fill=fill, stroke="#111", sw=1, rx=2, extra='opacity="0.85"')
    pads(c, [r for r in B.PARTS if B.PARTS[r]["side"] == "bottom"])
    pads_top_only = [r for r in B.PARTS if B.PARTS[r]["side"] == "top"]
    for ref in pads_top_only:
        # these leads protrude on the back; pads are visible as dots
        pads(c, [ref])
    for ref in B.REFS_BOTTOM:
        pp = B.pad_positions(ref)
        xs = [v[0] for v in pp.values()]
        ys = [v[1] for v in pp.values()]
        c.text(sum(xs) / len(xs), sum(ys) / len(ys) + 0.0, ref, 8, "#000", "middle", "bold")
    c.text(B.P["W"] / 2, B.P["H"] + 1.7, "TYŁ", 8, "#555")
    dims(c)
    return c.svg()
