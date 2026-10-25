"""Allowlisted portable reviews and narrowly normalized artifact identities."""
from __future__ import annotations

import hashlib
import io
import json
import re
import zipfile
from pathlib import Path, PurePosixPath

from lxml import etree

from wongo.errors import InputError
from wongo.evidence import (
    atomic_bytes,
    digest,
    hash_file,
    load_records,
    safe_path,
    snapshot,
    validate_record,
    verify_record,
)

SCHEMA = "wongo-review/1"


def record_references(record: dict) -> set[str]:
    """Named evidence links, including historical page-inspection provenance."""
    result = record["result"]
    values = result.get("evidence_ids", [])
    if not isinstance(values, list) or any(not isinstance(value, str) or not value for value in values):
        raise InputError("Evidence references must be a list of record identifiers.")
    refs = set(values)
    for key in ("preview_record_id", "carried_from", "review_note_id"):
        if result.get(key):
            if not isinstance(result[key], str):
                raise InputError("Evidence references must be record identifiers.")
            refs.add(result[key])
    pages = result.get("checked_pages", [])
    if not isinstance(pages, list) or any(not isinstance(page, dict) for page in pages):
        raise InputError("Evidence checked_pages must be a list of page mappings.")
    for page in pages:
        if page.get("original_record_id"):
            if not isinstance(page["original_record_id"], str):
                raise InputError("Original page evidence must name a record identifier.")
            refs.add(page["original_record_id"])
    if any(not isinstance(value, str) or not value for value in refs):
        raise InputError("Evidence references must be nonempty record identifiers.")
    return refs


def _record_closure(project: Path, selected: list[dict], available: list[dict],
                    current: dict) -> tuple[list[dict], list[dict]]:
    by_id = {record["record_id"]: record for record in available}
    included = {record["record_id"]: record for record in selected}
    queue = list(selected)
    while queue:
        for ref in record_references(queue.pop()):
            if ref in included:
                continue
            record = by_id.get(ref)
            if record is None:
                raise InputError(f"Evidence references a missing record: {ref}. Restore it before export.")
            original = {"id": record["subject_id"], "subject": record["subject"]}
            state = verify_record(project, record, current=original)
            if state["state"] != "fresh":
                raise InputError(f"Referenced evidence is {state['state']}: {ref}. {state['detail']}")
            included[ref] = record
            queue.append(record)
    ordered = sorted(included.values(), key=lambda record: (record["recorded_at"], record["record_id"]))
    return ([record for record in ordered if record["subject_id"] == current["id"]],
            [record for record in ordered if record["subject_id"] != current["id"]])


def _pdf_info_dates(raw: bytes) -> bytes:
    """Mask same-length date strings only in an uncompressed trailer Info dict.

    Streams, XMP, IDs, object ordering and unsupported PDFs retain exact bytes.
    Conservative false negatives are preferable to hiding a content change.
    """
    start = re.search(rb"startxref\s+(\d+)\s+%%EOF\s*$", raw)
    if not raw.startswith(b"%PDF-") or not start:
        return raw
    offset = int(start[1])
    tail = re.fullmatch(rb"xref\s+(.*?)\btrailer\s*<<(.*?)>>\s*startxref\s+\d+\s+%%EOF\s*",
                        raw[offset:], re.DOTALL)
    if not tail or any(key in tail[2] for key in (b"/Prev", b"/XRefStm", b"/Encrypt")):
        return raw
    info = re.search(rb"/Info\s+(\d+)\s+(\d+)\s+R\b", tail[2])
    if not info:
        return raw
    lines = tail[1].splitlines()
    entries = {}
    while lines:
        section = re.fullmatch(rb"(\d+)\s+(\d+)\s*", lines.pop(0))
        if not section:
            return raw
        first, count = int(section[1]), int(section[2])
        if count > len(lines):
            return raw
        for number in range(first, first + count):
            entry = re.fullmatch(rb"(\d{10}) (\d{5}) ([nf])\s*", lines.pop(0))
            if not entry or number in entries:
                return raw
            entries[number] = (int(entry[1]), int(entry[2]), entry[3])
    entry = entries.get(int(info[1]))
    if not entry or entry[1] != int(info[2]) or entry[2] != b"n":
        return raw
    object_offset = entry[0]
    header = re.compile(info[1] + rb"\s+" + info[2] + rb"\s+obj\s*<<(.*?)>>\s*endobj", re.DOTALL)
    obj = header.match(raw, object_offset)
    if not obj or object_offset >= offset:
        return raw
    body = obj[1]
    if b"stream" in body or b"<<" in body:
        return raw
    # Tokenize literal strings before names so a date-looking key inside a title
    # cannot become a metadata field. Complex dictionaries fall back to exact bytes.
    token = re.compile(rb"\s+|%[^\r\n]*|/(?:[^\s()<>{}\[\]/%]+)|\((?:\\.|[^()\\])*\)|<[^<>]*>|\[[^\[\]]*\]|[-+\d.]+|[A-Za-z]+", re.DOTALL)
    spans = list(token.finditer(body))
    if b"".join(m[0] for m in spans) != body:
        return raw
    significant = [m for m in spans if not m[0].isspace() and not m[0].startswith(b"%")]
    masked = bytearray(body)
    for first, second in zip(significant, significant[1:]):
        if first[0] in {b"/CreationDate", b"/ModDate"} and re.fullmatch(
                rb"\(D:[0-9+'Zz\- :]+\)", second[0]):
            masked[second.start():second.end()] = b"(" + b"0" * (len(second[0]) - 2) + b")"
    return raw[:obj.start(1)] + bytes(masked) + raw[obj.end(1):]


