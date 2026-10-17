#!/usr/bin/env bash
# Builds the firmware logic for the host (C sources compiled as C++ against
# mock AVR headers) and runs the scenarios in sim.cpp.
set -euo pipefail
cd "$(dirname "$0")/../.."
OUT=${TMPDIR:-/tmp}/tinytimer-sim
mkdir -p "$OUT"
INC="-Itools/sim/include -Ifirmware/src"
CXX=${CXX:-c++}
FLAGS="-std=c++11 -fpermissive -w -g -DF_CPU=9600000UL $INC ${SIM_FLAGS:-}"
# SIM_TARGET=calib simulates the calibration program instead of the timer
TARGET=${SIM_TARGET:-main}
[ "$TARGET" = calib ] && FLAGS="$FLAGS -DSIM_CALIB -DCAL_MIN=1"
rm -f "$OUT"/*.o
$CXX $FLAGS -c tools/sim/sim.cpp -o "$OUT/sim.o"
for f in $TARGET oled render; do
  extra=""; [ "$f" = "$TARGET" ] && extra="-Dmain=firmware_main"
  $CXX $FLAGS $extra -x c++ -c "firmware/src/$f.c" -o "$OUT/$f.o"
done
$CXX "$OUT"/*.o -o "$OUT/sim"
"$OUT/sim" ${SCENARIO:-}
