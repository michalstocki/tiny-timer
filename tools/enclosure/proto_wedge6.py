"""Klin 6, etap 1: prototyp bryły (sama sylwetka) z narożnikami G2, porównanie z klinem 5 i kontrola miejsca na wnętrze.

Uruchomienie (bez okna; skrypt czyta klin 5, żeby mieć elementy wnętrza i bryłę do porównania):
    /Applications/Blender.app/Contents/MacOS/Blender --background docs/obudowa-klin-5/obudowa-klin-5.blend \
        --python tools/enclosure/proto_wedge6.py

Parametry (zmienne środowiskowe, domyślnie wariant A):
    TT_RB   promień narożników przy podstawie (klin 5: 5)          TT_RA   promień wierzchołka (klin 5: 13)
    TT_RE   promień krawędzi boków (klin 5: 3)                     TT_SM   gładkość G2 przekroju, 0 = łuk (klin 5: 0)
    TT_SME  gładkość G2 krawędzi boków (domyślnie = TT_SM)         TT_SIDE bok trójkąta (klin 5: 67,0)
    TT_LEN  długość (klin 5: 74,1)                                 TT_OUT  folder wyjściowy
    TT_NORENDER=1  bez renderów (tylko liczby, STL i .blend)

Elementy wnętrza zostają tam, gdzie były w klinie 5. Przy większym boku przesuwam je razem ze środkiem okręgu wpisanego
(wtedy każda ścianka odsuwa się od nich o tyle samo). To szacunek rozmiaru, nie nowy układ: ten powstanie w etapie 2.
"""
import json
import math
import os
import sys
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpyutil as U
import g2geom as G
from geom2d import clip_top, convex_hull

ROOT = Path(__file__).resolve().parents[2]
env = os.environ.get
RB, RA, RE = float(env("TT_RB", "10")), float(env("TT_RA", "13")), float(env("TT_RE", "6"))
SM = float(env("TT_SM", "0.5"))
SME = float(env("TT_SME", str(SM)))
SIDE, LEN = float(env("TT_SIDE", "67.0")), float(env("TT_LEN", "74.1"))
OUT = ROOT / env("TT_OUT", "docs/obudowa-klin-6/prototyp/wariant-A")
RENDERS = OUT / "renders"
OUT.mkdir(parents=True, exist_ok=True)
RENDERS.mkdir(exist_ok=True)

# klin 5 (build_wedge5 / wedge3_solver)
K5 = dict(side=67.0, len=74.1, rb=5.0, ra=13.0, re=3.0, sm=0.0)
WALL, PANEL, T_TOP, WE = 2.0, 1.6, 4.4, 3.0
INSET_IN = (WALL, WALL, PANEL)                # podstawa, tył, front
SEAM_PSI = (208.0, 332.0)                     # szew pokrywy na narożnikach podstawy (kąt normalnej, jak PSI1 w klinie 5)
HATCH_MARGIN = 0.3                            # klapka (z przylgą) leży na płaskim dnie z takim zapasem
NSEG = 40                                     # punktów na narożnik przekroju
GROUPS_IN = ["Baterie", "Styki", "Plytka", "Plytka_przyciskow", "Wyswietlacz", "Glosnik"]
PASS_THROUGH = {"OLED_szklo", "B3F_trzpien_minus", "B3F_trzpien_run", "B3F_trzpien_plus", "Glosnik_ramka"}

scene = bpy.context.scene


def objs_of(coll_name):
    c = bpy.data.collections.get(coll_name)
    return [o for o in c.all_objects if o.type == "MESH"] if c else []


# ---------------------------------------------------------------- przekroje i bryła
def sec_outer(p, e=0.0):
    return G.section(p["side"], p["rb"], p["ra"], p["sm"], (e, e, e), NSEG)


def sec_inner(p):
    pts, info = G.section(p["side"], p["rb"], p["ra"], p["sm"], INSET_IN, NSEG)
    return pts, info


def z_top(p):
    return max(z for _, z in sec_outer(p)[0])


def end_prof(p):
    """(u, e) od płaszczyzny boku do ściany, z dodatkowym punktem na u = WE (tam leży szew boku)."""
    prof, t = G.end_profile(p["re"], p["sme"], 20)
    prof = sorted(prof)
    if t > WE:
        for (u0, e0), (u1, e1) in zip(prof, prof[1:]):
            if u0 < WE < u1:
                prof.append((WE, e0 + (e1 - e0) * (WE - u0) / (u1 - u0)))
        prof.sort()
    return prof, t


