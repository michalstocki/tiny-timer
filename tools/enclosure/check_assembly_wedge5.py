"""Kontrola składania klina 5.

    Blender --background --python tools/enclosure/build_wedge5.py                          # -> obudowa-klin-5.blend
    TT_NOHOOK=1 Blender --background --python tools/enclosure/build_wedge5.py              # -> obudowa-klin-5-bez-zaczepow.blend
    Blender --background docs/obudowa-klin-5/obudowa-klin-5-bez-zaczepow.blend --python tools/enclosure/check_assembly_wedge5.py
    Blender --background docs/obudowa-klin-5/obudowa-klin-5.blend --python tools/enclosure/check_assembly_wedge5.py -- blokada

Bez argumentu (wariant bez zaczepów, czyli z odgiętymi nogami zatrzasków):
  - zdejmowanie pokrywy pionowo w górę razem z elektroniką: objętość wspólna z korpusem, klapką, ogniwami, stykami i głośnikiem;
  - klapka: położenie zamknięte, otwieranie (obrót wokół dolnej krawędzi lewego końca kołnierza, prawy koniec w dół, do 30°)
    i wysunięcie języka z kieszeni (w prawo i w dół);
  - wsuwanie płytek styków od góry (pokrywa zdjęta, ogniwa wyjęte): płytka z przyciskami i sprężynami rozprężonymi do 8 mm
    przesuwana pionowo w górę, kolizje z korpusem (szczeliny, strop koszyka, wycięcia na sprężyny);
  - strop koszyka: ogniwo wepchnięte w głąb (w górę o 0,5 / 1 / 3 mm przy otwartej klapce) musi trafić w korpus;
  - wkładanie ogniw od spodu (klapka zdjęta), każde osobno przy pozostałych na miejscu: ogniwo przesunięte o 0,8 mm
    w stronę sprężyny (sprężyna ściśnięta z 4 do 3,2 mm, jej bryłę pomija się) i ruch pionowo w dół.
Z argumentem "blokada" (wariant z zaczepami): małe ruchy pokrywy z zamkniętego położenia. Każdy powinien dać kolizję
z korpusem (czyli być zablokowany): w górę, w przód, w tył, podważenie przedniej krawędzi (obrót wokół tylnego narożnika)
i tylnej (obrót wokół przedniego).
"""
import math
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector


