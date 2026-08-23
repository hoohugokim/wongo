#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["python-docx>=1.1"]
# ///
"""Build assets/reference.docx for quarto-manuscript-est.

Reproducible: pandoc's default reference doc restyled per ES&T requirements.
Re-run me when requirements change — never hand-edit the .docx.
Structural styles only (fonts/sizes/heading hierarchy/captions); target-dependent
concerns (double spacing, line numbers, collab font swap) are render.py's job.

Font/size: Times New Roman (12pt body/headings, 10pt captions). Task 6's
verification pass (SKILL.md VERIFIED section, 2026-07-03) checked ES&T's
official Author Guidelines but found no stated body font or point size
requirement — only "Line numbers are not required" and the section-heading
list were confirmed. In the absence of a
verified value, this uses the brief's Times New Roman 12pt default (a
standard, portal-safe serif per SKILL.md's own implementation note: "SWITCH
to a standard serif ... for the actual submission render — journal portals
dislike exotic fonts"). Revisit if a future verification pass finds an
explicit ES&T font/size requirement.
"""
import subprocess
import tempfile
from pathlib import Path

from docx import Document
from docx.shared import Pt, RGBColor

OUT = Path(__file__).resolve().parent.parent / "assets" / "reference.docx"
BODY_FONT = "Times New Roman"


def restyle(doc: Document) -> None:
    body = doc.styles["Normal"]
    body.font.name = BODY_FONT
    body.font.size = Pt(12)
    for name, italic in (("Heading 1", False), ("Heading 2", False), ("Heading 3", True)):
        s = doc.styles[name]
        s.font.name = BODY_FONT
        s.font.size = Pt(12)
        s.font.bold = not italic
        s.font.italic = italic
        s.font.color.rgb = RGBColor(0, 0, 0)
    for name in ("Caption", "Image Caption", "Table Caption"):
        try:
            s = doc.styles[name]
        except KeyError:
            continue
        s.font.name = BODY_FONT
        s.font.size = Pt(10)
        s.font.color.rgb = RGBColor(0, 0, 0)
        s.font.italic = False


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        ref = Path(td) / "reference.docx"
        with open(ref, "wb") as fh:
            subprocess.run(
                ["quarto", "pandoc", "--print-default-data-file", "reference.docx"],
                stdout=fh, check=True,
            )
        doc = Document(str(ref))
        restyle(doc)
        OUT.parent.mkdir(parents=True, exist_ok=True)
        doc.save(str(OUT))
        print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
