"""Router 2 warstw dla płytki głównej: siatka 0,1 mm, ruchy co 45°, przelotki, kary za zakręty i przelotki.

Warstwy: 0 = F (strona elementów), 1 = B (strona lutowania). Wynik: ścieżki i przelotki w mm w widoku od strony elementów.
Nie jest to układ gwarantujący DRC: poprawność sprawdza niezależnie fab_drc.py (geometria dokładna, nie siatkowa).
"""
import heapq
import math
import random

import fab

G = 0.1
R = fab.RULES
TW, CLR, VIA_D = R["track"], R["clearance"], R["via_d"]
INF = 1e18
DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
STEP = [1.0, math.sqrt(2)] * 4
NO_DIR = 8


class Board:
    def __init__(self, nets):
        self.nx = int(round(fab.W / G)) + 1
        self.ny = int(round(fab.H / G)) + 1
        self.occ = [[0] * (self.nx * self.ny) for _ in range(2)]     # 0 wolne, -1 twarda przeszkoda, >0 sieć
        self.nets = nets
        self.nid = {n: i + 1 for i, n in enumerate(nets)}

    def idx(self, ix, iy):
        return ix * self.ny + iy

    def stamp(self, layer, x, y, r, owner):
        """Zaznacz węzły w odległości <= r od (x, y); na styku dwóch różnych sieci węzeł staje się twardą przeszkodą."""
        n = int(math.ceil(r / G)) + 1
        cx, cy = int(round(x / G)), int(round(y / G))
        occ = self.occ[layer]
        for ix in range(max(0, cx - n), min(self.nx, cx + n + 1)):
            dx = ix * G - x
            for iy in range(max(0, cy - n), min(self.ny, cy + n + 1)):
                dy = iy * G - y
                if dx * dx + dy * dy <= r * r:
                    i = ix * self.ny + iy
                    cur = occ[i]
                    if cur == 0:
                        occ[i] = owner
                    elif cur != owner:
                        occ[i] = -1


def build_board(nets):
    b = Board(nets)
    # krawędź płytki i zaokrąglone narożniki: miedź (z połową ścieżki) >= edge_clearance od krawędzi
    lim = R["edge_clearance"] + TW / 2
    for ix in range(b.nx):
        x = ix * G
        for iy in range(b.ny):
            y = iy * G
            d = min(x, fab.W - x, y, fab.H - y)
            r = fab.CORNER_R
            cx = r if x < r else (fab.W - r if x > fab.W - r else None)
            cy = r if y < r else (fab.H - r if y > fab.H - r else None)
            if cx is not None and cy is not None:
                d = r - math.hypot(x - cx, y - cy)
            if d < lim:
                for L in range(2):
                    b.occ[L][b.idx(ix, iy)] = -1
    for (mx, my) in fab.HOLES:
        for L in range(2):
            b.stamp(L, mx, my, fab.MOUNT_KEEPOUT, -1)
    for p in fab.PADS:
        owner = b.nid.get(p["net"], -1)
        r = (p["d"] / 2) * (math.sqrt(2) if p["shape"] == "rect" else 1.0) + CLR + TW / 2
        for L in range(2):
            b.stamp(L, p["x"], p["y"], r, owner)
    return b


