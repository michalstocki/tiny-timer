#!/usr/bin/env bash
# Eksport plików produkcyjnych płytki głównej z docs/plytka-glowna/tt-main.kicad_pcb przez kicad-cli (KiCad 8, 9 lub 10;
# sprawdzony na 10.0.7).
# Uruchamiać na komputerze z KiCadem:   bash tools/pcb/export_fab.sh
# Wynik: docs/plytka-glowna/produkcja/ (gerber/, drc-kicad.txt, tt-main-gerber.zip). Zip wysyłasz do fabryki.
set -euo pipefail
cd "$(dirname "$0")/../.."

KC="${KICAD_CLI:-kicad-cli}"
if ! command -v "$KC" >/dev/null 2>&1; then
  for p in "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli" "/usr/local/bin/kicad-cli" "/opt/homebrew/bin/kicad-cli"; do
    [ -x "$p" ] && KC="$p" && break
  done
fi
command -v "$KC" >/dev/null 2>&1 || [ -x "$KC" ] || { echo "Nie znaleziono kicad-cli (ustaw KICAD_CLI=/ścieżka/do/kicad-cli)"; exit 1; }
echo "kicad-cli: $KC ($("$KC" version 2>/dev/null || true))"

PCB=docs/plytka-glowna/tt-main.kicad_pcb
OUT=docs/plytka-glowna/produkcja
rm -rf "$OUT"
mkdir -p "$OUT/gerber"

echo "== 1. DRC KiCada (wszystkie błędy i ostrzeżenia do pliku, błędy wstrzymują eksport)"
"$KC" pcb drc --severity-all --units mm --format report --output "$OUT/drc-kicad.txt" "$PCB" || true
grep -E "^\*\* Found|violations|unconnected" "$OUT/drc-kicad.txt" || true
"$KC" pcb drc --severity-error --exit-code-violations --units mm --format report --output "$OUT/drc-kicad-bledy.txt" "$PCB" \
  || { echo "DRC znalazł BŁĘDY: zob. $OUT/drc-kicad-bledy.txt (eksport przerwany)"; exit 2; }

echo "== 2. Gerbery (miedź, maska, opis, obrys), rozszerzenia Protel (.gtl/.gbl/...), maska odjęta od opisu"
"$KC" pcb export gerbers --layers "F.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts" --subtract-soldermask \
  --output "$OUT/gerber/" "$PCB"

echo "== 3. Wiercenia Excellon (mm), pola metalizowane i niemetalizowane w osobnych plikach"
"$KC" pcb export drill --format excellon --excellon-units mm --excellon-separate-th --drill-origin absolute \
  --generate-map --map-format gerberx2 --output "$OUT/gerber/" "$PCB"
# mapy wierceń są tylko do podglądu: poza zipem, żeby fabryka nie wzięła ich za warstwę
mkdir -p "$OUT/mapa-wiercen" && mv "$OUT"/gerber/*-drl_map.gbr "$OUT/mapa-wiercen/"

echo "== 4. Podglądy SVG warstw do porównania z docs/plytka-glowna/plytka-strona-*.svg"
# KiCad 9+: bez --mode-single --output jest katalogiem (stary tryb przestarzały); KiCad 8 tej flagi nie zna
SVG_MODE=()
"$KC" pcb export svg --help 2>&1 | grep -q -- "--mode-single" && SVG_MODE=(--mode-single)
"$KC" pcb export svg "${SVG_MODE[@]}" --layers "F.Cu,F.SilkS,Edge.Cuts" --exclude-drawing-sheet --fit-page-to-board --output "$OUT/kicad-F.svg" "$PCB"
"$KC" pcb export svg "${SVG_MODE[@]}" --layers "B.Cu,B.SilkS,Edge.Cuts" --mirror --exclude-drawing-sheet --fit-page-to-board --output "$OUT/kicad-B.svg" "$PCB"

echo "== 5. Archiwum do wysłania do fabryki"
( cd "$OUT/gerber" && rm -f ../tt-main-gerber.zip && zip -q ../tt-main-gerber.zip ./* )
ls -l "$OUT/gerber" "$OUT/tt-main-gerber.zip"
echo "Gotowe. Przed zamówieniem otwórz zip w podglądzie fabryki (np. JLCPCB) i porównaj z podglądami SVG."
