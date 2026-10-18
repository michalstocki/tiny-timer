#!/usr/bin/env python3
"""Breadboard design of the ATtiny13A timer: single source of truth.

Everything the build manual shows (steps, hole addresses, wire colours,
drawings, continuity checks) is generated from the data in this file, and
`verify()` rebuilds the electrical nets from the steps and compares them with
the schematic from the project brief (section "Schemat i mapa pinow").

Board model (60 columns; the first 30 hold the circuit, the large buttons sit in columns 32-46):
  * columns 1..30 from the left, rows a-e above the centre groove and f-j
    below it; holes a..e of one column are one strip, f..j another;
  * four power rails, each one electrically continuous:
        T+  top outer  (edge of the board)      T-  top inner (next to row a)
        B+  bottom inner (next to row j)        B-  bottom outer (edge)
    rail holes are addressed by the nearest column: "T+12";
  * the printed red/blue lines of a real board are irrelevant, only these
    four names are used.
"""
from collections import defaultdict
import json
import sys

COLS = 60
ROWS_UP = "abcde"
ROWS_DN = "fghij"
RAILS = ("T+", "T-", "B+", "B-")

# ----------------------------------------------------------------- data ----
# Item kinds:  ("wire", a, b, colour)  /  ("part", ref, pins{name: hole})
# modes: the ATtiny is programmed OUT of the circuit (own DIP-8 socket board),
# so there is a single configuration, "work" (battery operation).
BOTH = ("isp", "work")
ISP = ("isp",)
WORK = ("work",)

COLOURS = {
    "red": "czerwony", "black": "czarny", "green": "zielony", "yellow": "żółty",
    "orange": "pomarańczowy", "blue": "niebieski", "violet": "fioletowy",
    "gray": "szary", "white": "biały",
}

PARTS = {
    # ref: (kind, value, polish name)
    "U1": ("ic", "ATtiny13A", "ATtiny13A (DIP-8)"),
    "R1": ("res", "15k", "rezystor 15 kΩ (RESET do plusa)"),
    "R2": ("res", "470", "rezystor 470 Ω (baza tranzystora)"),
    "R3": ("res", "47k", "rezystor 47 kΩ (baza do masy)"),
    "R4": ("res", "33", "rezystor 33 Ω, ½ W (szeregowy z głośnikiem)"),
    "R5": ("res", "8.2k", "rezystor 8,2 kΩ (PB4 do plusa)"),
    "R6": ("res", "8.2k", "rezystor 8,2 kΩ (przycisk „−”, taki sam jak R5)"),
    "R7": ("res", "4.7k", "rezystor 4,7 kΩ (SDA do plusa, tylko jeśli moduł nie ma)"),
    "R8": ("res", "4.7k", "rezystor 4,7 kΩ (SCL do plusa, tylko jeśli moduł nie ma)"),
    "C1": ("cap", "100n", "kondensator 100 nF (przy ATtiny)"),
    "C2": ("cap", "100n", "kondensator 100 nF (przy zasilaniu OLED)"),
    "C3": ("elco", "100u", "kondensator elektrolityczny 100 µF"),
    "D1": ("led", "LED", "dioda LED (zabezpieczenie głośnika)"),
    "Q1": ("npn", "BC547A", "tranzystor BC547A"),
    "S1": ("sw", "run", "przycisk „run”"),
    "S2": ("sw", "+", "przycisk „+”"),
    "S3": ("sw", "-", "przycisk „−”"),
}

# (stage, id, kind, payload..., modes, optional)
ITEMS = []


def part(stage, ref, pins, modes=BOTH, optional=False, note=""):
    ITEMS.append(dict(stage=stage, kind="part", ref=ref, pins=pins, modes=modes,
                      optional=optional, note=note))


def wire(stage, a, b, colour, modes=BOTH, note="", optional=False):
    ITEMS.append(dict(stage=stage, kind="wire", a=a, b=b, colour=colour,
                      modes=modes, note=note, optional=optional))


# ---- stage 1: power and ATtiny ---------------------------------------------
# U1 straddles the groove in columns 11-14, notch to the left.
part(1, "U1", {"1": "f11", "2": "f12", "3": "f13", "4": "f14",
               "5": "e14", "6": "e13", "7": "e12", "8": "e11"})
