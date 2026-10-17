#!/usr/bin/env python3
"""Generates the bell icon table (16x16, one 16-bit word per column, bit0 = top row)."""
ART = [
    "0000000110000000",
    "0000001111000000",
    "0000011111100000",
    "0000111111110000",
    "0000111111110000",
    "0000111111110000",
    "0001111111111000",
    "0001111111111000",
    "0001111111111000",
    "0011111111111100",
    "0011111111111100",
    "0111111111111110",
    "0111111111111110",
    "1111111111111111",
    "0000011111100000",
    "0000001111000000",
]
assert len(ART) == 16 and all(len(r) == 16 for r in ART)
out = []
for x in range(16):  # one 16-bit word per column, bit0 = top row of the icon
    w = 0
    for i in range(16):
        if ART[i][x] == "1":
            w |= 1 << i
    out.append(w)
print("static const uint16_t bell_bmp[16] PROGMEM = {")
for k in range(0, 16, 8):
    print("    " + ", ".join("0x%04X" % v for v in out[k:k + 8]) + ",")
print("};")
