#!/usr/bin/env python3
"""Płytka przycisków (TT-BTN) jako płytka drukowana do zamówienia: plik KiCada, kontrola projektu, Gerbery przez export_fab.sh.

    python3 tools/pcb/fab_buttons.py            # kontrola + docs/plytka-przyciskow/tt-buttons.kicad_pcb
    bash tools/pcb/export_fab.sh docs/plytka-przyciskow/tt-buttons.kicad_pcb docs/plytka-przyciskow/produkcja

Geometria jest ta sama co na płytce uniwersalnej (docs/plytka-przyciskow/README.md, dane: pcb-layout.json, klucz
button_board): przyciski co 17,78 mm, otwory M2 po przekątnej, pola przewodów KEY1…KEY4 w tych samych miejscach. Zarys jest
o PAD_X = 2 mm szerszy z każdej strony (54 x 16 mm), bo otwory nóżek skrajnych przycisków (12,5 mm wg karty B3F) wypadałyby
przy szerokości 50 mm 0,4 mm od krawędzi. Współrzędne w widoku od strony elementów (przyciski od góry), początek w lewym
dolnym narożniku zarysu, x wzdłuż obudowy (lewa krawędź od strony głośnika), y w głąb (y = 0 od strony frontu).

Przycisk Omron B3F-4055 (karta A070-E1-08): nóżki 12,5 x 5,0 mm, otwory Ø1,2; kołki ustalające Ø1,6 w otworach Ø1,8, 9,0 mm od
siebie na osi przycisku; widok z góry: 4 i 3 u góry, 2 i 1 u dołu, 4-3 oraz 2-1 połączone wewnątrz na stałe.
"""
import json
import math
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/plytka-przyciskow"
BB = json.loads((ROOT / "docs/pcb-klin3/pcb-layout.json").read_text())["button_board"]

PAD_X = 2.0                                   # poszerzenie zarysu z każdej strony względem płytki uniwersalnej
W, H = BB["width"] + 2 * PAD_X, BB["depth"]
CORNER_R = BB["corner_radius"]
THICKNESS = BB["thickness"]
LEG_DX, LEG_DY = 12.5 / 2, 5.0 / 2            # nóżki B3F względem środka przycisku
LEG_DRILL, LEG_PAD = 1.2, 2.2
BOSS_DY, BOSS_DRILL = 4.5, 1.8
M2_DRILL = 2.2
WIRE_DRILL, WIRE_PAD = 1.2, 2.0               # pola przewodów jak KEY na płytce głównej
RULES = dict(track=0.30, clearance_min=0.25, edge_clearance=0.50, silk_width=0.15, mask_margin=0.05,
             m2_track=2.3, m2_pad=3.4)        # miedź od osi M2: łeb wkręta Ø4 od strony lutowania, słupek Ø3,6 od strony elementów

BTN = {b["ref"]: (b["x"] + PAD_X, b["y"], b["label"]) for b in BB["buttons"]}       # S3 (−), S1 (run), S2 (+)
M2 = [(h["x"] + PAD_X, h["y"]) for h in BB["mounting_holes"]]
LABEL = {"minus": "-", "run": "RUN", "plus": "+"}
ROW_NET = {"S3": ("KEY4", "PB4"), "S1": ("GND", "PB3"), "S2": ("GND", "PB4")}     # (górny rząd 4-3, dolny rząd 2-1)

# pola przewodów: te same oczka co na płytce uniwersalnej (kolumny G i N: x = 16,11 i 33,89 przed poszerzeniem)
XG, XN = M2[0][0], M2[1][0]
YR = {2: M2[0][1], 4: BTN["S1"][1], 6: M2[1][1]}                                   # rzędy oczek 2, 4, 6
WIRES = {"KEY1": ("GND", XN, YR[4]), "KEY2": ("PB3", XN, YR[2]), "KEY3": ("PB4", XG, YR[4]), "KEY4": ("KEY4", XG, YR[6])}
NETS = ["GND", "PB3", "PB4", "KEY4"]


def legs(ref):
    cx, cy, _ = BTN[ref]
    top, bot = ROW_NET[ref]
    return {"4": (cx - LEG_DX, cy + LEG_DY, top), "3": (cx + LEG_DX, cy + LEG_DY, top),
            "2": (cx - LEG_DX, cy - LEG_DY, bot), "1": (cx + LEG_DX, cy - LEG_DY, bot)}


