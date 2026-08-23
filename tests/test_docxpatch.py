"""Regression tests for the OOXML pathology fixes.

These pin the behaviors documented in docs/docx-quirks.md — each test exists
because the corresponding bug shipped a wrong-looking manuscript at least once.
Scaffold phase: tests import the functions from legacy/render.py; when the
engine migrates into wongo.docxpatch, only the import below should change.

Run: uv run --with pytest --with python-docx --with pyyaml pytest
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "legacy"))

from docx import Document  # noqa: E402
from docx.oxml import OxmlElement  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402

import render  # noqa: E402  (legacy/render.py)


def _para_with_duplicate_ppr(doc):
    """Reproduce Quarto 1.10's invalid output: a paragraph with TWO pPr,
    the second carrying pStyle + jc=left (the one Word honors)."""
    p = doc.add_paragraph("Figure 1: A caption.")
    p.paragraph_format.line_spacing = 1.0  # creates the FIRST pPr
    first = p._p.find(qn("w:pPr"))
    extra = OxmlElement("w:pPr")
    st = OxmlElement("w:pStyle")
    st.set(qn("w:val"), "ImageCaption")
    jc = OxmlElement("w:jc")
    jc.set(qn("w:val"), "left")
    extra.append(st)
    extra.append(jc)
    first.addnext(extra)  # the SECOND pPr, as Quarto 1.10 emits it
    return p


def test_dedupe_ppr_merges_duplicates_later_wins():
    doc = Document()
    p = _para_with_duplicate_ppr(doc)
    assert len([c for c in p._p if c.tag == qn("w:pPr")]) == 2
    render.dedupe_ppr(doc)
    pprs = [c for c in p._p if c.tag == qn("w:pPr")]
    assert len(pprs) == 1
    ppr = pprs[0]
    # later pPr's properties won; pStyle reordered to first child
    assert ppr[0].tag == qn("w:pStyle")
    jc = ppr.find(qn("w:jc"))
    assert jc is not None and jc.get(qn("w:val")) == "left"


def test_normalize_ppr_order_puts_spacing_before_jc():
    doc = Document()
    p = doc.add_paragraph("text")
    ppr = p._p.get_or_add_pPr()
    # deliberately wrong order: jc before spacing (Word silently drops jc)
    jc = OxmlElement("w:jc")
    jc.set(qn("w:val"), "both")
    spacing = OxmlElement("w:spacing")
    spacing.set(qn("w:line"), "240")
    ppr.append(jc)
    ppr.append(spacing)
    render.normalize_ppr_order(doc)
    tags = [c.tag for c in p._p.find(qn("w:pPr"))]
    assert tags.index(qn("w:spacing")) < tags.index(qn("w:jc"))


def test_caption_lead_regex_handles_nbsp_and_si_prefix():
    m = render._CAPTION_LEAD.match("Figure\xa01: A caption.")
    assert m and m.group(1).replace("\xa0", " ") == "Figure 1"
    m = render._CAPTION_LEAD.match("Table S\xa02: An SI caption.")
    assert m is not None
    # prose like "Table 1 shows" (no delimiter) must NOT match the strict form
    assert render._CAPTION_LEAD.match("Table 1 shows the result") is None


def test_settings_compat_stamp(tmp_path):
    doc = Document()
    path = tmp_path / "t.docx"
    doc.save(str(path))
    render.patch_theme_fonts(path, "Cambria")
    import zipfile

    with zipfile.ZipFile(str(path)) as z:
        settings = z.read("word/settings.xml").decode()
        theme = z.read("word/theme/theme1.xml").decode()
    assert "compatibilityMode" in settings
    assert 'w:val="15"' in settings
    assert "Cambria" in theme


def test_track_changes_collab_only(tmp_path):
    for tracked in (True, False):
        doc = Document()
        path = tmp_path / f"t{tracked}.docx"
        doc.save(str(path))
        render.patch_theme_fonts(path, "Cambria", track_changes=tracked)
        import zipfile

        with zipfile.ZipFile(str(path)) as z:
            settings = z.read("word/settings.xml").decode()
        assert ("<w:trackChanges/>" in settings) is tracked
        if tracked and "<w:defaultTabStop" in settings:
            # schema order: trackChanges must precede defaultTabStop
            assert settings.index("<w:trackChanges/>") < settings.index("<w:defaultTabStop")
