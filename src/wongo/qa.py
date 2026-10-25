"""Final OOXML inventory, renderer-specific previews, and scoped inspection records."""
from __future__ import annotations

import copy
import hashlib
import posixpath
import re
import shutil
import subprocess
import tempfile
import uuid
import zipfile
from pathlib import Path

from lxml import etree

from wongo import __version__, toolchain
from wongo.errors import InputError, OutputError, ToolchainError
from wongo.evidence import (
    evidence_dir,
    hash_file,
    load_records,
    make_record,
    safe_path,
    save_record,
    snapshot,
    validate_record,
    verify_record,
)
from wongo.textio import require_docx

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "v": "urn:schemas-microsoft-com:vml",
}
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


def _xml(raw: bytes):
    return etree.fromstring(raw, parser=etree.XMLParser(resolve_entities=False, no_network=True))


def inspect_docx(path: Path | str) -> dict:
    """Read actual package fields; no inference about native Word pagination."""
    path = Path(path)
    require_docx(path)
    issues = []
    images = []
    captions = []
    tables = []
    text = []
    math_count = revision_count = superscript_count = 0
    try:
        with zipfile.ZipFile(path) as package:
            names = set(package.namelist())
            if len(names) != len(package.namelist()):
                raise InputError("Duplicate DOCX ZIP entries are ambiguous. Restore a valid DOCX and retry.")
            parts = ["word/document.xml"] + sorted(
                name for name in names if re.fullmatch(r"word/(?:(?:header|footer)\d+|footnotes|endnotes)\.xml", name)
            )
            for part in parts:
                document = _xml(package.read(part))
                relpath = posixpath.join(posixpath.dirname(part), "_rels", posixpath.basename(part) + ".rels")
                relationships = {}
                if relpath in names:
                    relationships = {
                        rel.get("Id"): rel for rel in _xml(package.read(relpath))
                    }
                text.extend(document.xpath(".//w:t/text()", namespaces=NS))
                math_count += len(document.xpath(".//m:oMath", namespaces=NS))
                revision_count += len(document.xpath(".//w:ins | .//w:del | .//w:moveFrom | .//w:moveTo", namespaces=NS))
                superscript_count += len(document.xpath(".//w:vertAlign[@w:val='superscript']", namespaces=NS))
                for number, paragraph in enumerate(document.xpath(".//w:p", namespaces=NS), start=1):
                    styles = paragraph.xpath("./w:pPr/w:pStyle/@w:val", namespaces=NS)
                    if any("caption" in style.casefold() for style in styles):
                        captions.append({"part": part, "paragraph": number,
                                         "text": "".join(paragraph.xpath(".//w:t/text()", namespaces=NS))})
                for number, table in enumerate(document.xpath(".//w:tbl", namespaces=NS), start=1):
                    rows = table.findall(f"{{{NS['w']}}}tr")
                    tables.append({
                        "part": part, "table": number, "rows": len(rows),
                        "columns": max((len(row.findall(f"{{{NS['w']}}}tc")) for row in rows), default=0),
                        "repeat_header_rows": len(table.xpath("./w:tr/w:trPr/w:tblHeader", namespaces=NS)),
                        "non_splitting_rows": len(table.xpath("./w:tr/w:trPr/w:cantSplit", namespaces=NS)),
                    })
                drawings = document.xpath(".//w:drawing | .//w:pict", namespaces=NS)
                for drawing in drawings:
                    docprops = drawing.xpath(".//wp:docPr", namespaces=NS)
                    prop = docprops[0] if docprops else None
                    legacy_alt = drawing.xpath(".//v:shape/@alt", namespaces=NS)
                    description = (prop.get("descr", "") if prop is not None else
                                   legacy_alt[0] if legacy_alt else "").strip()
                    title = prop.get("title", "") if prop is not None else ""
                    decorative = bool(drawing.xpath(".//*[local-name()='decorative' and @val='1']"))
                    refs = drawing.xpath(".//a:blip/@r:embed | .//a:blip/@r:link | .//v:imagedata/@r:id", namespaces=NS)
                    for rid in refs:
                        relationship = relationships.get(rid)
                        embedded = None
                        embedded_hash = None
                        external = relationship is not None and relationship.get("TargetMode") == "External"
                        if relationship is not None and not external:
                            target = relationship.get("Target", "")
                            embedded = posixpath.normpath(target.lstrip("/") if target.startswith("/") else
                                                         posixpath.join(posixpath.dirname(part), target))
                            if embedded in names and not embedded.startswith("../"):
                                embedded_hash = hashlib.sha256(package.read(embedded)).hexdigest()
                        occurrence = len(images) + 1
                        images.append({
                            "part": part, "occurrence": occurrence, "relationship_id": rid,
                            "drawing_id": prop.get("id") if prop is not None else None,
                            "embedded_path": embedded, "sha256": embedded_hash,
                            "description": description, "title": title, "decorative": decorative,
                            "external": external,
                        })
                        if embedded_hash is None:
                            issues.append({"id": "unverified-image", "part": part, "image": occurrence,
                                           "detail": "Image is external or its embedded relationship cannot be verified."})
                        if not description and not decorative:
                            issues.append({"id": "missing-alt-text", "part": part, "image": occurrence,
                                           "detail": "Final OOXML has no image description or decorative designation."})
    except (OSError, KeyError, zipfile.BadZipFile, etree.XMLSyntaxError) as exc:
        raise InputError(f"Could not inspect DOCX {path.name}: {exc}. Restore a valid DOCX and retry.") from exc
    return {
        "ok": not issues, "representation": "native-docx-ooxml", "sha256": hash_file(path),
        "native_word_pagination_verified": False, "images": images, "captions": captions,
        "tables": tables, "math_count": math_count, "revision_count": revision_count,
        "superscript_count": superscript_count,
        "extracted_text": "\n".join(text), "text_representation": "OOXML text extraction; not a layout preview",
        "issues": issues,
    }


