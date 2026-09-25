"""wongo command line — a thin shell over the engine.

Every command prints text by default, or exactly one JSON object with --json
(see wongo.clitools). User-fixable problems are WongoError: the message goes to
stderr (or into the JSON error object) with exit code 1, never a traceback.
Prompts appear only when a person is at a terminal, so CI, the byte-compare
harness and the Claude agent can never hang on one.
"""
from __future__ import annotations

import argparse
import sys
import textwrap
from pathlib import Path

from wongo import __version__, worksheet_cli
from wongo.clitools import emit_json, is_interactive
from wongo.engine.worksheet import shell_arg
from wongo.errors import WongoError
from wongo.textio import configure_stdio


def _json(args: argparse.Namespace) -> bool:
    return bool(getattr(args, "json", False))


# ---------------------------------------------------------------------------
# render / check


def render_summary(result) -> str:
    passed = sum(1 for c in result.checks if c.ok)
    parts = [f"{passed} passed"]
    if result.hard_failures:
        names = ", ".join(c.name for c in result.hard_failures)
        parts.append(f"HARD FAIL: {names} (this render is not submission-ready)")
    if result.warnings:
        parts.append(f"WARN: {', '.join(c.name for c in result.warnings)}")
    return "checks: " + ", ".join(parts)


def _cmd_render(args: argparse.Namespace) -> int:
    from wongo.engine import render_project
    from wongo.engine.checks import print_report

    json_mode = _json(args)

    def on_event(kind: str, payload: dict) -> None:
        if kind == "checks" and not json_mode:
            print_report(payload["checks"])
            sys.stdout.flush()  # the report must precede quarto's own output

    result = render_project(Path(args.project), args.target, style_override=args.style,
                            on_event=on_event, quarto_stdout=2 if json_mode else None)
    if json_mode:
        emit_json("render", True, target=result.target, outputs=result.outputs,
                  checks=result.checks, manifest=result.manifest,
                  quarto=result.quarto_version,
                  hard_failures=[c.name for c in result.hard_failures],
                  warnings=[c.name for c in result.warnings])
        return 0
    for path in result.outputs:
        print(f"wrote {path}")
    print(render_summary(result))
    return 0


def _cmd_check(args: argparse.Namespace) -> int:
    from wongo.engine.checks import print_report, run_checks

    checks = run_checks(Path(args.project).resolve())
    hard = [c for c in checks if c.level == "HARD" and not c.ok]
    if _json(args):
        emit_json("check", not hard, checks=checks)
    else:
        print_report(checks)
    return 1 if args.strict and hard else 0


# ---------------------------------------------------------------------------
# roundtrip / diff


def _cmd_roundtrip(args: argparse.Namespace) -> int:
    from wongo.engine.roundtrip import extract

    result = extract(Path(args.docx), Path(args.project), qmd=args.qmd)
    if _json(args):
        emit_json("roundtrip", True, worksheet=result.worksheet, changes=result.changes,
                  kinds=result.kinds, unmatched=result.unmatched, unparsed=result.unparsed)
        return 0
    print(f"wrote {result.worksheet} ({result.changes} changes; NONE applied — "
          "review dispositions first)")
    if result.changes:
        print(f"next: wongo review {shell_arg(result.worksheet)}")
    return 0


def _cmd_diff(args: argparse.Namespace) -> int:
    from wongo.engine.diff import diff_documents
    from wongo.errors import InputError

    original, revised = Path(args.original), Path(args.revised)
    for label, path in (("original", original), ("revised", revised)):
        if not path.exists():
            raise InputError(f"{label} DOCX not found: {path}")
    out = Path(args.out) if args.out else revised.with_name(revised.stem + "-tracked.docx")
    report = diff_documents(original, revised, out, author=args.author, date=args.date)
    if _json(args):
        emit_json("diff", True, output=out, **report)
        return 0
    print(f"wrote {out}")
    print(f"  words: +{report['inserted_words']} inserted, -{report['deleted_words']} deleted")
    print(f"  paragraphs: +{report['inserted_paragraphs']}, -{report['deleted_paragraphs']}")
    if report["tables_differ"]:
        print("  NOTE: tables differ between the two documents and are NOT "
              "tracked by this tool — run Word Compare for table pages.")
    if report["rich_paragraphs_skipped"]:
        print(f"  NOTE: {report['rich_paragraphs_skipped']} changed paragraph(s) contain "
              "fields, drawings, footnotes, or other rich OOXML and were not "
              "rewritten — run Word Compare for those paragraphs.")
    return 0


