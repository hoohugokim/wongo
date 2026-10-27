"""Explicit, scoped audit execution against disposable copies of sealed builds."""
from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from wongo.engine.inputs import EMPTY_DIRECTORY, _expand, _resolve_spec, audit_specs
from wongo.errors import ConfigError, InputError, ToolchainError
from wongo.evidence import digest, hash_file, make_record, safe_path, save_record, snapshot
from wongo.profiles import load_journal_config
from wongo.textio import read_text


def _emit(on_event, identifier, output):
    if output and on_event is not None:
        on_event("diagnostic", {"source": f"audit:{identifier}", "text": output})


def _copy_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copy2(source, destination)
    except OSError as exc:
        raise InputError(f"Could not snapshot audit input {source.name}: {exc}. Restore or unlock it.") from exc


def _content(path: Path) -> str:
    if path.is_dir():
        return digest({p.relative_to(path).as_posix(): hash_file(p)
                       for p in sorted(path.rglob("*")) if p.is_file()})
    return hash_file(path)


def _scratch_inputs(project: Path, root: Path, spec: dict) -> tuple[dict, dict, dict]:
    paths, hashes, copied = {}, {}, {}
    for item in spec["inputs"]:
        key, source, external = _resolve_spec(project, item)
        if not source.exists():
            raise InputError(f"Audit {spec['id']} input missing: {key}. Restore it before auditing.")
        if external:
            destination = root / "external" / digest(key)[:16] / source.name
        else:
            destination = safe_path(root, key, must_exist=False)
        if source.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
        paths[key] = str(destination)
        for entry in _expand(project, item):
            if entry.path is None:
                raise InputError(f"Audit {spec['id']} input missing: {entry.key}. Restore it before auditing.")
            target = destination / entry.path.relative_to(source) if source.is_dir() else destination
            paths[entry.key] = str(target)
            if entry.path.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                hashes[entry.key] = EMPTY_DIRECTORY
            else:
                _copy_file(entry.path, target)
                hashes[entry.key] = hash_file(target)
            copied[target] = _content(target)
        copied[destination] = _content(destination)
    return paths, hashes, copied


def _command(script: Path) -> list[str]:
    if script.suffix.lower() == ".py":
        return [sys.executable, str(script)]
    if script.suffix.lower() == ".r":
        from wongo.toolchain import find_rscript

        tool = find_rscript()
        if tool is None:
            raise ToolchainError("Rscript was not found. Run wongo doctor and install R before this audit.")
        return [tool.path, str(script)]
    return [str(script)]


def _validate_result(raw: object, identifier: str) -> tuple[list[dict], dict]:
    if not isinstance(raw, dict) or not isinstance(raw.get("assertions"), list) or not raw["assertions"]:
        raise InputError(f"Audit {identifier} must report a nonempty assertions list; no audit was certified.")
    digest(raw)
    ids = []
    for assertion in raw["assertions"]:
        if (not isinstance(assertion, dict) or not isinstance(assertion.get("id"), str)
                or not assertion["id"].strip() or type(assertion.get("ok")) is not bool
                or not isinstance(assertion.get("detail"), str) or not assertion["detail"].strip()):
            raise InputError(f"Audit {identifier} assertions need id, boolean ok, and nonempty detail.")
        for field in ("source", "artifact", "rendered_context"):
            if field not in assertion:
                raise InputError(f"Audit {identifier} assertion {assertion['id']} needs {field} evidence.")
        ids.append(assertion["id"])
    coverage = raw.get("coverage")
    if (not isinstance(coverage, dict)
            or any(not isinstance(coverage.get(key), list)
                   or any(not isinstance(value, str) or not value.strip() for value in coverage[key])
                   for key in ("checked", "untested"))):
        raise InputError(f"Audit {identifier} coverage needs checked and untested lists of identifiers.")
    if (len(ids) != len(set(ids)) or set(coverage["checked"]) != set(ids)
            or len(coverage["checked"]) != len(set(coverage["checked"]))):
        raise InputError(f"Audit {identifier} checked coverage must name each distinct reported assertion exactly.")
    if set(coverage["checked"]) & set(coverage["untested"]):
        raise InputError(f"Audit {identifier} cannot label the same assertion checked and untested.")
    coverage = {**coverage, "scope": "Only the declared assertions were checked; scientific validity is project-owned."}
    return raw["assertions"], coverage


