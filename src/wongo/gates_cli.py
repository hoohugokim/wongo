"""CLI adapters for proposals and deliberately confirmed local author decisions."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from wongo.clitools import emit_json, is_interactive
from wongo.errors import InputError
from wongo.gates import confirm_gate, confirmation_challenge, gate_status, propose_gate


def add_parsers(sub, common: argparse.ArgumentParser) -> None:
    parser = sub.add_parser("gates", help="Inspect, propose, and human-review author decisions")
    actions = parser.add_subparsers(dest="gates_command", required=True, metavar="<action>")
    for action in ("status", "propose", "review"):
        command = actions.add_parser(action, parents=[common])
        command.add_argument("--project", default=".")
        command.add_argument("--target", default="submission", choices=("collab", "submission"))
        if action == "propose":
            command.add_argument("gate")
            command.add_argument("--decision", choices=("approved", "rejected"), default="approved")
            command.add_argument("--proposer", default="agent")
            command.add_argument("--rationale", default="")
            command.add_argument("--evidence", action="append", default=[])
        elif action == "review":
            command.add_argument("gate", nargs="?")
            command.add_argument("--reviewer", default=None)
            command.add_argument("--evidence", action="append", default=[])
        command.set_defaults(fn={"status": cmd_status, "propose": cmd_propose, "review": cmd_review}[action],
                             command=f"gates {action}")


def _lines(state: dict) -> list[str]:
    lines = [f"configured author gates: {state['state']}"]
    if not state.get("gates"):
        lines.append("Author authorization is not configured; no submission approval is recorded.")
    for gate in state.get("gates", []):
        lines.append(f"  {gate['id']}: {gate.get('state', 'invalid')} — {gate['label']}")
        for kind in ("approval", "proposal"):
            evidence = gate.get(kind)
            if evidence:
                lines.append(f"    {kind}: {evidence['state']} · {evidence.get('attribution', '?')}")
    lines.append("Decision attribution is local; Wongo does not authenticate identity.")
    return lines


def cmd_status(args) -> int:
    result = gate_status(Path(args.project), args.target)
    if args.json:
        emit_json("gates status", result["state"] != "invalid", author_decisions=result)
    else:
        print("\n".join(_lines(result)))
    return 1 if result["state"] == "invalid" else 0


def cmd_propose(args) -> int:
    result = propose_gate(Path(args.project), args.gate, args.decision, target=args.target,
                          proposer=args.proposer, rationale=args.rationale, evidence_ids=args.evidence)
    if args.json:
        emit_json("gates propose", True, **{key: value for key, value in result.items() if key != "ok"})
    else:
        print(f"proposal recorded: {result['path']}")
        print("A person must run wongo gates review to confirm this decision.")
    return 0


def _ask(prompt: str) -> str:
    print(prompt, file=sys.stderr, flush=True)
    return input().strip()


def cmd_review(args) -> int:
    if not is_interactive():
        raise InputError(
            "wongo gates review needs a person at a terminal. Ask the author to run it; "
            "agents may record proposals with wongo gates propose."
        )
    project = Path(args.project)
    state = gate_status(project, args.target)
    if state["state"] == "invalid":
        raise InputError(state["detail"])
    entries = [gate for gate in state["gates"] if args.gate is None or gate["id"] == args.gate]
    if not entries:
        raise InputError("No matching manual gate is configured. Add manual_gates to _journal.yml.")
    reviewer = args.reviewer or _ask("Your name for the local decision record:")
    if not reviewer.strip():
        raise InputError("A reviewer name is required to attribute the decision.")
    decisions = []
    for gate in entries:
        print(f"{gate['label']} ({gate['id']}): current state {gate.get('state', 'invalid')}", file=sys.stderr)
        print("Review the exact outputs and supporting evidence before deciding.", file=sys.stderr)
        selection = _ask("1 approve · 2 reject · 3 skip")
        if selection in {"", "3"}:
            continue
        if selection not in {"1", "2"}:
            raise InputError("Type 1, 2, or 3 for a gate decision; no decision was recorded for this gate.")
        decision = "approved" if selection == "1" else "rejected"
        challenge = confirmation_challenge(project, gate["id"], decision, target=args.target)
        confirmation = _ask(f"To confirm this exact build and decision, type: {challenge}")
        rationale = _ask("Decision note (optional):")
        proposal = gate.get("proposal") or {}
        refs = args.evidence or (proposal.get("evidence_ids", []) if proposal.get("state") == "fresh" else [])
        decisions.append(confirm_gate(project, gate["id"], decision, reviewer=reviewer,
                                      confirmation=confirmation, target=args.target,
                                      rationale=rationale, evidence_ids=refs))
    result = gate_status(project, args.target)
    if args.json:
        emit_json("gates review", True, decisions=decisions, author_decisions=result)
    else:
        print("\n".join(_lines(result)))
    return 0
