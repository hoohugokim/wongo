"""Explicit main-to-SI links resolved from the final SI's bookmarked captions."""
from __future__ import annotations

import copy
import hashlib
import re
import zipfile
from pathlib import Path
from urllib.parse import unquote

from lxml import etree

from wongo.errors import ConfigError, InputError

SCHEME = "wongo-si:"
_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
       "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
_REL = "{http://schemas.openxmlformats.org/package/2006/relationships}Relationship"
_LABEL = re.compile(r"(?:fig|tbl)-[\w.-]+\Z")
_LINK = re.compile(r"(?<![!\\])\[[^\]\n]*\]\(\s*<?(wongo-si:[^\s)>]*)>?\s*\)", re.IGNORECASE)
_LEAD = re.compile(r"^(Figure|Table)\s+(S?\s*\d+(?:[.-]\d+)*[a-z]?)(?=[.:](?:\s|$))")


def enabled(cfg: dict) -> bool:
    value = cfg.get("si_references", False)
    if type(value) is not bool:
        raise ConfigError("_journal.yml si_references must be true or false.")
    return value


def source_requests(text: str) -> list[tuple[str, int]]:
    from wongo.engine.checks import INLINE_CODE_RE, _markdown_context

    visible, _ = _markdown_context(text)
    visible = INLINE_CODE_RE.sub(lambda match: "\n" * match[0].count("\n"), visible)
    return [(unquote(match[1][len(SCHEME):]), visible.count("\n", 0, match.start()) + 1)
            for match in _LINK.finditer(visible)]


def source_issues(cfg: dict, texts: dict[str, str]) -> tuple[list[str], int]:
    active = enabled(cfg)
    issues, count = [], 0
    for name, text in texts.items():
        for label, line in source_requests(text):
            count += 1
            where = f"{name}:{line}"
            if not active:
                issues.append(f"{where}: enable si_references: true in _journal.yml or remove the SI link")
            elif name != "index.qmd":
                issues.append(f"{where}: wongo-si links are supported only from the main manuscript")
            elif "si.qmd" not in texts:
                issues.append(f"{where}: si.qmd is missing; restore it or remove the SI link")
            elif not _LABEL.fullmatch(label):
                issues.append(f"{where}: use a fig- or tbl- SI label without a URL query or fragment")
    return issues, count


def _xml(raw: bytes):
    try:
        return etree.fromstring(raw, parser=etree.XMLParser(resolve_entities=False, no_network=True))
    except etree.XMLSyntaxError as exc:
        raise InputError("Invalid DOCX XML in an SI reference. Preserve valid OOXML in transforms and render again.") from exc


def _package(path: Path) -> tuple[dict, list]:
    try:
        with zipfile.ZipFile(path) as package:
            infos = package.infolist()
            if len(infos) != len({item.filename for item in infos}):
                raise InputError(f"Duplicate DOCX members in {path.name}. Restore a valid document.")
            return {item.filename: package.read(item.filename) for item in infos}, infos
    except (OSError, zipfile.BadZipFile) as exc:
        raise InputError(f"Cannot read {path.name} for SI references. Restore a valid DOCX.") from exc


def _caption_labels(raw: bytes, requested: set[str]) -> dict[str, dict]:
    root = _xml(raw)
    nodes = list(root.iter())
    positions = {node: index for index, node in enumerate(nodes)}
    result = {}
    for label in sorted(requested):
        bookmarks = root.xpath("//w:bookmarkStart[@w:name=$name]", namespaces=_NS, name=label)
        if len(bookmarks) != 1:
            raise InputError(f"SI reference {label!r} needs exactly one bookmark in the final SI; "
                             "restore its label, remove duplicates, and render again.")
        start = bookmarks[0]
        ident = start.get(f"{{{_NS['w']}}}id")
        if not ident:
            raise InputError(f"SI reference {label!r} has no bookmark id. Preserve SI bookmarks in transforms.")
        ends = root.xpath("//w:bookmarkEnd[@w:id=$id]", namespaces=_NS, id=ident)
        if len(ends) != 1 or positions[ends[0]] <= positions[start]:
            raise InputError(f"SI reference {label!r} has an invalid bookmark range. Preserve SI bookmarks in transforms.")
        first, last = positions[start], positions[ends[0]]
        enclosing_table = next(start.iterancestors(f"{{{_NS['w']}}}tbl"), None)
        captions = []
        for paragraph in root.xpath("//w:p", namespaces=_NS):
            text = "".join(node.text or "" for node in paragraph.iter(f"{{{_NS['w']}}}t")
                           if first < positions[node] < last
                           and not any(parent.tag == f"{{{_NS['w']}}}del" for parent in node.iterancestors()))
            match = _LEAD.match(text.strip())
            if not match:
                continue
            style = paragraph.find("w:pPr/w:pStyle", namespaces=_NS)
            caption_style = style is not None and style.get(f"{{{_NS['w']}}}val") in {
                "Caption", "ImageCaption", "TableCaption"}
            # Unstyled Quarto captions are siblings of the float's bookmarks;
            # nested data cells must not supply a caption-looking scientific value.
            direct = paragraph.getparent() is start.getparent() or paragraph in start.iterancestors()
            table = next(paragraph.iterancestors(f"{{{_NS['w']}}}tbl"), None)
            if direct or (caption_style and table is enclosing_table):
                captions.append(match)
        if len(captions) != 1:
            raise InputError(f"SI reference {label!r} needs one numbered Figure/Table caption inside its bookmark. "
                             "Use an English numbered top-level float and preserve its caption in transforms.")
        match = captions[0]
        expected = "Figure" if label.startswith("fig-") else "Table"
        if match[1] != expected:
            raise InputError(f"SI label {label!r} has a {match[1]} caption; correct its float type.")
        number = re.sub(r"\s+", "", match[2])
        result[label] = {"display": f"{expected} {number}", "bookmark_id": ident}
    return result