def pads():
    """Wszystkie pola: (nazwa, pin, net, x, y, średnica pola, otwór, kształt)."""
    out = []
    for ref in BTN:
        for pin, (x, y, net) in legs(ref).items():
            out.append((ref, pin, net, x, y, LEG_PAD, LEG_DRILL, "circle"))
    for name, (net, x, y) in WIRES.items():
        out.append((name, "1", net, x, y, WIRE_PAD, WIRE_DRILL, "rect" if name == "KEY1" else "circle"))
    return out


def npth():
    """Otwory bez metalizacji: (x, y, średnica, opis)."""
    out = [(x, y, M2_DRILL, "M2") for x, y in M2]
    for ref, (cx, cy, _) in BTN.items():
        out += [(cx, cy - BOSS_DY, BOSS_DRILL, "kolek " + ref), (cx, cy + BOSS_DY, BOSS_DRILL, "kolek " + ref)]
    return out


# ---------------------------------------------------------------- trasowanie (ręczne, 45°)
def tracks():
    """(net, warstwa 0 = F strona elementów / 1 = B strona lutowania, punkt a, punkt b)."""
    L = {r: legs(r) for r in BTN}
    p = lambda r, pin: L[r][pin][:2]
    t = []
    # B: rzędy nóżek (nóżki jednego rzędu łączy też przycisk, ścieżka daje ciągłość bez niego)
    for r in BTN:
        t += [(L[r]["4"][2], 1, p(r, "4"), p(r, "3")), (L[r]["2"][2], 1, p(r, "2"), p(r, "1"))]
    # B: GND od S1 do S2 górnym rzędem i odejście do KEY1
    tee = (XN, p("S1", "3")[1])
    t += [("GND", 1, p("S1", "3"), tee), ("GND", 1, tee, p("S2", "4")), ("GND", 1, tee, WIRES["KEY1"][1:])]
    # B: PB3 do KEY2, KEY4 do KEY4
    t.append(("PB3", 1, p("S1", "1"), WIRES["KEY2"][1:]))
    t.append(("KEY4", 1, p("S3", "3"), WIRES["KEY4"][1:]))
    # F: PB4 od S3 przez KEY3 osią przycisków pod S1, potem między S1.1, KEY1 i KEY2 do S2.2
    a, k3 = p("S3", "1"), WIRES["KEY3"][1:]
    y0 = k3[1]
    x1 = p("S1", "1")[0] + 0.25
    # przejście między polem S1.1 a narożnikiem kwadratowego pola KEY1: 1,6 mm od środka S1.1 w stronę narożnika
    s11, corner = p("S1", "1"), (XN - WIRE_PAD / 2, YR[4] - WIRE_PAD / 2)
    dist = math.dist(s11, corner)
    d1 = (s11[0] + 1.6 * (corner[0] - s11[0]) / dist, s11[1] + 1.6 * (corner[1] - s11[1]) / dist)
    d2 = (XN, p("S2", "2")[1])
    for u, v in ((a, k3), (k3, (x1, y0)), ((x1, y0), d1), (d1, d2), (d2, p("S2", "2"))):
        t.append(("PB4", 0, u, v))
    return t


# ---------------------------------------------------------------- kontrola projektu
def seg_point(a, b, q):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    n = dx * dx + dy * dy
    s = 0.0 if n == 0 else max(0.0, min(1.0, ((q[0] - ax) * dx + (q[1] - ay) * dy) / n))
    return math.hypot(ax + s * dx - q[0], ay + s * dy - q[1])


def seg_seg(a, b, c, d):
    def cross(o, p_, q):
        return (p_[0] - o[0]) * (q[1] - o[1]) - (p_[1] - o[1]) * (q[0] - o[0])
    d1, d2, d3, d4 = cross(c, d, a), cross(c, d, b), cross(a, b, c), cross(a, b, d)
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
        return 0.0
    return min(seg_point(c, d, a), seg_point(c, d, b), seg_point(a, b, c), seg_point(a, b, d))


