"""Read-only readiness and locally attributed author decisions for exact builds."""
from __future__ import annotations

import re
from pathlib import Path

from wongo.errors import ConfigError, InputError, WongoError
from wongo.evidence import digest, load_records, make_record, save_record, snapshot, verify_record
from wongo.profiles import load_journal_config

_GATE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*\Z")
_DECISIONS = {"approved", "rejected"}


def manual_gates(cfg: dict) -> list[dict]:
    raw = cfg.get("manual_gates", [])
    if not isinstance(raw, list):
        raise ConfigError("_journal.yml manual_gates must be a list of named gates.")
    gates = []
    seen = set()
    for item in raw:
        if not isinstance(item, dict):
            raise ConfigError("Each manual_gates entry needs id and label strings.")
        unknown = set(item) - {"id", "label", "required"}
        if unknown:
            fields = ', '.join(sorted(map(str, unknown)))
            raise ConfigError(f"Unsupported manual gate fields: {fields}. Use id, label, required.")
        name, label = item.get("id"), item.get("label")
        if not isinstance(name, str) or not _GATE_ID.fullmatch(name):
            raise ConfigError("Each manual gate id must use letters, digits, '.', '_' or '-'.")
        if name in seen:
            raise ConfigError(f"Duplicate manual gate id {name!r}; choose distinct ids.")
        if not isinstance(label, str) or not label.strip():
            raise ConfigError(f"Manual gate {name!r} needs a nonempty label.")
        required = item.get("required", True)
        if not isinstance(required, bool):
            raise ConfigError(f"Manual gate {name!r} required must be true or false.")
        seen.add(name)
        gates.append({"id": name, "label": label.strip(), "required": required})
    for key in ("visual_review_required", "demonstration"):
        if key in cfg and not isinstance(cfg[key], bool):
            raise ConfigError(f"_journal.yml {key} must be true or false.")
    return gates


def _gate(project: Path, gate_id: str) -> dict:
    for gate in manual_gates(load_journal_config(project)):
        if gate["id"] == gate_id:
            return gate
    raise InputError(f"Manual gate {gate_id!r} is not configured. Add its definition to _journal.yml.")


def _reference_records(project: Path, evidence_ids, current: dict) -> list[str]:
    if evidence_ids is None:
        return []
    if not isinstance(evidence_ids, (list, tuple)) or any(
            not isinstance(value, str) or not value for value in evidence_ids):
        raise InputError("Gate evidence references must be a list of evidence record ids.")
    if not evidence_ids:
        return []
    available = {record["record_id"]: record for record in load_records(project)}
    refs = list(dict.fromkeys(evidence_ids))
    for reference in refs:
        record = available.get(reference)
        if record is None or verify_record(project, record, current=current)["state"] != "fresh":
            raise InputError(f"Gate evidence {reference!r} is missing or stale. Refresh it before deciding.")
    return refs


def _current(project: Path, target: str) -> dict | None:
    try:
        return snapshot(project, target)
    except InputError:
        return None


def confirmation_challenge(project: Path, gate_id: str, decision: str = "approved",
                           *, target: str = "submission") -> str:
    if decision not in _DECISIONS:
        raise InputError("Gate decision must be approved or rejected.")
    gate = _gate(Path(project), gate_id)
    current = snapshot(project, target)
    identity = digest({"subject": current["id"], "gate": gate, "decision": decision})[:16]
    return f"CONFIRM {decision} {gate_id} {identity}"


