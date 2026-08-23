#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["PyYAML>=6"]
# ///
"""Extract coauthor tracked changes/comments from a DOCX into a merge worksheet.

Usage: roundtrip.py <coauthor.docx> [--project DIR]

Runs pandoc (via quarto) with --track-changes=all, parses insertion/deletion/
comment spans with author attribution, aligns each change to a line of the
current index.qmd (one-sentence-per-line invariant), and writes
decisions/merge-<date>-<stem>.md. NEVER applies changes: every worksheet row
starts as 'disposition: PENDING' for interactive review (SKILL.md S4 rules).
"""
from __future__ import annotations

import argparse
import difflib
import re
import subprocess
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from wongo.engine import checks as mslib

SPAN_RE = re.compile(
    r"\[(?P<text>[^\][]*)\]\{\.(?P<kind>insertion|deletion|comment-start|comment-end)(?P<attrs>[^}]*)\}",
    re.DOTALL,
)
ATTR_RE = re.compile(r'([\w-]+)="([^"]*)"')


@dataclass
class Change:
    kind: str      # insertion | deletion | replacement | comment | unparsed
    author: str    # "?" when unknown (always "?" for unparsed)
    old: str       # deleted text / annotated span ("" for unparsed)
    new: str       # inserted text / comment note ("" for unparsed)
    context: str   # nearby original prose, for alignment / manual lookup


def _attrs(raw: str) -> dict:
    return dict(ATTR_RE.findall(raw))


def _plain(md: str) -> str:
    """Original text: deletions kept, insertions dropped, markers removed."""
    def repl(m):
        return m.group("text") if m.group("kind") == "deletion" else ""
    return SPAN_RE.sub(repl, md)


def _context_before(md: str, pos: int) -> str:
    """Clean prose immediately preceding `pos`, for worksheet display.

    Plain-ifies the *entire* prefix before slicing to the last 60 chars —
    slicing a raw character window first (then plain-ifying just that slice)
    can start mid-span, leaking a partial ...}{.attrs="..." fragment into the
    context shown to the human reviewer. Whitespace (including the blank
    line pandoc emits between paragraphs) is collapsed to single spaces so
    the worksheet's "- context: ...…" stays a single markdown list item
    instead of a stray blank line splitting it into a new paragraph.
    """
    return " ".join(_plain(md[:pos]).split())[-60:]


def extract_changes(md: str) -> list[Change]:
    # Each entry is (match_start, Change) so the final ordering reflects where
    # each change actually occurs in `md`, rather than re-searching for the
    # change's own (possibly-transformed, possibly-duplicated) text after the
    # fact — a `md.find(c.old or c.new)` re-search would misorder or
    # mis-locate changes whose old/new text recurs elsewhere in the document.
    changes: list[tuple[int, Change]] = []
    matches = list(SPAN_RE.finditer(md))
    used: set[int] = set()

    # comments: pair comment-start with its comment-end, capture annotated span
    for i, m in enumerate(matches):
        if m.group("kind") != "comment-start":
            continue
        attrs = _attrs(m.group("attrs"))
        cid = attrs.get("id", "")
        end = next(
            (e for e in matches if e.group("kind") == "comment-end"
             and _attrs(e.group("attrs")).get("id") == cid),
            None,
        )
        annotated = md[m.end():end.start()] if end is not None else ""
        # Confirmed against real `quarto pandoc --track-changes=all` output
        # (quarto 1.9.38 / pandoc 3.8.3): the reviewer's note text is the
        # *content* of the comment-start span itself; comment-end is always
        # empty (`[]{.comment-end id="N"}`). The `comment` attribute fallback
        # is kept as a defensive no-op in case some other pandoc build emits
        # the note as an attribute instead. See references/quarto-docx-quirks.md.
        note = m.group("text") or attrs.get("comment", "")
        changes.append((m.start(), Change(
            kind="comment", author=attrs.get("author", "?"),
            old=_plain(annotated).strip(), new=note.strip(),
            context=_context_before(md, m.start()),
        )))
        used.add(i)
        if end is not None:
            used.add(matches.index(end))

    # insertions/deletions, pairing adjacent del+ins into replacements
    i = 0
    while i < len(matches):
        if i in used:
            i += 1
            continue
        m = matches[i]
        kind = m.group("kind")
        if kind not in ("insertion", "deletion"):
            i += 1
            continue
        attrs = _attrs(m.group("attrs"))
        context = _context_before(md, m.start())
        nxt = matches[i + 1] if i + 1 < len(matches) else None
        if (
            kind == "deletion" and nxt is not None and (i + 1) not in used
            and nxt.group("kind") == "insertion"
            and md[m.end():nxt.start()].strip() == ""
            # same author only: an adjacent del+ins by *different* authors is
            # two independent edits (each needs its own disposition), not one
            # person's replacement
            and attrs.get("author") == _attrs(nxt.group("attrs")).get("author")
        ):
            changes.append((m.start(), Change(
                kind="replacement", author=attrs.get("author", "?"),
                old=m.group("text"), new=nxt.group("text"), context=context,
            )))
            used.update({i, i + 1})
            i += 2
            continue
        if kind == "insertion":
            changes.append((m.start(), Change("insertion", attrs.get("author", "?"), "", m.group("text"), context)))
        else:
            changes.append((m.start(), Change("deletion", attrs.get("author", "?"), m.group("text"), "", context)))
        used.add(i)
        i += 1

    # Safety net: SPAN_RE cannot match a span whose bracket content itself
    # contains square brackets — e.g. an inserted citation
    # `[cited work [@doe2020]]{.insertion ...}` — realistic in manuscripts.
    # Rather than letting such an edit vanish silently (which would break this
    # tool's core promise that no coauthor change is dropped without a trace),
    # scan for raw change markers the regex did not consume and surface each
    # as an 'unparsed' row the human must resolve against the DOCX directly.
    # See references/quarto-docx-quirks.md (2026-07-03).
    covered = [(m.start(), m.end()) for m in matches]
    for marker in ("{.insertion", "{.deletion", "{.comment-start"):
        pos = md.find(marker)
        while pos != -1:
            if not any(s <= pos < e for s, e in covered):
                changes.append((pos, Change(
                    kind="unparsed", author="?", old="", new="",
                    context=_context_before(md, pos),
                )))
            pos = md.find(marker, pos + 1)

    changes.sort(key=lambda pair: pair[0])
    return [c for _, c in changes]


