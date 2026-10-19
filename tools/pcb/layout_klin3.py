"""Back-side placement, variant "klin3" (display and buttons are separate modules, 40 x 24 mm):
result of tools/pcb/optimize.py (PCB_VARIANT=klin3, 40 24 16000 3 = width, height, iterations, seed).
Format: ref -> (footprint, x, y, rot, value). Bottom parts are mirrored when seen from the front."""
import board as B

B.LAYOUT.clear()
B.LAYOUT.update({
    "U1": ("dip8", 11.80, 14.10, 180, "ATtiny13A in DIP-8 socket"),
    "R1": ("res_v", 11.75, 5.15, 0, "15 k"),
    "R2": ("res_v", 22.85, 20.25, 180, "470"),
    "R3": ("res_v", 23.30, 10.40, 180, "47 k"),
    "R4": ("res_h", 21.85, 5.05, 180, "33, 1/2 W"),
    "R5": ("res_v", 15.60, 3.00, 180, "8.2 k"),
    "R6": ("res_v", 32.00, 12.15, 270, "8.2 k"),
    "C1": ("cap5", 15.55, 7.20, 180, "100 nF"),
    "C2": ("cap5", 6.05, 9.50, 270, "100 nF"),
    "C3": ("elco5", 7.10, 16.65, 270, "100 uF"),
    "D1": ("led", 36.60, 6.85, 270, "LED"),
    "Q1": ("to92", 22.90, 15.25, 270, "BC547B"),
    "SPK": ("wire2", 35.10, 14.90, 90, "speaker leads"),
    "BAT": ("wire2", 12.95, 8.30, 0, "battery leads"),
    "KEY": ("wire4", 28.90, 20.45, 90, "button board leads"),
    "DISP": ("wire4", 20.25, 11.15, 0, "display module leads"),
})
