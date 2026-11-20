"""Geometria bryły klina 6 (bez bpy): przekrój G2, powierzchnie odsunięte do wnętrza i układ narożnika.

Bryła C zatwierdzona 20.11.2026 (docs/obudowa-klin-6/README.md): RB 9, RA 15, RE 9, gładkość G2 przekroju 0,9, boków 0,75,
bok 67,0, długość 74,1. Parametry można zmienić zmiennymi TT_RB, TT_RA, TT_RE, TT_SM, TT_SME (tylko do eksperymentów).

Powierzchnia odsunięta o d („skóra”): w każdym przekroju x to przekrój G2 odsunięty o (e_d(x) - d) + d_strony, gdzie
(u, e_d) to krzywa zaokrąglenia krawędzi boku (u od płaszczyzny boku, e wcięcie) odsunięta o d po normalnej. Daleko od
boków e_d = d, więc skóra to zwykłe odsunięcie przekroju o grubości ścianek; przy bokach skóra idzie za zaokrągleniem, więc
ścianki nie robią się cienkie. Przekrój odsunięty liczy g2geom.section (trójkąt odsunięty, promienie R - d): w narożnikach
ścianka wychodzi do ok. 0,4 mm grubsza niż przy dokładnym odsunięciu (po stronie bezpiecznej dla wnętrza).
"""
import math
import os

import g2geom as G

env = os.environ.get
SIDE, LEN = 67.0, 74.1
RB, RA, RE = float(env("TT_RB", "9")), float(env("TT_RA", "15")), float(env("TT_RE", "9"))
SM, SME = float(env("TT_SM", "0.9")), float(env("TT_SME", "0.75"))
NSEG = 36                         # punktów na narożnik przekroju
NE = 18                           # punktów na krzywej krawędzi boku


def section(inset=(0.0, 0.0, 0.0), n=NSEG):
    """Przekrój (y, z) odsunięty o inset = (podstawa, tył, front)."""
    return G.section(SIDE, RB, RA, SM, tuple(inset), n)[0]


def z_top(inset=(0.0, 0.0, 0.0)):
    return max(z for _, z in section(inset))


def end_curve(n=NE):
    """(u, e) od ściany (t, 0) do płaszczyzny boku (0, t) i cofnięcie t."""
    return G.end_profile(RE, SME, n)


