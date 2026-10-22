#!/usr/bin/env python3
"""Buduje paczkę produkcyjną płytki głównej: trasowanie (z pamięci podręcznej), DRC/LVS, podglądy SVG, plik KiCada, BOM.

    python3 tools/pcb/fab_build.py              # używa zapisanego trasowania (docs/plytka-glowna/trasowanie.json)
    python3 tools/pcb/fab_build.py --reroute    # liczy trasowanie od nowa (ok. 1-3 min) i zapisuje
"""
import json
import math
import sys
from pathlib import Path

import fab
import fab_drc

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/plytka-glowna"
ROUTE_JSON = OUT / "trasowanie.json"
R = fab.RULES


def merge_tracks(tracks):
    """Scala kolejne współliniowe odcinki tej samej sieci i warstwy."""
    def key(a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = math.hypot(dx, dy)
        return (round(dx / n, 3), round(dy / n, 3)) if n else (0, 0)

    out = []
    groups = {}
    for (net, L, a, b) in tracks:
        a, b = (round(a[0], 4), round(a[1], 4)), (round(b[0], 4), round(b[1], 4))
        if a != b:
            groups.setdefault((net, L), []).append([a, b])
    for (net, L), segs in groups.items():
        changed = True
        while changed:
            changed = False
            for i in range(len(segs)):
                for j in range(len(segs)):
                    if i == j or segs[i] is None or segs[j] is None:
                        continue
                    a, b = segs[i]
                    c, d = segs[j]
                    if b == c and key(a, b) == key(c, d):
                        segs[i] = [a, d]
                        segs[j] = None
                        changed = True
                    elif b == d and key(a, b) == key(d, c):
                        segs[i] = [a, c]
                        segs[j] = None
                        changed = True
            segs = [s for s in segs if s is not None]
        out += [(net, L, s[0], s[1]) for s in segs]
    return out


def load_or_route(reroute):
    if reroute or not ROUTE_JSON.exists():
        import fab_router
        r = fab_router.Router(seed=1)
        res, order = r.route(tries=12)
        if res["failed"]:
            sys.exit("trasowanie niepełne: %s" % res["failed"])
        design = dict(tracks=merge_tracks([(n, L, a, b) for (n, L, a, b) in res["tracks"]]),
                      vias=[(n, round(x, 4), round(y, 4)) for (n, x, y) in res["vias"]])
        OUT.mkdir(parents=True, exist_ok=True)
        ROUTE_JSON.write_text(json.dumps(dict(
            note="trasowanie plytki glownej (widok od strony elementow, mm, warstwa 0 = F strona elementow, 1 = B strona lutowania); "
                 "wygenerowane przez tools/pcb/fab_build.py --reroute",
            tracks=[[n, L, list(a), list(b)] for (n, L, a, b) in design["tracks"]],
            vias=[list(v) for v in design["vias"]]), indent=0))
        return design
    d = json.loads(ROUTE_JSON.read_text())
    return dict(tracks=[(n, L, tuple(a), tuple(b)) for n, L, a, b in d["tracks"]], vias=[tuple(v) for v in d["vias"]])


BOM = [
    # (ref, ilość, wartość, opis / wymagania)
    ("U1", 1, "ATtiny13A-PU, DIP-8", "zaprogramowany poza płytką (docs/programowanie.md), wkładany w gniazdo"),
    ("U1 (gniazdo)", 1, "gniazdo DIP-8, rząd 7,62 mm", "zwykłe lub precyzyjne, wysokość z układem do 8,5 mm"),
    ("R1", 1, "15 kΩ, 1/4 W", "stojący, raster 2,54 mm"),
    ("R2", 1, "470 Ω, 1/4 W", "stojący, raster 2,54 mm"),
    ("R3", 1, "47 kΩ, 1/4 W", "stojący, raster 2,54 mm"),
    ("R5, R6", 2, "8,2 kΩ, 1/4 W", "stojące, raster 2,54 mm; R5 i R6 muszą być jednakowe (dzielnik przycisków)"),
    ("R4", 1, "33 Ω, 1/2 W", "leżący, raster 12,7 mm, korpus do 9 × 3,2 mm"),
    ("C1, C2", 2, "100 nF (104), 50 V", "ceramiczny lub foliowy, raster 5,08 mm, wysokość do 6 mm"),
    ("C3", 1, "100 µF, min. 10 V", "elektrolit Ø5 mm, raster 2,0 mm, wysokość do 8 mm (zob. README)"),
    ("D1", 1, "LED 5 mm, dowolna", "dioda zabezpieczająca równolegle do głośnika"),
    ("Q1", 1, "BC547A (lub B/C), TO-92", "sterowanie głośnikiem"),
    ("DISP", 4, "przewód 0,14 mm², silikonowy, ok. 60 mm", "czerwony, czarny, zielony, żółty do modułu OLED (lub przewody Dupont żeńskie przecięte)"),
    ("KEY", 4, "przewód 0,14 mm², silikonowy", "czarny, pomarańczowy, niebieski, zielony do płytki przycisków"),
    ("BAT", 2, "przewód 0,14-0,25 mm², silikonowy", "czerwony (+) i czarny (−) od styków koszyka"),
    ("SPK", 2, "przewód 0,14 mm², silikonowy", "dwa przewody od głośnika (bez polaryzacji)"),
    ("MH1, MH2", 2, "wkręt samogwintujący M2,5 × 5 mm", "łeb od strony elementów; nie dłuższe niż 5,6 mm (ścianka za słupkiem ma 0,5 mm)"),
]


def write_bom():
    import csv
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "bom.csv", "w", newline="") as fh:
        w = csv.writer(fh, delimiter=";", lineterminator="\n")
        w.writerow(["oznaczenie", "ilość", "wartość", "uwagi"])
        w.writerows(BOM)


