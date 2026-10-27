"""Exact build identities and evidence records shared by audits, QA and decisions."""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

from wongo import __version__
from wongo.errors import InputError
from wongo.textio import read_text, write_text_atomic

SCHEMA = "wongo-evidence/1"
KINDS = {"audit", "inspection", "preview", "visual-review", "gate-proposal", "approval",
         "review-note", "review-disposition"}


def digest(value) -> str:
    try:
        raw = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise InputError("Evidence must contain finite JSON values. Fix the evidence producer.") from exc
    return hashlib.sha256(raw).hexdigest()


def hash_file(path: Path | str) -> str:
    path = Path(path)
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise InputError(f"Could not read {path}: {exc}. Restore or unlock the file and retry.") from exc


def safe_path(root: Path, raw: str, *, must_exist: bool = True) -> Path:
    root = Path(root).resolve()
    if not isinstance(raw, str) or not raw.strip() or "\x00" in raw:
        raise InputError("Evidence paths must be nonempty relative paths.")
    portable = PurePosixPath(raw.replace("\\", "/"))
    if (not portable.parts or portable.is_absolute() or ".." in portable.parts
            or ":" in portable.parts[0]):
        raise InputError(f"Evidence path must stay inside its project: {raw}")
    target = (root / Path(*portable.parts)).resolve()
    if not target.is_relative_to(root):
        raise InputError(f"Evidence path escapes its project: {raw}")
    if must_exist and not target.is_file():
        raise InputError(f"Evidence file missing: {raw}. Restore the file or rerun its producer.")
    return target


def evidence_dir(project: Path) -> Path:
    return safe_path(Path(project), "output/.wongo-evidence", must_exist=False)


def engine_identity() -> dict:
    root = Path(__file__).resolve().parent
    files = {p.relative_to(root).as_posix(): hash_file(p) for p in sorted(root.rglob("*.py"))}
    return {"version": __version__, "files": files, "sha256": digest(files)}


def snapshot(project: Path, target: str = "submission") -> dict:
    from wongo.engine import install_identity, output_freshness, read_manifest, source_fingerprint

    project = Path(project).resolve()
    if target not in {"collab", "submission"}:
        raise InputError("Evidence target must be collab or submission.")
    freshness = output_freshness(project, target)
    if freshness["state"] != "fresh":
        raise InputError(
            f"The {target} outputs are {freshness['state']}. Preserve coauthor edits, "
            "then render current outputs before creating evidence."
        )
    entry = read_manifest(project)["targets"][target]
    outputs = {}
    for name, expected in entry.get("outputs", {}).items():
        path = safe_path(project / "output", name)
        actual = hash_file(path)
        if actual != expected:
            raise InputError(f"{name} changed while binding evidence. Preserve edits and render again.")
        outputs[name] = actual
    if not outputs:
        raise InputError("The render manifest has no outputs. Render again before creating evidence.")
    assets = {
        key: value.get("sha256") if isinstance(value, dict) else None
        for key, value in (entry.get("identity") or {}).items() if key != "source"
    }
    sources = source_fingerprint(project)
    if sources != entry.get("sources"):
        raise InputError("Sources changed while capturing evidence. Render current outputs and retry.")
    subject = {
        "target": target, "sources": sources, "assets": assets,
        "journal": entry.get("journal"), "ms_type": entry.get("ms_type"),
        "style": entry.get("style"), "engine": engine_identity(),
        "tools": {"quarto": entry.get("quarto"), "wongo": entry.get("wongo")},
        "outputs": outputs, "checks_failed": list(entry.get("checks_failed") or []),
    }
    if (output_freshness(project, target)["state"] != "fresh"
            or read_manifest(project).get("targets", {}).get(target) != entry
            or source_fingerprint(project) != sources
            or engine_identity() != subject["engine"]):
        raise InputError("Build changed while capturing evidence. Render current outputs and retry.")
    return {"id": digest(subject), "subject": subject, "installation": install_identity()}