def artifact_identity(path: Path) -> dict:
    path = Path(path)
    try:
        return _identity_bytes(path.read_bytes(), path.name)
    except OSError as exc:
        raise InputError(f"Cannot read artifact identity: {path.name}. Restore or unlock it.") from exc


def _identity_bytes(data: bytes, name: str) -> dict:
    suffix = Path(name).suffix.lower()
    raw_hash = hashlib.sha256(data).hexdigest()
    normalizer = "exact-bytes/1"
    normalized = raw_hash
    if suffix == ".docx":
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as package:
                if len(package.namelist()) != len(set(package.namelist())):
                    raise InputError(f"Duplicate DOCX ZIP entries: {name}")
                parts = {}
                for member in sorted(package.namelist()):
                    raw = package.read(member)
                    if member == "docProps/core.xml":
                        xml = etree.fromstring(raw, parser=etree.XMLParser(resolve_entities=False, no_network=True))
                        for element in xml:
                            if element.tag in {
                                "{http://purl.org/dc/terms/}created",
                                "{http://purl.org/dc/terms/}modified",
                            }:
                                element.text = ""
                        raw = etree.tostring(xml, method="c14n")
                    parts[member] = hashlib.sha256(raw).hexdigest()
            normalized, normalizer = digest(parts), "docx-core-dates-and-zip-metadata/1"
        except (OSError, zipfile.BadZipFile, etree.XMLSyntaxError) as exc:
            raise InputError(f"Cannot inspect DOCX identity: {name}. Restore a valid DOCX.") from exc
    elif suffix == ".pdf":
        normalized = hashlib.sha256(_pdf_info_dates(data)).hexdigest()
        normalizer = "pdf-uncompressed-info-dates-same-length/1"
    return {"sha256": raw_hash, "content_sha256": normalized, "normalizer": normalizer}


def compare_artifacts(first: Path, second: Path) -> dict:
    a, b = artifact_identity(first), artifact_identity(second)
    classification = "changed"
    if a["sha256"] == b["sha256"]:
        classification = "identical"
    elif a["normalizer"] == b["normalizer"] and a["content_sha256"] == b["content_sha256"]:
        classification = "metadata-only"
    return {"classification": classification, "first": a, "second": b}


