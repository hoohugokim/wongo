"""CLI adapters for explicit audits and portable evidence."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from wongo.clitools import emit_json
from wongo.errors import InputError
from wongo.evidence import load_records, verify_record
from wongo.review_export import compare_artifacts, export_review, verify_bundle
from wongo.textio import read_text


def _show(args, command, result):
    ok = result.get("ok", True)
    if args.json:
        emit_json(command, ok, **{key: value for key, value in result.items() if key != "ok"})
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0 if ok else 1


def audit(args):
    from wongo.audit import run_audits

    def on_event(kind, payload):
        if kind == "diagnostic":
            text = payload["text"]
            print(text, file=sys.stderr, end="" if text.endswith("\n") else "\n")

    return _show(args, "audit", run_audits(Path(args.project), args.target, args.name,
                                          on_event=on_event))


def list_evidence(args):
    project = Path(args.project)
    records = load_records(project, kind=args.kind, target=args.target)
    return _show(args, "evidence list", {"ok": True, "records": [
        {"record": record, **verify_record(project, record)} for record in records
    ]})


def verify(args):
    path = Path(args.file)
    if path.suffix.lower() == ".zip":
        result = verify_bundle(path)
    else:
        try:
            record = json.loads(read_text(path))
        except (OSError, ValueError) as exc:
            raise InputError("Evidence JSON could not be read. Select a valid receipt.") from exc
        result = verify_record(Path(args.project), record)
        result["ok"] = result["state"] == "fresh"
    return _show(args, "evidence verify", result)


def export(args):
    result = export_review(Path(args.project), Path(args.destination), args.target,
                           include=args.include, include_outputs=args.outputs,
                           include_artifacts=args.artifacts, record_ids=args.record)
    return _show(args, "evidence export", result)


def compare(args):
    return _show(args, "evidence compare", {"ok": True, **compare_artifacts(
        Path(args.first), Path(args.second))})


def note(args):
    from wongo.review_notes import add_review_note

    try:
        references = json.loads(read_text(Path(args.references)))
    except (OSError, ValueError) as exc:
        raise InputError("Review references must be a readable JSON list. See docs/build-evidence.md.") from exc
    result = add_review_note(Path(args.project), args.reviewer, args.statement, references,
                             args.target, reviewer_identity=args.reviewer_identity)
    return _show(args, "evidence note", result)


def disposition(args):
    from wongo.clitools import is_interactive
    from wongo.evidence import snapshot
    from wongo.review_notes import record_disposition

    if not is_interactive():
        raise InputError("evidence disposition needs a person at a terminal to assess the review claim.")
    project = Path(args.project)
    current = snapshot(project, args.target)
    records = load_records(project, "review-note", args.target)
    claim = next((record for record in records if record["record_id"] == args.note), None)
    if claim is None or verify_record(project, claim, current=current)["state"] != "fresh":
        raise InputError("Select a current review-note record before deciding its disposition.")
    print(f"Reviewer {claim['result']['reviewer']}: {claim['result']['statement']}", file=sys.stderr)
    print(json.dumps(claim["result"]["references"], ensure_ascii=False, indent=2), file=sys.stderr)
    print(f"Record {args.decision} by {args.maintainer}? Type 1 to confirm; other input cancels.", file=sys.stderr)
    try:
        answer = input().strip()
    except EOFError as exc:
        raise InputError("No review disposition recorded. Confirm at a terminal.") from exc
    if answer != "1":
        raise InputError("Review disposition cancelled; no record written.")
    if snapshot(project, args.target)["id"] != current["id"]:
        raise InputError("Build changed during confirmation. Inspect the current claim and retry.")
    result = record_disposition(project, args.note, args.decision, args.maintainer,
                                args.reason, args.target, confirmed=True)
    return _show(args, "evidence disposition", result)


def add_parsers(sub, common):
    command = sub.add_parser("audit", parents=[common],
                             help="Explicitly run project-declared contextual audits")
    command.add_argument("--project", default=".")
    command.add_argument("--target", default="submission", choices=("collab", "submission"))
    command.add_argument("--name", default=None)
    command.set_defaults(fn=audit, command="audit")
    group = sub.add_parser("evidence", help="Inspect, verify and export build evidence")
    actions = group.add_subparsers(dest="evidence_action", required=True)
    command = actions.add_parser("list", parents=[common])
    command.add_argument("--project", default=".")
    command.add_argument("--target", default="submission", choices=("collab", "submission"))
    command.add_argument("--kind", default=None)
    command.set_defaults(fn=list_evidence, command="evidence list")
    command = actions.add_parser("verify", parents=[common])
    command.add_argument("file")
    command.add_argument("--project", default=".")
    command.set_defaults(fn=verify, command="evidence verify")
    command = actions.add_parser("export", parents=[common])
    command.add_argument("destination")
    command.add_argument("--project", default=".")
    command.add_argument("--target", default="submission", choices=("collab", "submission"))
    command.add_argument("--include", action="append", default=[])
    command.add_argument("--outputs", action="store_true", help="Include sealed DOCX files")
    command.add_argument("--artifacts", action="store_true", help="Include generated evidence artifacts")
    command.add_argument("--record", action="append", default=None)
    command.set_defaults(fn=export, command="evidence export")
    command = actions.add_parser("compare", parents=[common])
    command.add_argument("first")
    command.add_argument("second")
    command.set_defaults(fn=compare, command="evidence compare")
    command = actions.add_parser("note", parents=[common], help="Record an attributed reviewer claim")
    command.add_argument("--project", default=".")
    command.add_argument("--target", default="submission", choices=("collab", "submission"))
    command.add_argument("--reviewer", required=True)
    command.add_argument("--reviewer-identity", default=None)
    command.add_argument("--statement", required=True)
    command.add_argument("--references", required=True, help="JSON file containing exact source/artifact references")
    command.set_defaults(fn=note, command="evidence note")
    command = actions.add_parser("disposition", parents=[common], help="Human disposition of a claim; needs a terminal")
    command.add_argument("note", help="Exact review-note record id")
    command.add_argument("--project", default=".")
    command.add_argument("--target", default="submission", choices=("collab", "submission"))
    command.add_argument("--decision", required=True, choices=("accept", "reject", "needs-work"))
    command.add_argument("--maintainer", required=True)
    command.add_argument("--reason", required=True)
    command.set_defaults(fn=disposition, command="evidence disposition")