def locate(change: Change, qmd_lines: list[str]) -> int | None:
    """Best-matching 1-based line in the .qmd for this change's original text.

    Front matter (YAML header) is excluded from candidates via
    mslib.split_front_matter so coauthor prose never spuriously matches
    title/author/abstract metadata; returned indices still index into the
    full qmd_lines list (front matter included), as documented in the
    interface contract.

    Unparsed changes always return None: their context ends with the raw
    unmatched span text (useful for a human, junk for difflib), so any line
    it "matched" would be a spurious guess — worse than an honest UNMATCHED.
    (Note the guard must be explicit: the needle is built from context+old,
    and an unparsed change's *context* is non-empty, so without the guard the
    fuzzy match could still fire.)
    """
    if change.kind == "unparsed":
        return None
    full_text = "\n".join(qmd_lines)
    _, body = mslib.split_front_matter(full_text)
    fm_line_count = len(full_text.splitlines()) - len(body.splitlines())

    needle = " ".join(f"{change.context} {change.old}".split())
    if not needle.strip():
        needle = change.new
    best_line, best_score = None, 0.0
    for idx, line in enumerate(qmd_lines, start=1):
        if idx <= fm_line_count:
            continue
        if not line.strip() or line.lstrip().startswith(("#", "---", "<!--", "!", "```")):
            continue
        score = difflib.SequenceMatcher(None, needle.lower(), line.lower()).ratio()
        if change.old and change.old.strip().lower() in line.lower():
            score += 0.5
        if score > best_score:
            best_line, best_score = idx, score
    return best_line if best_score >= 0.3 else None


def write_worksheet(changes, locations, out_path: Path, source_name: str) -> None:
    lines = [
        f"# Merge worksheet — {source_name} — {date.today().isoformat()}",
        "",
        "Review each item; set disposition to one of: apply / reject: <reason> /",
        "fix-code (edit inside auto-generated output) / needs-PI. Apply to the",
        ".qmd only AFTER every disposition is approved (quarto-manuscript-sci S4).",
        "Items marked 'unparsed' could not be machine-extracted: open the source",
        "DOCX at the quoted context and review that change by hand before setting",
        "a disposition — do NOT treat an unparsed row as ignorable.",
        "",
    ]
    for n, (c, loc) in enumerate(zip(changes, locations), start=1):
        if c.kind == "unparsed":
            lines += [
                f"## {n}. unparsed — {c.author}",
                "- PARSER COULD NOT EXTRACT THIS CHANGE — open the DOCX and "
                "review this location manually.",
                f"- location: index.qmd:{loc if loc else 'UNMATCHED — find manually'}",
                f"- context: …{c.context.strip()}…",
                "- disposition: PENDING",
                "",
            ]
            continue
        lines += [
            f"## {n}. {c.kind} — {c.author}",
            f"- location: index.qmd:{loc if loc else 'UNMATCHED — find manually'}",
            f"- old: {c.old or '—'}",
            f"- new: {c.new or '—'}",
            f"- context: …{c.context.strip()}…",
            "- disposition: PENDING",
            "",
        ]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("docx")
    ap.add_argument("--project", default=".")
    args = ap.parse_args(argv)
    project = Path(args.project).resolve()
    docx_path = Path(args.docx).resolve()

    if not docx_path.exists():
        raise SystemExit(f"coauthor docx not found: {docx_path}")
    index_qmd = project / "index.qmd"
    if not index_qmd.exists():
        raise SystemExit(f"project index.qmd not found: {index_qmd}")

    # --wrap=none: with the default auto-wrap, pandoc can break a long
    # insertion/deletion span's text (or its attribute list) across a hard
    # line boundary, embedding a literal "\n" inside the regex-captured text.
    # Confirmed via a live run against the synthetic fixture; see
    # references/quarto-docx-quirks.md (2026-07-03).
    try:
        md = subprocess.run(
            ["quarto", "pandoc", "--track-changes=all", "--wrap=none", str(docx_path), "-t", "markdown"],
            capture_output=True, text=True, check=True,
        ).stdout
    except subprocess.CalledProcessError as e:
        raise SystemExit(f"pandoc extraction failed: {e.stderr.strip()[-500:]}")

    changes = extract_changes(md)
    qmd_lines = index_qmd.read_text(encoding="utf-8").splitlines()
    locations = [locate(c, qmd_lines) for c in changes]

    out = project / "decisions" / f"merge-{date.today():%Y%m%d}-{docx_path.stem}.md"
    write_worksheet(changes, locations, out, docx_path.name)
    print(f"wrote {out} ({len(changes)} changes; NONE applied — review dispositions first)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