def main():
    write_bom()
    design = load_or_route("--reroute" in sys.argv)
    errors, warns, info = fab_drc.check(design)
    n_tr = len(design["tracks"])
    length = sum(math.dist(a, b) for (_, _, a, b) in design["tracks"])
    print("ścieżek %d (%.0f mm), przelotek %d, najmniejszy odstęp miedzi %.3f mm, najmniejszy odstęp otworów %.2f mm"
          % (n_tr, length, len(design["vias"]), info["min_clearance"], info["min_hole_gap"]))
    if errors:
        print("BŁĘDY DRC/LVS (%d):" % len(errors))
        for e in errors[:40]:
            print("  - " + e)
        return 1
    print("DRC i LVS: OK (0 błędów; każda sieć w jednym kawałku, brak zwarć)")
    import fab_kicad
    import fab_render
    import fab_silk
    tf, wf = fab_silk.layout_f()
    tb, wb = fab_silk.layout_b()
    for w_ in wf + wb:
        print("  uwaga (opisy): " + w_)
    OUT.mkdir(parents=True, exist_ok=True)
    pcb = fab_kicad.build(design, tf, tb)
    assert fab_kicad.balanced(pcb), "niezbalansowane nawiasy w pliku KiCada"
    (OUT / "tt-main.kicad_pcb").write_text(pcb)
    for side, name, ttl in (("F", "plytka-strona-elementow", "Strona elementów (F)"),
                            ("B", "plytka-strona-lutowania", "Strona lutowania (B), widok odbity")):
        (OUT / (name + ".svg")).write_text(fab_render.render(design, side, tf if side == "F" else tb, ttl))
    import fab_plan
    (OUT / "plan-montazu.svg").write_text(fab_plan.plan_montazu(design))
    (OUT / "plan-pomiarow.svg").write_text(fab_plan.plan_pomiarow(design))
    print("zapisano", (OUT / "tt-main.kicad_pcb").relative_to(ROOT), "i podglądy SVG")
    return 0


if __name__ == "__main__":
    sys.exit(main())
