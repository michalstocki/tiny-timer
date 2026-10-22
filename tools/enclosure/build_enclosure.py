"""Parametryczna obudowa minutnika (iteracja 2), model w Blenderze. 1 jednostka = 1 mm.

Uruchomienie (bez okna):
    /Applications/Blender.app/Contents/MacOS/Blender --background \
        --python tools/enclosure/build_enclosure.py

Wejście: docs/pcb/pcb-layout.json (zarys płytki, otwory, elementy, wysokości).
Wyjście: docs/obudowa/ (.blend, STL każdej części, rendery).

Układ współrzędnych jak w specyfikacji płytki: widok z przodu, początek w lewym
dolnym rogu płytki, +x w prawo, +y w górę, +z w stronę użytkownika (przód).
Górna powierzchnia laminatu to z = 0, dolna z = -1.6.

Bryła: płaski stos, dłuższa krawędź wzdłuż x (równolegle do wyświetlacza).
Dwie części korpusu, rozdzielone w płaszczyźnie Z_SPLIT:
  - czara przednia: panel z oknem OLED i kapslami, komora elektroniki, płytka
    na 4 słupkach (zostaje w czarze po otwarciu, tył płytki jest odsłonięty),
  - blok tylny: przegroda, koszyk 3xAAA (kanały ułożone wzdłuż x, ogniwa wzdłuż y,
    czyli w poprzek wyświetlacza), głośnik, 4 otwory na wkręty M2.5 od tyłu.
"""
import json
import math
import struct
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[2]
LAYOUT = ROOT / "docs/pcb/pcb-layout.json"
OUT = ROOT / "docs/obudowa"
RENDERS = OUT / "renders"

# ---------------------------------------------------------------- parametry
layout = json.loads(LAYOUT.read_text())
BW, BH, BT = (layout["board"][k] for k in ("width", "height", "thickness"))
HOLES = [(h["x"], h["y"], h["diameter"]) for h in layout["mounting_holes"]]
OLED = layout["parts"]["OLED"]["body"]
GLASS = layout["derived"]["oled_module"]["glass_rect"]
BUTTONS = {k: v["centre"] for k, v in layout["derived"]["buttons"].items()}
BTN_LABEL = {k: v["label"] for k, v in layout["derived"]["buttons"].items()}

WALL = 2.0           # ścianki boczne
PANEL = 1.6          # panel przedni
GAP = 1.5            # luz płytki do ścianki komory (tolerancja zarysu ±0.3)
R_OUT = 6.0          # promień pionowych narożników
R_TOP = R_OUT        # zaokrąglenie krawędzi frontu: takie samo jak krawędzi pionowych
R_BOT = 1.5          # zaokrąglenie krawędzi tyłu (większe zabierałoby miejsce klapce i łbom wkrętów)
Z_PANEL_IN = 6.8     # wewnętrzna powierzchnia panelu (OLED 6.5, trzpień 7.3)
Z_FRONT = Z_PANEL_IN + PANEL
Z_SPLIT = -(BT + 9.0 + 0.6)          # płaszczyzna podziału: obwiednia tyłu płytki 9.0 + luz
PART_T = 1.6                         # przegroda bloku tylnego
Z_PART_BOT = Z_SPLIT - PART_T

# koszyk AAA (Ø10.5 x 44.5): trzy kanały obok siebie wzdłuż x, ogniwa wzdłuż y
CELL_D, CELL_L = 10.5, 44.5
CAV_L = 51.0                         # długość wnęki: ogniwo + sprężyna + płytki styków
CH_W, DIV, CH_DEPTH = 11.0, 1.2, 11.0
BACK_WALL = 1.6
Z_POCKET_BOT = Z_PART_BOT - CH_DEPTH
Z_BACK = Z_POCKET_BOT - BACK_WALL
CELL_ZC = Z_POCKET_BOT + CELL_D / 2

# głośnik Ø26.5 x 9
SPK_D, SPK_H, SPK_POCKET = 26.5, 9.0, 27.0
SPK_STRIP = SPK_POCKET + 0.8

# wkręty łączące części: M2.5 od tyłu, łeb Ø4.6 w zagłębieniu Ø4.8
SCREW_BORE_R, SCREW_HOLE_R, SCREW_BORE_DEPTH = 2.4, 1.35, 3.5
SCREW_PILOT_R, SCREW_PILOT_DEPTH = 1.05, 9.5
BOSS_R = 3.0
WL = 8.8             # lewa ściana bloku: mieści zagłębienia wkrętów i margines klapki

