"""wongo.engine.diff — tracked-changes stamping for revision submissions (S6).

Given the originally submitted DOCX and a revised render, produce a copy of
the revised document whose differences appear as REAL Word track changes
(`w:ins` / `w:del`), attributed to a chosen author/date. Journals that demand
a marked-up revision get one without a manual Word Compare session.

Scope (v2): body-level paragraphs made of text runs and hyperlinks. Word-level
diffs within replaced paragraphs; whole-paragraph insertions/deletions fully
tracked. Each token keeps the run properties (italics, superscripts, ...) of
the run it came from, and tokens that sit inside a `w:hyperlink` (Quarto emits
every crossref and linked citation this way) are rebuilt inside a copy of
that hyperlink, so links survive exactly once and in reading order.

Changed paragraphs containing fields, drawings, footnote references, tabs,
breaks, math, existing tracked changes, or any other rich OOXML are not
rewritten and are REPORTED (`rich_paragraphs_skipped`) rather than flattened
or duplicated. TABLES are deliberately left untouched (their content is
data-driven from .qmd chunks, and merging table diffs is a Word-Compare-grade
problem); if any table text differs between the two documents — including
data tables NESTED inside Quarto's 1x1 float wrappers — this is REPORTED
(`tables_differ`) so the human knows to run Word Compare.

The emitted markup is the exact syntax `quarto pandoc --track-changes=all`
parses (see docs/docx-quirks.md), so `wongo roundtrip` can extract our own
output back into a merge worksheet.

Implementation notes:
- All edits happen IN PLACE on the revised document's own paragraph
  elements — never clone-and-remove — so every paragraph element stays live
  in the lxml tree across the whole opcode walk.
- Deletions are materialized as NEW paragraphs (the revised doc no longer
  contains them) inserted at the aligned position; they carry `w:delText`,
  never `w:t`, per ECMA-376 tracked-deletion semantics.
- Hyperlink copies for deleted text come from the ORIGINAL document, whose
  relationship ids mean nothing in the revised package; only anchor-only
  (internal crossref) hyperlinks are copied from that side.
- Revision ids start above the highest id already present in the revised
  document so they never collide with pre-existing tracked changes.
"""
from __future__ import annotations

import copy
import re
from datetime import UTC, datetime
from difflib import SequenceMatcher
from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from wongo.errors import InputError

_TOKEN_RE = re.compile(r"\s+|\S+")
_RUN_CHILDREN = {qn("w:rPr"), qn("w:t")}
# zero-width markers that carry no text and survive a rebuild untouched
_ZERO_WIDTH = {qn("w:bookmarkStart"), qn("w:bookmarkEnd"), qn("w:proofErr")}
_REBUILT = {qn("w:r"), qn("w:ins"), qn("w:del"), qn("w:hyperlink")}


def _norm(text: str) -> str:
    return " ".join(text.split())


# ---------------------------------------------------------------------------
# Reading paragraphs into formatted tokens


def _run_segment(run, container):
    if any(child.tag not in _RUN_CHILDREN for child in run):
        return None
    text = "".join(t.text or "" for t in run.findall(qn("w:t")))
    return (text, run.find(qn("w:rPr")), container)


def _segments(p_el) -> list | None:
    """[(text, rPr|None, hyperlink|None)] per run of a rebuildable paragraph,
    or None when the paragraph holds rich OOXML this writer cannot recreate."""
    segments = []
    for child in p_el:
        if child.tag == qn("w:pPr") or child.tag in _ZERO_WIDTH:
            continue
        if child.tag == qn("w:r"):
            seg = _run_segment(child, None)
            if seg is None:
                return None
            segments.append(seg)
        elif child.tag == qn("w:hyperlink"):
            for sub in child:
                if sub.tag in _ZERO_WIDTH:
                    continue
                if sub.tag != qn("w:r"):
                    return None
                seg = _run_segment(sub, child)
                if seg is None:
                    return None
                segments.append(seg)
        else:
            return None
    return segments


def _tokens(segments) -> list[tuple[str, object, object]]:
    """Split each run's text into word/whitespace tokens that remember the
    run properties and hyperlink container they came from."""
    out = []
    for text, rpr, container in segments:
        for tok in _TOKEN_RE.findall(text):
            out.append((tok, rpr, container))
    return out


def _is_rebuildable(paragraph) -> bool:
    return _segments(paragraph._p) is not None


# ---------------------------------------------------------------------------
# Writing tracked runs back


