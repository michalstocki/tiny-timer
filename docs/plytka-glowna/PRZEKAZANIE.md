# Przekazanie: dokończenie płytki głównej na komputerze z KiCadem

Dokument dla sesji Claude Code uruchomionej na komputerze, na którym jest zainstalowany KiCad (8 lub 9). Poprzednia sesja nie miała KiCada, więc zrobiła wszystko poza eksportem plików produkcyjnych i niezależnym DRC KiCada.

**Stan 2026-10-22: kroki 1–5 wykonane w KiCadzie 10.0.7** (szczegóły w [README](README.md), sekcja „Co sprawdziłem”). Plik dla fabryki: `produkcja/tt-main-gerber.zip`. Otwarte zostają: wysokość C3 i podgląd w serwisie fabryki.

## Kontekst

- Repozytorium `tiny-timer`, gałąź **`claude/pcb-buttons-design-5fa3bc`** (wypchnięta na `origin`). Zacznij od `git fetch && git checkout claude/pcb-buttons-design-5fa3bc && git pull`.
- Projekt: minutnik ATtiny13A w obudowie „klin 4” ([README](../obudowa-klin-4/README.md)). Płytka główna 40 × 24 mm, 2 warstwy, elementy THT lutowane ręcznie, ma zostać zamówiona w fabryce (np. JLCPCB), potem zmontowana wg [instrukcji](instrukcja-montazu.md).
- Rozmieszczenie elementów jest **zamrożone** (jest podstawą modelu obudowy w Blenderze, którego tu może nie być). Nie przesuwaj elementów bez zgody właściciela.
- Decyzje właściciela (z rozmowy): moduł OLED ma własne pull-upy I2C (bez R7/R8), C3 to elektrolit Ø5 mm o rozstawie 2,0 mm, drobne przesunięcia dozwolone (≤ 1,5 mm, bez zmiany wysokości, ale tylko po ponownej kontroli kolizji z obudową; bez Blendera lepiej ich nie robić).

## Co jest zrobione

| Co | Gdzie | Stan |
| --- | --- | --- |
| Trasowanie 2 warstw, DRC i LVS własne | `tools/pcb/fab_router.py`, `fab_drc.py`, `fab_build.py` | 0 błędów, najmniejszy odstęp 0,28 mm (wymagane 0,25) |
| Plik KiCada | `docs/plytka-glowna/tt-main.kicad_pcb` (format v7) | **wygenerowany skryptem, nie otwarty w KiCadzie**; składnia sprawdzona własnym parserem, współrzędne pól zgodne z modelem |
| Podglądy, plany do instrukcji, BOM | `docs/plytka-glowna/*.svg`, `bom.csv` | gotowe |
| Instrukcja montażu z kontrolami | [`instrukcja-montazu.md`](instrukcja-montazu.md) | gotowa |
| Skrypt eksportu | `tools/pcb/export_fab.sh` | **nie uruchamiany** (flagi `kicad-cli` z pamięci) |

## Co zostało zrobić (kolejność)

1. **Otwórz `tt-main.kicad_pcb` w KiCadzie** (pcbnew). Sprawdź, czy się wczytuje: obrys 40 × 24 mm z narożnikami R3, 2 otwory M2,5, 16 stopek, 12 sieci, ścieżki obu warstw. Porównaj z `plytka-strona-elementow.svg` (F) i `plytka-strona-lutowania.svg` (B, odbicie). Jeśli KiCad zgłasza błąd wczytywania, popraw generator `tools/pcb/fab_kicad.py` (nie ręcznie plik, bo jest generowany) i uruchom `python3 tools/pcb/fab_build.py`.
2. **Uruchom** `bash tools/pcb/export_fab.sh`. Jeśli któraś flaga `kicad-cli` jest nieznana w tej wersji, sprawdź `kicad-cli pcb export gerbers --help` i popraw skrypt. Skrypt robi: DRC KiCada (`produkcja/drc-kicad.txt`), Gerbery (F.Cu, B.Cu, maska, opis, obrys), wiercenia Excellon (PTH i NPTH osobno), SVG kontrolne i `produkcja/tt-main-gerber.zip`.
3. **Przejrzyj raport DRC.** Błędy (clearance, hole-to-hole, copper-edge, shorting, unconnected, via/drill) trzeba naprawić w generatorze i wyeksportować od nowa. Dopuszczalne ostrzeżenia: brak courtyard stopek, „silkscreen overlap/clipped” (opisy lekko zachodzące na pola: fabryka je przytnie), brak przypisania stopek do biblioteki. Własny DRC wymaga odstępu 0,25 mm; domyślne reguły KiCada są luźniejsze (0,2 mm), więc to powinno przejść.
4. **Zweryfikuj Gerbery** w przeglądarce Gerberów KiCada (gerbview) lub w podglądzie fabryki: obie warstwy miedzi, maska (otwory na polach), opis (odbity poprawnie na B.SilkS), obrys i otwory (2 × Ø2,7 niemetalizowane). Sprawdź, że wiercenia w `produkcja/gerber/*.drl` mają: pola Ø0,8…1,2 mm, przelotkę Ø0,4 mm, otwory M2,5 Ø2,7 mm w osobnym pliku NPTH.
5. **Zacommituj** `docs/plytka-glowna/produkcja/` (jest mały), zmień w [`README.md`](README.md) zdanie „Status” (Gerbery wyeksportowane i sprawdzone w KiCadzie), wypchnij.
6. **Powiedz właścicielowi**, co sprawdziłeś i czego nie, oraz jak zamówić (parametry są w README, sekcja „Parametry do zamówienia”). Nie zamawiaj za niego.

## Znane ryzyka i otwarte sprawy

- **Wysokość C3**: model obudowy zakłada 8,0 mm, a typowy elektrolit Ø5 mm ma 11 mm (README, ryzyko 2). Warto zapytać właściciela o wysokość jego kondensatora, zanim zamówi płytki.
- **Opisy**: nie wszystkie opisy pól się zmieściły (README, ryzyko 3). To kosmetyka, opis pinów jest w instrukcji.
- **Orientacja widoku**: cały pakiet jest w widoku od strony elementów (x' = W − x względem `pcb-layout.json`). Elementy są na F.Cu (strona elementów), strona lutowania to B.Cu (w obudowie przy ściance pokrywy). Jeśli w KiCadzie coś wygląda odbite, sprawdź to w pierwszej kolejności.
- Własne pliki Gerber nie powstały celowo: kanoniczne są te z KiCada.

## Gotowy prompt dla nowej sesji

> Pracujemy w repozytorium `tiny-timer`, gałąź `claude/pcb-buttons-design-5fa3bc` (zrób `git fetch`, `git checkout`, `git pull`). Przeczytaj `docs/plytka-glowna/PRZEKAZANIE.md` i wykonaj wszystkie kroki z sekcji „Co zostało zrobić”: otwórz `tt-main.kicad_pcb` w KiCadzie (kicad-cli jest zainstalowany), uruchom `bash tools/pcb/export_fab.sh`, przejrzyj DRC i Gerbery, napraw ewentualne problemy w generatorze `tools/pcb/fab_*.py`, zacommituj i wypchnij wyniki. Nie przesuwaj elementów. Na końcu napisz mi, co sprawdziłeś, czego nie, i wskaż dokładny plik do wysłania do fabryki.