wire(1, "a11", "T+11", "red", note="VCC układu (pin 8) na szynę plus")
wire(1, "j14", "B-14", "black", note="GND układu (pin 4) na szynę minus")
wire(1, "T+15", "B+15", "red", note="łączy górną i dolną szynę plus (długi przewód)")
wire(1, "T-16", "B-16", "black", note="łączy górną i dolną szynę minus (długi przewód)")
wire(1, "j8", "B+8", "red", note="plus na dolny pasek w kolumnie 8")
part(1, "R1", {"1": "h11", "2": "h8"}, note="RESET (pin 1) przez 15 kΩ do plusa")
part(1, "C1", {"1": "T+9", "2": "T-9"}, note="odsprzęganie zasilania ATtiny")
# power: battery from the start (the ATtiny is programmed OUT of the circuit
# in the user's own DIP-8 programmer socket, so nothing of the programmer
# is ever wired on this board)
wire(1, "BAT:+", "T+30", "red", note="plus koszyka 3×AAA; baterię wpinaj dopiero po sprawdzeniu zwarć")
wire(1, "BAT:-", "T-30", "black", note="minus koszyka 3×AAA")

# ---- stage 3: speaker (driver built in columns 17-27 of the upper half) -----
wire(3, "a13", "b17", "gray", note="PB1 (pin 6) do kolumny 17")
part(3, "R2", {"1": "a17", "2": "a20"}, note="PB1 do bazy tranzystora")
part(3, "Q1", {"C": "d19", "B": "d20", "E": "d21"})
part(3, "R3", {"1": "b20", "2": "b23"}, note="baza do masy")
wire(3, "a21", "T-21", "black", note="emiter tranzystora do masy")
wire(3, "a23", "T-23", "black", note="masa dla rezystora 47 kΩ")
wire(3, "a22", "T+22", "red", note="plus dla rezystora 33 Ω")
part(3, "R4", {"1": "e27", "2": "e22"}, note="33 Ω, ½ W, szeregowo z głośnikiem")
wire(3, "b19", "d26", "white", note="kolektor tranzystora do kolumny 26")
part(3, "D1", {"A": "a26", "K": "a27"}, note="anoda od strony kolektora (kolumna 26)")
wire(3, "SPK:2", "c26", "white", note="głośnik, wyprowadzenie od strony kolektora")
wire(3, "SPK:1", "c27", "white", note="głośnik, wyprowadzenie od strony rezystora 33 Ω")
part(3, "C3", {"+": "T+24", "-": "T-24"}, note="elektrolit na szynach")

# ---- stage 4: display (connector block in the lower right) ------------------
wire(4, "OLED:VCC", "i20", "red")
wire(4, "h20", "B+20", "red", note="plus dla modułu OLED")
wire(4, "OLED:SCL", "i23", "yellow")
wire(4, "h23", "b12", "yellow", note="SCL do PB2 (pin 7)")
wire(4, "OLED:SDA", "i26", "green")
wire(4, "h26", "b14", "green", note="SDA do PB0 (pin 5)")
wire(4, "OLED:GND", "B-29", "black")
part(4, "C2", {"1": "B+21", "2": "B-21"})
part(4, "R7", {"1": "j26", "2": "j20"}, optional=True,
     note="tylko jeśli moduł OLED nie ma pull-upów")
part(4, "R8", {"1": "g23", "2": "g20"}, optional=True,
     note="tylko jeśli moduł OLED nie ma pull-upów")