def make_record(current: dict, kind: str, producer: dict, result: dict, coverage: dict,
                *, artifacts: list[dict] | None = None) -> dict:
    if kind not in KINDS:
        raise InputError(f"Unknown evidence kind {kind!r}.")
    if current.get("id") != digest(current.get("subject")):
        raise InputError("The evidence snapshot identity is invalid. Capture a new snapshot.")
    body = {
        "schema": SCHEMA, "kind": kind, "subject_id": current["id"],
        "subject": current["subject"], "installation": current.get("installation", {}),
        "producer": producer, "result": result, "coverage": coverage,
        "artifacts": list(artifacts or []),
        "recorded_at": datetime.now(UTC).isoformat(timespec="microseconds"),
    }
    return {**body, "record_id": digest(body)}


def validate_record(record: dict) -> None:
    if not isinstance(record, dict) or record.get("schema") != SCHEMA:
        raise InputError("Unsupported evidence schema. Regenerate the record with this Wongo version.")
    if not isinstance(record.get("kind"), str) or record["kind"] not in KINDS:
        raise InputError("Unknown evidence kind. Regenerate the record with its producer.")
    for key in ("subject", "producer", "result", "coverage"):
        if not isinstance(record.get(key), dict):
            raise InputError(f"Evidence {key} must be a mapping. Fix its producer.")
    if record.get("subject_id") != digest(record["subject"]):
        raise InputError("Evidence subject identity does not match its contents.")
    if record.get("record_id") != digest({k: v for k, v in record.items() if k != "record_id"}):
        raise InputError("Evidence record hash does not match its contents. Regenerate it.")
    if not isinstance(record.get("recorded_at"), str):
        raise InputError("Evidence recorded_at is missing. Regenerate it.")
    if not isinstance(record.get("artifacts"), list):
        raise InputError("Evidence artifacts must be a list.")
    for item in record["artifacts"]:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str) \
                or not isinstance(item.get("sha256"), str):
            raise InputError("Each evidence artifact needs a relative path and SHA-256.")


def save_record(project: Path, record: dict) -> Path:
    validate_record(record)
    path = safe_path(evidence_dir(project), f"{record['kind']}/{record['record_id']}.json",
                     must_exist=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_text_atomic(path, json.dumps(record, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    return path


def load_records(project: Path, kind: str | None = None, target: str | None = None) -> list[dict]:
    root = evidence_dir(project)
    if kind is not None and kind not in KINDS:
        raise InputError(f"Unknown evidence kind {kind!r}.")
    paths = (root / kind).glob("*.json") if kind else root.glob("*/*.json")
    records = []
    for path in sorted(paths):
        safe_path(root, path.relative_to(root).as_posix())
        try:
            record = json.loads(read_text(path))
        except (OSError, ValueError) as exc:
            raise InputError(f"Invalid evidence JSON: {path}. Regenerate its record.") from exc
        validate_record(record)
        if path.stem != record["record_id"] or path.parent.name != record["kind"]:
            raise InputError(f"Evidence filename disagrees with its identity: {path.name}")
        if target is None or record["subject"].get("target") == target:
            records.append(record)
    return sorted(records, key=lambda r: (r["recorded_at"], r["record_id"]))


def verify_record(project: Path, record: dict, *, current: dict | None = None) -> dict:
    try:
        validate_record(record)
        for artifact in record["artifacts"]:
            path = safe_path(Path(project), artifact["path"])
            if hash_file(path) != artifact["sha256"]:
                return {"state": "stale", "detail": f"Evidence artifact changed: {artifact['path']}"}
    except InputError as exc:
        return {"state": "invalid", "detail": str(exc)}
    try:
        current = current or snapshot(project, record["subject"].get("target", "submission"))
    except InputError as exc:
        return {"state": "stale", "detail": str(exc)}
    if current["id"] != record["subject_id"]:
        return {"state": "stale", "detail": "The build, declared inputs, engine, or outputs changed."}
    return {"state": "fresh", "detail": "Exact build and artifact identities match."}


def atomic_bytes(path: Path, raw: bytes) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise
    return path