def e_at(p, u):
    prof, t = end_prof(p)
    if u >= t:
        return 0.0
    us = [a for a, _ in prof]
    es = [b for _, b in prof]
    return float(np.interp(u, us, es))


def solid_bm(p):
    prof, t = end_prof(p)
    us = [(u, e) for u, e in prof]
    xs = [(u, e) for u, e in us] + [(p["len"] - u, e) for u, e in reversed(us)]
    bm = bmesh.new()
    rings = []
    for x, e in xs:
        ring = [bm.verts.new((x, y, z)) for y, z in sec_outer(p, e)[0]]
        rings.append((x, ring))
    m = len(rings[0][1])
    for (xa, ra_), (xb, rb_) in zip(rings, rings[1:]):
        if abs(xb - xa) < 1e-6:
            continue
        for i in range(m):
            bm.faces.new((ra_[i], ra_[(i + 1) % m], rb_[(i + 1) % m], rb_[i]))
    bm.faces.new(rings[0][1])
    bm.faces.new(list(reversed(rings[-1][1])))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def cavity_bm(p):
    pts = clip_top(sec_inner(p)[0], z_top(p) - T_TOP)
    return U.extrude_x_bm(pts, WE, p["len"] - WE)


def material(name, color, rough=0.55):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    b = mat.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = color
    b.inputs["Roughness"].default_value = rough
    return mat


C_BODY, LID_C = (0.90, 0.89, 0.84, 1), (0.28, 0.30, 0.33, 1)
M_BODY, M_LID = material("k6_korpus", C_BODY), material("k6_pokrywa", LID_C)


def two_tone(ob, length):
    """Kolory jak w klinie 5: pokrywa (ciemna) od szwu na narożnikach podstawy przez wierzchołek, boki i dno jasne."""
    ob.data.materials.append(M_BODY)
    ob.data.materials.append(M_LID)
    for f in ob.data.polygons:
        c, n = f.center, f.normal
        psi = math.degrees(math.atan2(n.z, n.y)) % 360
        lid = WE - 0.01 < c.x < length - WE + 0.01 and not (SEAM_PSI[0] < psi < SEAM_PSI[1])
        f.material_index = 1 if lid else 0


# ---------------------------------------------------------------- kontrola wnętrza
def comp_points(dy=0.0, dz=0.0, dx=0.0):
    out = {}
    for g in GROUPS_IN:
        for o in objs_of(g):
            v = np.array([tuple(o.matrix_world @ w.co) for w in o.data.vertices])
            out[o.name] = (g, v + np.array([dx, dy, dz]))
    return out


def sdist(poly, yz):
    """Odległość ze znakiem (dodatnia w środku) punktów od wypukłego wielokąta CCW (przez proste krawędzi)."""
    P = np.array(poly)
    Q = np.roll(P, -1, axis=0)
    d = Q - P
    ln = np.hypot(d[:, 0], d[:, 1])
    keep = ln > 1e-9
    P, d, ln = P[keep], d[keep], ln[keep]
    nrm = np.stack([-d[:, 1], d[:, 0]], 1) / ln[:, None]
    s = (yz[:, None, 0] - P[None, :, 0]) * nrm[None, :, 0] + (yz[:, None, 1] - P[None, :, 1]) * nrm[None, :, 1]
    return s.min(axis=1)


def clearances(p, pts):
    inner = clip_top(sec_inner(p)[0], z_top(p) - T_TOP)
    res = {}
    for name, (g, v) in pts.items():
        sel = v[(v[:, 0] > WE + 0.01) & (v[:, 0] < p["len"] - WE - 0.01)]
        if len(sel):
            res[name] = float(sdist(inner, sel[:, 1:]).min())
    return res


def shift_for(p):
    db = p["side"] - K5["side"]
    return db / 2, db / (2 * math.sqrt(3)), (p["len"] - K5["len"]) / 2


def hatch_ok(p, hy):
    _, info = sec_outer(p)
    dy = shift_for(p)[0]
    f0, f1 = info["setbacks"][0], p["side"] - info["setbacks"][1]
    return f0, f1, (hy[0] - HATCH_MARGIN + dy) - f0, f1 - (hy[1] + HATCH_MARGIN + dy)


