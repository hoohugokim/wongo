"""Extract coauthor tracked changes/comments from a DOCX into a merge worksheet.

`extract()` runs pandoc (via quarto) with --track-changes=all, parses
insertion/deletion/comment spans with author attribution, aligns each change to
a line of the source .qmd (default index.qmd; one-sentence-per-line invariant),
and writes decisions/merge-<date>-<stem>.md. NEVER applies changes: every row
starts as 'disposition: PENDING'; people decide rows with `wongo review` (or the
agent with `wongo worksheet set`), and approved rows are applied to the .qmd
outside wongo.
"""
from __future__ import annotations

import difflib
import re
import subprocess
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from wongo import toolchain
from wongo.engine import checks as mslib
from wongo.errors import InputError, ToolchainError
from wongo.textio import read_text, require_docx

SPAN_RE = re.compile(
    r"\[(?P<text>[^\][]*)\]\{\.(?P<kind>insertion|deletion|comment-start|comment-end)(?P<attrs>[^}]*)\}",
    re.DOTALL,
)
ATTR_RE = re.compile(r'([\w-]+)="([^"]*)"')
WORD_RE = re.compile(r"\w+")  # Unicode-aware: Hangul words count as words
CONTEXT_CHARS = 60  # rendered text kept before each change
ANCHOR_WORDS = 8    # at most this many context words are matched against a line


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
    return " ".join(_plain(md[:pos]).split())[-CONTEXT_CHARS:]


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


def _words(text: str) -> list[str]:
    return WORD_RE.findall(text.lower())


def _contains_run(words: list[str], run: list[str]) -> bool:
    """Whether `run` occurs in `words` as consecutive words."""
    n = len(run)
    return any(words[i:i + n] == run for i in range(len(words) - n + 1))


def _tail_run(context: list[str], words: list[str], then: list[str] | None = None) -> int:
    """How many of the context's last words (at most ANCHOR_WORDS) `words`
    holds consecutively, followed directly by `then`; 0 if none."""
    for k in range(min(len(context), ANCHOR_WORDS), 0, -1):
        if _contains_run(words, context[-k:] + (then or [])):
            return k
    return 0


def _comment_lines(lines: list[str]) -> set[int]:
    """1-based numbers of the lines inside HTML comments. Comments are never
    rendered, so no coauthor edited them; prose before an inline `<!--` keeps
    its line a candidate."""
    inside: set[int] = set()
    is_open = False
    for idx, line in enumerate(lines, start=1):
        if is_open:
            inside.add(idx)
            is_open = "-->" not in line
            continue
        start = line.find("<!--")
        if start == -1:
            continue
        end = line.find("-->", start + 4)
        if not line[:start].strip() and (end == -1 or not line[end + 3:].strip()):
            inside.add(idx)
        is_open = end == -1
    return inside


def _anchor_strength(context: list[str], old: list[str], words: list[str]) -> int:
    """How surely a line is where the change happened, from exact word runs:
    the context's last words followed by the old text, then a context tail of
    three or more words (all an insertion has), then the old text alone, then a
    two-word tail. 0 means no anchor; the fuzzy score decides."""
    joined = _tail_run(context, words, old) if old else 0
    if joined:
        return 100 + joined
    tail = _tail_run(context, words)
    if tail >= 3:
        return 50 + tail
    if old and _contains_run(words, old):
        return 20 + tail
    return 10 if tail == 2 else 0


def locate(change: Change, qmd_lines: list[str]) -> int | None:
    """Best-matching 1-based line in the .qmd for this change's original text.

    Candidates exclude the front matter (via mslib.split_front_matter, so
    coauthor prose never spuriously matches title/author/abstract metadata),
    lines inside HTML comments, headings and other markup lines; returned
    indices still index into the full qmd_lines list, as documented in the
    interface contract.

    Each candidate is first judged by exact word runs (_anchor_strength): the
    rendered context ends right where the change happened, so its last words,
    followed by any old text, pin the line even when an unrelated line looks
    more similar overall. The difflib similarity of context plus old text
    breaks ties, and decides alone when nothing anchors (e.g. a context that
    is mostly a rendered citation absent from the source).

    Unparsed changes always return None: their context ends with the raw
    unmatched span text (useful for a human, junk for matching), so any line
    it "matched" would be a spurious guess — worse than an honest UNMATCHED.
    The guard must stay explicit: that context is non-empty and could still
    anchor or fuzzy-match a line.
    """
    if change.kind == "unparsed":
        return None
    full_text = "\n".join(qmd_lines)
    _, body = mslib.split_front_matter(full_text)
    fm_line_count = len(full_text.splitlines()) - len(body.splitlines())
    comments = _comment_lines(qmd_lines)

    needle = " ".join(f"{change.context} {change.old}".split())
    if not needle.strip():
        needle = change.new
    context = _words(change.context)
    if len(change.context) >= CONTEXT_CHARS:
        context = context[1:]  # the window may start mid-word
    old = _words(change.old)

    best_line, best_key = None, (0, 0.0)
    for idx, line in enumerate(qmd_lines, start=1):
        if idx <= fm_line_count or idx in comments:
            continue
        if not line.strip() or line.lstrip().startswith(("#", "---", "<!--", "!", "```")):
            continue
        score = difflib.SequenceMatcher(None, needle.lower(), line.lower()).ratio()
        if change.old and change.old.strip().lower() in line.lower():
            score += 0.5
        key = (_anchor_strength(context, old, _words(line)), score)
        if key > best_key:
            best_line, best_key = idx, key
    strength, score = best_key
    return best_line if strength or score >= 0.3 else None


