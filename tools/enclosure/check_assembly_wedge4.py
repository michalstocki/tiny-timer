"""Kontrola składania klina 4.

    Blender --background --python tools/enclosure/build_wedge4.py                          # -> obudowa-klin-4.blend
    TT_NOHOOK=1 Blender --background --python tools/enclosure/build_wedge4.py              # -> obudowa-klin-4-bez-zaczepow.blend
    Blender --background docs/obudowa-klin-4/obudowa-klin-4-bez-zaczepow.blend --python tools/enclosure/check_assembly_wedge4.py
    Blender --background docs/obudowa-klin-4/obudowa-klin-4.blend --python tools/enclosure/check_assembly_wedge4.py -- blokada

Bez argumentu (wariant bez zaczepów, czyli z odgiętymi nogami zatrzasków):
  - zdejmowanie pokrywy pionowo w górę razem z elektroniką: objętość wspólna z korpusem, ogniwami, stykami i głośnikiem;
  - wyjmowanie ogniw pionowo w górę (pokrywa zdjęta), każde osobno przy pozostałych na miejscu.
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

static = of("Korpus", "Baterie", "Styki", "Glosnik")
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

# ogniwa: pokrywa zdjęta (daleko), każde ogniwo wyjmowane pionowo przy pozostałych na miejscu
place(Matrix.Translation((0, 0, 200)))
styki = of("Styki")
bad2 = 0
for name in ("AAA_A", "AAA_B", "AAA_C"):
    cell = [o for o in bpy.data.objects if o.name in (name, name + "_plus")]
    others = [o for o in of("Baterie") if o not in cell]
    for dz in (0.5, 1, 2, 4, 8, 12, 16, 24):
        for o in cell:
            o.location.z = dz
        bpy.context.view_layer.update()
        for o in cell:
            for b in [korpus] + styki + others:
                v = overlap(o, b)
                if v > 0.5:
                    bad2 += 1
                    print(f"OGNIWO {name} dz={dz:4.1f}  {o.name} x {b.name} {v:8.2f} mm3")
    for o in cell:
        o.location.z = 0
bpy.context.view_layer.update()
place(Matrix.Identity(4))
print(f"Wyjmowanie ogniw w górę: kolizji {bad2}")