# obrys
TRAY_W = 3 * CH_W + 2 * DIV
BODY_L = WL + TRAY_W + WALL + SPK_STRIP + WALL
XC = BW / 2
XL, XR = XC - BODY_L / 2, XC + BODY_L / 2
Y_IN0, Y_IN1 = -GAP, BH + GAP                  # wnętrze komory w y
Y0, Y1 = Y_IN0 - WALL, Y_IN1 + WALL
TX0 = XL + WL                                  # koszyk: początek wnęki w x
TX1 = TX0 + TRAY_W
CH_X = [(TX0 + i * (CH_W + DIV), TX0 + i * (CH_W + DIV) + CH_W) for i in range(3)]
CH_XC = [(a + b) / 2 for a, b in CH_X]
CY0 = BH / 2 - CAV_L / 2                       # wnęka koszyka w y (środek na osi płytki)
CY1 = CY0 + CAV_L
SPK_X_IN1 = XR - WALL
SPK_CX = SPK_X_IN1 + 0.2 - SPK_POCKET / 2
SPK_CY = BH / 2
SCREWS = [(XL + 4.3, 5.0), (XL + 4.3, BH - 5.0), (XR - 4.3, 5.0), (XR - 4.3, BH - 5.0)]

CAP_R, CAP_FLANGE_R, CAP_TOP, CAP_BOT = 4.8, 5.9, Z_FRONT + 1.4, 6.0
PANEL_HOLE_R = 5.1
R_WIN = (GLASS[3] - GLASS[1] + 0.6) / 2 - 0.005   # półkole: promień = połowa wysokości okna (o 5 µm mniej, by uniknąć zdublowanych punktów)

# ---------------------------------------------------------------- narzędzia
scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 0.001
scene.unit_settings.length_unit = "MILLIMETERS"

COLL = {}


def coll(name):
    if name not in COLL:
        c = bpy.data.collections.new(name)
        scene.collection.children.link(c)
        COLL[name] = c
    return COLL[name]


def finish(name, bm, group, color):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    coll(group).objects.link(ob)
    ob.color = color
    ob["grupa"] = group
    return ob


def box_bm(x0, y0, z0, x1, y1, z1):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(x1 - x0, y1 - y0, z1 - z0), verts=bm.verts)
    bmesh.ops.translate(bm, vec=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), verts=bm.verts)
    return bm


def box(name, x0, y0, z0, x1, y1, z1, group="tmp", color=(1, 1, 1, 1)):
    return finish(name, box_bm(x0, y0, z0, x1, y1, z1), group, color)


