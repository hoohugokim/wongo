"""Tests for wongo.engine.diff — tracked-changes stamping for revisions.

The S6 promise: given the originally submitted DOCX and a revised render,
produce a copy of the revised document whose differences from the original
appear as real Word track changes (w:ins / w:del), so journals that demand
a marked-up revision get one without a manual Word Compare session.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from docx import Document
from docx.opc.constants import RELATIONSHIP_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from wongo.engine.diff import diff_documents
from wongo.errors import InputError


def _make_doc(tmp_path: Path, name: str, paragraphs: list[str]) -> Path:
    doc = Document()
    for text in paragraphs:
        doc.add_paragraph(text)
    path = tmp_path / name
    doc.save(str(path))
    return path


def _body_paras(doc_path: Path) -> list:
    return Document(str(doc_path)).paragraphs


def _add_hyperlink(paragraph, text: str, url: str = "https://example.com") -> None:
    rel_id = paragraph.part.relate_to(
        url, RELATIONSHIP_TYPE.HYPERLINK, is_external=True
    )
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), rel_id)
    run = OxmlElement("w:r")
    node = OxmlElement("w:t")
    node.text = text
    run.append(node)
    hyperlink.append(run)
    paragraph._p.append(hyperlink)


def _text_run(text: str):
    run = OxmlElement("w:r")
    node = OxmlElement("w:t")
    node.text = text
    run.append(node)
    return run


def _ins_texts(p) -> list[str]:
    out = []
    for ins in p._p.findall(qn("w:ins")):
        for r in ins.findall(qn("w:r")):
            for t in r.findall(qn("w:t")):
                out.append(t.text or "")
    return out


def _del_texts(p) -> list[str]:
    out = []
    for dele in p._p.findall(qn("w:del")):
        for r in dele.findall(qn("w:r")):
            for dt in r.findall(qn("w:delText")):
                out.append(dt.text or "")
    return out


def test_identical_documents_produce_no_changes(tmp_path):
    orig = _make_doc(tmp_path, "a.docx", ["Same one.", "Same two."])
    rev = _make_doc(tmp_path, "b.docx", ["Same one.", "Same two."])
    report = diff_documents(orig, rev, tmp_path / "out.docx")
    assert report["inserted_words"] == 0
    assert report["deleted_words"] == 0
    for p in _body_paras(tmp_path / "out.docx"):
        assert _ins_texts(p) == []
        assert _del_texts(p) == []


def test_word_replacement_emits_del_then_ins_in_same_paragraph(tmp_path):
    orig = _make_doc(tmp_path, "a.docx", ["The catalyst was copper."])
    rev = _make_doc(tmp_path, "b.docx", ["The catalyst was nickel."])
    diff_documents(orig, rev, tmp_path / "out.docx")
    p = _body_paras(tmp_path / "out.docx")[0]
    dels = "".join(_del_texts(p))
    inss = "".join(_ins_texts(p))
    assert "copper" in dels
    assert "nickel" in inss
    # unchanged words stay as plain runs outside any tracking element
    plain = "".join(
        t.text or ""
        for r in p._p.findall(qn("w:r"))
        for t in r.findall(qn("w:t"))
    )
    assert "catalyst" in plain and "copper" not in plain and "nickel" not in plain


def test_inserted_paragraph_is_fully_tracked(tmp_path):
    orig = _make_doc(tmp_path, "a.docx", ["First paragraph."])
    rev = _make_doc(tmp_path, "b.docx", ["First paragraph.", "A brand new paragraph."])
    diff_documents(orig, rev, tmp_path / "out.docx")
    paras = _body_paras(tmp_path / "out.docx")
    assert len(paras) == 2
    # python-docx's .text does not see inside w:ins; extract via the tracker
    assert "".join(_ins_texts(paras[1])) == "A brand new paragraph."
    assert paras[1].text == ""  # nothing outside the tracking wrapper


def test_deleted_paragraph_retained_as_full_deletion(tmp_path):
    orig = _make_doc(tmp_path, "a.docx", ["Keep me.", "Delete me entirely.", "Keep me too."])
    rev = _make_doc(tmp_path, "b.docx", ["Keep me.", "Keep me too."])
    diff_documents(orig, rev, tmp_path / "out.docx")
    paras = _body_paras(tmp_path / "out.docx")
    assert len(paras) == 3  # deletion retained in place
    deleted = ["".join(_del_texts(p)) for p in paras]
    assert "Delete me entirely." in deleted
    # the retained deletion paragraph carries no visible w:t text
    assert paras[1].text == ""


def test_deletions_use_del_text_element(tmp_path):
    orig = _make_doc(tmp_path, "a.docx", ["Original wording here."])
    rev = _make_doc(tmp_path, "b.docx", ["Revised wording here."])
    diff_documents(orig, rev, tmp_path / "out.docx")
    p = _body_paras(tmp_path / "out.docx")[0]
    for dele in p._p.findall(qn("w:del")):
        assert dele.findall(qn("w:r"))
        for r in dele.findall(qn("w:r")):
            assert r.findall(qn("w:delText"))
            assert not r.findall(qn("w:t"))  # deletions never use w:t


def test_author_and_date_stamped_on_tracking_elements(tmp_path):
    orig = _make_doc(tmp_path, "a.docx", ["Old line."])
    rev = _make_doc(tmp_path, "b.docx", ["New line."])
    diff_documents(orig, rev, tmp_path / "out.docx",
                   author="Coauthor Round", date="2026-08-25T00:00:00Z")
    p = _body_paras(tmp_path / "out.docx")[0]
    for tag in ("w:ins", "w:del"):
        el = p._p.find(qn(tag))
        assert el is not None
        assert el.get(qn("w:author")) == "Coauthor Round"
        assert el.get(qn("w:date")) == "2026-08-25T00:00:00Z"


def test_tables_are_left_untouched_but_reported(tmp_path):
    for name, value in (("a.docx", "old"), ("b.docx", "new")):
        doc = Document()
        doc.add_paragraph("Intro.")
        doc.add_table(rows=1, cols=2).cell(0, 0).text = value
        doc.save(str(tmp_path / name))
    report = diff_documents(tmp_path / "a.docx", tmp_path / "b.docx",
                            tmp_path / "out.docx")
    assert report["tables_differ"] is True
    out = Document(str(tmp_path / "out.docx"))
    assert out.tables[0].cell(0, 0).text == "new"  # untouched, no crash


def test_changed_hyperlink_paragraph_is_tracked_with_link_preserved(tmp_path):
    """Quarto emits every crossref and linked citation as w:hyperlink, so a
    real manuscript's body paragraphs are almost all 'hyperlink paragraphs';
    they must be diffed, and the link must survive exactly once, in order."""
    orig = _make_doc(tmp_path, "a.docx", ["See old source."])
    revised = Document()
    paragraph = revised.add_paragraph()
    paragraph.add_run("See ")
    _add_hyperlink(paragraph, "new")
    paragraph.add_run(" source.")
    revised.save(str(tmp_path / "b.docx"))

    report = diff_documents(orig, tmp_path / "b.docx", tmp_path / "out.docx")

    assert report["rich_paragraphs_skipped"] == 0
    output = Document(str(tmp_path / "out.docx")).paragraphs[0]
    links = output._p.findall(qn("w:hyperlink"))
    assert len(links) == 1
    # python-docx's Hyperlink.text ignores runs wrapped in w:ins — read the XML
    assert "".join(t.text or "" for t in links[0].iter(qn("w:t"))) == "new"
    # visible reading order: equal + inserted text, deletions excluded
    visible = "".join(
        t.text or "" for t in output._p.iter(qn("w:t"))
    )
    assert visible == "See new source."
    assert "old" in "".join(dt.text or "" for dt in output._p.iter(qn("w:delText")))
    assert "new" in "".join(
        t.text or "" for ins in output._p.iter(qn("w:ins")) for t in ins.iter(qn("w:t"))
    )


def test_inserted_paragraph_with_internal_crossref_link_keeps_the_link(tmp_path):
    orig = _make_doc(tmp_path, "a.docx", ["First."])
    revised = Document()
    revised.add_paragraph("First.")
    p = revised.add_paragraph()
    p.add_run("As shown in ")
    anchor = OxmlElement("w:hyperlink")
    anchor.set(qn("w:anchor"), "fig-main")
    anchor.append(_text_run("Figure 1"))
    p._p.append(anchor)
    p.add_run(".")
    revised.save(str(tmp_path / "b.docx"))

    report = diff_documents(orig, tmp_path / "b.docx", tmp_path / "out.docx")

    assert report["inserted_paragraphs"] == 1
    out = Document(str(tmp_path / "out.docx")).paragraphs[1]
    links = out._p.findall(qn("w:hyperlink"))
    assert len(links) == 1
    assert links[0].get(qn("w:anchor")) == "fig-main"
    assert "".join(t.text or "" for t in links[0].iter(qn("w:t"))) == "Figure 1"
    ins_text = "".join(t.text or "" for ins in out._p.iter(qn("w:ins")) for t in ins.iter(qn("w:t")))
    assert ins_text == "As shown in Figure 1."


def test_word_edit_preserves_per_run_formatting_of_untouched_words(tmp_path):
    def make(name, verb):
        d = Document()
        p = d.add_paragraph()
        p.add_run("The strain ")
        italic = p.add_run("Geobacter sulfurreducens")
        italic.italic = True
        p.add_run(f" {verb} acetate.")
        path = tmp_path / name
        d.save(str(path))
        return path

    diff_documents(make("a.docx", "oxidized"), make("b.docx", "consumed"), tmp_path / "out.docx")
    out = Document(str(tmp_path / "out.docx")).paragraphs[0]
    formatting = {}
    for r in out._p.iter(qn("w:r")):
        rpr = r.find(qn("w:rPr"))
        italic = rpr is not None and rpr.find(qn("w:i")) is not None
        for node in r:
            if node.tag in (qn("w:t"), qn("w:delText")) and (node.text or "").strip():
                formatting[node.text] = italic
    assert formatting["Geobacter"] is True and formatting["sulfurreducens"] is True
    assert formatting["strain"] is False
    assert formatting["oxidized"] is False and formatting["consumed"] is False


def test_nested_table_cell_change_is_reported(tmp_path):
    """Quarto wraps every crossref table in a 1x1 outer table, so data cells
    live in NESTED tables — those must count toward tables_differ."""
    def make(name, val):
        d = Document()
        d.add_paragraph("Intro.")
        wrapper = d.add_table(rows=1, cols=1)
        wrapper.cell(0, 0).paragraphs[0].text = "Table 1: caption"
        inner = wrapper.cell(0, 0).add_table(rows=1, cols=2)
        inner.cell(0, 0).text = val
        path = tmp_path / name
        d.save(str(path))
        return path

    report = diff_documents(make("a.docx", "old"), make("b.docx", "new"), tmp_path / "out.docx")
    assert report["tables_differ"] is True


def test_revision_ids_do_not_collide_with_existing_tracked_changes(tmp_path):
    orig = _make_doc(tmp_path, "a.docx", ["Same.", "Old line."])
    rev = Document()
    p = rev.add_paragraph()
    ins = OxmlElement("w:ins")
    for key, value in (("w:id", "9000"), ("w:author", "X"), ("w:date", "2026-01-01T00:00:00Z")):
        ins.set(qn(key), value)
    ins.append(_text_run("Same."))
    p._p.append(ins)
    rev.add_paragraph("New line.")
    rev.save(str(tmp_path / "b.docx"))

    diff_documents(orig, tmp_path / "b.docx", tmp_path / "out.docx")
    out = Document(str(tmp_path / "out.docx"))
    ids = [el.get(qn("w:id")) for el in out.element.body.iter() if el.tag in (qn("w:ins"), qn("w:del"))]
    assert len(ids) == len(set(ids)), ids


@pytest.mark.parametrize("output_name", ["a.docx", "b.docx"])
def test_output_cannot_overwrite_either_input(tmp_path, output_name):
    orig = _make_doc(tmp_path, "a.docx", ["Original."])
    revised = _make_doc(tmp_path, "b.docx", ["Revised."])

    with pytest.raises(InputError, match="output DOCX must differ"):
        diff_documents(orig, revised, tmp_path / output_name)
