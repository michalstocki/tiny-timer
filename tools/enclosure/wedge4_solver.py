"""Solver przekroju obudowy klin 4 (geometria 2D + numpy, bez bpy). Rozszerza wedge3_solver.

Zmiany względem klina 3.1 (wedge3_solver z warunkami build_wedge31.py):
  - szew tyłu leży na narożniku tyłu z podstawą (lustrzanie do frontu), więc płytka główna może zejść aż do zaokrąglenia
    (dawniej musiała się kończyć nad wargą zatrzasku na prostym odcinku tyłu);
  - ogniwa leżą w rzędzie na podłodze, oś-oś 11,5 mm: tyle wynosi rozstaw styków podwójnych Keystone 5213/5214
    (układ 2 + 1 się nie mieści: płytki styków 9,2 x 10,4 i 21,0 x 11,0 mm nachodziłyby na siebie);
  - zatrzaski pokrywy stoją w strefach na końcach (przy głośniku i przy prawym boku), poza zasięgiem ogniw: w strefie ogniw
    każdy milimetr nogi zatrzasku przy narożniku kosztował ok. 1 mm boku (noga 1,2 mm + 1,0 mm na ugięcie: bok 71,5 zamiast 65,5);
  - ogniwo przy froncie trzyma się z dala od toru noska pokrywy (ścianka gniazda styku musi go ominąć);
  - wyświetlacz ma przewody wlutowane płasko w moduł (bez wtyczek), więc nad modułem jest tylko ok. 3 mm i może on
    leżeć nad ogniwami.

Uruchomienie (numpy jest w Blenderze, nie w systemowym pythonie):
    Blender --background --python tools/enclosure/wedge4_solver.py
"""
import math
import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wedge3_solver as S  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]

CELL_R = S.CELL_R
CELL_PITCH = 11.5                     # oś-oś ogniw = rozstaw styków podwójnych Keystone 5213/5214
Z_AXIS = 7.8                          # oś ogniw nad stołem: kieszeń dolnych zaczepów styku podwójnego (7,0 pod osią) + 0,8 mm dna
CELL_KO = CELL_R + 0.3
WIRE_H = 3.0                          # przewody wlutowane w moduł i położone płasko na jego tylnej ściance
# ogniwo przy froncie: tor noska pokrywy przy zdejmowaniu kończy się na y = 7,55; za nim ścianka gniazda 0,6 mm, luz 0,25
# i brzeg płytki styku od osi ogniwa (4,75 dla podwójnej), czyli oś ogniwa A >= 13,15 mm; CELLS_KO to odpowiadająca temu odległość krawędzi strefy ogniw
NOSE_SWEEP_Y, CONTACT_HALF_W = 7.55, 4.75
CELLS_KO = NOSE_SWEEP_Y + 0.6 + 0.25 + CONTACT_HALF_W - CELL_KO
# górny róg płytki styku przy ogniwie A (5,5 nad osią, 4,75 przed nią) nie może wejść w pochyłą ścianę frontu (luz 0,5)
PLATE_TOP, PLATE_CLR = 5.5, 0.5


def cell_a_min(z=Z_AXIS):
    return max(CELLS_KO + CELL_KO, (S.PANEL + PLATE_CLR + (z + PLATE_TOP) * S.cos_t) / S.sin_t + CONTACT_HALF_W)
BACK_INTO_FILLET = 2.5                # płytka może zejść tyle poza koniec prostego odcinka tyłu (sprawdza ją i tak profil wnętrza)


def tubes(yc, z=Z_AXIS):
    return [(yc - CELL_PITCH, z), (yc, z), (yc + CELL_PITCH, z)]


def bundle_clear(pts, yc, sweep=True):
    """Czy punkty niesione przez pokrywę omijają ogniwa (przy osi środkowego ogniwa yc) i przy zdejmowaniu pionowo w górę."""
    for cy_, cz_ in tubes(yc):
        r = S.B_RH
        dy = pts[:, 0] - cy_
        dz = pts[:, 1] - cz_
        if np.any(dy * dy + dz * dz < r * r):
            return False
        if sweep and np.any((np.abs(dy) < r) & (dz < 0)):
            return False
    return True


