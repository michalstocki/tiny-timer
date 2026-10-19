#!/usr/bin/env python3
"""Preliminary PCB design of the ATtiny13A timer (iteration 1).

Single source of truth for: outline, mounting holes, parts, footprints
(pads, holes, bodies, heights), nets, and checks. Everything is in
millimetres, in the FRONT VIEW frame: origin = lower-left corner of the
board outline, +x to the right, +y up, looking at the front (TOP) side.

Sides:  top    = front, user-facing: OLED module + 3 buttons
        bottom = back: everything else (bodies); the leads of those parts
                 come out on the top side in the free strips and are
                 soldered/trimmed there (joint height assumed <= 2.0 mm).
"""
import json
import math
import os
import sys

# Variant of the design (parallel concepts, the base one must stay untouched):
#   base = iteration 1, buttons on the main board (48 x 50 mm)
#   klin = wedge enclosure: buttons on a separate small board, a shorter main board
VARIANT = os.environ.get("PCB_VARIANT", "base")
KLIN_H = 36.0

# ---------------------------------------------------------------- params ----
P = dict(
    W=48.0, H=50.0,             # board outline
    corner_r=3.0,
    thickness=1.6,
    hole_margin=3.5,            # mounting hole centre distance from the edges
    mount_d=2.7,                # M2.5 clearance
    mount_keepout_r=3.2,
    oled_len=38.0, oled_h=12.0,  # module PCB (ESTIMATE from the photo, measure!)
    oled_pin_to_edge=1.5,        # pin centre to the module's left edge (ESTIMATE)
    glass_w=25.0, glass_h=10.0,  # given by the user
    glass_to_pin=5.0,            # pin centre to the glass' left edge (user)
    oled_thickness=4.0,          # given by the user (without pins)
    oled_standoff=2.5,           # plastic of the pin header under the module (assumed)
    btn_gap_x=4.0,               # gap between button bodies
    group_gap_y=3.0,             # gap between display module and buttons
    # B3F-4055, from the Omron datasheet supplied by the user
    btn_body=12.0, btn_height=7.3, btn_plunger=3.8, btn_cap_d=7.1,
    btn_pitch_x=12.5, btn_pitch_y=5.0, btn_hole=1.2, btn_boss_d=1.8, btn_boss_dy=4.5,
    btn_lead_below=3.5,
    track_w=0.30, clearance=0.30,
    pad_d=1.8, pad_d_btn=2.2, via_d=0.9, via_drill=0.4, hole_d=0.9,
    bottom_height=9.0,           # envelope of the back side (chip in socket ~8.5)
)
if VARIANT == "klin":
    P["H"] = float(os.environ.get("PCB_H", KLIN_H))

# ------------------------------------------------------------ footprints ----
# Pads are given in the part's local COMPONENT VIEW (looking at the part
# from its mounting side, +y up). For bottom parts x is mirrored when they
# are placed in the front-view frame.
FP = {
    # DIP-8 socket: pin 1 at the origin, pins 1-4 go down, 5-8 up on the right
    "dip8": dict(pads={str(i + 1): (0.0, -2.54 * i) for i in range(4)} |
                 {str(5 + i): (7.62, -7.62 + 2.54 * i) for i in range(4)},
                 body=(-1.4, -8.9, 9.0, 1.4), height=4.5, hole=0.9, pad=1.7),
    # axial resistor standing on end (pads 2.54 apart) / lying (R4)
    "res_v": dict(pads={"1": (0.0, 0.0), "2": (2.54, 0.0)}, body=(-1.5, -1.5, 4.0, 1.5),
                  height=7.5, hole=0.8, pad=1.7),
    "res_h": dict(pads={"1": (0.0, 0.0), "2": (12.7, 0.0)}, body=(1.8, -2.0, 10.9, 2.0),
                  height=4.0, hole=0.9, pad=1.9),
    "cap5": dict(pads={"1": (0.0, 0.0), "2": (5.08, 0.0)}, body=(-0.5, -2.2, 5.6, 2.2),
                 height=6.0, hole=0.8, pad=1.7),
    "elco5": dict(pads={"+": (0.0, 0.0), "-": (2.54, 0.0)}, body=(-1.2, -2.6, 3.8, 2.6),
                  height=8.0, hole=0.8, pad=1.7),
    "led": dict(pads={"A": (0.0, 0.0), "K": (2.54, 0.0)}, body=(-1.3, -2.7, 3.9, 2.7),
                height=8.7, hole=0.9, pad=1.7),
    "to92": dict(pads={"C": (-2.54, 0.0), "B": (0.0, 0.0), "E": (2.54, 0.0)},
                 body=(-2.6, -0.7, 2.6, 4.2), height=5.5, hole=0.8, pad=1.7),
    "wire2": dict(pads={"1": (0.0, 0.0), "2": (2.54, 0.0)}, body=(-1.2, -1.2, 3.8, 1.2),
                  height=0.0, hole=1.2, pad=2.3),
    # 4 wires to the separate button board (GND, PB3, PB4, S3 low side); pitch 3.5 keeps 1.2 mm between pads
    "wire4": dict(pads={str(i + 1): (3.5 * i, 0.0) for i in range(4)}, body=(-1.2, -1.2, 11.7, 1.2),
                  height=0.0, hole=1.2, pad=2.3),
}
# OLED header (top side), local frame = front view, origin = pin SDA
FP["oled"] = dict(pads={"SDA": (0.0, 0.0), "SCL": (0.0, -2.54), "VCC": (0.0, -5.08), "GND": (0.0, -7.62)},
                  body=None, height=P["oled_thickness"] + P["oled_standoff"], hole=1.0, pad=1.8)
