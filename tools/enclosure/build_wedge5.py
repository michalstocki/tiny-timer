"""Obudowa minutnika, wariant "klin 5": graniastosłup o podstawie zaokrąglonego trójkąta równobocznego.

Uruchomienie (bez okna):
    /Applications/Blender.app/Contents/MacOS/Blender --background --python tools/enclosure/build_wedge5.py

Wejście: docs/pcb-klin3/pcb-layout.json. Wyjście: docs/obudowa-klin-5/. Przekrój liczy wedge5_solver.

Zmiany względem klina 4 (docs/obudowa-klin-4):
  1. Styki zmierzone na prawdziwych częściach: płytki pojedyncze 9,9 x 9,1 (blaszka 2 x 7 na środku górnej krawędzi),
     podwójne 20,1 x 9,1 (rozstaw styków 10,3; jedna z blaszką 3 x 6 na środku), przycisk Ø6 x 1,5, sprężyna Ø6, 8 mm
     swobodna, 3 mm najbardziej ściśnięta, 1 mm luzu wokół sprężyny. Zadziory na bocznych krawędziach (1 mm, do 1,3 mm
     z grubością blachy) trzymają płytkę w szczelinie na wcisk.
  2. Ogniwa co 10,8 mm, oś 7,4 mm nad stołem; wkładane od spodu przez klapkę w dnie. Klapka: przylga dookoła, język
     przy lewym końcu w kieszeni pod ścianką gniazd, przy prawym ucho z wkrętem M2 x 6 (łeb stożkowy) w tulei korpusu.

Zmiany klina 4 względem klina 3.1 (docs/obudowa-klin-3.1):
  1. Szew tyłu leży na narożniku tyłu z podstawą, lustrzanie do frontu. Pokrywa to front, wierzchołek i cały tył, korpus
     to płytka taca. Płytka główna schodzi niżej po tylnej ściance, więc trójkąt jest mniejszy.
  2. Zatrzaski: cztery nogi z zaczepem (dwie przy froncie, dwie przy tyle), w strefach na końcach poza ogniwami. Zaczep
     chwyta od dołu poziomą półkę w korpusie, więc pokrywy nie da się podnieść ani przesunąć, dopóki noga nie zostanie
     odgięta. Zwalnianie: szpilką przez otwór w spodzie (pchnięcie w skośną dolną ściankę zaczepu odgina nogę i unosi róg).
  3. Ogniwa w rzędzie na podłodze, gniazda styków Keystone 5204 / 5226 (pojedyncze z blaszką) i 5213 / 5214 (podwójne)
     według katalogu M65: płytki 9,2 x 10,4 i 21,0 x 11,0 mm, grubość 0,51, rozstaw styków podwójnych 11,5 mm,
     odległość płytek dla AAA 49,5 mm. Płytki wsuwa się od góry w szczeliny ścianek gniazd.
  4. Wyświetlacz bez wtyczek: przewody wlutowane w moduł i położone płasko, okno i przyciski na środku długości.
  5. Kapsle przycisków z gniazdem na wystający trzpień B3F-4055 (3,8 x 3,8 mm) i czterema żebrami docisku (3,5 mm
     między żebrami, jak w nasadkach Omron B32), bez luzu.

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
import wedge5_solver as W
from bpyutil import (apply_matrix, bevel, box, clip_top, coll, cut, cyl, cyl_bm, extrude_x_bm, finish, intersect,
                     manifold_report, rrect_bm, union, write_stl)

ROOT = Path(__file__).resolve().parents[2]
LAYOUT = ROOT / os.environ.get("TT_LAYOUT", "docs/pcb-klin3/pcb-layout.json")
OUT = ROOT / os.environ.get("TT_OUT", "docs/obudowa-klin-5")
RENDERS = OUT / "renders"
NOHOOK = bool(os.environ.get("TT_NOHOOK"))     # kontrola zdejmowania: bez zaczepów na nogach zatrzasków

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
BTN_SCREW = tuple((h["x"], h["y"]) for h in BBL["mounting_holes"])
BTN_LABEL = {"minus": "-", "run": "run", "plus": "+"}
PILL_L, PILL_W = 14.0, 9.5
DISH_AX, DISH_BY, DISH_DEPTH = 11.0, 6.0, 2.0
PILL_DROP, DOME_R = 0.6, 25.0
CAP_R, CAP_FLANGE_R, PANEL_HOLE_R = 4.8, 5.9, 5.1
# B3F-4055 (karta Omron): korpus 12 x 12 x 4,3, okrągła część Ø7,1 do 5,5, trzpień 3,8 x 3,8 do 7,3 nad płytką, skok 0,25
SW_BODY, SW_COLLAR, SW_TOP, PLUNGER = 4.3, 5.5, 7.3, 3.8
CAP_BOT = SW_COLLAR + 0.3                     # spód kapsla nad okrągłą częścią (więcej niż skok)
SOCK, SOCK_RIB_W = PLUNGER + 0.2, 0.6         # gniazdo z luzem 0,1 na stronę i cztery żebra docisku
SOCK_GRIP = 3.5                               # odstęp żeber (nasadki Omron B32 do 12 x 12: 3,5 mm na trzpieniu 3,8)
MODULE_W, MODULE_T = S.MODULE_W, S.MODULE_T
MOD_L, MOD_PIN_END = DM["outline"][0], DM["pin_to_end"]
GLASS_W, GLASS_H = DM["glass"]
WIRE_H = W.WIRE_H

# ogniwa AAA w rzędzie i styki zmierzone na prawdziwych częściach (19.11.2026)
CELL_D, CELL_L, NUB_R, NUB_H = 10.5, 44.5, 1.9, 0.8
PL_T = 0.4                                    # grubość blachy: NIE ZMIERZONA (przyjęta); szczelina 0,9 mieści 0,3...0,5
SGL_W, SGL_H = 9.9, 9.1                       # płytka pojedyncza, styk na środku
SGL_TAB_W, SGL_TAB_L = 2.0, 7.0               # blaszka lutownicza pojedynczej: na środku górnej krawędzi
DUAL_W, DUAL_H = 20.1, 9.1                    # płytka podwójna, styki na środku wysokości
DUAL_TAB_W, DUAL_TAB_L = 3.0, 6.0             # blaszka płytki podwójnej (tylko jedna z dwóch ją ma): na środku
CONTACT_PITCH = W.CONTACT_PITCH               # 10,3: rozstaw styków płytki podwójnej
BTN_H, BTN_R = 1.5 - PL_T, 3.0                # przycisk (+) Ø6, 1,5 mm razem z blachą
SPR_R, SPR_MARGIN = 3.0, 1.0                  # sprężyna (-) Ø6 (z proporcji na zdjęciu), 1 mm wolnego miejsca dookoła
SPR_FREE, SPR_MIN = 8.0, 3.0                  # sprężyna swobodna i najbardziej ściśnięta
SPR_AT_MAX = 4.0                              # sprężyna przy najdłuższym ogniwie (44,5): 1 mm zapasu do pełnego ściśnięcia
L_CONT = CELL_L + BTN_H + SPR_AT_MAX          # odległość płytek (od strony ogniw)
CW_BACK, CW_SLOT, CW_LIP = 1.0, 0.9, 0.9      # ścianka gniazda: tył, szczelina (blacha + zadziory 1,0...1,3 na wcisk), wargi
CW_GRIP = 0.8                                 # wargi zachodzą na boczne brzegi płytki (sprężyna Ø6 + 1 mm mieści się w oknie)
CW_CLR = 0.25                                 # luz płytki w szczelinie (na boki)
Z_AX = W.Z_AXIS
B_RCH = S.B_RCH

# głośnik Ø26,5 x 9 (ramka 4) przy lewym boku
SPK_D, SPK_H, SPK_FR, SPK_POCKET = 26.5, 9.0, 4.0, 27.0
SPK_ZONE, RING_L = 11.2, 5.5

# układ w X: [lewy bok][głośnik][ścianka gniazd][ogniwa 49,5 między płytkami][ścianka gniazd][strefa zatrzasków][prawy bok]
LATCH_ZONE, LATCH_W = 4.5, 3.5
UA = WE + SPK_ZONE + CW_BACK + PL_T           # płaszczyzna styku lewych płytek (od strony ogniw)
UB = UA + L_CONT
L = UB + PL_T + CW_BACK + LATCH_ZONE + WE
XC = L / 2                                    # okno, przyciski i płytka główna na środku długości
LATCH_X = (WE + LATCH_ZONE / 2, L - WE - LATCH_ZONE / 2)
CX0, CX1 = WE + 0.25, L - WE - 0.25           # zakres X pokrywy między bokami

# ---------------------------------------------------------------- przekrój (solver)
S.GRID = 0.5
SOL = W.solve(str(LAYOUT))
if SOL is None:
    raise SystemExit("brak rozwiązania przekroju")
SIDE_LEN, B_YC, SM, FLIP, SB_FAR = SOL["side"], SOL["yc"], SOL["sm"], SOL["flip"], SOL["sb_far"]
CELLS = W.tubes(B_YC)                         # A (przy froncie), B, C (przy tyle)
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
X_R = XC + BW / 2                             # płytka główna na środku długości (bx = 0 przy X_R)


def pt_slope(s, d):
    return (s * cos_t + d * sin_t, s * sin_t - d * cos_t)


def pt_back(s, d):
    return (YC + s * UBK[0] - d * NB[0], H + s * UBK[1] - d * NB[1])


def mir(pts):
    """Odbicie punktów (y, z) względem środka głębokości: narożnik frontu -> narożnik tyłu."""
    return [(B - y, z) for y, z in pts]


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
C_HATCH = (0.62, 0.66, 0.70, 1)               # klapka: inny kolor tylko na renderach
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


def rect_yz(y0, y1, z0, z1):
    return [(y0, z0), (y1, z0), (y1, z1), (y0, z1)]


def outer_solid(x0=0.0, x1=L):
    return tmp("obrys", extrude_x_bm(OUTER, x0, x1))


# ---------------------------------------------------------------- geometria szwów (front i lustrzanie tył)
# Szew leży na zaokrąglonym narożniku ściany z podstawą (kąt normalnej psi liczony od osi +Y na froncie: 150° = front,
# 270° = dół). Zakładka połówkowa: zewnętrzna połowa ścianki pokrywy kończy się na psi1, wewnętrzna (nosek) schodzi do psi2.
def ang(psi, r, c=None):
    c = c or C_O
    return (c[0] + r * math.cos(math.radians(psi)), c[1] + r * math.sin(math.radians(psi)))


def arc_band(c, r0, r1, a0, a1, n=10):
    """Wielokąt: pierścień kołowy od promienia r0 do r1 między kątami a0 i a1 (stopnie)."""
    outer = [ang(a0 + (a1 - a0) * k / n, r1, c) for k in range(n + 1)]
    inner = [ang(a0 + (a1 - a0) * k / n, r0, c) for k in range(n, -1, -1)]
    return outer + inner


def sector(c, r, a0, a1, n=12):
    return [c] + [ang(a0 + (a1 - a0) * k / n, r, c) for k in range(n + 1)]


C_O = (RB / math.tan(math.radians(30)), RB)                 # środek zaokrąglenia zewnętrznego narożnika front/podstawa
PSI_RIM = 172.0                                             # zakładka boczna tylko tam, gdzie zdejmowanie w górę jest swobodne
PSI1, PSI2 = 208.0, 238.0                                   # koniec zewnętrznej połowy i końca noska (stopnie)
R_MC, R_MB = 4.15, 4.35                                     # granica połówek: promień (pokrywa) i (korpus, luz 0,2)
GAP_DEG = 3.2                                               # szczelina kątowa korpusu (ok. 0,25 mm na promieniu 5)


def corner_cut(gap, simple=False):
    """Kontur szwu przy narożniku frontu (od zewnątrz do wnętrza); gap = 0 dla pokrywy, 1 dla wycinania korpusu."""
    a1, a2 = PSI1 + gap * GAP_DEG, PSI2 + gap * 0.6     # nosek siada na ramieniu korpusu (luz 0,05 mm), zewnętrzna szczelina 0,25 mm
    if simple:
        return [ang(PSI_RIM + gap * GAP_DEG, 9.0), ang(PSI_RIM + gap * GAP_DEG, 0.5)]
    rm = R_MB if gap else R_MC
    return [ang(a1, 9.0), ang(a1, rm), ang(a2, rm), ang(a2, 0.5)]


def zone_poly(gap, simple=False):
    """Pas pokrywy: od szwu frontu przez wierzchołek do szwu tyłu (lustrzany) i całe wnętrze nad cięciwą."""
    f = corner_cut(gap, simple)
    return f + list(reversed(mir(f))) + [(B + 80, H + 80), (-80, H + 80)]


RIM_T = 0.9                                                 # grubość zewnętrznej połowy ścianki w zakładce bocznej
RIM = 1.0                                                   # zakładka na bokach: pokrywa wchodzi tyle w bok
RIM_CLR = 1.0                                               # luz zakładki w głąb wcięcia: pozwala unieść jeden róg przy zwalnianiu
_op = [(0.0, 0.0), (B, 0.0), (B / 2, H)]
OUT_HALF = U.fillet_poly(U.offset_poly(_op, [RIM_T] * 3), [RB - RIM_T, RB - RIM_T, RA - RIM_T])
OUT_HALF_B = U.fillet_poly(U.offset_poly(_op, [RIM_T + RIM_CLR] * 3), [RB - RIM_T - RIM_CLR, RB - RIM_T - RIM_CLR, RA - RIM_T - RIM_CLR])


def make_outer_bev():
    sh = tmp("obrys", extrude_x_bm(OUTER, 0.0, L))
    bevel(sh, R_END, segments=6)
    return sh


def make_shell0():
    sh = make_outer_bev()
    cut(sh, tmp("wnetrze", extrude_x_bm(INNER, WE, L - WE)))
    return sh


# ---------------------------------------------------------------- zatrzaski (przekrój w układzie frontu; tył lustrzanie)
LATCH_Y, LATCH_T = 10.5, 1.2                  # zewnętrzna ścianka nogi od krawędzi podstawy, grubość nogi
LATCH_Z0 = WALL + 0.4                         # spód nogi nad podłogą (podłoga ma górę na z = WALL)
BARB, BARB_H = 0.8, 1.1                       # wysięg zaczepu i wysokość (dolna ścianka skośna 45°, górna pozioma)
SHELF_T, SHELF_GRIP = 1.0, 0.6                # półka korpusu: grubość i zachodzenie na zaczep
Z_CATCH = LATCH_Z0 + BARB_H                   # poziom płaskiej ścianki zaczepu
POKE_R = 0.8                                  # otwór na szpilkę w spodzie (Ø1,6)


def wall_z(y, back=False):
    """Wysokość wewnętrznej powierzchni ściany pochyłej nad punktem y (front: grubość PANEL, tył: WALL)."""
    if back:
        return ((B - y) * sin_t - WALL) / cos_t
    return (y * sin_t - PANEL) / cos_t


def latch_leg_poly():
    y0, y1 = LATCH_Y, LATCH_Y + LATCH_T
    return [(y0, LATCH_Z0), (y1, LATCH_Z0), (y1, wall_z(y1) + 0.7), (y0, wall_z(y0) + 0.7)]


def latch_barb_poly():
    y0 = LATCH_Y
    return [(y0 + 0.05, LATCH_Z0 + 0.05), (y0 - BARB, LATCH_Z0 + BARB), (y0 - BARB, Z_CATCH), (y0 + 0.05, Z_CATCH)]


def latch_shelf_polys():
    y0 = LATCH_Y
    rib = rect_yz(y0 - BARB - 1.6, y0 - BARB - 0.2, WALL - 1.0, Z_CATCH + 0.1 + SHELF_T)
    shelf = rect_yz(y0 - BARB - 1.6, y0 - BARB + SHELF_GRIP, Z_CATCH + 0.1, Z_CATCH + 0.1 + SHELF_T)
    return rib, shelf


# ================================================================ POKRYWA
shell0 = make_shell0()
tube = make_outer_bev()
cut(tube, tmp("wn_rura", extrude_x_bm(INNER, -2.0, L + 2.0)))
cover = bpy.data.objects.new("Pokrywa", tube.data.copy())
coll("tmp").objects.link(cover)
regroup(cover, "Pokrywa", LID_C)
intersect(cover, prism_x("strefa_pokrywy", zone_poly(0), WE - RIM + 0.25, L - WE + RIM - 0.25))
cut(cover, prism_x("rim_l", OUT_HALF, WE - RIM - 1.0, CX0), prism_x("rim_p", OUT_HALF, CX1, L - WE + RIM + 1.0))
for c_, pts in ((C_O, sector(C_O, 5.5, PSI_RIM, PSI2 + 1.0)), (None, mir(sector(C_O, 5.5, PSI_RIM, PSI2 + 1.0)))):
    cut(cover, prism_x("nosek_l", pts, WE - RIM - 1.0, CX0), prism_x("nosek_p", pts, CX1, L - WE + RIM + 1.0))
bpy.data.objects.remove(tube, do_unlink=True)
chk("pokrywa: strefa i zakładki boczne", cover)

# nosek zakładki: wewnętrzna połowa schodzi do PSI2, pogrubiona do wnętrza narożnika (r 2,6 od środka zewnętrznego)
nib = arc_band(C_O, 2.6, 3.55, PSI1 - 6.0, PSI2)
union(cover, prism_x("nosek_f", nib, CX0 + 0.5, CX1 - 0.5), prism_x("nosek_t", mir(nib), CX0 + 0.5, CX1 - 0.5))
chk("pokrywa: noski", cover)

# nogi zatrzasków (front i tył, przy obu końcach)
for lx in LATCH_X:
    for back in (False, True):
        leg = latch_leg_poly()
        if back:
            y0, y1 = B - LATCH_Y - LATCH_T, B - LATCH_Y
            leg = [(y0, LATCH_Z0), (y1, LATCH_Z0), (y1, wall_z(y1, True) + 0.7), (y0, wall_z(y0, True) + 0.7)]
        union(cover, prism_x("noga", leg, lx - LATCH_W / 2, lx + LATCH_W / 2))
        if not NOHOOK:
            bp = latch_barb_poly()
            union(cover, prism_x("zaczep", mir(bp) if back else bp, lx - LATCH_W / 2 + 0.2, lx + LATCH_W / 2 - 0.2))
chk("pokrywa: zatrzaski", cover)

# okno, listewki modułu
cut(cover, to_world(tmp("okno", rrect_bm(-GLASS_W / 2 - 0.3, -GLASS_H / 2 - 0.3, -0.5, GLASS_W / 2 + 0.3, GLASS_H / 2 + 0.3,
                                          PANEL + 0.6, R_WIN)), M_DISP))
for sx in (-MOD_L / 2 + 5.0, MOD_L / 2 - 5.0):
    for sy in (-1, 1):
        y0, y1 = (MODULE_W / 2 + 0.3, MODULE_W / 2 + 1.3) if sy > 0 else (-MODULE_W / 2 - 1.3, -MODULE_W / 2 - 0.3)
        union(cover, to_world(boxuv("listwa", sx - 3.0, sx + 3.0, y0, y1, -3.0, 0.3), M_DISP))
for sx in (-1, 1):
    x0, x1 = (MOD_L / 2 + 0.3, MOD_L / 2 + 1.3) if sx > 0 else (-MOD_L / 2 - 1.3, -MOD_L / 2 - 0.3)
    union(cover, to_world(boxuv("listwa", x0, x1, -3.0, 3.0, -3.0, 0.3), M_DISP))
chk("pokrywa: moduł", cover)

# słupki płytki głównej
for hx, hy, _ in HOLES:
    union(cover, to_world(cyl("slupek", hx, hy, 0.0, S.D_JOINT + 0.4, 2.9, seg=32), M_BOARD))
for hx, hy, _ in HOLES:
    cut(cover, to_world(cyl("pilot", hx, hy, -0.1, S.D_JOINT + WALL - 0.5, 1.05, seg=24), M_BOARD))
chk("pokrywa: słupki płytki", cover)

# otwory pod kapsle, obniżenie pod tabletkę, słupki płytki przycisków
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
for bx, by in BTN_SCREW:
    union(cover, to_world(cyl("slupek_b", bx, by, 0.0, BZ_CEIL + 0.6, 1.8, seg=24), M_BTN))
    cut(cover, to_world(cyl("pilot_b", bx, by, -0.1, 5.5, 0.85, seg=20), M_BTN))
chk("pokrywa: przyciski", cover)

# ================================================================ KORPUS: taca z podłogą, bokami i dolnymi narożnikami
body = regroup(shell0, "Korpus", C_BODY)
body.name = "Korpus"
cut(body, prism_x("strefa_korpusu", zone_poly(1), WE, L - WE))
chk("korpus: podział", body)

# półki zatrzasków i otwory na szpilkę
for lx in LATCH_X:
    for back in (False, True):
        rib, shelf = latch_shelf_polys()
        if back:
            rib, shelf = mir(rib), mir(shelf)
        union(body, prism_x("polka_z", rib, lx - LATCH_W / 2 - 0.75, lx + LATCH_W / 2 + 0.75),
              prism_x("polka", shelf, lx - LATCH_W / 2 - 0.75, lx + LATCH_W / 2 + 0.75))
        py = LATCH_Y - 0.45
        cut(body, cyl("szpilka", lx, B - py if back else py, -1.0, WALL + 0.05, POKE_R, seg=24))
chk("korpus: półki zatrzasków", body)

# ---------------------------------------------------------------- gniazda styków (zmierzone płytki)
# Szereg: BAT- = sprężyna A (prawy koniec, pojedyncza z blaszką) -> A -> przycisk A i sprężyna B na lewej podwójnej
# (z blaszką 3 x 6, nieużywana) -> B -> przycisk B i sprężyna C na prawej podwójnej (bez blaszki) -> C -> przycisk C
# (lewy koniec, pojedyncza z blaszką) = BAT+. Płytka podwójna leży na środku między ogniwami, styki 0,25 mm poza osiami.
CY = [c[0] for c in CELLS]
PLO = Z_AX - DUAL_H / 2                       # spód płytek (styki na środku wysokości), dno szczelin
DM_L, DM_P = (CY[0] + CY[1]) / 2, (CY[1] + CY[2]) / 2
PLATES = {   # koniec: lista (rodzaj, y0, y1)
    "L": [("dual", DM_L - DUAL_W / 2, DM_L + DUAL_W / 2), ("sgl", CY[2] - SGL_W / 2, CY[2] + SGL_W / 2)],
    "P": [("sgl", CY[0] - SGL_W / 2, CY[0] + SGL_W / 2), ("dual", DM_P - DUAL_W / 2, DM_P + DUAL_W / 2)],
}
CONTACTS = {  # koniec: lista (rodzaj styku, y środka)
    "L": [("btn", DM_L - CONTACT_PITCH / 2), ("spr", DM_L + CONTACT_PITCH / 2), ("btn", CY[2])],
    "P": [("spr", CY[0]), ("btn", DM_P - CONTACT_PITCH / 2), ("spr", DM_P + CONTACT_PITCH / 2)],
}
PLATE_TOP = PLO + DUAL_H
# strop koszyka: łuki nad ogniwami (luz 0,25 do ogniwa Ø10,5, grubość 0,8 na grzbiecie), ścianki gniazd sięgają do jego góry
ROOF_CLR, ROOF_T = 0.25, 0.8
ROOF_RI = W.CELL_R + ROOF_CLR                 # wnętrze łuku
ROOF_RO = ROOF_RI + ROOF_T                    # zewnętrze łuku
ROOF_TOP = Z_AX + ROOF_RO
ROOF_BOT = Z_AX + 3.0                         # spód przegród między ogniwami (ścięty płasko, przegroda ma tam 1,5 mm)
ROOF_SKIRT = 1.0                              # ścianki boczne koszyka wzdłuż krawędzi otworu klapki, od dna do stropu
RIB_W, RIB_TOP = 1.6, 17.0                    # żebra na stropie (w środkowej strefie wolne miejsce sięga 19...30 mm)
SPR_SLOT_W, SPR_SLOT_L = 2 * SPR_R + 1.0, SPR_FREE + 0.5   # wycięcie w stropie na sprężynę wsuwanej płytki (swobodna 8 mm)
CW_TOP = max(PLATE_TOP + 0.5, ROOF_TOP)
CW_Y0 = min(p[1] for v in PLATES.values() for p in v) - CW_CLR - 0.6
CW_Y1 = max(p[2] for v in PLATES.values() for p in v) + CW_CLR + 0.6
if CW_Y0 < W.NOSE_SWEEP_Y or CW_Y1 > B - W.NOSE_SWEEP_Y:
    raise SystemExit(f"ścianka gniazd wchodzi w tor noska: y {CW_Y0:.2f}..{CW_Y1:.2f}")
# sprężyna Ø6 + 1 mm luzu musi się zmieścić w oknie między wargami (w poziomie) i nad dnem korpusu (w pionie)
SPR_KO = SPR_R + SPR_MARGIN
spr_margin = []
for end in ("L", "P"):
    for kind, yc_ in CONTACTS[end]:
        if kind != "spr":
            continue
        for _, y0, y1 in PLATES[end]:
            if y0 <= yc_ <= y1:
                spr_margin.append(min(yc_ - SPR_KO - (y0 + CW_GRIP), (y1 - CW_GRIP) - (yc_ + SPR_KO)))
spr_margin.append(Z_AX - SPR_KO - WALL)
if min(spr_margin) < 0:
    raise SystemExit(f"sprężyna z luzem 1 mm nie mieści się w oknie gniazda: {spr_margin}")

IN_CLEAR = U.offset_poly(INNER_FULL, [0.5] * len(INNER_FULL))   # wnętrze z luzem 0,5 do ścian pokrywy


def clear_solid(x0, x1):
    """Strefa dla ścianek gniazd i stropu: wnętrze z luzem 0,5 do ścian pokrywy, ale bez odsuwania od podłogi korpusu
    (sam IN_CLEAR zaczyna się 0,5 nad podłogą i ścianki wisiałyby nad dnem). Przy podłodze (do z = 3) pokrywy nie ma:
    jej ściany są tam dalej niż y 8,5 od krawędzi podstawy tylko w narożnikach, poza ściankami gniazd."""
    sol = prism_x("wnetrze_luz", IN_CLEAR, x0, x1)
    union(sol, boxuv("przy_podlodze", x0, x1, 8.5, B - 8.5, -1.0, 3.0))
    return sol


def wall_x(end):
    """Płaszczyzny ścianki gniazd w X: tył, początek i koniec szczeliny, koniec warg (od strony ogniw)."""
    if end == "L":
        xb0 = UA - PL_T - CW_BACK
        xs0 = UA - PL_T
        return xb0, xs0, xs0 + CW_SLOT, xs0 + CW_SLOT + CW_LIP
    xb0 = UB + PL_T + CW_BACK
    xs0 = UB + PL_T
    return xb0, xs0, xs0 - CW_SLOT, xs0 - CW_SLOT - CW_LIP


def contact_wall(end):
    """Ścianka gniazd: tył, szczelina na płytki (wsuwane od góry, zadziory trzymają je na wcisk), wargi na bocznych
    brzegach płytek. Okno między wargami sięga do dna szczeliny (bez dolnej wargi: miejsce na sprężynę z luzem)."""
    xb0, xs0, xs1, xl1 = wall_x(end)
    lo, hi = min(xb0, xl1), max(xb0, xl1)
    wall = boxuv("scianka_g", lo, hi, CW_Y0, CW_Y1, 1.0, CW_TOP)
    intersect(wall, clear_solid(lo - 1.0, hi + 1.0))
    s0, s1 = min(xs0, xs1), max(xs0, xs1)
    lip0, lip1 = (s1, hi) if end == "L" else (lo, s0)
    for kind, y0, y1 in PLATES[end]:
        cut(wall, boxuv("szczelina", s0, s1, y0 - CW_CLR, y1 + CW_CLR, PLO, CW_TOP + 1.0))
        cut(wall, boxuv("okno_g", lip0 - 0.1, lip1 + 0.1, y0 + CW_GRIP, y1 - CW_GRIP, PLO, CW_TOP + 1.0))
    return wall


for end in ("L", "P"):
    union(body, contact_wall(end))
chk("korpus: gniazda styków", body)


# ---------------------------------------------------------------- klapka w dnie
# Otwór między końcami warg obu ścianek gniazd, w poprzek trzech ogniw (5,25 + 0,3 luzu od osi skrajnych). Przylga: od spodu
# otwór jest większy (o RAB_X na końcach i HATCH_RAB na bokach, do wysokości RAB_T), więc klapka opiera się kołnierzem
# o korpus i nie da się jej wcisnąć do środka. Lewy koniec: język w kieszeni pod ścianką gniazd (nad dnem korpusu).
# Prawy koniec: ucho pod ścianką gniazd z wkrętem M2 x 6 (łeb stożkowy) wkręcanym w tuleję w strefie zatrzasków.
HC, RAB_X, RAB_Y, RAB_T = W.HATCH_GAP, 1.0, W.HATCH_RAB, 1.0
X0, X1 = wall_x("L")[3], wall_x("P")[3]
Y0, Y1 = CY[0] - W.CELL_R - W.HATCH_CELL_CLR, CY[2] + W.CELL_R + W.HATCH_CELL_CLR
TONGUE_L, TONGUE_W, TONGUE_T = 2.0, 14.0, 0.8           # język: wysięg za otwór, szerokość, grubość (z RAB_T do RAB_T + 0,8)
POCKET_TOP = 2.3                                       # kieszeń z zapasem na obrót klapki (kontrola: check_assembly_wedge5)
EAR_W, EAR_T = 7.0, 1.4
SCREW_X, SCREW_Y = L - WE - LATCH_ZONE / 2, CY[1]
SCREW_HEAD_R, SCREW_CLR_R, SCREW_PILOT_R = 2.0, 1.2, 0.85   # łeb Ø4 (zagłębienie 90°), otwór w uchu Ø2,4, otwór pilotowy Ø1,7
BOSS_TOP, PILOT_TOP = 8.0, 7.2
CRADLE_TOP, CRADLE_R = Z_AX - 3.0, W.CELL_R + 0.15     # kołyska ogniw na klapce: korytka r 5,4 do 3 mm pod osią
POCKET_SKIN = PLO - POCKET_TOP
if POCKET_SKIN < 0.4:
    raise SystemExit(f"kieszeń języka za blisko dna szczelin: {POCKET_SKIN:.2f} mm")

cut(body, tmp("otwor_klapki", rrect_bm(X0, Y0, -1.0, X1, Y1, WALL + 0.5, 1.0)),
    tmp("przylga", rrect_bm(X0 - RAB_X, Y0 - RAB_Y, -1.0, X1 + RAB_X, Y1 + RAB_Y, RAB_T, 1.5)),
    tmp("kieszen_ucha", rrect_bm(X1 - 1.0, SCREW_Y - EAR_W / 2, -1.0, SCREW_X + SCREW_HEAD_R + 0.1, SCREW_Y + EAR_W / 2, EAR_T, 2.0)),
    box("kieszen_jezyka", X0 - TONGUE_L - 0.3, CY[1] - TONGUE_W / 2 - 0.3, RAB_T - 0.01, X0 + 0.1, CY[1] + TONGUE_W / 2 + 0.3, POCKET_TOP))
# podważanie: wnęka w spodzie przy prawym końcu kołnierza, obok ucha (na paznokieć lub śrubokręt)
cut(body, box("wneka", X1 + RAB_X - 0.2, SCREW_Y + EAR_W / 2 + 1.5, -1.0, X1 + RAB_X + 1.4, SCREW_Y + EAR_W / 2 + 7.5, 0.8))
union(body, box("tuleja", wall_x("P")[0] - 0.01, SCREW_Y - 3.5, WALL - 0.5, L - WE + 0.3, SCREW_Y + 3.5, BOSS_TOP))
cut(body, cyl("pilot_wkretu", SCREW_X, SCREW_Y, -1.0, PILOT_TOP, SCREW_PILOT_R, seg=24))
chk("korpus: klapka", body)

hatch = finish("Klapka", rrect_bm(X0 - RAB_X + HC, Y0 - RAB_Y + HC, 0.0, X1 + RAB_X - HC, Y1 + RAB_Y - HC, RAB_T, 1.5 - HC),
               "Klapka", C_HATCH)
hatch["grupa"] = "Klapka"
union(hatch, tmp("czop", rrect_bm(X0 + HC, Y0 + HC, RAB_T - 0.01, X1 - HC, Y1 - HC, WALL, 1.0 - HC)),
      tmp("ucho", rrect_bm(X1 - 1.0, SCREW_Y - EAR_W / 2 + HC, 0.0, SCREW_X + SCREW_HEAD_R + 0.1 - HC, SCREW_Y + EAR_W / 2 - HC,
                           EAR_T, 2.0 - HC)),
      box("jezyk", X0 - TONGUE_L, CY[1] - TONGUE_W / 2, RAB_T - 0.01, X0 + HC + 0.5, CY[1] + TONGUE_W / 2, RAB_T + TONGUE_T),
      box("kolyska", X0 + HC, Y0 + HC, WALL - 0.01, X1 - 0.6, Y1 - HC, CRADLE_TOP))
for cy_ in CY:
    cut(hatch, xcyl("korytko", cy_, Z_AX, X0 - 1.0, X1 + 1.0, CRADLE_R, 64))
cut(hatch, cyl("otw_wkretu", SCREW_X, SCREW_Y, -1.0, EAR_T + 1.0, SCREW_CLR_R, seg=24),
    tmp("stozek", cyl_bm(SCREW_X, SCREW_Y, -0.01, SCREW_HEAD_R - SCREW_CLR_R, SCREW_HEAD_R + 0.01, r2=SCREW_CLR_R, seg=32)))
chk("klapka", hatch)

# ---------------------------------------------------------------- strop koszyka
# Zamyka koszyk od strony wnętrza: przy otwartej klapce ogniwa nie da się wepchnąć do środka obudowy. Łuk nad każdym ogniwem
# (wnętrze r 5,5, zewnętrze r 6,3, od 3 mm nad osią), ścianki boczne wzdłuż krawędzi otworu, żebra na stropie w strefach
# z wolnym miejscem. Płytki styków nadal wsuwa się od góry: szczeliny w ściankach gniazd są otwarte, a nad sprężynami są
# wycięcia (Ø6 + 1, swobodna sprężyna 8 mm), przez które sprężyna przechodzi przy wsuwaniu płytki. Wycięcia (7 mm) są
# węższe od ogniwa. Blaszki lutownicze wystają nad ścianki gniazd, poza stropem.
SPRINGS = [(end, yc_) for end in ("L", "P") for kind, yc_ in CONTACTS[end] if kind == "spr"]
VALLEYS = [(CY[0] + CY[1]) / 2, (CY[1] + CY[2]) / 2]
RX0, RX1 = X0 - 0.4, X1 + 0.4                 # zachodzi na wargi (okna wycina się potem jeszcze raz)
roof = xcyl("strop", CY[0], Z_AX, RX0, RX1, ROOF_RO, 96)
union(roof, xcyl("strop_b", CY[1], Z_AX, RX0, RX1, ROOF_RO, 96), xcyl("strop_c", CY[2], Z_AX, RX0, RX1, ROOF_RO, 96))
intersect(roof, boxuv("strop_zakres", RX0, RX1, Y0 - ROOF_SKIRT, Y1 + ROOF_SKIRT, ROOF_BOT, ROOF_TOP + 1.0))
# ścianki boczne do spodu stropu i wypełnienie między ścianką a łukiem (nad ogniwem, kształt nada mu wycięcie walca);
# wyżej się nie da: przy tyle nad ścianką jest dioda D1 płytki głównej (spód z = 10,84)
for y_a, y_b, f_a, f_b in ((Y0 - ROOF_SKIRT, Y0, Y0 - ROOF_SKIRT, Y0 + 1.2), (Y1, Y1 + ROOF_SKIRT, Y1 - 1.2, Y1 + ROOF_SKIRT)):
    union(roof, boxuv("scianka_koszyka", RX0, RX1, y_a, y_b, WALL - 0.01, ROOF_BOT + 0.05),
          boxuv("wypelnienie", RX0, RX1, f_a, f_b, ROOF_BOT - 1.5, ROOF_BOT + 0.05))
for ym in VALLEYS:
    union(roof, boxuv("zebro_stropu", RX0, RX1, ym - RIB_W / 2, ym + RIB_W / 2, ROOF_BOT, RIB_TOP))
rib_c0 = max([UA + SPR_SLOT_L + 0.5 for e, yc_ in SPRINGS if e == "L" and abs(yc_ - CY[1]) < SPR_SLOT_W / 2 + RIB_W / 2] + [RX0])
rib_c1 = min([UB - SPR_SLOT_L - 0.5 for e, yc_ in SPRINGS if e == "P" and abs(yc_ - CY[1]) < SPR_SLOT_W / 2 + RIB_W / 2] + [RX1])
union(roof, boxuv("zebro_stropu_b", rib_c0, rib_c1, CY[1] - RIB_W / 2, CY[1] + RIB_W / 2, ROOF_BOT, RIB_TOP))
for cy_ in CY:
    cut(roof, xcyl("strop_wn", cy_, Z_AX, RX0 - 1.0, RX1 + 1.0, ROOF_RI, 96))
intersect(roof, clear_solid(RX0 - 1.0, RX1 + 1.0))
union(body, roof)
for end in ("L", "P"):
    xb0, xs0, xs1, xl1 = wall_x(end)
    lo, hi = min(xb0, xl1), max(xb0, xl1)
    lip0, lip1 = (max(xs0, xs1), hi) if end == "L" else (lo, min(xs0, xs1))
    for kind, y0, y1 in PLATES[end]:
        cut(body, boxuv("okno_g", lip0 - 0.1, lip1 + 0.1, y0 + CW_GRIP, y1 - CW_GRIP, PLO, RIB_TOP + 1.0))
for end, yc_ in SPRINGS:
    xa, xb = (wall_x("L")[2], UA + SPR_SLOT_L) if end == "L" else (UB - SPR_SLOT_L, wall_x("P")[2])
    cut(body, boxuv("wyciecie_sprezyny", xa, xb, yc_ - SPR_SLOT_W / 2, yc_ + SPR_SLOT_W / 2, Z_AX, RIB_TOP + 1.0))
chk("korpus: strop koszyka", body)

# pierścień głośnika i otwory dźwiękowe w lewym boku
ring = xcyl("pierscien", SPK_CY, SPK_CZ, WE - 0.2, WE + RING_L, SPK_POCKET / 2 + 1.9, 96)
cut(ring, xcyl("pierscien_w", SPK_CY, SPK_CZ, WE - 0.5, WE + RING_L + 0.5, SPK_POCKET / 2, 96))
intersect(ring, outer_solid())
union(body, ring)
holes = [(0.0, 0.0)]
holes += [(4.5 * math.cos(2 * math.pi * i / 8 + 0.2), 4.5 * math.sin(2 * math.pi * i / 8 + 0.2)) for i in range(8)]
holes += [(9.0 * math.cos(2 * math.pi * i / 14 + 0.07), 9.0 * math.sin(2 * math.pi * i / 14 + 0.07)) for i in range(14)]
bm = bmesh.new()
for dy, dz in holes:
    ret = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=20, radius1=1.0, radius2=1.0, depth=WE + 0.8)
    bmesh.ops.rotate(bm, verts=ret["verts"], cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "Y"))
    bmesh.ops.translate(bm, vec=((WE + 0.3 - 0.5) / 2, SPK_CY + dy, SPK_CZ + dz), verts=ret["verts"])
cut(body, tmp("dzwieki", bm))
chk("korpus: głośnik", body)

# wcięcia w bokach pod zakładki pokrywy (zewnętrzna warstwa w pasie pokrywy, szczelina 0,25 mm, luz w głąb RIM_CLR)
for x0, x1 in ((WE - RIM, WE + 0.5), (L - WE - 0.5, L - WE + RIM)):
    rab = prism_x("rab", OUTER, x0, x1)
    intersect(rab, prism_x("rab_s", zone_poly(1, simple=True), x0, x1))
    cut(rab, prism_x("rab_w", OUT_HALF_B, x0 - 1.0, x1 + 1.0))
    cut(body, rab)
chk("korpus: wcięcia boczne", body)

# kontrola: ścianki gniazd i ścianki boczne koszyka muszą stać na dnie (pasek 0,4 mm tuż nad dnem pod nimi ma być pełny).
# Liczba brył tego nie wykryje: ścianki łączą się z resztą korpusu przez tuleję wkrętu i strop.
def fill_ratio(x0, x1, y0, y1, z0, z1):
    probe = box("sonda_dna", x0, y0, z0, x1, y1, z1)
    v0 = (x1 - x0) * (y1 - y0) * (z1 - z0)
    intersect(probe, body, keep=True)
    v = manifold_report(probe)[1]
    bpy.data.objects.remove(probe, do_unlink=True)
    return v / v0


BASE_Z0, BASE_Z1 = WALL + 0.02, WALL + 0.42
TY0, TY1 = CY[1] - TONGUE_W / 2 - 0.3, CY[1] + TONGUE_W / 2 + 0.3       # pod lewą ścianką jest kieszeń języka (do z 2,3)
xl, xr = wall_x("L"), wall_x("P")
BASE_PROBES = {
    "ścianka gniazd L (przód)": (xl[0] + 0.1, xl[3] - 0.1, CW_Y0 + 0.8, TY0 - 0.2),
    "ścianka gniazd L (tył)": (xl[0] + 0.1, xl[3] - 0.1, TY1 + 0.2, CW_Y1 - 0.8),
    "ścianka gniazd P": (xr[3] + 0.1, xr[0] - 0.1, CW_Y0 + 0.8, CW_Y1 - 0.8),
    "ścianka koszyka (przód)": (RX0 + 1.0, RX1 - 1.0, Y0 - ROOF_SKIRT + 0.1, Y0 - 0.1),
    "ścianka koszyka (tył)": (RX0 + 1.0, RX1 - 1.0, Y1 + 0.1, Y1 + ROOF_SKIRT - 0.1),
}
base_fill = {k: fill_ratio(*v, BASE_Z0, BASE_Z1) for k, v in BASE_PROBES.items()}
print("Styk ze dnem (wypełnienie paska 0,4 mm nad dnem): " + ", ".join(f"{k} {r * 100:.0f}%" for k, r in base_fill.items()))
if min(base_fill.values()) < 0.98:
    raise SystemExit("ścianka nie stoi na dnie korpusu")

# ================================================================ KAPSLE (w układzie płytki przycisków)
caps = []
SURF_R = RA - 0.15


def socket(cap, bx, y0):
    """Gniazdo na trzpień B3F-4055: kwadrat z luzem i cztery żebra docisku (3,5 mm między żebrami), fazka wejściowa."""
    cut(cap, box("gniazdo", bx - SOCK / 2, y0 - SOCK / 2, CAP_BOT - 0.1, bx + SOCK / 2, y0 + SOCK / 2, SW_TOP + 0.05))
    fz = bmesh.new()
    bmesh.ops.create_cone(fz, cap_ends=True, cap_tris=False, segments=4, radius1=(SOCK / 2 + 0.4) * math.sqrt(2),
                          radius2=SOCK / 2 * math.sqrt(2), depth=0.4)
    bmesh.ops.rotate(fz, verts=fz.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 4, 3, "Z"))
    bmesh.ops.translate(fz, vec=(bx, y0, CAP_BOT + 0.2 - 0.001), verts=fz.verts)
    cut(cap, tmp("fazka", fz))
    g = (SOCK - SOCK_GRIP) / 2
    for sx, sy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        if sx:
            x0, x1 = (bx + SOCK / 2 - g, bx + SOCK / 2 + 0.01) if sx > 0 else (bx - SOCK / 2 - 0.01, bx - SOCK / 2 + g)
            rb = box("zebro", x0, y0 - SOCK_RIB_W / 2, CAP_BOT + 0.4, x1, y0 + SOCK_RIB_W / 2, SW_TOP + 0.06)
        else:
            y_0, y_1 = (y0 + SOCK / 2 - g, y0 + SOCK / 2 + 0.01) if sy > 0 else (y0 - SOCK / 2 - 0.01, y0 - SOCK / 2 + g)
            rb = box("zebro", bx - SOCK_RIB_W / 2, y_0, CAP_BOT + 0.4, bx + SOCK_RIB_W / 2, y_1, SW_TOP + 0.06)
        union(cap, rb)


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
        cut(cap, finish("tri", U.prism_bm([(bx - 1.6, y0 - 2.1), (bx + 2.3, y0), (bx - 1.6, y0 + 2.1)], zt, top + 0.1), "tmp", T))
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
    socket(cap, bx, y0)
    to_world(cap, M_BTN)
    caps.append(cap)

# ================================================================ STYKI I OGNIWA (podgląd)
C_NICKEL, C_CELL, C_GOLD = (0.78, 0.74, 0.62, 1), (0.20, 0.42, 0.72, 1), (0.85, 0.65, 0.20, 1)
C_STYK = "Styki"


def plate_obj(name, end, y0, y1, z0, z1, tab=None):
    """Płytka styku w szczelinie; tab = (szerokość, długość) blaszki na środku górnej krawędzi, prosto do góry."""
    xa, xb = (UA - PL_T, UA) if end == "L" else (UB, UB + PL_T)
    p = finish(name, extrude_x_bm(rect_yz(y0, y1, z0, z1), xa, xb), C_STYK, C_NICKEL)
    if tab:
        ym, (tw, tl) = (y0 + y1) / 2, tab
        union(p, finish("blaszka", extrude_x_bm(rect_yz(ym - tw / 2, ym + tw / 2, z1 - 0.01, z1 + tl), xa, xb), "tmp", T))
    return p


def button(name, end, cy_):
    xa, xb = (UA, UA + BTN_H) if end == "L" else (UB - BTN_H, UB)
    return finish(name, cyl_bm(cy_, Z_AX, xa, xb, BTN_R, axis="X", seg=32), C_STYK, C_NICKEL)


def spring(name, end, cy_, length):
    xa, xb = (UA, UA + length) if end == "L" else (UB - length, UB)
    return finish(name, cyl_bm(cy_, Z_AX, xa, xb, SPR_R, axis="X", seg=32), C_STYK, C_NICKEL)


SPR_LEN = L_CONT - CELL_L - BTN_H             # sprężyna przy najdłuższym ogniwie (dociśniętym do przycisku po drugiej stronie)
NAMES = {("L", 0): ("styk_podwojny_lewy", (DUAL_TAB_W, DUAL_TAB_L)), ("L", 1): ("styk_C_plus_BAT+", (SGL_TAB_W, SGL_TAB_L)),
         ("P", 0): ("styk_A_minus_BAT-", (SGL_TAB_W, SGL_TAB_L)), ("P", 1): ("styk_podwojny_prawy", None)}
for end in ("L", "P"):
    for i, (kind, y0, y1) in enumerate(PLATES[end]):
        name, tab = NAMES[(end, i)]
        ob = plate_obj(name, end, y0, y1, PLO, PLO + (DUAL_H if kind == "dual" else SGL_H), tab)
        ob["koniec"], ob["y0"], ob["y1"] = end, y0, y1        # do kontroli wsuwania płytek (check_assembly_wedge5)
    for j, (kind, yc_) in enumerate(CONTACTS[end]):
        ob = button(f"przycisk_{end}{j}", end, yc_) if kind == "btn" else spring(f"sprezyna_{end}{j}", end, yc_, SPR_LEN)
        ob["koniec"], ob["yc"] = end, yc_
scene["spr_free"], scene["ua"], scene["ub"], scene["spr_r"] = SPR_FREE, UA, UB, SPR_R

# ogniwa: (+) od strony przycisku
for name, cy_, plus_left in (("AAA_A", CY[0], True), ("AAA_B", CY[1], False), ("AAA_C", CY[2], True)):
    if plus_left:
        n0 = UA + BTN_H
        finish(name + "_plus", cyl_bm(cy_, Z_AX, n0, n0 + NUB_H, NUB_R, axis="X"), "Baterie", C_GOLD)
        finish(name, cyl_bm(cy_, Z_AX, n0 + NUB_H, n0 + CELL_L, CELL_D / 2, axis="X"), "Baterie", C_CELL)
    else:
        n1 = UB - BTN_H
        finish(name + "_plus", cyl_bm(cy_, Z_AX, n1 - NUB_H, n1, NUB_R, axis="X"), "Baterie", C_GOLD)
        finish(name, cyl_bm(cy_, Z_AX, n1 - CELL_L, n1 - NUB_H, CELL_D / 2, axis="X"), "Baterie", C_CELL)

# ================================================================ PŁYTKI, MODUŁ, GŁOŚNIK (podgląd)
C_PCB, C_PART = (0.10, 0.42, 0.22, 1), (0.55, 0.40, 0.25, 1)
pcb = finish("PCB", rrect_bm(0, 0, -BT, BW, BH, 0, 3.0), "Plytka", C_PCB)
for hx, hy, hd in HOLES:
    cut(pcb, cyl("o", hx, hy, -BT - 0.5, 0.5, hd / 2, seg=24))
to_world(pcb, M_BOARD)
for name, p_ in REAR.items():
    bx0, by0, bx1, by1 = p_["body"]
    h = HEIGHT_OVERRIDE.get(name, p_["height_above_board"])
    to_world(box("el_" + name, bx0, by0, -BT - h, bx1, by1, -BT, "Plytka", C_PART), M_BOARD)

mod = box("OLED_modul", -MOD_L / 2, -MODULE_W / 2, -MODULE_T, MOD_L / 2, MODULE_W / 2, -MODULE_T + 1.2, "Wyswietlacz", (0.08, 0.20, 0.42, 1))
to_world(mod, M_DISP)
to_world(box("OLED_szklo", -GLASS_W / 2, -GLASS_H / 2, -MODULE_T + 1.2, GLASS_W / 2, GLASS_H / 2, 0.0, "Wyswietlacz", (0.04, 0.05, 0.10, 1)), M_DISP)
pin_x = -MOD_L / 2 + MOD_PIN_END
to_world(box("przewody_OLED", pin_x - 1.3, -5.3, -MODULE_T - WIRE_H, pin_x + 1.3 + 6.0, 5.3, -MODULE_T, "Wyswietlacz",
             (0.15, 0.15, 0.17, 1)), M_DISP)

BB_EXTRA = float(os.environ.get("TT_BB_EXTRA", "0"))  # 2 = płytka drukowana TT-BTN (54 mm, o 2 mm szersza z każdej strony)
bpcb = finish("PCB_przyciski", rrect_bm(-BB_EXTRA, 0, -BT, BB_W + BB_EXTRA, BB_D, 0, 2.0), "Plytka_przyciskow", C_PCB)
for bx, by in BTN_SCREW:
    cut(bpcb, cyl("o", bx, by, -BT - 0.5, 0.5, 1.1, seg=20))
to_world(bpcb, M_BTN)
for k, bx in BTN_X.items():
    parts = [box("B3F_" + k, bx - 6, BB_D / 2 - 6, 0, bx + 6, BB_D / 2 + 6, SW_BODY, "Plytka_przyciskow", (0.15, 0.15, 0.17, 1)),
             cyl("B3F_podstawa_" + k, bx, BB_D / 2, SW_BODY, SW_COLLAR, 3.55, "Plytka_przyciskow", (0.3, 0.3, 0.32, 1), seg=32),
             box("B3F_trzpien_" + k, bx - PLUNGER / 2, BB_D / 2 - PLUNGER / 2, SW_COLLAR, bx + PLUNGER / 2, BB_D / 2 + PLUNGER / 2,
                 SW_TOP, "Plytka_przyciskow", (0.8, 0.8, 0.82, 1)),
             box("B3F_nozki_" + k, bx - 2.5, BB_D / 2 - 2.5, -BT - 1.9, bx + 2.5, BB_D / 2 + 2.5, -BT, "Plytka_przyciskow", (0.6, 0.6, 0.6, 1))]
    for p_ in parts:
        to_world(p_, M_BTN)

cyl("Glosnik_ramka", SPK_CY, SPK_CZ, WE + 0.05, WE + SPK_FR, SPK_D / 2, "Glosnik", (0.12, 0.12, 0.13, 1), seg=96, axis="X")
cyl("Glosnik_stozek", SPK_CY, SPK_CZ, WE + SPK_FR, WE + SPK_H, 10.0, "Glosnik", (0.2, 0.2, 0.22, 1), seg=96, axis="X")

# ================================================================ KONTROLA I EKSPORT
def islands(ob):
    """Liczba spójnych kawałków siatki (część do druku musi być jedną bryłą; ścianka wisząca nad dnem daje 2)."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    seen, n = set(), 0
    for f in bm.faces:
        if f.index in seen:
            continue
        n += 1
        stack = [f]
        seen.add(f.index)
        while stack:
            g = stack.pop()
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen:
                        seen.add(h.index)
                        stack.append(h)
    bm.free()
    return n


