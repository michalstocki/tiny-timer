"""Solver przekroju obudowy klin-3 (czysta geometria 2D + numpy, bez bpy).

Szuka najmniejszego boku zaokrąglonego trójkąta równobocznego, w którym mieszczą się jednocześnie (przekrój Y-Z):
  - moduł wyświetlacza z wtyczkami na froncie (wklejony na wewnętrzną stronę panelu),
  - płytka główna na tylnej ściance pokrywy (elementy do wnętrza),
  - płytka przycisków pod wierzchołkiem,
  - trzy ogniwa AAA w układzie 2 + 1 w korpusie (dostęp od góry, po zdjęciu pokrywy).
Elementy niesione przez pokrywę nie mogą przy zdejmowaniu (ruch pionowo w górę) zahaczyć o ogniwa.

Uruchomienie (numpy jest w Blenderze, nie w systemowym pythonie):
    Blender --background --python tools/enclosure/wedge3_solver.py
"""
import json
import math
import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from geom2d import clip_top, fillet_poly, offset_poly

ROOT = Path(__file__).resolve().parents[2]

THETA = 60.0
RA, RB = 13.0, 5.0
WALL, PANEL = 2.0, 1.6
T_TOP = 4.4
BZ_CEIL = 6.8
BB_D = 16.0
BT = 1.6
MODULE_T, MODULE_W = 4.0, 12.0        # moduł OLED: grubość (z szybą, bez listwy) i szerokość (wzdłuż skosu)
PLUG_H = 11.0                         # wtyczki żeńskie (kątowe) na listwie pinów: wysokość nad tylną ścianką modułu
PLUG_W = 10.6                         # cztery obudowy 2,54 mm obok siebie wzdłuż skosu
D_JOINT = 2.5                         # odstęp laminatu płytki głównej od ścianki: nóżki z lutem do 2,0 mm
# ogniwa 2 + 1 jak w piramidzie: dolne w korytkach (żeberko 1,0 mm), górne leży w dolince między dolnymi (luz 0,5 mm);
# korytka sięgają tylko do osi dolnych ogniw (otwarte od góry), więc pokrywa musi omijać same ogniwa (r 5,25 + 0,75)
CELL_R, B_RCH = 5.25, 5.5
B_PITCH = 12.0                                           # oś-oś dolnych ogniw
B_DIST = 2 * CELL_R + 0.5                                # oś-oś ogniwa górnego i dolnego (luz 0,5)
B_RH = CELL_R + 0.75                                     # promień strefy zakazanej wokół ogniwa dla elementów pokrywy
Z_POCKET = 1.6
B_ZL = Z_POCKET + B_RCH
B_ZU = B_ZL + math.sqrt(B_DIST ** 2 - (B_PITCH / 2) ** 2)
FRONT_BAND_CLEAR = 6.5                # oś ogniwa od wewnętrznej płaszczyzny frontu (5,25 + 1,0 pogrubienie zakładki + 0,25 luzu)
LIP_B = 10.0                          # długość języka zatrzasku na tyle (po ściance)
HEIGHT_OVERRIDE = {"U1": 8.5}
WIRE_PAD_H = 4.0                      # nad polami przewodów zostaje miejsce na wygięcie przewodów

th = math.radians(THETA)
sin_t, cos_t = math.sin(th), math.cos(th)
NB = (sin_t, cos_t)
UBK = (cos_t, -sin_t)


def profile(side, ra=RA, t_top=T_TOP):
    h = side / 2 * math.tan(th)
    out_pts = [(0.0, 0.0), (side, 0.0), (side / 2, h)]
    in_pts = offset_poly(out_pts, [WALL, WALL, PANEL])
    gamma = math.pi - 2 * th
    z_top = h - ra * (1 / math.sin(gamma / 2) - 1)
    inner_full = fillet_poly(in_pts, [max(RB - WALL, 0.8), max(RB - WALL, 0.8), max(ra - 1.8, 0.8)])
    z_ceil = z_top - t_top
    outer = fillet_poly(out_pts, [RB, RB, ra])
    return dict(side=side, H=h, z_top=z_top, z_ceil=z_ceil, inner=clip_top(inner_full, z_ceil), inner_full=inner_full,
                outer=outer)


