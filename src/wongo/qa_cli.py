"""Explicit QA commands; human page inspection is confirmed at a terminal."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from wongo import clitools
from wongo.errors import InputError
from wongo.qa import (
    _find_record,
    _page_map,
    carry_visual_review,
    create_preview,
    inspect_outputs,
    record_native_review,
    record_visual_review,
)


def add_parsers(sub, common: argparse.ArgumentParser) -> None:
    parser = sub.add_parser("qa", help="Inspect final DOCX, export layout previews, and record page inspection")
    actions = parser.add_subparsers(dest="qa_command", required=True)
    for name, help_text, handler in (
        ("inspect", "Inventory final OOXML images/descriptions, tables, equations and revisions", cmd_inspect),
        ("preview", "Generate optional renderer-specific PDF and page images", cmd_preview),
        ("review", "Record pages a person inspected; needs a terminal", cmd_review),
        ("native-review", "Record a person's native Microsoft Word inspection; needs a terminal", cmd_native_review),
        ("carry", "Carry existing inspection only onto matching renderer/settings and page bytes", cmd_carry),
    ):
        item = actions.add_parser(name, parents=[common], help=help_text)
        item.add_argument("--project", default=".")
        item.add_argument("--target", choices=("collab", "submission"), default="submission")
        item.set_defaults(fn=handler, command=f"qa {name}")
        if name == "preview":
            item.add_argument("--renderer", choices=("libreoffice",), default="libreoffice")
            item.add_argument("--dpi", type=int, default=144)
            item.add_argument("--timeout", type=int, default=120)
        elif name in {"review", "native-review"}:
            if name == "review":
                item.add_argument("--preview", default=None, help="Preview record id; default: latest")
            else:
                item.add_argument("--word-version", required=True)
                item.add_argument("--document", required=True, action="append", help="Native document.docx:page-count (repeat for every output)")
            item.add_argument("--reviewer", required=True)
            selection = item.add_mutually_exclusive_group(required=True)
            selection.add_argument("--page", action="append", help="Inspected document:page (repeatable)")
            selection.add_argument("--all-pages", action="store_true")
            item.add_argument("--note", default="")
        elif name == "carry":
            item.add_argument("--preview", required=True, help="Current preview record id")
            item.add_argument("--review", required=True, help="Prior visual-review record id")


def _emit(args, result) -> int:
    if args.json:
        clitools.emit_json(args.command, result["ok"], **{k: v for k, v in result.items() if k != "ok"})
    else:
        print(f"{args.command}: {'recorded' if result['ok'] else 'issues found'}")
        print(f"evidence: {result['path']}")
        if args.command == "qa preview":
            print("Converted layout preview; native Microsoft Word pagination remains unverified.")
            for name, document in result["record"]["result"]["documents"].items():
                print(f"  {name}: {document['page_count']} pages; {document['pdf']['path']}")
        if args.command == "qa inspect":
            for name, document in result["record"]["result"]["documents"].items():
                for issue in document["issues"]:
                    print(f"  {name}: {issue['id']}: {issue['detail']}")
    return 0 if result["ok"] else 1


def cmd_inspect(args) -> int:
    return _emit(args, inspect_outputs(Path(args.project), args.target))


def cmd_preview(args) -> int:
    return _emit(args, create_preview(Path(args.project), args.target, renderer=args.renderer,
                                     dpi=args.dpi, timeout=args.timeout))


def cmd_review(args) -> int:
    if not clitools.is_interactive():
        raise InputError("wongo qa review needs a person at a terminal. Open the page images and confirm the pages actually inspected.")
    project = Path(args.project)
    preview = _find_record(project, "preview", args.target, args.preview)
    if args.all_pages:
        pages = [{"document": name, "page": number} for name, number in _page_map(preview)]
    else:
        pages = []
        for raw in args.page:
            try:
                name, number = raw.rsplit(":", 1)
                pages.append({"document": name, "page": int(number)})
            except (ValueError, AttributeError) as exc:
                raise InputError("Use --page document.docx:1 for each inspected page.") from exc
    print(f"Record {len(pages)} inspected preview page(s) for {args.reviewer}?", file=sys.stderr)
    print("This records converted page inspection; native Word pagination stays unverified.", file=sys.stderr)
    print("Type 1 to confirm that you inspected these pages; any other input cancels.", file=sys.stderr)
    try:
        answer = input()
    except EOFError as exc:
        raise InputError("No visual inspection was recorded. Confirm at a terminal after inspecting pages.") from exc
    if answer.strip() != "1":
        raise InputError("Visual inspection cancelled; no evidence record was written.")
    return _emit(args, record_visual_review(project, args.target, args.reviewer, pages,
                                            preview_id=preview["record_id"], note=args.note,
                                            confirmed=True))


def cmd_carry(args) -> int:
    return _emit(args, carry_visual_review(Path(args.project), args.target, args.preview, args.review))


def cmd_native_review(args) -> int:
    from wongo.evidence import snapshot

    if not clitools.is_interactive():
        raise InputError("wongo qa native-review needs a person at a terminal after native Word inspection.")
    current = snapshot(Path(args.project), args.target)
    documents = {}
    try:
        for raw in args.document:
            name, count = raw.rsplit(":", 1)
            if name in documents:
                raise ValueError("duplicate document")
            documents[name] = int(count)
        pages = ([{"document": name, "page": number} for name, count in documents.items()
                  for number in range(1, count + 1)] if args.all_pages else
                 [{"document": raw.rsplit(":", 1)[0], "page": int(raw.rsplit(":", 1)[1])}
                  for raw in args.page])
    except (ValueError, IndexError) as exc:
        raise InputError("Use --document file.docx:page-count and --page file.docx:page.") from exc
    print(f"Record {len(pages)} native Word page(s) inspected by {args.reviewer} using Word {args.word_version}?", file=sys.stderr)
    print("Type 1 to attest you inspected those exact final DOCX files; any other input cancels.", file=sys.stderr)
    try:
        answer = input()
    except EOFError as exc:
        raise InputError("No native Word inspection was recorded; confirm after inspecting current files.") from exc
    if answer.strip() != "1":
        raise InputError("Native Word inspection cancelled; no evidence record was written.")
    return _emit(args, record_native_review(Path(args.project), args.target, args.reviewer,
                                            args.word_version, documents, pages, note=args.note,
                                            confirmed=True, subject_id=current["id"]))