# B3F-4055 (top side). Terminal numbers as on the datasheet (top view):
# 4 upper-left, 3 upper-right, 2 lower-left, 1 lower-right.
# Datasheet: 4-3 are connected, 2-1 are connected, the switch joins the rows.
FP["b3f"] = dict(pads={"4": (-6.25, 2.5), "3": (6.25, 2.5), "2": (-6.25, -2.5), "1": (6.25, -2.5)},
                 body=(-6.0, -6.0, 6.0, 6.0), height=P["btn_height"], hole=P["btn_hole"],
                 pad=P["pad_d_btn"],
                 bosses=[(0.0, P["btn_boss_dy"]), (0.0, -P["btn_boss_dy"])])


def derived():
    p = P
    d = {}
    d["cx"], d["cy"] = p["W"] / 2, p["H"] / 2
    d["oled_pin_x"] = d["cx"] - (p["glass_to_pin"] + p["glass_w"] / 2)       # SDA pin column
    d["oled_cy"] = d["cy"] + (p["oled_h"] + p["group_gap_y"]) / 2
    if VARIANT == "klin":
        d["oled_cy"] = d["cy"]              # no buttons below: the module sits in the middle
    d["btn_cy"] = d["cy"] - (p["btn_body"] + p["group_gap_y"]) / 2
    pitch = p["btn_body"] + p["btn_gap_x"]
    d["btn_cx"] = [d["cx"] - pitch, d["cx"], d["cx"] + pitch]
    d["strip_h"] = d["cy"] - (p["oled_h"] + p["group_gap_y"] / 2 + 0.0) - 0.0
    return d


D = derived()

# ---------------------------------------------------------------- parts ----
# ref: (footprint, side, x, y, rotation_deg, value)
PARTS = {}


def add(ref, fp, side, x, y, rot=0, value=""):
    PARTS[ref] = dict(fp=fp, side=side, x=x, y=y, rot=rot, value=value)


def place_all():
    PARTS.clear()
    cx, cy = D["cx"], D["cy"]
    # --- front side ---------------------------------------------------------
    # OLED: pin SDA is the upper pin; header pitch 2.54; centre of the 4 pins = module centre
    oy_top = D["oled_cy"] + 3.81
    add("OLED", "oled", "top", D["oled_pin_x"], oy_top, 0, "SSD1306 128x32 module")
    # buttons left to right: "-", "run", "+" (klin: on a separate board, wired to the KEY pads)
    if VARIANT == "base":
        add("S3", "b3f", "top", D["btn_cx"][0], D["btn_cy"], 0, "B3F-4055 (-)")
        add("S1", "b3f", "top", D["btn_cx"][1], D["btn_cy"], 0, "B3F-4055 (run)")
        add("S2", "b3f", "top", D["btn_cx"][2], D["btn_cy"], 0, "B3F-4055 (+)")
    # --- back side (positions are filled in by LAYOUT below) -----------------
    for ref, (fp, x, y, rot, val) in LAYOUT.items():
        add(ref, fp, "bottom", x, y, rot, val)


# Back-side parts: (footprint, x, y, rotation, value). x,y = position of the
# part origin in the front-view frame (see FP for the origin of each part).
LAYOUT = {}


