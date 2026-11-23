"""Składa przeglądarkę klina 6 (jeden plik HTML z danymi wnętrza klina 5).

    python3 tools/enclosure/make_klin6_viewer.py   # -> docs/obudowa-klin-6/prototyp/przegladarka-klin6.html
Dane (wnetrze-klin5.json) tworzy proto_wedge6.py.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
tpl = (ROOT / "tools/enclosure/klin6_viewer.html").read_text()
data = (ROOT / "docs/obudowa-klin-6/prototyp/wariant-A/wnetrze-klin5.json").read_text()
out = ROOT / "docs/obudowa-klin-6/prototyp/przegladarka-klin6.html"
out.write_text(tpl.replace("/*__DATA__*/null", data))
print(out, out.stat().st_size)
