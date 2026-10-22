#!/usr/bin/env python3
"""Płytka przycisków na płytce uniwersalnej 2,54 mm: kontrola projektu, szablon 1:1, schemat połączeń (PDF).

    python3 tools/pcb/button_board.py            # sprawdza projekt i zapisuje docs/plytka-przyciskow/
    python3 tools/pcb/button_board.py --check    # tylko sprawdzenie (bez plików)

Wejście: docs/pcb-klin3/pcb-layout.json, klucz button_board (zarys, przyciski, otwory M2).
Dane przycisku: karta Omron B3F (A070-E1-08), s. 6, model B3F-4055 (bez nóżki masy):
  nóżki 12,5 x 5,0 mm, otwory Ø1,2, dwa kołki ustalające Ø1,8 co 9,0 mm na osi między kolumnami nóżek;
  połączenia wewnętrzne (widok z góry): 4-3 oraz 2-1 połączone na stałe, wciśnięcie zwiera górny rząd z dolnym.
PDF powstaje z SVG przez rsvg-convert (1 jednostka SVG = 1 mm, strona A4, skala 1:1 bez przeskalowania).
"""
import json
import math
import shutil
import subprocess
import sys
import tempfile
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LAYOUT = ROOT / "docs/pcb-klin3/pcb-layout.json"
OUT = ROOT / "docs/plytka-przyciskow"
PDF = OUT / "plytka-przyciskow-szablon.pdf"

G = 2.54                       # raster płytki uniwersalnej
LEG_DX, LEG_DY = 12.5, 5.0     # rozstaw nóżek B3F (karta)
BODY = 12.0                    # korpus B3F 12 x 12
BOSS_DY = 4.5                  # kołki ustalające: ±4,5 mm od osi nóżek (9,0 mm między nimi)
BOSS_D, LEG_HOLE_D, M2_D = 1.8, 1.2, 2.2
HEAD_R = 2.0                   # łeb wkręta M2 (pan head Ø4) od strony lutowania
COLS = "ABCDEFGHIJKLMNOPQRST"

# ---------------------------------------------------------------- dane z projektu obudowy
BB = json.loads(LAYOUT.read_text())["button_board"]
W, D, T, R_CORNER = BB["width"], BB["depth"], BB["thickness"], BB["corner_radius"]
BUTTONS = sorted(BB["buttons"], key=lambda b: b["x"])          # S3 (−), S1 (run), S2 (+)
M2 = [(h["x"], h["y"]) for h in BB["mounting_holes"]]
NAME = {"minus": "−", "run": "run", "plus": "+"}

# raster: nóżki pierwszego przycisku (x ± 6,35, y ± 2,54) leżą na oczkach
COL0 = BUTTONS[0]["x"] - 2.5 * G
ROW0 = BUTTONS[0]["y"] - 3 * G
NCOL = int((W - COL0) / G + 1e-9) + 1
NROW = int((D - ROW0) / G + 1e-9) + 1


def hole(k, j):
    return COL0 + k * G, ROW0 + j * G


def addr(k, j):
    return COLS[k] + str(j + 1)


def parse(a):
    return COLS.index(a[0]), int(a[1:]) - 1


def hxy(a):
    return hole(*parse(a))


def legs(b):
    """Nóżki przycisku: numer z karty (widok z góry: 4 lewa góra, 3 prawa góra, 2 lewa dół, 1 prawa dół) -> adres oczka."""
    kc = (b["x"] - COL0) / G
    kl = round(kc - 2.5)
    jb = round((b["y"] - G - ROW0) / G)
    return {4: addr(kl, jb + 2), 3: addr(kl + 5, jb + 2), 2: addr(kl, jb), 1: addr(kl + 5, jb)}


LEGS = {b["ref"]: legs(b) for b in BUTTONS}

# ---------------------------------------------------------------- połączenia (strona lutowania)
# przewód rozdzielczy (np. wire-wrap Ø0,25, w izolacji): (od, do, sieć, punkty pośrednie w mm lub None = prosto)
JUMPERS = [
    ("M5", "N4", "GND", None),
    ("O5", "N4", "GND", None),
    ("M3", "N2", "PB3", None),
    ("F3", "G4", "PB4", None),
    ("O3", "G4", "PB4", [(None, 6.73), (16.11, 6.73)]),        # trasa po rowku między rzędami 3 i 4, z dala od łba wkręta
    ("F5", "G6", "KEY4", None),
]
CABLE = {"KEY1": ("N4", "GND", "czarny"), "KEY2": ("N2", "PB3", "pomarańczowy"),
         "KEY3": ("G4", "PB4", "niebieski"), "KEY4": ("G6", "S3 (−) górna strona", "zielony")}
NETCOLOR = {"GND": "#111111", "PB3": "#e07b00", "PB4": "#1565c0", "KEY4": "#2e7d32"}
WIRE_SLACK = 6.0               # naddatek na zdjęcie izolacji i lutowanie (obie końcówki razem)


def wire_path(j):
    a, b, _, via = j
    p0, p1 = hxy(a), hxy(b)
    pts = [p0]
    for vx, vy in via or []:
        pts.append((p0[0] if vx is None else vx, vy))
    pts.append(p1)
    return pts


def path_len(pts):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


# ---------------------------------------------------------------- kontrola projektu
def uf_make():
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        parent[find(a)] = find(b)
    return find, union


def netlist(pressed):
    """Które pola KEY są zwarte, gdy wciśnięte są przyciski z listy `pressed` (karta: 4-3 i 2-1 stałe, wciśnięcie zwiera rzędy)."""
    find, union = uf_make()
    for ref, lg in LEGS.items():
        union(lg[4], lg[3])
        union(lg[2], lg[1])
        if ref in pressed:
            union(lg[3], lg[1])
    for a, b, _, _ in JUMPERS:
        union(a, b)
    keys = {k: find(v[0]) for k, v in CABLE.items()}
    return {frozenset(k for k in keys if keys[k] == r) for r in set(keys.values())}


