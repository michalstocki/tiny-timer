"""Obudowa minutnika, wariant "klin 3": graniastosłup o podstawie zaokrąglonego trójkąta równobocznego, upakowany ciaśniej.

Uruchomienie (bez okna):
    /Applications/Blender.app/Contents/MacOS/Blender --background --python tools/enclosure/build_wedge3.py

Wejście: docs/pcb-klin3/pcb-layout.json (płytka główna bez wyświetlacza i przycisków). Wyjście: docs/obudowa-klin-3/.

Zmiany względem "klina 2" (docs/obudowa-klin-2):
  1. Moduł wyświetlacza leży sam na froncie, wklejony od wewnątrz na panel (klej na gorąco, 6 listewek ustalających),
     a z płytką główną łączą go cztery żeńskie przewody (kątowe wtyczki na listwie pinów modułu).
  2. Płytka główna (40 x 24 mm) leży na tylnej ściance pokrywy, elementami do wnętrza.
  3. Ogniwa 2 + 1 (piramida: dwa w korytkach na podłodze, trzecie w dolince między nimi) wkłada się od góry po zdjęciu
     pokrywy. Nie ma więc klapki ani otworu w boku.
  4. Pokrywa nie ma wkrętów. Z przodu zakładka (cienka wargą na zewnątrz korpusu), z tyłu elastyczny język
     z zaczepem, odblokowywany palcem (łapka na zewnątrz). Pokrywa zdejmuje się pionowo w górę razem z elektroniką.
Rozmiar trójkąta liczy S = wedge3_solver (najmniejszy bok, w którym mieści się cała zawartość).

Układ współrzędnych: X wzdłuż graniastosłupa, Y w głąb (od frontu do tyłu), Z w górę, podstawa na z = 0.
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
import wedge3_solver as S
from bpyutil import (apply_matrix, bevel, box, box_bm, clip_top, coll, cut, cyl, cyl_bm, discs_hull, extrude_x_bm, finish,
                     intersect, manifold_report, prism_bm, rrect_bm, union, write_stl)

ROOT = Path(__file__).resolve().parents[2]
LAYOUT = ROOT / os.environ.get("TT_LAYOUT", "docs/pcb-klin3/pcb-layout.json")
OUT = ROOT / os.environ.get("TT_OUT", "docs/obudowa-klin-3")
RENDERS = OUT / "renders"

# ---------------------------------------------------------------- parametry
layout = json.loads(LAYOUT.read_text())
BW, BH, BT = (layout["board"][k] for k in ("width", "height", "thickness"))
HOLES = [(h["x"], h["y"], h["diameter"]) for h in layout["mounting_holes"]]
DM = layout["display_module"]
BBL = layout["button_board"]
HEIGHT_OVERRIDE = S.HEIGHT_OVERRIDE
REAR = {k: p for k, p in layout["parts"].items() if p["side"] == "bottom" and p["body"] is not None and
        HEIGHT_OVERRIDE.get(k, p["height_above_board"]) > 0}

THETA, RA, RB = S.THETA, S.RA, S.RB
WALL, PANEL, T_TOP = S.WALL, S.PANEL, S.T_TOP
WE, R_END = 3.0, 3.0                          # grubość boków trójkątnych, zaokrąglenie ich krawędzi
D_B = WALL + S.D_JOINT                        # głębokość strony lutowania płytki głównej pod zewnętrzną powierzchnią tyłu
BZ_CEIL = S.BZ_CEIL
BB_W, BB_D = BBL["width"], BBL["depth"]
BTN_X = {b["label"]: b["x"] for b in BBL["buttons"]}
BTN_SCREW_X = tuple(h["x"] for h in BBL["mounting_holes"])
BTN_LABEL = {"minus": "-", "run": "run", "plus": "+"}
PILL_L, PILL_W = 14.0, 9.5
DISH_AX, DISH_BY, DISH_DEPTH = 11.0, 6.0, 2.0
PILL_DROP, DOME_R = 0.6, 25.0
CAP_BOT, CAP_R, CAP_FLANGE_R, PANEL_HOLE_R = 6.0, 4.8, 5.9, 5.1
MODULE_W, MODULE_T, PLUG_H = S.MODULE_W, S.MODULE_T, S.PLUG_H
MOD_L, MOD_PIN_END = DM["outline"][0], DM["pin_to_end"]
GLASS_W, GLASS_H = DM["glass"]
LIP_B, LIP_F = S.LIP_B, 6.0                   # długość języka zatrzasku (tył) i zakładki (front)
T_LIP_F, T_LIP_B = 1.0, 1.2                   # grubość wargi frontu i języka tyłu
HOOK = 0.9                                    # wysokość zaczepu

# ogniwa AAA 2 + 1
CELL_D, CELL_L = 10.5, 44.5
CAV_L = 51.0
Z_POCKET = S.Z_POCKET
B_RCH, B_PITCH, B_ZL, B_ZU = S.B_RCH, S.B_PITCH, S.B_ZL, S.B_ZU

# głośnik Ø26,5 x 9 (ramka 4) przy lewym boku
SPK_D, SPK_H, SPK_FR, SPK_POCKET = 26.5, 9.0, 4.0, 27.0
SPK_ZONE, RING_L = 11.2, 5.5

# układ w X: [lewy bok][głośnik][przegroda 1,2][ogniwa 51][prawy bok]
UA = WE + SPK_ZONE + 1.2
UB = UA + CAV_L
L = UB + WE
XC = L / 2
CX0, CX1 = WE + 0.25, L - WE - 0.25           # zakres X pokrywy między bokami

# ---------------------------------------------------------------- przekrój (solver)
S.GRID = 0.5
SOL = S.solve(str(LAYOUT), sides=[x * 0.5 for x in range(120, 170)])
if SOL is None:
    raise SystemExit("brak rozwiązania przekroju")
SIDE_LEN, B_YC, SM, FLIP, SB_FAR = SOL["side"], SOL["yc"], SOL["sm"], SOL["flip"], SOL["sb_far"]
BCELLS = S.tubes(B_YC)
PR = S.profile(SIDE_LEN)
B, H, Z_TOP, Z_CEIL = SIDE_LEN, PR["H"], PR["z_top"], PR["z_ceil"]
OUTER, INNER, INNER_FULL = PR["outer"], PR["inner"], PR["inner_full"]
YC = B / 2
ZB = Z_CEIL - BZ_CEIL
D_BTN = T_TOP + BZ_CEIL
BZ_TOP, BZ_PILL = D_BTN, D_BTN - PILL_DROP

th = math.radians(THETA)
sin_t, cos_t = math.sin(th), math.cos(th)
NF, NB, UBK = (-sin_t, cos_t), (sin_t, cos_t), (cos_t, -sin_t)
S_TANG_A = RA / math.tan(math.radians((180 - 2 * THETA) / 2))
S_F = SM - MODULE_W / 2 - 3.5                 # dolna krawędź pokrywy po froncie (od krawędzi podstawy)
S_B = SB_FAR + 2.0                            # dolna krawędź pokrywy po tyle (od ostrego wierzchołka)
X_R = UB - 2.0                                # prawy koniec płytki głównej (bx = 0 bez obrotu)


def pt_slope(s, d):
    return (s * cos_t + d * sin_t, s * sin_t - d * cos_t)


def pt_back(s, d):
    return (YC + s * UBK[0] - d * NB[0], H + s * UBK[1] - d * NB[1])


def incircle(poly):
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
M_DISP = Matrix(((1, 0, 0, XC), (0, cos_t, -sin_t, pt_slope(SM, PANEL)[0]), (0, sin_t, cos_t, pt_slope(SM, PANEL)[1]), (0, 0, 0, 1)))
_o = pt_back(SB_FAR, D_B)
M_BACK = Matrix(((-1, 0, 0, X_R), (0, -UBK[0], NB[0], _o[0]), (0, -UBK[1], NB[1], _o[1]), (0, 0, 0, 1)))
M_FLIP = Matrix.Translation((BW / 2, BH / 2, 0)) @ Matrix.Rotation(math.pi, 4, "Z") @ Matrix.Translation((-BW / 2, -BH / 2, 0))
M_BOARD = M_BACK @ (M_FLIP if FLIP else Matrix.Identity(4))
M_BTN = Matrix.Translation((XC - BB_W / 2, YC - BB_D / 2, ZB))
R_WIN = (GLASS_H + 0.6) / 2 - 0.005


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


def xcyl(name, y, z, x0, x1, r, seg=32):
    return cyl(name, y, z, x0, x1, r, seg=seg, axis="X")


def boxuv(name, u0, u1, v0, v1, z0, z1, group="tmp", color=T):
    return box(name, u0, v0, z0, u1, v1, z1, group, color)


def prism_x(name, pts, x0, x1):
    return tmp(name, extrude_x_bm(pts, x0, x1))


def outer_solid(x0=0.0, x1=L):
    return tmp("obrys", extrude_x_bm(OUTER, x0, x1))


def zone_poly(s_f, s_b):
    """Pas pokrywy: od s_f po froncie (od krawędzi podstawy), przez wierzchołek, do s_b po tyle (od ostrego wierzchołka);
    obejmuje też wnętrze nad cięciwą łączącą obie krawędzie."""
    fy, fz = s_f * cos_t, s_f * sin_t
    a_in, a_out = (fy - 4.4 * NF[0], fz - 4.4 * NF[1]), (fy + 8 * NF[0], fz + 8 * NF[1])
    by_, bz_ = YC + s_b * UBK[0], H + s_b * UBK[1]
    b_in, b_out = (by_ - 4.4 * NB[0], bz_ - 4.4 * NB[1]), (by_ + 8 * NB[0], bz_ + 8 * NB[1])
    p1 = (YC + 10 * NF[0], H + 10 * NF[1] + 10)
    p2 = (YC + 10 * NB[0], H + 10 * NB[1] + 10)
    return [a_in, a_out, p1, p2, b_out, b_in]


# ---------------------------------------------------------------- korpus i pokrywa: powłoka
# shell0: pusta powłoka (źródło pokrywy), shell1: powłoka z uchwytami ogniw (źródło korpusu)
def make_shell(with_holders):
    sh = outer_solid()
    bevel(sh, R_END, segments=6)
    cav = tmp("wnetrze", extrude_x_bm(INNER, WE, L - WE))
    if with_holders:
        # przegroda za głośnikiem (cały przekrój wnętrza) i podłoga z dwoma korytkami; brzegi korytek 1,5 mm poniżej osi ogniw,
        # żeby ogniwo dało się wyjąć w górę i na bok bez zahaczenia o brzeg
        cut(cav, prism_x("przegroda", OUTER, UA - 1.2, UA))
        blk = boxuv("podloga", UA - 0.6, UB + 0.5, B_YC - B_PITCH / 2 - B_RCH - 2.5, B_YC + B_PITCH / 2 + B_RCH + 2.5, 0.0, B_ZL - 1.5)
        cut(cav, blk)
    cut(sh, cav)
    return sh


shell0 = make_shell(False)
shell1 = make_shell(True)
chk("powłoka", shell1)

# podział: pokrywa = pas powłoki w x od CX0 do CX1; korpus = reszta (szczelina 0,25 mm)
cover = bpy.data.objects.new("Pokrywa", shell0.data.copy())
coll("tmp").objects.link(cover)
regroup(cover, "Pokrywa", LID_C)
intersect(cover, prism_x("strefa_pokrywy", zone_poly(S_F, S_B), CX0, CX1))
body = regroup(shell1, "Korpus", C_BODY)
body.name = "Korpus"
cut(body, prism_x("strefa_korpusu", zone_poly(S_F - 0.25, S_B + 0.25), WE, L - WE))
bpy.data.objects.remove(shell0, do_unlink=True)
chk("podział", body)

# ================================================================ ZAKŁADKA FRONTU (cienka warga pokrywy na zewnątrz korpusu)
# materiał wargi bierzemy z pustej powłoki (zewnętrzna warstwa grubości T_LIP_F), nie z korpusu z uchwytami
shell_ref = make_shell(False)
lip_poly = [pt_slope(S_F - LIP_F, -1.5), pt_slope(S_F, -1.5), pt_slope(S_F, T_LIP_F), pt_slope(S_F - LIP_F, T_LIP_F)]
lip_f = bpy.data.objects.new("warga_frontu", shell_ref.data.copy())
coll("tmp").objects.link(lip_f)
intersect(lip_f, prism_x("wp_f", lip_poly, CX0, CX1))
union(cover, lip_f)
chk("pokrywa: warga frontu", cover)
# wpust w korpusie (warga + 0,25 luzu) i pogrubienie ścianki od wnętrza
reb_poly = [pt_slope(S_F - LIP_F - 0.25, -1.5), pt_slope(S_F - 0.1, -1.5), pt_slope(S_F - 0.1, T_LIP_F + 0.25),
            pt_slope(S_F - LIP_F - 0.25, T_LIP_F + 0.25)]
cut(body, prism_x("wpust_f", reb_poly, WE, L - WE))
rib_poly = [pt_slope(S_F - LIP_F - 1.0, PANEL - 0.2), pt_slope(S_F - 0.15, PANEL - 0.2), pt_slope(S_F - 0.15, PANEL + 1.0),
            pt_slope(S_F - LIP_F - 1.0, PANEL + 1.0)]
union(body, prism_x("zebro_f", rib_poly, WE - 0.2, L - WE + 0.2))
chk("korpus: wpust frontu", body)

# ================================================================ ZATRZASK TYŁU (język pokrywy z zaczepem, łapka na palec)
T_X0, T_X1 = XC - 7.0, XC + 7.0
s_end = S_B + LIP_B
tong_poly = [pt_back(S_B, -1.5), pt_back(s_end, -1.5), pt_back(s_end, T_LIP_B), pt_back(S_B, T_LIP_B)]
tongue = bpy.data.objects.new("jezyk", shell_ref.data.copy())
coll("tmp").objects.link(tongue)
intersect(tongue, prism_x("jp", tong_poly, T_X0, T_X1))
hook_poly = [pt_back(s_end - 2.8, T_LIP_B - 0.1), pt_back(s_end - 2.8, T_LIP_B + HOOK), pt_back(s_end - 1.6, T_LIP_B + HOOK),
             pt_back(s_end - 0.4, T_LIP_B - 0.1)]
tab_poly = [pt_back(s_end - 2.2, -1.6), pt_back(s_end, -1.6), pt_back(s_end, 0.3), pt_back(s_end - 2.2, 0.3)]
NOHOOK = bool(os.environ.get("TT_NOHOOK"))          # kontrola zdejmowania: bez zaczepu i rowka (zaczep ma ocierać się o rowek)
union(cover, tongue, prism_x("lapka", tab_poly, XC - 5.0, XC + 5.0))
if not NOHOOK:
    union(cover, prism_x("zaczep", hook_poly, T_X0 + 1.0, T_X1 - 1.0))
chk("pokrywa: zatrzask", cover)
# korpus: wpust na język, żebro od wnętrza, rowek na zaczep
reb_b = [pt_back(S_B + 0.1, -1.5), pt_back(s_end + 0.5, -1.5), pt_back(s_end + 0.5, T_LIP_B + 0.25), pt_back(S_B + 0.1, T_LIP_B + 0.25)]
cut(body, prism_x("wpust_b", reb_b, T_X0 - 0.5, T_X1 + 0.5))
rib_b = [pt_back(S_B + 0.1, WALL - 0.2), pt_back(s_end + 1.0, WALL - 0.2), pt_back(s_end + 1.0, WALL + 1.4), pt_back(S_B + 0.1, WALL + 1.4)]
union(body, prism_x("zebro_b", rib_b, T_X0 - 1.5, T_X1 + 1.5))
groove = [pt_back(s_end - 2.95, T_LIP_B + 0.2), pt_back(s_end - 2.95, T_LIP_B + HOOK + 0.25), pt_back(s_end + 0.1, T_LIP_B + HOOK + 0.25),
          pt_back(s_end + 0.1, T_LIP_B + 0.2)]
if not NOHOOK:
    cut(body, prism_x("rowek", groove, T_X0 - 0.1 + 0.9, T_X1 + 0.1 - 0.9))
chk("korpus: zatrzask", body)
bpy.data.objects.remove(shell_ref, do_unlink=True)

# ================================================================ POKRYWA: okno, listewki modułu, słupki, przyciski
cut(cover, to_world(tmp("okno", rrect_bm(-GLASS_W / 2 - 0.3, -GLASS_H / 2 - 0.3, -0.5, GLASS_W / 2 + 0.3, GLASS_H / 2 + 0.3,
                                          PANEL + 0.6, R_WIN)), M_DISP))
ribs = []
for sx in (-MOD_L / 2 + 5.0, MOD_L / 2 - 5.0):
    for sy in (-1, 1):
        y0, y1 = (MODULE_W / 2 + 0.3, MODULE_W / 2 + 1.3) if sy > 0 else (-MODULE_W / 2 - 1.3, -MODULE_W / 2 - 0.3)
        ribs.append(boxuv("listwa", sx - 3.0, sx + 3.0, y0, y1, -3.0, 0.3))
for sx in (-1, 1):
    x0, x1 = (MOD_L / 2 + 0.3, MOD_L / 2 + 1.3) if sx > 0 else (-MOD_L / 2 - 1.3, -MOD_L / 2 - 0.3)
    ribs.append(boxuv("listwa", x0, x1, -3.0, 3.0, -3.0, 0.3))
for rb_ in ribs:
    union(cover, to_world(rb_, M_DISP))
chk("pokrywa: moduł", cover)

# słupki płytki głównej: od ścianki do strony lutowania (bz 0 .. D_JOINT), wkręt M2,5 od strony elementów
for hx, hy, _ in HOLES:
    union(cover, to_world(cyl("slupek", hx, hy, 0.0, S.D_JOINT + 0.4, 2.9, seg=32), M_BOARD))
for hx, hy, _ in HOLES:
    cut(cover, to_world(cyl("pilot", hx, hy, -0.1, S.D_JOINT + WALL - 0.5, 1.05, seg=24), M_BOARD))
chk("pokrywa: słupki płytki", cover)

# otwory pod kapsle, obniżenie pod tabletkę
for k in ("minus", "plus"):
    cut(cover, to_world(cyl("otw", BTN_X[k], BB_D / 2, BZ_CEIL - 0.5, BZ_TOP + 4.0, PANEL_HOLE_R), M_BTN))
cut(cover, to_world(tmp("otw_run", rrect_bm(BTN_X["run"] - PILL_L / 2 - 0.3, BB_D / 2 - PILL_W / 2 - 0.3, BZ_CEIL - 0.5,
                                            BTN_X["run"] + PILL_L / 2 + 0.3, BB_D / 2 + PILL_W / 2 + 0.3, BZ_TOP + 4.0,
                                            PILL_W / 2 + 0.3)), M_BTN))
RS = (DISH_BY ** 2 + DISH_DEPTH ** 2) / (2 * DISH_DEPTH)
bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=96, v_segments=48, radius=RS)
bmesh.ops.scale(bm, vec=(DISH_AX / DISH_BY, 1.0, 1.0), verts=bm.verts)
bmesh.ops.translate(bm, vec=(XC - BB_W / 2 + BTN_X["run"], YC, Z_TOP - DISH_DEPTH + RS), verts=bm.verts)
cut(cover, tmp("zaglebienie", bm))
chk("pokrywa: przyciski", cover)
for bx in BTN_SCREW_X:
    union(cover, to_world(cyl("slupek_b", bx, BB_D / 2, 0.0, BZ_CEIL + 0.6, 1.8, seg=24), M_BTN))
    cut(cover, to_world(cyl("pilot_b", bx, BB_D / 2, -0.1, 5.5, 0.85, seg=20), M_BTN))
chk("pokrywa: słupki przycisków", cover)

# ================================================================ KORPUS: korytka, szczelina na płytkę łączącą, głośnik
for cy_, cz_ in BCELLS[:2]:
    cut(body, xcyl("korytko", cy_, cz_, UA - 0.3, UB + 0.3, B_RCH, 48))
chk("korytka", body)
# szczelina w żeberku między korytkami pod płytkę łączącą ogniwa 1 i 2 (prawy koniec)
cut(body, prism_x("sz_wysoki", discs_hull([BCELLS[0], BCELLS[1]], 4.8, 24), UB - 0.7, UB + 0.1))
chk("szczelina styków", body)

ring = xcyl("pierscien", SPK_CY, SPK_CZ, WE - 0.2, WE + RING_L, SPK_POCKET / 2 + 1.9, 96)
cut(ring, xcyl("pierscien_w", SPK_CY, SPK_CZ, WE - 0.5, WE + RING_L + 0.5, SPK_POCKET / 2, 96))
intersect(ring, outer_solid())
union(body, ring)
chk("pierścień", body)
holes = [(0.0, 0.0)]
holes += [(4.5 * math.cos(2 * math.pi * i / 8 + 0.2), 4.5 * math.sin(2 * math.pi * i / 8 + 0.2)) for i in range(8)]
holes += [(9.0 * math.cos(2 * math.pi * i / 14 + 0.07), 9.0 * math.sin(2 * math.pi * i / 14 + 0.07)) for i in range(14)]
bm = bmesh.new()
for dy, dz in holes:
    ret = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=20, radius1=1.0, radius2=1.0, depth=WE + 0.8)
    bmesh.ops.rotate(bm, verts=ret["verts"], cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "Y"))
    bmesh.ops.translate(bm, vec=((WE + 0.3 - 0.5) / 2, SPK_CY + dy, SPK_CZ + dz), verts=ret["verts"])
cut(body, tmp("dzwieki", bm))
chk("otwory głośnika", body)

# ================================================================ KAPSLE (w układzie płytki przycisków)
caps = []
SURF_R = RA - 0.15
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
        intersect(cap, tmp("kopula", dome))
        union(cap, finish("kolnierz", rrect_bm(bx - PILL_L / 2 - 0.8, y0 - PILL_W / 2 - 0.8, CAP_BOT,
                                               bx + PILL_L / 2 + 0.8, y0 + PILL_W / 2 + 0.8, CAP_BOT + 0.6,
                                               PILL_W / 2 + 0.8), "tmp", T))
        zt = top - 0.4
        cut(cap, finish("tri", prism_bm([(bx - 1.6, y0 - 2.1), (bx + 2.3, y0), (bx - 1.6, y0 + 2.1)], zt, top + 0.1), "tmp", T))
    else:
        cap = cyl("Kapsel_" + lab, bx, y0, CAP_BOT, BZ_TOP + 2.0, CAP_R, "Kapsle", color, seg=48)
        surf = cyl("powierzchnia", y0, BZ_TOP - RA, bx - 8, bx + 8, SURF_R, seg=96, axis="X")
        intersect(cap, surf)
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
swap = [False, True, False]
for i, (cy_, cz_) in enumerate(BCELLS):
    if not swap[i]:
        c0 = UA + 6.0
        c1 = c0 + CELL_L
        body_u, nub_u = (c0, c1 - 0.8), (c1 - 0.8, c1)
    else:
        c0 = UA + 0.5
        c1 = c0 + CELL_L
        body_u, nub_u = (c0 + 0.8, c1), (c0, c0 + 0.8)
    finish(f"AAA_{i + 1}", cyl_bm(cy_, cz_, body_u[0], body_u[1], CELL_D / 2, axis="X"), "Baterie", C_CELL)
    finish(f"AAA_{i + 1}_plus", cyl_bm(cy_, cz_, nub_u[0], nub_u[1], 2.0, axis="X"), "Baterie", C_GOLD)


def plate(name, u_end, ca, cb=None):
    cb = cb or ca
    pts = discs_hull([ca, cb], 4.5, 24)
    ua, ub = (u_end, u_end + 0.5) if u_end == UA else (u_end - 0.5, u_end)
    return finish(name, extrude_x_bm(pts, ua, ub), "Styki", C_NICKEL)


def spring(name, c, low_end):
    if low_end:
        return finish(name, cyl_bm(c[0], c[1], UA + 0.5, UA + 6.0, SPR_R, r2=SPR_R * 0.55, axis="X", seg=32), "Styki", C_NICKEL)
    return finish(name, cyl_bm(c[0], c[1], UA + 0.5 + CELL_L, UB - 0.5, SPR_R * 0.55, r2=SPR_R, axis="X", seg=32), "Styki", C_NICKEL)


c1_, c2_, c3_ = BCELLS
spring("sprezyna_1", c1_, True)
plate("plytka_1_neg", UA, c1_)
spring("sprezyna_3", c3_, True)
plate("plytka_lacznik_niski", UA, c2_, c3_)
spring("sprezyna_2", c2_, False)
plate("plytka_lacznik_wysoki", UB, c1_, c2_)
plate("plytka_3_pos", UB, c3_)

# ================================================================ PŁYTKI, MODUŁ, GŁOŚNIK (podgląd, nie do wydruku)
C_PCB, C_BLACK, C_PART = (0.10, 0.42, 0.22, 1), (0.04, 0.04, 0.05, 1), (0.55, 0.40, 0.25, 1)
pcb = finish("PCB", rrect_bm(0, 0, -BT, BW, BH, 0, 3.0), "Plytka", C_PCB)
for hx, hy, hd in HOLES:
    cut(pcb, cyl("o", hx, hy, -BT - 0.5, 0.5, hd / 2, seg=24))
to_world(pcb, M_BOARD)
for name, p in REAR.items():
    bx0, by0, bx1, by1 = p["body"]
    h = HEIGHT_OVERRIDE.get(name, p["height_above_board"])
    to_world(box("el_" + name, bx0, by0, -BT - h, bx1, by1, -BT, "Plytka", C_PART), M_BOARD)

# moduł wyświetlacza (szkło do panelu) i wtyczki
mod = box("OLED_modul", -MOD_L / 2, -MODULE_W / 2, -MODULE_T, MOD_L / 2, MODULE_W / 2, -MODULE_T + 1.2, "Wyswietlacz", (0.08, 0.20, 0.42, 1))
to_world(mod, M_DISP)
to_world(box("OLED_szklo", -GLASS_W / 2, -GLASS_H / 2, -MODULE_T + 1.2, GLASS_W / 2, GLASS_H / 2, 0.0, "Wyswietlacz", (0.04, 0.05, 0.10, 1)), M_DISP)
pin_x = -MOD_L / 2 + MOD_PIN_END
to_world(box("listwa_pinow", pin_x - 1.3, -5.2, -MODULE_T - 2.5, pin_x + 1.3, 5.2, -MODULE_T, "Wyswietlacz", (0.12, 0.12, 0.13, 1)), M_DISP)
for k in range(4):
    yy = (k - 1.5) * 2.54
    to_world(box(f"wtyczka_{k + 1}", pin_x - 1.2, yy - 1.15, -MODULE_T - PLUG_H, pin_x + 1.2, yy + 1.15, -MODULE_T - 2.5, "Wyswietlacz",
                 (0.15, 0.15, 0.17, 1)), M_DISP)

# płytka przycisków
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
printable = {"korpus": [body], "pokrywa": [cover], "kapsle": caps}
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
print(f"Trójkąt: bok {B:.1f}  wysokość ostrego wierzchołka {H:.1f}, szczyt po zaokrągleniu {Z_TOP:.1f}")
print(f"Rozwiązanie: oś zestawu ogniw y {B_YC:.2f}, środek modułu po froncie s {SM}, płytka dalszy brzeg s {SB_FAR}, obrót {FLIP}")
print(f"Obrys: L {L:.1f}  pokrywa x {CX0:.2f}..{CX1:.2f}  S_F {S_F:.1f}  S_B {S_B:.1f}  płytka x {X_R - BW:.1f}..{X_R:.1f}")
print(f"Głośnik: środek (y {SPK_CY:.1f}, z {SPK_CZ:.1f}), r wolne {SPK_FIT:.1f} (potrzeba {SPK_POCKET / 2 + 1.9:.1f} z pierścieniem)")
scene["ctl_y"], scene["ctl_z"] = B / 2, H - 25.0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "obudowa-klin-3.blend"))
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


ALL = ["Korpus", "Pokrywa", "Kapsle", "Styki", "Baterie", "Plytka", "Plytka_przyciskow", "Wyswietlacz", "Glosnik"]
SHELL = ["Korpus", "Pokrywa", "Kapsle"]
CARRIED = ("Pokrywa", "Kapsle", "Plytka", "Plytka_przyciskow", "Wyswietlacz")
cx = L / 2
n_front = Vector((0, NF[0], NF[1]))
front_c = Vector((XC, *pt_slope(SM, 0)))
back_c = Vector((XC, *pt_back(S_B + 5, 0)))
n_back = Vector((0, NB[0], NB[1]))

render("01-przod-iso.png", SHELL, (cx + 200, -150, H * 0.8 + 120), (cx, B * 0.5, H * 0.4), lens=70)
render("02-przod-prostopadle.png", SHELL, front_c + n_front * 400, front_c, up=(0, cos_t, sin_t), ortho=110)
render("03-gora.png", SHELL, (cx, YC, 500), (cx, YC, 0), up=(0, 1, 0), ortho=110)
render("04-bok-lewy-glosnik.png", SHELL, (-300, B / 2, H / 2), (0, B / 2, H / 2), ortho=100)
render("05-bok-prawy.png", SHELL, (L + 300, B / 2, H / 2), (L, B / 2, H / 2), ortho=100)
render("06-spod.png", SHELL, (cx, B * 0.5, -300), (cx, B * 0.5, 0), up=(0, 1, 0), ortho=110)
render("07-tyl-iso.png", SHELL, (cx - 150, B + 180, H * 0.8 + 100), (cx, B * 0.5, H * 0.4), lens=70)
render("08-tyl-zatrzask.png", SHELL, back_c + n_back * 120 + Vector((60, 0, 0)), back_c, lens=90)

lift = Vector((0, 0, 70))
for g in CARRIED:
    for o in GROUPS[g]:
        o.location += lift
render("09-pokrywa-zdjeta.png", ALL, (cx + 250, -190, H * 0.8 + 200), (cx, B * 0.45, H * 0.8), lens=50)
render("10-ogniwa-od-gory.png", ["Korpus", "Styki", "Baterie", "Glosnik"], (cx + 70, B + 70, H * 1.0), (cx, B_YC + 6, 8), lens=50)
render("11-pokrywa-od-srodka.png", ["Pokrywa", "Kapsle", "Plytka", "Plytka_przyciskow", "Wyswietlacz"],
       (cx + 90, B * 0.8, lift.z + 4), (cx - 5, YC - 12, lift.z + H * 0.6), lens=40)
render("12-pokrywa-od-tylu-wewn.png", ["Pokrywa", "Kapsle", "Plytka", "Plytka_przyciskow", "Wyswietlacz"],
       (cx - 50, B + 60, lift.z + 5), (cx + 8, B * 0.55, lift.z + H * 0.45), lens=45)
for g in CARRIED:
    for o in GROUPS[g]:
        o.location -= lift
sec = make_section("x", 40.0)
render("13-przekroj-poprzeczny.png", ["Przekroj"], (-400, B / 2, H / 2), (40.0, B / 2, H / 2), ortho=100)
drop_section(sec)
sec = make_section("x", XC - 17.5)
render("14-przekroj-wtyczki.png", ["Przekroj"], (-400, B / 2, H / 2), (XC - 17.5, B / 2, H / 2), ortho=100)
drop_section(sec)
tc = pt_back(S_B + LIP_B / 2, 0)
sec = make_section("x", XC)
render("15-przekroj-zatrzask.png", ["Przekroj"], (-400, tc[0], tc[1]), (XC, tc[0], tc[1]), ortho=30)
lc = pt_slope(S_F, 0)
render("18-przekroj-zakladka-frontu.png", ["Przekroj"], (-400, lc[0], lc[1]), (XC, lc[0], lc[1]), ortho=30)
drop_section(sec)
sec = make_section("x", XC + BTN_X["plus"] - BTN_X["run"])
render("16-przekroj-przycisk-plus.png", ["Przekroj"], (-400, YC, Z_TOP - 20), (XC, YC, Z_TOP - 20), ortho=60)
drop_section(sec)
render("17-przyciski-zblizenie.png", SHELL, (XC + 55, YC - 70, Z_TOP + 60), (XC, YC, Z_TOP - 2), lens=95)

for ob in bpy.data.objects:
    ob.hide_render = False
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "obudowa-klin-3.blend"))
print("GOTOWE")
