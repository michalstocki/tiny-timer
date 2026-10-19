"""Obudowa minutnika, wariant "klin": leżący graniastosłup o podstawie trójkąta równobocznego.

Uruchomienie (bez okna):
    /Applications/Blender.app/Contents/MacOS/Blender --background \
        --python tools/enclosure/build_wedge.py

Wejście: docs/pcb-klin/pcb-layout.json (płytka wariantu klin). Wyjście: docs/obudowa-klin/ (.blend, STL, rendery).

Koncepcja ze szkicu właściciela: bok (przekrój poprzeczny) to trójkąt równoboczny o zaokrąglonych rogach, bryła
leży wzdłuż osi X. Wszystkie krawędzie są zaokrąglone (rogi trójkąta oraz obwód boków). Wyświetlacz jest na
skośnej ściance frontowej, trzy przyciski na zaokrąglonym wierzchołku (górna krawędź):
  - "-" i "+" mają powierzchnię zlicowaną z zaokrągleniem wierzchołka (dlatego są wypukłe),
  - środkowy ("run") to lekko wypukła tabletka w wydłużonym obniżeniu.
Przyciski są na OSOBNEJ płytce (poziomej, pod wierzchołkiem), bo leżą w innej płaszczyźnie niż ekran.

Układ współrzędnych obudowy: X wzdłuż graniastosłupa, Y w głąb (od frontu do tyłu), Z w górę, podstawa na z = 0.
Płytka główna leży równolegle do ścianki frontowej (kąt THETA), jej układ (bx, by, bz) jak w specyfikacji:
bx w prawo, by w górę po skosie, bz w stronę użytkownika (od laminatu do panelu).

Części:
  - korpus: tył, podstawa z koszykiem 3xAAA, boki trójkątne (głośnik po lewej),
  - pokrywa: front + wierzchołek + wierzch tyłu. Niesie obie płytki, więc po wykręceniu czterech wkrętów
    z boków schodzi (pionowo w górę) razem z elektroniką. Do korpusu idą tylko przewody baterii i głośnika,
  - klapka koszyka (od spodu) i trzy kapsle przycisków.
"""
import json
import math
import os
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpyutil as U
from bpyutil import (apply_matrix, bevel, box, box_bm, clip_top, coll, cut, cyl, cyl_bm, extrude_x_bm, fillet_poly,
                     finish, inside_convex, intersect, manifold_report, offset_poly, prism_bm, rrect_bm, rrect_pts,
                     union, write_stl)

ROOT = Path(__file__).resolve().parents[2]
# domyślnie płytka wariantu "klin" (bez przycisków, 48 x 36 mm); TT_LAYOUT pozwala zbudować obudowę z innej płytki,
# np. TT_LAYOUT=docs/pcb/pcb-layout.json (podstawowa 48 x 50 mm), a TT_OUT zmienia katalog wyjściowy
LAYOUT = ROOT / os.environ.get("TT_LAYOUT", "docs/pcb-klin/pcb-layout.json")
OUT = ROOT / os.environ.get("TT_OUT", "docs/obudowa-klin")
RENDERS = OUT / "renders"

# ---------------------------------------------------------------- parametry
layout = json.loads(LAYOUT.read_text())
BW, BH, BT = (layout["board"][k] for k in ("width", "height", "thickness"))
HOLES = [(h["x"], h["y"], h["diameter"]) for h in layout["mounting_holes"]]
OLED = layout["parts"]["OLED"]["body"]
GLASS = layout["derived"]["oled_module"]["glass_rect"]
HEIGHT_OVERRIDE = {"U1": 8.5}
REAR = {k: p for k, p in layout["parts"].items() if p["side"] == "bottom" and
        HEIGHT_OVERRIDE.get(k, p["height_above_board"]) > 0}

THETA = 60.0                      # kąt przy podstawie: 60° = trójkąt równoboczny (skos frontu = skos tyłu)
RA, RB = 13.0, 5.0                # promienie zaokrągleń: wierzchołek (przyciski) i rogi podstawy
WALL, PANEL = 2.0, 1.6            # ścianki; panel przedni
T_TOP = 4.4                       # grubość masy pod wierzchołkiem: 2,4 pod obniżeniem + głębokość obniżenia 2,0
WE = 3.0                          # grubość boków trójkątnych
R_END = 3.0                       # zaokrąglenie krawędzi boków trójkątnych
D_PCB = 8.4                       # laminat płytki głównej pod zewnętrzną powierzchnią skosu (OLED 6,5 + luz 0,3 + panel 1,6)
Z_PANEL_IN = D_PCB - PANEL        # wewnętrzna powierzchnia panelu w układzie płytki (bz)
BZ_CEIL = 6.8                     # wewnętrzna powierzchnia sufitu pod wierzchołkiem w układzie płytki przycisków (bz)
D_BTN = T_TOP + BZ_CEIL           # laminat płytki przycisków pod zewnętrznym szczytem wierzchołka
BB_W, BB_D = 52.0, 16.0           # płytka przycisków (rozstaw przycisków 18 mm)
BTN_X = {"minus": 8.0, "run": 26.0, "plus": 44.0}
BTN_LABEL = {"minus": "-", "run": "run", "plus": "+"}
BTN_SCREW_X = (16.0, 36.0)
PILL_L, PILL_W = 14.0, 9.5        # środkowy kapsel: tabletka
DISH_AX, DISH_BY, DISH_DEPTH = 11.0, 6.0, 2.0   # obniżenie: półosie na powierzchni (X, Y) i głębokość
PILL_DROP = 0.6                   # szczyt tabletki pod szczytem wierzchołka
DOME_R = 25.0                     # promień wypukłości tabletki
MARGIN = 1.0

