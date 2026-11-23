"""Narożniki o ciągłej krzywiźnie (G2) i bryła klina z takimi narożnikami. Czysta geometria (bez bpy).

Narożnik G2: krzywizna rośnie liniowo od 0 do 1/R (przejście klotoidalne), potem łuk o promieniu R, potem maleje do 0.
Parametry jak w zaokrągleniu „curvature continuous” w programach CAD:
  r       promień nominalny: narożnik zaczyna się tam, gdzie zacząłby się łuk o promieniu r (to samo cofnięcie od
          wierzchołka r * tan(kąt skrętu / 2)), więc R10 G2 zajmuje na ścianach tyle miejsca co R10 kołowy,
  smooth  udział przejść w kącie skrętu, 0...1 (0 = łuk kołowy, G1; 1 = same przejścia, krzywizna szczytowa w jednym punkcie).
Przy większym smooth środek narożnika jest ciaśniejszy (najmniejszy promień r_min < r, patrz r_min()), a styk ze ścianą
łagodniejszy: krzywizna rośnie od zera, więc odblask na krawędzi nie ma skoku.

Bryła klina: przekrój (zaokrąglony trójkąt) wyciągnięty wzdłuż X; krawędzie boków (trójkątnych ścian na końcach)
zaokrąglone narożnikiem G2 o kącie 90°. Przekrój w odległości u od końca to przekrój podstawowy odsunięty do środka
o e(u), gdzie (u, e) leży na krzywej narożnika końca. Odsunięcie przekroju liczę jako trójkąt odsunięty o e z promieniami
narożników r - e (ten sam smooth), więc każdy przekrój jest gładki i ma tyle samo punktów (pierścienie siatki).

Układ: X wzdłuż, Y w głąb (front y = 0), Z w górę, podstawa na z = 0 (jak w build_wedge5).
"""
import math

R_MIN = 0.25                     # najmniejszy promień narożnika przekroju odsuniętego (żeby nie zrobić ostrza)


def _unit_curve(turn, smooth, steps):
    """Narożnik o najmniejszym promieniu 1: punkty i cofnięcie."""
    r = 1.0
    smooth = min(max(smooth, 0.0), 1.0)
    lt = smooth * turn * r                      # długość jednego przejścia (krzywizna 0 -> 1/r)
    la = (1.0 - smooth) * turn * r              # długość łuku
    total = 2 * lt + la

    def kappa(s):
        if lt > 0 and s < lt:
            return s / lt / r
        if s <= lt + la:
            return 1.0 / r
        return max(total - s, 0.0) / lt / r if lt > 0 else 1.0 / r

    ds = total / steps
    x = y = th = 0.0
    pts = [(0.0, 0.0)]
    for i in range(steps):
        s = (i + 0.5) * ds
        k = kappa(s)
        thm = th + k * ds / 2                   # punkt środkowy
        x += math.cos(thm) * ds
        y += math.sin(thm) * ds
        th += k * ds
        pts.append((x, y))
    # wierzchołek: przecięcie osi x z prostą przez koniec w kierunku turn
    ex, ey = pts[-1]
    return pts, ex - ey / math.tan(turn)


def r_min(turn, r, smooth):
    """Najmniejszy promień krzywizny narożnika G2 o promieniu nominalnym r."""
    return r * math.tan(turn / 2) / _unit_curve(turn, smooth, 400)[1]


def corner_curve(turn, r, smooth, n=32, steps=1200):
    """Narożnik w układzie lokalnym: start w (0, 0) z kierunkiem +x, skręt w lewo o kąt turn (radiany).

    Zwraca (punkty, t): n + 1 punktów krzywej i cofnięcie t = r * tan(turn / 2) (wierzchołek w (t, 0)).
    """
    pts, t1 = _unit_curve(turn, smooth, steps)
    t = r * math.tan(turn / 2)
    k = t / t1
    return [(pts[round(i * steps / n)][0] * k, pts[round(i * steps / n)][1] * k) for i in range(n + 1)], t


def offset_poly(pts, insets):
    """Wypukły wielokąt CCW przesunięty do wnętrza; insets[i] to wcięcie krawędzi pts[i] -> pts[i+1]."""
    n = len(pts)
    lines = []
    for i in range(n):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
        dx, dy = x1 - x0, y1 - y0
        ln = math.hypot(dx, dy)
        nx, ny = -dy / ln, dx / ln
        lines.append((x0 + nx * insets[i], y0 + ny * insets[i], dx / ln, dy / ln))
    out = []
    for i in range(n):
        px, py, dx, dy = lines[i - 1]
        qx, qy, ex, ey = lines[i]
        den = dx * ey - dy * ex
        tt = ((qx - px) * ey - (qy - py) * ex) / den
        out.append((px + dx * tt, py + dy * tt))
    return out