printable = {"korpus": [body], "pokrywa": [cover], "klapka": [hatch], "kapsle": caps}
OUT.mkdir(parents=True, exist_ok=True)
RENDERS.mkdir(parents=True, exist_ok=True)
report = []
for fname, objs in printable.items():
    if not NOHOOK:
        write_stl(OUT / f"{fname}.stl", objs)
    for ob in objs:
        bad, vol = manifold_report(ob)
        d = ob.dimensions
        n_isl = islands(ob)
        report.append(f"{ob.name:18s} wymiary {d.x:6.1f} x {d.y:5.1f} x {d.z:5.1f} mm  objętość {vol:9.1f} mm3  krawędzie nie-rozmaitościowe: {bad}"
                      f"  osobne bryły: {n_isl}{'' if n_isl == 1 else '  <-- BŁĄD: część rozpada się na kawałki'}")
print("\n".join(report))
DEFL = SHELF_GRIP + 0.2                       # ugięcie nogi potrzebne do zwolnienia
LF_F, LF_B = wall_z(LATCH_Y) - Z_CATCH, wall_z(B - LATCH_Y, True) - Z_CATCH
eps_f, eps_b = (1.5 * LATCH_T * DEFL / lf ** 2 for lf in (LF_F, LF_B))
print(f"Trójkąt: bok {B:.1f}  wysokość ostrego wierzchołka {H:.1f}, szczyt po zaokrągleniu {Z_TOP:.1f}")
print(f"Rozwiązanie: oś środkowego ogniwa y {B_YC:.2f}, ogniwa y {[round(c, 2) for c in CY]}, moduł s {SM}, płytka s {SB_FAR}, obrót {FLIP}")
print(f"Obrys: L {L:.2f}  XC {XC:.2f}  UA {UA:.2f}  UB {UB:.2f}  zatrzaski x {LATCH_X}  płytka x {X_R - BW:.1f}..{X_R:.1f}")
print(f"Zatrzask: wolna długość nogi {LF_F:.1f} (front) / {LF_B:.1f} (tył), ugięcie {DEFL:.1f}, odkształcenie {eps_f * 100:.2f}% / {eps_b * 100:.2f}%")
print(f"Ścianki gniazd: y {CW_Y0:.2f}..{CW_Y1:.2f}, góra z {CW_TOP:.2f}; odległość płytek {L_CONT:.2f}, sprężyna {SPR_LEN:.2f} mm "
      f"przy ogniwie 44,5 ({CELL_L - (SPR_FREE - SPR_LEN):.1f}...44,5 mm: sprężyna dociska, najmniej {SPR_MIN} mm)")