def check():
    errors, notes = [], []
    err = errors.append

    # geometria rastra
    if not (0 < COL0 < G and 0 < ROW0 < G):
        err("raster nie zaczyna się w pierwszym oczku")
    last_x, last_y = hole(NCOL - 1, NROW - 1)
    notes.append("raster: %d kolumn (A-%s) x %d rzędów, pierwsze oczko (%.2f; %.2f), ostatnie (%.2f; %.2f), zarys %.0f x %.0f"
                 % (NCOL, COLS[NCOL - 1], NROW, COL0, ROW0, last_x, last_y, W, D))
    for b in BUTTONS:
        kc = (b["x"] - COL0) / G
        if abs(kc - 2.5 - round(kc - 2.5)) > 1e-6:
            err("przycisk %s: nóżki nie leżą na oczkach (kolumna %.4f)" % (b["ref"], kc))
    for (mx, my) in M2:
        kx, ky = (mx - COL0) / G, (my - ROW0) / G
        if abs(kx - round(kx)) > 1e-6 or abs(ky - round(ky)) > 1e-6:
            err("otwór M2 (%.2f; %.2f) nie leży na oczku" % (mx, my))

    # nóżki względem karty (12,5 x 5,0)
    dev = []
    for b in BUTTONS:
        for n, a in LEGS[b["ref"]].items():
            x, y = hxy(a)
            ix = b["x"] + (LEG_DX / 2 if n in (3, 1) else -LEG_DX / 2)
            iy = b["y"] + (LEG_DY / 2 if n in (4, 3) else -LEG_DY / 2)
            dev.append((abs(x - ix), abs(y - iy)))
    dxm, dym = max(d[0] for d in dev), max(d[1] for d in dev)
    notes.append("odchyłka oczek od położenia nóżek z karty: max %.2f mm (x), %.2f mm (y); karta: 12,5 ±0,5 (długość nóżek), "
                 "otwory ±0,1" % (dxm, dym))
    if dxm > 0.25 or dym > 0.1:
        err("oczka za daleko od nóżek (%.2f / %.2f)" % (dxm, dym))

    # logika: dla każdej kombinacji wciśniętych przycisków porównaj z modelem „S1: KEY1-KEY2, S2: KEY1-KEY3, S3: KEY3-KEY4”
    model = {"S1": ("KEY1", "KEY2"), "S2": ("KEY1", "KEY3"), "S3": ("KEY3", "KEY4")}
    for n in range(4):
        for combo in product(("S1", "S2", "S3"), repeat=n):
            find, union = uf_make()
            for k in CABLE:
                find(k)
            for ref in set(combo):
                union(*model[ref])
            exp = {}
            for k in CABLE:
                exp.setdefault(find(k), set()).add(k)
            exp = {frozenset(v) for v in exp.values()}
            got = netlist(set(combo))
            if got != exp:
                err("wciśnięte %s: oczekiwano %s, jest %s" % (combo or "nic", sorted(map(sorted, exp)), sorted(map(sorted, got))))
    notes.append("logika: puszczone = 4 osobne pola; S1 zwiera KEY1-KEY2, S2 zwiera KEY1-KEY3, S3 zwiera KEY3-KEY4; "
                 "sprawdzone wszystkie kombinacje wciśnięć (OK)")

    # oczka: poprawne, nie na otworach M2, bez kolizji z łbem wkręta, poza korpusami przycisków
    used = {}
    for ref, lg in LEGS.items():
        for n, a in lg.items():
            used[a] = used.get(a, 0) + 1
    for a, b, _, _ in JUMPERS:
        used[a] = used.get(a, 0) + 1
        used[b] = used.get(b, 0) + 1
    for k, (a, _, _) in CABLE.items():
        used[a] = used.get(a, 0) + 1
    m2_addr = {addr(round((x - COL0) / G), round((y - ROW0) / G)) for x, y in M2}
    for a, cnt in sorted(used.items()):
        k, j = parse(a)
        if not (0 <= k < NCOL and 0 <= j < NROW):
            err("oczko %s poza rastrem" % a)
        if a in m2_addr:
            err("oczko %s to otwór M2" % a)
        x, y = hole(k, j)
        if min(x, y, W - x, D - y) < 0.8:
            err("oczko %s leży przy samej krawędzi (%.2f mm): pole zostałoby przecięte" % (a, min(x, y, W - x, D - y)))
        for mx, my in M2:
            if math.dist((x, y), (mx, my)) < HEAD_R + 1.4:
                err("oczko %s za blisko łba wkręta M2 (%.2f mm)" % (a, math.dist((x, y), (mx, my))))
        if cnt > 3:
            err("oczko %s: %d przewodów (max 3)" % (a, cnt))
    own = {a for lg in LEGS.values() for a in lg.values()}
    for k, (a, _, _) in CABLE.items():
        x, y = hxy(a)
        for b in BUTTONS:
            if abs(x - b["x"]) < BODY / 2 + 1.0 and abs(y - b["y"]) < BODY / 2 + 1.0:
                err("pole %s (%s) leży pod korpusem %s lub przy nim (od strony elementów zasłonięte)" % (k, a, b["ref"]))
        if a in own:
            err("pole %s na nóżce" % k)
    # trasy przewodów omijają łeb wkręta
    for j in JUMPERS:
        pts = wire_path(j)
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            for mx, my in M2:
                dx, dy = x1 - x0, y1 - y0
                t = max(0, min(1, ((mx - x0) * dx + (my - y0) * dy) / (dx * dx + dy * dy)))
                dist = math.dist((mx, my), (x0 + t * dx, y0 + t * dy))
                if dist < HEAD_R + 0.3:
                    err("przewód %s-%s przechodzi %.2f mm od osi wkręta M2" % (j[0], j[1], dist))
    # kołki ustalające i M2 względem korpusów
    for (mx, my) in M2:
        for b in BUTTONS:
            if abs(mx - b["x"]) < BODY / 2 + 1.8 and abs(my - b["y"]) < BODY / 2 + 1.8:
                err("słupek M2 (%.2f; %.2f) koliduje z korpusem %s" % (mx, my, b["ref"]))
    return errors, notes