def _make_run(text: str, rpr_template, *, deleted: bool):
    r = OxmlElement("w:r")
    if rpr_template is not None:
        r.append(copy.deepcopy(rpr_template))
    target = OxmlElement("w:delText") if deleted else OxmlElement("w:t")
    if text != text.strip():
        target.set(qn("xml:space"), "preserve")
    target.text = text
    r.append(target)
    return r


def _wrap(kind: str, runs: list, author: str, date: str, counter: list[int]):
    wrap = OxmlElement(f"w:{kind}")
    wrap.set(qn("w:id"), str(counter[0]))
    counter[0] += 1
    wrap.set(qn("w:author"), author)
    wrap.set(qn("w:date"), date)
    for r in runs:
        wrap.append(r)
    return wrap


def _strip_content(p_el) -> None:
    """Remove runs, hyperlinks, and tracking wrappers; keep pPr and markers."""
    for child in list(p_el):
        if child.tag in _REBUILT:
            p_el.remove(child)


def _hyperlink_shell(container):
    shell = OxmlElement("w:hyperlink")
    for key, value in container.attrib.items():
        shell.set(key, value)
    return shell


def _safe_original_container(container):
    """A hyperlink copied from the original document is only safe when it is
    anchor-only: an r:id would dangle in the revised package."""
    if container is None or container.get(qn("r:id")) is not None:
        return None
    return container


def _emit(p_el, items, author: str, date: str, counter: list[int]) -> None:
    """Append `items` = [(kind, token, rPr, container)] to paragraph `p_el`,
    grouping consecutive same-kind tokens into one w:ins/w:del and
    consecutive same-container tokens into one rebuilt hyperlink."""
    groups: list[tuple[str, object, list]] = []  # (kind, container, [(tok, rPr)])
    for kind, tok, rpr, container in items:
        if groups and groups[-1][0] == kind and groups[-1][1] is container:
            groups[-1][2].append((tok, rpr))
        else:
            groups.append((kind, container, [(tok, rpr)]))

    current_container, current_shell = None, None
    for kind, container, toks in groups:
        runs = [_make_run(tok, rpr, deleted=(kind == "del")) for tok, rpr in toks]
        element = runs if kind == "equal" else [_wrap(kind, runs, author, date, counter)]
        if container is None:
            parent = p_el
            current_container, current_shell = None, None
        else:
            if container is not current_container:
                current_shell = _hyperlink_shell(container)
                p_el.append(current_shell)
                current_container = container
            parent = current_shell
        for el in element:
            parent.append(el)


# ---------------------------------------------------------------------------
# Main entry


def _max_revision_id(doc) -> int:
    ids = [0]
    for el in doc.element.body.iter(qn("w:ins"), qn("w:del")):
        try:
            ids.append(int(el.get(qn("w:id")) or 0))
        except ValueError:
            continue
    return max(ids)


def _table_text(doc) -> str:
    """Every text node inside every table, nested tables included (Quarto
    nests data tables inside 1x1 float wrappers, invisible to doc.tables)."""
    return "\n".join(
        t.text or ""
        for tbl in doc.element.body.iter(qn("w:tbl"))
        for t in tbl.iter(qn("w:t"))
    )


