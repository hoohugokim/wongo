"""CLI for the S4 merge worksheet: `wongo worksheet status|lint|set` and `wongo review`.

cli.py calls ``add_parsers(sub, common)`` with its subparsers object and a parent
parser that defines ``--json``. Each handler takes the argparse Namespace and
returns an exit code; user errors are raised as WongoError for the main CLI to
print (or to emit as the JSON error object). With ``--json`` a handler prints
exactly one JSON object through clitools.emit_json.

No command here writes a .qmd: rows are decided in the worksheet, and approved
rows are applied to the manuscript by the person or the agent, outside wongo.
"""
from __future__ import annotations

import argparse
import unicodedata
from pathlib import Path

from wongo import clitools
from wongo.engine.worksheet import DECISIONS, Row, Worksheet, check_disposition, shell_arg
from wongo.errors import InputError
from wongo.review import review

WORKSHEET_DESCRIPTION = """\
A merge worksheet (decisions/merge-<date>-<name>.md, written by `wongo roundtrip`)
holds one row per coauthor change. Decide every row, check the worksheet, then
apply the approved rows to the .qmd yourself or with the agent. wongo never
edits the .qmd.

  wongo review <file>                        decide rows at the terminal
  wongo worksheet set <file> <row> <value>   decide or propose one row (agent, scripts)
  wongo worksheet status <file>              progress and a table of the rows
  wongo worksheet lint <file>                exit 1 until every row is validly decided

dispositions: apply | fix-code | needs-PI  (each may add ' — note')
              reject: <reason>  |  PROPOSED <one of those>  |  PENDING"""

FILE_HELP = "the merge worksheet, e.g. decisions/merge-20260925-coauthor.md"
PROJECT_HELP = (
    "manuscript folder that holds the .qmd (default: the folder above decisions/ "
    "when the worksheet is in one, else the current folder)"
)


