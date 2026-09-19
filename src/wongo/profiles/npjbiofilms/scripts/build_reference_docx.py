#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["python-docx>=1.1"]
# ///
"""Build assets/reference.docx for quarto-manuscript-npjbiofilms.

Reproducible: pandoc's default reference doc restyled per npj Biofilms and
Microbiomes requirements. Re-run me when requirements change — never
hand-edit the .docx.
Structural styles only (fonts/sizes/heading hierarchy/captions); target-dependent
concerns (double spacing, line numbers, collab font swap) are render.py's job.

Font/size: Times New Roman (12pt body/headings, 10pt captions). This
skill's verification pass (SKILL.md VERIFIED section, 2026-07-04) fetched
and read npj Biofilms and Microbiomes' own Submission guidelines page in
full: formatting requirements only apply at acceptance, and no body font or
point size is stated anywhere in the fetched guidance (the page's own
"NOT MENTIONED" list explicitly names "font size for main text" as absent).
The one VERIFIED sans-serif rule (Arial/Helvetica, 8pt) applies only to
lettering baked into figure IMAGES, not to the manuscript body text, so it
is intentionally NOT applied here. In the absence of a verified body-text
font requirement, this uses the same standard, portal-safe serif default as
quarto-manuscript-npjcw's and quarto-manuscript-est's reference docs — TNR
12pt. Revisit if a future verification pass finds an explicit npj Biofilms
and Microbiomes manuscript-body font/size requirement.
"""
import subprocess
import tempfile
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

OUT = Path(__file__).resolve().parent.parent / "assets" / "reference.docx"
BODY_FONT = "Times New Roman"


def _style_by_name(doc: Document, style_name: str):
    """Exact UI-name lookup; `doc.styles[name]` round-trips through
    python-docx's alias table and hits a deprecated style-id fallback on
    pandoc's capitalized "Caption" (see wongo docs/docx-quirks.md)."""
    for style in doc.styles:
        if style.name == style_name:
            return style
    return None


def _set_font(style, name: str) -> None:
    """Literal font on all four rFonts slots with the theme links removed.

    A w:asciiTheme/w:hAnsiTheme attribute outranks the literal w:ascii/w:hAnsi
    on the same rFonts, so pandoc's theme-linked heading styles would keep
    rendering in Word's theme font (Aptos) under a house style that leaves
    reference-doc fonts alone (see wongo docs/docx-quirks.md)."""
    style.font.name = name
    rfonts = style.element.get_or_add_rPr().get_or_add_rFonts()
    rfonts.set(qn("w:eastAsia"), name)
    rfonts.set(qn("w:cs"), name)
    for attr in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
        if rfonts.get(qn(attr)) is not None:
            del rfonts.attrib[qn(attr)]


def restyle(doc: Document) -> None:
    body = doc.styles["Normal"]
    _set_font(body, BODY_FONT)
    body.font.size = Pt(12)
    for name, italic in (("Heading 1", False), ("Heading 2", False), ("Heading 3", True)):
        s = doc.styles[name]
        _set_font(s, BODY_FONT)
        s.font.size = Pt(12)
        s.font.bold = not italic
        s.font.italic = italic
        s.font.color.rgb = RGBColor(0, 0, 0)
    for name in ("Caption", "Image Caption", "Table Caption"):
        s = _style_by_name(doc, name)
        if s is None:
            continue
        _set_font(s, BODY_FONT)
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
