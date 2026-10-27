"""Author decisions are explicit, attributed, and tied to exact evidence."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

from wongo.engine import render_project
from wongo.errors import ConfigError, InputError
from wongo.evidence import digest, evidence_dir, hash_file, make_record, save_record, snapshot
from wongo.gates import (
    confirm_gate,
    confirmation_challenge,
    gate_status,
    manual_gates,
    propose_gate,
    readiness,
)


@pytest.fixture(autouse=True)
def stable_engine_identity(monkeypatch):
    monkeypatch.setattr("wongo.evidence.engine_identity", lambda: {"sha256": "test-engine"})


def configure(project, **values):
    path = project / "_journal.yml"
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    cfg.update(values)
    path.write_text(yaml.safe_dump(cfg), encoding="utf-8")


def configured(project):
    configure(project, manual_gates=[{"id": "submission", "label": "Author submission decision"}])


def approve(project):
    return confirm_gate(
        project, "submission", "approved", reviewer="Ada", target="submission",
        confirmation=confirmation_challenge(project, "submission"),
    )


@pytest.mark.parametrize("raw", ["yes", {}, [{"id": "bad id", "label": "Bad"}],
                                  [{"id": "x", "label": ""}],
                                  [{"id": "x", "label": "Gate", "required": "yes"}],
                                  [{"id": "x", "label": "Gate", 1: "unknown field"}],
                                  [{"id": "x", "label": "Gate"}, {"id": "x", "label": "Again"}]])
def test_manual_gate_contract_is_validated(raw):
    with pytest.raises(ConfigError):
        manual_gates({"manual_gates": raw})


def test_no_author_gates_cannot_mean_authorization(stub_quarto, wongo_project):
    render_project(wongo_project, "submission")
    result = readiness(wongo_project)
    assert result["technical"]["state"] == "passed"
    assert result["author_decisions"]["state"] == "not-configured"
    assert result["submission_approved"] is False


def test_machine_pass_with_pending_human_gate_is_not_approval(stub_quarto, wongo_project):
    configured(wongo_project)
    render_project(wongo_project, "submission")
    result = readiness(wongo_project)
    assert result["technical"]["state"] == "passed"
    assert result["author_decisions"]["gates"][0]["state"] == "not-recorded"
    assert result["submission_approved"] is False


def test_authorized_collab_build_is_never_submission_approval(stub_quarto, wongo_project):
    configured(wongo_project)
    render_project(wongo_project, "collab")
    confirm_gate(wongo_project, "submission", "approved", target="collab", reviewer="Ada",
                 confirmation=confirmation_challenge(wongo_project, "submission", target="collab"))
    result = readiness(wongo_project, "collab")
    assert result["technical"]["state"] == "passed"
    assert result["author_decisions"]["state"] == "approved"
    assert result["submission_approved"] is False


def test_proposal_does_not_approve_and_confirmation_is_attributed(stub_quarto, wongo_project):
    configured(wongo_project)
    render_project(wongo_project, "submission")
    proposal = propose_gate(wongo_project, "submission", rationale="Please review author list")
    assert proposal["record"]["kind"] == "gate-proposal"
    assert gate_status(wongo_project)["gates"][0]["state"] == "proposed"
    assert readiness(wongo_project)["submission_approved"] is False
    result = approve(wongo_project)
    assert result["record"]["result"]["reviewer"] == "Ada"
    assert result["record"]["producer"]["identity_assurance"] == "local-attribution"
    assert gate_status(wongo_project)["gates"][0]["state"] == "approved"
    assert readiness(wongo_project)["submission_approved"] is True
    with pytest.raises(InputError, match="decision"):
        propose_gate(wongo_project, "submission")


def test_confirmation_needs_exact_current_challenge(stub_quarto, wongo_project):
    configured(wongo_project)
    render_project(wongo_project, "submission")
    with pytest.raises(InputError, match="confirm"):
        confirm_gate(wongo_project, "submission", "approved", reviewer="Ada", confirmation="yes")
    challenge = confirmation_challenge(wongo_project, "submission")
    cfg = wongo_project / "_journal.yml"
    cfg.write_text(cfg.read_text(encoding="utf-8") + "\n# changed\n", encoding="utf-8")
    render_project(wongo_project, "submission")
    with pytest.raises(InputError, match="confirm"):
        confirm_gate(wongo_project, "submission", "approved", reviewer="Ada", confirmation=challenge)


@pytest.mark.parametrize("change", ["source", "output", "gate-definition"])
def test_approval_for_changed_subject_or_policy_stays_visibly_stale(
        stub_quarto, wongo_project, change):
    configured(wongo_project)
    render_project(wongo_project, "submission")
    approve(wongo_project)
    if change == "source":
        path = wongo_project / "index.qmd"
        path.write_text(path.read_text(encoding="utf-8") + "\nChanged text.\n", encoding="utf-8")
        render_project(wongo_project, "submission")
    elif change == "output":
        path = wongo_project / "output/main-submission.docx"
        path.write_bytes(path.read_bytes() + b" ")
    else:
        configure(wongo_project, manual_gates=[{"id": "submission", "label": "A different decision"}])
        render_project(wongo_project, "submission")
    result = gate_status(wongo_project)
    assert result["gates"][0]["state"] == "stale"
    assert result["gates"][0]["approval"]["state"] == "stale"


def test_corrupt_approval_receipt_is_invalid_not_absent(stub_quarto, wongo_project):
    configured(wongo_project)
    render_project(wongo_project, "submission")
    path = evidence_dir(wongo_project) / "approval/bad.json"
    path.parent.mkdir(parents=True)
    path.write_text("{}", encoding="utf-8")
    assert gate_status(wongo_project)["state"] == "invalid"
    assert readiness(wongo_project)["submission_approved"] is False


def test_required_audit_and_visual_evidence_are_independent(stub_quarto, wongo_project):
    configured(wongo_project)
    configure(wongo_project, audits=[{"id": "values", "script": "audit.py", "required": True}],
              visual_review_required=True)
    (wongo_project / "audit.py").write_text("# declared audit\n", encoding="utf-8")
    render_project(wongo_project, "submission")
    approve(wongo_project)
    result = readiness(wongo_project)
    assert result["author_decisions"]["state"] == "approved"
    assert result["audit"]["state"] == "not-recorded"
    assert result["visual"]["state"] == "not-recorded"
    assert result["submission_approved"] is False

    current = snapshot(wongo_project)
    from wongo.engine.inputs import audit_specs

    spec = audit_specs(wongo_project, yaml.safe_load((wongo_project / "_journal.yml").read_text()))[0]
    record = make_record(current, "audit", audit_producer(wongo_project, spec),
                         {"audit_id": "values", "ok": False,
                          "assertions": [{"id": "paragraph", "ok": False, "detail": "Mismatch",
                                          "source": "source", "artifact": "artifact", "rendered_context": "paragraph"}]},
                         {"checked": ["paragraph"], "untested": ["table"]})
    save_record(wongo_project, record)
    result = readiness(wongo_project)
    assert result["audit"]["state"] == "failed"
    assert result["audit"]["checks"][0]["coverage"]["untested"] == ["table"]


def test_gate_evidence_references_must_be_current_and_known(stub_quarto, wongo_project):
    configured(wongo_project)
    render_project(wongo_project, "submission")
    with pytest.raises(InputError, match="evidence"):
        propose_gate(wongo_project, "submission", evidence_ids=["missing-record"])


@pytest.mark.parametrize("damage", ["empty-assertions", "summary-mismatch", "wrong-definition",
                                  "wrong-script", "no-execution", "invented-input"])
def test_forged_audit_summary_does_not_satisfy_required_evidence(stub_quarto, wongo_project, damage):
    from wongo.engine.inputs import audit_specs

    configured(wongo_project)
    configure(wongo_project, audits=[{"id": "values", "script": "audit.py", "required": True}])
    (wongo_project / "audit.py").write_text("# audit\n", encoding="utf-8")
    render_project(wongo_project, "submission")
    approve(wongo_project)
    spec = audit_specs(wongo_project, yaml.safe_load((wongo_project / "_journal.yml").read_text()))[0]
    result = {"audit_id": "values", "ok": True,
              "assertions": [{"id": "paragraph", "ok": True, "detail": "Checked paragraph",
                              "source": "source", "artifact": "artifact", "rendered_context": "paragraph"}]}
    producer = audit_producer(wongo_project, spec)
    if damage == "empty-assertions":
        result["assertions"] = []
    elif damage == "summary-mismatch":
        result["assertions"][0]["ok"] = False
    elif damage == "wrong-definition":
        producer["definition"] = "wrong"
    elif damage == "wrong-script":
        producer["script"]["sha256"] = "0" * 64
    elif damage == "no-execution":
        producer.pop("execution")
    else:
        producer["inputs"] = {"invented.txt": "0" * 64}
    save_record(wongo_project, make_record(snapshot(wongo_project), "audit", producer, result,
                                         {"checked": ["paragraph"], "untested": []}))
    state = readiness(wongo_project)
    assert state["audit"]["state"] == "invalid"
    assert state["audit"]["required_passed"] is False
    assert state["submission_approved"] is False


def audit_producer(project, spec):
    return {"id": spec["id"], "definition": digest(spec),
            "script": {"path": spec["script"], "sha256": hash_file(project / spec["script"])},
            "inputs": {}, "python": sys.version,
            "execution": {"executable": Path(sys.executable).name, "sha256": hash_file(sys.executable)}}


def test_status_dimensions_are_read_only_and_demo_rows_are_identifiable(
        stub_quarto, wongo_project, monkeypatch):
    from wongo.status import format_status, project_status

    configured(wongo_project)
    configure(wongo_project, demonstration=True)
    for target in ("collab", "submission"):
        render_project(wongo_project, target)
    decisions = wongo_project / "decisions"
    decisions.mkdir()
    (decisions / "merge-demo.md").write_text(
        "# Merge worksheet\n\n## 1. insertion — Demo\n- location: index.qmd:10\n"
        "- old: —\n- new: example\n- context: Body text.\n- disposition: PENDING\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("subprocess.run", lambda *a, **kw: pytest.fail("status executed a process"))
    # Existing install identity uses git; isolate that observation, not any evidence producer.
    monkeypatch.setattr("wongo.engine.install_identity", lambda: {"state": "dirty"})
    state = project_status(wongo_project)
    assert state.technical["state"] == "passed"
    assert state.author_decisions["state"] == "not-recorded"
    assert state.demonstration is True
    assert state.worksheet_context == "demonstration"
    assert "demonstration" in "\n".join(format_status(state)).lower()
    assert "submission approved" not in "\n".join(format_status(state)).lower()


def test_gate_review_refuses_an_agent_terminal(cli, stub_quarto, wongo_project, monkeypatch):
    configured(wongo_project)
    render_project(wongo_project, "submission")
    monkeypatch.setattr("wongo.gates_cli.is_interactive", lambda: False)
    code, stdout, _ = cli("gates", "review", "submission", "--project", str(wongo_project), "--json")
    result = json.loads(stdout)
    assert code == 1
    assert result["error"]["kind"] == "input"
    assert "person at a terminal" in result["error"]["message"]
    assert load_approvals(wongo_project) == []


def load_approvals(project):
    from wongo.evidence import load_records

    return load_records(project, "approval")


def test_human_gate_cli_confirmation_retains_one_json_object(
        cli, stub_quarto, wongo_project, monkeypatch):
    configured(wongo_project)
    render_project(wongo_project, "submission")
    answers = iter(["1", confirmation_challenge(wongo_project, "submission"), "Author list checked"])
    monkeypatch.setattr("wongo.gates_cli.is_interactive", lambda: True)
    monkeypatch.setattr("builtins.input", lambda *args: next(answers))
    code, stdout, stderr = cli("gates", "review", "submission", "--reviewer", "Ada",
                               "--project", str(wongo_project), "--json")
    result = json.loads(stdout)
    assert code == 0 and result["ok"] is True
    assert result["author_decisions"]["state"] == "approved"
    assert "CONFIRM approved submission" in stderr
    assert len(load_approvals(wongo_project)) == 1


def test_a_record_without_declared_human_confirmation_is_not_an_approval(stub_quarto, wongo_project):
    configured(wongo_project)
    render_project(wongo_project, "submission")
    definition = manual_gates(yaml.safe_load((wongo_project / "_journal.yml").read_text()))[0]
    record = make_record(snapshot(wongo_project), "approval", {"name": "automated checker"},
                         {"gate_id": "submission", "definition_hash": digest(definition),
                          "decision": "approved", "reviewer": "Agent"}, {})
    save_record(wongo_project, record)
    assert gate_status(wongo_project)["state"] == "invalid"
    assert readiness(wongo_project)["submission_approved"] is False


@pytest.mark.parametrize("damage", ["missing-id", "decision-list", "bad-references"])
def test_malformed_gate_result_is_visible_and_cannot_be_proposed_over(stub_quarto, wongo_project, damage):
    configured(wongo_project)
    render_project(wongo_project, "submission")
    definition = manual_gates(yaml.safe_load((wongo_project / "_journal.yml").read_text()))[0]
    result = {"gate_id": "submission", "definition_hash": digest(definition),
              "decision": "approved", "reviewer": "Ada", "evidence_ids": []}
    if damage == "missing-id":
        result.pop("gate_id")
    elif damage == "decision-list":
        result["decision"] = []
    else:
        result["evidence_ids"] = "not-a-list"
    save_record(wongo_project, make_record(snapshot(wongo_project), "approval",
                {"method": "human-confirmed", "identity_assurance": "local-attribution"}, result, {}))
    assert gate_status(wongo_project)["state"] == "invalid"
    assert readiness(wongo_project)["submission_approved"] is False
    with pytest.raises(InputError):
        propose_gate(wongo_project, "submission")


def test_native_word_attestation_is_separate_and_incomplete_documents_stay_partial(
        stub_quarto, wongo_project):
    configure(wongo_project, visual_review_required=True)
    render_project(wongo_project, "submission")
    current = snapshot(wongo_project)
    outputs = current["subject"]["outputs"]
    documents = {name: {"docx_sha256": value, "page_count": 1} for name, value in outputs.items()}
    result = {"ok": True, "complete": True, "representation": "native-word-inspection",
              "native_word_attested": True, "verification_method": "local-human-attestation",
              "reviewer": "Ada", "word_version": "Word 2024", "documents": documents,
              "checked_pages": [{"document": name, "page": 1} for name in outputs]}
    record = make_record(current, "visual-review", {"name": "wongo.qa.review"}, result,
                         {"checked": result["checked_pages"], "untested": []})
    save_record(wongo_project, record)
    visual = readiness(wongo_project)["visual"]
    assert visual["state"] == "passed"
    assert visual["native_word_attested"] is True
    assert visual["native_word_verified"] is False
    result = {**result, "documents": {name: info for name, info in documents.items() if name.startswith("main")},
              "checked_pages": [{"document": next(name for name in outputs if name.startswith("main")), "page": 1}]}
    save_record(wongo_project, make_record(current, "visual-review", {"name": "wongo.qa.review"}, result, {}))
    assert readiness(wongo_project)["visual"]["state"] == "partial"
    save_record(wongo_project, make_record(current, "inspection", {"name": "OOXML inventory"},
                                         {"ok": False}, {"checked": [], "untested": []}))
    visual = readiness(wongo_project)["visual"]
    assert visual["inspection"]["state"] == "failed"
    assert visual["state"] == "failed"
    assert visual["required_passed"] is False


def test_regenerated_preview_does_not_reuse_old_visual_review_implicitly(stub_quarto, wongo_project):
    configure(wongo_project, visual_review_required=True)
    render_project(wongo_project, "submission")
    current = snapshot(wongo_project)
    documents, artifacts = preview_documents(wongo_project, current)
    preview = make_record(current, "preview", {"renderer": "test"},
                          {"ok": True, "documents": documents, "settings": {"dpi": 100}}, {},
                          artifacts=artifacts)
    save_record(wongo_project, preview)
    checked = [{"document": name, "page": 1, "sha256": info["pages"][0]["sha256"]}
               for name, info in documents.items()]
    review = make_record(current, "visual-review", {"name": "human page inspection"},
                         {"ok": True, "complete": True, "preview_record_id": preview["record_id"],
                          "reviewer": "Ada", "checked_pages": checked},
                         {"checked": checked, "untested": []}, artifacts=artifacts)
    save_record(wongo_project, review)
    assert readiness(wongo_project)["visual"]["state"] == "passed"
    new_preview = make_record(current, "preview", {"renderer": "test"},
                              {"ok": True, "documents": documents, "settings": {"dpi": 200}}, {},
                              artifacts=artifacts)
    save_record(wongo_project, new_preview)
    visual = readiness(wongo_project)["visual"]
    assert visual["state"] == "stale"
    assert visual["required_passed"] is False


def test_status_requests_human_inspection_after_a_current_preview(stub_quarto, wongo_project):
    from wongo.status import project_status

    configure(wongo_project, visual_review_required=True)
    for target in ("collab", "submission"):
        render_project(wongo_project, target)
    current = snapshot(wongo_project)
    documents, artifacts = preview_documents(wongo_project, current)
    preview = make_record(current, "preview", {"renderer": "test"},
                          {"ok": True, "documents": documents}, {}, artifacts=artifacts)
    save_record(wongo_project, preview)
    state = project_status(wongo_project)
    assert state.next_command == "wongo qa review --help"
    assert "person must inspect" in state.next_reason


def preview_documents(project, current):
    documents, artifacts = {}, []
    for name, value in current["subject"]["outputs"].items():
        page = project / "output" / f"{name}-page.png"
        page.write_bytes(name.encode())
        artifact = {"path": page.relative_to(project).as_posix(), "sha256": hash_file(page)}
        artifacts.append(artifact)
        documents[name] = {"docx_sha256": value, "page_count": 1, "pages": [{"number": 1, **artifact}]}
    return documents, artifacts


@pytest.mark.parametrize("damage", ["omit-si", "wrong-docx", "no-count", "unbound-page"])
def test_malformed_preview_inventory_cannot_satisfy_visual_requirement(stub_quarto, wongo_project, damage):
    configure(wongo_project, visual_review_required=True)
    render_project(wongo_project, "submission")
    current = snapshot(wongo_project)
    documents, artifacts = preview_documents(wongo_project, current)
    name = next(iter(documents))
    if damage == "omit-si":
        documents.pop(next(item for item in documents if item.startswith("si")))
    elif damage == "wrong-docx":
        documents[name]["docx_sha256"] = "wrong"
    elif damage == "no-count":
        documents[name].pop("page_count")
    else:
        artifacts = []
    preview = make_record(current, "preview", {"renderer": "test"},
                          {"ok": True, "documents": documents}, {}, artifacts=artifacts)
    save_record(wongo_project, preview)
    checked = [{"document": item, "page": 1, "sha256": info["pages"][0]["sha256"]}
               for item, info in documents.items()]
    review = make_record(current, "visual-review", {"name": "human inspection"},
                         {"ok": True, "complete": True, "preview_record_id": preview["record_id"],
                          "reviewer": "Ada", "checked_pages": checked}, {})
    save_record(wongo_project, review)
    result = readiness(wongo_project)
    assert result["visual"]["state"] == "invalid"
    assert result["visual"]["required_passed"] is False
    assert result["submission_approved"] is False


def test_open_coauthor_rows_block_core_and_status_consistently(stub_quarto, wongo_project):
    from wongo.status import project_status

    configured(wongo_project)
    for target in ("collab", "submission"):
        render_project(wongo_project, target)
    approve(wongo_project)
    assert readiness(wongo_project)["submission_approved"] is True
    folder = wongo_project / "decisions"
    folder.mkdir()
    (folder / "merge-review.md").write_text(
        "# Merge worksheet\n\n## 1. insertion — Ada\n- location: index.qmd:10\n"
        "- old: —\n- new: text\n- context: Body.\n- disposition: PENDING\n", encoding="utf-8")
    core = readiness(wongo_project)
    card = project_status(wongo_project)
    assert core["author_decisions"]["state"] == "approved"
    assert core["author_decisions"]["coauthor_rows"]["open"] == 1
    assert core["submission_approved"] is card.submission_approved is False
    assert card.next_command.startswith("wongo review ")