# koszyk 3xAAA (ogniwo Ø10,5 x 44,5), ogniwa wzdłuż X, kanały obok siebie wzdłuż Y, otwarte od spodu
CELL_D, CELL_L = 10.5, 44.5
CAV_L = 51.0
CH_W, DIV, CH_DEPTH, SIDE = 11.0, 1.2, 11.0, 2.0
Z_POCKET = 1.6                    # podłoga koszyka (klapka siedzi we wpuście)
Z_CH_TOP = Z_POCKET + CH_DEPTH
BAT_TOP = Z_CH_TOP + 1.6          # sufit koszyka 1,6
TRAY_W = 3 * CH_W + 2 * DIV
BAT_W = TRAY_W + 2 * SIDE
CELL_ZC = Z_POCKET + CELL_D / 2

# głośnik Ø26,5 x 9 (ramka 4) przy lewym boku
SPK_D, SPK_H, SPK_FR, SPK_POCKET = 26.5, 9.0, 4.0, 27.0
SPK_ZONE = 11.2
RING_L = 5.5
SCR_ZONE = 8.0                    # strefa wkrętów i zapasu przewodów z prawej strony
BOSS_R, BOSS_L = 3.0, 6.5

# układ w X
UA = WE + SPK_ZONE + 1.2          # początek wnęki koszyka
UB = UA + CAV_L
X_BLOCK0 = UA - 1.2
PCB_W = UB - X_BLOCK0
XB = X_BLOCK0 + PCB_W / 2         # środek płytek w X
L = UB + SCR_ZONE + WE

# ---------------------------------------------------------------- przekrój poprzeczny (Y, Z)
th = math.radians(THETA)
sin_t, cos_t, tan_t = math.sin(th), math.cos(th), math.tan(th)
NF = (-sin_t, cos_t)              # normalna zewnętrzna frontu (y, z)
NB = (sin_t, cos_t)               # normalna zewnętrzna tyłu
UBK = (cos_t, -sin_t)             # kierunek wzdłuż tyłu w dół od wierzchołka
BAT_ZTOP_CLEAR = BAT_TOP + 0.5
S_LO = 9.5                        # dolna krawędź pokrywy po skosie (powyżej zaokrąglenia rogu podstawy)
S_TANG_A = RA / math.tan(math.radians((180 - 2 * THETA) / 2))      # od ostrego wierzchołka do początku łuku
S_BACK = S_TANG_A + 14.0          # tylna krawędź pokrywy: po tyle od ostrego wierzchołka wzdłuż tyłu


def profile(side):
    """Wielokąty zewnętrzny i wewnętrzny (z zaokrągleniami) trójkąta o podstawie `side`."""
    h = side / 2 * tan_t
    out_pts = [(0.0, 0.0), (side, 0.0), (side / 2, h)]
    in_pts = offset_poly(out_pts, [WALL, WALL, PANEL])        # krawędzie: podstawa, tył, front
    gamma = math.pi - 2 * th
    z_top = h - RA * (1 / math.sin(gamma / 2) - 1)
    outer = fillet_poly(out_pts, [RB, RB, RA])
    inner_full = fillet_poly(in_pts, [max(RB - WALL, 0.8), max(RB - WALL, 0.8), max(RA - 1.8, 0.8)])
    z_ceil = z_top - T_TOP
    inner = clip_top(inner_full, z_ceil)                       # sufit pod wierzchołkiem (masa pod przyciskami)
    return dict(side=side, H=h, z_top=z_top, z_ceil=z_ceil, out_pts=out_pts, in_pts=in_pts, outer=outer,
                inner=inner, inner_full=inner_full)


def envelope(s0):
    """Punkty (y, z) zajmowane przez płytkę główną i jej elementy od tyłu (z marginesem), próbkowane gęsto."""
    pts = []
    P = lambda s, d: (s * cos_t + d * sin_t, s * sin_t - d * cos_t)
    rects = [(s0 - 1.5, s0 + BH + 1.5, 2.0, D_PCB + BT + MARGIN)]
    for k, p in REAR.items():
        x0, y0, x1, y1 = p["body"]
        h = HEIGHT_OVERRIDE.get(k, p["height_above_board"])
        rects.append((s0 + y0 - MARGIN, s0 + y1 + MARGIN, D_PCB + BT, D_PCB + BT + h + MARGIN))
    for sa, sb, da, db in rects:
        n, m = int(sb - sa) + 2, int(db - da) + 2
        for i in range(n + 1):
            for j in range(m + 1):
                pts.append(P(sa + (sb - sa) * i / n, da + (db - da) * j / m))
    return pts


def feasible(side, s0):
    """Sprawdza, czy w trójkącie o boku `side` mieszczą się: płytka z elementami (nachylona), koszyk
    (nad którym nic nie wisi) i płytka przycisków pod wierzchołkiem."""
    pr = profile(side)
    inner = pr["inner"]
    pts = envelope(s0)
    if any(not inside_convex(inner, p) for p in pts):
        return None
    yb = max([p[0] for p in pts if p[1] < BAT_ZTOP_CLEAR], default=0.0) + 0.5
    if any(not inside_convex(inner, p) for p in [(yb, 2.0), (yb + BAT_W, 2.0), (yb, BAT_TOP), (yb + BAT_W, BAT_TOP)]):
        return None
    yc, zb = side / 2, pr["z_ceil"] - BZ_CEIL
    z_low = zb - BT - 1.9 - 0.5                      # nóżki przycisków pod laminatem
    for hw, z0, z1 in ((BB_D / 2 + 0.5, z_low, zb), (6.5, zb, zb + 4.3 + 0.3)):
        if any(not inside_convex(inner, p) for p in [(yc - hw, z0), (yc + hw, z0), (yc - hw, z1), (yc + hw, z1)]):
            return None
    if any(yc - BB_D / 2 - 0.5 <= p[0] <= yc + BB_D / 2 + 0.5 and z_low <= p[1] <= zb + 4.6 for p in pts):
        return None
    return dict(side=side, s0=s0, yb=yb)