# ---- stage 5: buttons (left side) ------------------------------------------
part(5, "R5", {"1": "i13", "2": "i8"}, note="PB4 (pin 3) przez 8,2 kΩ do plusa")
# large (12 mm) tact switches: body about 5 columns wide, one per 6 columns
part(5, "S1", {"A1": "e32", "A2": "e34", "B1": "f32", "B2": "f34"})
wire(5, "a32", "T-32", "black", note="„run”: górna para styków do masy")
wire(5, "g34", "h12", "orange", note="„run”: dolna para styków do PB3 (pin 2)")
part(5, "S2", {"A1": "e38", "A2": "e40", "B1": "f38", "B2": "f40"})
wire(5, "a38", "T-38", "black", note="„+”: górna para styków do masy")
wire(5, "g40", "h13", "blue", note="„+”: dolna para styków do PB4 (pin 3)")
part(5, "S3", {"A1": "e44", "A2": "e46", "B1": "f44", "B2": "f46"})
part(5, "R6", {"1": "b44", "2": "b40"}, note="„−”: górna para styków do masy przez 8,2 kΩ (kolumna 40 to masa „+”); R6 ma być taki sam jak R5")
wire(5, "g44", "g13", "blue", note="„−”: dolna para styków do PB4 (pin 3)")

STAGE_TITLES = {
    1: "Zasilanie i ATtiny13A",
    3: "Głośnik",
    4: "Wyświetlacz OLED",
    5: "Przyciski",
}

# ------------------------------------------------------ reference netlist ----
# From the brief (section "Schemat i mapa pinow" and "Gloœnik 6,4 ohm").
REF_WORK = {
    "VCC": ["U1.8", "R1.2", "R4.2", "R5.2", "C1.1", "C2.1", "C3.+", "OLED:VCC", "BAT:+", "R7.2", "R8.2"],
    "GND": ["U1.4", "Q1.E", "R3.2", "S1.A1", "S1.A2", "S2.A1", "S2.A2", "R6.2",
            "C1.2", "C2.2", "C3.-", "OLED:GND", "BAT:-"],
    "RESET": ["U1.1", "R1.1"],
    "PB3": ["U1.2", "S1.B1", "S1.B2"],
    "PB4": ["U1.3", "R5.1", "S2.B1", "S2.B2", "S3.B1", "S3.B2"],
    "S3-UP": ["S3.A1", "S3.A2", "R6.1"],
    "PB0-SDA": ["U1.5", "OLED:SDA", "R7.1"],
    "PB2-SCL": ["U1.7", "OLED:SCL", "R8.1"],
    "PB1": ["U1.6", "R2.1"],
    "BASE": ["R2.2", "Q1.B", "R3.1"],
    "COLLECTOR": ["Q1.C", "SPK:2", "D1.A"],
    "SPK-R": ["SPK:1", "D1.K", "R4.1"],
}
# Items that exist as parts but whose pin is absent in a mode are skipped.


def hole_node(h):
    """Electrical node of a hole address."""
    if ":" in h:
        return "EXT/" + h
    for r in RAILS:
        if h.startswith(r):
            n = int(h[len(r):])
            assert 1 <= n <= COLS, h
            return "RAIL/" + r
    row, col = h[0], int(h[1:])
    assert 1 <= col <= COLS, h
    if row in ROWS_UP:
        return "UP/%d" % col
    if row in ROWS_DN:
        return "DN/%d" % col
    raise ValueError(h)


def valid_hole(h):
    try:
        hole_node(h)
        return True
    except Exception:
        return False


def active_items(mode, with_optional=True, upto=None):
    for it in ITEMS:
        if mode not in it["modes"]:
            continue
        if not with_optional and it["optional"]:
            continue
        if upto is not None and it["stage"] > upto:
            continue
        yield it


class DSU:
    def __init__(self):
        self.p = {}

    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        self.p[self.find(a)] = self.find(b)


def build_nets(mode, with_optional=True, upto=None):
    """Returns (dsu, pin_node) where pin_node maps 'U1.8' / 'UNO:D10' to its
    hole node; also the list of problems found while building."""
    dsu = DSU()
    pin_node = {}
    problems = []
    used = defaultdict(list)   # hole -> items

    def use(h, what):
        used[h].append(what)

    for it in active_items(mode, with_optional, upto):
        if it["kind"] == "wire":
            for end in ("a", "b"):
                h = it[end]
                if ":" in h:
                    pin_node[h] = hole_node(h)
                    dsu.find(hole_node(h))
                else:
                    use(h, "przewód %s-%s" % (it["a"], it["b"]))
            dsu.union(hole_node(it["a"]), hole_node(it["b"]))
        else:
            ref = it["ref"]
            for pin, h in it["pins"].items():
                use(h, "%s.%s" % (ref, pin))
                pin_node["%s.%s" % (ref, pin)] = hole_node(h)
                dsu.find(hole_node(h))
            if PARTS[ref][0] == "sw":   # contacts on the same side are joined
                dsu.union(hole_node(it["pins"]["A1"]), hole_node(it["pins"]["A2"]))
                dsu.union(hole_node(it["pins"]["B1"]), hole_node(it["pins"]["B2"]))
    for h, whats in used.items():
        if len(whats) > 1:
            problems.append("dwa elementy w jednym otworze %s: %s" % (h, ", ".join(whats)))
    return dsu, pin_node, problems