def pad_dist(a, b, pp):
    """Odległość odcinka a-b od brzegu pola (koło albo kwadrat), ujemna przy nachodzeniu."""
    x, y, d, shape = pp[3], pp[4], pp[5], pp[7]
    if shape == "circle":
        return seg_point(a, b, (x, y)) - d / 2
    h = d / 2
    c = [(x - h, y - h), (x + h, y - h), (x + h, y + h), (x - h, y + h)]
    if all(abs(q[0] - x) <= h and abs(q[1] - y) <= h for q in (a,)):
        return -1.0
    return min(seg_seg(a, b, c[i], c[(i + 1) % 4]) for i in range(4))


def edge_dist(q):
    """Odległość punktu od zarysu (prostokąt z narożnikami R) od wewnątrz."""
    x, y = q
    r = CORNER_R
    cx, cy = min(max(x, r), W - r), min(max(y, r), H - r)
    if (cx, cy) != (x, y):
        return r - math.hypot(x - cx, y - cy)
    return min(x, y, W - x, H - y)


def check():
    errors, info = [], {}
    P, T, N = pads(), tracks(), npth()
    hw = RULES["track"] / 2
    # 1. łączność: pola połączone ścieżkami tej samej warstwy przez pola (THT na obu warstwach); jedna grupa na sieć
    parent = {}

    def find(k):
        while parent.setdefault(k, k) != k:
            parent[k] = parent[parent[k]]
            k = parent[k]
        return k

    def union(a, b):
        parent[find(a)] = find(b)
    for i, (net, L, a, b) in enumerate(T):
        for end in (a, b):
            hits = [pp for pp in P if math.hypot(pp[3] - end[0], pp[4] - end[1]) < 1e-6]
            others = [j for j, (n2, L2, c, d) in enumerate(T) if j != i and L2 == L and (math.hypot(c[0] - end[0], c[1] - end[1]) < 1e-6
                                                                                       or math.hypot(d[0] - end[0], d[1] - end[1]) < 1e-6)]
            if not hits and not others:
                errors.append(f"wiszący koniec ścieżki {net} na {end}")
            for pp in hits:
                if pp[2] != net:
                    errors.append(f"ścieżka {net} kończy się na polu {pp[0]}.{pp[1]} sieci {pp[2]}")
                union(("t", i), ("p", pp[0], pp[1]))
            for j in others:
                union(("t", i), ("t", j))
    for net in NETS:
        groups = {find(("p", pp[0], pp[1])) for pp in P if pp[2] == net}
        if len(groups) != 1:
            errors.append(f"sieć {net} w {len(groups)} kawałkach")
    # 2. odstępy: ścieżka-pole innej sieci, ścieżka-ścieżka (ta sama warstwa), pole-pole, miedź-krawędź, miedź-otwory NPTH
    mins = []
    for (net, L, a, b) in T:
        for pp in P:
            if pp[2] != net:
                g = pad_dist(a, b, pp) - hw
                mins.append(g)
                if g < RULES["clearance_min"]:
                    errors.append(f"ścieżka {net} {a}-{b} za blisko pola {pp[0]}.{pp[1]}: {g:.3f} mm")
        for (net2, L2, c, d) in T:
            if net2 != net and L2 == L:
                g = seg_seg(a, b, c, d) - 2 * hw
                mins.append(g)
                if g < RULES["clearance_min"]:
                    errors.append(f"ścieżki {net} i {net2} za blisko: {g:.3f} mm")
        for q in (a, b):
            if edge_dist(q) - hw < RULES["edge_clearance"]:
                errors.append(f"ścieżka {net} za blisko krawędzi w {q}")
        for (x, y, dr, what) in N:
            lim = RULES["m2_track"] if what == "M2" else dr / 2 + RULES["clearance_min"]
            g = seg_point(a, b, (x, y)) - hw
            if g < lim:
                errors.append(f"ścieżka {net} za blisko otworu {what} ({x:.2f}, {y:.2f}): {g:.2f} mm")
    for i, a in enumerate(P):
        if edge_dist(a[3:5]) - a[5] / 2 < RULES["edge_clearance"]:
            errors.append(f"pole {a[0]}.{a[1]} za blisko krawędzi")
        for b in P[i + 1:]:
            rad = lambda q: q[5] / 2 * (math.sqrt(2) if q[7] == "rect" else 1.0)      # kwadrat: promień opisany (ostrożnie)
            g = math.hypot(a[3] - b[3], a[4] - b[4]) - rad(a) - rad(b)
            if a[2] != b[2]:
                mins.append(g)
                if g < RULES["clearance_min"]:
                    errors.append(f"pola {a[0]}.{a[1]} i {b[0]}.{b[1]} za blisko: {g:.3f}")
        for (x, y, dr, what) in N:
            d = math.hypot(a[3] - x, a[4] - y)
            lim = RULES["m2_pad"] if what == "M2" else (a[5] + dr) / 2 + RULES["clearance_min"]
            if d < lim:
                errors.append(f"pole {a[0]}.{a[1]} za blisko otworu {what}: {d:.2f} mm")
    for (x, y, dr, what) in N:
        if edge_dist((x, y)) - dr / 2 < 1.0:
            errors.append(f"otwór {what} za blisko krawędzi")
    info["min_clearance"] = min(mins)
    # 3. zgodność z obudową: przyciski i M2 w tych samych miejscach co w danych obudowy
    for b in BB["buttons"]:
        assert abs(BTN[b["ref"]][0] - PAD_X - b["x"]) < 1e-9
    return errors, info


