"""`wongo status`: one read-only card — where the manuscript stands and the
single next command to run. Fast: no rendering, no network, no R."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from wongo import __version__, toolchain
from wongo.engine.worksheet import shell_arg
from wongo.errors import WongoError

UP_TO_DATE = "renders current; author authorization not recorded"


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
    source_identity: dict = field(default_factory=dict)
    evidence_target: str = "submission"
    technical: dict = field(default_factory=dict)
    audit: dict = field(default_factory=dict)
    visual: dict = field(default_factory=dict)
    author_decisions: dict = field(default_factory=dict)
    submission_approved: bool = False
    demonstration: bool = False
    worksheet_context: str | None = None


def project_status(project: Path) -> Status:
    from wongo.engine import install_identity, output_freshness, read_manifest, style_name
    from wongo.engine.checks import run_checks
    from wongo.profiles import load_journal_config, load_profile, manuscript_type

    project = Path(project).resolve()
    status = Status(project=project, is_project=(project / "_journal.yml").exists(),
                    source_identity=install_identity())
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
        status.style = style_name(cfg)
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
    manifest = read_manifest(project)
    for target in ("collab", "submission"):
        status.outputs[target] = output_freshness(project, target)
        failed = ((manifest.get("targets") or {}).get(target) or {}).get("checks_failed") or []
        if failed:
            status.outputs[target]["checks_failed"] = list(failed)
    from wongo.gates import readiness

    try:
        dimensions = readiness(project, "submission", checks=checks, outputs=status.outputs["submission"])
    except WongoError as exc:
        status.config_error = str(exc)
        status.next_command = "wongo doctor"
        status.next_reason = "the evidence or author-gate configuration has a problem"
        return status
    for name in ("technical", "audit", "visual", "author_decisions", "submission_approved", "demonstration"):
        setattr(status, name, dimensions[name])
    coauthors = status.author_decisions["coauthor_rows"]
    status.worksheet = coauthors["worksheet"]
    status.worksheet_open = coauthors["open"]
    status.worksheet_context = coauthors["context"] if status.worksheet else None

    collab = status.outputs["collab"]["state"]
    saved_over = [f"output/{name}" for target in ("collab", "submission")
                  if status.outputs[target]["state"] == "modified"
                  for name in status.outputs[target]["changed"]]
    if status.quarto is None:
        status.next_command, status.next_reason = "wongo doctor", "Quarto was not found"
    elif saved_over:
        # a render would replace the file, and it may hold a coauthor's edits:
        # no command to run blindly, only the choice to make first
        status.next_command = ""
        status.next_reason = (
            f"{', '.join(saved_over)} changed after rendering (saved over in Word?). If it "
            "holds coauthor edits, move it into from-coauthors/ and run wongo roundtrip on "
            "it; if not, render again"
        )
    elif coauthors["state"] == "invalid":
        status.next_command = ""
        status.next_reason = coauthors["detail"]
    elif status.worksheet and status.worksheet_open:
        status.next_command = f"wongo review {shell_arg(status.worksheet)}"
        status.next_reason = (
            f"{status.worksheet_open} demonstration fixture row(s) remain unresolved"
            if status.demonstration else
            f"{status.worksheet_open} coauthor edit(s) still need a decision"
        )
    elif status.hard_failures:
        status.next_command = "wongo check"
        status.next_reason = f"HARD check(s) failing: {', '.join(status.hard_failures)}"
    elif collab in ("missing", "stale", "unknown"):
        status.next_command = "wongo render --target collab"
        stale_reason = status.outputs["collab"].get("detail") or (
            "sources changed since the last coauthor render"
        )
        status.next_reason = {"missing": "no coauthor render yet",
                              "stale": stale_reason,
                              "unknown": "the last render predates wongo's output manifest"}[collab]
    elif status.outputs["collab"].get("checks_failed"):
        failed = ", ".join(status.outputs["collab"]["checks_failed"])
        status.next_command = ""
        status.next_reason = f"the coauthor render recorded failed checks: {failed}"
    elif status.outputs["submission"]["state"] != "fresh":
        status.next_command = "wongo render --target submission"
        status.next_reason = "technical checks pass and the coauthor render is current; author authorization is separate"
    elif not status.audit.get("required_passed", True):
        status.next_command = "wongo audit --target submission"
        status.next_reason = f"required audit evidence is {status.audit['state']}"
    elif not status.visual.get("required_passed", True):
        inventory_state = status.visual.get("inspection", {}).get("state")
        if inventory_state in {"failed", "stale", "invalid"}:
            status.next_command = "wongo qa inspect --target submission"
            status.next_reason = f"recorded OOXML inventory is {inventory_state}; resolve its issues and inspect again"
        elif status.visual.get("representation") == "native-word-inspection":
            status.next_command = "wongo qa native-review --help"
            status.next_reason = "a person must inspect the remaining native Word pages and record the inspection"
        elif status.visual.get("preview", {}).get("state") == "fresh":
            status.next_command = "wongo qa review --help"
            status.next_reason = "a person must inspect the current preview pages and record the inspection"
        else:
            status.next_command = "wongo qa preview --target submission"
            status.next_reason = f"required visual evidence is {status.visual['state']}"
    elif status.author_decisions.get("state") not in {"approved", "not-configured", "not-required"}:
        status.next_command = "wongo gates status"
        status.next_reason = f"renders current; author decisions are {status.author_decisions['state']}"
    else:
        status.next_command = ""
        status.next_reason = (
            "renders current; configured author gates approved (locally attributed)"
            if status.submission_approved else UP_TO_DATE
        )
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
    ident = status.source_identity or {}
    commit = str(ident.get("commit") or "")[:12]
    source = ident.get("state") or "unknown"
    lines.append(
        f"engine:     wongo {__version__} · source {source}"
        + (f" {commit}" if commit else "")
    )
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
        if info.get("checks_failed"):
            detail += f"; render checks failed: {', '.join(info['checks_failed'])}"
        lines.append(f"{target + ':':<12}{detail}")
    for label, evidence in (("technical", status.technical), ("audit", status.audit),
                            ("visual", status.visual), ("author", status.author_decisions)):
        lines.append(f"{label + ':':<12}{evidence.get('state', 'not-recorded')} ({status.evidence_target})")
    if status.demonstration:
        lines.append("context:    synthetic demonstration; fixture rows are demonstration decisions")
    if status.worksheet:
        context = "demonstration, " if status.worksheet_context == "demonstration" else ""
        lines.append(f"worksheet:  {status.worksheet} ({context}{status.worksheet_open} open)")
    if status.next_command:
        lines.append(f"next:       {status.next_command}  — {status.next_reason}")
    else:
        lines.append(f"next:       {status.next_reason}")
    return lines