print(f"Strop koszyka: z {ROOF_BOT:.2f}..{ROOF_TOP:.2f} (łuki r {ROOF_RI:.2f}/{ROOF_RO:.2f}), żebra do z {RIB_TOP}, "
      f"wycięcia na sprężyny {SPR_SLOT_W:.1f} x {SPR_SLOT_L:.1f}, ścianki gniazd do z {CW_TOP:.2f}")
print(f"Sprężyna z luzem 1 mm: zapas w oknie i nad dnem {min(spr_margin):.2f} mm; kieszeń języka {POCKET_SKIN:.2f} mm pod dnem szczelin")
print(f"Klapka: otwór x {X0:.2f}..{X1:.2f}, y {Y0:.2f}..{Y1:.2f}; z przylgą {X1 - X0 + 2 * RAB_X:.1f} x {Y1 - Y0 + 2 * RAB_Y:.1f} mm; "
      f"wkręt x {SCREW_X:.2f} y {SCREW_Y:.2f}; płaskie dno od y {W.FLAT0:.2f} do {B - W.FLAT0:.2f}")
scene["hatch_pivot_x"], scene["hatch_x0"], scene["hatch_tongue_l"] = X0 - RAB_X + HC, X0, TONGUE_L
print(f"Głośnik: środek (y {SPK_CY:.1f}, z {SPK_CZ:.1f}), r wolne {SPK_FIT:.1f} (potrzeba {SPK_POCKET / 2 + 1.9:.1f} z pierścieniem)")
scene["ctl_y"], scene["ctl_z"] = B / 2, H - 25.0
BLEND = OUT / ("obudowa-klin-5-bez-zaczepow.blend" if NOHOOK else "obudowa-klin-5.blend")
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
if "--norender" in sys.argv or NOHOOK:
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