class Router:
    def __init__(self, seed=0):
        self.nets = [n for n in fab.net_names() if len([p for p in fab.PADS if p["net"] == n]) > 1]
        self.base = build_board(self.nets)
        self.pads = {}
        for p in fab.PADS:
            self.pads.setdefault(p["net"], []).append(p)
        self.rng = random.Random(seed)

    # -------------------------------------------------------------- jedna próba
    def attempt(self, order, via_penalty=18.0, bend=(0.35, 1.0)):
        occ = [list(self.base.occ[0]), list(self.base.occ[1])]
        nx, ny = self.base.nx, self.base.ny
        via_rho = (VIA_D / 2 + CLR + TW / 2) - (TW + CLR) + 0.12
        vr_stamp = VIA_D / 2 + CLR + TW / 2
        tracks, vias, failed = [], [], []

        def stamp(layer, x, y, r, owner):
            n = int(math.ceil(r / G)) + 1
            cx, cy = int(round(x / G)), int(round(y / G))
            o = occ[layer]
            for ix in range(max(0, cx - n), min(nx, cx + n + 1)):
                dx = ix * G - x
                for iy in range(max(0, cy - n), min(ny, cy + n + 1)):
                    dy = iy * G - y
                    if dx * dx + dy * dy <= r * r:
                        i = ix * ny + iy
                        cur = o[i]
                        if cur == 0:
                            o[i] = owner
                        elif cur != owner:
                            o[i] = -1

        def via_ok(ix, iy, nid):
            rr = int(math.ceil(via_rho / G))
            for L in range(2):
                o = occ[L]
                for jx in range(max(0, ix - rr), min(nx, ix + rr + 1)):
                    for jy in range(max(0, iy - rr), min(ny, iy + rr + 1)):
                        if (jx - ix) ** 2 + (jy - iy) ** 2 <= rr * rr:
                            v = o[jx * ny + jy]
                            if v != 0 and v != nid:
                                return False
            return True

        def octile(ix, iy, tx, ty):
            dx, dy = abs(ix - tx), abs(iy - ty)
            return (dx + dy) + (math.sqrt(2) - 2) * min(dx, dy)

        def astar(starts, goals, tx, ty, nid):
            goal = set(goals)
            heap = []
            best = {}
            prev = {}
            for s in starts:
                st = (s[0], s[1], s[2], NO_DIR)
                best[st] = 0.0
                heapq.heappush(heap, (octile(s[1], s[2], tx, ty), 0.0, st))
            while heap:
                f, g, st = heapq.heappop(heap)
                if g > best.get(st, INF):
                    continue
                L, ix, iy, d = st
                if (L, ix, iy) in goal:
                    path = [st]
                    while path[-1] in prev:
                        path.append(prev[path[-1]])
                    return [(p[0], p[1], p[2]) for p in path[::-1]]
                o = occ[L]
                for nd, (dx, dy) in enumerate(DIRS):
                    jx, jy = ix + dx, iy + dy
                    if not (0 <= jx < nx and 0 <= jy < ny):
                        continue
                    v = o[jx * ny + jy]
                    if v != 0 and v != nid:
                        continue
                    if dx and dy:                       # skos: oba sąsiady ortogonalne muszą być wolne
                        v1, v2 = o[jx * ny + iy], o[ix * ny + jy]
                        if (v1 != 0 and v1 != nid) or (v2 != 0 and v2 != nid):
                            continue
                    cost = STEP[nd]
                    if d != NO_DIR and d != nd:
                        turn = min((nd - d) % 8, (d - nd) % 8)
                        cost += bend[0] if turn == 1 else bend[1]
                    ng = g + cost
                    t = (L, jx, jy, nd)
                    if ng < best.get(t, INF):
                        best[t] = ng
                        prev[t] = st
                        heapq.heappush(heap, (ng + octile(jx, jy, tx, ty), ng, t))
                L2 = 1 - L
                if via_ok(ix, iy, nid) and occ[L2][ix * ny + iy] in (0, nid):
                    t = (L2, ix, iy, NO_DIR)
                    ng = g + via_penalty
                    if ng < best.get(t, INF):
                        best[t] = ng
                        prev[t] = st
                        heapq.heappush(heap, (ng + octile(ix, iy, tx, ty), ng, t))
            return None

        def pad_nodes(p, rad):
            cx, cy = int(round(p["x"] / G)), int(round(p["y"] / G))
            out = []
            n = int(math.ceil(rad / G)) + 1
            for ix in range(cx - n, cx + n + 1):
                for iy in range(cy - n, cy + n + 1):
                    if math.hypot(ix * G - p["x"], iy * G - p["y"]) <= rad and 0 <= ix < nx and 0 <= iy < ny:
                        out.append((ix, iy))
            return out

        for net in order:
            nid = self.base.nid[net]
            pads = list(self.pads[net])
            first = pads.pop(0)
            tree = {(L, ix, iy) for L in range(2) for ix, iy in pad_nodes(first, 0.12)}
            remaining = pads
            tree_pts = [(first["x"], first["y"])]
            while remaining:
                # najbliższy jeszcze niepołączony pad
                remaining.sort(key=lambda q: min(math.hypot(q["x"] - a, q["y"] - b_) for a, b_ in tree_pts))
                tgt = remaining.pop(0)
                goals = [(L, ix, iy) for L in range(2) for ix, iy in pad_nodes(tgt, 0.12)]
                path = astar(list(tree), goals, int(round(tgt["x"] / G)), int(round(tgt["y"] / G)), nid)
                if path is None:
                    failed.append((net, tgt["ref"], tgt["pin"]))
                    continue
                # zapis: odcinki (L) i przelotki; dociągnięcie końców do środków pól
                segs = []
                for a, b_ in zip(path, path[1:]):
                    if a[0] == b_[0]:
                        segs.append((a[0], (a[1] * G, a[2] * G), (b_[1] * G, b_[2] * G)))
                    else:
                        vias.append((net, a[1] * G, a[2] * G))
                        stamp(0, a[1] * G, a[2] * G, vr_stamp, nid)
                        stamp(1, a[1] * G, a[2] * G, vr_stamp, nid)
                tracks += [(net,) + s for s in segs]
                for (L, ix, iy) in path:
                    stamp(L, ix * G, iy * G, TW + CLR, nid)
                tree.update(path)
                tree_pts += [(a[1] * G, a[2] * G) for a in path[::4]]
                tree_pts.append((tgt["x"], tgt["y"]))
                for L in range(2):
                    for ix, iy in pad_nodes(tgt, 0.12):
                        tree.add((L, ix, iy))
        return dict(tracks=tracks, vias=vias, failed=failed)

    # -------------------------------------------------------------- wiele prób
    def route(self, tries=40, verbose=True):
        def hp(net):
            pts = [(p["x"], p["y"]) for p in self.pads[net]]
            xs, ys = [q[0] for q in pts], [q[1] for q in pts]
            return (max(xs) - min(xs)) + (max(ys) - min(ys))

        base = sorted(self.nets, key=hp)
        best = None
        for t in range(tries):
            order = list(base)
            if t:
                self.rng.shuffle(order)
                if t % 2:
                    order.sort(key=lambda n: hp(n) * self.rng.uniform(0.5, 1.5))
            res = self.attempt(order)
            score = (len(res["failed"]), len(res["vias"]), sum(math.dist(a, b_) for (_, _, a, b_) in res["tracks"]))
            if verbose:
                print("  próba %2d: niepołączone %d, przelotki %d, długość %.0f mm" % (t, score[0], score[1], score[2]))
            if best is None or score < best[0]:
                best = (score, res, order)
            if best[0][0] == 0 and t >= 3:
                break
        return best[1], best[2]


if __name__ == "__main__":
    r = Router(seed=1)
    res, order = r.route(tries=6)
    print("niepołączone:", res["failed"])
