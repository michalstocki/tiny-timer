"""Wspólne funkcje pomocnicze dla skryptów bpy (obudowa klin). 1 jednostka = 1 mm.

Funkcje są skopiowane z build_enclosure.py (iteracja 2) i rozszerzone o walec wzdłuż X, profil
wielokąta wyciągany wzdłuż X, zaokrąglanie narożników wielokąta 2D i modyfikator Bevel.
Iteracja 2 zostaje bez zmian, żeby jej wynik dało się odtworzyć.
"""
import math
import struct

import bmesh
import bpy
from mathutils import Matrix

COLL = {}
TMP = (1, 1, 1, 1)


def init_scene():
    scene = bpy.context.scene
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 0.001
    scene.unit_settings.length_unit = "MILLIMETERS"
    COLL.clear()
    return scene


def coll(name):
    if name not in COLL:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
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


def box(name, x0, y0, z0, x1, y1, z1, group="tmp", color=TMP):
    return finish(name, box_bm(x0, y0, z0, x1, y1, z1), group, color)


def cyl_bm(cx, cy, z0, z1, r, r2=None, seg=48, axis="Z"):
    """Walec/stożek, promień r przy mniejszej współrzędnej osi.
    axis="Z": środek (cx, cy) w xy, zakres z0..z1.
    axis="Y": (cx, cy) to (x, z), zakres y to z0..z1.
    axis="X": (cx, cy) to (y, z), zakres x to z0..z1."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg,
                          radius1=r, radius2=r if r2 is None else r2, depth=abs(z1 - z0))
    mid = (z0 + z1) / 2
    if axis == "Y":
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(-math.pi / 2, 3, "X"))
        bmesh.ops.translate(bm, vec=(cx, mid, cy), verts=bm.verts)
    elif axis == "X":
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "Y"))
        bmesh.ops.translate(bm, vec=(mid, cx, cy), verts=bm.verts)
    else:
        bmesh.ops.translate(bm, vec=(cx, cy, mid), verts=bm.verts)
    return bm


def cyl(name, cx, cy, z0, z1, r, group="tmp", color=TMP, **kw):
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


def extrude_x_bm(pts_yz, x0, x1):
    """Wielokąt w płaszczyźnie (y, z) wyciągnięty wzdłuż X od x0 do x1."""
    bm = bmesh.new()
    n = len(pts_yz)
    a = [bm.verts.new((x0, y, z)) for y, z in pts_yz]
    b = [bm.verts.new((x1, y, z)) for y, z in pts_yz]
    bm.faces.new(a[::-1])
    bm.faces.new(b)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((a[i], a[j], b[j], b[i]))
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


# ---------------------------------------------------------------- wielokąt 2D
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


# ---------------------------------------------------------------- operacje na siatkach
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


def intersect(target, other, keep=False):
    boolean(target, other, "INTERSECT", keep=keep)


def bevel(ob, width, segments=5, angle=40):
    """Zaokrągla ostre krawędzie (kąt > angle) modyfikatorem Bevel i zapisuje wynik w siatce."""
    m = ob.modifiers.new("bev", "BEVEL")
    m.width, m.segments = width, segments
    m.limit_method = "ANGLE"
    m.angle_limit = math.radians(angle)
    new = evaluated_mesh(ob)
    old = ob.data
    ob.data = new
    ob.modifiers.remove(m)
    bpy.data.meshes.remove(old)


def apply_matrix(ob, M):
    """Wpisuje transformację M w wierzchołki siatki (obiekt zostaje z jednostkową macierzą)."""
    ob.data.transform(M @ ob.matrix_basis)
    ob.matrix_basis = Matrix.Identity(4)
    ob.data.update()


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
        fh.write(b"tiny-timer obudowa klin, mm".ljust(80, b" "))
        fh.write(struct.pack("<I", len(tris)))
        for n, vs in tris:
            fh.write(struct.pack("<12fH", n.x, n.y, n.z, *[c for v in vs for c in (v.x, v.y, v.z)], 0))
