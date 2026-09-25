"""`wongo worksheet status|lint|set` and `wongo review` through argparse, wired
the way cli.py wires them: add_parsers(sub, common) with a --json parent."""
from __future__ import annotations

import argparse
import json
import unicodedata

import pytest

from wongo import clitools
from wongo.engine.worksheet import Worksheet
from wongo.errors import InputError
from wongo.worksheet_cli import (
    add_parsers,
    cmd_lint,
    cmd_review,
    cmd_set,
    cmd_status,
    default_project,
    resolve_worksheet,
)

HEADER = "# Merge worksheet — coauthor.docx — 2026-09-25\n\nReview each item.\n\n"
QMD = (
    "---\n"
    'title: "A synthetic manuscript"\n'
    "---\n"
    "\n"
    "The two reactors was operated for 30 days.\n"  # 5
    "Removal efficiency reached `r round(eff, 1)`% in reactor A.\n"  # 6
)
UNMATCHED = "index.qmd:UNMATCHED — find manually"


def row(n, kind, author, location, disposition):
    return (
        f"## {n}. {kind} — {author}\n- location: {location}\n- old: a\n- new: b\n"
        f"- context: …c…\n- disposition: {disposition}\n\n"
    )


SHEET = (
    HEADER
    + row(1, "replacement", "Jane Doe", "index.qmd:5", "apply")
    + row(2, "deletion", "김민수", "index.qmd:6", "PROPOSED fix-code — inline R value")
    + row(3, "comment", "John Roe", UNMATCHED, "PENDING")
    + row(4, "insertion", "Jane Doe", "index.qmd:5", "reject: 중복 표현")
)
DECIDED = (
    HEADER
    + row(1, "replacement", "Jane Doe", "index.qmd:5", "apply")
    + row(2, "deletion", "김민수", "index.qmd:6", "apply — prose next to the inline value")
    + row(3, "comment", "John Roe", UNMATCHED, "needs-PI")
)


def make_parser():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", help="print one JSON object")
    parser = argparse.ArgumentParser(prog="wongo")
    sub = parser.add_subparsers(dest="command", required=True)
    add_parsers(sub, common)
    return parser


def run(*argv):
    args = make_parser().parse_args([str(a) for a in argv])
    return args.fn(args)


@pytest.fixture
def project(tmp_path):
    (tmp_path / "index.qmd").write_text(QMD, encoding="utf-8")
    (tmp_path / "decisions").mkdir()
    return tmp_path


def columns(line: str, cell: str) -> int:
    """Terminal column where ``cell`` starts (wide East Asian characters count 2)."""
    prefix = line[: line.index(cell)]
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in prefix)


def write_sheet(project, text):
    path = project / "decisions" / "merge-20260925-coauthor.md"
    path.write_text(text, encoding="utf-8", newline="")
    return path


# ---------------------------------------------------------------------------
# Wiring


def test_every_command_sets_its_handler():
    parser = make_parser()
    cases = {
        ("worksheet", "status", "f.md"): cmd_status,
        ("worksheet", "lint", "f.md"): cmd_lint,
        ("worksheet", "set", "f.md", "3", "apply"): cmd_set,
        ("review", "f.md"): cmd_review,
    }
    for argv, handler in cases.items():
        args = parser.parse_args(list(argv))
        assert args.fn is handler
        assert args.json is False
    assert parser.parse_args(["worksheet", "lint", "f.md", "--json"]).json is True


