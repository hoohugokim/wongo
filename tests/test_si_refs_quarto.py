"""Real Quarto/knitr labels whose order exists only after R executes."""
from __future__ import annotations

import hashlib
import os
import zipfile

import pytest
from lxml import etree

from wongo.engine import output_freshness, read_manifest, render_project
from wongo.errors import InputError

pytestmark = pytest.mark.skipif(os.environ.get("WONGO_REAL_QUARTO_TEST") != "1",
                                reason="run in the real-Quarto job")


def _text(path):
    with zipfile.ZipFile(path) as package:
        xml = etree.fromstring(package.read("word/document.xml"))
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    return " ".join(xml.xpath("//w:t/text()", namespaces=ns)).replace("\xa0", " ")


@pytest.mark.parametrize("target", ["collab", "submission"])
def test_data_driven_table_order_is_reflected_in_main_and_missing_label_refuses(tmp_path, target):
    project = tmp_path / "paper"
    (project / "profiles/demo").mkdir(parents=True)
    (project / "profiles/demo/profile.yml").write_text(
        "slug: demo\njournal: Synthetic\n"
        "manuscript_types: [{type: article, word_limit: 500, counting_rule: source estimate}]\n"
        "si: {separate_file: true, needs_cover_sheet: false}\n"
        "sources: []\nverified_date: '2026-10-23'\n", encoding="utf-8")
    (project / "_journal.yml").write_text(
        "journal: demo\nms_type: article\nstyle: default\nsi_references: true\n"
        "dependencies: [order.txt]\n", encoding="utf-8")
    (project / "_quarto.yml").write_text(
        "project: {type: default, output-dir: output}\nformat: docx\n"
        "execute: {echo: false}\n", encoding="utf-8")
    (project / "index.qmd").write_text(
        "---\ntitle: Main\n---\n\n"
        "See [SI table](wongo-si:tbl-beta) and [other SI table](wongo-si:tbl-alpha) "
        "and [SI figure](wongo-si:fig-curve) in the Supporting Information.[^si]\n\n"
        "[^si]: Repeated in a note: [SI table](wongo-si:tbl-beta).\n", encoding="utf-8")
    (project / "si.qmd").write_text(
        "---\ntitle: Supporting Information\ncrossref:\n  tbl-title: Table S\n  fig-title: Figure S\n---\n\n"
        "```{r}\n#| results: asis\n"
        'labels <- readLines("order.txt")\n'
        'for (label in labels) {\n'
        '  cat(knitr::kable(data.frame(value=1), caption=paste0(label, " observations. {#tbl-", label, "}")), sep="\\n")\n'
        '  cat("\\n\\n")\n'
        '}\n```\n\n'
        '```{r}\n#| label: fig-curve\n#| fig-cap: A synthetic response.\nplot(1:3)\n```\n', encoding="utf-8")
    order = project / "order.txt"
    sources = {name: (project / name).read_bytes() for name in ("index.qmd", "si.qmd", "_quarto.yml")}
    for labels, expected in (("alpha\nbeta\n", ["Table S2", "Table S1"]),
                              ("beta\nalpha\n", ["Table S1", "Table S2"])):
        order.write_text(labels, encoding="utf-8")
        render_project(project, target)
        entry = read_manifest(project)["targets"][target]
        refs = entry["si_references"]["references"]
        assert [ref["display"] for ref in refs] == expected + ["Figure S1", expected[0]]
        assert refs[-1]["part"] == "word/footnotes.xml"
        assert all(value in _text(project / "output" / f"main-{target}.docx") for value in expected)
        assert output_freshness(project, target)["state"] == "fresh"
        assert entry["si_references"]["si_sha256"] == entry["outputs"][f"si-{target}.docx"]
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (project / "output").iterdir() if p.is_file()}
    order.write_text("gamma\nalpha\n", encoding="utf-8")
    assert output_freshness(project, target)["state"] == "stale"
    with pytest.raises(InputError, match="tbl-beta"):
        render_project(project, target)
    assert {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (project / "output").iterdir() if p.is_file()} == before
    assert {name: (project / name).read_bytes() for name in sources} == sources