def solve_side():
    for side in [x * 0.5 for x in range(100, 260)]:
        for s0 in [x * 0.5 for x in range(14, 60)]:
            r = feasible(side, s0)
            if r:
                return r
    raise SystemExit("brak rozwiązania przekroju")


SOL = solve_side()
SIDE_LEN, S0, YB = SOL["side"], SOL["s0"], SOL["yb"]
PR = profile(SIDE_LEN)
B, H, Z_TOP, Z_CEIL = SIDE_LEN, PR["H"], PR["z_top"], PR["z_ceil"]
OUTER, INNER, INNER_FULL = PR["outer"], PR["inner"], PR["inner_full"]
YC = B / 2                                            # oś grzbietu (wierzchołka) w Y
ZB = Z_CEIL - BZ_CEIL                                 # górna powierzchnia płytki przycisków


def pt_slope(s, d):
    """Punkt (y, z) na froncie: s po skosie od krawędzi podstawy, d w głąb od zewnętrznej powierzchni."""
    return (s * cos_t + d * sin_t, s * sin_t - d * cos_t)


def pt_back(s, d):
    """Punkt (y, z) na tyle: s po tylnej ściance od ostrego wierzchołka w dół, d w głąb od zewnętrznej powierzchni."""
    return (YC + s * UBK[0] - d * NB[0], H + s * UBK[1] - d * NB[1])


