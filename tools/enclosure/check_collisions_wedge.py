"""Kontrola kolizji dla wariantów "klin": objętość wspólna korpusu, pokrywy i klapki z resztą brył.

    Blender --background docs/obudowa-klin/obudowa-klin.blend --python tools/enclosure/check_collisions_wedge.py
    (klin 3: docs/obudowa-klin-3/obudowa-klin-3.blend)
Pokazuje tylko pary z objętością wspólną > 0.5 mm3. Płytki, elementy, baterie, styki, głośnik i kapsle
nie powinny wchodzić w korpus, pokrywę ani klapkę, a korpus, pokrywa i klapka nie mogą na siebie zachodzić.
"""
import bmesh
import bpy


def volume(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    v = abs(bm.calc_volume())
    bm.free()
    return v


def overlap(a, b):
    tmp = bpy.data.objects.new("t", a.data.copy())
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


SOLID = ("Korpus", "Pokrywa", "Klapka")
OTHERS = SOLID + ("Kapsle", "Styki", "Baterie", "Plytka", "Plytka_przyciskow", "Glosnik", "Wyswietlacz")
solid = [o for o in bpy.data.objects if o.type == "MESH" and o.get("grupa") in SOLID]
others = [o for o in bpy.data.objects if o.type == "MESH" and o.get("grupa") in OTHERS]

# kontrola działania testu: sześcian 1x1x1 mm w lewym boku korpusu (z dala od otworów) musi dać 1 mm3
me = bpy.data.meshes.new("ctl")
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=1.0)
bmesh.ops.translate(bm, vec=(1.0, bpy.context.scene.get("ctl_y", 45.0), bpy.context.scene.get("ctl_z", 45.0)), verts=bm.verts)
bm.to_mesh(me)
bm.free()
ctl = bpy.data.objects.new("ctl", me)
bpy.context.scene.collection.objects.link(ctl)
print(f"Kontrola testu: {overlap(bpy.data.objects['Korpus'], ctl):.2f} mm3 (oczekiwane 1.00)")
bpy.data.objects.remove(ctl, do_unlink=True)

bad = 0
for a in solid:
    for b in others:
        if a is b or (a.name >= b.name and b in solid):
            continue
        v = overlap(a, b)
        if v > 0.5:
            bad += 1
            print(f"KOLIZJA {a.name:16s} x {b.name:22s} {v:8.2f} mm3")
print(f"Sprawdzono {len(solid) * len(others)} par, kolizji: {bad}")