# ---------------------------------------------------------------- opisy (widok od strony elementów)
def silk():
    """(warstwa F/B, tekst, x, y, wysokość) i odcinki (x0, y0, x1, y1) na F.SilkS."""
    texts, lines = [], []
    for ref, (cx, cy, lab) in BTN.items():
        h = 6.0
        lines += [(cx - h, cy + h, cx + h, cy + h), (cx - h, cy - h, cx + h, cy - h)]
        for sx in (-h, h):
            lines += [(cx + sx, cy + h, cx + sx, cy + 3.9), (cx + sx, cy - h, cx + sx, cy - 3.9)]
        texts.append(("F", ref, cx, cy + 2.4 if ref != "S1" else cy + 2.4, 1.0))
        texts.append(("F", LABEL[lab], cx, cy - 2.4, 1.0 if lab == "run" else 1.4))
    for name, (net, x, y) in WIRES.items():
        lab = "K" + name[-1]
        ty = y + 2.35 if name != "KEY4" else y + 1.95
        texts.append(("F", lab, x, ty, 0.9))
        texts.append(("B", lab, x, ty, 0.9))
    texts.append(("B", "TT-BTN v1.0", BTN["S1"][0], BTN["S1"][1], 0.9))
    texts.append(("B", "glosnik ->", BTN["S2"][0], BTN["S2"][1], 0.9))   # odbity: w widoku od lutowania strzałka wskazuje głośnik
    return texts, lines


CU_TEXTS = [(0, "TOP", BTN["S2"][0], BTN["S2"][1] + 0.0, 1.2, 0.25), (1, "BOT", BTN["S3"][0], BTN["S3"][1], 1.2, 0.25)]


# ---------------------------------------------------------------- plik KiCada (format v7, jak tt-main.kicad_pcb)
X0, Y0 = 100.0, 100.0
NS = uuid.UUID("6f1c2d5e-0000-4000-8000-0000b77b0001")


def tid(*parts):
    return str(uuid.uuid5(NS, "/".join(str(p) for p in parts)))


def K(x, y):
    return X0 + x, Y0 + H - y


def f(v):
    s = ("%.4f" % v).rstrip("0").rstrip(".")
    return s if s not in ("-0", "") else "0"