def incircle(poly):
    """Środek i promień największego koła w wypukłym wielokącie."""
    n = len(poly)

    def dist(p):
        d = 1e9
        for i in range(n):
            (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
            d = min(d, ((x1 - x0) * (p[1] - y0) - (y1 - y0) * (p[0] - x0)) / math.hypot(x1 - x0, y1 - y0))
        return d
    cx, cy = sum(p[0] for p in poly) / n, sum(p[1] for p in poly) / n
    best, step = (cx, cy, dist((cx, cy))), 4.0
    for _ in range(60):
        for dx in (-step, 0, step):
            for dy in (-step, 0, step):
                q = (cx + dx, cy + dy)
                d = dist(q)
                if d > best[2]:
                    best = (q[0], q[1], d)
        cx, cy = best[0], best[1]
        step *= 0.85
    return best


SPK_CY, SPK_CZ, SPK_FIT = incircle(INNER_FULL)

# ---------------------------------------------------------------- transformacje
M_SLOPE = Matrix(((1, 0, 0, 0), (0, cos_t, -sin_t, D_PCB * sin_t), (0, sin_t, cos_t, -D_PCB * cos_t), (0, 0, 0, 1)))
M_BOARD = M_SLOPE @ Matrix.Translation((XB - BW / 2, S0, 0))       # (bx, by, bz) płytki głównej -> świat
M_BTN = Matrix.Translation((XB - BB_W / 2, YC - BB_D / 2, ZB))      # (bx, by, bz) płytki przycisków -> świat
R_WIN = (GLASS[3] - GLASS[1] + 0.6) / 2 - 0.005
BZ_TOP = D_BTN                                                      # bz szczytu wierzchołka (w układzie płytki przycisków)
BZ_PILL = BZ_TOP - PILL_DROP                                        # szczyt tabletki
CAP_BOT, CAP_R, CAP_FLANGE_R, PANEL_HOLE_R = 6.0, 4.8, 5.9, 5.1

# wkręty łączące pokrywę z korpusem: po dwa na stronę, wzdłuż X, w bosach pokrywy
Y_A, Z_A = pt_slope(S_LO + 3.5, PANEL + BOSS_R - 0.6)               # bos przy dolnej krawędzi frontu
Y_B, Z_B = pt_back(S_BACK - 7.0, WALL + BOSS_R - 0.6)               # bos pod tylną krawędzią pokrywy
BOSSES = [(Y_A, Z_A), (Y_B, Z_B)]


def to_world(ob, M):
    apply_matrix(ob, M)
    return ob


# ---------------------------------------------------------------- scena
scene = U.init_scene()
C_BODY = (0.90, 0.89, 0.84, 1)
C_DARK = (0.22, 0.24, 0.27, 1)
C_ORANGE = (0.95, 0.45, 0.15, 1)
LID_C = (0.28, 0.30, 0.33, 1)
T = (1, 1, 1, 1)


def chk(label, ob):
    """TT_DEBUG=1: liczba krawędzi nierozmaitościowych po etapie (do szukania kłopotliwych booleanów)."""
    if os.environ.get("TT_DEBUG"):
        print(f"  [{label}] {ob.name}: nie-rozmaitościowe {manifold_report(ob)[0]}")
        if os.environ.get("TT_DEBUG") == "2":
            bmm = bmesh.new()
            bmm.from_mesh(ob.data)
            for e in bmm.edges:
                if not e.is_manifold:
                    a, b = (v.co for v in e.verts)
                    print(f"      krawędź ({a.x:.2f},{a.y:.2f},{a.z:.2f}) - ({b.x:.2f},{b.y:.2f},{b.z:.2f})")
            bmm.free()


def tmp(name, bm):
    return finish(name, bm, "tmp", T)


def regroup(ob, group, color):
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    coll(group).objects.link(ob)
    ob["grupa"] = group
    ob.color = color
    return ob


def outer_solid(x0=0.0, x1=L):
    return tmp("obrys", extrude_x_bm(OUTER, x0, x1))


def zone_poly(s_lo, s_back):
    """Pas ścianek pokrywy: od s_lo po froncie (od krawędzi podstawy), przez wierzchołek, do s_back po tyle
    (od ostrego wierzchołka). Obejmuje też ok. 4 mm wnętrza, ale nie koszyk."""
    fy, fz = s_lo * cos_t, s_lo * sin_t
    a_in, a_out = (fy - 4.4 * NF[0], fz - 4.4 * NF[1]), (fy + 8 * NF[0], fz + 8 * NF[1])
    by_, bz_ = YC + s_back * UBK[0], H + s_back * UBK[1]
    b_in, b_out = (by_ - 4.4 * NB[0], bz_ - 4.4 * NB[1]), (by_ + 8 * NB[0], bz_ + 8 * NB[1])
    p1 = (YC + 10 * NF[0], H + 10 * NF[1] + 10)
    p2 = (YC + 10 * NB[0], H + 10 * NB[1] + 10)
    return [a_in, a_out, p1, p2, b_out, b_in]


def xcyl(name, y, z, x0, x1, r, seg=32):
    return cyl(name, y, z, x0, x1, r, seg=seg, axis="X")


def boxuv(name, u0, u1, v0, v1, z0, z1, group="tmp", color=T):
    """Prostopadłościan z zakresem u (wzdłuż X), v (wzdłuż Y), z."""
    return box(name, u0, v0, z0, u1, v1, z1, group, color)


# --- powłoka: obrys (zaokrąglony także na krawędziach boków) - wnętrze z sufitem pod wierzchołkiem
# koszyk (pełny blok od podstawy) zostaje w materiale: odejmuję go od wnętrza zamiast dokładać do gotowej
# powłoki (dolna ściana bloku leżałaby w jednej płaszczyźnie z podstawą, co daje zdegenerowane krawędzie)
TX0, TX1 = X_BLOCK0, UB + 1.2
V0 = YB + SIDE
CH_V = [(V0 + i * (CH_W + DIV), V0 + i * (CH_W + DIV) + CH_W) for i in range(3)]
CH_VC = [(a + b) / 2 for a, b in CH_V]
V1 = CH_V[2][1]
shell = outer_solid()
bevel(shell, R_END, segments=6)
cavity = tmp("wnetrze", extrude_x_bm(INNER, WE, L - WE))
cut(cavity, boxuv("koszyk", TX0, TX1, YB, YB + BAT_W, 0.0, BAT_TOP))
cut(shell, cavity)
chk("powłoka", shell)

# --- podział na pokrywę i korpus (szczeliny 0,25 mm), pokrywa w x = WE+0,25 ... L-WE-0,25, poza zaokrągleniem boków
cover = bpy.data.objects.new("Pokrywa", shell.data.copy())
coll("tmp").objects.link(cover)
regroup(cover, "Pokrywa", LID_C)
intersect(cover, tmp("strefa_pokrywy", extrude_x_bm(zone_poly(S_LO, S_BACK), WE + 0.25, L - WE - 0.25)))
body = regroup(shell, "Korpus", C_BODY)
body.name = "Korpus"
cut(body, tmp("strefa_korpusu", extrude_x_bm(zone_poly(S_LO - 0.25, S_BACK + 0.25), WE, L - WE)))
chk("podział", body)

# ================================================================ POKRYWA
# okno OLED (szkło + 0,3 mm luzu na stronę), końce półkoliste
cut(cover, to_world(tmp("okno", rrect_bm(GLASS[0] - 0.3, GLASS[1] - 0.3, Z_PANEL_IN - 0.5,
                                         GLASS[2] + 0.3, GLASS[3] + 0.3, D_PCB + 0.5, R_WIN)), M_BOARD))

# słupki płytki głównej (cztery, wkręty M2,5 od tyłu po zdjęciu pokrywy)
feat = None
for hx, hy, _ in HOLES:
    s_ = cyl("slupek", hx, hy, 0.0, D_PCB - 1.0, 2.9, seg=32)
    feat = s_ if feat is None else (union(feat, s_) or feat)
union(cover, to_world(feat, M_BOARD))
for hx, hy, _ in HOLES:
    cut(cover, to_world(cyl("pilot", hx, hy, -0.1, 5.2, 1.05, seg=24), M_BOARD))

# otwory pod kapsle w wierzchołku (przez grubą masę), obniżenie pod środkową tabletkę
for k in ("minus", "plus"):
    cut(cover, to_world(cyl("otw", BTN_X[k], BB_D / 2, BZ_CEIL - 0.5, BZ_TOP + 4.0, PANEL_HOLE_R), M_BTN))
cut(cover, to_world(tmp("otw_run", rrect_bm(BTN_X["run"] - PILL_L / 2 - 0.3, BB_D / 2 - PILL_W / 2 - 0.3, BZ_CEIL - 0.5,
                                            BTN_X["run"] + PILL_L / 2 + 0.3, BB_D / 2 + PILL_W / 2 + 0.3, BZ_TOP + 4.0,
                                            PILL_W / 2 + 0.3)), M_BTN))
RS = (DISH_BY ** 2 + DISH_DEPTH ** 2) / (2 * DISH_DEPTH)            # promień kuli, z której powstaje obniżenie
bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=96, v_segments=48, radius=RS)
bmesh.ops.scale(bm, vec=(DISH_AX / DISH_BY, 1.0, 1.0), verts=bm.verts)
bmesh.ops.translate(bm, vec=(XB, YC, Z_TOP - DISH_DEPTH + RS), verts=bm.verts)
cut(cover, tmp("zaglebienie", bm))
chk("pokrywa: przyciski", cover)

# słupki płytki przycisków (2 szt. między przyciskami), M2 od spodu po zdjęciu pokrywy
for bx in BTN_SCREW_X:
    union(cover, to_world(cyl("slupek_b", bx, BB_D / 2, 0.0, BZ_CEIL + 0.6, 1.8, seg=24), M_BTN))
    cut(cover, to_world(cyl("pilot_b", bx, BB_D / 2, -0.1, 5.5, 0.85, seg=20), M_BTN))

