"""Regression tests for safe round-trip worksheet creation."""

from datetime import date

from wongo.engine.roundtrip import available_worksheet_path


def test_available_worksheet_path_never_overwrites_existing_review(tmp_path):
    decisions = tmp_path / "decisions"
    decisions.mkdir()
    first = decisions / "merge-20260830-coauthor.md"
    second = decisions / "merge-20260830-coauthor-2.md"
    first.write_text("approved dispositions", encoding="utf-8")
    second.write_text("another review", encoding="utf-8")

    result = available_worksheet_path(
        tmp_path, "coauthor", day=date(2026, 8, 30)
    )

    assert result == decisions / "merge-20260830-coauthor-3.md"
    assert first.read_text(encoding="utf-8") == "approved dispositions"
    assert second.read_text(encoding="utf-8") == "another review"


def test_worksheet_locations_name_the_source_qmd(tmp_path):
    from wongo.engine.roundtrip import Change, write_worksheet

    out = tmp_path / "ws.md"
    change = Change("insertion", "Reviewer", "", "added text", "context")
    write_worksheet([change], [7], out, "si-collab.docx", qmd_name="si.qmd")
    text = out.read_text(encoding="utf-8")
    assert "- location: si.qmd:7" in text
    assert "index.qmd" not in text
