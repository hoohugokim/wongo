"""Tests for the migrated render engine (HANDOFF step 4).

The SI cover sheet had TWO known gaps pinned here tests-first (see
HANDOFF-wongo-uplift.md): it printed journal+ms_type where the profile wants
AUTHORS (ES&T: cover sheet carries authors, title, page/figure/table counts),
and the page-count line shipped a literal placeholder string.
"""
from __future__ import annotations

import struct
import zlib

from docx import Document
from docx.oxml.ns import qn

from wongo.engine import (
    insert_toc_art,
    postprocess_main,
    prepend_si_cover,
    resolve_style,
    si_item_counts,
)


def _meta():
    return {
        "title": "Electron Bifurcation in Wastewater",
        "author": [
            {"name": "Hoo Hugo Kim", "affiliations": [{"name": "KIST"}], "corresponding": True},
            {"name": "Jane Doe", "affiliations": [{"name": "KIST"}]},
        ],
    }


def test_cover_sheet_carries_authors_and_title_not_journal():
    doc = Document()
    doc.add_paragraph("SI body")
    prepend_si_cover(
        doc,
        profile={"journal": "Environmental Science & Technology", "si": {}},
        counts={"figures": 3, "tables": 2},
        meta=_meta(),
    )
    text = "\n".join(p.text for p in doc.paragraphs[:6])
    assert "Supporting Information" in text
    assert "Electron Bifurcation in Wastewater" in text
    assert "Hoo Hugo Kim" in text and "Jane Doe" in text
    # gap 1: journal name / ms_type must NOT appear anymore
    assert "Journal:" not in text
    assert "research-article" not in text


def test_cover_sheet_page_count_is_a_live_field_not_placeholder():
    doc = Document()
    doc.add_paragraph("SI body")
    prepend_si_cover(
        doc,
        profile={"si": {}},
        counts={"figures": 0, "tables": 0},
        meta=_meta(),
    )
    paras = doc.paragraphs[:6]
    texts = [p.text for p in paras]
    # gap 2: the literal placeholder must be gone
    assert not any("fill from final page count" in t for t in texts)
    # replaced by a NUMPAGES field Word resolves on open
    xml_all = "\n".join(p._p.xml for p in paras)
    assert "NUMPAGES" in xml_all
    assert any(t.startswith("Pages:") for t in texts)


def test_cover_sheet_ends_with_page_break_before_body():
    doc = Document()
    doc.add_paragraph("SI body")
    prepend_si_cover(doc, profile={"si": {}}, counts={"figures": 0, "tables": 0}, meta=_meta())
    W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    brs = list(doc._element.body.iter(f"{W}br"))
    assert any(br.get(f"{W}type") == "page" for br in brs)


def test_explicit_style_override_wins_without_changing_project_default(monkeypatch):
    monkeypatch.setenv("WONGO_STYLE", "default")
    cfg = {"style": "kist-wcr"}

    assert resolve_style(cfg)["_name"] == "kist-wcr"
    assert resolve_style(cfg, override="default")["_name"] == "default"
    assert resolve_style(cfg)["_name"] == "kist-wcr"


# ---------------------------------------------------------------------------
# postprocess_main integration (no quarto needed: a python-docx document
# stands in for the pandoc render)



def _write_png(path, w, h):
    def chunk(tag, data):
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    raw = b"".join(b"\x00" + b"\xff\x00\x00" * w for _ in range(h))
    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw))
           + chunk(b"IEND", b""))
    path.write_bytes(png)
    return path


def _project(tmp_path):
    (tmp_path / "index.qmd").write_text(
        "---\ntitle: T\nauthor:\n  - name: A\n---\n\nBody.\n", encoding="utf-8"
    )
    return tmp_path


def _pandoc_like_docx(path):
    """A document shaped like pandoc 3.10 output: no pgSz/pgMar in sectPr."""
    doc = Document()
    sect_pr = doc.sections[0]._sectPr
    for tag in ("w:pgSz", "w:pgMar"):
        el = sect_pr.find(qn(tag))
        if el is not None:
            sect_pr.remove(el)
    doc.add_paragraph("Body text.")
    doc.add_table(rows=1, cols=2)
    doc.save(str(path))
    return path


