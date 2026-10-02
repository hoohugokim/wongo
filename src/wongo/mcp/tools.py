"""MCP Tools for Wongo: exposes 12 deterministic manuscript tools.

Every tool returns a structured dictionary with ok: bool and actionable fields.
Wongo never modifies source .qmd files directly; all outputs are in output/ or decisions/.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from mcp.server.mcpserver import MCPServer

from wongo.clitools import to_jsonable
from wongo.errors import WongoError
from wongo.mcp.resources import worksheet_uri


def _safe_call(fn, *args, **kwargs) -> dict[str, Any]:
    """Execute an engine function and return a structured JSON-able dictionary."""
    try:
        res = fn(*args, **kwargs)
        if isinstance(res, dict):
            data = to_jsonable(res)
            if "ok" not in data:
                data["ok"] = True
            return data
        return {"ok": True, "data": to_jsonable(res)}
    except WongoError as err:
        return {
            "ok": False,
            "error": {
                "kind": err.kind,
                "message": str(err),
            },
            **to_jsonable(err.details),
        }
    except Exception as err:
        return {
            "ok": False,
            "error": {
                "kind": "internal",
                "message": str(err),
            },
        }


def register_tools(server: MCPServer) -> None:
    """Register all 12 Wongo tools onto the MCP server."""

    @server.tool(name="wongo_status", description="Get manuscript project readiness, output freshness, and recommended next step.")
    def wongo_status(project: str = ".") -> dict[str, Any]:
        from wongo.status import project_status

        def _run():
            st = project_status(Path(project))
            return {
                "ok": st.config_error is None,
                "is_project": st.is_project,
                "journal": st.journal,
                "ms_type": st.ms_type,
                "style": st.style,
                "config_error": st.config_error,
                "next_command": st.next_command,
                "next_reason": st.next_reason,
                "hard_failures": st.hard_failures,
                "warnings": st.warnings,
                "worksheet": str(st.worksheet) if st.worksheet else None,
                "worksheet_open": st.worksheet_open,
                "outputs": to_jsonable(st.outputs),
            }

        return _safe_call(_run)

    @server.tool(name="wongo_doctor", description="Run environment & toolchain diagnostics (Quarto, R, knitr, rmarkdown, jsonlite).")
    def wongo_doctor(project: str = ".") -> dict[str, Any]:
        from wongo.doctor import run_doctor

        def _run():
            checks = run_doctor(Path(project))
            hard = [c for c in checks if c.level == "HARD" and not c.ok]
            warn = [c for c in checks if c.level == "WARN" and not c.ok]
            return {
                "ok": not bool(hard),
                "hard_failures": [c.name for c in hard],
                "warnings": [c.name for c in warn],
                "checks": [to_jsonable(c) for c in checks],
            }

        return _safe_call(_run)

    @server.tool(name="wongo_scaffold", description="Scaffold a new verified Quarto manuscript workspace with templates and config.")
    def wongo_scaffold(
        dest: str,
        journal: str = "est",
        ms_type: str | None = None,
        style: str | None = None,
        example: bool = False,
    ) -> dict[str, Any]:
        from wongo.scaffold import scaffold

        def _run():
            res = scaffold(Path(dest), journal=journal, ms_type=ms_type, style=style, example=example)
            return {
                "ok": True,
                "dest": str(res.dest),
                "journal": res.journal,
                "journal_name": res.journal_name,
                "ms_type": res.ms_type,
                "style": res.style,
                "example": res.example,
            }

        return _safe_call(_run)

    @server.tool(name="wongo_profile_get", description="Get verified journal requirements, word limits, counting rules, and guidelines.")
    def wongo_profile_get(slug: str) -> dict[str, Any]:
        from wongo.profiles import find_profile_dir, load_profile, profile_staleness_days

        def _run():
            prof = load_profile(slug)
            pdir = find_profile_dir(slug)
            days = profile_staleness_days(prof)
            return {
                "ok": True,
                "slug": slug,
                "journal": prof.get("journal"),
                "publisher": prof.get("publisher"),
                "verified_date": prof.get("verified_date"),
                "staleness_days": days,
                "submission_portal": prof.get("submission_portal"),
                "manuscript_types": prof.get("manuscript_types", []),
                "line_numbers": prof.get("line_numbers"),
                "spacing": prof.get("spacing"),
                "toc_graphic": prof.get("toc_graphic"),
                "si": prof.get("si"),
                "profile_dir": str(pdir),
            }

        return _safe_call(_run)

    @server.tool(name="wongo_check", description="Validate manuscript against journal profile with actionable patch hints.")
    def wongo_check(project: str = ".", strict: bool = False) -> dict[str, Any]:
        from wongo.engine.checks import run_checks

        def _run():
            checks = run_checks(Path(project).resolve())
            hard = [c for c in checks if c.level == "HARD" and not c.ok]
            warn = [c for c in checks if c.level == "WARN" and not c.ok]
            return {
                "ok": not (strict and hard),
                "has_hard_failures": bool(hard),
                "hard_failures": [c.name for c in hard],
                "warnings": [c.name for c in warn],
                "checks": [to_jsonable(c) for c in checks],
            }

        return _safe_call(_run)

    @server.tool(name="wongo_render", description="Render manuscript to collab or submission grade DOCX (main + SI).")
    def wongo_render(
        target: str = "submission",
        project: str = ".",
        style: str | None = None,
    ) -> dict[str, Any]:
        from wongo.engine import render_project

        def _run():
            # stdout belongs exclusively to the MCP JSON-RPC transport.
            res = render_project(Path(project), target, style_override=style, quarto_stdout=2)
            return {
                "ok": True,
                "target": res.target,
                "outputs": [str(p) for p in res.outputs],
                "quarto_version": res.quarto_version,
                "hard_failures": [c.name for c in res.hard_failures],
                "warnings": [c.name for c in res.warnings],
                "checks": [to_jsonable(c) for c in res.checks],
            }

        return _safe_call(_run)

    @server.tool(name="wongo_roundtrip", description="Extract coauthor Word tracked changes and comments into a merge worksheet.")
    def wongo_roundtrip(
        docx_path: str,
        project: str = ".",
        qmd: str = "index.qmd",
    ) -> dict[str, Any]:
        from wongo.engine.roundtrip import extract

        def _run():
            res = extract(Path(docx_path), Path(project), qmd=qmd)
            return {
                "ok": True,
                "worksheet": str(res.worksheet),
                "worksheet_uri": worksheet_uri(res.worksheet),
                "changes": res.changes,
                "kinds": res.kinds,
                "unmatched": res.unmatched,
                "unparsed": res.unparsed,
            }

        return _safe_call(_run)

    @server.tool(name="wongo_worksheet_status", description="Inspect merge worksheet counts, decision states, and rows.")
    def wongo_worksheet_status(file: str, project: str | None = None) -> dict[str, Any]:
        from wongo.engine.worksheet import Worksheet
        from wongo.worksheet_cli import _project, resolve_worksheet

        def _run():
            path = resolve_worksheet(file)
            root = _project(project, path)
            ws = Worksheet.load(path)
            counts = ws.counts()
            cache: dict = {}
            return {
                "ok": True,
                "file": str(path),
                "project": str(root),
                "worksheet_uri": worksheet_uri(path),
                "counts": to_jsonable(counts),
                "rows": [r.to_dict(project=root, cache=cache) for r in ws.rows],
            }

        return _safe_call(_run)

    @server.tool(name="wongo_worksheet_set", description="Set or propose a disposition on a single merge worksheet row.")
    def wongo_worksheet_set(
        file: str,
        row: int,
        disposition: str,
        force: bool = False,
        location: int | None = None,
        project: str | None = None,
    ) -> dict[str, Any]:
        from wongo.engine.worksheet import Worksheet, check_disposition
        from wongo.worksheet_cli import _holds_a_decision, _project, resolve_worksheet

        def _run():
            chosen = check_disposition(disposition)
            path = resolve_worksheet(file)
            root = _project(project, path)
            ws = Worksheet.load(path)
            target_row = ws.row(row)
            if not force and _holds_a_decision(target_row.disposition):
                current = " ".join(target_row.disposition.text.split())
                from wongo.errors import InputError

                raise InputError(
                    f"row {row} already has a decision ({current}); pass force=True to replace it"
                )
            if location is not None:
                ws.set_location(row, location)
            if chosen.state == "final":
                ws.decide(row, disposition)
            else:
                ws.set_disposition(row, disposition)
            ws.save()
            updated = ws.row(row)
            return {
                "ok": True,
                "file": str(path),
                "row": row,
                "disposition": updated.to_dict(project=root),
            }

        return _safe_call(_run)

    @server.tool(name="wongo_worksheet_batch_propose", description="Batch-propose dispositions for multiple merge worksheet rows with rationale.")
    def wongo_worksheet_batch_propose(
        file: str,
        proposals: list[dict[str, Any]],
        force: bool = False,
        project: str | None = None,
    ) -> dict[str, Any]:
        from wongo.engine.worksheet import Worksheet
        from wongo.worksheet_cli import _project, resolve_worksheet

        def _run():
            path = resolve_worksheet(file)
            root = _project(project, path)
            ws = Worksheet.load(path)
            updated_rows = ws.batch_propose(proposals, force=force)
            if updated_rows:
                ws.save()
            cache: dict = {}
            return {
                "ok": True,
                "file": str(path),
                "updated_count": len(updated_rows),
                "rows": [r.to_dict(project=root, cache=cache) for r in updated_rows],
            }

        return _safe_call(_run)

    @server.tool(name="wongo_worksheet_lint", description="Check merge worksheet for unapproved rows, malformed values, or syntax problems.")
    def wongo_worksheet_lint(file: str, project: str | None = None) -> dict[str, Any]:
        from wongo.engine.worksheet import Worksheet
        from wongo.worksheet_cli import _project, resolve_worksheet

        def _run():
            path = resolve_worksheet(file)
            root = _project(project, path)
            ws = Worksheet.load(path)
            problems = ws.lint(project=root)
            errors = [to_jsonable(p) for p in problems if p.severity == "error"]
            warnings = [to_jsonable(p) for p in problems if p.severity == "warning"]
            return {
                "ok": len(errors) == 0,
                "file": str(path),
                "project": str(root),
                "errors": errors,
                "warnings": warnings,
                "problems": [to_jsonable(p) for p in problems],
            }

        return _safe_call(_run)

    @server.tool(name="wongo_diff", description="Stamp tracked differences between original and revised DOCX into real Word track changes.")
    def wongo_diff(
        original: str,
        revised: str,
        out: str | None = None,
        author: str = "Revised manuscript",
        date: str | None = None,
    ) -> dict[str, Any]:
        from wongo.engine.diff import diff_documents

        def _run():
            orig_p = Path(original)
            rev_p = Path(revised)
            out_p = Path(out) if out else rev_p.with_name(rev_p.stem + "-tracked.docx")
            rep = diff_documents(orig_p, rev_p, out_p, author=author, date=date)
            return {
                "ok": True,
                "output": str(out_p),
                "inserted_words": rep.get("inserted_words", 0),
                "deleted_words": rep.get("deleted_words", 0),
                "inserted_paragraphs": rep.get("inserted_paragraphs", 0),
                "deleted_paragraphs": rep.get("deleted_paragraphs", 0),
                "tables_differ": rep.get("tables_differ", False),
                "rich_paragraphs_skipped": rep.get("rich_paragraphs_skipped", 0),
            }

        return _safe_call(_run)