def test_help_explains_the_workflow(capsys):
    with pytest.raises(SystemExit) as exc:
        make_parser().parse_args(["worksheet", "--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "wongo never" in out and "edits the .qmd" in out
    assert "reject: <reason>" in out and "PROPOSED <one of those>" in out
    with pytest.raises(SystemExit):
        make_parser().parse_args(["worksheet", "set", "--help"])
    assert "--location N" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# status


def test_status_text(project, capsys):
    path = write_sheet(project, SHEET)
    assert run("worksheet", "status", path) == 0
    out = capsys.readouterr().out
    assert f"{path}: 4 rows, 2 need a decision" in out
    assert "  decided     2  (apply 1, reject 1)" in out
    assert "  proposed    1  (fix-code 1)" in out
    assert "  pending     1" in out
    lines = out.splitlines()
    table = [line for line in lines if line.startswith("    ") or line.startswith("  row")]
    assert table[0].split() == ["row", "kind", "author", "location", "disposition"]
    assert table[2].split() == ["2", "deletion", "김민수", "index.qmd:6", "PROPOSED", "fix-code"]
    assert table[3].split()[-2:] == ["index.qmd:UNMATCHED", "PENDING"]
    # Hangul takes two terminal columns: the location column still lines up.
    assert columns(table[1], "index.qmd:5") == columns(table[2], "index.qmd:6")
    assert lines[-1] == f"next: wongo review {path}"


def test_status_json(project, capsys):
    path = write_sheet(project, SHEET)
    assert run("worksheet", "status", path, "--json") == 0
    body = json.loads(capsys.readouterr().out)
    assert (body["command"], body["ok"]) == ("worksheet status", True)
    assert body["counts"]["total"] == 4 and body["counts"]["needs_decision"] == 2
    assert body["counts"]["decisions"] == {"apply": 1, "reject": 1, "fix-code": 0, "needs-PI": 0}
    assert body["rows"][1]["author"] == "김민수"
    assert body["rows"][1]["state"] == "proposed" and body["rows"][1]["proposal"] == "fix-code"
    assert body["rows"][2]["unmatched"] is True and body["rows"][2]["line"] is None
    assert body["next"] == f"wongo review {path}"


def test_status_points_to_lint_when_everything_is_decided(project, capsys):
    path = write_sheet(project, DECIDED)
    run("worksheet", "status", path)
    assert capsys.readouterr().out.splitlines()[-1] == f"next: wongo worksheet lint {path}"


# ---------------------------------------------------------------------------
# lint


def test_lint_fails_while_rows_need_decisions(project, capsys):
    path = write_sheet(project, SHEET)
    assert run("worksheet", "lint", path) == 1
    out = capsys.readouterr().out.splitlines()
    assert out[0].startswith("row 2: error: PROPOSED fix-code is not confirmed")
    assert out[1].startswith("row 3: error: still PENDING")
    assert out[-2] == "lint: 2 errors, 0 warnings — not ready to apply"
    assert out[-1] == f"next: wongo review {path}"


def test_lint_json(project, capsys):
    path = write_sheet(project, SHEET)
    assert run("worksheet", "lint", path, "--json") == 1
    body = json.loads(capsys.readouterr().out)
    assert (body["command"], body["ok"], body["errors"], body["warnings"]) == (
        "worksheet lint", False, 2, 0
    )
    assert [p["row"] for p in body["problems"]] == [2, 3]
    assert body["problems"][0]["severity"] == "error"
    assert body["project"] == str(project.resolve())


def test_lint_warnings_alone_pass_and_the_project_defaults_to_above_decisions(
    project, tmp_path_factory, monkeypatch, capsys
):
    path = write_sheet(project, DECIDED)
    monkeypatch.chdir(tmp_path_factory.mktemp("elsewhere"))
    assert run("worksheet", "lint", path) == 0
    out = capsys.readouterr().out.splitlines()
    assert out[0].startswith("row 2: warning: apply on index.qmd:6, a line with inline code")
    assert out[1] == "lint: OK (0 errors, 1 warning) — 3 of 3 rows decided  (apply 2, needs-PI 1)"
    assert "wongo never edits the .qmd" in out[2]


def test_lint_blocks_apply_on_unmatched(project, capsys):
    path = write_sheet(project, HEADER + row(1, "comment", "A", UNMATCHED, "apply"))
    assert run("worksheet", "lint", path, "--json") == 1
    body = json.loads(capsys.readouterr().out)
    assert "location is UNMATCHED" in body["problems"][0]["message"]


def test_lint_explicit_project(project, tmp_path, capsys):
    path = write_sheet(project, DECIDED)
    empty = tmp_path / "empty"
    empty.mkdir()
    assert run("worksheet", "lint", path, "--project", empty) == 0
    assert "index.qmd not found" in capsys.readouterr().out
    with pytest.raises(InputError, match="project folder not found"):
        run("worksheet", "lint", path, "--project", tmp_path / "missing")


# ---------------------------------------------------------------------------
# set


def test_set_disposition(project, capsys):
    path = write_sheet(project, SHEET)
    assert run("worksheet", "set", path, 3, "reject: off topic") == 0
    out = capsys.readouterr().out.splitlines()
    assert out == ["row 3: disposition PENDING -> reject: off topic", f"saved {path}"]
    assert path.read_text(encoding="utf-8") == SHEET.replace(
        f"- location: {UNMATCHED}\n- old: a\n- new: b\n- context: …c…\n- disposition: PENDING",
        f"- location: {UNMATCHED}\n- old: a\n- new: b\n- context: …c…\n- disposition: reject: off topic",
    )


def test_set_joins_an_unquoted_disposition(project):
    path = write_sheet(project, SHEET)
    run("worksheet", "set", path, 3, "PROPOSED", "reject:", "duplicate", "sentence")
    assert Worksheet.load(path).row(3).disposition.text == "PROPOSED reject: duplicate sentence"


def test_set_location_and_disposition_together(project, capsys):
    path = write_sheet(project, SHEET)
    assert run("worksheet", "set", path, 3, "apply", "--location", 5) == 0
    out = capsys.readouterr().out.splitlines()
    assert out[0] == f"row 3: location {UNMATCHED} -> index.qmd:5"
    assert out[1] == "row 3: disposition PENDING -> apply"
    r = Worksheet.load(path).row(3)
    assert (r.location, r.disposition.decision) == ("index.qmd:5", "apply")


def test_set_json(project, capsys):
    path = write_sheet(project, SHEET)
    assert run("worksheet", "set", path, 2, "--location", 6, "--json") == 0
    body = json.loads(capsys.readouterr().out)
    assert (body["command"], body["ok"], body["row"], body["changed"]) == ("worksheet set", True, 2, False)
    assert body["changes"] == {"location": {"old": "index.qmd:6", "new": "index.qmd:6"}}
    assert body["disposition"]["proposal"] == "fix-code"
    assert path.read_text(encoding="utf-8") == SHEET


def test_set_unchanged_does_not_rewrite(project, capsys):
    path = write_sheet(project, SHEET)
    before = path.stat().st_mtime_ns
    run("worksheet", "set", path, 1, "apply")
    assert capsys.readouterr().out.splitlines() == [
        "row 1: disposition unchanged (apply)", "nothing changed; file not written"
    ]
    assert path.stat().st_mtime_ns == before


@pytest.mark.parametrize(
    ("argv", "match"),
    [
        ((3,), "nothing to set"),
        ((3, "approve"), "invalid disposition 'approve'"),
        ((3, "reject:", "--location", 5), "reject needs a reason"),
        ((3, ""), "the disposition is empty"),
        ((9, "apply"), r"row 9 is not in .* \(its rows: 1-4\)"),
        ((3, "--location", 0), "whole number"),
    ],
)
def test_set_validation_errors(project, argv, match):
    path = write_sheet(project, SHEET)
    with pytest.raises(InputError, match=match):
        run("worksheet", "set", path, *argv)
    assert path.read_text(encoding="utf-8") == SHEET


def test_set_never_writes_a_qmd(project):
    with pytest.raises(InputError, match="not a merge worksheet"):
        run("worksheet", "set", project / "index.qmd", 1, "apply")
    assert (project / "index.qmd").read_text(encoding="utf-8") == QMD


# ---------------------------------------------------------------------------
# review


def test_review_refuses_without_a_terminal(project, monkeypatch):
    path = write_sheet(project, SHEET)
    monkeypatch.setattr(clitools, "is_interactive", lambda: False)
    with pytest.raises(InputError, match="needs a person at a terminal.*wongo worksheet set"):
        run("review", path)
    assert path.read_text(encoding="utf-8") == SHEET


def test_review_refuses_json(project, monkeypatch):
    path = write_sheet(project, SHEET)
    monkeypatch.setattr(clitools, "is_interactive", lambda: True)
    with pytest.raises(InputError, match="no JSON output"):
        run("review", path, "--json")


def test_review_runs_at_a_terminal(project, monkeypatch, capsys):
    path = write_sheet(project, SHEET)
    monkeypatch.setattr(clitools, "is_interactive", lambda: True)
    answers = iter(["", "4"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    monkeypatch.chdir(project)
    assert run("review", "merge-20260925-coauthor.md") == 0  # found in ./decisions/
    out = capsys.readouterr().out
    assert "in .qmd:  Removal efficiency reached" in out  # project = folder above decisions/
    ws = Worksheet.load(path)
    assert ws.row(2).disposition.text == "fix-code — inline R value"
    assert ws.row(3).disposition.text == "needs-PI"
    assert "next: wongo worksheet lint decisions/merge-20260925-coauthor.md" in out


def test_resolve_worksheet_and_default_project(project, tmp_path_factory, monkeypatch):
    path = write_sheet(project, SHEET)
    monkeypatch.chdir(project)
    assert resolve_worksheet("merge-20260925-coauthor.md").resolve() == path.resolve()
    assert str(resolve_worksheet("missing.md")) == "missing.md"
    assert default_project(path) == project.resolve()
    loose = tmp_path_factory.mktemp("loose") / "merge.md"
    loose.write_text(SHEET, encoding="utf-8")
    assert default_project(loose) == project.resolve()  # the current folder