def _unchanged(project, target, current):
    if snapshot(project, target)["id"] != current["id"]:
        raise InputError("The build changed during QA. Existing evidence was left unchanged; retry on current outputs.")


def inspect_outputs(project: Path, target: str = "submission") -> dict:
    project = Path(project).resolve()
    current = snapshot(project, target)
    documents = {name: inspect_docx(safe_path(project / "output", name))
                 for name in current["subject"]["outputs"]}
    for document in documents.values():
        extracted = document.pop("extracted_text")
        document["text_identity"] = {"sha256": hashlib.sha256(extracted.encode("utf-8")).hexdigest(),
                                     "characters": len(extracted)}
        document["text_representation"] = "OOXML extracted-text identity only; no layout preview or full manuscript text"
    _unchanged(project, target, current)
    result = {"ok": all(doc["ok"] for doc in documents.values()),
              "representation": "native-docx-ooxml", "documents": documents,
              "native_word_pagination_verified": False}
    record = make_record(current, "inspection", {"name": "wongo.qa.inspect", "version": __version__}, result, {
        "checked": ["embedded-image-identities", "final-image-descriptions", "table-structure", "math-and-revisions"],
        "untested": ["native Word pagination", "scientific correctness", "semantic adequacy of descriptions"],
    })
    path = save_record(project, record)
    return {"ok": result["ok"], "record": record, "path": path}