# bosy na wkręty boczne (wzdłuż X), otwory prowadzące
for y, z in BOSSES:
    union(cover, xcyl("bos_l", y, z, WE + 0.25, WE + 0.25 + BOSS_L, BOSS_R),
          xcyl("bos_p", y, z, L - WE - 0.25 - BOSS_L, L - WE - 0.25, BOSS_R))
    cut(cover, xcyl("pilot_l", y, z, WE + 0.2, WE + 0.25 + BOSS_L - 0.5, 1.05, 24),
        xcyl("pilot_p", y, z, L - WE - 0.25 - BOSS_L + 0.5, L - WE - 0.2, 1.05, 24))
chk("pokrywa: bosy", cover)

# ================================================================ KORPUS
# koszyk: trzy kanały otwarte od spodu, okno w podłodze, wpust klapki
for va, vb in CH_V:
    cut(body, boxuv("kanal", UA, UB, va, vb, Z_POCKET, Z_CH_TOP))
chk("kanały", body)
WIN_U, WIN_V = (UA + 1.0, UB - 1.0), (CH_V[0][0] + 0.05, V1 - 0.05)
cut(body, boxuv("okno_bat", *WIN_U, *WIN_V, -0.5, Z_POCKET + 0.3))
REC_U, REC_V = (WIN_U[0] - 1.0, WIN_U[1] + 1.0), (WIN_V[0] - 0.9, WIN_V[1] + 0.9)
cut(body, boxuv("wpust_bat", *REC_U, *REC_V, -0.5, 0.8))
chk("okno+wpust", body)
d1, d2 = (CH_V[0][1], CH_V[1][0]), (CH_V[1][1], CH_V[2][0])
cut(body, boxuv("sz1", UB - 0.7, UB + 0.1, d1[0] - 0.2, d1[1] + 0.2, Z_POCKET, Z_CH_TOP),
    boxuv("sz2", UA - 0.1, UA + 0.7, d2[0] - 0.2, d2[1] + 0.2, Z_POCKET, Z_CH_TOP))
HK_U = (UA + 2.5, UA + 6.0)
cut(body, boxuv("zat1", HK_U[0] - 0.5, HK_U[1] + 0.5, CH_V[0][0] - 0.6, CH_V[0][0] + 0.2, Z_POCKET + 1.2, Z_POCKET + 3.2),
    boxuv("zat2", HK_U[0] - 0.5, HK_U[1] + 0.5, V1 - 0.2, V1 + 0.6, Z_POCKET + 1.2, Z_POCKET + 3.2))
chk("szczeliny+zatrzaski", body)
cut(body, cyl("palec", UB + 2.0, (WIN_V[0] + WIN_V[1]) / 2, -0.5, 0.8, 4.5, seg=40))
# otwory na przewody baterii w suficie koszyka (minus przy lewym końcu kanału 1, plus przy prawym kanału 3)
cut(body, cyl("prz_minus", UA + 2.5, CH_VC[0], Z_CH_TOP - 0.5, BAT_TOP + 0.5, 1.5, seg=24),
    cyl("prz_plus", UB - 2.5, CH_VC[2], Z_CH_TOP - 0.5, BAT_TOP + 0.5, 1.5, seg=24))

# głośnik: pierścień oporowy przy lewym boku i otwory dźwiękowe w trójkątnym boku
ring = xcyl("pierscien", SPK_CY, SPK_CZ, WE - 0.2, WE + RING_L, SPK_POCKET / 2 + 1.9, 96)
cut(ring, xcyl("pierscien_w", SPK_CY, SPK_CZ, WE - 0.5, WE + RING_L + 0.5, SPK_POCKET / 2, 96))
intersect(ring, outer_solid())
union(body, ring)
chk("pierścień", body)
holes = [(0.0, 0.0)]
holes += [(4.5 * math.cos(2 * math.pi * i / 8 + 0.2), 4.5 * math.sin(2 * math.pi * i / 8 + 0.2)) for i in range(8)]
holes += [(9.0 * math.cos(2 * math.pi * i / 14 + 0.07), 9.0 * math.sin(2 * math.pi * i / 14 + 0.07)) for i in range(14)]
# wszystkie otwory jednym wycięciem (jeden cutter z wieloma walcami: mniej artefaktów niż 23 osobne booleany)
bm = bmesh.new()
for dy, dz in holes:
    ret = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=20, radius1=1.0, radius2=1.0, depth=WE + 0.8)
    bmesh.ops.rotate(bm, verts=ret["verts"], cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "Y"))
    bmesh.ops.translate(bm, vec=((WE + 0.3 - 0.5) / 2, SPK_CY + dy, SPK_CZ + dz), verts=ret["verts"])
cut(body, tmp("dzwieki", bm))
chk("otwory głośnika", body)

# wkręty boczne: otwór przelotowy w boku i zagłębienie na łeb
for y, z in BOSSES:
    cut(body, xcyl("w_otw_l", y, z, -0.5, WE + 0.1, 1.35, 24), xcyl("w_lb_l", y, z, -0.5, 1.0, 2.4, 32),
        xcyl("w_otw_p", y, z, L - WE - 0.1, L + 0.5, 1.35, 24), xcyl("w_lb_p", y, z, L - 1.0, L + 0.5, 2.4, 32))
chk("wkręty boczne", body)

# ================================================================ KLAPKA KOSZYKA
lid = finish("Klapka_baterii", box_bm(REC_U[0] + 0.25, REC_V[0] + 0.25, 0.0, REC_U[1] - 0.25, REC_V[1] - 0.25, 0.8),
             "Klapka", LID_C)
union(lid, boxuv("wtyk", WIN_U[0] + 0.25, WIN_U[1] - 0.25, WIN_V[0] + 0.25, WIN_V[1] - 0.25, 0.8, Z_POCKET))
vl, vh = WIN_V[0] + 0.25, WIN_V[1] - 0.25
union(lid,
      boxuv("jezyk1", *HK_U, vl, vl + 0.8, Z_POCKET, Z_POCKET + 3.0),
      boxuv("zab1", *HK_U, CH_V[0][0] - 0.4, vl + 0.1, Z_POCKET + 1.4, Z_POCKET + 2.9),
      boxuv("jezyk2", *HK_U, vh - 0.8, vh, Z_POCKET, Z_POCKET + 3.0),
      boxuv("zab2", *HK_U, vh - 0.1, V1 + 0.4, Z_POCKET + 1.4, Z_POCKET + 2.9))

