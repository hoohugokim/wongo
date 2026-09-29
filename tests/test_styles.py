"""Tests for the taste layer in wongo.styles (bold caption leads, WR-style
title-block rebuild, keywords injection, page geometry, style-profile
loading). Uses plain python-docx Document() objects; the blank template
lacks a few styles Quarto's reference.docx normally ships (Author,
Abstract), so tests add them explicitly.
"""
from __future__ import annotations

import pytest
from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Mm

from wongo.errors import ConfigError
from wongo.styles import (
    apply_page_geometry,
    bold_caption_leads,
    inject_keywords,
    load_style,
    rebuild_title_block,
)


def _ensure_style(doc, name):
    if name not in {s.name for s in doc.styles}:
        doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)


# ---------------------------------------------------------------------------
# (a) bold_caption_leads


def test_body_level_caption_bold_lead_and_rest():
    doc = Document()
    p = doc.add_paragraph("Figure\xa01: A caption.", style="Caption")
    bold_caption_leads(doc, {"lead": "bold", "delimiter": ".", "align": "justify"})
    assert [r.text for r in p.runs] == ["Figure 1.", " A caption."]
    assert p.runs[0].font.bold is True
    assert not p.runs[1].font.bold
    assert p.alignment == WD_ALIGN_PARAGRAPH.JUSTIFY


def test_table_cell_caption_lead_bolded_and_prose_untouched():
    doc = Document()
    table = doc.add_table(rows=1, cols=1)
    cell = table.rows[0].cells[0]
    cap_p = cell.paragraphs[0]
    cap_p.text = "Table S\xa02: SI caption"
    prose_p = cell.add_paragraph("Table 1 shows the result")

    bold_caption_leads(doc, {"lead": "bold", "delimiter": ".", "align": "justify"})

    assert [r.text for r in cap_p.runs] == ["Table S2.", " SI caption"]
    assert cap_p.runs[0].font.bold is True

    # prose that merely starts with "Table <n>" but has no [.:] delimiter
    # right after the number must never be mistaken for a caption
    assert len(prose_p.runs) == 1
    assert prose_p.text == "Table 1 shows the result"
    assert not prose_p.runs[0].font.bold


# ---------------------------------------------------------------------------
# (b) rebuild_title_block


def _title_block_doc():
    doc = Document()
    _ensure_style(doc, "Author")
    _ensure_style(doc, "Abstract")
    doc.add_paragraph("Author One", style="Author")
    doc.add_paragraph("Author Two", style="Author")
    doc.add_paragraph("This is the abstract text.", style="Abstract")
    return doc


def _title_block_meta():
    return {
        "author": [
            {
                "name": "Jane Q. Public",
                "affiliations": [{"name": "KIST", "address": "Seoul", "country": "Korea"}],
                "corresponding": True,
                "email": "jane@kist.re.kr",
            },
            {
                "name": "John Doe",
                "affiliations": [{"name": "KIST", "address": "Seoul", "country": "Korea"}],
            },
        ]
    }


def test_rebuild_title_block_merges_authors_into_one_paragraph():
    doc = _title_block_doc()
    rebuild_title_block(doc, _title_block_meta(), {})

    paras = doc.paragraphs
    author_paras = [p for p in paras if "Jane Q. Public" in p.text and "John Doe" in p.text]
    assert len(author_paras) == 1, "expected exactly one merged author paragraph"
    merged = author_paras[0]
    assert merged.style.name == "Author"

    sup_runs = [r for r in merged.runs if r.font.superscript]
    assert [r.text for r in sup_runs] == ["a,*", "a"]

    # the abstract paragraph is untouched and still present exactly once
    abstract_paras = [p for p in paras if p.style.name == "Abstract"]
    assert len(abstract_paras) == 1
    assert abstract_paras[0].text == "This is the abstract text."


def test_rebuild_title_block_lettered_affiliation_and_corresponding_lines():
    doc = _title_block_doc()
    rebuild_title_block(doc, _title_block_meta(), {})

    paras = doc.paragraphs
    aff_paras = [p for p in paras if p.text == "a KIST, Seoul, Korea"]
    assert len(aff_paras) == 1

    corr_label = [p for p in paras if p.text.startswith("* Corresponding author")]
    assert len(corr_label) == 1
    assert corr_label[0].text == "* Corresponding author:"

    email_paras = [p for p in paras if p.text.startswith("E-mail:")]
    assert len(email_paras) == 1
    assert "jane@kist.re.kr" in email_paras[0].text
    assert "J. Q. Public" in email_paras[0].text


# ---------------------------------------------------------------------------
# (c) inject_keywords


