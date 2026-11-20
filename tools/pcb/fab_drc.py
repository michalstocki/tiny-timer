"""DRC i porównanie z netlistą (LVS) płytki głównej na dokładnej geometrii (nie na siatce routera).

Kształty miedzi: ("circle", x, y, r), ("seg", x0, y0, x1, y1, w) (kapsuła), ("rect", x0, y0, x1, y1) (kwadratowe pole).
Sprawdza: odstęp miedź-miedź różnych sieci, miedź od krawędzi płytki, miedź od otworów M2,5, pierścień pól i przelotek,
odstęp otworów, rozmiary wierteł, oraz łączność każdej sieci (otwarcia) i zwarcia między sieciami.
"""
import math

import fab

R = fab.RULES


# ---------------------------------------------------------------- geometria
def pt_seg(px, py, x0, y0, x1, y1):
    dx, dy = x1 - x0, y1 - y0
    L = dx * dx + dy * dy
    if L == 0:
        return math.hypot(px - x0, py - y0)
    t = max(0.0, min(1.0, ((px - x0) * dx + (py - y0) * dy) / L))
    return math.hypot(px - (x0 + t * dx), py - (y0 + t * dy))


def _ccw(ax, ay, bx, by, cx, cy):
    return (cy - ay) * (bx - ax) - (by - ay) * (cx - ax)


def seg_cross(a, b, c, d):
    d1 = _ccw(*c, *d, *a)
    d2 = _ccw(*c, *d, *b)
    d3 = _ccw(*a, *b, *c)
    d4 = _ccw(*a, *b, *d)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)) and d1 != 0 and d2 != 0 and d3 != 0 and d4 != 0


def seg_seg(a, b, c, d):
    if seg_cross(a, b, c, d):
        return 0.0
    return min(pt_seg(*a, *c, *d), pt_seg(*b, *c, *d), pt_seg(*c, *a, *b), pt_seg(*d, *a, *b))


def rect_edges(r):
    x0, y0, x1, y1 = r
    return [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]


def in_rect(x, y, r):
    return r[0] <= x <= r[2] and r[1] <= y <= r[3]


def gap(a, b):
    """Odstęp krawędzi dwóch kształtów (ujemny lub 0 = nakładają się)."""
    ka, kb = a[0], b[0]
    if ka > kb:
        a, b, ka, kb = b, a, kb, ka
    if ka == "circle":
        if kb == "circle":
            return math.hypot(a[1] - b[1], a[2] - b[2]) - a[3] - b[3]
        if kb == "seg":
            return pt_seg(a[1], a[2], *b[1:5]) - a[3] - b[5] / 2
        r = b[1:5]
        dx = max(r[0] - a[1], 0, a[1] - r[2])
        dy = max(r[1] - a[2], 0, a[2] - r[3])
        return math.hypot(dx, dy) - a[3]
    if ka == "rect":
        if kb == "rect":
            dx = max(a[1] - b[3], b[1] - a[3], 0)
            dy = max(a[2] - b[4], b[2] - a[4], 0)
            return math.hypot(dx, dy)
        return None   # rect-seg liczone niżej (kolejność alfabetyczna: circle < rect < seg)
    # a = seg, b = seg
    return seg_seg(a[1:3], a[3:5], b[1:3], b[3:5]) - a[5] / 2 - b[5] / 2


def gap_rect_seg(rc, sg):
    r = rc[1:5]
    p0, p1 = sg[1:3], sg[3:5]
    if in_rect(*p0, r) or in_rect(*p1, r):
        return 0.0 - sg[5] / 2
    d = min(seg_seg(p0, p1, e0, e1) for e0, e1 in rect_edges(r))
    return d - sg[5] / 2


def gap_any(a, b):
    ka, kb = a[0], b[0]
    if {ka, kb} == {"rect", "seg"}:
        return gap_rect_seg(a, b) if ka == "rect" else gap_rect_seg(b, a)
    return gap(a, b)


def edge_dist(x, y):
    """Odległość punktu leżącego wewnątrz zarysu (prostokąt z zaokrąglonymi narożnikami) od krawędzi płytki."""
    W, H, r = fab.W, fab.H, fab.CORNER_R
    d = min(x, fab.W - x, y, H - y)
    cx = r if x < r else (W - r if x > W - r else None)
    cy = r if y < r else (H - r if y > H - r else None)
    if cx is not None and cy is not None:
        d = r - math.hypot(x - cx, y - cy)
    return d


# ---------------------------------------------------------------- miedź
def copper(design):
    """design: dict(tracks=[(net, layer, (x0,y0), (x1,y1))...], vias=[(net, x, y)...]).
    Zwraca {layer: [(kształt, sieć, opis)]} dla warstw 0 (F) i 1 (B)."""
    out = {0: [], 1: []}
    for p in fab.PADS:
        if p["shape"] == "rect":
            h = p["d"] / 2
            sh = ("rect", p["x"] - h, p["y"] - h, p["x"] + h, p["y"] + h)
        else:
            sh = ("circle", p["x"], p["y"], p["d"] / 2)
        for L in (0, 1):
            out[L].append((sh, p["net"], "%s.%s" % (p["ref"], p["pin"])))
    for (net, x, y) in design["vias"]:
        for L in (0, 1):
            out[L].append((("circle", x, y, R["via_d"] / 2), net, "via(%.2f,%.2f)" % (x, y)))
    for (net, L, a, b) in design["tracks"]:
        out[L].append((("seg", a[0], a[1], b[0], b[1], R["track"]), net, "track %s" % net))
    return out