def section_render(name, xpos, ctr, ortho):
    sec = make_section("x", xpos)
    render(name, ["Przekroj"], (-400, ctr[0], ctr[1]), (xpos, ctr[0], ctr[1]), ortho=ortho)
    drop_section(sec)


ALL = ["Korpus", "Klapka", "Pokrywa", "Kapsle", "Styki", "Baterie", "Plytka", "Plytka_przyciskow", "Wyswietlacz", "Glosnik"]
SHELL = ["Korpus", "Klapka", "Pokrywa", "Kapsle"]
CARRIED = ("Pokrywa", "Kapsle", "Plytka", "Plytka_przyciskow", "Wyswietlacz")
cx = L / 2
n_front = Vector((0, NF[0], NF[1]))
front_c = Vector((XC, *pt_slope(SM, 0)))
back_c = Vector((XC, *pt_back(SB_FAR - BH / 2, 0)))
n_back = Vector((0, NB[0], NB[1]))

render("01-przod-iso.png", SHELL, (cx + 200, -150, H * 0.8 + 120), (cx, B * 0.5, H * 0.4), lens=70)
render("02-przod-prostopadle.png", SHELL, front_c + n_front * 400, front_c, up=(0, cos_t, sin_t), ortho=100)
render("03-gora.png", SHELL, (cx, YC, 500), (cx, YC, 0), up=(0, 1, 0), ortho=100)
render("04-bok-lewy-glosnik.png", SHELL, (-300, B / 2, H / 2), (0, B / 2, H / 2), ortho=90)
render("05-bok-prawy.png", SHELL, (L + 300, B / 2, H / 2), (L, B / 2, H / 2), ortho=90)
render("06-spod.png", SHELL, (cx, B * 0.5, -300), (cx, B * 0.5, 0), up=(0, 1, 0), ortho=100)
render("07-tyl-iso.png", SHELL, (cx - 150, B + 180, H * 0.8 + 100), (cx, B * 0.5, H * 0.4), lens=70)
render("08-tyl-prostopadle.png", SHELL, back_c + n_back * 400, back_c, up=(0, -cos_t, sin_t), ortho=100)