P5 = dict(K5, sme=0.0)
P6 = dict(side=SIDE, len=LEN, rb=RB, ra=RA, re=RE, sm=SM, sme=SME)

hatch = bpy.data.objects["Klapka"]
hy = (min((hatch.matrix_world @ v.co).y for v in hatch.data.vertices),
      max((hatch.matrix_world @ v.co).y for v in hatch.data.vertices))
base = clearances(P5, comp_points())
need = {k: min(v, 0.3) for k, v in base.items()}


def worst(p):
    dy, dz, dx = shift_for(p)
    c = clearances(p, comp_points(dy, dz, dx))
    return c, min(c[k] - need[k] for k in need), min(need, key=lambda k: c[k] - need[k])


cl6, margin6, worst6 = worst(P6)


def side_needed(p, with_hatch):
    lo, hi = K5["side"] - 6, K5["side"] + 40
    for _ in range(30):
        mid = (lo + hi) / 2
        q = dict(p, side=mid)
        ok = worst(q)[1] >= -0.005 and (not with_hatch or min(hatch_ok(q, hy)[2:]) >= 0)
        lo, hi = (lo, mid) if ok else (mid, hi)
    return hi


side_fit = side_needed(P6, False)
side_fit_hatch = side_needed(P6, True)
f0, f1, hm0, hm1 = hatch_ok(P6, hy)
_, info6 = sec_outer(P6)
turn = math.radians(120)
rep = dict(
    params=P6,
    wymiary=dict(dl=LEN, szer=round(max(y for y, _ in sec_outer(P6)[0]) - min(y for y, _ in sec_outer(P6)[0]), 2),
                 wys=round(z_top(P6), 2)),
    wymiary_klin5=dict(dl=K5["len"], szer=round(max(y for y, _ in sec_outer(P5)[0]) - min(y for y, _ in sec_outer(P5)[0]), 2),
                       wys=round(z_top(P5), 2)),
    r_min=dict(podstawa=round(G.r_min(turn, RB, SM), 2), wierzcholek=round(G.r_min(turn, RA, SM), 2),
               boki=round(G.r_min(math.pi / 2, RE, SME), 2)),
    cofniecie=dict(podstawa=round(info6["setbacks"][0], 2), wierzcholek=round(info6["setbacks"][2], 2),
                   boki=round(end_prof(P6)[1], 2)),
    plaskie_dno=dict(od=round(f0, 2), do=round(f1, 2), klapka=[round(hy[0], 2), round(hy[1], 2)],
                     zapas_front=round(hm0, 2), zapas_tyl=round(hm1, 2)),
    scianka_przy_boku=dict(wciecie_na_WE=round(e_at(P6, WE), 2), podstawa_tyl=round(WALL - e_at(P6, WE), 2),
                           front=round(PANEL - e_at(P6, WE), 2)),
    luzy={k: dict(klin5=round(base[k], 2), klin6=round(cl6[k], 2)) for k in sorted(base)},
    najgorszy=dict(element=worst6, zapas=round(margin6, 2)),
    bok_potrzebny=dict(bez_klapki=round(side_fit, 1), z_plaska_klapka=round(side_fit_hatch, 1)),
)
(OUT / "raport.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False))
print("RAPORT", json.dumps(rep, ensure_ascii=False))

# ---------------------------------------------------------------- dane dla przeglądarki (elementy wnętrza klina 5)
data = dict(k5=dict(K5, wall=WALL, panel=PANEL, t_top=T_TOP, we=WE, hatch_y=list(hy), seam_psi=list(SEAM_PSI)),
            need={k: round(v, 3) for k, v in need.items()}, parts=[])
for g in GROUPS_IN:
    for o in objs_of(g):
        me = o.data
        me.calc_loop_triangles()
        vs = [tuple(round(c, 2) for c in (o.matrix_world @ v.co)) for v in me.vertices]
        tris = [list(t.vertices) for t in me.loop_triangles]
        data["parts"].append(dict(name=o.name, group=g, v=vs, t=tris))
(OUT / "wnetrze-klin5.json").write_text(json.dumps(data, separators=(",", ":")))

# ---------------------------------------------------------------- przekrój porównawczy (SVG)
def svg_section(path):
    sc, pad = 9.0, 13.0
    W, Hh = (K5["side"] + 2 * pad) * sc, (z_top(P6) + 2 * pad) * sc
    tf = lambda y, z: ((y + pad) * sc, (z_top(P6) + pad - z) * sc)
    poly = lambda pts: " ".join(f"{a:.1f},{b:.1f}" for a, b in (tf(y, z) for y, z in pts))
    dy, dz, _ = shift_for(P6)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {Hh:.0f}" font-family="Helvetica" font-size="17">',
           f'<rect width="{W:.0f}" height="{Hh:.0f}" fill="#f4f4f1"/>']
    pts = comp_points(dy, dz)
    for name, (g, v) in pts.items():
        hull = convex_hull([tuple(a) for a in v[:, 1:]])
        bad = cl6.get(name, 1) < need.get(name, 0) - 0.005
        out.append(f'<polygon points="{poly(hull)}" fill="{"#e0503c" if bad else "#9db4c8"}" fill-opacity="0.55" stroke="none"/>')
    for p, col, dash in ((P5, "#888", "8 6"), (P6, "#1d2733", "")):
        o, _ = sec_outer(p)
        i = clip_top(sec_inner(p)[0], z_top(p) - T_TOP)
        for pl in (o, i):
            out.append(f'<polygon points="{poly(pl)}" fill="none" stroke="{col}" stroke-width="{3 if p is P6 else 2}"'
                       f' stroke-dasharray="{dash}"/>')
    # grzebień krzywizny (normalna do wnętrza, długość proporcjonalna do krzywizny)
    for p, col in ((P5, "#b0b0b0"), (P6, "#d9822b")):
        o, _ = G.section(p["side"], p["rb"], p["ra"], p["sm"], (0, 0, 0), 60)
        ks = G.curvature(o)
        tips = []
        for k in range(len(o)):
            a, b = o[k - 1], o[(k + 1) % len(o)]
            tx, tz = b[0] - a[0], b[1] - a[1]
            ln = math.hypot(tx, tz) or 1
            nx, nz = tz / ln, -tx / ln            # na zewnątrz
            s = ks[k] * 40
            tip = (o[k][0] + nx * s, o[k][1] + nz * s)
            tips.append(tip)
            out.append(f'<line x1="{tf(*o[k])[0]:.1f}" y1="{tf(*o[k])[1]:.1f}" x2="{tf(*tip)[0]:.1f}" y2="{tf(*tip)[1]:.1f}"'
                       f' stroke="{col}" stroke-width="1"/>')
        out.append(f'<polyline points="{poly(tips + tips[:1])}" fill="none" stroke="{col}" stroke-width="1.5"/>')
    y0, y1 = hy[0] + dy, hy[1] + dy
    out.append(f'<line x1="{tf(y0, -2)[0]:.1f}" y1="{tf(y0, -2)[1]:.1f}" x2="{tf(y1, -2)[0]:.1f}" y2="{tf(y1, -2)[1]:.1f}"'
               f' stroke="#3a7d44" stroke-width="5"/>')
    out.append(f'<line x1="{tf(f0, -3.5)[0]:.1f}" y1="{tf(f0, -3.5)[1]:.1f}" x2="{tf(f1, -3.5)[0]:.1f}" y2="{tf(f1, -3.5)[1]:.1f}"'
               f' stroke="#1d2733" stroke-width="5"/>')
    out.append(f'<text x="20" y="30">klin 5 (przerywana, szary grzebień) / klin 6 (ciągła, pomarańczowy grzebień krzywizny)</text>')
    out.append(f'<text x="20" y="54">klin 6: RB {RB:g}, RA {RA:g}, gładkość {SM:g}, bok {SIDE:g}. Zielony: klapka klina 5, czarny: płaskie dno klina 6</text>')
    out.append("</svg>")
    Path(path).write_text("\n".join(out))