# ================================================================ KAPSLE (w układzie płytki przycisków)
caps = []
SURF_R = RA - 0.15                                    # powierzchnia "-" i "+": zlicowana z zaokrągleniem wierzchołka
for k, bx in BTN_X.items():
    lab = BTN_LABEL[k]
    color = {"minus": C_DARK, "run": C_ORANGE, "plus": C_DARK}[k]
    y0 = BB_D / 2
    if k == "run":
        top = BZ_PILL
        cap = finish("Kapsel_run", rrect_bm(bx - PILL_L / 2, y0 - PILL_W / 2, CAP_BOT, bx + PILL_L / 2, y0 + PILL_W / 2,
                                              top + 3.0, PILL_W / 2), "Kapsle", color)
        dome = bmesh.new()
        bmesh.ops.create_uvsphere(dome, u_segments=96, v_segments=48, radius=DOME_R)
        bmesh.ops.translate(dome, vec=(bx, y0, top - DOME_R), verts=dome.verts)
        intersect(cap, tmp("kopula", dome))                       # lekko wypukła tabletka
        union(cap, finish("kolnierz", rrect_bm(bx - PILL_L / 2 - 0.8, y0 - PILL_W / 2 - 0.8, CAP_BOT,
                                               bx + PILL_L / 2 + 0.8, y0 + PILL_W / 2 + 0.8, CAP_BOT + 0.6,
                                               PILL_W / 2 + 0.8), "tmp", T))
        zt = top - 0.4
        cut(cap, finish("tri", prism_bm([(bx - 1.6, y0 - 2.1), (bx + 2.3, y0), (bx - 1.6, y0 + 2.1)], zt, top + 0.1), "tmp", T))
    else:
        cap = cyl("Kapsel_" + lab, bx, y0, CAP_BOT, BZ_TOP + 2.0, CAP_R, "Kapsle", color, seg=48)
        surf = cyl("powierzchnia", y0, BZ_TOP - RA, bx - 8, bx + 8, SURF_R, seg=96, axis="X")
        intersect(cap, surf)                                      # górna powierzchnia = zaokrąglenie wierzchołka
        union(cap, cyl("kolnierz", bx, y0, CAP_BOT, CAP_BOT + 0.6, CAP_FLANGE_R, seg=48))
        zt = BZ_TOP - 0.15 - 0.4
        if lab == "-":
            cut(cap, box("m", bx - 2.2, y0 - 0.5, zt, bx + 2.2, y0 + 0.5, BZ_TOP + 0.5))
        else:
            cut(cap, box("p1", bx - 2.2, y0 - 0.5, zt, bx + 2.2, y0 + 0.5, BZ_TOP + 0.5),
                box("p2", bx - 0.5, y0 - 2.2, zt, bx + 0.5, y0 + 2.2, BZ_TOP + 0.5))
    cut(cap, box("gniazdo", bx - 2.0, y0 - 2.0, CAP_BOT - 0.1, bx + 2.0, y0 + 2.0, 7.3))
    to_world(cap, M_BTN)
    caps.append(cap)

# ================================================================ STYKI, OGNIWA (podgląd)
C_NICKEL, C_CELL, C_GOLD = (0.78, 0.74, 0.62, 1), (0.20, 0.42, 0.72, 1), (0.85, 0.65, 0.20, 1)
SPR_R = 3.0
swap = [False, True, False]          # ogniwo 2 odwrócone (szereg)
for i, vc in enumerate(CH_VC):
    if not swap[i]:
        c0 = UA + 6.0
        c1 = c0 + CELL_L
        body_u, nub_u = (c0, c1 - 0.8), (c1 - 0.8, c1)
    else:
        c0 = UA + 0.5
        c1 = c0 + CELL_L
        body_u, nub_u = (c0 + 0.8, c1), (c0, c0 + 0.8)
    finish(f"AAA_{i + 1}", cyl_bm(vc, CELL_ZC, body_u[0], body_u[1], CELL_D / 2, axis="X"), "Baterie", C_CELL)
    finish(f"AAA_{i + 1}_plus", cyl_bm(vc, CELL_ZC, nub_u[0], nub_u[1], 2.0, axis="X"), "Baterie", C_GOLD)


def plate(name, u_end, va, vb):
    ua, ub = (u_end, u_end + 0.5) if u_end == UA else (u_end - 0.5, u_end)
    return box(name, ua, va, CELL_ZC - 4.5, ub, vb, CELL_ZC + 4.5, "Styki", C_NICKEL)


def spring(name, vc, low_end):
    if low_end:
        return finish(name, cyl_bm(vc, CELL_ZC, UA + 0.5, UA + 6.0, SPR_R, r2=SPR_R * 0.55, axis="X", seg=32), "Styki", C_NICKEL)
    return finish(name, cyl_bm(vc, CELL_ZC, UA + 0.5 + CELL_L, UB - 0.5, SPR_R * 0.55, r2=SPR_R, axis="X", seg=32), "Styki", C_NICKEL)


v1, v2, v3 = CH_VC
spring("sprezyna_1", v1, True)
plate("plytka_1_neg", UA, v1 - 4.5, v1 + 4.5)
spring("sprezyna_3", v3, True)
plate("plytka_lacznik_niski", UA, v2 - 4.5, v3 + 4.5)
spring("sprezyna_2", v2, False)
plate("plytka_lacznik_wysoki", UB, v1 - 4.5, v2 + 4.5)
plate("plytka_3_pos", UB, v3 - 4.5, v3 + 4.5)

