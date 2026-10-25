"""Explicit audits bind contextual results to scratch snapshots and exact live builds."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from wongo.audit import run_audits, validate_audit_record
from wongo.engine import render_project, source_fingerprint
from wongo.engine.checks import run_checks
from wongo.engine.inputs import audit_specs
from wongo.errors import ConfigError, InputError
from wongo.evidence import load_records, snapshot, verify_record

_RESULT = {
    "assertions": [{"id": "value", "ok": True, "detail": "Explicit fixture check.",
                    "source": "index.qmd:8", "artifact": "data/facts.json#/value",
                    "rendered_context": {"paragraph": "Fixture body"}}],
    "coverage": {"checked": ["value"], "untested": ["all other scientific claims"]},
}


def _configure(project, script_body=None, *, required=False, inputs=None, timeout=120):
    config = project / "_journal.yml"
    cfg = yaml.safe_load(config.read_text(encoding="utf-8"))
    cfg["audits"] = [{"id": "values", "script": "scripts/audit.py", "required": required,
                      "inputs": inputs or [], "timeout": timeout}]
    config.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    script = project / "scripts" / "audit.py"
    script.parent.mkdir(exist_ok=True)
    script.write_text(script_body or (
        "import json, os\nfrom pathlib import Path\n"
        f"result = {repr(_RESULT)}\n"
        "Path(os.environ['WONGO_AUDIT_RESULT']).write_text(json.dumps(result))\n"
    ), encoding="utf-8")
    return script


def _deliverables(project):
    return {p.name: p.read_bytes() for p in (project / "output").glob("*") if p.is_file()}


def test_explicit_audit_creates_fresh_scoped_receipt_without_changing_delivery(
        stub_quarto, wongo_project):
    _configure(wongo_project)
    render_project(wongo_project, "submission")
    before = _deliverables(wongo_project)
    result = run_audits(wongo_project)
    assert result["ok"]
    assert _deliverables(wongo_project) == before
    receipt = result["records"][0]
    assert receipt["result"]["audit_id"] == "values"
    assert receipt["coverage"]["untested"] == ["all other scientific claims"]
    assert verify_record(wongo_project, receipt)["state"] == "fresh"
    assert Path(result["paths"][0]).is_file()


@pytest.mark.parametrize("field", ["id", "script", "inputs", "execution", "python", "definition", "ok"])
def test_receipt_validator_rejects_incomplete_or_conflicting_producer(
        stub_quarto, wongo_project, field):
    import copy

    _configure(wongo_project)
    render_project(wongo_project, "submission")
    receipt = run_audits(wongo_project)["records"][0]
    cfg = yaml.safe_load((wongo_project / "_journal.yml").read_text(encoding="utf-8"))
    spec = audit_specs(wongo_project, cfg)[0]
    validate_audit_record(receipt, spec, wongo_project)
    damaged = copy.deepcopy(receipt)
    if field == "ok":
        damaged["result"]["ok"] = False
    else:
        damaged["producer"].pop(field)
    with pytest.raises(InputError):
        validate_audit_record(damaged, spec, wongo_project)


def test_audits_use_only_explicitly_allowed_scratch_inputs(stub_quarto, wongo_project):
    data = wongo_project / "data"
    data.mkdir()
    (data / "facts.json").write_text('{"value": 12.4}', encoding="utf-8")
    (data / "private.json").write_text("PRIVATE", encoding="utf-8")
    body = (
        "import json, os\nfrom pathlib import Path\n"
        "root = Path(os.environ['WONGO_AUDIT_PROJECT'])\n"
        "assert (root/'data/facts.json').is_file()\n"
        "assert not (root/'data/private.json').exists()\n"
        "assert all(Path(p).is_file() for p in os.environ['WONGO_AUDIT_OUTPUTS'].split(os.pathsep))\n"
        f"result = {repr(_RESULT)}\n"
        "Path(os.environ['WONGO_AUDIT_RESULT']).write_text(json.dumps(result))\n"
    )
    script = _configure(wongo_project, body, inputs=["data/facts.json"])
    sources = source_fingerprint(wongo_project)
    assert "data/facts.json" in sources and "scripts/audit.py" in sources
    assert "data/private.json" not in sources
    render_project(wongo_project, "submission")
    result = run_audits(wongo_project)
    assert result["ok"]
    assert script.read_text(encoding="utf-8") == body


def test_assertion_failure_is_recorded_even_when_script_exits_zero(stub_quarto, wongo_project):
    result = {**_RESULT, "ok": True, "assertions": [{**_RESULT["assertions"][0], "ok": False}]}
    body = ("import json,os\nfrom pathlib import Path\n"
            f"Path(os.environ['WONGO_AUDIT_RESULT']).write_text(json.dumps({repr(result)}))\n")
    _configure(wongo_project, body)
    render_project(wongo_project, "submission")
    response = run_audits(wongo_project)
    assert not response["ok"]
    assert not response["records"][0]["result"]["ok"]


@pytest.mark.parametrize("mutated", ["output", "input"])
def test_a_snapshot_mutation_refuses_receipt_and_preserves_deliverables(
        stub_quarto, wongo_project, mutated):
    data = wongo_project / "data"
    data.mkdir()
    (data / "facts.json").write_text("{}", encoding="utf-8")
    body = ("import json,os\nfrom pathlib import Path\n"
            + ("target=Path(os.environ['WONGO_AUDIT_OUTPUTS'].split(os.pathsep)[0])\n"
               if mutated == "output" else
               "target=Path(os.environ['WONGO_AUDIT_PROJECT'])/'data/facts.json'\n")
            + "target.write_text('changed')\n"
            + f"Path(os.environ['WONGO_AUDIT_RESULT']).write_text(json.dumps({repr(_RESULT)}))\n")
    _configure(wongo_project, body, inputs=["data/facts.json"])
    render_project(wongo_project, "submission")
    before = _deliverables(wongo_project)
    with pytest.raises(InputError, match="changed.*snapshot|snapshot.*changed"):
        run_audits(wongo_project)
    assert _deliverables(wongo_project) == before
    assert load_records(wongo_project, "audit") == []


def test_changed_checker_or_data_stales_the_record(stub_quarto, wongo_project):
    script = _configure(wongo_project)
    render_project(wongo_project, "submission")
    receipt = run_audits(wongo_project)["records"][0]
    script.write_text(script.read_text(encoding="utf-8") + "# changed\n", encoding="utf-8")
    assert verify_record(wongo_project, receipt)["state"] == "stale"
    with pytest.raises(InputError, match="stale"):
        run_audits(wongo_project)


@pytest.mark.parametrize("body,match", [
    ("raise RuntimeError('broken checker')\n", "failed"),
    ("import os\nfrom pathlib import Path\nPath(os.environ['WONGO_AUDIT_RESULT']).write_text('{bad')\n", "JSON"),
    ("import os\nfrom pathlib import Path\nPath(os.environ['WONGO_AUDIT_RESULT']).write_text('{}')\n", "assertions"),
])
def test_execution_and_protocol_failures_do_not_create_evidence(
        stub_quarto, wongo_project, body, match):
    _configure(wongo_project, body)
    render_project(wongo_project, "submission")
    before = _deliverables(wongo_project)
    with pytest.raises(InputError, match=match):
        run_audits(wongo_project)
    assert _deliverables(wongo_project) == before
    assert load_records(wongo_project, "audit") == []


def test_audit_configuration_is_validated_without_running_scripts(wongo_project):
    config = wongo_project / "_journal.yml"
    cfg = yaml.safe_load(config.read_text(encoding="utf-8"))
    cfg["audits"] = [{"id": "x", "script": "../escape.py"}]
    config.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    with pytest.raises(ConfigError, match="escapes"):
        source_fingerprint(wongo_project)


@pytest.mark.parametrize("field,value", [
    ("required", "yes"), ("timeout", True), ("timeout", 0),
    ("inputs", False), ("inputs", "facts.json"), ("id", "bad id"),
])
def test_malformed_audit_configuration_fails_before_execution(wongo_project, field, value):
    _configure(wongo_project)
    path = wongo_project / "_journal.yml"
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    cfg["audits"][0][field] = value
    path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    with pytest.raises(ConfigError):
        source_fingerprint(wongo_project)


def test_check_does_not_execute_declared_audits(stub_quarto, wongo_project):
    script = _configure(wongo_project, "raise RuntimeError('must never execute in check')\n")
    before = script.read_bytes()
    assert run_checks(wongo_project)
    assert script.read_bytes() == before
    assert not (wongo_project / "output" / ".wongo-evidence").exists()


def test_an_audit_is_bound_to_the_selected_target(stub_quarto, wongo_project):
    _configure(wongo_project)
    render_project(wongo_project, "collab")
    receipt = run_audits(wongo_project, target="collab")["records"][0]
    assert receipt["subject"]["target"] == "collab"
    assert receipt["subject_id"] == snapshot(wongo_project, "collab")["id"]


def test_missing_or_unknown_audit_never_becomes_a_pass(stub_quarto, wongo_project):
    render_project(wongo_project, "submission")
    with pytest.raises(ConfigError, match="Declare"):
        run_audits(wongo_project)
    _configure(wongo_project)
    render_project(wongo_project, "submission")
    with pytest.raises(ConfigError, match="unknown|Unknown"):
        run_audits(wongo_project, name="unknown")


def test_timeout_preserves_delivery_and_accepts_no_receipt(stub_quarto, wongo_project):
    _configure(wongo_project, "import time\ntime.sleep(5)\n", timeout=1)
    render_project(wongo_project, "submission")
    before = _deliverables(wongo_project)
    with pytest.raises(InputError, match="timed out"):
        run_audits(wongo_project)
    assert _deliverables(wongo_project) == before
    assert load_records(wongo_project, "audit") == []


def test_audit_stdout_is_diagnostic_only(stub_quarto, wongo_project, capfd):
    body = ("import json,os\nfrom pathlib import Path\nprint('AUDIT NOISE')\n"
            f"Path(os.environ['WONGO_AUDIT_RESULT']).write_text(json.dumps({repr(_RESULT)}))\n")
    _configure(wongo_project, body)
    render_project(wongo_project, "submission")
    capfd.readouterr()
    events = []
    assert run_audits(wongo_project, on_event=lambda kind, payload: events.append((kind, payload)))["ok"]
    output = capfd.readouterr()
    assert output.out == output.err == ""
    assert "AUDIT NOISE" in events[0][1]["text"]


def test_external_inputs_need_explicit_audit_permission_and_stay_temporary(
        stub_quarto, wongo_project, tmp_path):
    external = tmp_path / "expected.json"
    external.write_text('{"value": 12.4}', encoding="utf-8")
    body = ("import json,os\nfrom pathlib import Path\n"
            "inputs=json.loads(os.environ['WONGO_AUDIT_INPUTS'])\n"
            f"copied=Path(inputs[{str(external)!r}])\n"
            f"assert copied != Path({str(external)!r})\n"
            "assert json.loads(copied.read_text())['value']==12.4\n"
            f"Path(os.environ['WONGO_AUDIT_RESULT']).write_text(json.dumps({repr(_RESULT)}))\n")
    _configure(wongo_project, body, inputs=[{"path": str(external), "external": True}])
    render_project(wongo_project, "submission")
    assert run_audits(wongo_project)["ok"]
    assert not (wongo_project / "expected.json").exists()
    assert external.read_text(encoding="utf-8") == '{"value": 12.4}'


def test_live_input_mutation_is_detected_without_reverting_someone_elses_save(
        stub_quarto, wongo_project):
    data = wongo_project / "facts.json"
    data.write_text("{}", encoding="utf-8")
    body = ("import json,os\nfrom pathlib import Path\n"
            f"Path({str(data)!r}).write_text('changed by the fixture')\n"
            f"Path(os.environ['WONGO_AUDIT_RESULT']).write_text(json.dumps({repr(_RESULT)}))\n")
    _configure(wongo_project, body, inputs=["facts.json"])
    render_project(wongo_project, "submission")
    before = _deliverables(wongo_project)
    with pytest.raises(InputError, match="Live build inputs"):
        run_audits(wongo_project)
    assert _deliverables(wongo_project) == before
    assert data.read_text(encoding="utf-8") == "changed by the fixture"
    assert load_records(wongo_project, "audit") == []


def test_corrupted_snapshot_copy_is_rejected_before_running_the_script(
        stub_quarto, wongo_project, monkeypatch):
    import wongo.audit as audit

    _configure(wongo_project)
    render_project(wongo_project, "submission")
    original = audit._copy_file

    def copy(source, destination):
        original(source, destination)
        if destination.suffix == ".docx":
            destination.write_bytes(b"wrong copy")

    monkeypatch.setattr(audit, "_copy_file", copy)
    with pytest.raises(InputError, match="while copying"):
        run_audits(wongo_project)
    assert load_records(wongo_project, "audit") == []


@pytest.mark.parametrize("update", [
    {"assertions": []},
    {"assertions": [{**_RESULT["assertions"][0], "ok": "true"}]},
    {"coverage": {"checked": ["invented"], "untested": []}},
    {"coverage": {"checked": ["value"]}},
    {"coverage": {"checked": ["value"], "untested": ["value"]}},
])
def test_audit_protocol_does_not_accept_incomplete_or_invented_coverage(
        stub_quarto, wongo_project, update):
    report = {**_RESULT, **update}
    body = ("import json,os\nfrom pathlib import Path\n"
            f"Path(os.environ['WONGO_AUDIT_RESULT']).write_text(json.dumps({repr(report)}))\n")
    _configure(wongo_project, body)
    render_project(wongo_project, "submission")
    with pytest.raises(InputError):
        run_audits(wongo_project)
    assert load_records(wongo_project, "audit") == []