def write_worksheet(
    changes, locations, out_path: Path, source_name: str, qmd_name: str = "index.qmd"
) -> None:
    lines = [
        f"# Merge worksheet — {source_name} — {date.today().isoformat()}",
        "",
        "Review each item; set disposition to one of: apply / reject: <reason> /",
        "fix-code (edit inside auto-generated output) / needs-PI. Decide rows with",
        f"`wongo review {out_path.parent.name}/{out_path.name}` (or `wongo worksheet set`),",
        f"then run `wongo worksheet lint {out_path.parent.name}/{out_path.name}`; apply",
        "approved rows to the .qmd only",
        "after lint passes. wongo never edits the .qmd.",
        "Items marked 'unparsed' could not be machine-extracted: open the source",
        "DOCX at the quoted context and review that change by hand before setting",
        "a disposition — do NOT treat an unparsed row as ignorable.",
        "",
    ]
    for n, (c, loc) in enumerate(zip(changes, locations), start=1):
        if c.kind == "unparsed":
            lines += [
                f"## {n}. unparsed — {c.author}",
                (
                    "- PARSER COULD NOT EXTRACT THIS CHANGE — open the DOCX and "
                    "review this location manually."
                ),
                f"- location: {qmd_name}:{loc if loc else 'UNMATCHED — find manually'}",
                f"- context: …{c.context.strip()}…",
                "- disposition: PENDING",
                "",
            ]
            continue
        lines += [
            f"## {n}. {c.kind} — {c.author}",
            f"- location: {qmd_name}:{loc if loc else 'UNMATCHED — find manually'}",
            f"- old: {c.old or '—'}",
            f"- new: {c.new or '—'}",
            f"- context: …{c.context.strip()}…",
            "- disposition: PENDING",
            "",
        ]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def available_worksheet_path(
    project: Path, source_stem: str, day: date | None = None
) -> Path:
    """Choose a worksheet path without overwriting an earlier review.

    A worksheet may already contain human dispositions, so repeated
    extraction of the same DOCX creates ``-2``, ``-3``, ... rather than
    silently replacing the first file.
    """
    day = day or date.today()
    directory = Path(project) / "decisions"
    base = directory / f"merge-{day:%Y%m%d}-{source_stem}.md"
    if not base.exists():
        return base
    suffix = 2
    while True:
        candidate = base.with_name(f"{base.stem}-{suffix}{base.suffix}")
        if not candidate.exists():
            return candidate
        suffix += 1


@dataclass
class RoundtripResult:
    worksheet: Path
    changes: int
    kinds: dict[str, int] = field(default_factory=dict)
    unmatched: int = 0
    unparsed: int = 0


def pandoc_markdown(docx_path: Path) -> str:
    """The coauthor DOCX as pandoc markdown with tracked changes as spans.

    --wrap=none: with auto-wrap pandoc can break a long span's text or its
    attribute list across lines (docs/docx-quirks.md, 2026-07-03). pandoc
    writes UTF-8 whatever the locale, so decode it as UTF-8: the locale code
    page (CP949 on Korean Windows) garbles or crashes on Hangul.
    """
    cmd = [*toolchain.quarto_command(), "pandoc", "--track-changes=all", "--wrap=none",
           str(docx_path), "-t", "markdown"]
    try:
        done = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", check=True)
    except subprocess.CalledProcessError as exc:
        raise ToolchainError(f"pandoc extraction failed: {exc.stderr.strip()[-500:]}") from exc
    except OSError as exc:
        raise ToolchainError(f"could not run Quarto ({cmd[0]}): {exc}") from exc
    return done.stdout


def extract(docx: Path, project: Path, qmd: str = "index.qmd") -> RoundtripResult:
    """Write a PENDING merge worksheet for a coauthor's DOCX; never edits .qmd."""
    project = Path(project).resolve()
    docx_path = Path(docx).resolve()
    if not docx_path.exists():
        raise InputError(f"coauthor docx not found: {docx_path}")
    source = project / qmd
    if not source.exists():
        raise InputError(f"project source not found: {source} (use --qmd si.qmd for an SI render)")

    require_docx(docx_path)
    qmd_text = read_text(source)
    mslib.split_front_matter(qmd_text, source=qmd)  # a front-matter typo names its line
    changes = extract_changes(pandoc_markdown(docx_path))
    qmd_lines = qmd_text.splitlines()
    locations = [locate(c, qmd_lines) for c in changes]
    out = available_worksheet_path(project, docx_path.stem)
    write_worksheet(changes, locations, out, docx_path.name, qmd_name=qmd)
    kinds: dict[str, int] = {}
    for c in changes:
        kinds[c.kind] = kinds.get(c.kind, 0) + 1
    return RoundtripResult(
        worksheet=out,
        changes=len(changes),
        kinds=kinds,
        unmatched=sum(1 for c, loc in zip(changes, locations) if loc is None and c.kind != "unparsed"),
        unparsed=kinds.get("unparsed", 0),
    )