lift = Vector((0, 0, 60))
for g in CARRIED:
    for o in GROUPS[g]:
        o.location += lift
render("09-pokrywa-zdjeta.png", ALL, (cx + 250, -190, H * 0.8 + 200), (cx, B * 0.45, H * 0.7), lens=50)
render("10-ogniwa-od-gory.png", ["Korpus", "Klapka", "Styki", "Baterie", "Glosnik"], (cx, YC, 400), (cx, YC, 0), up=(0, 1, 0), ortho=85)
render("11-koszyk-styki.png", ["Korpus", "Klapka", "Styki"], (L + 40, -30, 60), (UB - 6, YC, 6), lens=55)
render("12-pokrywa-od-srodka.png", ["Pokrywa", "Kapsle", "Plytka", "Plytka_przyciskow", "Wyswietlacz"],
       (cx + 70, B * 0.5, lift.z - 60), (cx, YC, lift.z + H * 0.5), up=(0, 1, 0), lens=40)
for g in CARRIED:
    for o in GROUPS[g]:
        o.location -= lift
section_render("13-przekroj-poprzeczny.png", XC + 3.0, (B / 2, H / 2), 85)
section_render("14-przekroj-zatrzaski.png", LATCH_X[1], (B / 2, H / 2), 85)
section_render("15-zatrzask-front-zblizenie.png", LATCH_X[1], (LATCH_Y - 1.0, 5.0), 16)
section_render("16-przekroj-przycisk-plus.png", XC + BTN_X["plus"] - BB_W / 2, (YC, Z_TOP - 12), 34)
render("17-przyciski-zblizenie.png", SHELL, (XC + 55, YC - 70, Z_TOP + 60), (XC, YC, Z_TOP - 2), lens=95)
section_render("18-kapsel-gniazdo.png", XC + BTN_X["plus"] - BB_W / 2, (YC, ZB + 6.5), 14)
section_render("19-przekroj-gniazda-styku.png", UB + 0.2, (B / 2, 10), 70)
section_render("20-szew-tylu-zblizenie.png", XC + 10.0, (B - 7.0, 4.5), 16)