def sdist_inside(poly, pts):
    """Najmniejsza odległość (ze znakiem, + = wewnątrz) punktów od krawędzi wypukłego wielokąta CCW."""
    pts = np.asarray(pts, float)
    d = np.full(len(pts), 1e9)
    n = len(poly)
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
        e = math.hypot(x1 - x0, y1 - y0)
        d = np.minimum(d, ((x1 - x0) * (pts[:, 1] - y0) - (y1 - y0) * (pts[:, 0] - x0)) / e)
    return d


GRID = 0.5


def grid(a0, a1, b0, b1, step=None):
    step = step or GRID
    na, nb = max(int((a1 - a0) / step), 1), max(int((b1 - b0) / step), 1)
    return [(a0 + (a1 - a0) * i / na, b0 + (b1 - b0) * j / nb) for i in range(na + 1) for j in range(nb + 1)]


def front_pts(side, rects):
    """Punkty (y, z) z prostokątów (sf, d) na froncie (sf po skosie od krawędzi podstawy, d w głąb)."""
    out = []
    for sa, sb, da, db in rects:
        out += [(s * cos_t + d * sin_t, s * sin_t - d * cos_t) for s, d in grid(sa, sb, da, db)]
    return np.array(out)


def back_pts(side, rects):
    """Punkty (y, z) z prostokątów (sb, d) na tyle (sb po tylnej ściance od ostrego wierzchołka w dół, d w głąb)."""
    yc, h = side / 2, side / 2 * math.tan(th)
    out = []
    for sa, sb, da, db in rects:
        out += [(yc + s * UBK[0] - d * NB[0], h + s * UBK[1] - d * NB[1]) for s, d in grid(sa, sb, da, db)]
    return np.array(out)


def load_pcb(layout_path):
    lay = json.loads(Path(layout_path).read_text())
    parts = []
    for k, p in lay["parts"].items():
        if p["side"] != "bottom" or p["body"] is None:
            continue
        h = HEIGHT_OVERRIDE.get(k, p["height_above_board"])
        if h <= 0:
            h = WIRE_PAD_H
        parts.append((k, p["body"], h))
    return lay["board"]["width"], lay["board"]["height"], parts


def pcb_rects(parts, bh, sb_far, flip, margin=1.0):
    """Prostokąty (sb, d) płytki na tylnej ściance. Układ płytki: by rośnie do wierzchołka, więc sb = sb_far - by;
    flip = obrót płytki o 180° w jej płaszczyźnie (by -> bh - by)."""
    rects = [(sb_far - bh - margin, sb_far + margin, WALL + 0.05, D_JOINT + WALL + BT)]
    for k, (x0, y0, x1, y1), h in parts:
        if flip:
            y0, y1 = bh - y1, bh - y0
        rects.append((sb_far - y1 - margin, sb_far - y0 + margin, WALL + D_JOINT + BT, WALL + D_JOINT + BT + h + margin))
    return rects


def button_board_pts(pr, side):
    yc, zb = side / 2, pr["z_ceil"] - BZ_CEIL
    z_low = zb - BT - 1.9 - 0.5
    pts = grid(yc - BB_D / 2 - 0.5, yc + BB_D / 2 + 0.5, z_low, zb, 0.5) + grid(yc - 6.8, yc + 6.8, zb, zb + 4.6, 0.5)
    return np.array(pts)


def tubes(yc):
    return [(yc - B_PITCH / 2, B_ZL), (yc + B_PITCH / 2, B_ZL), (yc, B_ZU)]


def bundle_clear(pts, yc, gap=0.0, sweep=True):
    """Czy punkty (niesione przez pokrywę) omijają zestaw ogniw (przy położeniu yc) i przy zdejmowaniu pionowo w górę."""
    ok = True
    for cy_, cz_ in tubes(yc):
        r = B_RH + gap
        dy = pts[:, 0] - cy_
        dz = pts[:, 1] - cz_
        if np.any(dy * dy + dz * dz < r * r):
            return False
        if sweep and np.any((np.abs(dy) < r) & (dz < 0)):          # pod rurką: zahaczyłoby przy podnoszeniu
            return False
    return ok