def propose_gate(project: Path, gate_id: str, decision: str = "approved", *,
                 target: str = "submission", proposer: str = "agent", rationale: str = "",
                 evidence_ids: list[str] | None = None) -> dict:
    project = Path(project).resolve()
    gate = _gate(project, gate_id)
    if decision not in _DECISIONS or not isinstance(proposer, str) or not proposer.strip():
        raise InputError("A gate proposal needs approved/rejected and a named proposer.")
    current = snapshot(project, target)
    state = gate_status(project, target, current=current)
    if state["state"] == "invalid":
        raise InputError(state["detail"])
    entry = next(item for item in state["gates"] if item["id"] == gate_id)
    if entry["state"] in _DECISIONS:
        raise InputError("A human decision is already recorded. Have a person review it to change the decision.")
    refs = _reference_records(project, evidence_ids, current)
    record = make_record(
        current, "gate-proposal", {"name": "wongo.gates.propose", "id": gate_id},
        {"gate_id": gate_id, "definition_hash": digest(gate), "proposed_decision": decision,
         "proposer": proposer.strip(), "rationale": rationale, "evidence_ids": refs},
        {"checked": [gate_id], "untested": ["human confirmation"]},
    )
    if snapshot(project, target)["id"] != current["id"] or _gate(project, gate_id) != gate:
        raise InputError("The build changed while proposing a gate. Refresh outputs and propose again.")
    path = save_record(project, record)
    return {"ok": True, "record": record, "path": path}


def confirm_gate(project: Path, gate_id: str, decision: str, *, reviewer: str,
                 confirmation: str, target: str = "submission", rationale: str = "",
                 evidence_ids: list[str] | None = None) -> dict:
    """Record deliberately confirmed local input; this is not identity authentication.

    The interactive CLI obtains the current challenge from the person. Other
    trusted human interfaces must obtain the same explicit confirmation; this
    operation is intentionally absent from agent-facing MCP tools.
    """
    project = Path(project).resolve()
    gate = _gate(project, gate_id)
    if decision not in _DECISIONS or not isinstance(reviewer, str) or not reviewer.strip():
        raise InputError("A human gate decision needs approved/rejected and the person's name.")
    current = snapshot(project, target)
    expected = confirmation_challenge(project, gate_id, decision, target=target)
    if confirmation != expected:
        raise InputError("Explicit confirmation of this current build and gate is required. Review and confirm again.")
    refs = _reference_records(project, evidence_ids, current)
    record = make_record(
        current, "approval",
        {"name": "wongo.gates.review", "id": gate_id, "method": "human-confirmed",
         "identity_assurance": "local-attribution"},
        {"gate_id": gate_id, "definition_hash": digest(gate), "decision": decision,
         "reviewer": reviewer.strip(), "rationale": rationale, "evidence_ids": refs},
        {"checked": [gate_id], "untested": ["authenticated identity", "unconfigured author decisions"]},
    )
    if snapshot(project, target)["id"] != current["id"] or _gate(project, gate_id) != gate:
        raise InputError("The build changed during confirmation. Review the current outputs and confirm again.")
    return {"ok": True, "record": record, "path": save_record(project, record)}


