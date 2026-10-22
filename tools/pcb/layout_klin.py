"""Back-side placement, variant "klin" (no buttons on the main board, 48 x 36 mm):
result of tools/pcb/optimize.py (PCB_VARIANT=klin, seed 4, 15000 iterations).
Format: ref -> (footprint, x, y, rot, value). Bottom parts are mirrored when seen from the front."""
import board as B

B.LAYOUT.clear()
B.LAYOUT.update({
    "U1": ("dip8", 22.25, 25.30, 270, "ATtiny13A in DIP-8 socket"),
    "R1": ("res_v", 8.95, 25.30, 180, "15 k"),
    "R2": ("res_v", 31.30, 25.65, 0, "470"),
    "R3": ("res_v", 22.90, 10.55, 180, "47 k"),
    "R4": ("res_h", 44.75, 20.45, 90, "33, 1/2 W"),
    "R5": ("res_v", 25.50, 29.50, 90, "8.2 k"),
    "R6": ("res_v", 31.90, 29.80, 0, "8.2 k"),
    "C1": ("cap5", 10.65, 33.25, 90, "100 nF"),
    "C2": ("cap5", 11.45, 10.70, 0, "100 nF"),
    "C3": ("elco5", 23.15, 6.05, 180, "100 uF"),
    "D1": ("led", 35.30, 10.15, 180, "LED"),
    "Q1": ("to92", 30.50, 10.60, 0, "BC547B"),
    "SPK": ("wire2", 40.70, 10.15, 90, "speaker leads"),
    "BAT": ("wire2", 17.45, 6.25, 180, "battery leads"),
    "KEY": ("wire4", 35.95, 32.85, 0, "button board leads"),
})