def volume(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    v = abs(bm.calc_volume())
    bm.free()
    return v


def bbox(ob):
    pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return [min(p[i] for p in pts) for i in range(3)], [max(p[i] for p in pts) for i in range(3)]


def disjoint(a, b):
    (a0, a1), (b0, b1) = bbox(a), bbox(b)
    return any(a1[i] < b0[i] or b1[i] < a0[i] for i in range(3))


def overlap_once(a, b):
    if disjoint(a, b):
        return 0.0
    tmp = bpy.data.objects.new("t", a.data.copy())
    tmp.matrix_world = a.matrix_world
    bpy.context.scene.collection.objects.link(tmp)
    m = tmp.modifiers.new("i", "BOOLEAN")
    m.operation, m.object, m.solver = "INTERSECT", b, "EXACT"
    bpy.context.view_layer.update()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    t2 = bpy.data.objects.new("t2", me)
    v = volume(t2) if len(me.polygons) else 0.0
    for o in (tmp, t2):
        bpy.data.objects.remove(o, do_unlink=True)
    return v


def overlap(a, b):
    return max(overlap_once(a, b), overlap_once(b, a))


def of(*groups):
    return [o for o in bpy.data.objects if o.type == "MESH" and o.get("grupa") in groups]


carried = of("Pokrywa", "Kapsle", "Plytka", "Plytka_przyciskow", "Wyswietlacz")
base = {o.name: o.matrix_world.copy() for o in carried}


def place(M):
    for o in carried:
        o.matrix_world = M @ base[o.name]
    bpy.context.view_layer.update()


args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
korpus = of("Korpus")[0]
pokrywa = of("Pokrywa")[0]

if "blokada" in args:
    B = korpus.dimensions.y + 0.0
    y0 = min((korpus.matrix_world @ Vector(c)).y for c in korpus.bound_box)
    y1 = y0 + B
    print("Blokada pokrywy (oczekiwana kolizja pokrywy z korpusem w każdym ruchu):")
    moves = [("w górę 0,4 mm", Matrix.Translation((0, 0, 0.4))),
             ("w przód 0,4 mm", Matrix.Translation((0, -0.4, 0))),
             ("w tył 0,4 mm", Matrix.Translation((0, 0.4, 0))),
             ("przód w górę 1° (oś: tylny narożnik)", Matrix.Translation((0, y1 - 5, 5)) @ Matrix.Rotation(math.radians(-1), 4, "X") @ Matrix.Translation((0, -(y1 - 5), -5))),
             ("tył w górę 1° (oś: przedni narożnik)", Matrix.Translation((0, y0 + 5, 5)) @ Matrix.Rotation(math.radians(1), 4, "X") @ Matrix.Translation((0, -(y0 + 5), -5)))]
    place(Matrix.Identity(4))
    print(f"  położenie zamknięte: pokrywa x korpus {overlap(pokrywa, korpus):6.2f} mm3 (oczekiwane 0)")
    free = 0
    for label, M in moves:
        place(M)
        v = overlap(pokrywa, korpus)
        free += v < 0.05
        print(f"  {label:40s} {v:6.2f} mm3 {'zablokowane' if v >= 0.05 else 'SWOBODNE'}")
    place(Matrix.Identity(4))
    print(f"Ruchów swobodnych: {free}")
    raise SystemExit

static = of("Korpus", "Klapka", "Baterie", "Styki", "Glosnik")
bad = 0
for dz in (0.5, 1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48):
    place(Matrix.Translation((0, 0, dz)))
    for a in carried:
        for b in static:
            v = overlap(a, b)
            if v > 0.5:
                bad += 1
                print(f"ZDEJMOWANIE dz={dz:4.1f}  {a.name:18s} x {b.name:22s} {v:8.2f} mm3")
place(Matrix.Identity(4))
print(f"Zdejmowanie pokrywy w górę: kolizji {bad}")

# klapka: obrót wokół dolnej krawędzi lewego końca kołnierza (prawy koniec w dół), potem wysunięcie języka
place(Matrix.Translation((0, 0, 200)))
klapka = of("Klapka")[0]
k0 = klapka.matrix_world.copy()
sc = bpy.context.scene
px = sc["hatch_pivot_x"]


def hatch_at(M):
    klapka.matrix_world = M @ k0
    bpy.context.view_layer.update()
    return overlap(klapka, korpus)


print(f"Klapka zamknięta: klapka x korpus {hatch_at(Matrix.Identity(4)):6.2f} mm3 (oczekiwane 0)")
bad3 = 0
for deg in (1, 2, 3, 5, 8, 12, 16, 20, 25, 30):
    R = Matrix.Translation((px, 0, 0)) @ Matrix.Rotation(math.radians(deg), 4, "Y") @ Matrix.Translation((-px, 0, 0))
    v = hatch_at(R)
    if v > 0.05:
        bad3 += 1
        print(f"KLAPKA obrót {deg:2d}°  {v:8.2f} mm3")
R30 = Matrix.Translation((px, 0, 0)) @ Matrix.Rotation(math.radians(30), 4, "Y") @ Matrix.Translation((-px, 0, 0))
for dx in (0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0):
    v = hatch_at(Matrix.Translation((dx, 0, -0.3 * dx)) @ R30)
    if v > 0.05:
        bad3 += 1
        print(f"KLAPKA wysuwanie dx={dx:3.1f}  {v:8.2f} mm3")
print(f"Otwieranie klapki: kolizji {bad3}")
# blokada: klapka zamknięta, przykręcona; ruch w górę (wciśnięcie) musi być zablokowany przylgą, ruch w dół wkrętem
v_up = hatch_at(Matrix.Translation((0, 0, 0.3)))
v_left = hatch_at(Matrix.Translation((-0.4, 0, 0)))
print(f"Klapka w górę 0,3 mm: {v_up:6.2f} mm3 ({'zablokowana' if v_up >= 0.05 else 'SWOBODNA'}); "
      f"w lewo 0,4 mm: {v_left:6.2f} mm3 ({'zablokowana' if v_left >= 0.05 else 'SWOBODNA'})")
v_d = hatch_at(Matrix.Translation((0, 0, -0.3)))
print(f"Klapka w dół 0,3 mm bez wkrętu: {v_d:6.2f} mm3 (język w kieszeni: {'trzyma' if v_d >= 0.05 else 'NIE trzyma, trzyma tylko wkręt'})")
klapka.matrix_world = Matrix.Translation((0, 0, -200)) @ k0
bpy.context.view_layer.update()

# ogniwa: pokrywa i klapka zdjęte, każde ogniwo przesunięte w stronę sprężyny i wkładane pionowo od spodu
styki = [o for o in of("Styki") if not o.name.startswith("sprezyna")]
bad2 = 0
for name, shift in (("AAA_A", 0.8), ("AAA_B", -0.8), ("AAA_C", 0.8)):
    cell = [o for o in bpy.data.objects if o.name in (name, name + "_plus")]
    others = [o for o in of("Baterie") if o not in cell]
    for dz in (0, -0.5, -1, -2, -4, -8, -12, -16, -24):
        for o in cell:
            o.location.x, o.location.z = shift, dz
        bpy.context.view_layer.update()
        for o in cell:
            for b in [korpus] + styki + others:
                v = overlap(o, b)
                if v > 0.05:
                    bad2 += 1
                    print(f"OGNIWO {name} dz={dz:5.1f}  {o.name} x {b.name} {v:8.2f} mm3")
    for o in cell:
        o.location.x, o.location.z = 0, 0
bpy.context.view_layer.update()
# płytki styków: wsuwanie od góry, sprężyny rozprężone (swobodna długość), bez ogniw
sc = bpy.context.scene
bad4 = 0
plates = [o for o in of("Styki") if "y0" in o]
for pl in plates:
    end = pl["koniec"]
    parts = [pl] + [o for o in of("Styki") if "yc" in o and o["koniec"] == end and pl["y0"] <= o["yc"] <= pl["y1"]]
    tmp_spr = []
    for o in parts[1:]:
        if o.name.startswith("sprezyna"):
            bm = bmesh.new()
            bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=24, radius1=sc["spr_r"], radius2=sc["spr_r"],
                                  depth=sc["spr_free"])
            bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "Y"))
            x_mid = sc["ua"] + sc["spr_free"] / 2 if end == "L" else sc["ub"] - sc["spr_free"] / 2
            zc = sum((o.matrix_world @ Vector(c)).z for c in o.bound_box) / 8
            bmesh.ops.translate(bm, vec=(x_mid, o["yc"], zc), verts=bm.verts)
            me = bpy.data.meshes.new("spr_free")
            bm.to_mesh(me)
            bm.free()
            t = bpy.data.objects.new("sprezyna_swobodna", me)
            bpy.context.scene.collection.objects.link(t)
            tmp_spr.append(t)
    moving = [p_ for p_ in parts if not p_.name.startswith("sprezyna")] + tmp_spr
    base_m = {o.name: o.matrix_world.copy() for o in moving}
    for dz in (0.0, 0.5, 1, 2, 4, 6, 8, 10, 14, 20, 30):
        for o in moving:
            o.matrix_world = Matrix.Translation((0, 0, dz)) @ base_m[o.name]
        bpy.context.view_layer.update()
        for o in moving:
            v = overlap(o, korpus)
            if v > 0.05:
                bad4 += 1
                print(f"PŁYTKA {pl.name} dz={dz:4.1f}  {o.name} x Korpus {v:8.2f} mm3")
    for o in moving:
        o.matrix_world = base_m[o.name]
    for t in tmp_spr:
        bpy.data.objects.remove(t, do_unlink=True)
bpy.context.view_layer.update()
print(f"Wsuwanie płytek styków od góry: kolizji {bad4}")
# strop: ogniwo wepchnięte w górę (klapka zdjęta) ma się oprzeć o korpus
free_up = 0
for name in ("AAA_A", "AAA_B", "AAA_C"):
    cell = [o for o in bpy.data.objects if o.name == name]
    res = []
    for dz in (0.5, 1.0, 3.0):
        cell[0].location.z = dz
        bpy.context.view_layer.update()
        v = overlap(cell[0], korpus)
        free_up += v < 0.05
        res.append(f"{dz:3.1f} mm: {v:6.1f} mm3")
    cell[0].location.z = 0
    print(f"Ogniwo {name} wepchnięte w górę: " + ", ".join(res))
bpy.context.view_layer.update()
print(f"Ogniwa wepchnięte w górę bez oporu: {free_up} (oczekiwane 0)")
klapka.matrix_world = k0
place(Matrix.Identity(4))
print(f"Wkładanie ogniw od spodu: kolizji {bad2}")