def kicad():
    nets = [""] + NETS
    nid = {n: i for i, n in enumerate(nets)}
    R = RULES
    o = []
    w = o.append
    w('(kicad_pcb (version 20221018) (generator tt_fab)')
    w('  (general (thickness %s))' % f(THICKNESS))
    w('  (paper "A4")')
    w('  (title_block (title "TT-BTN") (rev "1.0") (comment 1 "Minutnik ATtiny13A, plytka przyciskow 54x16 mm (obudowa klin 4)"))')
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
    w('  (setup')
    w('    (pad_to_mask_clearance %s)' % f(R["mask_margin"]))
    w('    (allow_soldermask_bridges_in_footprints no)')
    w('  )')
    for n in nets:
        w('  (net %d "%s")' % (nid[n], n))
    texts, lines = silk()

    def text_fp(s_, x, y, ax, ay, h, layer="F.SilkS"):
        kx, ky = K(x, y)
        return '(at %s %s) (layer "%s") (effects (font (size %s %s) (thickness %s)))' % (f(kx - ax), f(ky - ay), layer, f(h), f(h), f(R["silk_width"]))

    # przyciski: jedna stopka na przycisk (4 pola + 2 otwory kołków)
    for ref, (cx, cy, lab) in BTN.items():
        ax, ay = K(cx, cy)
        w('  (footprint "TT:SW_Omron_B3F-4055" (layer "F.Cu") (tstamp %s) (at %s %s)' % (tid("fp", ref), f(ax), f(ay)))
        w('    (descr "Omron B3F-4055, 12x12 mm, nozki 12,5 x 5,0 mm, kolki O1,6")')
        w('    (attr through_hole)')
        rt = [t for t in texts if t[1] == ref][0]
        w('    (fp_text reference "%s" %s (tstamp %s))' % (ref, text_fp(ref, rt[2], rt[3], ax, ay, rt[4]), tid("ref", ref)))
        w('    (fp_text value "B3F-4055" (at 0 1.5) (layer "F.Fab") hide (effects (font (size 1 1) (thickness 0.15))) (tstamp %s))' % tid("val", ref))
        for i, (x0, y0, x1, y1) in enumerate(l for l in lines if abs((l[0] + l[2]) / 2 - cx) <= 6.01):
            a, b = K(x0, y0), K(x1, y1)
            w('    (fp_line (start %s %s) (end %s %s) (stroke (width %s) (type solid)) (layer "F.SilkS") (tstamp %s))'
              % (f(a[0] - ax), f(a[1] - ay), f(b[0] - ax), f(b[1] - ay), f(R["silk_width"]), tid("sl", ref, i)))
        for pin, (x, y, net) in legs(ref).items():
            kx, ky = K(x, y)
            w('    (pad "%s" thru_hole circle (at %s %s) (size %s %s) (drill %s) (layers "*.Cu" "*.Mask") (net %d "%s") (tstamp %s))'
              % (pin, f(kx - ax), f(ky - ay), f(LEG_PAD), f(LEG_PAD), f(LEG_DRILL), nid[net], net, tid("pad", ref, pin)))
        for j, dy in enumerate((-BOSS_DY, BOSS_DY)):
            kx, ky = K(cx, cy + dy)
            w('    (pad "" np_thru_hole circle (at %s %s) (size %s %s) (drill %s) (layers "*.Cu" "*.Mask") (tstamp %s))'
              % (f(kx - ax), f(ky - ay), f(BOSS_DRILL), f(BOSS_DRILL), f(BOSS_DRILL), tid("boss", ref, j)))
        w('  )')
    # pola przewodów
    for name, (net, x, y) in WIRES.items():
        ax, ay = K(x, y)
        w('  (footprint "TT:Wire_Pad_D2.0" (layer "F.Cu") (tstamp %s) (at %s %s)' % (tid("fp", name), f(ax), f(ay)))
        w('    (descr "pole przewodu %s (%s)")' % (name, net))
        w('    (attr through_hole exclude_from_bom)')
        w('    (fp_text reference "%s" (at 0 0) (layer "F.SilkS") hide (effects (font (size 1 1) (thickness 0.15))) (tstamp %s))' % (name, tid("ref", name)))
        w('    (fp_text value "%s" (at 0 0) (layer "F.Fab") hide (effects (font (size 1 1) (thickness 0.15))) (tstamp %s))' % (net, tid("val", name)))
        w('    (pad "1" thru_hole %s (at 0 0) (size %s %s) (drill %s) (layers "*.Cu" "*.Mask") (net %d "%s") (tstamp %s))'
          % ("rect" if name == "KEY1" else "circle", f(WIRE_PAD), f(WIRE_PAD), f(WIRE_DRILL), nid[net], net, tid("pad", name)))
        w('  )')
    # otwory M2 (bez metalizacji)
    for i, (x, y) in enumerate(M2, 1):
        kx, ky = K(x, y)
        w('  (footprint "TT:MountingHole_M2" (layer "F.Cu") (tstamp %s) (at %s %s)' % (tid("mh", i), f(kx), f(ky)))
        w('    (attr exclude_from_pos_files exclude_from_bom)')
        w('    (fp_text reference "MH%d" (at 0 0) (layer "F.SilkS") hide (effects (font (size 1 1) (thickness 0.15))) (tstamp %s))' % (i, tid("mhr", i)))
        w('    (fp_text value "M2" (at 0 0) (layer "F.Fab") hide (effects (font (size 1 1) (thickness 0.15))) (tstamp %s))' % tid("mhv", i))
        w('    (pad "" np_thru_hole circle (at 0 0) (size %s %s) (drill %s) (layers "*.Cu" "*.Mask") (tstamp %s))'
          % (f(M2_DRILL), f(M2_DRILL), f(M2_DRILL), tid("mhp", i)))
        w('  )')
    # zarys 54 x 16 z narożnikami R2
    r = CORNER_R
    for i, (a, b) in enumerate((((r, 0), (W - r, 0)), ((W, r), (W, H - r)), ((W - r, H), (r, H)), ((0, H - r), (0, r)))):
        (a1, a2), (b1, b2) = K(*a), K(*b)
        w('  (gr_line (start %s %s) (end %s %s) (stroke (width 0.1) (type solid)) (layer "Edge.Cuts") (tstamp %s))'
          % (f(a1), f(a2), f(b1), f(b2), tid("edge", i)))
    d = r * (1 - math.sqrt(0.5))
    for i, (a, m, b) in enumerate((((0, r), (d, d), (r, 0)), ((W - r, 0), (W - d, d), (W, r)),
                                   ((W, H - r), (W - d, H - d), (W - r, H)), ((r, H), (d, H - d), (0, H - r)))):
        sa, sm, sb = K(*a), K(*m), K(*b)
        w('  (gr_arc (start %s %s) (mid %s %s) (end %s %s) (stroke (width 0.1) (type solid)) (layer "Edge.Cuts") (tstamp %s))'
          % (f(sa[0]), f(sa[1]), f(sm[0]), f(sm[1]), f(sb[0]), f(sb[1]), tid("arc", i)))
    # opisy swobodne
    for i, (L, s_, x, y, h) in enumerate(texts):
        if s_ in BTN:
            continue
        kx, ky = K(x, y)
        w('  (gr_text "%s" (at %s %s) (layer "%s") (tstamp %s) (effects (font (size %s %s) (thickness %s))%s))'
          % (s_, f(kx), f(ky), "F.SilkS" if L == "F" else "B.SilkS", tid("t", i, s_), f(h), f(h), f(R["silk_width"]),
             "" if L == "F" else " (justify mirror)"))
    for i, (L, s_, x, y, h, t) in enumerate(CU_TEXTS):
        kx, ky = K(x, y)
        w('  (gr_text "%s" (at %s %s) (layer "%s") (tstamp %s) (effects (font (size %s %s) (thickness %s))%s))'
          % (s_, f(kx), f(ky), "F.Cu" if L == 0 else "B.Cu", tid("tcu", i), f(h), f(h), f(t), "" if L == 0 else " (justify mirror)"))
    # miedź
    for i, (net, L, a, b) in enumerate(tracks()):
        ka, kb = K(*a), K(*b)
        w('  (segment (start %s %s) (end %s %s) (width %s) (layer "%s") (net %d) (tstamp %s))'
          % (f(ka[0]), f(ka[1]), f(kb[0]), f(kb[1]), f(R["track"]), "F.Cu" if L == 0 else "B.Cu", nid[net], tid("seg", i)))
    w(')')
    return "\n".join(o) + "\n"


def main():
    errors, info = check()
    length = sum(math.dist(a, b) for (_, _, a, b) in tracks())
    print(f"płytka {W:.1f} x {H:.1f} mm, pól {len(pads())}, otworów NPTH {len(npth())}, ścieżek {len(tracks())} ({length:.0f} mm), "
          f"najmniejszy odstęp miedzi {info['min_clearance']:.3f} mm")
    if errors:
        print("BŁĘDY (%d):" % len(errors))
        for e in errors:
            print("  - " + e)
        return 1
    print("kontrola: OK (każda sieć w jednym kawałku, odstępy, krawędź, otwory M2 i kołki)")
    if "--check" in sys.argv:
        return 0
    pcb = kicad()
    depth, q = 0, False
    for ch in pcb:
        if ch == '"':
            q = not q
        elif not q:
            depth += (ch == "(") - (ch == ")")
            assert depth >= 0
    assert depth == 0 and not q, "niezbalansowane nawiasy"
    (OUT / "tt-buttons.kicad_pcb").write_text(pcb)
    print("zapisano", (OUT / "tt-buttons.kicad_pcb").relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
