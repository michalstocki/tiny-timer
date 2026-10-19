#!/usr/bin/env python3
"""Simulated annealing of the back-side placement (positions and 90-degree
rotations) for a given board size. Deterministic (seeded)."""
import math
import random
import sys

import board as B
import layout  # noqa: F401


# parts that must stay close together (electrical sense), weight per mm of distance
PAIRS = [("C1", "U1", 1.5), ("C2", "OLED", 1.0), ("R1", "U1", 1.5), ("R5", "U1", 1.5),
         ("Q1", "R2", 1.5), ("Q1", "R3", 1.5), ("Q1", "D1", 1.0), ("Q1", "R4", 1.0), ("Q1", "SPK", 1.0),
         ("D1", "SPK", 1.0), ("R4", "SPK", 1.0), ("C3", "Q1", 0.7), ("R6", "S3", 1.5), ("BAT", "C3", 0.7),
         ("R2", "U1", 0.7)]


def _c(ref):
    pp = B.pad_positions(ref)
    xs = [q[0] for q in pp.values()]
    ys = [q[1] for q in pp.values()]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def cost():
    v = B.violations()
    pair = 0.0
    for a, b, wgt in PAIRS:
        (ax, ay), (bx, by) = _c(a), _c(b)
        pair += wgt * math.hypot(ax - bx, ay - by)
    return B.hpwl() + pair + 40.0 * len(v), v


def optimise(seed=1, iters=15000, movable=None):
    rnd = random.Random(seed)
    B.place_all()
    movable = movable or [r for r in B.PARTS if B.PARTS[r]["side"] == "bottom"]
    # random start inside the board
    for r in movable:
        p = B.PARTS[r]
        p["x"] = rnd.uniform(4, B.P["W"] - 4)
        p["y"] = rnd.uniform(3, B.P["H"] - 3)
        p["rot"] = rnd.choice([0, 90, 180, 270])
    best_c, _ = cost()
    cur_c = best_c
    best = {r: dict(B.PARTS[r]) for r in movable}
    T0 = 30.0
    for it in range(iters):
        T = T0 * (1 - it / iters) ** 2 + 0.02
        r = rnd.choice(movable)
        p = B.PARTS[r]
        old = dict(p)
        m = rnd.random()
        if m < 0.55:
            s = 3.0 if rnd.random() < 0.3 else 0.8
            p["x"] = round(old["x"] + rnd.gauss(0, s) * 1.0, 2)
            p["y"] = round(old["y"] + rnd.gauss(0, s) * 1.0, 2)
        elif m < 0.8:
            p["rot"] = (old["rot"] + rnd.choice([90, 180, 270])) % 360
        else:
            p["x"] = rnd.uniform(3, B.P["W"] - 3)
            p["y"] = rnd.uniform(3, B.P["H"] - 3)
        c, _ = cost()
        if c < cur_c or rnd.random() < math.exp((cur_c - c) / T):
            cur_c = c
            if c < best_c:
                best_c = c
                best = {k: dict(B.PARTS[k]) for k in movable}
        else:
            B.PARTS[r].update(old)
    for r in movable:
        B.PARTS[r].update(best[r])
    # snap to 0.05 mm
    for r in movable:
        for k in ("x", "y"):
            B.PARTS[r][k] = round(B.PARTS[r][k] * 20) / 20
    c, v = cost()
    return c, v


if __name__ == "__main__":
    W = float(sys.argv[1]) if len(sys.argv) > 1 else 48
    H = float(sys.argv[2]) if len(sys.argv) > 2 else 48
    iters = int(sys.argv[3]) if len(sys.argv) > 3 else 15000
    seed = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    B.P["W"], B.P["H"] = W, H
    B.D.update(B.derived())
    c, v = optimise(seed, iters)
    print("RESULT seed", seed, "cost %.1f" % c, "violations", len(v), "hpwl %.1f" % B.hpwl())
    for x in v[:6]:
        print("   -", x)
    for r in B.REFS_BOTTOM:
        p = B.PARTS[r]
        print('    "%s": ("%s", %.2f, %.2f, %d, "%s"),' % (r, p["fp"], p["x"], p["y"], p["rot"], p["value"]))
