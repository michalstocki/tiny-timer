#!/usr/bin/env python3
"""Small grid router (2 layers, vias) used only to check that the preliminary
placement can be routed. Not a production autorouter: the result is a
FEASIBILITY CHECK and a picture, not the final copper."""
import heapq
import math

import board as B

G = 0.25                    # grid in mm
INF = 10 ** 9


class Grid:
    def __init__(self):
        self.nx = int(round(B.P["W"] / G)) + 1
        self.ny = int(round(B.P["H"] / G)) + 1
        # owner[layer][ix][iy]: 0 free, -1 hard obstacle, >0 net id
        self.owner = [[[0] * self.ny for _ in range(self.nx)] for _ in range(2)]
        self.foreign_block = [[[0] * self.ny for _ in range(self.nx)] for _ in range(2)]

    def cell(self, x, y):
        return int(round(x / G)), int(round(y / G))

    def xy(self, ix, iy):
        return ix * G, iy * G


def disc_cells(g, x, y, r):
    cx, cy = g.cell(x, y)
    n = int(math.ceil(r / G)) + 1
    for ix in range(cx - n, cx + n + 1):
        for iy in range(cy - n, cy + n + 1):
            if 0 <= ix < g.nx and 0 <= iy < g.ny and math.hypot(ix * G - x, iy * G - y) <= r:
                yield ix, iy


def build_obstacles(g, net_ids):
    """Mark pads, holes, edges, mounting holes. A cell claimed by a pad of net n
    can only be entered by net n (or any net for 'hard' obstacles with id -1)."""
    W, H = B.P["W"], B.P["H"]
    clr, tw = B.P["clearance"], B.P["track_w"]
    # board edge keep-out (copper to edge >= 0.4 mm incl. half the track)
    edge = 0.5
    for L in range(2):
        for ix in range(g.nx):
            for iy in range(g.ny):
                x, y = ix * G, iy * G
                if x < edge or y < edge or x > W - edge or y > H - edge:
                    g.owner[L][ix][iy] = -1
                    continue
                # rounded corners
                r = B.P["corner_r"]
                for (ccx, ccy) in ((r, r), (W - r, r), (r, H - r), (W - r, H - r)):
                    if ((x < r and ccx == r) or (x > W - r and ccx == W - r)) and \
                       ((y < r and ccy == r) or (y > H - r and ccy == H - r)):
                        if math.hypot(x - ccx, y - ccy) > r - edge:
                            g.owner[L][ix][iy] = -1
    for (mx, my) in B.mount_holes():
        for L in range(2):
            for ix, iy in disc_cells(g, mx, my, B.P["mount_keepout_r"]):
                g.owner[L][ix][iy] = -1
    # pads
    pin_net = {}
    for net, pins in B.NETS.items():
        for ref, pin in pins:
            pin_net[(ref, pin)] = net
    pads = []
    for ref in B.PARTS:
        fp = B.FP[B.PARTS[ref]["fp"]]
        for pin, (x, y) in B.pad_positions(ref).items():
            net = pin_net.get((ref, pin))
            pads.append((ref, pin, x, y, net, fp["pad"], fp["hole"]))
    for (ref, pin, x, y, net, pad_d, hole) in pads:
        nid = net_ids.get(net, -1) if net else -1
        r = pad_d / 2 + clr + tw / 2
        for L in range(2):
            for ix, iy in disc_cells(g, x, y, r):
                cur = g.owner[L][ix][iy]
                if cur == 0:
                    g.owner[L][ix][iy] = nid
                elif cur != nid:
                    g.owner[L][ix][iy] = -1     # overlap of two nets' clearance zones
    # bosses of the buttons (non-plated holes keep-out)
    for ref, part in B.PARTS.items():
        fp = B.FP[part["fp"]]
        for (bx, by) in fp.get("bosses", []):
            for L in range(2):
                for ix, iy in disc_cells(g, part["x"] + bx, part["y"] + by, B.P["btn_boss_d"] / 2 + clr + tw / 2):
                    g.owner[L][ix][iy] = -1
    return pads