def test_default_style_renders_without_page_geometry_and_keeps_reference_fonts(tmp_path):
    import zipfile

    project = _project(tmp_path)
    path = _pandoc_like_docx(tmp_path / "main.docx")
    with zipfile.ZipFile(str(path)) as z:
        theme_before = z.read("word/theme/theme1.xml")
    postprocess_main(path, profile={}, cfg={"style": "default"}, target="collab", project=project)
    doc = Document(str(path))
    assert doc.paragraphs[0].text == "Body text."
    # default.yml says font: null == keep the journal reference-doc fonts;
    # nothing may be forced onto styles or the theme
    assert doc.styles["Normal"].font.name is None
    with zipfile.ZipFile(str(path)) as z:
        assert z.read("word/theme/theme1.xml") == theme_before
        settings = z.read("word/settings.xml").decode()
    assert 'w:val="15"' in settings  # correctness stamp still applied


def test_forbidden_line_numbers_override_house_style_for_submission(tmp_path):
    project = _project(tmp_path)
    path = _pandoc_like_docx(tmp_path / "main.docx")
    postprocess_main(
        path, profile={"line_numbers": "forbidden"}, cfg={"style": "kist-wcr"},
        target="submission", project=project,
    )
    doc = Document(str(path))
    assert all(s._sectPr.find(qn("w:lnNumType")) is None for s in doc.sections)


def test_forbidden_line_numbers_is_not_treated_as_true(tmp_path):
    project = _project(tmp_path)
    path = _pandoc_like_docx(tmp_path / "main.docx")
    postprocess_main(
        path, profile={"line_numbers": "forbidden"}, cfg={"style": "default"},
        target="submission", project=project,
    )
    doc = Document(str(path))
    assert all(s._sectPr.find(qn("w:lnNumType")) is None for s in doc.sections)


def test_si_item_counts_exclude_figure_wrappers_but_keep_nested_and_image_tables(tmp_path):
    doc = Document()
    # 1. Quarto figure float: 1x1 wrapper holding a picture + caption
    fig_wrap = doc.add_table(rows=1, cols=1)
    fig_wrap.cell(0, 0).paragraphs[0].add_run().add_picture(
        str(_write_png(tmp_path / "f.png", 4, 4))
    )
    fig_wrap.cell(0, 0).add_paragraph("Figure S1: a figure")
    # 2. Quarto table float: 1x1 wrapper holding a nested data table
    tbl_wrap = doc.add_table(rows=1, cols=1)
    tbl_wrap.cell(0, 0).paragraphs[0].text = "Table S1: a table"
    tbl_wrap.cell(0, 0).add_table(rows=2, cols=2)
    # 3. an ordinary standalone data table
    doc.add_table(rows=3, cols=3)
    # 4. a legitimate data table that happens to contain an image
    img_tbl = doc.add_table(rows=2, cols=2)
    img_tbl.cell(1, 1).paragraphs[0].add_run().add_picture(str(tmp_path / "f.png"))

    assert si_item_counts(doc) == {"figures": 1, "tables": 3}


def test_toc_art_fits_inside_profile_box_preserving_aspect_ratio(tmp_path):
    doc = Document()
    doc.add_paragraph("Body.")
    square = _write_png(tmp_path / "toc.png", 60, 60)
    insert_toc_art(doc, square, width_mm=82.55, height_mm=44.45)
    shape = doc.inline_shapes[-1]
    assert abs(shape.height.mm - 44.45) < 0.05
    assert abs(shape.width.mm - 44.45) < 0.05  # square stays square


def test_toc_art_without_height_limit_keeps_width_behavior(tmp_path):
    doc = Document()
    doc.add_paragraph("Body.")
    square = _write_png(tmp_path / "toc.png", 60, 60)
    insert_toc_art(doc, square, width_mm=50)
    shape = doc.inline_shapes[-1]
    assert abs(shape.width.mm - 50) < 0.05


def test_si_cover_on_document_without_paragraphs_does_not_crash():
    doc = Document()
    body = doc.element.body
    for p in list(body.iter(qn("w:p"))):
        body.remove(p)
    doc.add_table(rows=1, cols=1)
    prepend_si_cover(doc, profile={"si": {}}, counts={"figures": 0, "tables": 1}, meta=_meta())
    assert doc.paragraphs[0].text == "Supporting Information"