def _validate_gate_record(record: dict) -> None:
    result = record["result"]
    kind = record["kind"]
    decision_key = "decision" if kind == "approval" else "proposed_decision"
    actor_key = "reviewer" if kind == "approval" else "proposer"
    if (not isinstance(result.get("gate_id"), str) or not _GATE_ID.fullmatch(result["gate_id"])
            or not isinstance(result.get(decision_key), str) or result[decision_key] not in _DECISIONS
            or not isinstance(result.get(actor_key), str) or not result[actor_key].strip()
            or not isinstance(result.get("definition_hash"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", result["definition_hash"])):
        raise InputError("The gate record is incomplete; restore or regenerate it.")
    refs = result.get("evidence_ids", [])
    if not isinstance(refs, list) or any(not isinstance(value, str) or not value for value in refs):
        raise InputError("The gate record evidence references are invalid; regenerate it.")
    if kind == "approval" and (record["producer"].get("method") != "human-confirmed"
                               or record["producer"].get("identity_assurance") != "local-attribution"):
        raise InputError("This record does not declare deliberate human confirmation.")


def _gate_record_state(project: Path, record: dict, gate: dict, current: dict | None) -> dict:
    result = record["result"]
    decision_key = "decision" if record["kind"] == "approval" else "proposed_decision"
    actor_key = "reviewer" if record["kind"] == "approval" else "proposer"
    verified = verify_record(project, record, current=current)
    if result["definition_hash"] != digest(gate):
        verified = {"state": "stale", "detail": "The manual gate definition changed."}
    if verified["state"] == "fresh":
        try:
            _reference_records(project, result.get("evidence_ids", []), current or snapshot(project))
        except InputError as exc:
            verified = {"state": "stale", "detail": str(exc)}
    return {**verified, "record_id": record["record_id"], "recorded_at": record["recorded_at"],
            "decision": result[decision_key], "attribution": result[actor_key],
            "rationale": result.get("rationale", ""), "evidence_ids": result.get("evidence_ids", [])}


def gate_status(project: Path, target: str = "submission", *, current: dict | None = None) -> dict:
    project = Path(project).resolve()
    gates = manual_gates(load_journal_config(project))
    current = current or _current(project, target)
    try:
        approvals = load_records(project, "approval", target)
        proposals = load_records(project, "gate-proposal", target)
        for record in approvals + proposals:
            _validate_gate_record(record)
    except InputError as exc:
        return {"state": "invalid", "detail": str(exc), "gates": gates,
                "configured_required_gates_approved": False}
    entries = []
    for gate in gates:
        entry = {**gate, "state": "not-recorded", "approval": None, "proposal": None}
        for name, records in (("approval", approvals), ("proposal", proposals)):
            matching = [record for record in records if record["result"].get("gate_id") == gate["id"]]
            if matching:
                entry[name] = _gate_record_state(project, matching[-1], gate, current)
        if entry["approval"]:
            approval = entry["approval"]
            entry["state"] = approval["decision"] if approval["state"] == "fresh" else approval["state"]
        elif entry["proposal"]:
            proposal = entry["proposal"]
            entry["state"] = "proposed" if proposal["state"] == "fresh" else proposal["state"]
        entries.append(entry)
    required = [entry for entry in entries if entry["required"]]
    states = {entry["state"] for entry in required}
    if not entries:
        state = "not-configured"
    elif not required:
        state = "not-required"
    elif states == {"approved"}:
        state = "approved"
    else:
        state = next((name for name in ("invalid", "rejected", "stale", "proposed", "not-recorded")
                      if name in states), "not-recorded")
    known = {gate["id"] for gate in gates}
    retired = [{"gate_id": record["result"].get("gate_id"), "record_id": record["record_id"],
                "state": "stale", "detail": "The gate is no longer configured."}
               for record in approvals if record["result"].get("gate_id") not in known]
    return {"state": state, "gates": entries, "retired": retired,
            "configured_required_gates_approved": bool(required) and states == {"approved"},
            "scope": "Configured manual gates only; this is not a complete submission-readiness assessment.",
            "identity_assurance": "local-attribution; not authenticated identity",
            "outside_scope": "Unconfigured author decisions remain outside Wongo's knowledge."}


def _audit_status(project: Path, target: str, cfg: dict, current: dict | None) -> dict:
    from wongo.audit import validate_audit_record
    from wongo.engine.inputs import audit_specs

    specs = audit_specs(project, cfg)
    if not specs:
        return {"state": "not-configured", "checks": [], "required_passed": True}
    try:
        records = load_records(project, "audit", target)
    except InputError as exc:
        return {"state": "invalid", "detail": str(exc), "checks": [], "required_passed": False}
    entries = []
    for spec in specs:
        name = spec.get("id")
        required = spec["required"]
        matches = [record for record in records
                   if record["result"].get("audit_id", record["producer"].get("id")) == name]
        entry = {"id": name, "required": required, "state": "not-recorded", "coverage": {}}
        if matches:
            record = matches[-1]
            verified = verify_record(project, record, current=current)
            entry.update(verified, record_id=record["record_id"], coverage=record["coverage"])
            if entry["state"] == "fresh":
                try:
                    validate_audit_record(record, spec, project)
                    entry["state"] = "passed" if record["result"]["ok"] else "failed"
                except InputError as exc:
                    entry.update(state="invalid", detail=str(exc))
        entries.append(entry)
    required_entries = [entry for entry in entries if entry["required"]]
    considered = required_entries or entries
    states = {entry["state"] for entry in considered}
    state = "passed" if states == {"passed"} else next(
        (name for name in ("invalid", "failed", "stale", "not-recorded") if name in states), "not-recorded")
    return {"state": state, "checks": entries,
            "required_passed": all(entry["state"] == "passed" for entry in required_entries)}


def _visual_status(project: Path, target: str, cfg: dict, current: dict | None) -> dict:
    required = cfg.get("visual_review_required", False)
    try:
        previews = load_records(project, "preview", target)
        reviews = load_records(project, "visual-review", target)
        inspections = load_records(project, "inspection", target)
    except InputError as exc:
        return {"state": "invalid", "detail": str(exc), "required": required, "required_passed": False}
    result = {"state": "not-recorded", "required": required, "required_passed": not required,
              "scope": "Required visual readiness needs complete human page coverage and any recorded "
                       "OOXML inventory to pass; absent OOXML inspection is reported separately."}
    if inspections:
        inspection = inspections[-1]
        inspected = verify_record(project, inspection, current=current)
        if inspected["state"] == "fresh":
            ok = inspection["result"].get("ok")
            inspected["state"] = "passed" if ok is True else "failed" if ok is False else "invalid"
        result["inspection"] = {**inspected, "record_id": inspection["record_id"]}
    else:
        result["inspection"] = {"state": "not-recorded"}
    if reviews and reviews[-1]["result"].get("representation") == "native-word-inspection":
        review = reviews[-1]
        checked = verify_record(project, review, current=current)
        if checked["state"] != "fresh":
            return {**result, **checked, "required_passed": not required}
        reviewed = review["result"]
        documents = reviewed.get("documents")
        if (not isinstance(documents, dict) or not isinstance(reviewed.get("reviewer"), str)
                or not reviewed["reviewer"].strip() or not isinstance(reviewed.get("word_version"), str)
                or not reviewed["word_version"].strip() or reviewed.get("native_word_attested") is not True
                or reviewed.get("verification_method") != "local-human-attestation"):
            return {**result, "state": "invalid", "detail": "Native Word inspection attribution is incomplete.",
                    "required_passed": False}
        outputs = review["subject"].get("outputs") or {}
        expected = set()
        try:
            for name, info in documents.items():
                count = info["page_count"]
                if type(count) is not int or count <= 0 or info["docx_sha256"] != outputs.get(name):
                    raise ValueError("Native Word inspection document identity or page count is invalid.")
                expected.update((name, page) for page in range(1, count + 1))
            actual = {(page["document"], page["page"]) for page in reviewed["checked_pages"]}
            if any(type(page["page"]) is not int or page["page"] <= 0
                   for page in reviewed["checked_pages"]) or not actual <= expected:
                raise ValueError("Native Word inspection pages are outside the declared documents.")
        except (KeyError, TypeError, ValueError) as exc:
            return {**result, "state": "invalid", "detail": str(exc), "required_passed": False}
        complete = bool(expected) and actual == expected and set(documents) == set(outputs)
        state = "passed" if complete and reviewed.get("complete") is True else "partial"
        if reviewed.get("ok") is not True:
            state = "failed" if reviewed.get("ok") is False else "invalid"
        if result["inspection"]["state"] in {"failed", "invalid", "stale"}:
            state = result["inspection"]["state"]
        return {**result, "state": state, "review_record_id": review["record_id"],
                "reviewer": reviewed["reviewer"], "coverage": review["coverage"],
                "representation": "native-word-inspection", "native_word_verified": False,
                "native_word_attested": True,
                "identity_assurance": "locally attributed human attestation; not automated verification",
                "required_passed": not required or state == "passed"}
    if not previews:
        return result
    preview = previews[-1]
    result["preview_record_id"] = preview["record_id"]
    checked = verify_record(project, preview, current=current)
    result["preview"] = {**checked, "record_id": preview["record_id"]}
    if checked["state"] != "fresh":
        return {**result, **checked, "required_passed": not required}
    try:
        from wongo.qa import _page_map

        pages = _page_map(preview)
        if preview["result"].get("ok") is not True:
            raise InputError("The preview is not a successful page inventory. Generate it again.")
    except InputError as exc:
        return {**result, "state": "invalid", "detail": str(exc), "required_passed": False,
                "preview": {"state": "invalid", "detail": str(exc), "record_id": preview["record_id"]}}
    if not reviews:
        return result
    review = reviews[-1]
    checked = verify_record(project, review, current=current)
    if checked["state"] != "fresh":
        return {**result, **checked, "required_passed": not required}
    reviewed = review["result"]
    if reviewed.get("preview_record_id") != preview["record_id"]:
        return {**result, "state": "stale", "detail": "Preview identity changed; inspect or explicitly carry review.",
                "required_passed": not required}
    try:
        expected = {(document, number, page["sha256"]) for (document, number), page in pages.items()}
        actual = {(page["document"], page["page"], page["sha256"])
                  for page in reviewed["checked_pages"]}
    except (KeyError, TypeError) as exc:
        return {**result, "state": "invalid", "detail": f"Incomplete visual coverage: {exc}",
                "required_passed": False}
    if (not actual <= expected or not isinstance(reviewed.get("reviewer"), str)
            or not reviewed["reviewer"].strip()
            or any(type(page["page"]) is not int or page["page"] <= 0
                   for page in reviewed["checked_pages"])):
        return {**result, "state": "invalid", "detail": "Visual review does not match preview pages.",
                "required_passed": False}
    complete = bool(expected) and actual == expected
    state = "passed" if complete and reviewed.get("complete") is True else "partial"
    if reviewed.get("ok") is not True:
        state = "failed" if reviewed.get("ok") is False else "invalid"
    if result["inspection"]["state"] in {"failed", "invalid", "stale"}:
        state = result["inspection"]["state"]
    return {**result, "state": state, "review_record_id": review["record_id"],
            "reviewer": reviewed["reviewer"], "coverage": review["coverage"],
            "representation": "converted-preview", "native_word_verified": False,
            "required_passed": not required or state == "passed"}


def readiness(project: Path, target: str = "submission", *, checks=None, outputs=None) -> dict:
    from wongo.engine import output_freshness, read_manifest
    from wongo.engine.checks import run_checks

    project = Path(project).resolve()
    cfg = load_journal_config(project)
    manual_gates(cfg)
    checks = run_checks(project) if checks is None else checks
    freshness = outputs if outputs is not None else output_freshness(project, target)
    failed = [check.name for check in checks if check.level == "HARD" and not check.ok]
    entry = (read_manifest(project).get("targets") or {}).get(target) or {}
    failed = sorted(set(failed + list(entry.get("checks_failed") or [])))
    state = "failed" if failed else {
        "fresh": "passed", "missing": "not-recorded", "unknown": "not-recorded",
        "stale": "stale", "modified": "stale",
    }.get(freshness["state"], "not-recorded")
    current = _current(project, target)
    technical = {"state": state, "hard_failures": failed, "render_state": freshness["state"],
                 "scope": "Machine checks and render freshness; no author authorization."}
    audit = _audit_status(project, target, cfg, current)
    visual = _visual_status(project, target, cfg, current)
    author = gate_status(project, target, current=current)
    coauthors = coauthor_decisions(project, demonstration=cfg.get("demonstration", False))
    author["coauthor_rows"] = coauthors
    author["scope"] = "Configured manual gates; coauthor worksheet decisions are reported separately."
    approved = (target == "submission" and state == "passed" and audit["required_passed"] and visual["required_passed"]
                and author["configured_required_gates_approved"] and not coauthors["open"]
                and coauthors["state"] != "invalid")
    return {"target": target, "technical": technical, "audit": audit, "visual": visual,
            "author_decisions": author, "submission_approved": approved,
            "demonstration": cfg.get("demonstration", False)}


def coauthor_decisions(project: Path, *, demonstration: bool = False) -> dict:
    from wongo.engine.worksheet import Worksheet

    folder = Path(project) / "decisions"
    context = "demonstration" if demonstration else "coauthor-decisions"
    result = {"state": "not-recorded", "worksheet": None, "open": 0, "context": context}
    try:
        sheets = sorted(folder.glob("merge-*.md"), key=lambda path: (path.stat().st_mtime, path.name))
        if not sheets:
            return result
        sheet = sheets[-1]
        count = Worksheet.load(sheet).counts().needs_decision
    except (OSError, WongoError) as exc:
        return {**result, "state": "invalid", "detail": f"Could not read coauthor worksheet: {exc}"}
    return {"state": "pending" if count else "resolved", "worksheet": sheet.relative_to(project).as_posix(),
            "open": count, "context": context}