# ================================================================ PŁYTKI I GŁOŚNIK (podgląd, nie do wydruku)
C_PCB, C_BLACK, C_PART = (0.10, 0.42, 0.22, 1), (0.04, 0.04, 0.05, 1), (0.55, 0.40, 0.25, 1)
pcb = finish("PCB", rrect_bm(0, 0, -BT, BW, BH, 0, 3.0), "Plytka", C_PCB)
for hx, hy, hd in HOLES:
    cut(pcb, cyl("o", hx, hy, -BT - 0.5, 0.5, hd / 2, seg=24))
to_world(pcb, M_BOARD)
to_world(box("OLED_modul", OLED[0], OLED[1], 2.5, OLED[2], OLED[3], 6.5, "Plytka", C_BLACK), M_BOARD)
to_world(box("OLED_szklo", GLASS[0], GLASS[1], 6.3, GLASS[2], GLASS[3], 6.5, "Plytka", (0.10, 0.20, 0.45, 1)), M_BOARD)
for name, p in REAR.items():
    bx0, by0, bx1, by1 = p["body"]
    h = HEIGHT_OVERRIDE.get(name, p["height_above_board"])
    to_world(box("el_" + name, bx0, by0, -BT - h, bx1, by1, -BT, "Plytka", C_PART), M_BOARD)

bpcb = finish("PCB_przyciski", rrect_bm(0, 0, -BT, BB_W, BB_D, 0, 2.0), "Plytka_przyciskow", C_PCB)
for bx in BTN_SCREW_X:
    cut(bpcb, cyl("o", bx, BB_D / 2, -BT - 0.5, 0.5, 1.1, seg=20))
to_world(bpcb, M_BTN)
for k, bx in BTN_X.items():
    parts = [box("B3F_" + k, bx - 6, BB_D / 2 - 6, 0, bx + 6, BB_D / 2 + 6, 4.3, "Plytka_przyciskow", (0.15, 0.15, 0.17, 1)),
             cyl("B3F_podstawa_" + k, bx, BB_D / 2, 4.3, 5.5, 3.55, "Plytka_przyciskow", (0.3, 0.3, 0.32, 1), seg=32),
             box("B3F_trzpien_" + k, bx - 1.9, BB_D / 2 - 1.9, 5.5, bx + 1.9, BB_D / 2 + 1.9, 7.3, "Plytka_przyciskow", (0.8, 0.8, 0.82, 1)),
             box("B3F_nozki_" + k, bx - 2.5, BB_D / 2 - 2.5, -BT - 1.9, bx + 2.5, BB_D / 2 + 2.5, -BT, "Plytka_przyciskow", (0.6, 0.6, 0.6, 1))]
    for p_ in parts:
        to_world(p_, M_BTN)

cyl("Glosnik_ramka", SPK_CY, SPK_CZ, WE, WE + SPK_FR, SPK_D / 2, "Glosnik", (0.12, 0.12, 0.13, 1), seg=96, axis="X")
cyl("Glosnik_stozek", SPK_CY, SPK_CZ, WE + SPK_FR, WE + SPK_H, 10.0, "Glosnik", (0.2, 0.2, 0.22, 1), seg=64, axis="X")

# ================================================================ KONTROLA I EKSPORT
printable = {
    "korpus": [body],
    "pokrywa": [cover],
    "klapka-baterii": [lid],
    "kapsle": caps,
}
OUT.mkdir(parents=True, exist_ok=True)
RENDERS.mkdir(parents=True, exist_ok=True)
report = []
for fname, objs in printable.items():
    write_stl(OUT / f"{fname}.stl", objs)
    for ob in objs:
        bad, vol = manifold_report(ob)
        d = ob.dimensions
        report.append(f"{ob.name:18s} wymiary {d.x:6.1f} x {d.y:5.1f} x {d.z:5.1f} mm  objętość {vol:9.1f} mm3  krawędzie nie-rozmaitościowe: {bad}")
print("\n".join(report))
print(f"Trójkąt: bok {B:.1f}  wysokość ostrego wierzchołka {H:.1f}, szczyt po zaokrągleniu {Z_TOP:.1f}  s0 {S0}  koszyk y {YB:.1f}..{YB + BAT_W:.1f}")
print(f"Obrys: L {L:.1f}  płytki w X {XB - 24:.1f}..{XB + 24:.1f}  płytka przycisków x {XB - BB_W / 2:.1f}..{XB + BB_W / 2:.1f}, z góry {ZB:.1f}  sufit {Z_CEIL:.1f}")
print(f"Głośnik: środek (y {SPK_CY:.1f}, z {SPK_CZ:.1f}), r wolne {SPK_FIT:.1f} (potrzeba {SPK_POCKET / 2 + 1.9:.1f} z pierścieniem)")
print(f"Bosy (y, z): {[(round(y, 1), round(z, 1)) for y, z in BOSSES]}")

bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "obudowa-klin.blend"))
if "--norender" in sys.argv:
    print("GOTOWE (bez renderów)")
    raise SystemExit

# ---------------------------------------------------------------- rendery
GROUPS = {}
for ob in bpy.data.objects:
    GROUPS.setdefault(ob.get("grupa", ""), []).append(ob)