def section_y(name, ypos, ctr, ortho):
    """Przekrój płaszczyzną y = ypos (zostaje część od tyłu), widok od frontu; ctr = (x, z)."""
    sec = make_section("y", ypos)
    render(name, ["Przekroj"], (ctr[0], ypos - 400, ctr[1]), (ctr[0], ypos, ctr[1]), ortho=ortho)
    drop_section(sec)


# klapka: widok od spodu z klapką zdjętą i odsuniętą, przekroje przez język i wkręt
GROUPS["Klapka"][0].location += Vector((0, 0, -25))
render("21-klapka-zdjeta-od-spodu.png", ["Korpus", "Klapka", "Styki", "Baterie"], (cx + 110, -120, -170), (cx, YC, -8), lens=55)
GROUPS["Klapka"][0].location -= Vector((0, 0, -25))
render("22-spod-klapka.png", ["Korpus", "Klapka"], (cx + 60, YC - 90, -140), (cx, YC, 0), lens=60)
section_y("23-przekroj-klapki-wzdluz.png", SCREW_Y + 0.01, (L / 2, 14.0), 80)
section_y("24-jezyk-klapki-zblizenie.png", SCREW_Y + 0.01, (X0 - 1.0, 4.0), 14)
section_y("25-wkret-klapki-zblizenie.png", SCREW_Y + 0.01, (SCREW_X - 2.0, 4.5), 16)
render("26-strop-koszyka.png", ["Korpus", "Klapka", "Styki", "Glosnik"], (cx + 90, -95, 130), (cx, YC, 8), lens=50)
section_render("27-przekroj-stropu.png", XC - 6.0, (YC - 2, 9.0), 46)

for ob in bpy.data.objects:
    ob.hide_render = False
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
print("GOTOWE")