# ---------------------------------------------------------------------------
# scaffold


def choose(title: str, options: list[tuple[str | None, str]], default: int | None = None):
    """Numbered choice at a terminal; digits work with a Korean input method on."""
    print(title)
    for i, (_, label) in enumerate(options, start=1):
        print(f"  {i}. {label}")
    hint = f" [Enter = {default}]" if default else ""
    while True:
        try:
            answer = input(f"choose 1-{len(options)}{hint}: ").strip()
        except EOFError:
            return options[default - 1][0] if default else None
        if not answer and default:
            return options[default - 1][0]
        if answer.isdigit() and 1 <= int(answer) <= len(options):
            return options[int(answer) - 1][0]
        print(f"  please type a number from 1 to {len(options)}")


def _prompt_project_choices(journal, ms_type, style):
    from wongo.profiles import list_profiles, load_profile
    from wongo.styles import list_styles

    if journal is None:
        profiles = list_profiles()
        options = [(str(p["slug"]), f"{p['slug']:<14} {p.get('journal', '?')}") for p in profiles]
        options.append((None, "decide later (edit _journal.yml)"))
        journal = choose("Which journal is this manuscript for?", options)
    if journal and ms_type is None:
        types = load_profile(journal).get("manuscript_types") or []
        options = [(str(t["type"]), f"{t['type']:<18} word limit {t.get('word_limit', '—')}")
                   for t in types if t.get("type")]
        ms_type = choose("Which manuscript type?", options, default=1)
    if style is None:
        styles = list_styles()
        default = next((i for i, s in enumerate(styles, start=1) if s["name"] == "default"), 1)
        style = choose("Which house style?",
                       [(s["name"], f"{s['name']:<10} {s['description'][:60]}") for s in styles],
                       default=default)
    return journal, ms_type, style


def _cmd_scaffold(args: argparse.Namespace) -> int:
    from wongo.scaffold import scaffold

    journal, ms_type, style = args.journal, args.ms_type, args.style
    if not args.example and not _json(args) and journal is None and is_interactive():
        journal, ms_type, style = _prompt_project_choices(journal, ms_type, style)
    result = scaffold(Path(args.dest), journal=journal, ms_type=ms_type, style=style,
                      example=args.example)
    if _json(args):
        emit_json("scaffold", True, **{k: v for k, v in vars(result).items()})
        return 0
    print(f"scaffolded {result.dest}")
    if result.journal:
        print(f"  journal: {result.journal} ({result.journal_name}) · "
              f"ms_type: {result.ms_type or 'not set'} · style: {result.style}")
    print("next steps:")
    step = 1
    if Path.cwd().resolve() != result.dest:
        print(f"  {step}. cd {shell_arg(result.dest)}")
        step += 1
    if not result.journal or not result.ms_type:
        print(f"  {step}. fill in _journal.yml (journal slug + ms_type): "
              "wongo profile list / wongo profile show <slug>")
        step += 1
    if result.example:
        print(f"  {step}. open index.qmd to see how numbers, figures and citations are wired")
    else:
        print(f"  {step}. fill in index.qmd front matter; write ONE SENTENCE PER LINE")
    step += 1
    print(f"  {step}. wongo doctor, then wongo check && wongo render --target collab")
    return 0


# ---------------------------------------------------------------------------
# profile / style


def _cmd_profile_list(args: argparse.Namespace) -> int:
    from wongo.profiles import list_profiles

    profiles = list_profiles()
    if _json(args):
        emit_json("profile list", True, profiles=[
            {"slug": p.get("slug"), "journal": p.get("journal"),
             "verified_date": p.get("verified_date"), "dir": p.get("_dir")} for p in profiles])
        return 0
    for p in profiles:
        print(f"{p.get('slug', '?'):16} {p.get('journal', '?'):44} "
              f"verified: {p.get('verified_date', 'NEVER')}")
    return 0


def _cmd_profile_verify(args: argparse.Namespace) -> int:
    from wongo.profiles.verify import verify_profile

    json_mode = _json(args)
    result = verify_profile(args.slug, offline=args.offline,
                            emit=(lambda line: None) if json_mode else print)
    if json_mode:
        emit_json("profile verify", result.ok, result=result)
    return 0 if result.ok else 1


def _wrap(label: str, text: str, width: int = 92) -> list[str]:
    return textwrap.wrap(str(text), width=width, initial_indent=label,
                         subsequent_indent=" " * len(label)) or [label.rstrip()]


