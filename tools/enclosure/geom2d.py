"""Czysta geometria 2D (bez bpy): wielokąty wypukłe, zaokrąglanie, offset, otoczka. Używana przez bpyutil i solvery."""
import math


def offset_poly(pts, insets):
    """Wypukły wielokąt CCW przesunięty do wnętrza; insets[i] to wcięcie krawędzi pts[i] -> pts[i+1]."""
    n = len(pts)
    lines = []
    for i in range(n):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
        dx, dy = x1 - x0, y1 - y0
        ln = math.hypot(dx, dy)
        nx, ny = -dy / ln, dx / ln          # normalna do wnętrza (lewa dla CCW)
        lines.append((x0 + nx * insets[i], y0 + ny * insets[i], dx / ln, dy / ln))
    out = []
    for i in range(n):
        px, py, dx, dy = lines[i - 1]
        qx, qy, ex, ey = lines[i]
        den = dx * ey - dy * ex
        t = ((qx - px) * ey - (qy - py) * ex) / den
        out.append((px + dx * t, py + dy * t))
    return out


def fillet_poly(pts, radii, seg=12):
    """Zaokrągla narożniki wypukłego wielokąta (CCW): radii[i] dla wierzchołka pts[i]."""
    n = len(pts)
    out = []
    for i in range(n):
        p = pts[i]
        r = radii[i]
        if r <= 0:
            out.append(p)
            continue
        a, c = pts[i - 1], pts[(i + 1) % n]
        e1 = (a[0] - p[0], a[1] - p[1])
        e2 = (c[0] - p[0], c[1] - p[1])
        l1, l2 = math.hypot(*e1), math.hypot(*e2)
        e1 = (e1[0] / l1, e1[1] / l1)
        e2 = (e2[0] / l2, e2[1] / l2)
        th = math.acos(max(-1.0, min(1.0, e1[0] * e2[0] + e1[1] * e2[1])))
        t = r / math.tan(th / 2)
        t1 = (p[0] + e1[0] * t, p[1] + e1[1] * t)
        t2 = (p[0] + e2[0] * t, p[1] + e2[1] * t)
        bx, by = e1[0] + e2[0], e1[1] + e2[1]
        bl = math.hypot(bx, by)
        d = r / math.sin(th / 2)
        cx, cy = p[0] + bx / bl * d, p[1] + by / bl * d
        a1 = math.atan2(t1[1] - cy, t1[0] - cx)
        a2 = math.atan2(t2[1] - cy, t2[0] - cx)
        da = (a2 - a1 + math.pi) % (2 * math.pi) - math.pi      # krótszy łuk
        for k in range(seg + 1):
            ang = a1 + da * k / seg
            out.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    return out


def clip_top(poly, zc):
    """Wielokąt przycięty od góry płaszczyzną z <= zc (Sutherland-Hodgman, jedna krawędź)."""
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        ina, inb = a[1] <= zc, b[1] <= zc
        if ina:
            out.append(a)
        if ina != inb:
            t = (zc - a[1]) / (b[1] - a[1])
            out.append((a[0] + t * (b[0] - a[0]), zc))
    return out


def convex_hull(points):
    """Otoczka wypukła (Andrew), wynik CCW."""
    pts = sorted(set((round(x, 6), round(y, 6)) for x, y in points))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for q in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], q) <= 0:
            lo.pop()
        lo.append(q)
    for q in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], q) <= 0:
            up.pop()
        up.append(q)
    return lo[:-1] + up[:-1]


def discs_hull(centers, r, seg=24):
    """Otoczka kół o promieniu r (zaokrąglony wielokąt wokół środków)."""
    pts = [(cx + r * math.cos(2 * math.pi * k / seg), cy + r * math.sin(2 * math.pi * k / seg))
           for cx, cy in centers for k in range(seg)]
    return convex_hull(pts)


def inside_convex(poly, p, margin=0.0):
    """Czy punkt leży we wnętrzu wypukłego wielokąta CCW (co najmniej margin od krawędzi)."""
    n = len(poly)
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
        if ((x1 - x0) * (p[1] - y0) - (y1 - y0) * (p[0] - x0)) / math.hypot(x1 - x0, y1 - y0) < margin - 1e-9:
            return False
    return True