def route(max_nets=None, order=None, verbose=False):
    g = Grid()
    names = list(B.NETS)
    net_ids = {n: i + 1 for i, n in enumerate(names)}
    pads = build_obstacles(g, net_ids)
    pad_xy = {}
    for (ref, pin, x, y, net, pad_d, hole) in pads:
        pad_xy[(ref, pin)] = (x, y)
    via_r = B.P["via_d"] / 2 + B.P["clearance"] + B.P["track_w"] / 2
    spacing = int(math.ceil((B.P["track_w"] + B.P["clearance"]) / G))   # cells to dilate a track
    via_cells = int(math.ceil(via_r / G))
    tracks = {}   # net -> list of ((x0,y0),(x1,y1),layer)
    vias = {}
    failed = []

    def passable(L, ix, iy, nid):
        o = g.owner[L][ix][iy]
        return o == 0 or o == nid

    def astar(starts, goals, nid):
        # states (layer, ix, iy)
        goal_set = set(goals)
        pq = []
        dist = {}
        prev = {}
        for s in starts:
            dist[s] = 0
            heapq.heappush(pq, (0, s))
        tx = [g_[1] for g_ in goals]
        ty = [g_[2] for g_ in goals]
        gx, gy = sum(tx) / len(tx), sum(ty) / len(ty)
        while pq:
            d, s = heapq.heappop(pq)
            if d > dist.get(s, INF):
                continue
            if s in goal_set:
                path = [s]
                while path[-1] in prev:
                    path.append(prev[path[-1]])
                return path[::-1]
            L, ix, iy = s
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx_, ny_ = ix + dx, iy + dy
                if not (0 <= nx_ < g.nx and 0 <= ny_ < g.ny) or not passable(L, nx_, ny_, nid):
                    continue
                step = 1
                # prefer layer direction (top horizontal, bottom vertical), mild
                if (L == 0 and dy != 0) or (L == 1 and dx != 0):
                    step = 1.3
                t = (L, nx_, ny_)
                nd = d + step
                if nd < dist.get(t, INF):
                    dist[t] = nd
                    prev[t] = s
                    h = 0
                    heapq.heappush(pq, (nd + h, t))
            # via
            L2 = 1 - L
            if passable(L2, ix, iy, nid) and via_ok(ix, iy, nid):
                t = (L2, ix, iy)
                nd = d + 12
                if nd < dist.get(t, INF):
                    dist[t] = nd
                    prev[t] = s
                    heapq.heappush(pq, (nd, t))
        return None

    def via_ok(ix, iy, nid):
        for L in range(2):
            for jx in range(ix - via_cells, ix + via_cells + 1):
                for jy in range(iy - via_cells, iy + via_cells + 1):
                    if not (0 <= jx < g.nx and 0 <= jy < g.ny):
                        return False
                    if math.hypot(jx - ix, jy - iy) <= via_cells:
                        o = g.owner[L][jx][jy]
                        if o not in (0, nid):
                            return False
        return True

    def commit(path, nid, net):
        segs = []
        for a, b in zip(path, path[1:]):
            if a[0] == b[0]:
                segs.append((g.xy(a[1], a[2]), g.xy(b[1], b[2]), a[0]))
            else:
                vias.setdefault(net, []).append(g.xy(a[1], a[2]))
        tracks.setdefault(net, []).extend(segs)
        for (L, ix, iy) in path:
            for jx in range(ix - spacing + 1, ix + spacing):
                for jy in range(iy - spacing + 1, iy + spacing):
                    if 0 <= jx < g.nx and 0 <= jy < g.ny and g.owner[L][jx][jy] == 0:
                        g.owner[L][jx][jy] = nid
        for (L, ix, iy) in path:   # via barrel blocks both layers
            pass
        for (net_, pts) in [(net, vias.get(net, []))]:
            for (vx, vy) in pts:
                for L in range(2):
                    for ix, iy in disc_cells(g, vx, vy, via_r):
                        if g.owner[L][ix][iy] == 0:
                            g.owner[L][ix][iy] = nid

    def pin_cells(ref, pin, nid):
        x, y = pad_xy[(ref, pin)]
        cx, cy = g.cell(x, y)
        cells = []
        for L in range(2):
            cells.append((L, cx, cy))
        return cells

    nets_order = order or sorted(
        [n for n in names if len(B.NETS[n]) > 1],
        key=lambda n: (len(B.NETS[n]) > 4, -_hpwl(n, pad_xy)))
    # short nets first, then the multi-pin supply nets
    nets_order = sorted([n for n in names if len(B.NETS[n]) > 1], key=lambda n: (_hpwl(n, pad_xy)))
    for net in nets_order:
        nid = net_ids[net]
        pins = [(r, p) for (r, p) in B.NETS[net] if (r, p) in pad_xy]
        tree = set(pin_cells(*pins[0], nid))
        # make the starting pad cells passable for this net
        remaining = pins[1:]
        # connect nearest remaining pad to the tree repeatedly
        while remaining:
            best = None
            for pr in remaining:
                x, y = pad_xy[pr]
                dmin = min(math.hypot(x - g.xy(c[1], c[2])[0], y - g.xy(c[1], c[2])[1]) for c in tree)
                if best is None or dmin < best[0]:
                    best = (dmin, pr)
            pr = best[1]
            goals = pin_cells(*pr, nid)
            path = astar(list(tree), goals, nid)
            if path is None:
                failed.append((net, pr))
                remaining.remove(pr)
                continue
            commit(path, nid, net)
            tree.update(path)
            tree.update(goals)
            remaining.remove(pr)
    return dict(tracks=tracks, vias=vias, failed=failed, grid=g)


def _hpwl(net, pad_xy):
    pts = [pad_xy[p] for p in B.NETS[net] if p in pad_xy]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return (max(xs) - min(xs)) + (max(ys) - min(ys))


def merge_segments(tracks):
    """Merge collinear unit segments to longer ones."""
    out = {}
    for net, segs in tracks.items():
        by_layer = {0: [], 1: []}
        for (a, b, L) in segs:
            by_layer[L].append((a, b))
        res = []
        for L, lst in by_layer.items():
            horiz = {}
            vert = {}
            for (a, b) in lst:
                if abs(a[1] - b[1]) < 1e-9:
                    horiz.setdefault(round(a[1], 3), []).append(sorted([a[0], b[0]]))
                else:
                    vert.setdefault(round(a[0], 3), []).append(sorted([a[1], b[1]]))
            for y, rngs in horiz.items():
                for (x0, x1) in _union(rngs):
                    res.append(((x0, y), (x1, y), L))
            for x, rngs in vert.items():
                for (y0, y1) in _union(rngs):
                    res.append(((x, y0), (x, y1), L))
        out[net] = res
    return out


def _union(rngs):
    rngs = sorted(rngs)
    cur = list(rngs[0])
    res = []
    for a, b in rngs[1:]:
        if a <= cur[1] + 1e-9:
            cur[1] = max(cur[1], b)
        else:
            res.append(tuple(cur))
            cur = [a, b]
    res.append(tuple(cur))
    return res