def g2_poly(pts, radii, smooth, n=32):
    """Wypukły wielokąt CCW z narożnikami G2: radii[i] dla wierzchołka pts[i], smooth wspólny albo lista.

    Zwraca (punkty, info): n + 1 punktów na narożnik (proste odcinki między narożnikami bez dodatkowych punktów)
    i dla każdej krawędzi zapas prostego odcinka (ujemny = narożniki zachodzą na siebie).
    """
    m = len(pts)
    sm = smooth if isinstance(smooth, (list, tuple)) else [smooth] * m
    out, tbs = [], []
    for i in range(m):
        p, a, c = pts[i], pts[i - 1], pts[(i + 1) % m]
        din = (p[0] - a[0], p[1] - a[1])
        ln = math.hypot(*din)
        din = (din[0] / ln, din[1] / ln)
        dout = (c[0] - p[0], c[1] - p[1])
        ln = math.hypot(*dout)
        dout = (dout[0] / ln, dout[1] / ln)
        turn = math.atan2(din[0] * dout[1] - din[1] * dout[0], din[0] * dout[0] + din[1] * dout[1])
        curve, t = corner_curve(turn, radii[i], sm[i], n)
        tbs.append(t)
        nrm = (-din[1], din[0])
        sx, sy = p[0] - din[0] * t, p[1] - din[1] * t
        out += [(sx + din[0] * u + nrm[0] * v, sy + din[1] * u + nrm[1] * v) for u, v in curve]
    straight = []
    for i in range(m):
        ln = math.hypot(pts[(i + 1) % m][0] - pts[i][0], pts[(i + 1) % m][1] - pts[i][1])
        straight.append(ln - tbs[i] - tbs[(i + 1) % m])
    return out, dict(setbacks=tbs, straight=straight)


# ---------------------------------------------------------------- klin
THETA = math.radians(60.0)


def triangle(side):
    h = side / 2 * math.tan(THETA)
    return [(0.0, 0.0), (side, 0.0), (side / 2, h)]     # (y, z): front przy y = 0, tył przy y = side


def section(side, rb, ra, smooth, inset=(0.0, 0.0, 0.0), n=32, smooth_a=None):
    """Przekrój klina odsunięty do środka o inset (podstawa, tył, front); promienie narożników zmniejszone o wcięcie."""
    tri = offset_poly(triangle(side), list(inset))
    d_b = (inset[2] + inset[0]) / 2                     # front/podstawa
    d_k = (inset[0] + inset[1]) / 2                     # podstawa/tył
    d_a = (inset[1] + inset[2]) / 2                     # wierzchołek
    radii = [max(rb - d_b, R_MIN), max(rb - d_k, R_MIN), max(ra - d_a, R_MIN)]
    sa = smooth if smooth_a is None else smooth_a
    return g2_poly(tri, radii, [smooth, smooth, sa], n)


def end_profile(re, smooth_e, n=16):
    """Krzywa zaokrąglenia krawędzi boku: lista (u, e), u = odległość od płaszczyzny końca, e = wcięcie przekroju."""
    curve, t = corner_curve(math.pi / 2, re, smooth_e, n)
    return [(t - px, py) for px, py in curve], t        # od (t, 0) na ścianie do (0, t) na płaszczyźnie końca


def wedge_rings(side, length, rb, ra, re, smooth, smooth_e=None, n=32, ne=16, smooth_a=None):
    """Pierścienie siatki: lista (x, punkty przekroju (y, z)) od x = 0 do x = length; pierwszy i ostatni to dekle."""
    se = smooth if smooth_e is None else smooth_e
    prof, t = end_profile(re, se, ne)
    rings = []
    for u, e in reversed(prof):                         # lewy koniec: od płaszczyzny (u = 0) do ściany
        rings.append((u, section(side, rb, ra, smooth, (e, e, e), n, smooth_a)[0]))
    for u, e in prof:                                   # prawy koniec: od ściany do płaszczyzny
        rings.append((length - u, section(side, rb, ra, smooth, (e, e, e), n, smooth_a)[0]))
    return rings, t


def curvature(poly):
    """Krzywizna dyskretna w punktach zamkniętej łamanej (1/mm, okrąg przez trzy kolejne punkty)."""
    m = len(poly)
    ks = []
    for i in range(m):
        a, b, c = poly[i - 1], poly[i], poly[(i + 1) % m]
        ab = math.dist(a, b)
        bc = math.dist(b, c)
        ca = math.dist(c, a)
        cr = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        ks.append(0.0 if ab * bc * ca < 1e-12 else 2 * cr / (ab * bc * ca))
    return ks


if __name__ == "__main__":
    for sm in (0.0, 0.3, 0.5, 0.7, 1.0):
        print(f"smooth {sm}: R10 120° r_min = {r_min(math.radians(120), 10, sm):.2f} mm,"
              f" R6 90° r_min = {r_min(math.pi / 2, 6, sm):.2f} mm")