svg_section(OUT / "przekroj-porownanie.svg")

# ---------------------------------------------------------------- obiekty
for c in list(bpy.data.collections):
    for o in c.objects:
        o["grupa"] = c.name
k6 = U.finish("Klin6", solid_bm(P6), "Klin6", (1, 1, 1, 1))
two_tone(k6, LEN)
bad, vol = U.manifold_report(k6)
print(f"KLIN6 bryła: krawędzie nierozmaitościowe {bad}, objętość {vol / 1000:.1f} cm³")
U.write_stl(OUT / "prototyp-klin6.stl", [k6])
shell = U.finish("Klin6_skorupa", solid_bm(P6), "Klin6_skorupa", (1, 1, 1, 1))
U.cut(shell, U.finish("wneka", cavity_bm(P6), "tmp", (1, 1, 1, 1)))
shell.data.materials.append(M_BODY)
dy, dz, dx = shift_for(P6)
for g in GROUPS_IN:
    for o in objs_of(g):
        o.location += Vector((dx, dy, dz))
(OUT / "prototyp-klin6.blend").unlink(missing_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "prototyp-klin6.blend"), check_existing=False)
(OUT / "prototyp-klin6.blend1").unlink(missing_ok=True)
if env("TT_NORENDER"):
    print("GOTOWE (bez renderów)")
    raise SystemExit

