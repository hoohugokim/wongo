"""Attributed reviewer claims and separately confirmed maintainer dispositions."""
from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path

from lxml import etree

from wongo.errors import InputError
from wongo.evidence import (
    evidence_dir,
    hash_file,
    load_records,
    make_record,
    safe_path,
    save_record,
    snapshot,
    verify_record,
)
from wongo.textio import read_text

_NAMESPACES = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
}
_DECISIONS = {"accept", "reject", "needs-work"}


def _text(value, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InputError(f"Review {label} must be a nonempty string.")
    return value.strip()


def _json_pointer(path: Path, pointer: str) -> None:
    if not pointer.startswith("/") or re.search(r"~(?![01])", pointer):
        raise InputError("Review JSON pointer must use RFC 6901 '/key/index' syntax.")
    try:
        value = json.loads(read_text(path))
        for component in pointer[1:].split("/"):
            key = component.replace("~1", "/").replace("~0", "~")
            if isinstance(value, dict):
                value = value[key]
            elif isinstance(value, list) and re.fullmatch(r"0|[1-9][0-9]*", key):
                value = value[int(key)]
            else:
                raise KeyError(key)
    except (ValueError, KeyError, IndexError, OSError) as exc:
        raise InputError(f"Review JSON pointer {pointer!r} does not resolve in {path.name}.") from exc


def _artifact_pointer(path: Path, pointer: str) -> None:
    if pointer == "/":
        return
    if path.suffix.lower() == ".json":
        _json_pointer(path, pointer)
        return
    if path.suffix.lower() == ".docx":
        member, separator, expression = pointer.partition("#xpath=")
        if (not member or member.startswith("/") or ".." in Path(member).parts
                or ("#" in member) or (separator and not expression.startswith("/"))):
            raise InputError("Review DOCX pointer must name an OPC member, optionally '#xpath=/...'.")
        try:
            with zipfile.ZipFile(path) as package:
                raw = package.read(member)
            if separator:
                root = etree.fromstring(raw, parser=etree.XMLParser(resolve_entities=False, no_network=True))
                nodes = root.xpath(expression, namespaces=_NAMESPACES)
                if not isinstance(nodes, list) or not nodes:
                    raise ValueError("XPath must select at least one existing node")
        except (OSError, KeyError, ValueError, zipfile.BadZipFile, etree.Error) as exc:
            raise InputError(f"Review DOCX member/pointer {pointer!r} does not resolve in {path.name}.") from exc
        return
    raise InputError("Unsupported review artifact pointer. Use '/' for the whole file, a JSON pointer, "
                     "or a DOCX OPC member with optional '#xpath=/...'.")


def _references(project: Path, references) -> tuple[list[dict], list[dict]]:
    if not isinstance(references, list) or not references:
        raise InputError("Review references must be a nonempty list of exact source or artifact locations.")
    normalized, artifacts = [], {}
    for item in references:
        if not isinstance(item, dict):
            raise InputError("Each review reference must be a source_file/line or artifact/pointer mapping.")
        source = "source_file" in item
        allowed = {"source_file", "line", "end_line"} if source else {"artifact", "pointer"}
        if set(item) - allowed:
            raise InputError("A review reference must contain only source_file/line/end_line or artifact/pointer.")
        raw = item.get("source_file" if source else "artifact")
        path = safe_path(project, raw)
        relative = path.relative_to(project).as_posix()
        before = hash_file(path)
        if source:
            first, last = item.get("line"), item.get("end_line", item.get("line"))
            if type(first) is not int or type(last) is not int or first < 1 or last < first:
                raise InputError("Review source line/end_line must be positive integers in ascending order.")
            try:
                lines = read_text(path).splitlines()
            except (OSError, UnicodeError) as exc:
                raise InputError(f"Review source {relative} must be readable text.") from exc
            if last > len(lines):
                raise InputError(f"Review source line range exceeds {relative}'s {len(lines)} lines.")
            reference = {"source_file": relative, "line": first, "end_line": last, "sha256": before}
        else:
            pointer = _text(item.get("pointer"), "artifact pointer")
            _artifact_pointer(path, pointer)
            reference = {"artifact": relative, "pointer": pointer, "sha256": before}
        if hash_file(path) != before:
            raise InputError(f"Review reference {relative} changed while reading. Finish saving and retry.")
        normalized.append(reference)
        artifacts[relative] = before
    return normalized, [{"path": key, "sha256": value} for key, value in sorted(artifacts.items())]


def _save_current(project: Path, target: str, current: dict, record: dict) -> dict:
    after = snapshot(project, target)
    if after["id"] != current["id"] or verify_record(project, record, current=after)["state"] != "fresh":
        raise InputError("The build or review references changed. Refresh outputs and retry the review record.")
    path = save_record(project, record)
    return {"ok": True, "record": record, "path": path}


def add_review_note(project: Path, reviewer: str, statement: str, references,
                    target: str = "submission", *, reviewer_identity: str | None = None) -> dict:
    """Record an unverified claim; no correctness or readiness conclusion is inferred."""
    project = Path(project).resolve()
    reviewer, statement = _text(reviewer, "reviewer"), _text(statement, "statement")
    if reviewer_identity is not None:
        reviewer_identity = _text(reviewer_identity, "reviewer identity")
    current = snapshot(project, target)
    normalized, artifacts = _references(project, references)
    record = make_record(
        current, "review-note",
        {"name": "wongo.review_notes", "mechanism": "attributed-reviewer-claim",
         "identity_authenticated": False},
        {"reviewer": reviewer, "reviewer_identity": reviewer_identity, "statement": statement,
         "references": normalized, "claim_status": "unverified"},
        {"checked": ["reference locations and file identities"],
         "untested": ["reviewer claim correctness", "scientific validity"],
         "scope": "Attributed claim only; reference validation does not validate the claim."},
        artifacts=artifacts,
    )
    return _save_current(project, target, current, record)


def record_disposition(project: Path, note_id: str, decision: str, maintainer: str, reason: str,
                       target: str = "submission", *, confirmed: bool = False) -> dict:
    """Called only after a human interface obtains deliberate confirmation."""
    if confirmed is not True:
        raise InputError("A review disposition requires explicit human confirmation; an agent cannot approve it.")
    if not isinstance(decision, str) or decision not in _DECISIONS:
        raise InputError("Review disposition must be accept, reject, or needs-work.")
    maintainer, reason = _text(maintainer, "maintainer"), _text(reason, "reason")
    if not isinstance(note_id, str) or not re.fullmatch(r"[0-9a-f]{64}", note_id):
        raise InputError("Review note id must be the exact record id of an existing note.")
    project = Path(project).resolve()
    current = snapshot(project, target)
    note = next((record for record in load_records(project, "review-note", target)
                 if record["record_id"] == note_id), None)
    if note is None:
        raise InputError("Review note is missing for this target. Record or select a current note first.")
    if verify_record(project, note, current=current)["state"] != "fresh":
        raise InputError("Review note is stale. Review the current build and record a new note first.")
    note_path = evidence_dir(project) / "review-note" / f"{note_id}.json"
    artifacts = [*note["artifacts"], {"path": note_path.relative_to(project).as_posix(),
                                      "sha256": hash_file(note_path)}]
    record = make_record(
        current, "review-disposition",
        {"name": "wongo.review_notes", "mechanism": "local-human-attestation",
         "identity_authenticated": False},
        {"review_note_id": note_id, "decision": decision, "maintainer": maintainer,
         "reason": reason, "confirmed": True, "claim_status": "unverified"},
        {"checked": ["explicit maintainer disposition"],
         "untested": ["reviewer claim correctness", "scientific validity", "authenticated identity"],
         "scope": "Human disposition of a claim; independent of automated checks and author gates."},
        artifacts=artifacts,
    )
    return _save_current(project, target, current, record)


def review_status(project: Path, target: str = "submission") -> dict:
    project = Path(project).resolve()
    try:
        current = snapshot(project, target)
    except InputError:
        current = None
    dispositions = load_records(project, "review-disposition", target)
    notes = []
    for record in load_records(project, "review-note", target):
        state = verify_record(project, record, current=current)
        entries = []
        for disposition in dispositions:
            if disposition["result"].get("review_note_id") == record["record_id"]:
                entries.append({"record_id": disposition["record_id"],
                                **disposition["result"],
                                **verify_record(project, disposition, current=current)})
        notes.append({"record_id": record["record_id"], **record["result"],
                      **state, "dispositions": entries})
    return {"target": target, "notes": notes,
            "scope": "Reviewer claims and maintainer dispositions do not determine machine readiness."}