world = bpy.data.worlds.new("w")
scene.world = world
scene.render.engine = "BLENDER_EEVEE"
scene.eevee.taa_render_samples = 48
for ob in bpy.data.objects:
    if ob.type == "MESH" and all(m is None for m in ob.data.materials):
        ob.data.materials.clear()
        mat = bpy.data.materials.new(ob.name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = ob.color
        bsdf.inputs["Roughness"].default_value = 0.55
        ob.data.materials.append(mat)


def smooth(ob):
    ob.data.shade_smooth()
    ob.data.set_sharp_from_angle(angle=math.radians(35))


for ob in bpy.data.objects:
    if ob.type == "MESH":
        smooth(ob)
scene.render.resolution_x, scene.render.resolution_y = 1500, 1100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
cam_data = bpy.data.cameras.new("cam")
cam = bpy.data.objects.new("cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
sun_data = bpy.data.lights.new("sun", "SUN")
sun_data.energy = 2.0
sun_data.angle = math.radians(6)
sun = bpy.data.objects.new("sun", sun_data)
scene.collection.objects.link(sun)
sun.parent = cam
sun.rotation_euler = (math.radians(18), math.radians(-22), 0)
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.85, 0.87, 0.90, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.55


def aim(loc, tgt, up=(0, 0, 1)):
    f = (Vector(tgt) - Vector(loc)).normalized()
    z = -f
    x = Vector(up).cross(z).normalized()
    y = z.cross(x)
    m = Matrix(((x.x, y.x, z.x), (x.y, y.y, z.y), (x.z, y.z, z.z)))
    cam.matrix_world = Matrix.Translation(loc) @ m.to_4x4()


def render(name, show, loc, tgt, up=(0, 0, 1), ortho=None, lens=75):
    shown = set()
    for g in show:
        shown.update(o.name for o in GROUPS.get(g, []))
    for ob in bpy.data.objects:
        if ob.type == "MESH":
            ob.hide_render = ob.name not in shown
    cam_data.type = "ORTHO" if ortho else "PERSP"
    if ortho:
        cam_data.ortho_scale = ortho
    else:
        cam_data.lens = lens
    cam_data.clip_start, cam_data.clip_end = 1, 3000
    aim(loc, tgt, up)
    scene.render.filepath = str(RENDERS / name)
    bpy.ops.render.render(write_still=True)


def make_section(axis, pos):
    big = 600
    out = []
    for g in ALL:
        for o in GROUPS.get(g, []):
            dup = o.copy()
            dup.data = o.data.copy()
            coll("Przekroj").objects.link(dup)
            dup["grupa"] = "Przekroj"
            c = box("pl", -big, pos - big, -big, big, pos, big) if axis == "y" else box("pl", pos - big, -big, -big, pos, big, big)
            U.boolean(dup, c)
            smooth(dup)
            out.append(dup)
    GROUPS["Przekroj"] = out
    return out


def drop_section(objs):
    for o in objs:
        bpy.data.objects.remove(o, do_unlink=True)
    GROUPS["Przekroj"] = []


ALL = ["Korpus", "Pokrywa", "Klapka", "Kapsle", "Styki", "Baterie", "Plytka", "Plytka_przyciskow", "Glosnik"]
SHELL = ["Korpus", "Pokrywa", "Klapka", "Kapsle"]
cx = L / 2
n_front = Vector((0, NF[0], NF[1]))
front_c = Vector((XB, *pt_slope(S0 + 18, 0)))

render("01-przod-iso.png", SHELL, (cx + 200, -150, H * 0.8 + 120), (cx, B * 0.5, H * 0.4), lens=70)
render("02-przod-prostopadle.png", SHELL, front_c + n_front * 400, front_c, up=(0, cos_t, sin_t), ortho=140)
render("03-gora.png", SHELL, (cx, YC, 500), (cx, YC, 0), up=(0, 1, 0), ortho=130)
render("04-bok-lewy-glosnik.png", SHELL, (-300, B / 2, H / 2), (0, B / 2, H / 2), ortho=120)
render("05-spod-klapka.png", SHELL, (cx, B * 0.5, -300), (cx, B * 0.5, 0), up=(0, 1, 0), ortho=130)
render("06-spod-koszyk-otwarty.png", ["Korpus", "Pokrywa", "Kapsle", "Styki", "Baterie"], (cx + 60, B * 0.5 - 90, -230), (cx, B * 0.5, 8), up=(0, 1, 0), lens=70)
render("07-tyl-iso.png", SHELL, (cx - 150, B + 180, H * 0.8 + 100), (cx, B * 0.5, H * 0.4), lens=70)

# pokrywa zdjęta razem z płytkami: podnoszona pionowo (pokrywa obejmuje wierzchołek, więc tylko w górę)
lift = Vector((0, 0, 70))
for g in ("Pokrywa", "Kapsle", "Plytka", "Plytka_przyciskow"):
    for o in GROUPS[g]:
        o.location += lift
render("08-pokrywa-zdjeta.png", ALL, (cx + 300, -240, H * 0.8 + 200), (cx, B * 0.45, H * 0.8), lens=50)
render("09-pokrywa-od-tylu.png", ["Pokrywa", "Kapsle", "Plytka", "Plytka_przyciskow"], (cx - 60, B + 90, H * 0.4 + lift.z), (cx, B * 0.45, H * 0.5 + lift.z), lens=65)
for g in ("Pokrywa", "Kapsle", "Plytka", "Plytka_przyciskow"):
    for o in GROUPS[g]:
        o.location -= lift
sec = make_section("x", XB)
render("10-przekroj-poprzeczny.png", ["Przekroj"], (-400, B / 2, H / 2), (XB, B / 2, H / 2), ortho=120)
drop_section(sec)
sec = make_section("x", XB + BTN_X["plus"] - BTN_X["run"])        # przekrój przez przycisk "+"
render("11-przekroj-przycisk-plus.png", ["Przekroj"], (-400, YC, Z_TOP - 20), (XB, YC, Z_TOP - 20), ortho=60)
drop_section(sec)
render("12-przyciski-zblizenie.png", SHELL, (XB + 55, YC - 70, Z_TOP + 60), (XB, YC, Z_TOP - 2), lens=95)
render("13-przyciski-z-gory.png", SHELL, (XB, YC, Z_TOP + 200), (XB, YC, Z_TOP), up=(0, 1, 0), ortho=60)

for ob in bpy.data.objects:
    ob.hide_render = False
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "obudowa-klin.blend"))
print("GOTOWE")