def _run(command: list[str], *, timeout: int, cwd: Path | None = None) -> str:
    try:
        completed = subprocess.run(command, cwd=cwd, check=False, capture_output=True,
                                   text=True, encoding="utf-8", errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise ToolchainError(f"Preview tool timed out after {timeout} seconds. Retry with a larger --timeout.") from exc
    except OSError as exc:
        raise ToolchainError(f"Could not run preview tool {command[0]}: {exc}. Check its installation.") from exc
    if completed.returncode:
        raise ToolchainError("Preview generation failed. Check the renderer diagnostics and retry.",
                             output=(completed.stdout + completed.stderr)[-12000:])
    return completed.stdout


def create_preview(project: Path, target: str = "submission", *, renderer: str = "libreoffice",
                   dpi: int = 144, timeout: int = 120) -> dict:
    """Render disposable copies; final DOCX and render manifests are never edited."""
    if renderer != "libreoffice":
        raise InputError("Supported preview renderer: libreoffice. Native Word inspection is recorded separately.")
    if type(dpi) is not int or not 36 <= dpi <= 600:
        raise InputError("Preview dpi must be an integer from 36 to 600.")
    if type(timeout) is not int or timeout <= 0:
        raise InputError("Preview timeout must be a positive integer.")
    project = Path(project).resolve()
    current = snapshot(project, target)
    office = toolchain.qa_tool_command("soffice")
    info = toolchain.qa_tool_command("pdfinfo")
    raster = toolchain.qa_tool_command("pdftoppm")
    producer = {"name": "libreoffice", "version": toolchain.tool_version(office),
                "pdfinfo_version": toolchain.tool_version(info, ("-v",)),
                "pdftoppm_version": toolchain.tool_version(raster, ("-v",))}
    if any(value is None for key, value in producer.items() if key != "name"):
        raise ToolchainError("Could not determine preview tool versions. Repair the optional renderer tools and retry.")
    settings = {"dpi": dpi, "format": "png", "pdf_filter": "writer_pdf_Export"}
    preview_name = uuid.uuid4().hex
    destination = safe_path(project, (evidence_dir(project) / "previews" / preview_name).relative_to(project).as_posix(),
                            must_exist=False)
    documents = {}
    artifacts = []
    with tempfile.TemporaryDirectory(prefix="wongo-preview-") as temporary:
        scratch = Path(temporary)
        generated = scratch / "generated"
        generated.mkdir()
        profile = (scratch / "lo-profile").as_uri()
        for name, docx_hash in current["subject"]["outputs"].items():
            source = scratch / name
            shutil.copy2(safe_path(project / "output", name), source)
            if hash_file(source) != docx_hash:
                raise InputError(f"{name} changed while making a preview snapshot. Retry on current outputs.")
            _run([*office, f"-env:UserInstallation={profile}", "--headless", "--convert-to",
                  "pdf:writer_pdf_Export", "--outdir", str(generated), str(source)], timeout=timeout, cwd=scratch)
            if hash_file(source) != docx_hash:
                raise InputError(f"The renderer changed its {name} input copy. Preview evidence was not saved.")
            pdf = generated / (source.stem + ".pdf")
            if not pdf.is_file():
                raise ToolchainError(f"The preview renderer did not create {pdf.name}. Check LibreOffice diagnostics.")
            info_text = _run([*info, str(pdf)], timeout=timeout)
            page_match = re.search(r"^Pages:\s*(\d+)\s*$", info_text, re.MULTILINE)
            if page_match is None or int(page_match[1]) < 1:
                raise ToolchainError(f"Could not read the page count of {pdf.name}. Check the generated PDF.")
            page_count = int(page_match[1])
            prefix = generated / source.stem
            _run([*raster, "-r", str(dpi), "-png", str(pdf), str(prefix)], timeout=timeout)
            page_files = sorted(generated.glob(source.stem + "-*.png"),
                                key=lambda p: int(p.stem.rsplit("-", 1)[1]))
            if len(page_files) != page_count:
                raise ToolchainError(f"Expected {page_count} page images for {pdf.name}, got {len(page_files)}. Retry preview export.")
            pages = []
            for number, page in enumerate(page_files, start=1):
                rel = (destination / page.name).relative_to(project).as_posix()
                item = {"number": number, "path": rel, "sha256": hash_file(page)}
                pages.append(item)
                artifacts.append({"path": rel, "sha256": item["sha256"]})
            pdf_rel = (destination / pdf.name).relative_to(project).as_posix()
            pdf_hash = hash_file(pdf)
            artifacts.append({"path": pdf_rel, "sha256": pdf_hash})
            documents[name] = {"docx_sha256": docx_hash, "pdf": {"path": pdf_rel, "sha256": pdf_hash},
                               "page_count": page_count, "pages": pages}
        _unchanged(project, target, current)
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copytree(generated, destination)
        except OSError as exc:
            shutil.rmtree(destination, ignore_errors=True)
            raise OutputError(f"Could not save preview artifacts: {exc}. Check free space and folder permissions, then retry.") from exc
    result = {"ok": True, "representation": "converted-layout-preview", "renderer": producer,
              "settings": settings, "documents": documents, "native_word_verified": False,
              "inspection_status": "not-recorded"}
    try:
        record = make_record(current, "preview", producer, result,
                             {"checked": ["renderer execution", "page count", "page-image export"],
                              "untested": ["visual layout inspection", "native Microsoft Word pagination"]},
                             artifacts=artifacts)
        _unchanged(project, target, current)
        path = save_record(project, record)
    except BaseException:
        shutil.rmtree(destination, ignore_errors=True)
        raise
    return {"ok": True, "record": record, "path": path}


def _find_record(project: Path, kind: str, target: str, record_id: str | None) -> dict:
    records = load_records(project, kind, target)
    if record_id is not None:
        records = [record for record in records if record["record_id"] == record_id]
    if not records:
        raise InputError(f"No {kind} record found. Generate or select that evidence first.")
    return records[-1]


def _page_map(preview: dict) -> dict[tuple[str, int], dict]:
    documents = preview.get("result", {}).get("documents")
    if preview.get("kind") != "preview" or not isinstance(documents, dict) or not documents:
        raise InputError("The selected evidence is not a valid preview inventory. Generate a new preview.")
    expected_outputs = preview.get("subject", {}).get("outputs", {})
    if set(documents) != set(expected_outputs):
        raise InputError("Preview inventory omits or adds an output document. Generate a complete preview.")
    pages = {}
    artifact_pairs = {(item["path"], item["sha256"]) for item in preview.get("artifacts", [])}
    for name, document in documents.items():
        if not isinstance(document, dict) or type(document.get("page_count")) is not int:
            raise InputError("Preview documents need an explicit integer page count. Generate a new preview.")
        if document.get("docx_sha256") != expected_outputs[name]:
            raise InputError("Preview DOCX identity disagrees with its bound output. Generate a new preview.")
        entries = document.get("pages")
        if (not isinstance(entries, list) or document["page_count"] < 1
                or len(entries) != document["page_count"]):
            raise InputError("Preview page coverage is incomplete. Generate a new preview.")
        for number, page in enumerate(entries, start=1):
            if (not isinstance(page, dict) or page.get("number") != number
                    or (page.get("path"), page.get("sha256")) not in artifact_pairs):
                raise InputError("Preview page identities disagree with their artifacts. Generate a new preview.")
            pages[(name, number)] = page
    return pages


def compare_previews(current: dict, previous: dict) -> dict:
    """Page comparisons are scoped to the same renderer/version/settings."""
    validate_record(current)
    validate_record(previous)
    if current["kind"] != "preview" or previous["kind"] != "preview":
        raise InputError("Page comparison needs two preview records.")
    comparable = (current["result"]["renderer"] == previous["result"]["renderer"]
                  and current["result"]["settings"] == previous["result"]["settings"])
    old, new = _page_map(previous), _page_map(current)
    unchanged = []
    changed = []
    for key, page in new.items():
        item = {"document": key[0], "page": key[1], "sha256": page["sha256"]}
        (unchanged if comparable and key in old and old[key]["sha256"] == page["sha256"]
         else changed).append(item)
    return {"comparable": comparable, "unchanged": unchanged, "changed": changed,
            "removed": [{"document": key[0], "page": key[1]} for key in old if key not in new]}


def record_visual_review(project: Path, target: str, reviewer: str, pages: list[dict], *,
                         preview_id: str | None = None, note: str = "", confirmed: bool = False) -> dict:
    if confirmed is not True:
        raise InputError("A person must explicitly confirm visual inspection before it is recorded.")
    if not isinstance(reviewer, str) or not reviewer.strip():
        raise InputError("Name the person who inspected these pages.")
    if not isinstance(pages, list):
        raise InputError("Inspected pages must be a list of document/page mappings.")
    project = Path(project).resolve()
    current = snapshot(project, target)
    preview = _find_record(project, "preview", target, preview_id)
    if verify_record(project, preview, current=current)["state"] != "fresh":
        raise InputError("The selected preview is stale. Generate a current preview before recording inspection.")
    available = _page_map(preview)
    selected = set()
    for item in pages:
        if (not isinstance(item, dict) or type(item.get("page")) is not int
                or not isinstance(item.get("document"), str)):
            raise InputError("Each inspected page needs a document name and integer page number.")
        key = (item.get("document"), item["page"])
        if key not in available:
            raise InputError(f"Page {key} is absent from the selected preview.")
        selected.add(key)
    if not selected:
        raise InputError("Select at least one page that was actually inspected.")
    checked = [{"document": name, "page": number, "sha256": available[(name, number)]["sha256"],
                "reviewer": reviewer.strip()} for name, number in sorted(selected)]
    untested = [{"document": name, "page": number} for name, number in available if (name, number) not in selected]
    result = {"ok": True, "representation": "converted-preview-inspection",
              "reviewer": reviewer.strip(), "note": note,
              "preview_record_id": preview["record_id"], "checked_pages": checked,
              "untested_pages": untested, "complete": not untested, "native_word_verified": False,
              "attribution": "local human attestation; identity is not authenticated"}
    record = make_record(current, "visual-review", {"name": "wongo.qa.review", "version": __version__}, result,
                         {"checked": checked, "untested": untested,
                          "limitations": ["Only the named renderer's page images were inspected; native Word pagination is unverified."]},
                         artifacts=preview["artifacts"])
    _unchanged(project, target, current)
    return {"ok": True, "record": record, "path": save_record(project, record)}


def carry_visual_review(project: Path, target: str, preview_id: str, review_id: str) -> dict:
    """Rebind verified page inspections without inventing a new human decision."""
    project = Path(project).resolve()
    current = snapshot(project, target)
    preview = _find_record(project, "preview", target, preview_id)
    review = _find_record(project, "visual-review", target, review_id)
    if verify_record(project, preview, current=current)["state"] != "fresh":
        raise InputError("The destination preview is stale. Generate a current preview first.")
    old_preview_id = review["result"].get("preview_record_id")
    if not isinstance(old_preview_id, str):
        raise InputError("Only converted-preview inspection with page hashes can be carried. Native Word inspection must be confirmed separately.")
    old_preview = _find_record(project, "preview", target, old_preview_id)
    for original in (review, old_preview):
        original_snapshot = {"id": original["subject_id"], "subject": original["subject"]}
        if verify_record(project, original, current=original_snapshot)["state"] != "fresh":
            raise InputError("Prior inspection evidence or its artifacts changed. Inspect the pages again.")
    comparison = compare_previews(preview, old_preview)
    old_pages = _page_map(old_preview)
    for item in review["result"].get("checked_pages", []):
        key = (item.get("document"), item.get("page"))
        if key not in old_pages or item.get("sha256") != old_pages[key]["sha256"]:
            raise InputError("Prior inspection page identity disagrees with its preview. Inspect those pages again.")
    unchanged = {(item["document"], item["page"]) for item in comparison["unchanged"]}
    checked = [copy.deepcopy(item) for item in review["result"]["checked_pages"]
               if (item["document"], item["page"]) in unchanged]
    if not checked:
        raise InputError("No inspected pages have matching renderer/settings and page bytes. Inspect the new preview.")
    for item in checked:
        item["original_record_id"] = item.get("original_record_id", review["record_id"])
        item["original_recorded_at"] = item.get("original_recorded_at", review["recorded_at"])
    covered = {(item["document"], item["page"]) for item in checked}
    untested = [{"document": name, "page": number} for name, number in _page_map(preview) if (name, number) not in covered]
    result = {**review["result"], "preview_record_id": preview_id, "checked_pages": checked,
              "untested_pages": untested, "complete": not untested, "carried_from": review_id}
    record = make_record(current, "visual-review", {"name": "wongo.qa.carry", "version": __version__}, result,
                         {"checked": checked, "untested": untested,
                          "limitations": review["coverage"].get("limitations", [])}, artifacts=preview["artifacts"])
    _unchanged(project, target, current)
    return {"ok": True, "record": record, "path": save_record(project, record), "comparison": comparison}


def record_native_review(project: Path, target: str, reviewer: str, word_version: str,
                         documents: dict[str, int], pages: list[dict], *, note: str = "",
                         confirmed: bool = False, subject_id: str | None = None) -> dict:
    """Record a person's attributed Word inspection, without claiming tool observation."""
    if confirmed is not True:
        raise InputError("A person must explicitly confirm native Word inspection before it is recorded.")
    if (not isinstance(reviewer, str) or not reviewer.strip()
            or not isinstance(word_version, str) or not word_version.strip()):
        raise InputError("Name the reviewer and the Microsoft Word version they used.")
    project = Path(project).resolve()
    current = snapshot(project, target)
    if subject_id is not None and subject_id != current["id"]:
        raise InputError("The build changed during confirmation. Inspect current native Word files before recording a decision.")
    if (not isinstance(documents, dict) or set(documents) != set(current["subject"]["outputs"])
            or any(type(count) is not int or count < 1 for count in documents.values())):
        raise InputError("Provide a positive native Word page count for every final output document.")
    if not isinstance(pages, list):
        raise InputError("Inspected native pages must be a list of document/page mappings.")
    selected = set()
    available = {(name, number) for name, count in documents.items() for number in range(1, count + 1)}
    for item in pages:
        if (not isinstance(item, dict) or type(item.get("page")) is not int
                or not isinstance(item.get("document"), str)
                or (item["document"], item["page"]) not in available):
            raise InputError("An inspected native page is absent from the declared document page counts.")
        selected.add((item["document"], item["page"]))
    if not selected:
        raise InputError("Select at least one page actually inspected in native Word.")
    checked = [{"document": name, "page": number, "reviewer": reviewer.strip()}
               for name, number in sorted(selected)]
    untested = [{"document": name, "page": number} for name, number in sorted(available - selected)]
    inventory = {name: {"page_count": count, "docx_sha256": current["subject"]["outputs"][name]}
                 for name, count in documents.items()}
    result = {
        "ok": True, "representation": "native-word-inspection", "reviewer": reviewer.strip(),
        "word_version": word_version.strip(), "documents": inventory, "note": note,
        "checked_pages": checked, "untested_pages": untested, "complete": not untested,
        "native_word_attested": True, "native_word_verified": False,
        "verification_method": "local-human-attestation", "identity_authenticated": False,
    }
    record = make_record(current, "visual-review", {"name": "wongo.qa.native-review", "version": __version__},
                         result, {"checked": checked, "untested": untested,
                                  "limitations": ["Wongo records the person's attestation; it did not observe Word execution or authenticate their identity."]})
    _unchanged(project, target, current)
    return {"ok": True, "record": record, "path": save_record(project, record)}