# ---------------------------------------------------------------- SVG
FONT = "Helvetica, Arial, sans-serif"
MONO = "Menlo, Courier New, monospace"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class Svg:
    def __init__(self, w=210, h=297):
        self.w, self.h, self.e = w, h, []

    def add(self, s):
        self.e.append(s)

    def line(self, x1, y1, x2, y2, w=0.2, c="#000", dash=None, cap="butt"):
        d = ' stroke-dasharray="%s"' % dash if dash else ""
        self.add('<line x1="%.3f" y1="%.3f" x2="%.3f" y2="%.3f" stroke="%s" stroke-width="%.3f"%s stroke-linecap="%s"/>'
                 % (x1, y1, x2, y2, c, w, d, cap))

    def poly(self, pts, w=0.3, c="#000", dash=None, fill="none", close=False):
        d = ' stroke-dasharray="%s"' % dash if dash else ""
        tag = "polygon" if close else "polyline"
        self.add('<%s points="%s" fill="%s" stroke="%s" stroke-width="%.3f"%s stroke-linejoin="round" stroke-linecap="round"/>'
                 % (tag, " ".join("%.3f,%.3f" % p for p in pts), fill, c, w, d))

    def circ(self, x, y, r, w=0.2, c="#000", fill="none", dash=None):
        d = ' stroke-dasharray="%s"' % dash if dash else ""
        self.add('<circle cx="%.3f" cy="%.3f" r="%.3f" fill="%s" stroke="%s" stroke-width="%.3f"%s/>' % (x, y, r, fill, c, w, d))

    def rect(self, x, y, w, h, sw=0.2, c="#000", fill="none", dash=None, rx=0):
        d = ' stroke-dasharray="%s"' % dash if dash else ""
        self.add('<rect x="%.3f" y="%.3f" width="%.3f" height="%.3f" rx="%.3f" fill="%s" stroke="%s" stroke-width="%.3f"%s/>'
                 % (x, y, w, h, rx, fill, c, sw, d))

    def text(self, x, y, s, size=3.2, c="#000", anchor="start", weight="normal", font=FONT, rot=0, italic=False):
        tr = ' transform="rotate(%.1f %.3f %.3f)"' % (rot, x, y) if rot else ""
        st = ' font-style="italic"' if italic else ""
        self.add('<text x="%.3f" y="%.3f" font-family="%s" font-size="%.3f" fill="%s" text-anchor="%s" font-weight="%s"%s%s>%s</text>'
                 % (x, y, font, size, c, anchor, weight, st, tr, esc(s)))

    def label(self, x, y, s_, size=3.2, anchor="start", pad=0.6, **kw):
        """Tekst na białym tle (czytelny nad kropkami siatki)."""
        w = 0.56 * size * len(s_) + 2 * pad
        x0 = x if anchor == "start" else (x - w + pad if anchor == "end" else x - w / 2)
        self.add('<rect x="%.3f" y="%.3f" width="%.3f" height="%.3f" fill="#fff"/>' % (x0 - pad * (anchor == "start"), y - size * 0.85,
                                                                                    w, size * 1.15))
        self.text(x, y, s_, size=size, anchor=anchor, **kw)

    def para(self, x, y, lines, size=3.2, lead=1.45, **kw):
        for i, s in enumerate(lines):
            self.text(x, y + i * size * lead, s, size=size, **kw)
        return y + len(lines) * size * lead

    def save(self, path):
        body = "\n".join(self.e)
        path.write_text('<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="%dmm" height="%dmm" '
                        'viewBox="0 0 %d %d">\n<rect width="%d" height="%d" fill="#fff"/>\n%s\n</svg>\n'
                        % (self.w, self.h, self.w, self.h, self.w, self.h, body))


class View:
    """Płytka na stronie: (x, y) w mm płytki (y w górę) -> mm strony. mirror = widok od strony lutowania (odbicie względem osi pionowej)."""

    def __init__(self, ox, oy, scale=1.0, mirror=False):
        self.ox, self.oy, self.s, self.m = ox, oy, scale, mirror

    def p(self, x, y):
        return (self.ox + ((W - x) if self.m else x) * self.s, self.oy + (D - y) * self.s)

    def outline(self):
        x0, y0 = self.p(0, D)
        x1, y1 = self.p(W, 0)
        return min(x0, x1), y0, abs(x1 - x0), y1 - y0


def board_outline(svg, v, w=0.35, c="#000", dash=None, fill="none"):
    x, y, ww, hh = v.outline()
    svg.rect(x, y, ww, hh, sw=w, c=c, fill=fill, dash=dash, rx=R_CORNER * v.s)