def verify(mode, with_optional=True, upto=None, quiet=False):
    """Compares the nets built from the steps with the reference netlist.
    Returns a list of differences (empty = identical)."""
    ref = REF_WORK
    dsu, pin_node, problems = build_nets(mode, with_optional, upto)
    diffs = list(problems)
    present = set(pin_node)
    # reference nets, restricted to pins that exist in this build
    ref_nets = {}
    for name, pins in ref.items():
        ps = [p for p in pins if p in present]
        if ps:
            ref_nets[name] = ps
    # 1. all pins of a reference net must share a built net
    for name, ps in ref_nets.items():
        roots = {dsu.find(pin_node[p]) for p in ps}
        if len(roots) > 1:
            groups = defaultdict(list)
            for p in ps:
                groups[dsu.find(pin_node[p])].append(p)
            diffs.append("sieć %s jest rozerwana: %s" % (
                name, " | ".join(",".join(g) for g in groups.values())))
    # 2. different reference nets must not be merged (short)
    root_names = defaultdict(set)
    for name, ps in ref_nets.items():
        for p in ps:
            root_names[dsu.find(pin_node[p])].add(name)
    for root, names in root_names.items():
        if len(names) > 1:
            diffs.append("ZWARCIE: sieci %s są połączone" % " + ".join(sorted(names)))
    # 3. every pin of the build must be in some reference net
    all_ref = {p for ps in ref.values() for p in ps}
    for p in sorted(present):
        if p not in all_ref:
            diffs.append("pin %s nie występuje na schemacie" % p)
    return diffs


def connected(mode, p, q, upto=None, pressed=None, exclude=()):
    """True if two points (holes or pins) are in the same net.
    pressed: ref of a button held down; exclude: refs of parts to ignore
    (only resistors/capacitors are "transparent" in this model anyway)."""
    dsu, pin_node, _ = build_nets(mode, True, upto)
    if pressed:
        sw = next(i for i in ITEMS if i["kind"] == "part" and i["ref"] == pressed)
        dsu.union(hole_node(sw["pins"]["A1"]), hole_node(sw["pins"]["B1"]))

    def node(x):
        if x in pin_node:
            return pin_node[x]
        return hole_node(x)

    return dsu.find(node(p)) == dsu.find(node(q))


def stage_mode_check():
    """VCC-GND short check after each stage for both modes."""
    out = []
    for mode in ("work",):
        for s in sorted({i["stage"] for i in ITEMS}):
            if connected(mode, "T+9", "T-4", upto=s):
                out.append("stage %d / %s: szyna plus zwarta z minus" % (s, mode))
    return out


# ------------------------------------------------------------ footprints ----
def hole_rc(h):
    """(row index 0..9 over a..j, col) of a strip hole, None for rails."""
    if h[0] in "abcdefghij" and h[1:].isdigit():
        return "abcdefghij".index(h[0]), int(h[1:])
    return None


def hole_name(r, c):
    return "abcdefghij"[r] + str(c)


