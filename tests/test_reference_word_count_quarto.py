"""Run with WONGO_REAL_QUARTO_TEST=1; CI's Quarto jobs exercise each supported OS."""
from __future__ import annotations

import os

import pytest

from wongo.engine import render_project
from wongo.errors import GateError

pytestmark = pytest.mark.skipif(
    os.environ.get("WONGO_REAL_QUARTO_TEST") != "1", reason="run in the real-Quarto job",
)


def test_water_research_real_bibliography_changes_the_submission_boundary(tmp_path):
    project = tmp_path / "reference-count"
    project.mkdir()
    (project / "_journal.yml").write_text(
        "journal: wr\nms_type: research-paper\nstyle: default\n", encoding="utf-8")
    (project / "_quarto.yml").write_text(
        "project:\n  type: default\n  output-dir: output\nformat:\n  docx: default\n",
        encoding="utf-8")
    (project / "refs.bib").write_text("""@article{doe2020,
  author = {Doe, Jane and Roe, Richard},
  title = {Water Science},
  journal = {Demo Journal},
  year = {2020},
  doi = {10.1234/demo}
}
@article{unused, title = {An uncited reference must not enter the word count}, year = {2021}}
""", encoding="utf-8")
    # The shipped CSL renders ten words: Doe, J., Roe, R., 2020. Water
    # science. Demo Journal. https://doi.org/10.1234/demo
    source = ("---\nabstract: Short abstract.\nbibliography: refs.bib\n---\n\n"
              + "word " * 7985 + "Body cites [@doe2020].\n")
    (project / "index.qmd").write_text(source, encoding="utf-8")

    result = render_project(project, "submission")
    count = next(c for c in result.checks if c.name == "word-limit")
    assert count.ok and count.detail.startswith("8000 words ")
    assert "7990 source + 10 reference" in count.detail
    previous = {p.name: p.read_bytes() for p in (project / "output").iterdir() if p.is_file()}

    (project / "index.qmd").write_text(source + "Extra.\n", encoding="utf-8")
    with pytest.raises(GateError) as caught:
        render_project(project, "submission")
    count = next(c for c in caught.value.details["checks"] if c.name == "word-limit")
    assert not count.ok and count.detail.startswith("8001 words ")
    assert {p.name: p.read_bytes() for p in (project / "output").iterdir() if p.is_file()} == previous