def solve(layout_path, ra=S.RA, t_top=S.T_TOP, wire_h=WIRE_H, sides=None, skip=(), cells_ko=CELLS_KO):
    bw, bh, parts = S.load_pcb(layout_path)
    far = np.zeros((1, 2)) + 1e3
    for side in sides or [x * 0.5 for x in range(110, 172)]:
        pr = S.profile(side, ra, t_top)
        inner = pr["inner"]
        bb = S.button_board_pts(pr, side)
        if "bb" in skip:
            bb = far
        elif np.any(S.sdist_inside(inner, bb) < -1e-9):
            continue
        disp = []
        for sm in [x * 0.5 for x in range(int(2 * (S.MODULE_W / 2 + 2)), int(2 * (side - 8)))]:
            mod = S.front_pts(side, [(sm - S.MODULE_W / 2 - 0.3, sm + S.MODULE_W / 2 + 0.3, S.PANEL, S.PANEL + S.MODULE_T + 0.3)])
            wir = S.front_pts(side, [(sm - S.PLUG_W / 2 - 0.3, sm + S.PLUG_W / 2 + 0.3, S.PANEL + S.MODULE_T, S.PANEL + S.MODULE_T + wire_h)])
            allp = np.vstack([mod, wir])
            if np.any(S.sdist_inside(inner, allp) < -1e-9) or S.min_dist(allp, bb) < 1.0:
                continue
            disp.append((sm, allp))
        if "disp" in skip:
            disp = [(0.0, far)]
        if not disp:
            continue
        s_back_max = side - S.S_TANG_B + BACK_INTO_FILLET
        pcb = []
        for flip in (False, True):
            for sb_far in [x * 0.5 for x in range(int(2 * (bh + 5)), int(2 * s_back_max))]:
                p = S.back_pts(side, S.pcb_rects(parts, bh, sb_far, flip))
                if np.any(S.sdist_inside(inner, p) < -1e-9) or S.min_dist(p, bb) < 1.0:
                    continue
                pcb.append((flip, sb_far, p))
        if "pcb" in skip:
            pcb = [(False, 0.0, far)]
        if not pcb:
            continue
        for k in range(int(side / 0.5)):
            yc = k * 0.5
            cs = tubes(yc)
            if cs[0][0] - CELL_KO < cells_ko or cs[2][0] + CELL_KO > side - cells_ko or cs[0][0] < cell_a_min():
                continue
            if not all(S.sdist_inside(inner, [q])[0] >= S.B_RCH - 0.5 for q in cs):
                continue
            if "bundle" in skip:
                return dict(side=side, yc=yc)
            if not bundle_clear(bb, yc):
                continue
            dsel = [d for d in disp if bundle_clear(d[1], yc)]
            psel = [p for p in pcb if bundle_clear(p[2], yc)]
            for d in dsel:
                for p in psel:
                    if S.min_dist(d[1], p[2]) < 0.8:
                        continue
                    return dict(side=side, yc=yc, sm=d[0], flip=p[0], sb_far=p[1], z_top=pr["z_top"], z_ceil=pr["z_ceil"], H=pr["H"])
    return None


def describe(r, ra=S.RA):
    side = r["side"]
    h = side * math.sqrt(3) / 2 - ra
    area = math.sqrt(3) / 4 * side ** 2 - (math.sqrt(3) - math.pi / 3) * (ra ** 2 + 2 * S.RB ** 2)
    return f"bok {side:5.1f}  wysokość {h:5.1f}  szerokość {side - 2 * (math.sqrt(3) - 1) * S.RB:5.1f}  pole {area / 100:5.1f} cm2"


if __name__ == "__main__":
    S.GRID = float(os.environ.get("TT_GRID", "0.5"))
    lp = os.environ.get("TT_LAYOUT", str(ROOT / "docs/pcb-klin3/pcb-layout.json"))
    r0 = solve(lp)
    print("KLIN 4", describe(r0), {k: round(v, 2) for k, v in r0.items() if k in ("yc", "sm", "sb_far", "flip")})
    if os.environ.get("TT_SENS"):
        for label, kw in (("bez ogniw", dict(skip=("bundle",))), ("bez płytki głównej", dict(skip=("pcb",))),
                          ("bez wyświetlacza", dict(skip=("disp",))), ("bez płytki przycisków", dict(skip=("bb",))),
                          ("bez odstępu od noska", dict(cells_ko=0.0)), ("RA 16", dict(ra=16.0))):
            r = solve(lp, **kw)
            print(f"SENS {label:24s}", describe(r, kw.get("ra", S.RA)) if r else "brak")