def footprint(it):
    """Holes covered by the body of a part (without its own pin holes)."""
    ref = it["ref"]
    kind = d_kind(ref)
    pins = {k: hole_rc(v) for k, v in it["pins"].items()}
    cov = set()
    pts = [v for v in pins.values() if v]
    if not pts:
        return cov
    rows = [p[0] for p in pts]
    cols = [p[1] for p in pts]
    half = lambda r: r <= 4

    def clamp_rows(r0, r1):
        h = half(rows[0])
        return [r for r in range(r0, r1 + 1) if 0 <= r <= 9 and half(r) == h]

    if kind in ("res", "cap"):
        if len(pts) == 2:
            for c in range(min(cols) + 1, max(cols)):
                for r in range(min(rows), max(rows) + 1):
                    cov.add((r, c))
    elif kind == "elco":
        for r in clamp_rows(min(rows) - 1, max(rows) + 1):
            for c in range(min(cols) - 1, max(cols) + 2):
                if 1 <= c <= COLS:
                    cov.add((r, c))
    elif kind == "led":
        for r in clamp_rows(min(rows) - 1, max(rows) + 1):
            for c in range(min(cols), max(cols) + 1):
                cov.add((r, c))
    elif kind == "npn":
        for r in clamp_rows(min(rows) - 1, max(rows) + 1):
            for c in range(min(cols), max(cols) + 1):
                cov.add((r, c))
    elif kind == "sw":   # 12 mm body: about 5 columns, covers rows e and f
        cmin, cmax = min(cols), max(cols)
        for c in range(cmin - 1, cmax + 2):
            cov.add((4, c))
            cov.add((5, c))
    own = set(v for v in pins.values() if v)
    return cov - own


def d_kind(ref):
    return PARTS[ref][0]


MIN_SPAN = {"res": 3, "cap": 2}


def check_geometry(mode="work", with_optional=True):
    """Physical sanity of the layout: resistor spans, body footprints."""
    problems = []
    items = list(active_items(mode, with_optional))
    leads = defaultdict(list)       # (r,c) -> what
    foot = {}                       # ref -> set
    for it in items:
        if it["kind"] == "wire":
            for end in ("a", "b"):
                rc = hole_rc(it[end]) if ":" not in it[end] else None
                if rc:
                    leads[rc].append("przewód %s-%s" % (it["a"], it["b"]))
        else:
            for pin, h in it["pins"].items():
                rc = hole_rc(h)
                if rc:
                    leads[rc].append("%s.%s" % (it["ref"], pin))
            foot[it["ref"]] = footprint(it)
            kind = d_kind(it["ref"])
            pts = [hole_rc(h) for h in it["pins"].values()]
            if kind in ("res", "cap") and all(pts):
                (r1, c1), (r2, c2) = pts
                span = abs(c1 - c2)
                need = 5 if it["ref"] == "R4" else MIN_SPAN[kind]
                if span < need:
                    problems.append("%s: rozstaw %d kolumn < %d (za krótki)" % (it["ref"], span, need))
                if r1 != r2:
                    problems.append("%s: nóżki w różnych rzędach (%s, %s)" % (it["ref"], hole_name(r1, c1), hole_name(r2, c2)))
            if kind in ("res",) and not all(pts):
                if it["ref"] in ("R1", "R5", "R3", "R6", "R7", "R8"):
                    problems.append("%s: rezystor do szyny (pionowo) jest za krótki" % it["ref"])
    for ref, cov in foot.items():
        for rc in cov:
            for who in leads.get(rc, []):
                problems.append("%s zasłania otwór %s (jest tam %s)" % (ref, hole_name(*rc), who))
    refs = list(foot)
    for i in range(len(refs)):
        for j in range(i + 1, len(refs)):
            both = foot[refs[i]] & foot[refs[j]]
            for rc in sorted(both):
                problems.append("%s i %s zajmują ten sam obszar (%s)" % (refs[i], refs[j], hole_name(*rc)))
    return problems


def main():
    ok = True
    for mode in ("work",):
        for opt in (False, True):
            d = verify(mode, opt)
            tag = "%s%s" % (mode, "+optional" if opt else "")
            print("%-14s %s" % (tag, "ZGODNE ze schematem" if not d else "RÓŻNICE:"))
            for x in d:
                print("   -", x)
            ok &= not d
    for mode in ("work",):
        for x in check_geometry(mode):
            print("   geometria/%s: %s" % (mode, x))
            ok = False
    shorts = stage_mode_check()
    for s in shorts:
        print("   -", s)
        ok = False
    print("verdict:", "OK" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