def end_offset(d, n=NE):
    """Krzywa krawędzi boku odsunięta do wnętrza o d (po normalnej): lista (u, e) od płaszczyzny (u = d) do ściany (e = d),
    z prostymi odcinkami: płaszczyzna boku (u = d, e od dużego do t) i ściana (e = d) aż do u = t + d + 2."""
    prof, t = end_curve(4 * n)
    pts = sorted(prof)                       # od (0, t) do (t, 0) rosnąco w u
    out = []
    for i, (u, e) in enumerate(pts):
        a, b = pts[max(i - 1, 0)], pts[min(i + 1, len(pts) - 1)]
        du, de = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(du, de) or 1.0
        nu, ne = -de / ln, du / ln           # normalna do wnętrza (u i e rosną do wnętrza)
        if nu < 0:
            nu, ne = -nu, -ne
        out.append((u + nu * d, e + ne * d))
    # przerzedzenie do ok. n punktów
    step = max(1, len(out) // n)
    out = out[::step] + [out[-1]]
    out = [p for i, p in enumerate(out) if i == 0 or p[0] > out[i - 1][0] + 1e-6]
    out.append((t + d + 2.0, d))
    return out


def e_out(u):
    """Wcięcie zewnętrznej powierzchni w odległości u od płaszczyzny boku."""
    prof, t = end_curve(200)
    if u >= t:
        return 0.0
    pts = sorted(prof)
    for (u0, e0), (u1, e1) in zip(pts, pts[1:]):
        if u0 <= u <= u1:
            return e0 + (e1 - e0) * (u - u0) / ((u1 - u0) or 1.0)
    return pts[0][1]


def e_skin(d, u):
    """Wcięcie skóry d (bez grubości strony) w odległości u od płaszczyzny boku; None przed płaszczyzną skóry."""
    pts = end_offset(d, 200)
    if u < pts[0][0]:
        return None
    if u >= pts[-1][0]:
        return d
    for (u0, e0), (u1, e1) in zip(pts, pts[1:]):
        if u0 <= u <= u1:
            return e0 + (e1 - e0) * (u - u0) / ((u1 - u0) or 1.0)
    return d


def skin_rings(dv, length=LEN):
    """Pierścienie skóry odsuniętej o dv = (podstawa, tył, front) po normalnej: lista (x, przekrój)."""
    d = min(dv)
    rings = []
    curve = end_offset(d)
    for u, e in curve:
        rings.append((u, section([e - d + k for k in dv])))
    for u, e in reversed(curve):
        rings.append((length - u, section([e - d + k for k in dv])))
    if d <= 0:                                 # zewnętrzna powierzchnia: pierścienie wprost z krzywej
        prof, t = end_curve()
        rings = [(u, section([e + k for k in dv])) for u, e in sorted(prof)]
        rings += [(length - u, section([e + k for k in dv])) for u, e in sorted(prof, reverse=True)]
    return rings


def skin_section(dv, x, length=LEN):
    """Przekrój skóry dv w płaszczyźnie x (None, jeśli x leży poza skórą)."""
    u = min(x, length - x)
    d = min(dv)
    e = e_skin(d, u) if d > 0 else e_out(u)
    if e is None:
        return None
    return section([e - (d if d > 0 else 0) + k for k in dv])


def vline(poly, y):
    """Najniższe i najwyższe z przecięcia wielokąta pionową prostą y."""
    zs = []
    n = len(poly)
    for i in range(n):
        (y0, z0), (y1, z1) = poly[i], poly[(i + 1) % n]
        if (y0 - y) * (y1 - y) <= 0 and y0 != y1:
            zs.append(z0 + (z1 - z0) * (y - y0) / (y1 - y0))
    return (min(zs), max(zs)) if zs else None


# ---------------------------------------------------------------- układ narożnika front/podstawa
# Zamiast środka łuku (klin 5: ang(psi, r) wokół C_O, R5): punkt powierzchni o normalnej zewnętrznej pod kątem psi
# (150° = front, 270° = dół) przesunięty po normalnej. Promień r z klina 5 zamieniam na głębokość 5 - r: r = 9 to 4 mm na
# zewnątrz, r = 0,5 to 4,5 mm w głąb (najmniejszy promień krzywizny narożnika C to 5,4 mm, więc normalne się nie przecinają).
R_REF = 5.0


def _corner_samples():
    poly = G.section(SIDE, RB, RA, SM, (0.0, 0.0, 0.0), 400)[0]
    n = len(poly)
    out = []
    for i in range(n):
        a, b = poly[i - 1], poly[(i + 1) % n]
        ty, tz = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(ty, tz)
        if ln < 1e-12:
            continue
        psi = math.degrees(math.atan2(-ty / ln, tz / ln)) % 360      # normalna zewnętrzna (tz, -ty)
        y, z = poly[i]
        if y < SIDE / 2 and z < SIDE * 0.4 and 149.0 <= psi <= 271.0:
            out.append((psi, y, z))
    out.sort()
    return out


CORNER = _corner_samples()


def corner_pt(psi):
    for (p0, y0, z0), (p1, y1, z1) in zip(CORNER, CORNER[1:]):
        if p0 <= psi <= p1:
            t = (psi - p0) / ((p1 - p0) or 1.0)
            return y0 + (y1 - y0) * t, z0 + (z1 - z0) * t
    if psi < CORNER[0][0]:            # na prostym froncie
        p0, y0, z0 = CORNER[0]
        s = (p0 - psi)
        return y0, z0
    return CORNER[-1][1], CORNER[-1][2]


def ang(psi, r):
    """Odpowiednik ang(psi, r) z klina 5 dla narożnika G2 (r jak przy łuku R5: r > 5 na zewnątrz, r < 5 w głąb)."""
    y, z = corner_pt(psi)
    a = math.radians(psi)
    return y + (r - R_REF) * math.cos(a), z + (r - R_REF) * math.sin(a)


if __name__ == "__main__":
    print("z_top", round(z_top(), 2), " cofnięcie krawędzi boku", round(end_curve()[1], 2))
    for u in (2.0, 3.0, 3.5, 5.0, 7.0, 9.0, 11.0):
        print(f"u {u:4.1f}: zewn. e {e_out(u):.2f}  skóra 2,0 e {e_skin(2.0, u)}")
    for psi in (150, 172, 208, 238, 270):
        print(psi, [round(c, 2) for c in ang(psi, 5.0)], [round(c, 2) for c in ang(psi, 0.5)])
