"""Back-side placement (iteration 1): result of tools/pcb/optimize.py (seed 23, 48 x 50 mm).
Format: ref -> (footprint, x, y, rot, value). Bottom parts are mirrored when seen from the front."""
import board as B

B.LAYOUT.update({
    "U1": ("dip8", 18.50, 10.05, 0, "ATtiny13A in DIP-8 socket"),
    "R1": ("res_v", 24.20, 10.00, 0, "15 k"),
    "R2": ("res_v", 27.00, 42.30, 90, "470"),
    "R3": ("res_v", 37.30, 39.80, 180, "47 k"),
    "R4": ("res_h", 26.95, 45.50, 0, "33, 1/2 W"),
    "R5": ("res_v", 28.20, 8.25, 90, "8.2 k"),
    "R6": ("res_v", 7.35, 10.20, 0, "8.2 k"),
    "C1": ("cap5", 25.90, 5.75, 0, "100 nF"),
    "C2": ("cap5", 3.65, 33.95, 90, "100 nF"),
    "C3": ("elco5", 23.65, 40.00, 0, "100 uF"),
    "D1": ("led", 34.90, 43.00, 270, "LED"),
    "Q1": ("to92", 32.20, 40.35, 180, "BC547B"),
    "SPK": ("wire2", 30.70, 45.40, 90, "speaker leads"),
    "BAT": ("wire2", 15.55, 40.10, 180, "battery leads"),
})

if B.VARIANT != "base":
    import importlib
    importlib.import_module("layout_" + B.VARIANT)      # replaces B.LAYOUT with the variant's placement