def _cmd_profile_show(args: argparse.Namespace) -> int:
    from wongo.profiles import find_profile_dir, load_profile, profile_staleness_days

    pdir = find_profile_dir(args.slug)
    profile = load_profile(args.slug)
    paths = {name: str(pdir / rel) for name, rel in (
        ("skill", "SKILL.md"),
        ("checklist", "references/submission-checklist.md"),
        ("editorial", "references/editorial-framing.md"),
    ) if (pdir / rel).exists()}
    if _json(args):
        emit_json("profile show", True, profile={k: v for k, v in profile.items() if k != "_dir"},
                  dir=pdir, paths=paths)
        return 0
    days = profile_staleness_days(profile)
    lines = [f"{profile.get('slug', args.slug)} — {profile.get('journal', '?')} "
             f"({profile.get('publisher', '?')})",
             f"verified:     {profile.get('verified_date', 'NEVER')}"
             + (f" ({days} days ago)" if days is not None else ""),
             f"portal:       {profile.get('submission_portal') or '—'}",
             "manuscript types:"]
    for t in profile.get("manuscript_types") or []:
        limit = t.get("word_limit")
        refs = " incl. references" if t.get("word_limit_includes_references") else ""
        lines.append(f"  {t.get('type', '?'):<20} {limit if limit is not None else '—'} words{refs}")
        if t.get("counting_rule"):
            lines += _wrap("      rule: ", t["counting_rule"])
        if t.get("abstract_rule"):
            lines += _wrap("      abstract: ", t["abstract_rule"])
    toc = profile.get("toc_graphic") or {}
    toc_text = "not required"
    if toc.get("required"):
        toc_text = (f"required · max {toc.get('width_mm')} × {toc.get('height_mm')} mm"
                    f" · formats {', '.join(toc.get('formats') or []) or '—'}")
    si = profile.get("si") or {}
    lines += [
        f"line numbers: {profile.get('line_numbers')} · spacing: {profile.get('spacing') or '—'}"
        f" · blinding: {profile.get('blinding') or '—'}",
        f"TOC graphic:  {toc_text}",
        f"SI:           separate file: {si.get('separate_file')} · page prefix: "
        f"{si.get('page_prefix') or '—'} · cover sheet: {si.get('needs_cover_sheet')}",
    ]
    for name, path in paths.items():
        lines.append(f"{name + ':':<14}{path}")
    lines.append(f"sources:      {len(profile.get('sources') or [])} "
                 f"(audit with `wongo profile verify {profile.get('slug', args.slug)}`)")
    print("\n".join(lines))
    return 0


def _cmd_style_list(args: argparse.Namespace) -> int:
    from wongo.styles import list_styles

    styles = list_styles()
    if _json(args):
        emit_json("style list", True, styles=styles)
        return 0
    for s in styles:
        print(f"{s['name']:<10} {s['description']}")
    return 0


# ---------------------------------------------------------------------------
# doctor / status


def _cmd_doctor(args: argparse.Namespace) -> int:
    from wongo.doctor import run_doctor
    from wongo.engine.checks import print_report

    checks = run_doctor(Path(args.project))
    hard = [c for c in checks if c.level == "HARD" and not c.ok]
    warn = [c for c in checks if c.level == "WARN" and not c.ok]
    if _json(args):
        emit_json("doctor", not hard, checks=checks)
    else:
        print_report(checks)
        if hard:
            print(f"\ndoctor: {len(hard)} problem(s) to fix before rendering"
                  + (f", {len(warn)} warning(s)" if warn else ""))
        elif warn:
            print(f"\ndoctor: ready to render, {len(warn)} warning(s)")
        else:
            print("\ndoctor: ready to render")
    return 1 if hard else 0


def _cmd_status(args: argparse.Namespace) -> int:
    from wongo.status import format_status, project_status

    status = project_status(Path(args.project))
    if _json(args):
        emit_json("status", status.config_error is None, status=status)
    else:
        print("\n".join(format_status(status)))
    return 0