def grid_dots(svg, v, r_hole=0.5, inside_only=False, margin=0, color="#777", labels=False, label_size=1.6):
    for k in range(NCOL):
        for j in range(NROW):
            x, y = hole(k, j)
            px, py = v.p(x, y)
            svg.circ(px, py, r_hole * v.s, w=0.12 * (1 if v.s == 1 else 0.8), c=color)
    if margin:
        k0 = -int(margin // G) - 1
        for k in range(k0, NCOL + int(margin // G) + 2):
            for j in range(-int(margin // G) - 1, NROW + int(margin // G) + 2):
                if 0 <= k < NCOL and 0 <= j < NROW:
                    continue
                x, y = hole(k, j)
                if -margin <= x <= W + margin and -margin <= y <= D + margin:
                    px, py = v.p(x, y)
                    svg.circ(px, py, r_hole * v.s, w=0.1, c="#bbb")


def button_footprint(svg, v, b, with_labels=True):
    cx, cy = b["x"], b["y"]
    x0, y0 = v.p(cx - BODY / 2, cy + BODY / 2)
    x1, y1 = v.p(cx + BODY / 2, cy - BODY / 2)
    svg.rect(min(x0, x1), y0, abs(x1 - x0), y1 - y0, sw=0.2, c="#444", dash="1.2 0.8", rx=0.4 * v.s)
    px, py = v.p(cx, cy)
    svg.circ(px, py, 3.55 * v.s, w=0.15, c="#999", dash="0.6 0.6")
    svg.rect(px - 1.9 * v.s, py - 1.9 * v.s, 3.8 * v.s, 3.8 * v.s, sw=0.15, c="#999")
    svg.line(px - 1.2 * v.s, py, px + 1.2 * v.s, py, w=0.12, c="#999")
    svg.line(px, py - 1.2 * v.s, px, py + 1.2 * v.s, w=0.12, c="#999")


def legs_marks(svg, v, b, hole_d=LEG_HOLE_D, num_size=1.9):
    for n, a in LEGS[b["ref"]].items():
        x, y = hxy(a)
        px, py = v.p(x, y)
        svg.circ(px, py, hole_d / 2 * v.s, w=0.25 if v.s == 1 else 0.4, c="#000")
        sgn = -1 if v.m else 1
        dx = (-1.6 if n in (4, 2) else 1.6) * v.s * sgn
        svg.text(px + dx, py + (-0.9 if n in (4, 3) else 2.2) * v.s * (1 if v.s == 1 else 0.9), str(n), size=num_size * (1 if v.s == 1 else 1.7),
                 anchor="middle", c="#000", weight="bold")


# ---------------------------------------------------------------- strona 1: szablon 1:1
def page_template():
    s = Svg()
    ox, oy = (210 - W) / 2, 70.0
    v = View(ox, oy, 1.0)
    s.text(105, 14, "Płytka przycisków 50 × 16 mm: szablon w skali 1:1", size=6.2, anchor="middle", weight="bold")
    s.text(105, 21, "widok od strony ELEMENTÓW (od strony, z której wchodzą nóżki przycisków)", size=3.6, anchor="middle")
    s.text(105, 26.5, "płytka uniwersalna jednostronna FR4 1,6 mm, raster 2,54 mm, osobne pola lutownicze (nie paskowa)",
           size=3.0, anchor="middle", c="#333")
    s.rect(20, 31, 170, 9, sw=0.5, c="#c00")
    s.text(105, 37, "DRUKUJ W SKALI 100 % (Rzeczywisty rozmiar). Wyłącz „Dopasuj do strony”.", size=4.0, anchor="middle", c="#c00",
           weight="bold")

    # siatka w otoczeniu: do nakładania na prawdziwą płytkę
    grid_dots(s, v, color="#888", margin=9.0)
    board_outline(s, v, w=0.4)
    for k in range(NCOL):
        px, py = v.p(hole(k, 0)[0], 0)
        s.label(px, oy + D + 4.0, COLS[k], size=1.9, anchor="middle", c="#555")
    for j in range(NROW):
        px, py = v.p(0, hole(0, j)[1])
        s.label(ox - 1.6, py + 0.7, str(j + 1), size=1.9, anchor="end", c="#555")

    for b in BUTTONS:
        button_footprint(s, v, b)
        for n, a in LEGS[b["ref"]].items():
            px, py = v.p(*hxy(a))
            s.circ(px, py, LEG_HOLE_D / 2, w=0.25)
        for dy in (-BOSS_DY, BOSS_DY):
            bx, by = v.p(b["x"], b["y"] + dy)
            s.circ(bx, by, BOSS_D / 2, w=0.2, c="#b05a00", dash="0.5 0.4")
            s.line(bx - 0.9, by, bx + 0.9, by, w=0.12, c="#b05a00")
            s.line(bx, by - 0.9, bx, by + 0.9, w=0.12, c="#b05a00")

    # otwory M2 z opisem poza płytką
    for i, (mx, my) in enumerate(M2, 1):
        px, py = v.p(mx, my)
        s.line(px - 4.5, py, px + 4.5, py, w=0.25)
        s.line(px, py - 4.5, px, py + 4.5, w=0.25)
        s.circ(px, py, M2_D / 2, w=0.5, c="#c00")
        s.circ(px, py, 0.18, w=0.1, c="#c00", fill="#c00")
        ly = oy - 9 if my > D / 2 else oy + D + 10
        s.line(px, py, px, ly + (1.2 if my > D / 2 else -2.8), w=0.15, c="#c00")
        s.label(px, ly, "M2-%d: Ø2,2" % i, size=2.8, anchor="middle", c="#c00", weight="bold")

    # wymiary
    top = oy - 3
    s.line(ox, oy - 0.5, ox, top - 1, w=0.1, c="#555")
    s.line(ox + W, oy - 0.5, ox + W, top - 1, w=0.1, c="#555")
    s.line(ox, top, ox + W, top, w=0.15, c="#555")
    s.label(ox + W / 2 - 18, top + 0.9, "50,00", size=2.8, anchor="middle", weight="bold")
    s.line(ox + W + 1, oy, ox + W + 6, oy, w=0.1, c="#555")
    s.line(ox + W + 1, oy + D, ox + W + 6, oy + D, w=0.1, c="#555")
    s.line(ox + W + 5, oy, ox + W + 5, oy + D, w=0.15, c="#555")
    s.label(ox + W + 6.5, oy + D / 2 + 1, "16,00", size=2.8, weight="bold")
    yb = oy + D + 17
    xs = [0] + [b["x"] for b in BUTTONS] + [W]
    s.line(ox, yb, ox + W, yb, w=0.12, c="#555")
    for xv in xs:
        s.line(ox + xv, yb - 1.2, ox + xv, yb + 1.2, w=0.12, c="#555")
    for xa, xb in zip(xs, xs[1:]):
        s.label(ox + (xa + xb) / 2, yb + 3.6, "%.2f" % (xb - xa), size=2.2, anchor="middle", c="#333")
    for b in BUTTONS:
        s.line(ox + b["x"], yb - 1.2, ox + b["x"], yb - 12, w=0.1, c="#999", dash="0.6 0.6")
        s.text(ox + b["x"], yb - 3.0, "%s  %s" % (b["ref"], NAME[b["label"]]), size=3.0, anchor="middle", weight="bold")
    s.text(105, yb + 8.5, "osie przycisków co 17,78 mm (7 oczek), skrajne 7,22 mm od krawędzi; wymiary od lewej krawędzi",
           size=2.5, anchor="middle", c="#333")
    s.text(105, yb + 12.2, "dolna krawędź (y = 0): strona frontu, górna (y = 16): strona płytki głównej, lewa (x = 0): strona głośnika",
           size=2.5, anchor="middle", c="#333")

    # legenda
    ly = 128
    s.text(20, ly, "Legenda", size=4.0, weight="bold")
    leg = [("rect", "linia cięcia (zarys 50 × 16, narożniki R2)"),
           ("m2", "otwór M2: nawiercić Ø2,2 (2 szt.), środek = przecięcie osi"),
           ("hole", "oczko pod nóżkę B3F (12 szt.); karta zaleca otwory Ø1,2"),
           ("boss", "kołek ustalający B3F Ø1,8: ODCIĄĆ nożykiem (zalecane) albo wywiercić Ø1,8"),
           ("body", "obrys korpusu B3F 12 × 12, podstawa trzpienia Ø7,1, trzpień 3,8 × 3,8"),
           ("dot", "oczka płytki uniwersalnej (szare kropki poza zarysem: do wyrównania z prawdziwą płytką)")]
    for i, (kind, txt) in enumerate(leg):
        y = ly + 6 + i * 6.5
        if kind == "rect":
            s.rect(21, y - 3, 8, 4, sw=0.4, rx=1)
        elif kind == "m2":
            s.circ(25, y - 1, 1.1, w=0.5, c="#c00")
        elif kind == "hole":
            s.circ(25, y - 1, 0.6, w=0.25)
        elif kind == "boss":
            s.circ(25, y - 1, 0.9, w=0.2, c="#b05a00", dash="0.5 0.4")
        elif kind == "body":
            s.rect(21, y - 3, 8, 4, sw=0.2, c="#444", dash="1.2 0.8")
        else:
            s.circ(25, y - 1, 0.5, w=0.12, c="#888")
        s.text(33, y, txt, size=3.0)

    # tabela współrzędnych
    ty = 176
    s.text(20, ty, "Otwory do wywiercenia (od lewego dolnego narożnika zarysu, widok od strony elementów)", size=3.9, weight="bold")
    s.line(20, ty + 2, 190, ty + 2, w=0.3)
    rows = [("otwór", "x [mm]", "y [mm]", "Ø [mm]", "oczko", "uwagi")]
    for i, (mx, my) in enumerate(M2, 1):
        rows.append(("M2-%d" % i, "%.2f" % mx, "%.2f" % my, "2,2", addr(round((mx - COL0) / G), round((my - ROW0) / G)),
                     "wkręt M2 x 6 od strony lutowania"))
    for b in BUTTONS:
        for dy in (-BOSS_DY, BOSS_DY):
            rows.append(("kołek %s" % b["ref"], "%.2f" % b["x"], "%.2f" % (b["y"] + dy), "1,8", "-", "tylko jeśli nie odcinasz kołków"))
    colx = [20, 46, 66, 86, 104, 124]
    for i, r in enumerate(rows):
        y = ty + 7 + i * 4.6
        for x, t in zip(colx, r):
            s.text(x, y, t, size=3.0, font=MONO if i else FONT, weight="bold" if i == 0 else "normal",
                   c="#b05a00" if r[0].startswith("kołek") else "#000")
    # skala
    sy = 238
    s.text(20, sy - 4, "Kontrola skali wydruku: odcinek ma mieć dokładnie 100,0 mm, kwadrat 20 × 20 mm", size=3.2, weight="bold")
    s.line(20, sy + 2, 120, sy + 2, w=0.3)
    for i in range(11):
        s.line(20 + i * 10, sy, 20 + i * 10, sy + 4, w=0.2)
        s.text(20 + i * 10, sy + 8, str(i * 10), size=2.2, anchor="middle")
    s.rect(140, sy - 3, 20, 20, sw=0.3)
    s.text(150, sy + 8, "20 × 20", size=2.4, anchor="middle")
    howto = ["Jak używać:",
             "1) Przyklej szablon do płytki uniwersalnej tak, by kropki szablonu pokryły się z oczkami płytki.",
             "2) Nakłuj igłą środki M2, zdejmij szablon, wywierć Ø1,0 a potem Ø2,2 (płytkę zamocuj w imadle).",
             "3) Wytnij płytkę po linii cięcia (zostaw 0,2 mm na pilnik), zaokrąglij narożniki R2.",
             "4) Przymierz nóżki B3F w oczkach przed lutowaniem. Pełna instrukcja: README.md."]
    s.para(20, 266, howto, size=2.9, lead=1.4)
    s.text(20, 290, "Dane: pcb-layout.json (button_board), karta Omron B3F s. 6 (B3F-4055). Wygenerowano: tools/pcb/button_board.py",
           size=2.4, c="#666")
    return s


# ---------------------------------------------------------------- strona 2: połączenia od strony lutowania, 3:1
def page_wiring():
    s = Svg()
    sc = 3.0
    ox, oy = (210 - W * sc) / 2, 58.0
    v = View(ox, oy, sc, mirror=True)
    s.text(105, 14, "Połączenia: widok od strony LUTOWANIA (skala 3:1)", size=6.0, anchor="middle", weight="bold")
    s.text(105, 20.5, "płytkę obrócono jak kartkę wokół osi pionowej: kolumny idą od T (z lewej) do A (z prawej), rzędy 1-7 od dołu",
           size=3.1, anchor="middle", c="#333")
    s.text(105, 30.5, "Przewody w izolacji układaj płasko po stronie lutowania, nie wyżej niż końcówki nóżek (ok. 2 mm). "
           "Opis nóżki: przycisk/numer z karty Omron.", size=2.9, anchor="middle", c="#333")

    board_outline(s, v, w=0.5)
    grid_dots(s, v, r_hole=0.5, color="#aaa")
    for k in range(NCOL):
        px, py = v.p(hole(k, 0)[0], 0)
        s.text(px, oy - 3.2, COLS[k], size=3.0, anchor="middle", c="#555")
        s.text(px, oy + D * sc + 6.5, COLS[k], size=3.0, anchor="middle", c="#555")
    for j in range(NROW):
        px, py = v.p(0, hole(0, j)[1])
        s.text(ox - 4, py + 1.0, str(j + 1), size=3.0, anchor="end", c="#555")
        s.text(ox + W * sc + 4, py + 1.0, str(j + 1), size=3.0, anchor="start", c="#555")

    # obrysy przycisków (po drugiej stronie)
    for b in BUTTONS:
        button_footprint(s, v, b)
        x0, _ = v.p(b["x"] - BODY / 2, 0)
        x1, _ = v.p(b["x"] + BODY / 2, 0)
        s.line(x0, oy - 11.5, x1, oy - 11.5, w=0.4, c="#888")
        s.line(x0, oy - 11.5, x0, oy - 9.5, w=0.4, c="#888")
        s.line(x1, oy - 11.5, x1, oy - 9.5, w=0.4, c="#888")
        s.text((x0 + x1) / 2, oy - 14, "%s  %s  (po drugiej stronie)" % (b["ref"], NAME[b["label"]]), size=3.4, anchor="middle",
               weight="bold", c="#555")
    # M2: łeb wkręta
    for i, (mx, my) in enumerate(M2, 1):
        px, py = v.p(mx, my)
        s.circ(px, py, M2_D / 2 * sc, w=0.5, c="#c00")
        s.circ(px, py, HEAD_R * sc, w=0.3, c="#c00", dash="1.5 1")
        s.text(px, py + 0.9, "M2", size=3.0, anchor="middle", c="#c00", weight="bold")

    # nóżki
    for b in BUTTONS:
        for n, a in LEGS[b["ref"]].items():
            px, py = v.p(*hxy(a))
            s.circ(px, py, 1.15, w=0.4, c="#000", fill="#fff")
            s.text(px, py - 2.0 if n in (4, 3) else py + 4.6, "%s/%d" % (b["ref"], n), size=2.5, anchor="middle", weight="bold")
    # przewody rozdzielcze
    for j in JUMPERS:
        pts = [v.p(*q) for q in wire_path(j)]
        s.poly(pts, w=0.9, c=NETCOLOR[j[2]])
        for q in (pts[0], pts[-1]):
            s.circ(q[0], q[1], 1.0, w=0.3, c=NETCOLOR[j[2]], fill=NETCOLOR[j[2]])
    # pola przewodu do płytki głównej: opis obok oczka (strona wolna od przewodów)
    side = {"KEY1": 1, "KEY2": 1, "KEY3": 1, "KEY4": 1}       # +1: w prawo na rysunku, -1: w lewo
    desc = {"KEY1": "KEY1  GND", "KEY2": "KEY2  PB3", "KEY3": "KEY3  PB4", "KEY4": "KEY4  → R6"}
    for k, (a, net, col) in CABLE.items():
        px, py = v.p(*hxy(a))
        s.circ(px, py, 2.4, w=0.6, c="#000")
        s.circ(px, py, 1.0, w=0.3, c="#000", fill="#fff")
        sd = side[k]
        s.line(px + sd * 2.4, py, px + sd * 6, py, w=0.35, c="#000")
        s.label(px + sd * 7, py + 1.2, desc[k], size=3.6, anchor="start" if sd > 0 else "end", weight="bold")

    # legenda + tabela przewodów
    ly = oy + D * sc + 18
    s.text(20, ly, "Lista przewodów (adres oczka = kolumna + rząd z tego rysunku)", size=4.0, weight="bold")
    s.line(20, ly + 2, 190, ly + 2, w=0.3)
    head = ("nr", "od", "do", "sieć", "kolor", "trasa", "przewód")
    colx = [20, 31, 43, 70, 86, 114, 138]
    for x, t in zip(colx, head):
        s.text(x, ly + 7, t, size=3.0, weight="bold")
    rows = []
    for i, j in enumerate(JUMPERS, 1):
        L = path_len(wire_path(j))
        col = {"GND": "czarny", "PB3": "pomarańczowy", "PB4": "niebieski", "KEY4": "zielony"}[j[2]]
        rows.append(("W%d" % i, j[0], j[1], j[2], col, "%.1f mm + %.0f" % (L, WIRE_SLACK / 2), "izolowany Ø0,25"))
    for k, (a, net, col) in CABLE.items():
        rows.append((k, a, "pł. główna", {"KEY4": "R6"}.get(k, net), col, "wg obudowy", "linka 0,14 mm²"))
    for i, r in enumerate(rows):
        y = ly + 12.5 + i * 5.1
        for x, t in zip(colx, r):
            s.text(x, y, t, size=3.0, font=MONO)
        if i < len(JUMPERS):
            net = JUMPERS[i][2]
            s.line(26.5, y - 1.0, 29.5, y - 1.0, w=0.9, c=NETCOLOR[net])
    yy = ly + 12.5 + len(rows) * 5.1 + 3
    s.para(20, yy, ["Kolory: czarny = GND, pomarańczowy = PB3, niebieski = PB4, zielony = KEY4 (S3 do R6); ten sam kolor na rysunku i w kablu.",
                    "Trasa „x mm + 3”: odległość oczek + 3 mm na końcówki (zdjęcie izolacji, zagięcie, lutowanie).",
                    "Oczka z trzema przewodami: N4 i G4 (przewód do płytki głównej + dwa rozdzielcze, cienkie).",
                    "Przewód W5 (PB4) biegnie rowkiem między rzędami 3 i 4: omija łeb wkręta M2 (czerwone kółko przerywane)."],
           size=2.8, lead=1.5, c="#333")
    return s


# ---------------------------------------------------------------- strona 3: schemat, test
def switch_symbol(svg, x, y, w=22):
    """Wyłącznik SPST poziomy od (x, y) do (x+w, y)."""
    svg.circ(x, y, 0.8, w=0.4, fill="#fff")
    svg.circ(x + w, y, 0.8, w=0.4, fill="#fff")
    svg.line(x + 0.8, y, x + w - 4, y - 5.0, w=0.45)


def page_schematic():
    s = Svg()
    s.text(105, 14, "Schemat elektryczny płytki przycisków", size=6.2, anchor="middle", weight="bold")
    s.text(105, 20, "3 × Omron B3F-4055 (SPST-NO), 4 przewody do pól KEY płytki głównej", size=3.6, anchor="middle")

    x0, x1 = 78, 122          # wyłączniki
    ys = {"S1": 50, "S2": 72, "S3": 94}
    lab = {"S1": "S1  „run”", "S2": "S2  „+”", "S3": "S3  „−”"}
    for ref, y in ys.items():
        switch_symbol(s, x0, y, x1 - x0)
        s.text((x0 + x1) / 2, y - 8, lab[ref], size=3.6, anchor="middle", weight="bold")
    # lewy: KEY2 -> S1, szyna KEY3 -> S2 i S3
    kx = 44
    s.text(24, 38, "płytka przycisków", size=2.8, c="#666", italic=True)
    s.line(kx, 50, x0, 50, w=0.5, c=NETCOLOR["PB3"])
    s.line(kx, 72, x0, 72, w=0.5, c=NETCOLOR["PB4"])
    s.line(62, 72, 62, 94, w=0.5, c=NETCOLOR["PB4"])
    s.line(62, 94, x0, 94, w=0.5, c=NETCOLOR["PB4"])
    s.circ(62, 72, 0.9, w=0.3, c=NETCOLOR["PB4"], fill=NETCOLOR["PB4"])
    # prawy: GND szyna S1, S2; KEY4 -> S3
    gx = 138
    s.line(x1, 50, gx, 50, w=0.5, c=NETCOLOR["GND"])
    s.line(x1, 72, gx, 72, w=0.5, c=NETCOLOR["GND"])
    s.line(gx, 50, gx, 72, w=0.5, c=NETCOLOR["GND"])
    s.circ(gx, 72, 0.9, w=0.3, fill="#111")
    s.line(gx, 72, 154, 72, w=0.5, c=NETCOLOR["GND"])
    s.line(x1, 94, 154, 94, w=0.5, c=NETCOLOR["KEY4"])
    for name, y, net, sub in (("KEY2", 50, "PB3", "pin 2, pull-up wewnętrzny"), ("KEY3", 72, "PB4", "pin 3, R5 8,2 kΩ do VCC")):
        s.circ(kx, y, 1.6, w=0.5, fill="#fff")
        s.text(kx - 3.5, y + 1.2, name, size=3.4, anchor="end", weight="bold")
        s.text(kx - 3.5, y + 5.0, "%s: %s" % (net, sub), size=2.4, anchor="end", c="#444")
    s.circ(154, 72, 1.6, w=0.5, fill="#fff")
    s.text(157.5, 73.2, "KEY1", size=3.4, weight="bold")
    s.text(157.5, 77, "GND", size=2.6, c="#444")
    s.circ(154, 94, 1.6, w=0.5, fill="#fff")
    s.text(157.5, 95.2, "KEY4", size=3.4, weight="bold")
    s.text(157.5, 99, "do R6 8,2 kΩ → GND", size=2.4, c="#444")
    s.para(20, 108, ["Na płytce głównej: PB3 ma wewnętrzny pull-up, PB4 ma R5 (8,2 kΩ do VCC), a KEY4 jest połączone z GND przez R6 (8,2 kΩ).",
                     "Szczegóły: docs/schemat.md. Każdy przycisk jest na płytce uniwersalnej połączony z polami KEY krótkimi przewodami (strona 2)."],
           size=2.8, lead=1.5, c="#333")

    # wnętrze B3F
    bx, by = 25, 130
    s.text(20, by - 3, "Wnętrze B3F-4055 (karta Omron s. 6, widok z góry)", size=4.0, weight="bold")
    s.rect(bx + 8, by + 4, 30, 28, sw=0.4, rx=4)
    for n, (tx, ty) in {4: (bx + 8, by + 10), 3: (bx + 38, by + 10), 2: (bx + 8, by + 26), 1: (bx + 38, by + 26)}.items():
        s.rect(tx - 1.2, ty - 1.2, 2.4, 2.4, sw=0.3, fill="#000")
        s.text(tx + (-4 if n in (4, 2) else 4), ty + 1.0, str(n), size=3.4, anchor="middle", weight="bold")
    s.line(bx + 8, by + 10, bx + 38, by + 10, w=0.4)
    s.line(bx + 8, by + 26, bx + 38, by + 26, w=0.4)
    s.circ(bx + 23, by + 10, 0.8, w=0.3, fill="#000")
    s.circ(bx + 23, by + 26, 0.8, w=0.3, fill="#000")
    s.line(bx + 23, by + 26, bx + 23, by + 21, w=0.4)
    s.line(bx + 23, by + 10, bx + 23, by + 15, w=0.4)
    s.line(bx + 23, by + 21, bx + 26, by + 15.5, w=0.4)
    s.text(bx + 52, by + 8, "4 – 3 połączone na stałe", size=3.0)
    s.text(bx + 52, by + 28, "2 – 1 połączone na stałe", size=3.0)
    s.text(bx + 52, by + 18, "wciśnięcie zwiera górny rząd z dolnym", size=3.0, weight="bold")
    s.text(bx + 52, by + 34, "nóżki 4–3 oraz 2–1 dzieli 12,5 mm (dłuższy bok), rzędy dzieli 5,0 mm", size=2.6, c="#333")

    # test multimetrem
    ty = 180
    s.text(20, ty, "Kontrola multimetrem (zakres ciągłości / Ω) po zakończeniu lutowania", size=4.0, weight="bold")
    s.line(20, ty + 2, 190, ty + 2, w=0.3)
    cols = [20, 62, 100, 138]
    head = ("mierz między", "przyciski puszczone", "wciśnij", "oczekiwany wynik")
    for x, t in zip(cols, head):
        s.text(x, ty + 7, t, size=3.0, weight="bold")
    tests = [("KEY1 – KEY2", "rozwarcie (OL)", "S1 „run”", "< 1 Ω"),
             ("KEY1 – KEY3", "rozwarcie (OL)", "S2 „+”", "< 1 Ω"),
             ("KEY3 – KEY4", "rozwarcie (OL)", "S3 „−”", "< 1 Ω"),
             ("KEY1 – KEY4", "rozwarcie (OL)", "S1 lub S2", "rozwarcie (OL)"),
             ("KEY2 – KEY3", "rozwarcie (OL)", "S3", "rozwarcie (OL)")]
    for i, r in enumerate(tests):
        for x, t in zip(cols, r):
            s.text(x, ty + 12.5 + i * 5.2, t, size=3.0, font=MONO)
    s.para(20, ty + 41, ["Przed lutowaniem przewodów, na przycisku (nawet luźnym): nóżki 4–3 (12,5 mm) oraz 2–1 mają mieć ciągłość zawsze,",
                         "a 4–2 oraz 3–1 (5,0 mm) tylko po wciśnięciu. Jeśli jest odwrotnie, przycisk nie jest zgodny z kartą:",
                         "nie lutuj dalej i zmierz wszystkie sześć par nóżek."], size=2.8, lead=1.5, c="#333")
    s.text(20, 290, "Źródło połączeń wewnętrznych: Omron B3F (A070-E1-08), s. 6. Sprawdzone programowo: tools/pcb/button_board.py",
           size=2.4, c="#666")
    return s


# ---------------------------------------------------------------- strona 4: lista zakupów i skrót montażu
def page_assembly():
    s = Svg()
    s.text(105, 14, "Lista części i skrót montażu", size=6.2, anchor="middle", weight="bold")
    s.text(105, 20, "pełna instrukcja z uzasadnieniem: docs/plytka-przyciskow/README.md", size=3.2, anchor="middle", c="#333")
    y = 32
    s.text(20, y, "Części i narzędzia", size=4.2, weight="bold")
    s.line(20, y + 2, 190, y + 2, w=0.3)
    bom = ["3 × Omron B3F-4055 (trzpień wystający 7,3 mm, 2,55 N, bez nóżki masy; NIE B3F-4155)",
           "1 × płytka uniwersalna jednostronna FR4 1,6 mm, raster 2,54 mm, osobne pola (min. 55 × 20 mm, lepiej 70 × 30)",
           "6 × przewód rozdzielczy w izolacji Ø0,25 (wire-wrap AWG30), razem ok. 10 cm",
           "4 × linka 0,14 mm² w czterech kolorach (czarny, pomarańczowy, niebieski, zielony), długość wg obudowy",
           "2 × wkręt samogwintujący M2 × 6 (łeb od strony lutowania), cyna z topnikiem bezmyjnym",
           "wiertła Ø1,0 i Ø2,2 (opcjonalnie Ø1,2), imadło, piła do laminatu lub miniszlifierka z tarczą, pilnik, nożyk, "
           "szczypce tnące, multimetr, lutownica z grotem 1-2 mm"]
    s.para(22, y + 8, ["•  " + b_ for b_ in bom], size=3.0, lead=1.55)
    y = 92
    s.text(20, y, "Kolejność montażu", size=4.2, weight="bold")
    s.line(20, y + 2, 190, y + 2, w=0.3)
    steps = ["0. Na przycisku (nawet luźnym) sprawdź multimetrem: nóżki 4–3 oraz 2–1 (12,5 mm) mają ciągłość zawsze, 4–2 i 3–1 tylko po wciśnięciu.",
             "1. Wydrukuj stronę 1 w skali 100 % i sprawdź linijką odcinek 100 mm. Przyłóż do płytki: kropki szablonu na oczka płytki.",
             "2. Płytkę zamocuj w imadle na podkładce z drewna. Nakłuj M2, wywierć Ø1,0 a potem Ø2,2 (2 otwory).",
             "3. Wytnij zarys 50 × 16 mm (odchyłka do ±0,3), opiłuj, zaokrąglij narożniki R2, usuń zadziory.",
             "4. Odetnij kołki ustalające B3F równo z korpusem (od spodu). Przymierz nóżki w oczkach: jeśli wchodzą z oporem, rozwierć Ø1,2.",
             "5. Włóż 3 przyciski (korpusem do płytki, bokami równolegle do krawędzi). Zalutuj po jednej nóżce, sprawdź prostopadłość,",
             "    potem resztę (12 lutów, krótko, bez mycia płytki: karta B3F mówi, że mycie nie jest możliwe).",
             "6. Zalutuj przewody rozdzielcze W1-W6 po stronie lutowania wg strony 2 (płasko, w izolacji, z dala od łbów wkrętów M2).",
             "7. Zalutuj 4 przewody do płytki głównej (KEY1-KEY4) w oczka N4, N2, G4, G6. Końcówki po stronie elementów utnij równo z laminatem.",
             "8. Kontrola multimetrem wg strony 3. Sprawdź, czy żaden lut ani przewód nie wystaje ponad końcówki nóżek (ok. 2 mm).",
             "9. Płytkę przykręć do słupków pokrywy dwoma wkrętami M2 × 6 od strony lutowania, założ kapsle na trzpienie."]
    s.para(20, y + 8, steps, size=3.0, lead=1.55)
    y = 195
    s.text(20, y, "Najczęstsze pułapki", size=4.2, weight="bold")
    s.line(20, y + 2, 190, y + 2, w=0.3)
    trap = ["•  Płytka paskowa (stripboard) zewrze nóżki: potrzebne są osobne pola lutownicze.",
            "•  Raster płytki musi mieć 2,54 mm: skrajne oczka A i T rzędu mają trafić w kropki A i T szablonu (odległość 48,26 mm).",
            "•  Odwrócony szablon: wiercenie i przyciski robisz od strony ELEMENTÓW. Połączenia rysunku 2 są od strony lutowania (odbicie).",
            "•  Lut lub przewód pod łbem wkręta M2 przechyli płytkę: trzymaj przewody z dala od czerwonych kółek M2 na stronie 2.",
            "•  Kołki ustalające nie mieszczą się w oczkach: nie wciskaj przycisku siłą, odetnij kołki.",
            "•  Przycisk lutuj krótko (kilka sekund na nóżkę): plastikowy korpus mięknie od długiego grzania."]
    s.para(20, y + 8, trap, size=3.0, lead=1.55)
    s.text(20, 290, "Dane: karta Omron B3F (A070-E1-08), s. 6; obudowa: docs/obudowa-klin-4. Wygenerowano: tools/pcb/button_board.py",
           size=2.4, c="#666")
    return s


# ---------------------------------------------------------------- wyjście
def build():
    if shutil.which("rsvg-convert") is None:
        sys.exit("brak rsvg-convert (brew install librsvg)")
    OUT.mkdir(parents=True, exist_ok=True)
    pages = [("szablon", page_template()), ("polaczenia", page_wiring()), ("schemat", page_schematic()),
             ("montaz", page_assembly())]
    svgs = []
    with tempfile.TemporaryDirectory() as td:
        for name, pg in pages:
            p = Path(td) / (name + ".svg")
            pg.save(p)
            svgs.append(p)
            shutil.copy(p, OUT / ("plytka-przyciskow-%s.svg" % name))
        subprocess.run(["rsvg-convert", "-f", "pdf", "-o", str(PDF)] + [str(p) for p in svgs], check=True)
    return PDF


def main():
    errors, notes = check()
    for n in notes:
        print("  " + n)
    if errors:
        print("BŁĘDY:")
        for e in errors:
            print("  - " + e)
        sys.exit(1)
    print("kontrola: OK (%d przewodów rozdzielczych, 4 pola KEY)" % len(JUMPERS))
    if "--check" not in sys.argv:
        print("zapisano", build().relative_to(ROOT))


if __name__ == "__main__":
    main()