def check(design):
    errors, warns = [], []
    cu = copper(design)
    # odstęp miedź-miedź różnych sieci
    worst = 9.0
    for L, items in cu.items():
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                (sa, na, da), (sb, nb, db) = items[i], items[j]
                if na == nb:
                    continue
                # szybkie odrzucenie
                g = gap_any(sa, sb)
                worst = min(worst, g)
                if g < R["clearance_min"] - 1e-9:
                    errors.append("warstwa %s: %s i %s: odstęp %.3f mm < %.2f" % ("FB"[L], da, db, g, R["clearance_min"]))
    # krawędź płytki i otwory montażowe
    for L, items in cu.items():
        for sh, net, d in items:
            if sh[0] == "circle":
                e = edge_dist(sh[1], sh[2]) - sh[3]
            elif sh[0] == "rect":
                e = min(edge_dist(x, y) for x, y in ((sh[1], sh[2]), (sh[3], sh[2]), (sh[3], sh[4]), (sh[1], sh[4])))
            else:
                e = min(edge_dist(sh[1], sh[2]), edge_dist(sh[3], sh[4])) - sh[5] / 2
            if e < R["edge_clearance"] - 1e-9:
                errors.append("warstwa %s: %s: %.3f mm od krawędzi płytki (min %.2f)" % ("FB"[L], d, e, R["edge_clearance"]))
            for (mx, my) in fab.HOLES:
                if sh[0] == "circle":
                    dd = math.hypot(sh[1] - mx, sh[2] - my) - sh[3]
                elif sh[0] == "rect":
                    dd = gap(("circle", mx, my, 0.0), sh)
                else:
                    dd = pt_seg(mx, my, *sh[1:5]) - sh[5] / 2
                if dd < fab.MOUNT_KEEPOUT - 0.2 - 1e-9:
                    errors.append("warstwa %s: %s: %.2f mm od osi otworu M2,5 (min %.1f)" % ("FB"[L], d, dd, fab.MOUNT_KEEPOUT - 0.2))
    # pierścienie i wiertła
    holes = []
    for p in fab.PADS:
        ring = (p["d"] - p["drill"]) / 2
        if ring < R["min_annular"] - 1e-9:
            errors.append("%s.%s: pierścień %.2f mm" % (p["ref"], p["pin"], ring))
        if p["drill"] < 0.3:
            errors.append("%s.%s: wiertło %.2f" % (p["ref"], p["pin"], p["drill"]))
        holes.append((p["x"], p["y"], p["drill"] / 2, "%s.%s" % (p["ref"], p["pin"])))
    for (net, x, y) in design["vias"]:
        ring = (R["via_d"] - R["via_drill"]) / 2
        if ring < 0.15:
            errors.append("przelotka: pierścień %.2f" % ring)
        holes.append((x, y, R["via_drill"] / 2, "via(%.2f,%.2f)" % (x, y)))
    for (mx, my) in fab.HOLES:
        holes.append((mx, my, fab.MOUNT_D / 2, "M2,5"))
    wh = 9.0
    for i in range(len(holes)):
        for j in range(i + 1, len(holes)):
            g = math.hypot(holes[i][0] - holes[j][0], holes[i][1] - holes[j][1]) - holes[i][2] - holes[j][2]
            wh = min(wh, g)
            if g < R["hole_to_hole"] - 1e-9:
                errors.append("otwory %s i %s: %.2f mm od siebie" % (holes[i][3], holes[j][3], g))
    # łączność (LVS)
    lvs_errors, comps = connectivity(design, cu)
    errors += lvs_errors
    info = dict(min_clearance=worst, min_hole_gap=wh, components=comps)
    return errors, warns, info


def connectivity(design, cu):
    nodes = []
    for L, items in cu.items():
        for k, (sh, net, d) in enumerate(items):
            nodes.append((L, k, sh, net, d))
    parent = list(range(len(nodes)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        parent[find(a)] = find(b)

    # ta sama warstwa: nakładanie się kształtów
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            a, b = nodes[i], nodes[j]
            if a[0] != b[0]:
                continue
            if gap_any(a[2], b[2]) <= 1e-6:
                union(i, j)
    # pole przelotowe łączy warstwy (ta sama nazwa), przelotka też
    by_name = {}
    for i, (L, k, sh, net, d) in enumerate(nodes):
        if not d.startswith("track"):
            by_name.setdefault(d, []).append(i)
    for lst in by_name.values():
        for i in lst[1:]:
            union(lst[0], i)
    groups = {}
    for i, (L, k, sh, net, d) in enumerate(nodes):
        groups.setdefault(find(i), []).append(i)
    errs = []
    comp_of_net = {}
    for root, idxs in groups.items():
        nets = {nodes[i][3] for i in idxs}
        pins = sorted({nodes[i][4] for i in idxs if "." in nodes[i][4] and not nodes[i][4].startswith("track")})
        if len(nets) > 1:
            errs.append("ZWARCIE sieci %s: %s" % (sorted(map(str, nets)), pins))
        for n in nets:
            comp_of_net.setdefault(n, []).append(pins)
    for net in fab.net_names():
        pins = {"%s.%s" % (p["ref"], p["pin"]) for p in fab.PADS if p["net"] == net}
        comps = [set(c) for c in comp_of_net.get(net, []) if set(c) & pins]
        if len(pins) > 1 and not any(pins <= c for c in comps):
            errs.append("OTWARCIE sieci %s: pola w %d grupach: %s" % (net, len(comps), [sorted(c & pins) for c in comps]))
    return errs, {n: len(v) for n, v in comp_of_net.items()}