def min_dist(a, b):
    d2 = ((a[:, None, :] - b[None, :, :]) ** 2).sum(-1)
    return math.sqrt(d2.min())


def solve(layout_path, ra=RA, t_top=T_TOP, plug_h=PLUG_H, sides=None, verbose=False, skip=()):
    """Zwraca najmniejsze rozwiązanie albo None. plug_zone=True: wtyczki poza zasięgiem X ogniw i płytki (osobna strefa)."""
    bw, bh, parts = load_pcb(layout_path)
    for side in sides or [x * 0.5 for x in range(100, 180)]:
        pr = profile(side, ra, t_top)
        inner = pr["inner"]
        H = pr["H"]
        bb = button_board_pts(pr, side)
        if "bb" in skip:
            bb = np.zeros((1, 2)) + 1e3
        elif np.any(sdist_inside(inner, bb) < -1e-9):
            continue
        # moduł + wtyczki na froncie: położenie środka modułu sm po skosie
        s_front_end = side - 5.0 * math.tan(math.radians(30))
        disp = []
        for sm in [x * 0.5 for x in range(int(2 * (MODULE_W / 2 + 2)), int(2 * (side - 8)))]:
            mod = front_pts(side, [(sm - MODULE_W / 2 - 0.3, sm + MODULE_W / 2 + 0.3, PANEL, PANEL + MODULE_T + 0.3)])
            plg = front_pts(side, [(sm - PLUG_W / 2 - 0.3, sm + PLUG_W / 2 + 0.3, PANEL + MODULE_T, PANEL + MODULE_T + plug_h + 0.8)])
            allp = np.vstack([mod, plg])
            if np.any(sdist_inside(inner, allp) < -1e-9):
                continue
            if min_dist(allp, bb) < 1.0:
                continue
            disp.append((sm, mod, plg))
        if "disp" in skip:
            disp = [(0.0, np.zeros((1, 2)) + 1e3, np.zeros((1, 2)) + 1e3)]
        if not disp:
            continue
        # płytka główna na tyle: położenie dalszego brzegu płytki sb_far (od ostrego wierzchołka), obrót o 180° lub nie
        s_back_max = side - 2.9 - 0.3 - LIP_B - 2.0        # pod pokrywą musi zostać miejsce na język zatrzasku i jego żebro
        pcb = []
        for flip in (False, True):
            for sb_far in [x * 0.5 for x in range(int(2 * (bh + 5)), int(2 * s_back_max))]:
                p = back_pts(side, pcb_rects(parts, bh, sb_far, flip))
                if np.any(sdist_inside(inner, p) < -1e-9):
                    continue
                if min_dist(p, bb) < 1.0:
                    continue
                pcb.append((flip, sb_far, p))
        if "pcb" in skip:
            pcb = [(False, 0.0, np.zeros((1, 2)) + 1e3)]
        if not pcb:
            continue
        # położenie zestawu ogniw
        for k in range(int(side * 0.7 / 0.5)):
            yc = side * 0.15 + k * 0.5
            cs = tubes(yc)
            if not all(sdist_inside(inner, [q])[0] >= B_RCH - 0.5 for q in cs):
                continue
            if any(q[0] * sin_t - q[1] * cos_t - PANEL < FRONT_BAND_CLEAR for q in cs):
                continue            # zakładka frontu pogrubia ściankę od wnętrza o ok. 1 mm
            if "bundle" in skip:
                return dict(side=side, yc=yc)
            if not bundle_clear(bb, yc):
                continue
            dsel = [d for d in disp if bundle_clear(np.vstack([d[1], d[2]]), yc, sweep=True)]
            if not dsel:
                continue
            psel = [p for p in pcb if bundle_clear(p[2], yc, sweep=True)]
            if not psel:
                continue
            for d in dsel:
                for p in psel:
                    if min_dist(d[1], p[2]) < 0.8:                    # moduł (cienki) vs elementy płytki
                        continue
                    return dict(side=side, yc=yc, sm=d[0], flip=p[0], sb_far=p[1], z_top=pr["z_top"], z_ceil=pr["z_ceil"], H=H)
    return None