def export_review(project: Path, destination: Path, target: str = "submission", *,
                  include: list[str] | None = None, include_outputs: bool = False,
                  include_artifacts: bool = False, record_ids: list[str] | None = None) -> dict:
    project, destination = Path(project).resolve(), Path(destination).resolve()
    if destination.exists():
        raise InputError(f"Review destination exists: {destination}. Choose a new filename.")
    current = snapshot(project, target)
    records = load_records(project, target=target)
    requested = set(record_ids) if record_ids is not None else None
    selected, excluded = [], []
    for record in records:
        if requested is not None and record["record_id"] not in requested:
            continue
        state = verify_record(project, record, current=current)
        if state["state"] != "fresh":
            if requested is not None:
                raise InputError(f"Cannot attach {state['state']} evidence: {record['record_id']}")
            excluded.append({"record_id": record["record_id"], **state})
        else:
            selected.append(record)
    if requested is not None and requested - {r["record_id"] for r in selected}:
        raise InputError("Requested evidence record was not found for this target.")
    selected, historical = _record_closure(project, selected, records, current)
    excluded = [item for item in excluded if item["record_id"] not in {
        record["record_id"] for record in historical}]
    allowed = set(include or [])
    if include_outputs:
        allowed.update(f"output/{name}" for name in current["subject"]["outputs"])
    if include_artifacts:
        for record in selected + historical:
            for artifact in record["artifacts"]:
                if not artifact["path"].replace("\\", "/").startswith("output/.wongo-evidence/"):
                    raise InputError("Generated-artifact export requires files under output/.wongo-evidence. "
                                     "Select other project files explicitly with --include.")
                allowed.add(artifact["path"])
    blobs, files = {}, []
    for raw in sorted(allowed):
        path = safe_path(project, raw)
        if path == destination:
            raise InputError("The review archive cannot replace one of its inputs.")
        relative = path.relative_to(project).as_posix()
        blob = path.read_bytes()
        sha = hashlib.sha256(blob).hexdigest()
        if hash_file(path) != sha:
            raise InputError(f"Export input changed while reading: {relative}. Retry after saving.")
        member = f"files/{relative}"
        blobs[member] = blob
        identity = _identity_bytes(blob, relative)
        files.append({"path": member, "source": relative, "sha256": sha, "bytes": len(blob),
                      "identity": identity})
    included_sources = {item["source"] for item in files}
    omitted_artifacts = sorted({a["path"] for r in selected + historical for a in r["artifacts"]}
                               - included_sources)
    manifest = {
        "schema": SCHEMA, "subject_id": current["id"], "subject": current["subject"],
        "installation": current["installation"], "records": selected, "files": files,
        "historical_records": historical,
        "historical_scope": "Provenance links only; historical records are not current-build observations.",
        "excluded_records": excluded, "omitted_artifacts": omitted_artifacts,
        "source_files_included": sorted(raw for raw in allowed if not raw.startswith("output/")),
        "scope": "Only explicitly selected files are bundled; dependency hashes do not imply inclusion.",
    }
    manifest["bundle_id"] = digest(manifest)
    if snapshot(project, target)["id"] != current["id"]:
        raise InputError("Build changed during review export. Retry after rendering current outputs.")
    for record in selected + historical:
        original = {"id": record["subject_id"], "subject": record["subject"]}
        if verify_record(project, record, current=original)["state"] != "fresh":
            raise InputError("Evidence artifacts changed during review export. Retry after regenerating evidence.")
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as package:
        package.writestr("review.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        for name, blob in blobs.items():
            package.writestr(name, blob)
    atomic_bytes(destination, archive.getvalue())
    return {"ok": True, "path": str(destination), "bundle_id": manifest["bundle_id"],
            "files": files, "records": len(selected), "excluded_records": excluded,
            "historical_records": len(historical),
            "omitted_artifacts": omitted_artifacts}


def verify_bundle(path: Path) -> dict:
    try:
        with zipfile.ZipFile(path) as package:
            names = package.namelist()
            if len(names) != len(set(names)) or "review.json" not in names:
                raise InputError("Review archive has missing or duplicate entries.")
            for name in names:
                portable = PurePosixPath(name)
                if portable.is_absolute() or ".." in portable.parts or "\\" in name:
                    raise InputError("Review archive contains an unsafe path.")
            manifest = json.loads(package.read("review.json"))
            if not isinstance(manifest, dict):
                raise InputError("Review manifest must be a JSON mapping.")
            if manifest.get("schema") != SCHEMA or manifest.get("bundle_id") != digest(
                    {key: value for key, value in manifest.items() if key != "bundle_id"}):
                raise InputError("Review manifest identity is invalid.")
            if manifest["subject_id"] != digest(manifest["subject"]):
                raise InputError("Review build identity is invalid.")
            if not isinstance(manifest["subject"], dict):
                raise InputError("Review subject must be a mapping.")
            for key in ("outputs", "sources"):
                if not isinstance(manifest["subject"].get(key), dict):
                    raise InputError(f"Review subject {key} must be a mapping.")
            for key in ("records", "files", "historical_records"):
                value = manifest.get(key, [] if key == "historical_records" else None)
                if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
                    raise InputError(f"Review {key} must be a list of mappings.")
            if (not isinstance(manifest.get("omitted_artifacts"), list)
                    or any(not isinstance(item, str) for item in manifest["omitted_artifacts"])):
                raise InputError("Review omitted_artifacts must be a list of paths.")
            expected = {"review.json"}
            file_hashes = {}
            for item in manifest["files"]:
                if (not isinstance(item.get("path"), str) or not isinstance(item.get("source"), str)
                        or not isinstance(item.get("sha256"), str) or type(item.get("bytes")) is not int):
                    raise InputError("Review file needs path, source, SHA-256 and integer byte size.")
                if item["path"] in expected or not item["path"].startswith("files/"):
                    raise InputError("Review archive repeats a file or uses an invalid file prefix.")
                expected.add(item["path"])
                raw = package.read(item["path"])
                if len(raw) != item["bytes"] or hashlib.sha256(raw).hexdigest() != item["sha256"]:
                    raise InputError(f"Review file identity mismatch: {item['path']}")
                if item["path"] != f"files/{item['source']}":
                    raise InputError("Review file path disagrees with its source pointer.")
                source = item["source"]
                bound = {**manifest["subject"].get("sources", {}), **{
                    f"output/{name}": sha for name, sha in manifest["subject"]["outputs"].items()}}
                if source in bound and item["sha256"] != bound[source]:
                    raise InputError(f"Review file disagrees with the sealed build: {source}")
                if item.get("identity") != _identity_bytes(raw, source):
                    raise InputError("Review file normalized identity disagrees with its bytes.")
                file_hashes[item["source"]] = item["sha256"]
            if set(names) != expected:
                raise InputError("Review archive has unlisted or missing files.")
            for record in manifest["records"]:
                validate_record(record)
                if record["subject_id"] != manifest["subject_id"]:
                    raise InputError("Evidence belongs to a different build.")
            historical = manifest.get("historical_records", [])
            for record in historical:
                validate_record(record)
                if record["subject_id"] == manifest["subject_id"]:
                    raise InputError("Historical evidence must be separate from current observations.")
            records = manifest["records"] + historical
            ids = {record["record_id"] for record in records}
            if len(ids) != len(records):
                raise InputError("Review archive repeats an evidence record.")
            refs = set()
            omitted = set()
            for record in records:
                refs.update(record_references(record))
                for artifact in record["artifacts"]:
                    if artifact["path"] in file_hashes:
                        if file_hashes[artifact["path"]] != artifact["sha256"]:
                            raise InputError("Bundled artifact disagrees with its evidence record.")
                    else:
                        omitted.add(artifact["path"])
            if refs - ids:
                raise InputError("Review archive has missing referenced evidence.")
            by_id = {record["record_id"]: record for record in records}
            reachable = {record["record_id"] for record in manifest["records"]}
            queue = list(reachable)
            while queue:
                for ref in record_references(by_id[queue.pop()]):
                    if ref not in reachable:
                        reachable.add(ref)
                        queue.append(ref)
            if ids - reachable:
                raise InputError("Unreferenced historical evidence cannot be attached to this build.")
            if omitted != set(manifest["omitted_artifacts"]):
                raise InputError("Review archive does not accurately declare omitted artifacts.")
    except (OSError, zipfile.BadZipFile, ValueError, KeyError, TypeError) as exc:
        raise InputError("Invalid review archive. Export a new archive from verified evidence.") from exc
    return {"ok": True, "bundle_id": manifest["bundle_id"], "subject_id": manifest["subject_id"],
            "files": len(manifest["files"]), "records": len(manifest["records"]),
            "historical_records": len(manifest.get("historical_records", [])),
            "omitted_artifacts": manifest["omitted_artifacts"]}
