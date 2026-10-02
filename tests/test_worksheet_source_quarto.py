"""Actual Quarto/R rendered values stay identifiable after Word extraction."""
from __future__ import annotations

import os
import runpy
import shutil
from pathlib import Path

import pytest

from wongo.engine.roundtrip import extract
from wongo.engine.worksheet import Worksheet

pytestmark = pytest.mark.skipif(
    os.environ.get("WONGO_REAL_QUARTO_TEST") != "1", reason="run in the real-Quarto job",
)


def test_real_rendered_inline_value_survives_roundtrip_as_source_tag(tmp_path):
    demo = Path(__file__).resolve().parents[1] / "examples" / "aix-demo"
    fixture = tmp_path / "coauthor.docx"
    generate = runpy.run_path(str(demo / "generate_coauthor_fixture.py"))["generate_fixture"]
    generate(demo, fixture)
    project = tmp_path / "manuscript"
    shutil.copytree(demo, project)
    source = project / "index.qmd"
    original = source.read_bytes()
    result = extract(fixture, project)
    ws = Worksheet.load(result.worksheet)
    assert result.changes == 2 and result.unmatched == result.unparsed == 0
    calculated = next(row for row in ws.rows if row.old == "12.4")
    assert calculated.new == "approximately 13.1"
    assert calculated.word_count_delta == 1
    assert "inline-code" in calculated.to_dict(project=project)["tags"]
    assert "`r " in calculated.to_dict(project=project)["source"]["text"]
    assert source.read_bytes() == original
