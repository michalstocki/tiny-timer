"""Eksport płytki głównej do pliku KiCada (.kicad_pcb, format v7; KiCad 7/8/9 go otwiera).

Układ: widok od strony elementów, elementy na F.Cu (strona elementów), strona lutowania = B.Cu. Początek arkusza przesunięty
(X0, Y0), oś y KiCada skierowana w dół (y_kicad = Y0 + H - y). Stopki są jednorazowe (bez biblioteki): jeden element = jedna stopka
z polami i opisem; opisy na B.SilkS są lustrzane, żeby czytało się je po odwróceniu płytki.
"""
import math
import uuid

import fab
import board as B

X0, Y0 = 100.0, 100.0
NS = uuid.UUID("6f1c2d5e-0000-4000-8000-00000000e17a")


def tid(*parts):
    return str(uuid.uuid5(NS, "/".join(str(p) for p in parts)))


def K(x, y):
    return X0 + x, Y0 + fab.H - y


def f(v):
    s = "%.4f" % v
    s = s.rstrip("0").rstrip(".")
    return s if s not in ("-0", "") else "0"


def at(x, y):
    kx, ky = K(x, y)
    return "(at %s %s)" % (f(kx), f(ky))


def build(design, texts_f, texts_b, title_lines=()):
    nets = ["", ] + fab.net_names()
    nid = {n: i for i, n in enumerate(nets)}
    o = []
    w = o.append
    w('(kicad_pcb (version 20221018) (generator tt_fab)')
    w('  (general (thickness %s))' % f(fab.THICKNESS))
    w('  (paper "A4")')
    w('  (title_block (title "TT-MAIN") (rev "1.0") (comment 1 "Minutnik ATtiny13A, plytka glowna 40x24 mm (obudowa klin 4)"))')
    w('  (layers')
    for num, name, kind, user in ((0, "F.Cu", "signal", None), (31, "B.Cu", "signal", None), (32, "B.Adhes", "user", "B.Adhesive"),
                                  (33, "F.Adhes", "user", "F.Adhesive"), (34, "B.Paste", "user", None), (35, "F.Paste", "user", None),
                                  (36, "B.SilkS", "user", "B.Silkscreen"), (37, "F.SilkS", "user", "F.Silkscreen"),
                                  (38, "B.Mask", "user", None), (39, "F.Mask", "user", None), (40, "Dwgs.User", "user", "User.Drawings"),
                                  (41, "Cmts.User", "user", "User.Comments"), (42, "Eco1.User", "user", "User.Eco1"),
                                  (43, "Eco2.User", "user", "User.Eco2"), (44, "Edge.Cuts", "user", None), (45, "Margin", "user", None),
                                  (46, "B.CrtYd", "user", "B.Courtyard"), (47, "F.CrtYd", "user", "F.Courtyard"),
                                  (48, "B.Fab", "user", None), (49, "F.Fab", "user", None)):
        w('    (%d "%s" %s%s)' % (num, name, kind, (' "%s"' % user) if user else ""))
    w('  )')
    R = fab.RULES
    w('  (setup')
    w('    (pad_to_mask_clearance %s)' % f(R["mask_margin"]))
    w('    (allow_soldermask_bridges_in_footprints no)')
    w('  )')
    for n in nets:
        w('  (net %d "%s")' % (nid[n], n))

    # --- stopki elementów
    by_ref = {}
    for p in fab.PADS:
        by_ref.setdefault(p["ref"], []).append(p)
    ref_text = {}
    for (s_, x, y, h) in texts_f:
        ref_text.setdefault(s_, []).append((x, y))
    for ref, pads in by_ref.items():
        ax, ay = fab.to_comp(ref, 0.0, 0.0)
        kax, kay = K(ax, ay)
        part = B.PARTS[ref]
        val = part["value"]
        w('  (footprint "TT:%s" (layer "F.Cu") (tstamp %s) (at %s %s)' % (part["fp"], tid("fp", ref), f(kax), f(kay)))
        w('    (descr "%s")' % val.replace('"', ""))
        w('    (attr through_hole)')
        # opis: ref i wartość; ref na F.SilkS tam, gdzie ułożył go placer, inaczej ukryty
        pos = None
        for (s_, x, y, h) in texts_f:
            if s_ == ref:
                pos = (x, y)
        if pos:
            kx, ky = K(*pos)
            w('    (fp_text reference "%s" (at %s %s) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))) (tstamp %s))'
              % (ref, f(kx - kax), f(ky - kay), tid("ref", ref)))
        else:
            w('    (fp_text reference "%s" (at 0 0) (layer "F.SilkS") hide (effects (font (size 1 1) (thickness 0.15))) (tstamp %s))'
              % (ref, tid("ref", ref)))
        w('    (fp_text value "%s" (at 0 1.5) (layer "F.Fab") hide (effects (font (size 1 1) (thickness 0.15))) (tstamp %s))'
          % (val.replace('"', ""), tid("val", ref)))
        for (r_, x0, y0, x1, y1) in fab.silk_lines():
            if r_ != ref:
                continue
            ka, kb = K(x0, y0), K(x1, y1)
            w('    (fp_line (start %s %s) (end %s %s) (stroke (width %s) (type solid)) (layer "F.SilkS") (tstamp %s))'
              % (f(ka[0] - kax), f(ka[1] - kay), f(kb[0] - kax), f(kb[1] - kay), f(R["silk_width"]),
                 tid("sl", ref, f(x0), f(y0), f(x1), f(y1))))
        for p in pads:
            kx, ky = K(p["x"], p["y"])
            net = p["net"]
            netc = ' (net %d "%s")' % (nid[net], net) if net else ""
            w('    (pad "%s" thru_hole %s (at %s %s) (size %s %s) (drill %s) (layers "*.Cu" "*.Mask")%s (tstamp %s))'
              % (p["pin"], "rect" if p["shape"] == "rect" else "circle", f(kx - kax), f(ky - kay), f(p["d"]), f(p["d"]),
                 f(p["drill"]), netc, tid("pad", ref, p["pin"])))
        w('  )')

    # --- otwory montażowe M2,5 (nieszczelinowe, bez metalizacji)
    for i, (mx, my) in enumerate(fab.HOLES, 1):
        kx, ky = K(mx, my)
        w('  (footprint "TT:MountingHole_M2.5" (layer "F.Cu") (tstamp %s) (at %s %s)' % (tid("mh", i), f(kx), f(ky)))
        w('    (attr exclude_from_pos_files exclude_from_bom)')
        w('    (fp_text reference "MH%d" (at 0 0) (layer "F.SilkS") hide (effects (font (size 1 1) (thickness 0.15))) (tstamp %s))' % (i, tid("mhr", i)))
        w('    (fp_text value "M2.5" (at 0 0) (layer "F.Fab") hide (effects (font (size 1 1) (thickness 0.15))) (tstamp %s))' % tid("mhv", i))
        w('    (pad "" np_thru_hole circle (at 0 0) (size %s %s) (drill %s) (layers "*.Cu" "*.Mask") (tstamp %s))'
          % (f(fab.MOUNT_D), f(fab.MOUNT_D), f(fab.MOUNT_D), tid("mhp", i)))
        w('  )')

    # --- obrys płytki: prostokąt 40 x 24 z narożnikami R3
    r = fab.CORNER_R
    Wd, Hd = fab.W, fab.H
    edge = [((r, 0), (Wd - r, 0)), ((Wd, r), (Wd, Hd - r)), ((Wd - r, Hd), (r, Hd)), ((0, Hd - r), (0, r))]
    for i, (a, b) in enumerate(edge):
        (ax1, ay1), (bx1, by1) = K(*a), K(*b)
        w('  (gr_line (start %s %s) (end %s %s) (stroke (width 0.1) (type solid)) (layer "Edge.Cuts") (tstamp %s))'
          % (f(ax1), f(ay1), f(bx1), f(by1), tid("edge", i)))
    d = r * (1 - math.sqrt(0.5))
    for i, (cx, cy, a, m, b) in enumerate(((r, r, (0, r), (d, d), (r, 0)), (Wd - r, r, (Wd - r, 0), (Wd - d, d), (Wd, r)),
                                           (Wd - r, Hd - r, (Wd, Hd - r), (Wd - d, Hd - d), (Wd - r, Hd)),
                                           (r, Hd - r, (r, Hd), (d, Hd - d), (0, Hd - r)))):
        sa, sm, sb = K(*a), K(*m), K(*b)
        w('  (gr_arc (start %s %s) (mid %s %s) (end %s %s) (stroke (width 0.1) (type solid)) (layer "Edge.Cuts") (tstamp %s))'
          % (f(sa[0]), f(sa[1]), f(sm[0]), f(sm[1]), f(sb[0]), f(sb[1]), tid("arc", i)))

    # --- opisy swobodne: B.SilkS lustrzane, F.SilkS tylko te, które nie są oznaczeniami elementów
    refs = set(by_ref)
    for i, (s_, x, y, h) in enumerate(texts_f):
        if s_ in refs:
            continue
        kx, ky = K(x, y)
        w('  (gr_text "%s" (at %s %s) (layer "F.SilkS") (tstamp %s) (effects (font (size %s %s) (thickness %s))))'
          % (s_, f(kx), f(ky), tid("tf", i, s_), f(h), f(h), f(R["silk_width"])))
    for i, (s_, x, y, h) in enumerate(texts_b):
        kx, ky = K(x, y)
        w('  (gr_text "%s" (at %s %s) (layer "B.SilkS") (tstamp %s) (effects (font (size %s %s) (thickness %s)) (justify mirror)))'
          % (s_, f(kx), f(ky), tid("tb", i, s_), f(h), f(h), f(R["silk_width"])))

    # --- miedź
    for i, (net, L, a, b) in enumerate(design["tracks"]):
        ka, kb = K(*a), K(*b)
        w('  (segment (start %s %s) (end %s %s) (width %s) (layer "%s") (net %d) (tstamp %s))'
          % (f(ka[0]), f(ka[1]), f(kb[0]), f(kb[1]), f(R["track"]), "F.Cu" if L == 0 else "B.Cu", nid[net], tid("seg", i)))
    for i, (net, x, y) in enumerate(design["vias"]):
        kx, ky = K(x, y)
        w('  (via (at %s %s) (size %s) (drill %s) (layers "F.Cu" "B.Cu") (net %d) (tstamp %s))'
          % (f(kx), f(ky), f(R["via_d"]), f(R["via_drill"]), nid[net], tid("via", i)))
    w(')')
    return "\n".join(o) + "\n"


def balanced(text):
    """Kontrola nawiasów (poza cudzysłowami)."""
    depth, q = 0, False
    for ch in text:
        if ch == '"':
            q = not q
        elif not q:
            depth += ch == "("
            depth -= ch == ")"
            if depth < 0:
                return False
    return depth == 0 and not q
