"""Napisy w miedzi płytki głównej: „TOP” na F.Cu i „BOT” na B.Cu, na prośbę fabryki.

Po nich technolog fabryki sprawdza po wytrawieniu, że warstwy nie są zamienione ani odbite (pola THT są po obu stronach
takie same). Napis na B.Cu jest lustrzany, żeby czytał się od strony lutowania. Miedź napisu nie należy do żadnej sieci.
Miejsce: punkt siatki z największym odstępem od miedzi tej warstwy, który spełnia reguły DRC z zapasem, nie leży na opisach
tej strony i nie wchodzi w strefę wokół otworów M2,5. Współrzędne w widoku od strony elementów, tekst wyśrodkowany w (x, y).
"""
import math

import fab
import fab_drc
import fab_silk

TEXTS = ((0, "TOP"), (1, "BOT"))      # (warstwa: 0 = F.Cu, 1 = B.Cu, napis)
HEIGHT = 1.2                          # wysokość znaku [mm]
THICK = 0.25                          # grubość kreski [mm]: z zapasem czytelna po trawieniu miedzi 1 oz
CHAR_W = fab_silk.CHAR_W              # szerokość znaku / wysokość (zmierzona w Gerberze KiCada)
CLEAR = 0.35                          # odstęp ramki napisu od miedzi (reguła 0,25 + zapas na niedokładną szerokość liter)
SILK_GAP = 0.2                        # odstęp od opisów tej samej strony
STEP = 0.25


def text_box(s, x, y, h=HEIGHT, t=THICK):
    w = CHAR_W * h * len(s) + t
    return (x - w / 2, y - (h + t) / 2, x + w / 2, y + (h + t) / 2)


def box_gap(b, sh):
    """Odstęp prostokąta b od kształtu miedzi w notacji fab_drc (0 = nakładają się)."""
    if sh[0] == "circle":
        dx = max(b[0] - sh[1], 0, sh[1] - b[2])
        dy = max(b[1] - sh[2], 0, sh[2] - b[3])
        return math.hypot(dx, dy) - sh[3]
    if sh[0] == "rect":
        dx = max(b[0] - sh[3], sh[1] - b[2], 0)
        dy = max(b[1] - sh[4], sh[2] - b[3], 0)
        return math.hypot(dx, dy)
    return max(fab_drc.gap_rect_seg(("rect",) + tuple(b), sh), 0.0)


def placements(design, texts_f, texts_b):
    """Zwraca [(warstwa, napis, x, y, wysokość, grubość)]; AssertionError, gdy napis się nie mieści."""
    cu = fab_drc.copper(design)
    silk = {0: [fab_silk.text_box(x, y, s_, h) for (s_, x, y, h) in texts_f],
            1: [fab_silk.text_box(x, y, s_, h) for (s_, x, y, h) in texts_b]}
    out = []
    for L, s in TEXTS:
        best = None
        y = 0.0
        while y <= fab.H:
            x = 0.0
            while x <= fab.W:
                b = text_box(s, x, y)
                corners = ((b[0], b[1]), (b[2], b[1]), (b[2], b[3]), (b[0], b[3]))
                ok = all(0 < cx < fab.W and 0 < cy < fab.H for cx, cy in corners) \
                    and min(fab_drc.edge_dist(cx, cy) for cx, cy in corners) >= fab.RULES["edge_clearance"] + 0.1 \
                    and all(box_gap(b, ("circle", mx, my, 0.0)) >= fab.MOUNT_KEEPOUT for mx, my in fab.HOLES) \
                    and not any(fab_silk.box_hits_box((b[0] - SILK_GAP, b[1] - SILK_GAP, b[2] + SILK_GAP, b[3] + SILK_GAP), sb)
                                for sb in silk[L]) \
                    and not (L == 0 and any(fab_silk.box_hits_seg(b, *sl[1:]) for sl in fab.silk_lines()))
                if ok:
                    g = min(box_gap(b, sh) for sh, _, _ in cu[L])
                    if g >= CLEAR and (best is None or g > best[0]):
                        best = (g, x, y)
                x += STEP
            y += STEP
        assert best, "brak miejsca na napis w miedzi %r na warstwie %s" % (s, "FB"[L])
        out.append((L, s, round(best[1], 3), round(best[2], 3), HEIGHT, THICK))
    return out


if __name__ == "__main__":
    import fab_build
    d = fab_build.load_or_route(False)
    tf, _ = fab_silk.layout_f()
    tb, _ = fab_silk.layout_b()
    for p in placements(d, tf, tb):
        print(p)