def diff_documents(original: Path, revised: Path, out: Path,
                   author: str = "Revised manuscript",
                   date: str | None = None) -> dict:
    """Stamp tracked changes into `revised` vs `original`; save to `out`.

    Returns a report dict with insertion/deletion counts, the
    `tables_differ` flag, and `rich_paragraphs_skipped`. Neither input file
    is modified.
    """
    original = Path(original)
    revised = Path(revised)
    out = Path(out)
    if out.resolve() in {original.resolve(), revised.resolve()}:
        raise InputError("output DOCX must differ from both input paths")

    if date is None:
        date = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    doc_orig = Document(str(original))
    doc_rev = Document(str(revised))

    counter = [max(9000, _max_revision_id(doc_rev) + 1)]
    report = {"inserted_words": 0, "deleted_words": 0,
              "inserted_paragraphs": 0, "deleted_paragraphs": 0,
              "tables_differ": False, "rich_paragraphs_skipped": 0}

    o_paras = doc_orig.paragraphs
    o_texts = [_norm(p.text or "") for p in o_paras]
    r_paras = doc_rev.paragraphs
    r_texts = [_norm(p.text or "") for p in r_paras]

    def count_words(tokens) -> int:
        return len([t for t in tokens if t[0].strip()])

    def skip_rich(*paragraphs) -> bool:
        if all(_is_rebuildable(p) for p in paragraphs):
            return False
        report["rich_paragraphs_skipped"] += 1
        return True

    def mark_inserted_inplace(p) -> None:
        """Wrap ALL of revised paragraph p's content as insertions, in place."""
        if skip_rich(p):
            return
        tokens = _tokens(_segments(p._p))
        _strip_content(p._p)
        _emit(p._p, [("ins", tok, rpr, cont) for tok, rpr, cont in tokens],
              author, date, counter)
        report["inserted_words"] += count_words(tokens)
        report["inserted_paragraphs"] += 1

    def make_deleted_para(src_para):
        """New paragraph carrying the original paragraph as a full deletion."""
        if skip_rich(src_para):
            return None
        new_p = OxmlElement("w:p")
        src_ppr = src_para._p.find(qn("w:pPr"))
        if src_ppr is not None:
            new_p.append(copy.deepcopy(src_ppr))
        tokens = _tokens(_segments(src_para._p))
        _emit(new_p, [("del", tok, rpr, _safe_original_container(cont))
                      for tok, rpr, cont in tokens], author, date, counter)
        report["deleted_words"] += count_words(tokens)
        report["deleted_paragraphs"] += 1
        return new_p

    def rebuild_word_diff(p, old_para) -> None:
        """Rewrite revised paragraph p as equal/ins/del token runs vs old_para."""
        old_tokens = _tokens(_segments(old_para._p))
        new_tokens = _tokens(_segments(p._p))
        items: list = []
        sm_w = SequenceMatcher(a=[t[0] for t in old_tokens],
                               b=[t[0] for t in new_tokens], autojunk=False)
        for op, i1, i2, j1, j2 in sm_w.get_opcodes():
            if op == "equal":
                items += [("equal", tok, rpr, cont) for tok, rpr, cont in new_tokens[j1:j2]]
                continue
            if op in ("delete", "replace"):
                # deleted words sit in whatever link the preceding revised
                # text is in (schema allows w:del inside w:hyperlink), so a
                # link whose text changed is not split in two
                prev_cont = items[-1][3] if items else None
                items += [("del", tok, rpr, prev_cont) for tok, rpr, _ in old_tokens[i1:i2]]
                report["deleted_words"] += count_words(old_tokens[i1:i2])
            if op in ("insert", "replace"):
                items += [("ins", tok, rpr, cont) for tok, rpr, cont in new_tokens[j1:j2]]
                report["inserted_words"] += count_words(new_tokens[j1:j2])
        _strip_content(p._p)
        _emit(p._p, items, author, date, counter)

    body = doc_rev.element.body
    sect_pr = body.find(qn("w:sectPr"))

    sm = SequenceMatcher(a=o_texts, b=r_texts, autojunk=False)
    idx_r = 0
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            idx_r += j2 - j1
        elif op == "insert":
            for jp in range(j1, j2):
                mark_inserted_inplace(r_paras[jp])
            idx_r += j2 - j1
        elif op == "delete":
            anchor = (r_paras[idx_r]._p if idx_r < len(r_paras)
                      else (sect_pr if sect_pr is not None else None))
            for ip in range(i1, i2):
                tracked = make_deleted_para(o_paras[ip])
                if tracked is None:
                    continue
                if anchor is not None:
                    anchor.addprevious(tracked)
                else:
                    body.append(tracked)
        elif op == "replace":
            olds = o_paras[i1:i2]
            pairs = min(len(olds), j2 - j1)
            for k in range(pairs):
                p = r_paras[j1 + k]
                if skip_rich(olds[k], p):
                    continue
                rebuild_word_diff(p, olds[k])
            if len(olds) > pairs:  # surplus originals -> deletions after block
                last = r_paras[j2 - 1]._p
                for ip in range(i1 + pairs, i2):
                    tracked = make_deleted_para(olds[ip])
                    if tracked is None:
                        continue
                    last.addnext(tracked)
                    last = tracked
            for jp in range(j1 + pairs, j2):  # surplus revised -> insertions
                mark_inserted_inplace(r_paras[jp])
            idx_r += j2 - j1

    # Tables: untouched by design, but surface any difference (nested too).
    try:
        report["tables_differ"] = _table_text(doc_orig) != _table_text(doc_rev)
    except Exception:  # noqa: BLE001 — reporting must never fail the stamp
        report["tables_differ"] = False

    out.parent.mkdir(parents=True, exist_ok=True)
    doc_rev.save(str(out))
    return report