def validate_audit_record(record: dict, spec: dict, project: Path) -> None:
    """Validate kind-specific receipt bindings without running the audit script.

    Generic envelope/subject freshness remains the caller's responsibility.
    These consistency checks do not authenticate locally editable receipts.
    """
    identifier = spec["id"]
    producer, result = record.get("producer"), record.get("result")
    sources = record.get("subject", {}).get("sources")
    if not isinstance(producer, dict) or not isinstance(result, dict) or not isinstance(sources, dict):
        raise InputError(f"Audit {identifier} receipt is missing its producer, result, or source identities.")
    assertions, _ = _validate_result({**result, "coverage": record.get("coverage")}, identifier)
    if (record.get("kind") != "audit" or producer.get("id") != identifier
            or producer.get("definition") != digest(spec)
            or result.get("audit_id") != identifier or type(result.get("ok")) is not bool
            or result["ok"] != all(item["ok"] for item in assertions)):
        raise InputError(f"Audit {identifier} receipt disagrees with its definition or assertion outcomes.")
    root = Path(project).resolve()
    script_key = safe_path(root, spec["script"]).relative_to(root).as_posix()
    script = producer.get("script")
    sha = sources.get(script_key)
    if (not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{64}", sha)
            or not isinstance(script, dict) or script.get("path") != spec["script"]
            or script.get("sha256") != sha):
        raise InputError(f"Audit {identifier} receipt script identity does not match its bound sources.")
    expected = {}
    for item in spec["inputs"]:
        for entry in _expand(root, item):
            value = sources.get(entry.key)
            if (entry.path is None or not isinstance(value, str)
                    or (value != EMPTY_DIRECTORY and not re.fullmatch(r"[0-9a-f]{64}", value))):
                raise InputError(f"Audit {identifier} receipt input {entry.key} has no bound file identity.")
            expected[entry.key] = value
    if producer.get("inputs") != expected:
        raise InputError(f"Audit {identifier} receipt input identities do not match its explicit inputs.")
    execution = producer.get("execution")
    if (not isinstance(producer.get("python"), str) or not producer["python"].strip()
            or not isinstance(execution, dict) or not isinstance(execution.get("executable"), str)
            or not execution["executable"].strip() or not isinstance(execution.get("sha256"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", execution["sha256"])):
        raise InputError(f"Audit {identifier} receipt is missing its interpreter identity.")


def _unchanged(current: dict, project: Path, target: str) -> None:
    try:
        after = snapshot(project, target)
    except InputError as exc:
        raise InputError("Live build inputs or outputs changed during the audit. No receipt was accepted; "
                         "preserve edits, render again, and rerun the audit.") from exc
    if after["id"] != current["id"]:
        raise InputError("Live build inputs, engine, or outputs changed during the audit. "
                         "No receipt was accepted; finish changes and rerun it.")


def _execute(project: Path, spec: dict, current: dict, target: str, on_event=None) -> dict:
    with tempfile.TemporaryDirectory(prefix="wongo-audit-") as directory:
        scratch = Path(directory)
        root = scratch / "project"
        root.mkdir()
        script = safe_path(project, spec["script"])
        copied_script = safe_path(root, spec["script"], must_exist=False)
        _copy_file(script, copied_script)
        input_paths, input_hashes, copied = _scratch_inputs(project, root, spec)
        copied[copied_script] = hash_file(copied_script)
        script_key = script.relative_to(project).as_posix()
        source_hashes = current["subject"]["sources"]
        expected_inputs = {script_key: copied[copied_script], **input_hashes}
        if any(source_hashes.get(key) != value for key, value in expected_inputs.items()):
            raise InputError(f"Audit {spec['id']} inputs changed while copying its snapshot. "
                             "Finish saving, render again, and rerun the audit.")
        outputs = []
        for name in current["subject"]["outputs"]:
            source = safe_path(project / "output", name)
            destination = safe_path(root / "output", name, must_exist=False)
            _copy_file(source, destination)
            copied[destination] = hash_file(destination)
            if copied[destination] != current["subject"]["outputs"][name]:
                raise InputError(f"Audit output {name} changed while copying its snapshot. "
                                 "Preserve edits and rerun the audit against current outputs.")
            outputs.append(str(destination))
        _unchanged(current, project, target)
        report = scratch / "result.json"
        env = os.environ.copy()
        for key in ("WONGO_PROJECT", "WONGO_POSTPROCESS_OUTPUTS", "WONGO_POSTPROCESS_TARGET"):
            env.pop(key, None)
        env.update({
            "WONGO_AUDIT_PROJECT": str(root), "WONGO_AUDIT_RESULT": str(report),
            "WONGO_AUDIT_OUTPUTS": os.pathsep.join(outputs),
            "WONGO_AUDIT_INPUTS": json.dumps(input_paths, ensure_ascii=False),
            "WONGO_AUDIT_TARGET": target, "WONGO_AUDIT_ID": spec["id"],
            "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1",
        })
        command = _command(copied_script)
        execution = {"executable": Path(command[0]).name, "sha256": hash_file(command[0])}
        try:
            completed = subprocess.run(
                command, cwd=root, env=env, timeout=spec["timeout"],
                check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace",
            )
        except subprocess.TimeoutExpired as exc:
            output = exc.stdout or ""
            if isinstance(output, bytes):
                output = output.decode("utf-8", errors="replace")
            _emit(on_event, spec["id"], output)
            raise InputError(f"Audit {spec['id']} timed out after {spec['timeout']} seconds. "
                             "Fix its script or explicit timeout and rerun it.") from exc
        except OSError as exc:
            raise InputError(f"Could not run audit {spec['id']}: {exc}. Fix its script/interpreter.") from exc
        _emit(on_event, spec["id"], completed.stdout or "")
        _unchanged(current, project, target)
        for path, expected in copied.items():
            try:
                actual = _content(path)
            except InputError as exc:
                raise InputError(f"Audit {spec['id']} changed its snapshot: {path.name}. "
                                 "Audit scripts must inspect copies without modifying them.") from exc
            if actual != expected:
                raise InputError(f"Audit {spec['id']} changed its snapshot: {path.name}. "
                                 "Audit scripts must inspect copies without modifying them.")
        if completed.returncode != 0:
            raise InputError(f"Audit {spec['id']} failed (exit {completed.returncode}). "
                             "Fix the checker and rerun it; deliverables were not replaced.",
                             audit_id=spec["id"], output=completed.stdout or "")
        try:
            raw = json.loads(read_text(report))
        except (OSError, ValueError) as exc:
            raise InputError(f"Audit {spec['id']} did not write valid result JSON to WONGO_AUDIT_RESULT. "
                             "Fix its report protocol and rerun it.") from exc
        assertions, coverage = _validate_result(raw, spec["id"])
        producer = {
            "id": spec["id"], "script": {"path": spec["script"], "sha256": hash_file(script)},
            "inputs": input_hashes, "definition": digest(spec),
            "python": platform.python_version(), "execution": execution,
        }
        return make_record(current, "audit", producer,
                           {"audit_id": spec["id"], "ok": all(item["ok"] for item in assertions),
                            "assertions": assertions}, coverage)


def run_audits(project: Path, target: str = "submission", name: str | None = None,
               *, on_event=None) -> dict:
    """Run only explicitly configured audits; never called by check/status/render."""
    project = Path(project).resolve()
    specs = audit_specs(project, load_journal_config(project))
    if not specs:
        raise ConfigError("Declare audits in _journal.yml before running wongo audit.")
    if name is not None:
        specs = [item for item in specs if item["id"] == name]
        if not specs:
            raise ConfigError(f"Unknown audit {name!r}. Choose an id declared in _journal.yml audits.")
    current = snapshot(project, target)
    records = [_execute(project, spec, current, target, on_event) for spec in specs]
    _unchanged(current, project, target)
    paths = [save_record(project, record) for record in records]
    return {"ok": all(record["result"]["ok"] for record in records), "target": target,
            "records": records, "paths": [str(path) for path in paths],
            "scope": "Only explicitly declared audit assertions; not complete scientific validation."}