def pad_positions(ref):
    """Absolute pad centres {pin: (x, y)} in the front-view frame."""
    part = PARTS[ref]
    fp = FP[part["fp"]]
    r = math.radians(part["rot"])
    out = {}
    for pin, (lx, ly) in fp["pads"].items():
        if part["side"] == "bottom":
            lx = -lx                      # mirrored when seen from the front
        x = part["x"] + lx * math.cos(r) - ly * math.sin(r)
        y = part["y"] + lx * math.sin(r) + ly * math.cos(r)
        out[pin] = (x, y)
    return out


def body_rect(ref):
    """Axis-aligned bounding box (x0, y0, x1, y1) of the part body, front-view frame."""
    part = PARTS[ref]
    fp = FP[part["fp"]]
    if ref == "OLED":
        x0 = D["oled_pin_x"] - P["oled_pin_to_edge"]
        return (x0, D["oled_cy"] - P["oled_h"] / 2, x0 + P["oled_len"], D["oled_cy"] + P["oled_h"] / 2)
    b = fp["body"]
    if b is None:
        return None
    r = math.radians(part["rot"])
    pts = []
    for (lx, ly) in [(b[0], b[1]), (b[2], b[1]), (b[2], b[3]), (b[0], b[3])]:
        if part["side"] == "bottom":
            lx = -lx
        pts.append((part["x"] + lx * math.cos(r) - ly * math.sin(r),
                    part["y"] + lx * math.sin(r) + ly * math.cos(r)))
    xs, ys = [q[0] for q in pts], [q[1] for q in pts]
    return (min(xs), min(ys), max(xs), max(ys))


# ----------------------------------------------------------------- nets ----
# net -> list of (ref, pin)
NETS = {
    "VCC": [("U1", "8"), ("R1", "2"), ("R5", "2"), ("R4", "2"), ("C1", "2"), ("C2", "2"), ("C3", "+"),
            ("OLED", "VCC"), ("BAT", "1")],
    "GND": [("U1", "4"), ("Q1", "E"), ("R3", "2"), ("R6", "2"), ("C1", "1"), ("C2", "1"), ("C3", "-"),
            ("OLED", "GND"), ("BAT", "2"),
            ("S1", "2"), ("S1", "1"), ("S2", "2"), ("S2", "1")],
    "RESET": [("U1", "1"), ("R1", "1")],
    "PB3": [("U1", "2"), ("S1", "4"), ("S1", "3")],
    "PB4": [("U1", "3"), ("R5", "1"), ("S2", "4"), ("S2", "3"), ("S3", "4"), ("S3", "3")],
    "S3LOW": [("S3", "2"), ("S3", "1"), ("R6", "1")],
    "SDA": [("U1", "5"), ("OLED", "SDA")],
    "SCL": [("U1", "7"), ("OLED", "SCL")],
    "PB1": [("U1", "6"), ("R2", "1")],
    "BASE": [("R2", "2"), ("Q1", "B"), ("R3", "1")],
    "COLL": [("Q1", "C"), ("SPK", "2"), ("D1", "A")],
    "SPKR": [("SPK", "1"), ("D1", "K"), ("R4", "1")],
}
# These part numbers are used in the schematic of the project (see docs/schemat.md).
REFS_BOTTOM = ["U1", "R1", "R2", "R3", "R4", "R5", "R6", "C1", "C2", "C3", "D1", "Q1", "SPK", "BAT"]

if VARIANT == "klin":
    # S1..S3 live on the button board: S1 joins PB3 and GND, S2 joins PB4 and GND, S3 joins PB4 and R6 (to GND).
    # KEY pads: 1 = GND, 2 = PB3, 3 = PB4, 4 = S3 low side (R6 stays on the main board).
    NETS["GND"] = [p for p in NETS["GND"] if p[0] not in ("S1", "S2")] + [("KEY", "1")]
    NETS["PB3"] = [("U1", "2"), ("KEY", "2")]
    NETS["PB4"] = [("U1", "3"), ("R5", "1"), ("KEY", "3")]
    NETS["S3LOW"] = [("R6", "1"), ("KEY", "4")]
    REFS_BOTTOM = REFS_BOTTOM + ["KEY"]


def mount_holes():
    m, W, H = P["hole_margin"], P["W"], P["H"]
    return [(m, m), (W - m, m), (m, H - m), (W - m, H - m)]


