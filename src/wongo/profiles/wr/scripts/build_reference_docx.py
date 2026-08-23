#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["python-docx>=1.1"]
# ///
"""Build assets/reference.docx for quarto-manuscript-wr.

Reproducible: pandoc's default reference doc restyled per Water Research
requirements. Re-run me when requirements change — never hand-edit the .docx.
Structural styles only (fonts/sizes/heading hierarchy/captions); target-dependent
concerns (line numbers, collab font swap) are render.py's job.

Font/size: Times New Roman (12pt body/headings, 10pt captions). This skill's
verification pass (SKILL.md VERIFIED section, 2026-07-04) fetched and read
Water Research's official Guide for Authors "Writing and formatting" section
in full: it specifies single-column Word layout and editable-file
requirements, but no body font or point size is stated anywhere. In the
absence of a verified body-text font requirement, this uses the same
standard, portal-safe serif default as quarto-manuscript-est's and
quarto-manuscript-npjcw's reference docs — TNR 12pt. Revisit if a future
verification pass finds an explicit Water Research manuscript-body
font/size requirement.

IMPORTANT — line numbers: Water Research's GfA explicitly says "Please do
not include line numbering in the manuscript file, as it will be added
automatically" (profile.yml `line_numbers: false`). This reference doc does
NOT bake in line numbers, consistent with that instruction; render.py must
not insert them into the `--target submission` docx for this profile either
— Elsevier's own submission-processing pipeline adds them.
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