def _keywords_doc():
    doc = Document()
    _ensure_style(doc, "Abstract")
    doc.add_paragraph("Some abstract text.", style="Abstract")
    doc.add_paragraph("Body starts here.")
    return doc


def test_inject_keywords_inserts_after_last_abstract_paragraph():
    doc = _keywords_doc()
    inject_keywords(doc, {"keywords": ["a", "b"]})

    paras = doc.paragraphs
    abs_idx = max(i for i, p in enumerate(paras) if p.style.name == "Abstract")
    kw_p = paras[abs_idx + 1]
    assert kw_p.text == "Keywords: a, b"
    assert kw_p.alignment == WD_ALIGN_PARAGRAPH.LEFT


def test_inject_keywords_disabled_does_nothing():
    doc = _keywords_doc()
    before = [p.text for p in doc.paragraphs]
    inject_keywords(doc, {"keywords": ["a", "b"]}, enabled=False)
    assert [p.text for p in doc.paragraphs] == before


def test_inject_keywords_no_abstract_paragraph_does_nothing():
    doc = Document()
    doc.add_paragraph("Just a body paragraph.")
    before = [p.text for p in doc.paragraphs]
    inject_keywords(doc, {"keywords": ["a", "b"]})
    assert [p.text for p in doc.paragraphs] == before


# ---------------------------------------------------------------------------
# (d) apply_page_geometry from the kist-wcr style


def _assert_close_emu(actual, expected_mm, tol_twips=1):
    # OOXML page geometry is stored in twentieths of a point (dxa); a
    # millimeter value that isn't an exact multiple of one dxa (635 EMU)
    # round-trips to the nearest dxa, so exact EMU equality is the wrong
    # bar here — compare within one dxa instead.
    tol = tol_twips * 635
    assert abs(int(actual) - int(Mm(expected_mm))) <= tol, (actual, Mm(expected_mm))


def test_apply_page_geometry_sets_a4_and_margins_from_kist_wcr():
    style = load_style("kist-wcr")
    doc = Document()
    apply_page_geometry(doc, style)
    sec = doc.sections[0]
    _assert_close_emu(sec.page_width, 210)
    _assert_close_emu(sec.page_height, 297)
    _assert_close_emu(sec.left_margin, 25)
    _assert_close_emu(sec.right_margin, 25)
    _assert_close_emu(sec.top_margin, 30)
    _assert_close_emu(sec.bottom_margin, 25)


# ---------------------------------------------------------------------------
# (e) load_style with an unknown name


def test_load_style_unknown_name_raises_system_exit_naming_known_styles():
    with pytest.raises(ConfigError) as excinfo:
        load_style("nope")
    message = str(excinfo.value)
    assert "nope" in message
    assert "default" in message
    assert "kist-wcr" in message


def test_inject_keywords_when_abstract_is_the_last_paragraph():
    from docx import Document
    from docx.enum.style import WD_STYLE_TYPE

    from wongo.styles import inject_keywords

    doc = Document()
    if "Abstract" not in [s.name for s in doc.styles]:
        doc.styles.add_style("Abstract", WD_STYLE_TYPE.PARAGRAPH)
    doc.add_paragraph("Only an abstract.", style="Abstract")
    inject_keywords(doc, {"keywords": ["x", "y"]})
    assert doc.paragraphs[-1].text == "Keywords: x, y"


def test_rebuild_title_block_when_authors_are_the_last_paragraphs():
    from docx import Document
    from docx.enum.style import WD_STYLE_TYPE

    from wongo.styles import rebuild_title_block

    doc = Document()
    if "Author" not in [s.name for s in doc.styles]:
        doc.styles.add_style("Author", WD_STYLE_TYPE.PARAGRAPH)
    doc.add_paragraph("Title")
    doc.add_paragraph("Ann Author", style="Author")
    doc.add_paragraph("Bob Author", style="Author")
    meta = {"author": [
        {"name": "Ann Author", "affiliations": [{"name": "KIST"}], "corresponding": True, "email": "a@x.org"},
        {"name": "Bob Author", "affiliations": [{"name": "KIST"}]},
    ]}
    rebuild_title_block(doc, meta, {})
    texts = [p.text for p in doc.paragraphs]
    assert any(t.startswith("E-mail:") for t in texts)
    assert sum("Ann Author" in t for t in texts) == 1


def test_read_front_matter_ignores_a_bom(tmp_path):
    from wongo.styles import read_front_matter

    (tmp_path / "index.qmd").write_bytes(b"\xef\xbb\xbf---\r\ntitle: T\r\nkeywords: [a]\r\n---\r\nBody\r\n")

    assert read_front_matter(tmp_path, "index.qmd") == {"title": "T", "keywords": ["a"]}
