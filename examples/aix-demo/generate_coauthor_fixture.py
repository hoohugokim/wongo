"""Rebuild the synthetic coauthor DOCX from a fresh Quarto/R render.

Run ``uv run python examples/aix-demo/generate_coauthor_fixture.py`` from the
repository root. Requires Quarto and the R packages reported by ``wongo doctor``.
Only the fixture is replaced; all renders and revisions use a temporary copy.
"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from docx import Document

from wongo.engine import render_project
from wongo.engine.diff import diff_documents
from wongo.engine.roundtrip import extract
from wongo.engine.worksheet import Worksheet


def generate_fixture(demo: Path, output: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="wongo-aix-fixture-") as temporary:
        scratch = Path(temporary) / "manuscript"
        scratch.mkdir()
        for name in ("index.qmd", "si.qmd", "_journal.yml", "_quarto.yml", "refs.bib"):
            shutil.copy2(demo / name, scratch / name)
        shutil.copytree(demo / "figures", scratch / "figures")
        rendered = render_project(scratch, target="collab")
        original = next(path for path in rendered.outputs if path.name == "main-collab.docx")
        revised = Path(temporary) / "revised.docx"
        doc = Document(original)
        edits = [
            ("Chronoamperometry was conducted", "conducted",
             "conducted under steady-state potentiostatic polarization"),
            ("Under continuous flow conditions, functionalized electrodes sustained", "12.4",
             "approximately 13.1"),
        ]
        for anchor, old, new in edits:
            matches = [paragraph for paragraph in doc.paragraphs if anchor in paragraph.text]
            if len(matches) != 1:
                raise ValueError(f"Expected one rendered fixture paragraph containing {anchor!r}")
            runs = [run for run in matches[0].runs if old in run.text]
            if len(runs) != 1 or runs[0].text.count(old) != 1:
                raise ValueError(f"Expected one rendered run containing {old!r}")
            runs[0].text = runs[0].text.replace(old, new, 1)
        doc.save(revised)
        tracked = Path(temporary) / "coauthor-edits.docx"
        diff_documents(original, revised, tracked, author="Synthetic reviewer",
                       date="2026-10-02T00:00:00Z")
        result = extract(tracked, scratch)
        ws = Worksheet.load(result.worksheet)
        if result.changes != 2 or result.unmatched or result.unparsed:
            raise ValueError("Generated fixture must extract exactly two aligned changes")
        calculated = [row for row in ws.rows if row.old == "12.4"]
        if len(calculated) != 1 or "inline-code" not in calculated[0].to_dict(project=scratch)["tags"]:
            raise ValueError("Calculated-value edit must carry the source-derived inline-code tag")
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(tracked, output)


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    generate_fixture(root, root / "from-coauthors" / "coauthor-edits.docx")
