"""Project-owned scientific assertions against explicitly identified rendered content."""
from __future__ import annotations

import hashlib
import math
import posixpath
import re
import zipfile
from pathlib import Path

from lxml import etree

from wongo.errors import InputError
from wongo.textio import require_docx

_NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "v": "urn:schemas-microsoft-com:vml",
}
_MISSING = object()


def _xml(raw):
    return etree.fromstring(raw, parser=etree.XMLParser(resolve_entities=False, no_network=True))


def _result(identifier, ok, detail, *, source=None, artifact=None, context=None,
            expected=None, actual=None):
    def safe(value):
        if isinstance(value, float) and not math.isfinite(value):
            return str(value)
        if isinstance(value, dict):
            return {str(key): safe(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [safe(item) for item in value]
        return value if isinstance(value, (str, int, float, bool, type(None))) else str(value)

    return {
        "id": identifier, "ok": bool(ok), "detail": detail,
        "source": source if source is not None else "not-provided",
        "artifact": artifact if artifact is not None else "not-provided",
        "rendered_context": context,
        "expected": safe(expected), "actual": safe(actual),
    }


def scalar_assertion(data, pointer: str, *, allow_missing: bool = False,
                     finite: bool = True, source=None, assertion_id=None) -> dict:
    """Check an explicit JSON pointer for a nonempty scalar.

    A missing key always fails. A present null is allowed only by the project's
    policy. Text such as NA is ordinary text; this helper does not infer missingness.
    """
    identifier = assertion_id or f"scalar:{pointer}"
    value = data
    if pointer and not pointer.startswith("/"):
        raise InputError("An audit artifact pointer must be empty or begin with '/'.")
    for token in pointer.split("/")[1:] if pointer else []:
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(value, list) and not re.fullmatch(r"0|[1-9]\d*", token):
            value = _MISSING
            break
        try:
            value = value[int(token)] if isinstance(value, list) else value[token]
        except (KeyError, IndexError, TypeError, ValueError):
            value = _MISSING
            break
    if value is _MISSING:
        ok, detail, actual = False, "Artifact key is missing.", None
    elif value is None:
        ok, detail, actual = allow_missing, "Null is permitted." if allow_missing else "Scalar is null.", None
    elif isinstance(value, (list, dict)) or isinstance(value, str) and not value.strip():
        ok, detail, actual = False, "Expected one nonempty scalar, not an empty value or container.", value
    elif finite and isinstance(value, float) and not math.isfinite(value):
        ok, detail, actual = False, "Scalar is non-finite.", value
    else:
        ok, detail, actual = True, "Scalar satisfies the declared presence/finite policy.", value
    return _result(identifier, ok, detail, source=source, artifact=pointer,
                   expected={"scalar": True, "finite": finite, "allow_null": allow_missing},
                   actual=actual)


def _document(path: Path | str):
    require_docx(path)
    try:
        with zipfile.ZipFile(path) as package:
            return _xml(package.read("word/document.xml"))
    except (OSError, KeyError, zipfile.BadZipFile, etree.XMLSyntaxError) as exc:
        raise InputError(f"Could not inspect {Path(path).name}; restore a valid DOCX and rerun the audit.") from exc


def _text(element) -> str:
    kept = []
    for node in element.iter():
        if node.tag.rsplit("}", 1)[-1] in {"p", "tab", "br"}:
            kept.append(" ")
        if node.tag.rsplit("}", 1)[-1] != "t":
            continue
        if any(parent.tag == f"{{{_NS['w']}}}del" for parent in node.iterancestors()):
            continue
        kept.append(node.text or "")
    return " ".join("".join(kept).split())


def _contains(text: str, expected) -> bool:
    value = str(expected)
    if not value:
        return False
    return bool(re.search(r"(?<![\w.+−-])" + re.escape(value) + r"(?![\w+−-]|\.\d)", text))


def _punctuation_spans(text: str):
    start = 0
    for boundary in re.finditer(r"[.!?](?:[\"'”’)\]]*)(?=\s|$)", text):
        end = boundary.end()
        while start < end and text[start].isspace():
            start += 1
        if start < end:
            yield start, end
        start = end
    while start < len(text) and text[start].isspace():
        start += 1
    if start < len(text):
        yield start, len(text)


def paragraph_assertion(path: Path | str, context: str, expected, *, source=None,
                        artifact=None, assertion_id="paragraph-value") -> dict:
    """Match a value in the punctuation span containing one unique DOCX anchor.

    Projects supply the expected display string, including their rounding/units.
    Periods, question marks and exclamation marks followed by whitespace or the
    paragraph end bound the span; decimal points stay intact. This deliberately
    conservative rule does not infer semantic sentence or scientific meaning.
    """
    if not isinstance(context, str) or not context.strip():
        raise InputError("A paragraph audit needs a nonempty context anchor.")
    doc = _document(path)
    anchor = " ".join(context.split())
    matches = [(node, _text(node)) for node in doc.xpath(".//w:p", namespaces=_NS)
               if anchor in _text(node)]
    rendered = {"part": "word/document.xml", "anchor": anchor, "matches": len(matches)}
    if len(matches) != 1:
        return _result(assertion_id, False, "Rendered context is absent or ambiguous.", source=source,
                       artifact=artifact, context=rendered, expected=expected)
    node, text = matches[0]
    anchors = list(re.finditer(re.escape(anchor), text))
    rendered.update({"xpath": node.getroottree().getpath(node), "paragraph_text": text,
                     "anchor_matches": len(anchors), "scope": "punctuation-bounded text"})
    spans = [(start, end) for start, end in _punctuation_spans(text)
             if len(anchors) == 1 and start <= anchors[0].start() and anchors[0].end() <= end]
    if len(spans) != 1:
        return _result(assertion_id, False, "Context anchor is repeated or crosses a punctuation boundary.",
                       source=source, artifact=artifact, context=rendered, expected=expected)
    start, end = spans[0]
    local_text = text[start:end]
    rendered.update({"text": local_text, "span": {"start": start, "end": end}})
    ok = _contains(local_text, expected)
    return _result(assertion_id, ok, "Expected value matches its context." if ok else
                   "Expected value is absent from the identified context.", source=source,
                   artifact=artifact, context=rendered, expected=expected, actual=local_text)


def table_cell_assertion(path: Path | str, table: int, row: int, column: int, expected,
                         *, source=None, artifact=None, assertion_id="table-cell") -> dict:
    """Check zero-based OOXML table/row/cell indices, including nested tables."""
    if any(type(index) is not int or index < 0 for index in (table, row, column)):
        raise InputError("Table audit indices must be non-negative integers (zero-based).")
    doc = _document(path)
    location = {"part": "word/document.xml", "table": table, "row": row, "column": column}
    try:
        node = doc.xpath(".//w:tbl", namespaces=_NS)[table]
        cell = node.findall(f"{{{_NS['w']}}}tr")[row].findall(f"{{{_NS['w']}}}tc")[column]
    except IndexError:
        return _result(assertion_id, False, "Requested rendered table cell is absent.",
                       source=source, artifact=artifact, context=location, expected=expected)
    text = _text(cell)
    location.update({"xpath": cell.getroottree().getpath(cell), "text": text})
    ok = text == str(expected)
    return _result(assertion_id, ok, "Cell matches." if ok else "Cell differs from the expected value.",
                   source=source, artifact=artifact, context=location, expected=expected, actual=text)


def figure_order_assertion(path: Path | str, expected_hashes: list[str], *, source=None,
                           artifact=None, assertion_id="figure-order") -> dict:
    """Compare embedded image hashes in main-document drawing order."""
    doc = _document(path)
    actual = []
    try:
        with zipfile.ZipFile(path) as package:
            rels = _xml(package.read("word/_rels/document.xml.rels"))
            targets = {node.get("Id"): node for node in rels}
            for drawing in doc.xpath(".//a:blip | .//v:imagedata", namespaces=_NS):
                if any(parent.tag == f"{{{_NS['w']}}}del" for parent in drawing.iterancestors()):
                    continue
                relid = drawing.get(f"{{{_NS['r']}}}embed") or drawing.get(f"{{{_NS['r']}}}id")
                target = targets.get(relid)
                if target is None or target.get("TargetMode") == "External":
                    actual.append("external-or-unresolved-image")
                    continue
                member = posixpath.normpath(posixpath.join("word", target.get("Target", "")))
                actual.append(hashlib.sha256(package.read(member)).hexdigest())
    except (OSError, KeyError, zipfile.BadZipFile, etree.XMLSyntaxError) as exc:
        raise InputError(f"Could not inspect embedded images in {Path(path).name}; restore a valid DOCX.") from exc
    ok = actual == expected_hashes
    return _result(assertion_id, ok, "Embedded image order matches." if ok else
                   "Embedded image identities or order differ.", source=source, artifact=artifact,
                   context={"part": "word/document.xml", "scope": "embedded-drawing-order"},
                   expected=expected_hashes, actual=actual)