def cyl_bm(cx, cy, z0, z1, r, r2=None, seg=48, axis="Z"):
    """Walec/stożek. axis="Z": środek (cx,cy), zakres z0..z1.
    axis="Y": oś wzdłuż y; (cx,cy) to (x,z) środka, zakres y to z0..z1."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg,
                          radius1=r, radius2=r if r2 is None else r2, depth=abs(z1 - z0))
    if axis == "Y":      # promień r przy mniejszym y
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(-math.pi / 2, 3, "X"))
        bmesh.ops.translate(bm, vec=(cx, (z0 + z1) / 2, cy), verts=bm.verts)
    else:
        bmesh.ops.translate(bm, vec=(cx, cy, (z0 + z1) / 2), verts=bm.verts)
    return bm


def cyl(name, cx, cy, z0, z1, r, group="tmp", color=(1, 1, 1, 1), **kw):
    return finish(name, cyl_bm(cx, cy, z0, z1, r, **kw), group, color)


def prism_bm(pts, z0, z1):
    bm = bmesh.new()
    n = len(pts)
    b = [bm.verts.new((x, y, z0)) for x, y in pts]
    t = [bm.verts.new((x, y, z1)) for x, y in pts]
    bm.faces.new(b[::-1])
    bm.faces.new(t)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((b[i], b[j], t[j], t[i]))
    return bm


def rrect_pts(x0, y0, x1, y1, r, seg=14):
    pts = []
    for cx, cy, a0 in ((x1 - r, y0 + r, 270), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        for k in range(seg + 1):
            a = math.radians(a0 + 90 * k / seg)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def rrect_bm(x0, y0, z0, x1, y1, z1, r):
    return prism_bm(rrect_pts(x0, y0, x1, y1, r), z0, z1)


def loft_profile_bm(x0, y0, x1, y1, r_out, prof, min_r=0.3):
    """Bryła warstwami: prof to lista (z, wcięcie od obrysu), od dołu do góry. Promień
    narożnika w warstwie = r_out - wcięcie (powierzchnie współśrodkowe), nie mniej niż min_r."""
    bm = bmesh.new()
    rings = []
    for z, d in prof:
        pts = rrect_pts(x0 + d, y0 + d, x1 - d, y1 - d, max(r_out - d, min_r))
        rings.append([bm.verts.new((x, y, z)) for x, y in pts])
    n = len(rings[0])
    for a_, b_ in zip(rings, rings[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((a_[i], a_[j], b_[j], b_[i]))
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[-1])
    return bm


def top_arc(z_top, r, inset0, seg):
    """łuk kołowy krawędzi górnej: od ściany (wcięcie inset0) do płaszczyzny z_top (wcięcie inset0 + r)"""
    return [(z_top - r + r * math.sin(math.pi / 2 * k / seg), inset0 + r * (1 - math.cos(math.pi / 2 * k / seg)))
            for k in range(seg + 1)]


def loft_block_bm(x0, y0, x1, y1, z0, z1, r_out, r_bot, r_top, seg_bot=8, seg_top=24):
    """Zaokrąglony prostopadłościan: pionowe narożniki r_out, krawędź dolna r_bot, górna r_top (0 = ostra)."""
    prof = []
    if r_bot > 0:
        for k in range(seg_bot + 1):
            f = math.pi / 2 * k / seg_bot
            prof.append((z0 + r_bot * (1 - math.cos(f)), r_bot * (1 - math.sin(f))))
    else:
        prof.append((z0, 0.0))
    prof += top_arc(z1, r_top, 0.0, seg_top) if r_top > 0 else [(z1, 0.0)]
    return loft_profile_bm(x0, y0, x1, y1, r_out, prof)


def evaluated_mesh(ob):
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    return bpy.data.meshes.new_from_object(ob.evaluated_get(dg))


def boolean(target, cutter, op="DIFFERENCE", keep=False):
    m = target.modifiers.new("bool", "BOOLEAN")
    m.operation, m.object, m.solver = op, cutter, "EXACT"
    new = evaluated_mesh(target)
    old = target.data
    target.data = new
    target.modifiers.remove(m)
    bpy.data.meshes.remove(old)
    if not keep:
        bpy.data.objects.remove(cutter, do_unlink=True)


def cut(target, *cutters):
    for c in cutters:
        boolean(target, c)


def union(target, *parts):
    for p in parts:
        boolean(target, p, "UNION")


def text_cutter(txt, size, x, y, z0, depth):
    cu = bpy.data.curves.new("txt", "FONT")
    cu.body, cu.size, cu.align_x, cu.align_y = txt, size, "CENTER", "CENTER"
    cu.extrude = depth / 2
    ob = bpy.data.objects.new("txt", cu)
    coll("tmp").objects.link(ob)
    bpy.context.view_layer.update()
    me = evaluated_mesh(ob)
    bpy.data.objects.remove(ob, do_unlink=True)
    ob2 = bpy.data.objects.new("txt_mesh", me)
    ob2.location = (x, y, z0 + depth / 2)
    coll("tmp").objects.link(ob2)
    return ob2


C_BODY = (0.90, 0.89, 0.84, 1)
C_DARK = (0.22, 0.24, 0.27, 1)
C_ORANGE = (0.95, 0.45, 0.15, 1)
LID_C = (0.28, 0.30, 0.33, 1)

# ---------------------------------------------------------------- czara przednia
bm = loft_block_bm(XL, Y0, XR, Y1, Z_SPLIT, Z_FRONT, R_OUT, 0.0, R_TOP)
front = finish("Obudowa_przod", bm, "Przod", C_BODY)

# komora elektroniki otwarta od tyłu; sufit zaokrąglony współśrodkowo z frontem (grubość ścianki stała)
R_IN = R_TOP - WALL
cavity_prof = [(Z_SPLIT - 0.5, WALL), (Z_PANEL_IN - R_IN, WALL)] + top_arc(Z_PANEL_IN, R_IN, WALL, 24)[1:]
cut(front, finish("komora", loft_profile_bm(XL, Y0, XR, Y1, R_OUT, cavity_prof), "tmp", (1,) * 4))

# okno OLED (szkło + 0.3 mm luzu na stronę) i otwory pod kapsle
# końce okna to półkola (R_WIN); zasłaniają rogi szkła, ale nie aktywny obszar 22.4 x 5.6 mm (margines ok. 0.7 mm)
cut(front, finish("okno", rrect_bm(GLASS[0] - 0.3, GLASS[1] - 0.3, Z_PANEL_IN - 0.5, GLASS[2] + 0.3, GLASS[3] + 0.3, Z_FRONT + 0.5, R_WIN), "tmp", (1,) * 4))
for k, (bx, by) in BUTTONS.items():
    cut(front, cyl("otw", bx, by, Z_PANEL_IN - 0.5, Z_FRONT + 0.5, PANEL_HOLE_R))

# słupki płytki (od frontu) i słupki pod wkręty łączące; przycięte do zewnętrznej powierzchni czary,
# bo przy dużym zaokrągleniu frontu przy ściankach powierzchnia zewnętrzna jest niżej niż sufit
# (słupki sięgają ponad front i są przycinane przez INTERSECT, dzięki czemu nie ma styku wzdłuż linii)
feat = None
for hx, hy, _ in HOLES:
    p_ = cyl("slupek", hx, hy, 0.0, Z_FRONT + 0.5, 2.9, seg=32)
    feat = p_ if feat is None else (union(feat, p_) or feat)
for sx, sy in SCREWS:
    union(feat, cyl("boss", sx, sy, Z_SPLIT, Z_FRONT + 0.5, BOSS_R, seg=32))
boolean(feat, finish("obrys", loft_block_bm(XL, Y0, XR, Y1, Z_SPLIT, Z_FRONT, R_OUT, 0.0, R_TOP), "tmp", (1,) * 4), "INTERSECT")
union(front, feat)
for hx, hy, _ in HOLES:
    cut(front, cyl("pilot", hx, hy, -0.1, 5.2, 1.05, seg=24))
for sx, sy in SCREWS:
    cut(front, cyl("pilot_w", sx, sy, Z_SPLIT - 0.5, Z_SPLIT + SCREW_PILOT_DEPTH, SCREW_PILOT_R, seg=24))

# napis nad wyświetlaczem (grawer 0.4 mm)
cut(front, text_cutter("TINY TIMER", 5.0, BW / 2, 44.5, Z_FRONT - 0.4, 1.0))

# ---------------------------------------------------------------- blok tylny
bm = loft_block_bm(XL, Y0, XR, Y1, Z_BACK, Z_SPLIT, R_OUT, R_BOT, 0.0)
rear = finish("Obudowa_tyl", bm, "Tyl", C_BODY)

# koszyk: trzy kanały otwarte do tyłu, dzielniki, okno na baterie, wpust klapki
for xa, xb in CH_X:
    cut(rear, box("kanal", xa, CY0, Z_POCKET_BOT, xb, CY1, Z_PART_BOT))
WIN_X = (TX0 + 0.05, TX1 - 0.05)
WIN_Y = (CY0 + 1.25, CY1 - 1.25)
cut(rear, box("okno_bat", WIN_X[0], WIN_Y[0], Z_BACK - 0.5, WIN_X[1], WIN_Y[1], Z_POCKET_BOT + 0.3))
REC_X = (WIN_X[0] - 0.9, WIN_X[1] + 0.9)
REC_Y = (WIN_Y[0] - 1.0, WIN_Y[1] + 1.0)
cut(rear, box("wpust_bat", REC_X[0], REC_Y[0], Z_BACK - 0.5, REC_X[1], REC_Y[1], Z_BACK + 0.8))
# szczeliny w dzielnikach na łączniki szeregowe (koniec y wysokie: dzielnik 1, y niskie: dzielnik 2)
d1 = (CH_X[0][1], CH_X[1][0])
d2 = (CH_X[1][1], CH_X[2][0])
cut(rear, box("sz1", d1[0], CY1 - 0.7, Z_POCKET_BOT, d1[1], CY1 + 0.1, Z_PART_BOT),
    box("sz2", d2[0], CY0 - 0.1, Z_POCKET_BOT, d2[1], CY0 + 0.7, Z_PART_BOT))
# gniazda zatrzasków klapki: po jednym na bocznych ścianach koszyka, przy niskim końcu y
HK_Y = (CY0 + 1.5, CY0 + 5.0)
cut(rear, box("zat1", TX0 - 0.6, HK_Y[0] - 0.5, Z_POCKET_BOT + 1.2, TX0, HK_Y[1] + 0.5, Z_POCKET_BOT + 3.2),
    box("zat2", TX1, HK_Y[0] - 0.5, Z_POCKET_BOT + 1.2, TX1 + 0.6, HK_Y[1] + 0.5, Z_POCKET_BOT + 3.2))
# wyżłobienie pod palec przy wysokim końcu y klapki
cut(rear, cyl("palec", (TX0 + TX1) / 2, CY1 + 2.0, Z_BACK - 0.5, Z_BACK + 0.8, 4.5, seg=40))

# głośnik: kieszeń + otwory dźwiękowe w tylnej ściance
cut(rear, cyl("kiesz_glosnik", SPK_CX, SPK_CY, Z_POCKET_BOT, Z_PART_BOT, SPK_POCKET / 2, seg=96))
holes = [(0.0, 0.0)]
holes += [(4.5 * math.cos(2 * math.pi * i / 8 + 0.2), 4.5 * math.sin(2 * math.pi * i / 8 + 0.2)) for i in range(8)]
holes += [(9.0 * math.cos(2 * math.pi * i / 14), 9.0 * math.sin(2 * math.pi * i / 14)) for i in range(14)]
for dx, dy in holes:
    cut(rear, cyl("dzw", SPK_CX + dx, SPK_CY + dy, Z_BACK - 0.5, Z_POCKET_BOT + 0.3, 1.0, seg=16))

# przepusty przewodów w przegrodzie: bateria (oba końce koszyka) i głośnik
cut(rear, cyl("prz1", CH_XC[0], CY0 + 1.0, Z_PART_BOT - 0.5, Z_SPLIT + 0.5, 1.5, seg=24),
    cyl("prz2", CH_XC[2], CY1 - 1.0, Z_PART_BOT - 0.5, Z_SPLIT + 0.5, 1.5, seg=24),
    cyl("prz3", SPK_CX - 9.7, SPK_CY + 8.5, Z_PART_BOT - 0.5, Z_SPLIT + 0.5, 2.0, seg=24))

# wkręty łączące: otwór przelotowy + zagłębienie na łeb od tyłu
for sx, sy in SCREWS:
    cut(rear, cyl("w_otw", sx, sy, Z_BACK - 0.5, Z_SPLIT + 0.5, SCREW_HOLE_R, seg=24),
        cyl("w_lb", sx, sy, Z_BACK - 0.5, Z_BACK + SCREW_BORE_DEPTH, SCREW_BORE_R, seg=32))

# wypust centrujący: cienki kołnierz wchodzący do czary (z przerwami na słupki wkrętów)
ring = finish("wypust", rrect_bm(XL + WALL + 0.2, Y_IN0 + 0.2, Z_SPLIT - 0.1, XR - WALL - 0.2, Y_IN1 - 0.2, Z_SPLIT + 2.0, 3.8), "tmp", (1,) * 4)
cut(ring, finish("wypust_w", rrect_bm(XL + WALL + 1.2, Y_IN0 + 1.2, Z_SPLIT - 0.5, XR - WALL - 1.2, Y_IN1 - 1.2, Z_SPLIT + 3.0, 2.8), "tmp", (1,) * 4))
for sx, sy in SCREWS:
    cut(ring, cyl("wypust_s", sx, sy, Z_SPLIT - 0.5, Z_SPLIT + 3.0, BOSS_R + 0.4, seg=32))
union(rear, ring)

# ---------------------------------------------------------------- klapka koszyka (z zapasem do krawędzi)
lid = finish("Klapka_baterii", box_bm(REC_X[0] + 0.25, REC_Y[0] + 0.25, Z_BACK, REC_X[1] - 0.25, REC_Y[1] - 0.25, Z_BACK + 0.8), "Klapka", LID_C)
union(lid, box("wtyk", WIN_X[0] + 0.25, WIN_Y[0] + 0.25, Z_BACK + 0.8, WIN_X[1] - 0.25, WIN_Y[1] - 0.25, Z_POCKET_BOT))
xl = WIN_X[0] + 0.25      # języki przy bocznych krawędziach wtyku
xh = WIN_X[1] - 0.25
union(lid,
      box("jezyk1", xl, HK_Y[0], Z_POCKET_BOT, xl + 0.8, HK_Y[1], Z_POCKET_BOT + 3.0),
      box("zab1", TX0 - 0.4, HK_Y[0], Z_POCKET_BOT + 1.4, xl + 0.1, HK_Y[1], Z_POCKET_BOT + 2.9),
      box("jezyk2", xh - 0.8, HK_Y[0], Z_POCKET_BOT, xh, HK_Y[1], Z_POCKET_BOT + 3.0),
      box("zab2", xh - 0.1, HK_Y[0], Z_POCKET_BOT + 1.4, TX1 + 0.4, HK_Y[1], Z_POCKET_BOT + 2.9))

# ---------------------------------------------------------------- kapsle przycisków
CAP_COLORS = {"minus": C_DARK, "run": C_ORANGE, "plus": C_DARK}
caps = []
for k, (bx, by) in BUTTONS.items():
    lab = BTN_LABEL[k]
    cap = cyl("Kapsel_" + lab, bx, by, CAP_BOT, CAP_TOP, CAP_R, "Kapsle", CAP_COLORS[lab], seg=48)
    union(cap, cyl("kolnierz", bx, by, CAP_BOT, CAP_BOT + 0.6, CAP_FLANGE_R, seg=48))
    cut(cap, box("gniazdo", bx - 2.0, by - 2.0, CAP_BOT - 0.1, bx + 2.0, by + 2.0, 7.3))
    zt = CAP_TOP - 0.4
    if lab == "minus":
        cut(cap, box("m", bx - 2.2, by - 0.5, zt, bx + 2.2, by + 0.5, CAP_TOP + 0.1))
    elif lab == "plus":
        cut(cap, box("p1", bx - 2.2, by - 0.5, zt, bx + 2.2, by + 0.5, CAP_TOP + 0.1),
            box("p2", bx - 0.5, by - 2.2, zt, bx + 0.5, by + 2.2, CAP_TOP + 0.1))
    else:
        cut(cap, finish("tri", prism_bm([(bx - 1.6, by - 2.1), (bx + 2.3, by), (bx - 1.6, by + 2.1)], zt, CAP_TOP + 0.1), "tmp", (1,) * 4))
    caps.append(cap)

# ---------------------------------------------------------------- styki i baterie (podgląd)
C_NICKEL = (0.78, 0.74, 0.62, 1)
C_CELL = (0.20, 0.42, 0.72, 1)
C_GOLD = (0.85, 0.65, 0.20, 1)
SPR_R = 3.0
swap = [False, True, False]        # ogniwo 2 odwrócone (połączenie szeregowe)
for i, xc in enumerate(CH_XC):
    if not swap[i]:
        c0, c1 = CY0 + 6.0, CY0 + 6.0 + CELL_L           # ogniwo: minus (sprężyna) przy niskim y
        body = (c0, c1 - 0.8)
        nub = (c1 - 0.8, c1)
    else:
        c0, c1 = CY0 + 0.5, CY0 + 0.5 + CELL_L           # odwrócone: plus przy niskim y
        body = (c0 + 0.8, c1)
        nub = (c0, c0 + 0.8)
    finish(f"AAA_{i + 1}", cyl_bm(xc, CELL_ZC, body[0], body[1], CELL_D / 2, axis="Y"), "Baterie", C_CELL)
    finish(f"AAA_{i + 1}_plus", cyl_bm(xc, CELL_ZC, nub[0], nub[1], 2.0, axis="Y"), "Baterie", C_GOLD)


def plate(name, y_end, xa, xb):
    """płytka styku przy końcu wnęki (y_end = CY0 lub CY1), od xa do xb"""
    ya, yb = (y_end, y_end + 0.5) if y_end == CY0 else (y_end - 0.5, y_end)
    return box(name, xa, ya, CELL_ZC - 4.5, xb, yb, CELL_ZC + 4.5, "Styki", C_NICKEL)


def spring(name, xc, from_low_end):
    """sprężyna (Keystone 5204): stożek od płytki do ogniwa, szeroki przy płytce"""
    if from_low_end:
        return finish(name, cyl_bm(xc, CELL_ZC, CY0 + 0.5, CY0 + 6.0, SPR_R, r2=SPR_R * 0.55, axis="Y", seg=32), "Styki", C_NICKEL)
    return finish(name, cyl_bm(xc, CELL_ZC, CY0 + 0.5 + CELL_L, CY1 - 0.5, SPR_R * 0.55, r2=SPR_R, axis="Y", seg=32), "Styki", C_NICKEL)


x1, x2, x3 = CH_XC
spring("sprezyna_1", x1, True)
plate("plytka_1_neg", CY0, x1 - 4.5, x1 + 4.5)
spring("sprezyna_3", x3, True)
plate("plytka_lacznik_niski", CY0, x2 - 4.5, x3 + 4.5)       # ogniwo 3 (-) + ogniwo 2 (+)
spring("sprezyna_2", x2, False)
plate("plytka_lacznik_wysoki", CY1, x1 - 4.5, x2 + 4.5)      # ogniwo 1 (+) + ogniwo 2 (-)
plate("plytka_3_pos", CY1, x3 - 4.5, x3 + 4.5)

# ---------------------------------------------------------------- podgląd płytki i elementów (nie do wydruku)
C_PCB, C_BLACK, C_PART = (0.10, 0.42, 0.22, 1), (0.04, 0.04, 0.05, 1), (0.55, 0.40, 0.25, 1)
pcb = finish("PCB", rrect_bm(0, 0, -BT, BW, BH, 0, 3.0), "Plytka", C_PCB)
for hx, hy, hd in HOLES:
    cut(pcb, cyl("o", hx, hy, -BT - 0.5, 0.5, hd / 2, seg=24))
box("OLED_modul", OLED[0], OLED[1], 2.5, OLED[2], OLED[3], 6.5, "Plytka", C_BLACK)
box("OLED_szklo", GLASS[0], GLASS[1], 6.3, GLASS[2], GLASS[3], 6.5, "Plytka", (0.10, 0.20, 0.45, 1))
for k, (bx, by) in BUTTONS.items():
    box("B3F_" + k, bx - 6, by - 6, 0, bx + 6, by + 6, 4.3, "Plytka", (0.15, 0.15, 0.17, 1))
    cyl("B3F_podstawa_" + k, bx, by, 4.3, 5.5, 3.55, "Plytka", (0.3, 0.3, 0.32, 1), seg=32)
    box("B3F_trzpien_" + k, bx - 1.9, by - 1.9, 5.5, bx + 1.9, by + 1.9, 7.3, "Plytka", (0.8, 0.8, 0.82, 1))
HEIGHT_OVERRIDE = {"U1": 8.5}
for name, p in layout["parts"].items():
    if p["side"] != "bottom":
        continue
    h = HEIGHT_OVERRIDE.get(name, p["height_above_board"])
    if h <= 0:
        continue
    bx0, by0, bx1, by1 = p["body"]
    box("el_" + name, bx0, by0, -BT - h, bx1, by1, -BT, "Plytka", C_PART)
cyl("Glosnik_ramka", SPK_CX, SPK_CY, Z_PART_BOT - 4.0, Z_PART_BOT, SPK_D / 2, "Glosnik", (0.12, 0.12, 0.13, 1), seg=96)
cyl("Glosnik_stozek", SPK_CX, SPK_CY, Z_PART_BOT - SPK_H, Z_PART_BOT - 4.0, 10.0, "Glosnik", (0.2, 0.2, 0.22, 1), seg=64)

# ---------------------------------------------------------------- kontrola i eksport
def manifold_report(ob):
    bmm = bmesh.new()
    bmm.from_mesh(ob.data)
    bad = sum(1 for e in bmm.edges if not e.is_manifold)
    vol = bmm.calc_volume()
    bmm.free()
    return bad, vol


def write_stl(path, objs):
    tris = []
    for ob in objs:
        me = evaluated_mesh(ob)
        bmm = bmesh.new()
        bmm.from_mesh(me)
        bmesh.ops.triangulate(bmm, faces=bmm.faces)
        for f in bmm.faces:
            tris.append((f.normal.copy(), [v.co.copy() for v in f.verts]))
        bmm.free()
        bpy.data.meshes.remove(me)
    with open(path, "wb") as fh:
        fh.write(b"tiny-timer obudowa, mm".ljust(80, b" "))
        fh.write(struct.pack("<I", len(tris)))
        for n, vs in tris:
            fh.write(struct.pack("<12fH", n.x, n.y, n.z, *[c for v in vs for c in (v.x, v.y, v.z)], 0))


printable = {
    "obudowa-przod": [front],
    "obudowa-tyl": [rear],
    "klapka-baterii": [lid],
    "kapsle": caps,
}
OUT.mkdir(parents=True, exist_ok=True)
RENDERS.mkdir(parents=True, exist_ok=True)
for old in ("korpus.stl", "pokrywa-ukladu.stl"):
    (OUT / old).unlink(missing_ok=True)
report = []
for fname, objs in printable.items():
    write_stl(OUT / f"{fname}.stl", objs)
    for ob in objs:
        bad, vol = manifold_report(ob)
        d = ob.dimensions
        report.append(f"{ob.name:18s} wymiary {d.x:6.1f} x {d.y:5.1f} x {d.z:5.1f} mm  objętość {vol:9.1f} mm3  krawędzie nie-rozmaitościowe: {bad}")
print("\n".join(report))
print(f"Obrys: x {XL:.1f}..{XR:.1f} ({BODY_L:.1f})  y {Y0:.1f}..{Y1:.1f} ({Y1 - Y0:.1f})  z {Z_BACK:.1f}..{Z_FRONT:.1f} ({Z_FRONT - Z_BACK:.1f}), podział z={Z_SPLIT:.1f}")
print(f"Kanały (x): {[(round(a, 1), round(b, 1)) for a, b in CH_X]}  wnęka y {CY0:.1f}..{CY1:.1f}  głośnik ({SPK_CX:.1f}, {SPK_CY:.1f})")
print(f"Wkręty: {[(round(x, 1), round(y, 1)) for x, y in SCREWS]}")

# ---------------------------------------------------------------- rendery
GROUPS = {}
for ob in bpy.data.objects:
    GROUPS.setdefault(ob.get("grupa", ""), []).append(ob)

world = bpy.data.worlds.new("w")
world.color = (0.94, 0.95, 0.97)
scene.world = world
scene.render.engine = "BLENDER_EEVEE"
scene.eevee.taa_render_samples = 48
for ob in bpy.data.objects:
    if ob.type == "MESH" and all(m is None for m in ob.data.materials):
        ob.data.materials.clear()          # boolean zostawia puste sloty
        mat = bpy.data.materials.new(ob.name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = ob.color
        bsdf.inputs["Roughness"].default_value = 0.55
        ob.data.materials.append(mat)


def smooth(ob):
    """gładkie cieniowanie, ostre krawędzie tylko powyżej 35° (zaokrąglenia przestają wyglądać jak fasety)"""
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
    sun.hide_render = False
    cam_data.type = "ORTHO" if ortho else "PERSP"
    if ortho:
        cam_data.ortho_scale = ortho
    else:
        cam_data.lens = lens
    cam_data.clip_start, cam_data.clip_end = 1, 2000
    aim(loc, tgt, up)
    scene.render.filepath = str(RENDERS / name)
    bpy.ops.render.render(write_still=True)


def make_section(axis, pos):
    """Kopie wszystkich brył z odciętą połową (zostaje część >pos)."""
    big = 400
    out = []
    for g in ("Przod", "Tyl", "Klapka", "Kapsle", "Styki", "Baterie", "Plytka", "Glosnik"):
        for o in GROUPS.get(g, []):
            dup = o.copy()
            dup.data = o.data.copy()
            coll("Przekroj").objects.link(dup)
            dup["grupa"] = "Przekroj"
            if axis == "y":
                c = box("pl", -big, pos - big, -big, big, pos, big)
            else:
                c = box("pl", pos - big, -big, -big, pos, big, big)
            boolean(dup, c)
            smooth(dup)
            out.append(dup)
    GROUPS["Przekroj"] = out
    return out


def drop_section(objs):
    for o in objs:
        bpy.data.objects.remove(o, do_unlink=True)
    GROUPS["Przekroj"] = []


cx, cy = XC, BH / 2
zmid = (Z_FRONT + Z_BACK) / 2
ALL = ["Przod", "Tyl", "Klapka", "Kapsle", "Styki", "Baterie", "Plytka", "Glosnik"]
render("01-przod-iso.png", ["Przod", "Tyl", "Kapsle"], (cx + 120, cy - 190, 200), (cx, cy, 0), lens=70)
render("02-przod.png", ["Przod", "Tyl", "Kapsle"], (cx, cy, 300), (cx, cy, 0), up=(0, 1, 0), ortho=100)
render("03-tyl-iso.png", ["Przod", "Tyl", "Klapka", "Kapsle"], (cx - 110, cy - 200, -200), (cx, cy, zmid), lens=70)
render("04-tyl-koszyk-otwarty.png", ["Przod", "Tyl", "Kapsle", "Styki", "Baterie", "Glosnik"], (cx - 110, cy - 200, -200), (cx, cy, zmid), lens=70)
render("05-tyl-prosto.png", ["Przod", "Tyl", "Klapka"], (cx, cy, -300), (cx, cy, 0), up=(0, 1, 0), ortho=100)
render("06-bok.png", ["Przod", "Tyl", "Klapka", "Kapsle"], (cx, -300, zmid), (cx, cy, zmid), ortho=100)
render("07-otwarta-plytka.png", ["Przod", "Kapsle", "Plytka"], (cx - 60, cy - 150, -140), (cx, cy, 0), lens=70)
for g in ("Tyl", "Klapka", "Styki", "Baterie", "Glosnik"):
    for o in GROUPS[g]:
        o.location.z = -38.0
render("08-rozlozona.png", ALL, (cx + 150, cy - 200, 80), (cx, cy, -22), lens=60)
for g in ("Tyl", "Klapka", "Styki", "Baterie", "Glosnik"):
    for o in GROUPS[g]:
        o.location.z = 0.0
sec = make_section("y", cy)
render("09-przekroj-poprzeczny.png", ["Przekroj"], (cx, -300, zmid), (cx, cy, zmid), ortho=100)
drop_section(sec)
sec = make_section("x", CH_XC[1])
render("10-przekroj-koszyk.png", ["Przekroj"], (-300, cy, zmid), (CH_XC[1], cy, zmid), ortho=95)
drop_section(sec)

for ob in bpy.data.objects:
    ob.hide_render = False
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "obudowa.blend"))
print("GOTOWE")