def svg_solution(layout_path, r, path, ra=RA, t_top=T_TOP, plug_h=PLUG_H):
    """Rysunek rozwiązania (przekrój Y-Z): zarys, ścianki, obiekty jako obrysy punktów."""
    bw, bh, parts = load_pcb(layout_path)
    side = r["side"]
    pr = profile(side, ra, t_top)
    sc, M = 10.0, 20
    Hh = pr["H"]
    X = lambda y: M + y * sc
    Y = lambda z: M + (Hh + 4 - z) * sc
    el = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" style="background:#fff">' % (side * sc + 2 * M, (Hh + 8) * sc + 2 * M)]
    poly = lambda pts, st: el.append('<polygon points="%s" %s/>' % (" ".join("%.1f,%.1f" % (X(a), Y(b)) for a, b in pts), st))
    out = fillet_poly([(0, 0), (side, 0), (side / 2, pr["H"])], [RB, RB, ra])
    poly(out, 'fill="#eee" stroke="#000" stroke-width="1.5"')
    poly(pr["inner"], 'fill="#fff" stroke="#888" stroke-width="1"')

    def blob(pts, col):
        for q in pts:
            el.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" fill-opacity="0.35"/>' % (X(q[0]) - GRID * sc / 2, Y(q[1]) - GRID * sc / 2, GRID * sc, GRID * sc, col))
    blob(button_board_pts(pr, side), "#d33")
    sm = r["sm"]
    blob(front_pts(side, [(sm - MODULE_W / 2 - 0.3, sm + MODULE_W / 2 + 0.3, PANEL, PANEL + MODULE_T + 0.3)]), "#33d")
    blob(front_pts(side, [(sm - PLUG_W / 2 - 0.3, sm + PLUG_W / 2 + 0.3, PANEL + MODULE_T, PANEL + MODULE_T + plug_h + 0.8)]), "#69f")
    blob(back_pts(side, pcb_rects(parts, bh, r["sb_far"], r["flip"])), "#2a2")
    for cy_, cz_ in tubes(r["yc"]):
        el.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="#fc0" fill-opacity="0.5" stroke="#a80"/>' % (X(cy_), Y(cz_), CELL_R * sc))
        el.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="none" stroke="#a80" stroke-dasharray="3"/>' % (X(cy_), Y(cz_), B_RH * sc))
    el.append("</svg>")
    Path(path).write_text("\n".join(el))


if __name__ == "__main__" and not os.environ.get("TT_SOLVE_ONLY"):
    lp = os.environ.get("TT_LAYOUT", str(ROOT / "docs/pcb-klin3/pcb-layout.json"))
    GRID = 1.0
    st = [x * 1.0 for x in range(50, 85)]
    r0 = solve(lp, sides=st)
    svg_solution(lp, r0, os.environ.get("TT_SVG", "/tmp/sol.svg"))
    for label, skip in (("wszystko", ()), ("bez ogniw", ("bundle",)), ("bez PCB", ("pcb",)), ("bez wyśw.", ("disp",)),
                        ("bez przycisków", ("bb",)), ("tylko ogniwa+przyc.", ("pcb", "disp")), ("tylko PCB+przyc.", ("disp", "bundle")),
                        ("tylko wyśw.+przyc.", ("pcb", "bundle")), ("tylko PCB+ogniwa", ("bb", "disp"))):
        r = solve(lp, sides=st, skip=skip)
        print(f"SENS {label:22s}", r and r["side"], r and {k: round(v, 1) for k, v in r.items() if k in ("yc", "sm", "sb_far")})


if __name__ == "__main__" and os.environ.get("TT_SOLVE_ONLY"):
    GRID = 0.5
    lp = os.environ.get("TT_LAYOUT", str(ROOT / "docs/pcb-klin3/pcb-layout.json"))
    r = solve(lp, sides=[x * 0.5 for x in range(128, 160)])
    print("SOL", r)
    svg_solution(lp, r, os.environ.get("TT_SVG", "/tmp/sol.svg"))