# ---------------------------------------------------------------------------
# parser


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true",
                        help="print one JSON object instead of text")

    parser = argparse.ArgumentParser(
        prog="wongo",
        description="wongo (원고) — Quarto manuscript pipeline: verified journal "
        "profiles, submission-grade DOCX, Word-coauthor round-tripping.",
    )
    parser.add_argument("--version", action="version", version=f"wongo {__version__}")
    sub = parser.add_subparsers(dest="subcommand", required=True, metavar="<command>")

    p = sub.add_parser("render", parents=[common],
                       help="Render collab- or submission-grade DOCX (main + SI)")
    p.add_argument("--target", required=True, choices=("collab", "submission"))
    p.add_argument("--project", default=".")
    p.add_argument("--style", default=None,
                   help="style profile override (default: _journal.yml style: key)")
    p.set_defaults(fn=_cmd_render, command="render")

    p = sub.add_parser("check", parents=[common],
                       help="Run validation checks (word limit, citekeys, crossrefs, figures)")
    p.add_argument("--project", default=".")
    p.add_argument("--strict", action="store_true", help="exit 1 on any HARD failure")
    p.set_defaults(fn=_cmd_check, command="check")

    p = sub.add_parser("roundtrip", parents=[common],
                       help="Extract a coauthor DOCX's tracked changes into a merge worksheet")
    p.add_argument("docx")
    p.add_argument("--project", default=".")
    p.add_argument("--qmd", default="index.qmd",
                   help="source .qmd the DOCX was rendered from (use si.qmd for a "
                        "coauthor-edited SI render)")
    p.set_defaults(fn=_cmd_roundtrip, command="roundtrip")

    p = sub.add_parser("scaffold", parents=[common], help="Start a new manuscript project")
    p.add_argument("dest", nargs="?", default=".")
    p.add_argument("--journal", default=None, help="journal profile slug (wongo profile list)")
    p.add_argument("--ms-type", default=None, help="manuscript type of that journal")
    p.add_argument("--style", default=None, help="house style (wongo style list)")
    p.add_argument("--example", action="store_true",
                   help="include a small example manuscript that renders out of the box")
    p.set_defaults(fn=_cmd_scaffold, command="scaffold")

    p = sub.add_parser("diff", parents=[common],
                       help="Stamp tracked changes into a revised DOCX vs the "
                            "original submission (S6 marked-up revision)")
    p.add_argument("original", help="originally submitted DOCX")
    p.add_argument("revised", help="revised DOCX (never modified)")
    p.add_argument("-o", "--out", default=None,
                   help="output path (default: <revised-stem>-tracked.docx)")
    p.add_argument("--author", default="Revised manuscript",
                   help="attribution for stamped changes")
    p.add_argument("--date", default=None,
                   help="ISO timestamp for stamped changes (default: now UTC)")
    p.set_defaults(fn=_cmd_diff, command="diff")

    p = sub.add_parser("doctor", parents=[common],
                       help="Check this computer (Quarto, R) and the project's configuration")
    p.add_argument("--project", default=".")
    p.set_defaults(fn=_cmd_doctor, command="doctor")

    p = sub.add_parser("status", parents=[common],
                       help="Where the manuscript stands and the next command to run")
    p.add_argument("--project", default=".")
    p.set_defaults(fn=_cmd_status, command="status")

    p = sub.add_parser("profile", help="Journal profile tools")
    psub = p.add_subparsers(dest="profile_cmd", required=True, metavar="<action>")
    pl = psub.add_parser("list", parents=[common], help="List known journal profiles")
    pl.set_defaults(fn=_cmd_profile_list, command="profile list")
    ps = psub.add_parser("show", parents=[common],
                         help="Show a journal's verified requirements and judgment notes")
    ps.add_argument("slug")
    ps.set_defaults(fn=_cmd_profile_show, command="profile show")
    pv = psub.add_parser("verify", parents=[common],
                         help="Contract lint plus live-refetch drift audit for one profile")
    pv.add_argument("slug")
    pv.add_argument("--offline", action="store_true",
                    help="skip live HEAD checks, only check the contract and staleness")
    pv.set_defaults(fn=_cmd_profile_verify, command="profile verify")

    p = sub.add_parser("style", help="House style tools")
    ssub = p.add_subparsers(dest="style_cmd", required=True, metavar="<action>")
    sl = ssub.add_parser("list", parents=[common], help="List house styles")
    sl.set_defaults(fn=_cmd_style_list, command="style list")

    worksheet_cli.add_parsers(sub, common)  # worksheet status|lint|set, review
    return parser


def main(argv: list[str] | None = None) -> int:
    configure_stdio()
    args = build_parser().parse_args(sys.argv[1:] if argv is None else argv)
    try:
        return int(args.fn(args) or 0)
    except WongoError as exc:
        if _json(args):
            emit_json(getattr(args, "command", "wongo"), False,
                      error={"kind": exc.kind, "message": str(exc)},
                      **getattr(exc, "details", {}))
        else:
            print(str(exc), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