# ---------------------------------------------------------------- rendery
world = scene.world or bpy.data.worlds.new("w")
scene.world = world
scene.render.engine = "BLENDER_EEVEE"
scene.eevee.taa_render_samples = 48
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.85, 0.87, 0.90, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.55
for ob in bpy.data.objects:
    if ob.type == "MESH":
        if all(m is None for m in ob.data.materials) or not ob.data.materials:
            ob.data.materials.clear()
            ob.data.materials.append(material(ob.name, ob.color))
        ob.data.shade_smooth()
        ob.data.set_sharp_from_angle(angle=math.radians(35))
k6.data.shade_smooth()
k6.data.set_sharp_from_angle(angle=math.radians(80))    # bryła gładka; ostre tylko krawędzie dekli (90°)
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "Standard"
cam_data = bpy.data.cameras.new("cam")
cam = bpy.data.objects.new("cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
sun_data = bpy.data.lights.new("sun", "SUN")
sun_data.energy, sun_data.angle = 2.0, math.radians(6)
sun = bpy.data.objects.new("sun", sun_data)
scene.collection.objects.link(sun)
sun.parent = cam
sun.rotation_euler = (math.radians(18), math.radians(-22), 0)

zebra = bpy.data.materials.new("zebra")
zebra.use_nodes = True
nt = zebra.node_tree
nt.nodes.clear()
tc = nt.nodes.new("ShaderNodeTexCoord")
dot = nt.nodes.new("ShaderNodeVectorMath")
dot.operation = "DOT_PRODUCT"
dot.inputs[1].default_value = Vector((0.35, 0.45, 0.82)).normalized()
mul = nt.nodes.new("ShaderNodeMath")
mul.operation = "MULTIPLY"
mul.inputs[1].default_value = 7.0
fr = nt.nodes.new("ShaderNodeMath")
fr.operation = "FRACT"
gt = nt.nodes.new("ShaderNodeMath")
gt.operation = "GREATER_THAN"
gt.inputs[1].default_value = 0.5
em = nt.nodes.new("ShaderNodeEmission")
outn = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(tc.outputs["Reflection"], dot.inputs[0])
nt.links.new(dot.outputs["Value"], mul.inputs[0])
nt.links.new(mul.outputs[0], fr.inputs[0])
nt.links.new(fr.outputs[0], gt.inputs[0])
nt.links.new(gt.outputs[0], em.inputs["Color"])
nt.links.new(em.outputs[0], outn.inputs["Surface"])

K5_SHELL = [o for g in ("Korpus", "Pokrywa", "Klapka", "Kapsle") for o in objs_of(g)]
INTERIOR = [o for g in GROUPS_IN for o in objs_of(g)]


def aim(loc, tgt, up=(0, 0, 1)):
    f = (Vector(tgt) - Vector(loc)).normalized()
    z = -f
    x = Vector(up).cross(z).normalized()
    y = z.cross(x)
    cam.matrix_world = Matrix.Translation(loc) @ Matrix(((x.x, y.x, z.x), (x.y, y.y, z.y), (x.z, y.z, z.z))).to_4x4()


def render(path, show, loc, tgt, up=(0, 0, 1), ortho=None, lens=70, res=(1100, 900), mat=None):
    keep = {}
    if mat:
        for o in show:
            keep[o.name] = (list(o.data.materials), [f.material_index for f in o.data.polygons])
            o.data.materials.clear()
            o.data.materials.append(mat)
            for f in o.data.polygons:
                f.material_index = 0
    names = {o.name for o in show}
    for ob in bpy.data.objects:
        if ob.type == "MESH":
            ob.hide_render = ob.name not in names
    cam_data.type = "ORTHO" if ortho else "PERSP"
    if ortho:
        cam_data.ortho_scale = ortho
    else:
        cam_data.lens = lens
    cam_data.clip_start, cam_data.clip_end = 1, 3000
    scene.render.resolution_x, scene.render.resolution_y = res
    aim(loc, tgt, up)
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    if mat:
        for o in show:
            o.data.materials.clear()
            for m in keep[o.name][0]:
                o.data.materials.append(m)
            o.data.polygons.foreach_set("material_index", keep[o.name][1])


def side_by_side(name, views):
    """Kilka renderów obok siebie w jednym PNG (lewy = klin 5, prawy = klin 6)."""
    imgs = []
    for i, (show, kw) in enumerate(views):
        p = RENDERS / f"_tmp{i}.png"
        render(p, show, **kw)
        im = bpy.data.images.load(str(p))
        a = np.empty(im.size[0] * im.size[1] * 4, dtype=np.float32)
        im.pixels.foreach_get(a)
        imgs.append(a.reshape(im.size[1], im.size[0], 4))
        bpy.data.images.remove(im)
        p.unlink()
    gap = np.ones((imgs[0].shape[0], 12, 4), dtype=np.float32)
    row = np.concatenate([x for im in imgs for x in (im, gap)][:-1], axis=1)
    out = bpy.data.images.new(name, row.shape[1], row.shape[0], alpha=True)
    out.pixels.foreach_set(row.ravel())
    out.filepath_raw = str(RENDERS / name)
    out.file_format = "PNG"
    out.save()


H6 = z_top(P6)
cx, cy = LEN / 2, SIDE / 2
iso = dict(loc=(cx + 200, cy - 183.5, H6 * 0.8 + 120), tgt=(cx, cy, H6 * 0.4), lens=70)
iso5 = dict(loc=(K5["len"] / 2 + 200, 33.5 - 183.5, 45 * 0.8 + 120), tgt=(K5["len"] / 2, 33.5, 45 * 0.4), lens=70)
side_by_side("01-porownanie-przod-iso.png", [(K5_SHELL, iso5), ([k6], iso)])
end = dict(loc=(LEN + 300, cy, H6 / 2), tgt=(LEN, cy, H6 / 2), ortho=95)
end5 = dict(loc=(K5["len"] + 300, 33.5, H6 / 2), tgt=(K5["len"], 33.5, H6 / 2), ortho=95)
side_by_side("02-porownanie-bok.png", [(K5_SHELL, end5), ([k6], end)])
bot = dict(loc=(cx, cy, -300), tgt=(cx, cy, 0), up=(0, 1, 0), ortho=100)
bot5 = dict(loc=(K5["len"] / 2, 33.5, -300), tgt=(K5["len"] / 2, 33.5, 0), up=(0, 1, 0), ortho=100)
side_by_side("03-porownanie-spod.png", [(K5_SHELL, bot5), ([k6], bot)])
side_by_side("04-porownanie-zebra-iso.png", [(K5_SHELL, dict(iso5, mat=zebra)), ([k6], dict(iso, mat=zebra))])
cz = dict(loc=(LEN + 70, -35, 55), tgt=(LEN - 6, 8, 6), lens=80)
cz5 = dict(loc=(K5["len"] + 70, -35, 55), tgt=(K5["len"] - 6, 8, 6), lens=80)
side_by_side("05-porownanie-zebra-naroznik.png", [(K5_SHELL, dict(cz5, mat=zebra)), ([k6], dict(cz, mat=zebra))])
side_by_side("06-porownanie-naroznik.png", [(K5_SHELL, cz5), ([k6], cz)])
render(RENDERS / "07-klin6-tyl-iso.png", [k6], (cx - 150, SIDE + 180, H6 * 0.8 + 100), (cx, cy, H6 * 0.4), lens=70,
       res=(1500, 1100))

print("GOTOWE")
