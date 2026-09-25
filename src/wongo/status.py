"""`wongo status`: one read-only card — where the manuscript stands and the
single next command to run. Fast: no rendering, no network, no R."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from wongo import toolchain
from wongo.engine.worksheet import Worksheet
from wongo.errors import WongoError

WORKSHEET_GLOB = "merge-*.md"


@dataclass
class Status:
    project: Path
    is_project: bool
    journal: str | None = None
    journal_name: str | None = None
    ms_type: str | None = None
    style: str | None = None
    config_error: str | None = None
    quarto: str | None = None
    hard_failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    outputs: dict[str, dict] = field(default_factory=dict)
    worksheet: str | None = None
    worksheet_open: int = 0
    next_command: str = ""
    next_reason: str = ""


def _latest_worksheet(project: Path) -> Path | None:
    decisions = project / "decisions"
    if not decisions.is_dir():
        return None
    sheets = sorted(decisions.glob(WORKSHEET_GLOB), key=lambda p: (p.stat().st_mtime, p.name))
    return sheets[-1] if sheets else None


def _open_rows(worksheet: Path) -> int | None:
    """Rows still needing a decision (what `wongo review` would show), or
    None when the worksheet cannot be read."""
    try:
        return Worksheet.load(worksheet).counts().needs_decision
    except WongoError:
        return None


def project_status(project: Path) -> Status:
    from wongo.engine import output_freshness
    from wongo.engine.checks import run_checks
    from wongo.profiles import load_journal_config, load_profile, manuscript_type

    project = Path(project).resolve()
    status = Status(project=project, is_project=(project / "_journal.yml").exists())
    if not status.is_project:
        status.next_command = "wongo scaffold <folder>  (or: wongo scaffold demo --example)"
        status.next_reason = "this folder is not a wongo project"
        return status

    try:
        tool = toolchain.find_quarto()
        status.quarto = tool.path if tool else None
    except WongoError:
        status.quarto = None

    try:
        cfg = load_journal_config(project)
        status.journal, status.ms_type = cfg["journal"], cfg["ms_type"]
        status.style = cfg.get("style") or "default"
        profile = load_profile(cfg["journal"], project)
        status.journal_name = str(profile.get("journal", cfg["journal"]))
        manuscript_type(profile, cfg["ms_type"])
        checks = run_checks(project)
    except WongoError as exc:
        status.config_error = str(exc)
        status.next_command = "wongo doctor"
        status.next_reason = "the project configuration has a problem"
        return status

    status.hard_failures = [c.name for c in checks if c.level == "HARD" and not c.ok]
    status.warnings = [c.name for c in checks if c.level == "WARN" and not c.ok]
    for target in ("collab", "submission"):
        status.outputs[target] = output_freshness(project, target)
    sheet = _latest_worksheet(project)
    if sheet is not None:
        status.worksheet = str(sheet.relative_to(project))
        status.worksheet_open = _open_rows(sheet) or 0

    collab = status.outputs["collab"]["state"]
    if status.quarto is None:
        status.next_command, status.next_reason = "wongo doctor", "Quarto was not found"
    elif status.worksheet and status.worksheet_open:
        status.next_command = f"wongo review {status.worksheet}"
        status.next_reason = f"{status.worksheet_open} coauthor edit(s) still need a decision"
    elif status.hard_failures:
        status.next_command = "wongo check"
        status.next_reason = f"HARD check(s) failing: {', '.join(status.hard_failures)}"
    elif collab in ("missing", "stale", "unknown"):
        status.next_command = "wongo render --target collab"
        status.next_reason = {"missing": "no coauthor render yet",
                              "stale": "sources changed since the last coauthor render",
                              "unknown": "the last render predates wongo's output manifest"}[collab]
    elif status.outputs["submission"]["state"] != "fresh":
        status.next_command = "wongo render --target submission"
        status.next_reason = "checks pass and the coauthor render is current"
    else:
        status.next_command = ""
        status.next_reason = "everything is rendered and current"
    return status


def format_status(status: Status) -> list[str]:
    if not status.is_project:
        return [f"{status.project}: not a wongo project",
                f"next: {status.next_command}"]
    lines = [f"project:    {status.project}"]
    if status.config_error:
        lines += [f"config:     ERROR — {status.config_error}", f"next:       {status.next_command}"]
        return lines
    lines.append(f"journal:    {status.journal_name} ({status.journal}) · {status.ms_type} · "
                 f"style {status.style}")
    lines.append(f"quarto:     {status.quarto or 'NOT FOUND'}")
    if status.hard_failures:
        lines.append(f"checks:     HARD FAIL: {', '.join(status.hard_failures)}")
    elif status.warnings:
        lines.append(f"checks:     HARD ok; WARN: {', '.join(status.warnings)}")
    else:
        lines.append("checks:     all passing")
    for target, info in status.outputs.items():
        detail = info["state"]
        if info.get("changed") and info["state"] in ("stale", "modified", "missing"):
            detail += f" ({', '.join(info['changed'][:4])}"
            detail += ", …)" if len(info["changed"]) > 4 else ")"
        lines.append(f"{target + ':':<12}{detail}")
    if status.worksheet:
        lines.append(f"worksheet:  {status.worksheet} ({status.worksheet_open} open)")
    if status.next_command:
        lines.append(f"next:       {status.next_command}  — {status.next_reason}")
    else:
        lines.append(f"next:       nothing to do — {status.next_reason}")
    return lines
