"""Kontrola składania klina 3: zdejmowanie pokrywy pionowo w górę i wkładanie ogniw do korpusu.

    TT_NOHOOK=1 TT_OUT=<katalog> Blender --background --python tools/enclosure/build_wedge3.py -- --norender
    Blender --background <katalog>/obudowa-klin-3.blend --python tools/enclosure/check_assembly_wedge3.py

Zaczep zatrzasku celowo wchodzi w rowek (to jest zatrzask), więc kontrola zdejmowania działa na wariancie bez zaczepu.
Dla kolejnych przesunięć pokrywy i niesionych przez nią elementów sprawdza objętość wspólną z korpusem, ogniwami,
stykami i głośnikiem. Ogniwa: ścieżka wkładania (wszystkie wzdłuż frontu w górę: ścianka frontu pochyla się nad ogniwami) przy już włożonych poprzednich.
"""
import math

import bmesh
import bpy
from mathutils import Vector


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


def overlap(a, b):
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


def of(*groups):
    return [o for o in bpy.data.objects if o.type == "MESH" and o.get("grupa") in groups]


carried = of("Pokrywa", "Kapsle", "Plytka", "Plytka_przyciskow", "Wyswietlacz")
static = of("Korpus", "Baterie", "Styki", "Glosnik")
bad = 0
for dz in (0.5, 1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48):
    for o in carried:
        o.location.z = dz
    bpy.context.view_layer.update()
    for a in carried:
        for b in static:
            v = overlap(a, b)
            if v > 0.5:
                bad += 1
                print(f"ZDEJMOWANIE dz={dz:4.1f}  {a.name:18s} x {b.name:22s} {v:8.2f} mm3")
for o in carried:
    o.location.z = 0
print(f"Zdejmowanie pokrywy w górę: kolizji {bad}")

# wkładanie ogniw: ścieżka od pozycji końcowej w górę wzdłuż frontu
th = math.radians(60)
paths = {i: Vector((0, math.cos(th), math.sin(th))) for i in (1, 2, 3)}      # wzdłuż frontu w górę (ścianka się pochyla)
korpus = of("Korpus")[0]
placed = []
bad2 = 0
for i in (1, 2, 3):
    cell = [o for o in bpy.data.objects if o.name in (f"AAA_{i}", f"AAA_{i}_plus")]
    for t in (0, 2, 4, 8, 12, 16, 24, 32, 44):
        for o in cell:
            o.location = paths[i] * t
        bpy.context.view_layer.update()
        for o in cell:
            for b in [korpus] + placed:
                v = overlap(o, b)
                if v > 0.5 and not (t == 0 and b is korpus and v < 0.5):
                    bad2 += 1
                    print(f"WKŁADANIE ogniwo {i} t={t:4.1f}  {o.name} x {b.name} {v:8.2f} mm3")
    for o in cell:
        o.location = (0, 0, 0)
    placed += cell
bpy.context.view_layer.update()
print(f"Wkładanie ogniw: kolizji {bad2}")
