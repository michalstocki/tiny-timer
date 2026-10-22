"""Podglądy SVG płytki głównej: strona elementów (F) i strona lutowania (B, odbicie), z miedzią, opisami, otworami."""
import fab
import fab_silk

S = 24.0     # px/mm
M = 30
COL = dict(board="#2f6b3a", edge="#12301a", f="#c83a3a", b="#2f62d0", pad="#d9b34a", hole="#ffffff", silk="#f4f4f0")


def render(design, side="F", texts=None, title=None, cu_texts=()):
    """texts: opisy tej strony w widoku od strony elementów (x, y wyśrodkowane); dla strony B rysowane odbite razem z płytką.
    cu_texts: napisy w miedzi [(warstwa, napis, x, y, wysokość, grubość)]; rysowany tylko napis warstwy tej strony."""
    mirror = side == "B"
    W, H = fab.W, fab.H
    wpx, hpx = int(W * S + 2 * M), int(H * S + 2 * M + (30 if title else 0))

    def X(x):
        return M + ((W - x) if mirror else x) * S

    def Y(y):
        return M + (H - y) * S

    o = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" font-family="Helvetica, Arial, sans-serif">'
         % (wpx, hpx, wpx, hpx), '<rect width="100%" height="100%" fill="#fff"/>']
    o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%.1f" fill="%s" stroke="%s" stroke-width="2"/>'
             % (M, M, W * S, H * S, fab.CORNER_R * S, COL["board"], COL["edge"]))
    first, second = (0, 1) if side == "F" else (1, 0)
    for L, alpha in ((second, 0.35), (first, 1.0)):
        c = COL["f"] if L == 0 else COL["b"]
        for (net, l, a, b_) in design["tracks"]:
            if l == L:
                o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-opacity="%.2f" stroke-width="%.1f" '
                         'stroke-linecap="round"/>' % (X(a[0]), Y(a[1]), X(b_[0]), Y(b_[1]), c, alpha, fab.RULES["track"] * S))
    for (L, s_, x, y, h, t) in cu_texts:
        if L == first:
            o.append('<text x="%.1f" y="%.1f" font-size="%.1f" fill="%s" text-anchor="middle" font-weight="bold">%s</text>'
                     % (X(x), Y(y) + h * S * 0.35, h * S * 0.95, COL["f"] if L == 0 else COL["b"], s_))
    for (net, x, y) in design["vias"]:
        o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s"/><circle cx="%.1f" cy="%.1f" r="%.1f" fill="#fff"/>'
                 % (X(x), Y(y), fab.RULES["via_d"] / 2 * S, COL["pad"], X(x), Y(y), fab.RULES["via_drill"] / 2 * S))
    for p in fab.PADS:
        if p["shape"] == "rect":
            h = p["d"] / 2 * S
            o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s"/>' % (X(p["x"]) - h, Y(p["y"]) - h, 2 * h, 2 * h, COL["pad"]))
        else:
            o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s"/>' % (X(p["x"]), Y(p["y"]), p["d"] / 2 * S, COL["pad"]))
        o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="#fff"/>' % (X(p["x"]), Y(p["y"]), p["drill"] / 2 * S))
    for (mx, my) in fab.HOLES:
        o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="#fff" stroke="%s" stroke-width="1.5"/>' % (X(mx), Y(my), fab.MOUNT_D / 2 * S, COL["edge"]))
    sw = fab.RULES["silk_width"] * S
    if side == "F":
        for (_, x0, y0, x1, y1) in fab.silk_lines():
            o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="%.1f" stroke-linecap="round"/>'
                     % (X(x0), Y(y0), X(x1), Y(y1), COL["silk"], sw))
    for (s_, x, y, h) in (texts or []):
        o.append('<text x="%.1f" y="%.1f" font-size="%.1f" fill="%s" text-anchor="middle" font-weight="bold">%s</text>'
                 % (X(x), Y(y) + h * S * 0.35, h * S * 0.95, COL["silk"], s_.replace("&", "&amp;")))
    if title:
        o.append('<text x="%d" y="%d" font-size="15" fill="#222">%s</text>' % (M, hpx - 10, title))
    o.append("</svg>")
    return "\n".join(o)
