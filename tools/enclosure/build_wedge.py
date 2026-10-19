"""Obudowa minutnika, wariant "klin" (alternatywa dla płaskiego stosu z iteracji 2).

Uruchomienie (bez okna):
    /Applications/Blender.app/Contents/MacOS/Blender --background \
        --python tools/enclosure/build_wedge.py

Wejście: docs/pcb-klin/pcb-layout.json (płytka wariantu klin). Wyjście: docs/obudowa-klin/ (.blend, STL, rendery).

Koncepcja ze szkicu właściciela: bryła w kształcie klina (przekrój poprzeczny to ścięty trójkąt,
boki trójkątne wzdłuż X), wyświetlacz na pochyłej ściance frontowej, trzy przyciski na płaskim
grzbiecie. Przyciski leżą w innej płaszczyźnie niż ekran, więc są na OSOBNEJ płytce
(poziomej, pod grzbietem). Środkowy przycisk (run) stoi niżej, w płytkim wklęsłym zagłębieniu.

Układ współrzędnych obudowy: X wzdłuż klina, Y w głąb (od frontu do tyłu), Z w górę, podstawa na z = 0.
Płytka główna leży równolegle do ścianki frontowej (kąt ALPHA), jej układ (bx, by, bz) jak w specyfikacji:
bx w prawo, by w górę po skosie, bz w stronę użytkownika (od laminatu do panelu).

Części:
  - korpus: tył, podstawa z koszykiem 3xAAA, boki trójkątne (głośnik po lewej), tylna część grzbietu,
  - pokrywa: ścianka frontowa + grzbiet. Niesie obie płytki (główną i przycisków), więc po wykręceniu
    czterech wkrętów z boków schodzi razem z elektroniką. Do korpusu idą tylko przewody baterii i głośnika,
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
from bpyutil import (apply_matrix, bevel, box, box_bm, coll, cut, cyl, cyl_bm, extrude_x_bm, fillet_poly,
                     finish, intersect, manifold_report, offset_poly, prism_bm, rrect_bm, text_cutter,
                     union, write_stl)

ROOT = Path(__file__).resolve().parents[2]
# domyślnie płytka wariantu "klin" (bez przycisków, 48 x 36 mm); TT_LAYOUT pozwala zbudować klin z innej płytki,
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
BTN_X = {"minus": 8.0, "run": 24.0, "plus": 40.0}          # środki przycisków na płytce przycisków (rozstaw 16 mm)
BTN_LABEL = {"minus": "-", "run": "run", "plus": "+"}
HEIGHT_OVERRIDE = {"U1": 8.5}
REAR = {k: p for k, p in layout["parts"].items() if p["side"] == "bottom" and
        HEIGHT_OVERRIDE.get(k, p["height_above_board"]) > 0}

ALPHA, BETA = 60.0, 80.0          # kąt skosu frontu (płytka równolegle) i kąt tylnej ścianki
WALL, PANEL, TOP = 2.0, 1.6, 3.6  # ścianki, panel przedni, grzbiet (3,6 = 1,6 pod zagłębieniem + 2,0 jego głębokości)
D_PCB = 8.4                       # laminat płytki głównej pod zewnętrzną powierzchnią skosu (OLED 6,5 + luz 0,3 + panel 1,6)
Z_PANEL_IN = D_PCB - PANEL        # wewnętrzna powierzchnia panelu w układzie płytki (bz)
D_BTN = 10.4                      # laminat płytki przycisków pod zewnętrzną powierzchnią grzbietu
BB_W, BB_D = 48.0, 16.0           # płytka przycisków
DISH_R, DISH_H = 10.0, 2.0        # zagłębienie pod środkowy przycisk: promień na powierzchni, głębokość
CAP_UP = 1.4                      # kapsel wystaje ponad lokalną powierzchnię
MARGIN = 1.0
R_END = 2.0                       # zaokrąglenie krawędzi boków trójkątnych

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
SCR_ZONE = 7.0                    # strefa wkrętów i zapasu przewodów z prawej strony
BOSS_R, BOSS_L = 3.0, 6.5

# układ w X
UA = WALL + SPK_ZONE + 1.2        # początek wnęki koszyka
UB = UA + CAV_L
X_BLOCK0 = UA - 1.2
PCB_W = UB - X_BLOCK0
XB = X_BLOCK0 + PCB_W / 2         # środek płytek w X
L = UB + SCR_ZONE + WALL


# ---------------------------------------------------------------- przekrój poprzeczny (Y, Z)
a_, b_ = math.radians(ALPHA), math.radians(BETA)
tan_a, tan_b = math.tan(a_), math.tan(b_)
sin_a, cos_a = math.sin(a_), math.cos(a_)
BAT_ZTOP_CLEAR = BAT_TOP + 0.5


def envelope(s0):
    """Punkty (y, z) zajmowane z tyłu płytki głównej (laminat i elementy z marginesem), próbkowane gęsto."""
    pts = []
    P = lambda s, d: (s * cos_a + d * sin_a, s * sin_a - d * cos_a)
    rects = [(s0 - 1.5, s0 + BH + 1.5, 0.0, D_PCB + BT + MARGIN)]
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


def solve_profile():
    """Najmniejszy przekrój (H x B), w którym mieszczą się: płytka z elementami od tyłu, koszyk, nad którym
    nic nie wisi, i płytka przycisków pod grzbietem z pasem na styk pokrywy z korpusem."""
    best = None
    bb_below = D_BTN + 1.6 + 1.9 + 1.0          # w dół od grzbietu: płytka, laminat, nóżki, luz
    for s0 in [x * 0.5 for x in range(8, 70)]:
        pts = envelope(s0)
        if min(p[1] for p in pts) < WALL + 0.5:
            continue
        for dh in range(0, 17, 2):
            yb = max([p[0] for p in pts if p[1] < BAT_ZTOP_CLEAR], default=0.0) + 0.5
            H = max((s0 + BH + 1.5 + 3.5) * sin_a, max(p[1] for p in pts) + TOP) + dh
            yf = H / tan_a
            band = [p for p in pts if p[1] >= H - bb_below]
            yk = max(max([p[0] for p in band], default=yf) + 1.0, yf + 1.0)
            y_cut = yk + BB_D + 1.5                  # koniec pokrywy na grzbiecie
            need_back = max(max(p[0] + p[1] / tan_b for p in pts),
                            yb + BAT_W + BAT_TOP / tan_b,
                            y_cut + 7.2 + H / tan_b)  # 7,2: zaokrąglenie narożnika grzbietu + pas korpusu
            B = need_back + WALL / math.sin(b_)
            if best is None or H * B < best["H"] * best["B"]:
                best = dict(s0=s0, dh=dh, H=H, B=B, yb=yb, yk=yk, yf=yf, y_cut=y_cut)
    return best


SOL = solve_profile()
S0, H, B, YB, YK, YF, Y_CUT = (SOL[k] for k in ("s0", "H", "B", "yb", "yk", "yf", "y_cut"))
YV = B - H / tan_b                                   # tylny narożnik grzbietu
OUT_PTS = [(0.0, 0.0), (B, 0.0), (YV, H), (YF, H)]
IN_PTS = offset_poly(OUT_PTS, [WALL, WALL, TOP, PANEL])
OUTER = fillet_poly(OUT_PTS, [3.0, 3.0, 5.0, 5.0])
INNER = fillet_poly(IN_PTS, [1.0, 1.0, 3.0, 3.0])
NF = (-sin_a, cos_a)                                  # normalna zewnętrzna frontu (y, z)
S_LO = 6.75                                           # dolna krawędź pokrywy (po skosie od krawędzi podstawy)


def pt_slope(s, d):
    """Punkt (y, z) na skosie: s po skosie od krawędzi podstawy, d w głąb od zewnętrznej powierzchni."""
    return (s * cos_a + d * sin_a, s * sin_a - d * cos_a)


def incircle(poly):
    """Środek i promień największego koła w wypukłym wielokącie."""
    n = len(poly)

    def dist(p):
        d = 1e9
        for i in range(n):
            (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
            ln = math.hypot(x1 - x0, y1 - y0)
            d = min(d, ((x1 - x0) * (p[1] - y0) - (y1 - y0) * (p[0] - x0)) / ln)
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


SPK_CY, SPK_CZ, SPK_FIT = incircle(IN_PTS)

# ---------------------------------------------------------------- transformacje
M_SLOPE = Matrix(((1, 0, 0, 0), (0, cos_a, -sin_a, D_PCB * sin_a), (0, sin_a, cos_a, -D_PCB * cos_a), (0, 0, 0, 1)))
M_BOARD = M_SLOPE @ Matrix.Translation((XB - BW / 2, S0, 0))       # (bx, by, bz) płytki głównej -> świat
M_BTN = Matrix.Translation((XB - BB_W / 2, YK, H - D_BTN))           # (bx, by, bz) płytki przycisków -> świat
BTN_Y = YK + BB_D / 2
R_WIN = (GLASS[3] - GLASS[1] + 0.6) / 2 - 0.005
D_RUN = D_BTN - DISH_H                                              # bz powierzchni na dnie zagłębienia
CAP_TOP = {"minus": D_BTN + CAP_UP, "plus": D_BTN + CAP_UP, "run": D_RUN + CAP_UP}
CAP_BOT, CAP_R, CAP_FLANGE_R, PANEL_HOLE_R = 6.0, 4.8, 5.9, 5.1

# wkręty łączące pokrywę z korpusem: po dwa na stronę, wzdłuż X, w bosach pokrywy
Y_A, Z_A = pt_slope(11.5, PANEL + BOSS_R - 0.6)                      # bos przy dolnej krawędzi frontu
Y_B, Z_B = (YF + YK) / 2, H - TOP - BOSS_R + 0.6                     # bos pod grzbietem, przed płytką przycisków
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


def zone_poly(s_lo, y_cut):
    """Pas ścianek frontu i grzbietu: od s_lo po skosie do y_cut na grzbiecie (z 4 mm wnętrza)."""
    fy, fz = s_lo * cos_a, s_lo * sin_a
    a_in = (fy - 4.4 * NF[0], fz - 4.4 * NF[1])
    a_out = (fy + 8 * NF[0], fz + 8 * NF[1])
    c_out = (YF + 6 * NF[0], H + 6 * (NF[1] + 1.0))
    return [a_in, a_out, c_out, (y_cut, H + 6), (y_cut, H - 5.6)]


def xcyl(name, y, z, x0, x1, r, seg=32):
    return cyl(name, y, z, x0, x1, r, seg=seg, axis="X")


def boxuv(name, u0, u1, v0, v1, z0, z1, group="tmp", color=T):
    """Prostopadłościan z zakresem u (wzdłuż X), v (wzdłuż Y), z."""
    return box(name, u0, v0, z0, u1, v1, z1, group, color)


# --- powłoka: obrys - wnętrze (wnętrze od x = WALL do L - WALL)
# koszyk (pełny blok od podstawy) zostaje w materiale: odejmuję go od wnętrza zamiast dokładać do gotowej
# powłoki (dolna ściana bloku leżałaby w jednej płaszczyźnie z podstawą, co daje zdegenerowane krawędzie)
TX0, TX1 = X_BLOCK0, UB + 1.2
V0 = YB + SIDE
CH_V = [(V0 + i * (CH_W + DIV), V0 + i * (CH_W + DIV) + CH_W) for i in range(3)]
CH_VC = [(a + b) / 2 for a, b in CH_V]
V1 = CH_V[2][1]
shell = outer_solid()
bevel(shell, R_END, segments=5)
cavity = tmp("wnetrze", extrude_x_bm(INNER, WALL, L - WALL))
cut(cavity, boxuv("koszyk", TX0, TX1, YB, YB + BAT_W, 0.0, BAT_TOP))
cut(shell, cavity)
chk("powłoka", shell)

# --- podział na pokrywę i korpus (szczeliny 0,25 mm)
cover = bpy.data.objects.new("Pokrywa", shell.data.copy())
coll("tmp").objects.link(cover)
regroup(cover, "Pokrywa", LID_C)
intersect(cover, tmp("strefa_pokrywy", extrude_x_bm(zone_poly(S_LO, Y_CUT), WALL + 0.25, L - WALL - 0.25)))
body = regroup(shell, "Korpus", C_BODY)
body.name = "Korpus"
cut(body, tmp("strefa_korpusu", extrude_x_bm(zone_poly(S_LO - 0.25, Y_CUT + 0.25), WALL, L - WALL)))
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

# otwory pod kapsle na grzbiecie, zagłębienie pod środkowy przycisk (kulisty wycinek)
for k, bx in BTN_X.items():
    cut(cover, to_world(cyl("otw", bx, BB_D / 2, D_BTN - TOP - 0.5, D_BTN + 0.6, PANEL_HOLE_R), M_BTN))
R_SPH = (DISH_R ** 2 + DISH_H ** 2) / (2 * DISH_H)
bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=96, v_segments=48, radius=R_SPH)
bmesh.ops.translate(bm, vec=(XB, BTN_Y, H - DISH_H + R_SPH), verts=bm.verts)
cut(cover, tmp("zaglebienie", bm))

# słupki płytki przycisków (2 szt. między przyciskami), M2 od spodu po zdjęciu pokrywy
for bx in (16.0, 32.0):
    union(cover, to_world(cyl("slupek_b", bx, BB_D / 2, 0.0, D_BTN - TOP + 0.6, 1.8, seg=24), M_BTN))
    cut(cover, to_world(cyl("pilot_b", bx, BB_D / 2, -0.1, 5.5, 0.85, seg=20), M_BTN))

# bosy na wkręty boczne (wzdłuż X), otwory prowadzące
for y, z in BOSSES:
    union(cover, xcyl("bos_l", y, z, WALL + 0.25, WALL + 0.25 + BOSS_L, BOSS_R),
          xcyl("bos_p", y, z, L - WALL - 0.25 - BOSS_L, L - WALL - 0.25, BOSS_R))
    cut(cover, xcyl("pilot_l", y, z, WALL + 0.2, WALL + 0.25 + BOSS_L - 0.8, 1.05, 24),
        xcyl("pilot_p", y, z, L - WALL - 0.25 - BOSS_L + 0.8, L - WALL - 0.2, 1.05, 24))

# napis na dolnym pasie frontu (grawer 0,4 mm)
cut(cover, to_world(text_cutter("TINY TIMER", 4.2, XB, 10.4, D_PCB - 0.4, 1.0), M_SLOPE))

# ================================================================ KORPUS
# koszyk: blok od podstawy, trzy kanały otwarte od spodu, okno w podłodze, wpust klapki
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
ring = xcyl("pierscien", SPK_CY, SPK_CZ, WALL - 0.2, WALL + RING_L, SPK_POCKET / 2 + 1.9, 96)
cut(ring, xcyl("pierscien_w", SPK_CY, SPK_CZ, WALL - 0.5, WALL + RING_L + 0.5, SPK_POCKET / 2, 96))
intersect(ring, outer_solid())
union(body, ring)
chk("pierścień", body)
holes = [(0.0, 0.0)]
holes += [(4.5 * math.cos(2 * math.pi * i / 8 + 0.2), 4.5 * math.sin(2 * math.pi * i / 8 + 0.2)) for i in range(8)]
holes += [(9.0 * math.cos(2 * math.pi * i / 14 + 0.07), 9.0 * math.sin(2 * math.pi * i / 14 + 0.07)) for i in range(14)]
# wszystkie otwory jednym wycięciem (jeden cutter z wieloma walcami: mniej artefaktów niż 23 osobne booleany)
bm = bmesh.new()
for dy, dz in holes:
    ret = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=20, radius1=1.0, radius2=1.0, depth=WALL + 0.8)
    bmesh.ops.rotate(bm, verts=ret["verts"], cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "Y"))
    bmesh.ops.translate(bm, vec=((WALL + 0.3 - 0.5) / 2, SPK_CY + dy, SPK_CZ + dz), verts=ret["verts"])
cut(body, tmp("dzwieki", bm))

chk("otwory głośnika", body)
# wkręty boczne: otwór przelotowy w boku i zagłębienie na łeb
for y, z in BOSSES:
    cut(body, xcyl("w_otw_l", y, z, -0.5, WALL + 0.1, 1.35, 24), xcyl("w_lb_l", y, z, -0.5, 1.0, 2.4, 32),
        xcyl("w_otw_p", y, z, L - WALL - 0.1, L + 0.5, 1.35, 24), xcyl("w_lb_p", y, z, L - 1.0, L + 0.5, 2.4, 32))

chk("wkręty boczne", body)

# ================================================================ KLAPKA KORYTA
lid = finish("Klapka_baterii", box_bm(REC_U[0] + 0.25, REC_V[0] + 0.25, 0.0, REC_U[1] - 0.25, REC_V[1] - 0.25, 0.8),
             "Klapka", LID_C)
union(lid, boxuv("wtyk", WIN_U[0] + 0.25, WIN_U[1] - 0.25, WIN_V[0] + 0.25, WIN_V[1] - 0.25, 0.8, Z_POCKET))
vl, vh = WIN_V[0] + 0.25, WIN_V[1] - 0.25
union(lid,
      boxuv("jezyk1", *HK_U, vl, vl + 0.8, Z_POCKET, Z_POCKET + 3.0),
      boxuv("zab1", *HK_U, CH_V[0][0] - 0.4, vl + 0.1, Z_POCKET + 1.4, Z_POCKET + 2.9),
      boxuv("jezyk2", *HK_U, vh - 0.8, vh, Z_POCKET, Z_POCKET + 3.0),
      boxuv("zab2", *HK_U, vh - 0.1, V1 + 0.4, Z_POCKET + 1.4, Z_POCKET + 2.9))

# ================================================================ KAPSLE
caps = []
for k, bx in BTN_X.items():
    lab, top = BTN_LABEL[k], CAP_TOP[k]
    cap = cyl("Kapsel_" + lab, bx, BB_D / 2, CAP_BOT, top, CAP_R, "Kapsle", {"minus": C_DARK, "run": C_ORANGE, "plus": C_DARK}[k], seg=48)
    union(cap, cyl("kolnierz", bx, BB_D / 2, CAP_BOT, CAP_BOT + 0.6, CAP_FLANGE_R, seg=48))
    cut(cap, box("gniazdo", bx - 2.0, BB_D / 2 - 2.0, CAP_BOT - 0.1, bx + 2.0, BB_D / 2 + 2.0, 7.3))
    zt, y0 = top - 0.4, BB_D / 2
    if lab == "-":
        cut(cap, box("m", bx - 2.2, y0 - 0.5, zt, bx + 2.2, y0 + 0.5, top + 0.1))
    elif lab == "+":
        cut(cap, box("p1", bx - 2.2, y0 - 0.5, zt, bx + 2.2, y0 + 0.5, top + 0.1),
            box("p2", bx - 0.5, y0 - 2.2, zt, bx + 0.5, y0 + 2.2, top + 0.1))
    else:
        cut(cap, finish("tri", prism_bm([(bx - 1.6, y0 - 2.1), (bx + 2.3, y0), (bx - 1.6, y0 + 2.1)], zt, top + 0.1), "tmp", T))
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
for bx in (16.0, 32.0):
    cut(bpcb, cyl("o", bx, BB_D / 2, -BT - 0.5, 0.5, 1.1, seg=20))
to_world(bpcb, M_BTN)
for k, bx in BTN_X.items():
    parts = [box("B3F_" + k, bx - 6, BB_D / 2 - 6, 0, bx + 6, BB_D / 2 + 6, 4.3, "Plytka_przyciskow", (0.15, 0.15, 0.17, 1)),
             cyl("B3F_podstawa_" + k, bx, BB_D / 2, 4.3, 5.5, 3.55, "Plytka_przyciskow", (0.3, 0.3, 0.32, 1), seg=32),
             box("B3F_trzpien_" + k, bx - 1.9, BB_D / 2 - 1.9, 5.5, bx + 1.9, BB_D / 2 + 1.9, 7.3, "Plytka_przyciskow", (0.8, 0.8, 0.82, 1)),
             box("B3F_nozki_" + k, bx - 2.5, BB_D / 2 - 2.5, -BT - 1.9, bx + 2.5, BB_D / 2 + 2.5, -BT, "Plytka_przyciskow", (0.6, 0.6, 0.6, 1))]
    for p_ in parts:
        to_world(p_, M_BTN)

cyl("Glosnik_ramka", SPK_CY, SPK_CZ, WALL, WALL + SPK_FR, SPK_D / 2, "Glosnik", (0.12, 0.12, 0.13, 1), seg=96, axis="X")
cyl("Glosnik_stozek", SPK_CY, SPK_CZ, WALL + SPK_FR, WALL + SPK_H, 10.0, "Glosnik", (0.2, 0.2, 0.22, 1), seg=64, axis="X")

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
print(f"Profil: ALPHA {ALPHA} BETA {BETA}  H {H:.1f}  B {B:.1f}  grzbiet {YV - YF:.1f}  s0 {S0}  dh {SOL['dh']}  koszyk y {YB:.1f}..{YB + BAT_W:.1f}")
print(f"Obrys: L {L:.1f}  płytki w X {XB - 24:.1f}..{XB + 24:.1f}  wnęka koszyka {UA:.1f}..{UB:.1f}  YK {YK:.1f}  Y_CUT {Y_CUT:.1f}")
print(f"Głośnik: środek (y {SPK_CY:.1f}, z {SPK_CZ:.1f}), r wolne {SPK_FIT:.1f} (potrzeba {SPK_POCKET / 2:.1f})")
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
cx, cy, cz = L / 2, B / 2, H / 2
n_out = Vector((0, NF[0], NF[1]))
front_c = Vector((XB, *pt_slope(40, 0)))

render("01-przod-iso.png", SHELL, (cx + 150, -170, H + 140), (cx, B * 0.4, H * 0.45), lens=70)
render("02-przod-prostopadle.png", SHELL, front_c + n_out * 400, front_c, up=(0, math.cos(a_), math.sin(a_)), ortho=135)
render("03-gora.png", SHELL, (cx, B * 0.5, 500), (cx, B * 0.5, 0), up=(0, 1, 0), ortho=120)
render("04-bok-lewy-glosnik.png", SHELL, (-300, B / 2, H / 2), (0, B / 2, H / 2), ortho=110)
render("05-spod-klapka.png", SHELL, (cx, B * 0.5, -300), (cx, B * 0.5, 0), up=(0, 1, 0), ortho=120)
render("06-spod-koszyk-otwarty.png", ["Korpus", "Pokrywa", "Kapsle", "Styki", "Baterie"], (cx + 60, B * 0.5 - 80, -230), (cx, B * 0.5, 8), up=(0, 1, 0), lens=70)
render("07-tyl-iso.png", SHELL, (cx - 130, B + 160, H + 130), (cx, B * 0.5, H * 0.4), lens=70)

# pokrywa zdjęta razem z płytkami: przesunięta w górę i do przodu po normalnej frontu
lift = n_out * 70
for g in ("Pokrywa", "Kapsle", "Plytka", "Plytka_przyciskow"):
    for o in GROUPS[g]:
        o.location += lift
render("08-pokrywa-zdjeta.png", ALL, (cx + 170, -150, H + 190), (cx, B * 0.45, H * 0.45), lens=60)
for g in ("Pokrywa", "Kapsle", "Plytka", "Plytka_przyciskow"):
    for o in GROUPS[g]:
        o.location -= lift
# tył pokrywy: widok na płytkę od strony elementów
for g in ("Pokrywa", "Kapsle", "Plytka", "Plytka_przyciskow"):
    for o in GROUPS[g]:
        o.location += lift
render("09-pokrywa-od-tylu.png", ["Pokrywa", "Kapsle", "Plytka", "Plytka_przyciskow"], (cx - 100, B * 0.9 + 130, H * 0.1 - 60), (cx, B * 0.45 + lift.y, H * 0.5 + lift.z), lens=70)
for g in ("Pokrywa", "Kapsle", "Plytka", "Plytka_przyciskow"):
    for o in GROUPS[g]:
        o.location -= lift
sec = make_section("x", XB)
render("10-przekroj-poprzeczny.png", ["Przekroj"], (-400, B / 2, H / 2), (XB, B / 2, H / 2), ortho=120)
drop_section(sec)
render("11-przyciski-zblizenie.png", SHELL, (XB + 50, YK - 80, H + 70), (XB, YK + 8, H - 3), lens=95)

for ob in bpy.data.objects:
    ob.hide_render = False
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "obudowa-klin.blend"))
print("GOTOWE")