def to_json():
    out = dict(
        units="mm", frame="front view (top side), origin lower-left of the outline, +x right, +y up",
        board=dict(width=P["W"], height=P["H"], thickness=P["thickness"], corner_radius=P["corner_r"]),
        mounting_holes=[dict(x=x, y=y, diameter=P["mount_d"], keepout_radius=P["mount_keepout_r"])
                        for x, y in mount_holes()],
        parts={}, nets={k: [list(p) for p in v] for k, v in NETS.items()})
    for ref, part in PARTS.items():
        fp = FP[part["fp"]]
        out["parts"][ref] = dict(
            footprint=part["fp"], side=part["side"], value=part["value"], rotation=part["rot"],
            height_above_board=fp["height"], pads={k: dict(x=round(v[0], 3), y=round(v[1], 3))
                                                   for k, v in pad_positions(ref).items()},
            body=(None if body_rect(ref) is None else [round(v, 3) for v in body_rect(ref)]))
    return out


if __name__ == "__main__":
    print(json.dumps(D, indent=1))


# ------------------------------------------------------------------ checks ----
def _rect_overlap(a, b, m=0.0):
    return not (a[2] + m <= b[0] or b[2] + m <= a[0] or a[3] + m <= b[1] or b[3] + m <= a[1])


def _rect_circle_dist(r, cx, cy):
    dx = max(r[0] - cx, 0, cx - r[2])
    dy = max(r[1] - cy, 0, cy - r[3])
    return math.hypot(dx, dy)


def top_bodies():
    """Rectangles on the front side under which no hole/joint of a back part may lie."""
    out = []
    ref = "OLED"
    out.append((ref, body_rect(ref)))
    for ref in ("S1", "S2", "S3"):
        if ref in PARTS:
            out.append((ref, body_rect(ref)))
    return out


def violations(verbose=False):
    """List of rule violations of the current placement (empty = OK)."""
    W, H = P["W"], P["H"]
    v = []
    # bodies of the back side
    back = [r for r in PARTS if PARTS[r]["side"] == "bottom"]
    for r in back:
        b = body_rect(r)
        if b is None:
            continue
        if b[0] < 0.4 or b[1] < 0.4 or b[2] > W - 0.4 or b[3] > H - 0.4:
            v.append("%s: body outside the board" % r)
        for (mx, my) in mount_holes():
            if _rect_circle_dist(b, mx, my) < P["mount_keepout_r"]:
                v.append("%s: body in a mounting-hole keep-out" % r)
    for i, a in enumerate(back):
        for b_ in back[i + 1:]:
            ra, rb = body_rect(a), body_rect(b_)
            if ra and rb and _rect_overlap(ra, rb, 0.3):
                v.append("%s and %s: bodies overlap" % (a, b_))
    # pads
    allpads = []
    for r in PARTS:
        fp = FP[PARTS[r]["fp"]]
        for pin, (x, y) in pad_positions(r).items():
            allpads.append((r, pin, x, y, fp["pad"]))
    for (r, pin, x, y, d) in allpads:
        if PARTS[r]["side"] == "bottom":
            if x - d / 2 < 0.6 or y - d / 2 < 0.6 or x + d / 2 > W - 0.6 or y + d / 2 > H - 0.6:
                v.append("%s.%s: pad too close to the edge" % (r, pin))
            for (mx, my) in mount_holes():
                if math.hypot(x - mx, y - my) < P["mount_keepout_r"] + d / 2:
                    v.append("%s.%s: pad in a mounting-hole keep-out" % (r, pin))
            for (tr, tb) in top_bodies():
                if _rect_overlap((x - d / 2, y - d / 2, x + d / 2, y + d / 2), tb, 0.4):
                    v.append("%s.%s: lead/joint under the body of %s" % (r, pin, tr))
    for i, a in enumerate(allpads):
        for b_ in allpads[i + 1:]:
            if a[0] == b_[0]:
                continue
            gap = math.hypot(a[2] - b_[2], a[3] - b_[3]) - a[4] / 2 - b_[4] / 2
            if gap < 0.55:
                v.append("%s.%s and %s.%s: pads %.2f mm apart" % (a[0], a[1], b_[0], b_[1], gap))
    return v


def hpwl():
    tot = 0.0
    for net, pins in NETS.items():
        pts = []
        for (r, p) in pins:
            if r in PARTS:
                pts.append(pad_positions(r)[p])
        if len(pts) > 1:
            xs, ys = [q[0] for q in pts], [q[1] for q in pts]
            tot += (max(xs) - min(xs)) + (max(ys) - min(ys))
    return tot
