#!/usr/bin/env python3
"""Builds the preliminary PCB package: routing check + previews + JSON."""
import json
import os
import sys

import board as B
import layout  # noqa: F401  (fills B.LAYOUT)
import export
import render
import router
import spec

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "..", "docs", "pcb")


def main():
    os.makedirs(OUT, exist_ok=True)
    B.place_all()
    res = router.route()
    print("nets failed:", res["failed"])
    segs = router.merge_segments(res["tracks"])
    n_seg = sum(len(v) for v in segs.values())
    n_via = sum(len(v) for v in res["vias"].values())
    print("segments:", n_seg, "vias:", n_via)
    open(os.path.join(OUT, "pcb-przod.svg"), "w").write(render.top_view(res))
    open(os.path.join(OUT, "pcb-tyl.svg"), "w").write(render.bottom_view(res))
    v = B.violations()
    print("placement violations:", v)
    export.write_all(OUT)
    spec.write(OUT)
    n = sum(len(x) for x in B.NETS.values())
    print("pins in nets:", n)
    if v:
        return 1
    return 0 if not res["failed"] else 1


if __name__ == "__main__":
    sys.exit(main())