def resolve(main: Path, si: Path | None, *, active: bool) -> dict | None:
    """Resolve used hyperlinks only, after declared transforms and before sealing.

    All unrelated ZIP members stay byte-identical. No project source is written.
    """
    parts, infos = _package(main)
    pending, changed = [], {}
    for part in sorted(name for name in parts if name.startswith("word/") and name.endswith(".xml")):
        relpart = f"word/_rels/{Path(part).name}.rels"
        if part not in parts or relpart not in parts:
            continue
        root, rels = _xml(parts[part]), _xml(parts[relpart])
        targets = {rel.get("Id"): rel for rel in rels if rel.tag == _REL}
        for link in root.xpath("//w:hyperlink[@r:id]", namespaces=_NS):
            if any(parent.tag == f"{{{_NS['w']}}}del" for parent in link.iterancestors()):
                continue
            rel = targets.get(link.get(f"{{{_NS['r']}}}id"))
            if rel is None or not (rel.get("Target") or "").lower().startswith(SCHEME):
                continue
            if part not in {"word/document.xml", "word/footnotes.xml", "word/endnotes.xml"}:
                raise InputError(f"SI references in {part} are unsupported. Place them in the main body, "
                                 "footnotes or endnotes.")
            if not active:
                raise InputError("Rendered wongo-si links are supported only in the main manuscript "
                                 "with si_references: true in _journal.yml. Enable it or remove the link.")
            label = unquote(rel.get("Target")[len(SCHEME):])
            if not _LABEL.fullmatch(label):
                raise InputError(f"Invalid SI reference {label!r}. Use a fig- or tbl- label without query/fragment.")
            if not all(child.tag == f"{{{_NS['w']}}}r" and all(
                    node.tag in {f"{{{_NS['w']}}}rPr", f"{{{_NS['w']}}}t"} for node in child)
                       for child in link) or not len(link):
                raise InputError("Use plain text or emphasis as an SI link label; fields, images and equations "
                                 "cannot be replaced safely.")
            pending.append((label, part, link))
        changed[part] = (root, relpart, rels)
    if not pending:
        if not active:
            return None
        sha = hashlib.sha256(main.read_bytes()).hexdigest()
        return {"schema": "wongo-si-references/1", "si_sha256":
                hashlib.sha256(si.read_bytes()).hexdigest() if si is not None else None,
                "main_before": sha, "main_after": sha, "references": []}
    if si is None:
        raise InputError("Rendered SI references require si.qmd. Restore the SI or remove those links.")
    si_parts, _ = _package(si)
    if "word/document.xml" not in si_parts:
        raise InputError("The final SI has no document.xml. Preserve a valid SI DOCX in transforms.")
    labels = _caption_labels(si_parts["word/document.xml"], {item[0] for item in pending})
    before = hashlib.sha256(main.read_bytes()).hexdigest()
    references = []
    for label, part, link in pending:
        run = etree.Element(f"{{{_NS['w']}}}r")
        props = link[0].find("w:rPr", namespaces=_NS)
        if props is not None:
            props = copy.deepcopy(props)
            style = props.find("w:rStyle", namespaces=_NS)
            if style is not None and style.get(f"{{{_NS['w']}}}val") == "Hyperlink":
                props.remove(style)
            run.append(props)
        etree.SubElement(run, f"{{{_NS['w']}}}t").text = labels[label]["display"]
        run.tail = link.tail
        link.getparent().replace(link, run)
        references.append({"label": label, "part": part, **labels[label]})
    for part, (root, relpart, rels) in changed.items():
        if not any(item[1] == part for item in pending):
            continue
        used = {value for node in root.iter() for value in node.attrib.values()}
        for rel in list(rels):
            if (rel.get("Target") or "").lower().startswith(SCHEME) and rel.get("Id") not in used:
                rels.remove(rel)
        parts[part] = etree.tostring(root, encoding="UTF-8", xml_declaration=True, standalone=True)
        parts[relpart] = etree.tostring(rels, encoding="UTF-8", xml_declaration=True, standalone=True)
    with zipfile.ZipFile(main, "w") as package:
        for info in infos:
            package.writestr(info, parts[info.filename])
    return {"schema": "wongo-si-references/1", "si_sha256": hashlib.sha256(si.read_bytes()).hexdigest(),
            "main_before": before, "main_after": hashlib.sha256(main.read_bytes()).hexdigest(),
            "references": references}
