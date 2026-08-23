#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["python-docx>=1.1"]
# ///
"""Build assets/reference.docx for quarto-manuscript-envmicrobiome.

Reproducible: pandoc's default reference doc restyled per Environmental
Microbiome requirements. Re-run me when requirements change — never
hand-edit the .docx. Structural styles only (fonts/sizes/heading
hierarchy/captions); target-dependent concerns (double spacing, line
numbers) are render.py's job — this journal DOES verify both double-line
spacing and line+page numbering as initial-submission requirements (see
SKILL.md VERIFIED, 2026-07-04), unlike some Nature-brand sibling profiles
that defer formatting to acceptance.

Font/size: Times New Roman (12pt body/headings, 10pt captions). This
skill's verification pass (SKILL.md VERIFIED section, 2026-07-04) fetched
and read Environmental Microbiome's own "Preparing main manuscript text"
section in full: it specifies double-line spacing, line/page numbering,
SI units, and acceptable file formats (DOC/DOCX/RTF/TeX-LaTeX), but states
no body font family or point size anywhere. The journal's only VERIFIED
font/size rules apply to text baked into FIGURE images (fonts must be
embedded; figure lettering legible at 85mm/170mm final print width), not
to the manuscript body text, so that rule is intentionally NOT applied
here. In the absence of a verified body-text font requirement, this uses
the same standard, portal-safe serif default as the other profiles in this
library (e.g. quarto-manuscript-npjcw, quarto-manuscript-est) — TNR 12pt.
Revisit if a future verification pass finds an explicit Environmental
Microbiome manuscript-body font/size requirement.
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
