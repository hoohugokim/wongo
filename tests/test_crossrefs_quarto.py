"""Real generated-table numbering; run with WONGO_REAL_QUARTO_TEST=1."""
from __future__ import annotations

import os
import re
import zipfile

import pytest
from lxml import etree

from wongo.engine import render_project

pytestmark = pytest.mark.skipif(
    os.environ.get("WONGO_REAL_QUARTO_TEST") != "1", reason="run in the real-Quarto job",
)


def _table(label):
    return (
        f"```{{r}}\n#| label: tbl-{label}\n#| tbl-cap: {label} observations.\n"
        "knitr::kable(data.frame(value=c(1,2)))\n```\n\n"
    )


def _text(path):
    with zipfile.ZipFile(path) as package:
        xml = etree.fromstring(package.read("word/document.xml"))
    text = re.sub(r"\s+", " ", " ".join(xml.itertext()))
    return re.sub(r"\s+([.,;:])", r"\1", text)


def test_generated_main_and_si_tables_resolve_in_their_own_rendered_order(tmp_path):
    project = tmp_path / "manuscript"
    profile = project / "profiles" / "demo"
    profile.mkdir(parents=True)
    (profile / "profile.yml").write_text(
        "slug: demo\njournal: Synthetic\n"
        "manuscript_types: [{type: article, word_limit: 500, counting_rule: test}]\n"
        "si: {separate_file: true, page_prefix: S, needs_cover_sheet: false}\n"
        "sources: [https://example.org]\nverified_date: 2026-10-22\n",
        encoding="utf-8",
    )
    (project / "_journal.yml").write_text(
        "journal: demo\nms_type: article\nstyle: default\n", encoding="utf-8")
    (project / "_quarto.yml").write_text(
        "project: {type: default, output-dir: output}\nformat: docx\n"
        "execute: {echo: false}\n", encoding="utf-8")
    (project / "index.qmd").write_text(
        "---\ntitle: Main\n---\n\nSee @tbl-main.\n\n" + _table("main"),
        encoding="utf-8",
    )
    for order, callout in ((["first", "second"], "See Table 2 and Table 1."),
                           (["second", "first"], "See Table 1 and Table 2.")):
        (project / "si.qmd").write_text(
            "---\ntitle: Supplement\n---\n\nSee @tbl-second and @tbl-first.\n\n"
            + "".join(_table(label) for label in order), encoding="utf-8")
        result = render_project(project, "submission")
        assert not result.hard_failures
        assert "See Table 1." in _text(project / "output" / "main-submission.docx")
        assert callout in _text(project / "output" / "si-submission.docx")