def add_parsers(sub, common: argparse.ArgumentParser) -> None:
    """Add `worksheet status|lint|set` and `review` to the main wongo parser."""
    ws = sub.add_parser(
        "worksheet",
        help="Check and edit a merge worksheet from `wongo roundtrip` (never edits the .qmd)",
        description=WORKSHEET_DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    wsub = ws.add_subparsers(dest="worksheet_command", required=True, metavar="{status,lint,set}")

    p = wsub.add_parser(
        "status", parents=[common],
        help="Count decided, proposed and pending rows and list them",
        description="Show how far the review of a merge worksheet has got.",
    )
    p.add_argument("file", help=FILE_HELP)
    p.set_defaults(fn=cmd_status)

    p = wsub.add_parser(
        "lint", parents=[common],
        help="Check that every row is validly decided; exit 1 on any error",
        description=(
            "Errors: PENDING or unconfirmed PROPOSED rows, invalid values, reject without "
            "a reason, apply on an UNMATCHED location or an unparsed row. Warnings: apply "
            "on a .qmd line with inline code, or on a line past the end of the file. "
            "Exit 1 on any error; warnings alone exit 0."
        ),
    )
    p.add_argument("file", help=FILE_HELP)
    p.add_argument("--project", metavar="DIR", default=None, help=PROJECT_HELP)
    p.set_defaults(fn=cmd_lint)

    p = wsub.add_parser(
        "set", parents=[common],
        help="Set one row's disposition and/or location (for the agent and scripts)",
        description=(
            "Write a row's disposition exactly as given (continuation lines stay) and/or "
            "point it at another .qmd line. People usually decide with `wongo review`."
        ),
    )
    p.add_argument("file", help=FILE_HELP)
    p.add_argument("row", type=int, help="row number (the N in '## N. kind — author')")
    p.add_argument(
        "disposition", nargs="*", metavar="DISPOSITION",
        help="e.g. apply, 'reject: duplicate sentence', 'PROPOSED fix-code — why'",
    )
    p.add_argument(
        "--location", type=int, metavar="N", default=None,
        help="point the row at line N of its .qmd (e.g. an UNMATCHED change found by hand)",
    )
    p.set_defaults(fn=cmd_set)

    p = sub.add_parser(
        "review", parents=[common],
        help="Decide merge-worksheet rows one at a time at the terminal",
        description=(
            "Shows each row that still needs a decision with its .qmd line and any "
            "proposal; answer with a digit and Enter. The worksheet is saved after every "
            "decision. Never edits the .qmd. Needs a terminal: from a script or the agent, "
            "use `wongo worksheet set`."
        ),
    )
    p.add_argument("file", help=FILE_HELP)
    p.add_argument("--project", metavar="DIR", default=None, help=PROJECT_HELP)
    p.set_defaults(fn=cmd_review)


# ---------------------------------------------------------------------------
# Handlers


def cmd_status(args: argparse.Namespace) -> int:
    path = resolve_worksheet(args.file)
    ws = Worksheet.load(path)
    counts = ws.counts()
    file = shell_arg(path)
    step = f"wongo review {file}" if counts.needs_decision else f"wongo worksheet lint {file}"
    if args.json:
        clitools.emit_json(
            "worksheet status", True, file=str(path), counts=counts,
            rows=[row.to_dict() for row in ws.rows], next=step,
        )
        return 0
    plural = "" if counts.total == 1 else "s"
    print(f"{path}: {counts.total} row{plural}, {counts.needs_decision} need a decision")
    print(f"  decided   {counts.final:>3}{_breakdown(counts.decisions)}")
    print(f"  proposed  {counts.proposed:>3}{_breakdown(counts.proposals)}")
    print(f"  pending   {counts.pending:>3}")
    print(f"  invalid   {counts.invalid:>3}")
    if ws.rows:
        print()
        for line in _table(ws.rows):
            print(line)
    print(f"next: {step}")
    return 0


def cmd_lint(args: argparse.Namespace) -> int:
    path = resolve_worksheet(args.file)
    ws = Worksheet.load(path)
    project = _project(args.project, path)
    problems = ws.lint(project=project)
    errors = sum(1 for p in problems if p.severity == "error")
    warnings = len(problems) - errors
    counts = ws.counts()
    if args.json:
        clitools.emit_json(
            "worksheet lint", errors == 0, file=str(path), project=str(project),
            errors=errors, warnings=warnings, problems=problems, counts=counts,
        )
        return 1 if errors else 0
    for problem in problems:
        print(problem)
    file = shell_arg(path)
    tally = f"{errors} error{'' if errors == 1 else 's'}, {warnings} warning{'' if warnings == 1 else 's'}"
    if errors:
        print(f"lint: {tally} — not ready to apply")
        if counts.needs_decision:
            print(f"next: wongo review {file}")
        else:
            print("next: fix the rows above, then run wongo worksheet lint again")
        return 1
    print(f"lint: OK ({tally}) — {counts.final} of {counts.total} rows decided"
          f"{_breakdown(counts.decisions)}")
    print("next: apply the `apply` rows to the .qmd (fix-code: change the code; needs-PI: "
          "ask the PI), by you or the agent. wongo never edits the .qmd.")
    return 0


def cmd_set(args: argparse.Namespace) -> int:
    value = " ".join(args.disposition).strip() if args.disposition else None
    if value is None and args.location is None:
        raise InputError(
            "nothing to set: give a disposition, --location N, or both, e.g. "
            "`wongo worksheet set <file> 3 \"reject: duplicate sentence\"` or "
            "`wongo worksheet set <file> 3 --location 42`"
        )
    if value is not None:
        check_disposition(value)  # a bad value changes nothing, not even the location
    path = resolve_worksheet(args.file)
    ws = Worksheet.load(path)
    changes: dict[str, dict[str, str | None]] = {}
    if args.location is not None:
        before = ws.row(args.row).location
        changes["location"] = {"old": before, "new": ws.set_location(args.row, args.location).location}
    if value is not None:
        current = ws.row(args.row).disposition
        before = current.text
        if check_disposition(value).state == "final" and current.state in ("proposed", "final"):
            # recording a decision: keep the agent's rationale ("was PROPOSED ...")
            after = ws.decide(args.row, value).disposition.text
        else:
            after = ws.set_disposition(args.row, value).disposition.text
        changes["disposition"] = {"old": before, "new": after}
    changed = any(c["old"] != c["new"] for c in changes.values())
    if changed:
        ws.save()
    row = ws.row(args.row)
    if args.json:
        clitools.emit_json(
            "worksheet set", True, file=str(path), row=args.row, changed=changed,
            changes=changes, disposition=row.to_dict(),
        )
        return 0
    for key, change in changes.items():
        old, new = (_first_line(change["old"]), _first_line(change["new"]))
        if old == new:
            print(f"row {args.row}: {key} unchanged ({new})")
        else:
            print(f"row {args.row}: {key} {old} -> {new}")
    print(f"saved {path}" if changed else "nothing changed; file not written")
    return 0


def cmd_review(args: argparse.Namespace) -> int:
    if getattr(args, "json", False):
        raise InputError(
            "wongo review is interactive and has no JSON output; read a worksheet with "
            "`wongo worksheet status <file> --json` and change it with `wongo worksheet set`"
        )
    if not clitools.is_interactive():
        raise InputError(
            "wongo review needs a person at a terminal (stdin and stdout must be a terminal, "
            "and WONGO_NO_PROMPT unset). From a script or the agent, use "
            "`wongo worksheet set <file> <row> <disposition>`, and "
            "`wongo worksheet status <file>` to see what is left."
        )
    path = resolve_worksheet(args.file)
    project = _project(args.project, path)
    # input/print are looked up now, not bound at import, so tests can patch them.
    review(path, project, input_fn=input, print_fn=print)
    return 0


# ---------------------------------------------------------------------------
# Helpers


def resolve_worksheet(file: str | Path) -> Path:
    """The worksheet to open. A bare file name that is not in the current folder
    is also looked for in ./decisions/, where `wongo roundtrip` writes it (the
    worksheet header names the file without its folder)."""
    path = Path(file)
    if not path.exists() and path.parent == Path("."):
        candidate = Path("decisions") / path
        if candidate.is_file():
            return candidate
    return path


def default_project(worksheet: Path | str) -> Path:
    """The folder above decisions/ when the worksheet sits in one, else the current folder."""
    parent = Path(worksheet).resolve().parent
    if parent.name.lower() == "decisions":
        return parent.parent
    return Path.cwd()


def _project(given: str | None, worksheet: Path) -> Path:
    if given is None:
        return default_project(worksheet)
    project = Path(given)
    if not project.is_dir():
        raise InputError(f"project folder not found: {project}; pass the folder that holds the .qmd")
    return project


def _breakdown(per_decision: dict[str, int]) -> str:
    parts = [f"{k} {per_decision[k]}" for k in DECISIONS if per_decision.get(k)]
    return f"  ({', '.join(parts)})" if parts else ""


def _first_line(text: str | None) -> str:
    if text is None:
        return "(none)"
    first = text.split("\n")[0]
    return first if first.strip() else "(empty)"


def _table(rows: list[Row]) -> list[str]:
    """Aligned row table; widths count terminal columns, so Hangul names line up."""
    cells = [("row", "kind", "author", "location", "disposition")]
    for row in rows:
        cells.append((
            str(row.number), row.kind, row.author or "?", _short_location(row),
            _disposition_cell(row),
        ))
    caps = (6, 12, 20, 28, 0)
    widths = [
        min(max(_width(c[i]) for c in cells), caps[i]) if caps[i] else 0 for i in range(5)
    ]
    lines = []
    for c in cells:
        parts = [_fit(c[0], widths[0], right=True)]
        parts += [_fit(c[i], widths[i]) for i in (1, 2, 3)]
        parts.append(c[4])
        lines.append(("  " + "  ".join(parts)).rstrip())
    return lines


def _short_location(row: Row) -> str:
    if row.location is None:
        return "-"
    if row.unmatched:
        return f"{row.qmd}:UNMATCHED"
    return row.location


def _disposition_cell(row: Row) -> str:
    label = row.disposition.label
    if row.disposition.state == "final" and row.needs_decision:
        return f"{label} (blocked)"
    return label


def _char_width(ch: str) -> int:
    if unicodedata.combining(ch):
        return 0
    return 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1


def _width(text: str) -> int:
    return sum(_char_width(ch) for ch in text)


def _fit(text: str, width: int, *, right: bool = False) -> str:
    """Pad (or cut, marking the cut with '...') to exactly ``width`` columns."""
    if _width(text) > width:
        room, kept = width - 3, []
        for ch in text:
            room -= _char_width(ch)
            if room < 0:
                break
            kept.append(ch)
        text = "".join(kept) + "..."
    pad = " " * max(width - _width(text), 0)
    return pad + text if right else text + pad
