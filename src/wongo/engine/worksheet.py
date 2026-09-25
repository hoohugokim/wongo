"""Merge worksheet model: read, check and edit a `wongo roundtrip` worksheet losslessly.

`wongo roundtrip` writes ``decisions/merge-<date>-<stem>.md`` with one row per
coauthor change, every row starting as ``- disposition: PENDING``. A person
(``wongo review``) or the agent (``wongo worksheet set``) then decides each row.
This module reads the worksheet back without disturbing a byte it was not asked
to change: ``serialize(parse(raw)) == raw`` for any input (LF or CRLF, with or
without a BOM or a final newline, hand edits and unknown lines included).

Nothing here writes a .qmd. Approved rows are applied to the manuscript by the
person or the agent, outside wongo (the rule in wongo.engine.roundtrip).

Row layout, as roundtrip.write_worksheet writes it::

    ## 3. replacement — Jane Doe
    - location: index.qmd:95          (or index.qmd:UNMATCHED — find manually)
    - old: …
    - new: …
    - context: …
    - disposition: PENDING

Lines right after the disposition line that are not blank, not ``- key: value``
fields and not headings continue the disposition (an agent's long rationale).

Disposition grammar (keywords are case-insensitive)::

    PENDING
    PROPOSED <final>               the agent's proposal; the rest is its rationale
    apply | fix-code | needs-PI    each may add a note, e.g. "apply — prose only"
    reject: <reason>               the reason is required
"""
from __future__ import annotations

import os
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from wongo.errors import InputError, WongoError
from wongo.textio import detect_newline, read_text, write_text_atomic

BOM = b"\xef\xbb\xbf"
DEFAULT_QMD = "index.qmd"
DECISIONS = ("apply", "reject", "fix-code", "needs-PI")
STATES = ("pending", "proposed", "final", "invalid")
GRAMMAR = (
    "use apply, fix-code or needs-PI (each may add ' — note'), reject: <reason>, "
    "PROPOSED <one of those>, or PENDING"
)

# The writer uses an em dash; a hand-added row may use an en dash or hyphen.
ROW_RE = re.compile(r"^## ([0-9]+)\. (\S+) [—–-](?:[ \t](.*))?$")
FIELD_RE = re.compile(r"^- ([a-z][a-z-]*):[ \t]*(.*)$")
# Inline code whose value is generated at render time (knitr `r`, Quarto {r}/{python}).
INLINE_CODE_RE = re.compile(r"`(?:r[ \t]|\{(?:r|python)\})")

_HEADING_RE = re.compile(r"^#{1,6}(?:[ \t]|$)")
_UNMATCHED_RE = re.compile(r"^(?P<qmd>.+?):UNMATCHED(?![\w-])", re.IGNORECASE)
_LINE_RE = re.compile(r"^(?P<qmd>.+?):(?P<line>[0-9]+)(?![0-9])")
_KNOWN_FIELDS = ("location", "old", "new", "context", "disposition")

_PENDING = re.compile(r"pending(?![\w-])", re.IGNORECASE)
_PROPOSED = re.compile(r"proposed(?![\w-])[\s:]*", re.IGNORECASE)
_KEYWORD = re.compile(r"(apply|fix-code|needs-pi)(?![\w-])", re.IGNORECASE)
_REJECT = re.compile(r"reject(?![\w-])\s*", re.IGNORECASE)
_CANONICAL = {"apply": "apply", "fix-code": "fix-code", "needs-pi": "needs-PI"}
_NOTE_SEP = re.compile(r"\s*(?:[—–]+|-+|[:;,])?\s*")


# ---------------------------------------------------------------------------
# Dispositions


@dataclass(frozen=True)
class Disposition:
    """A parsed disposition value.

    ``state`` is pending | proposed | final | invalid. A final value carries its
    ``decision``; a proposal carries the proposed decision in ``proposal``. Both
    use the canonical spelling (apply, reject, fix-code, needs-PI). ``note`` is
    the note, the reject reason, or the proposal's rationale; ``problem`` says
    what is wrong with an invalid value and how to write a valid one.
    """

    text: str
    state: str
    decision: str | None = None
    proposal: str | None = None
    note: str = ""
    problem: str | None = None

    @property
    def label(self) -> str:
        """Short canonical form for tables: PENDING, PROPOSED apply, reject, INVALID."""
        if self.state == "pending":
            return "PENDING"
        if self.state == "proposed":
            return f"PROPOSED {self.proposal}"
        if self.state == "final":
            return str(self.decision)
        return "INVALID"


def parse_disposition(text: str) -> Disposition:
    """Classify a disposition value (its first line plus any continuation lines)."""
    flat = " ".join(text.split())
    if not flat:
        return Disposition(text, "invalid", problem=f"the disposition is empty; {GRAMMAR}")
    if m := _PENDING.match(flat):
        return Disposition(text, "pending", note=_note(flat[m.end():]))
    if m := _PROPOSED.match(flat):
        decision, note, problem = _parse_final(flat[m.end():])
        if problem:
            return Disposition(
                text, "invalid", problem=f"PROPOSED must be followed by a decision: {problem}"
            )
        return Disposition(text, "proposed", proposal=decision, note=note)
    decision, note, problem = _parse_final(flat)
    if problem:
        return Disposition(text, "invalid", problem=problem)
    return Disposition(text, "final", decision=decision, note=note)


def check_disposition(value: str) -> Disposition:
    """Validate a one-line disposition value, raising InputError with the grammar."""
    if "\n" in value or "\r" in value:
        raise InputError(f"a disposition must be a single line; {GRAMMAR}")
    parsed = parse_disposition(value)
    if parsed.state == "invalid":
        problem = str(parsed.problem)
        if GRAMMAR not in problem:
            problem = f"{problem}; {GRAMMAR}"
        raise InputError(f"invalid disposition {_clip(value.strip())!r}: {problem}")
    return parsed


def _parse_final(s: str) -> tuple[str | None, str, str | None]:
    """(decision, note, problem) for a final value; problem is None when valid."""
    if not s:
        return None, "", f"nothing follows it; {GRAMMAR}"
    if m := _KEYWORD.match(s):
        return _CANONICAL[m.group(1).lower()], _note(s[m.end():]), None
    if m := _REJECT.match(s):
        rest = s[m.end():]
        if not rest.startswith(":"):
            return None, "", "reject needs a colon and a reason: `reject: <reason>`"
        reason = rest[1:].strip()
        if not reason:
            return None, "", "reject needs a reason after the colon: `reject: <reason>`"
        return "reject", reason, None
    return None, "", f"`{_clip(s.split()[0])}` is not a disposition; {GRAMMAR}"


def _note(rest: str) -> str:
    """The note after a keyword, without its leading separator (' — ', ':', ...)."""
    return rest[_NOTE_SEP.match(rest).end():].strip()


def _clip(text: str, limit: int = 60) -> str:
    return text if len(text) <= limit else text[: limit - 3] + "..."


# ---------------------------------------------------------------------------
# Rows


@dataclass(slots=True)
class _Line:
    text: str  # content without its line ending
    eol: str  # "\r\n", "\n", or "" for a last line without a newline


@dataclass(frozen=True, eq=False)
class Row:
    """A parsed snapshot of one worksheet row. Re-read ``Worksheet.rows`` after a
    mutation; mutations address rows by number."""

    number: int
    kind: str  # insertion | deletion | replacement | comment | unparsed | (hand edits)
    author: str
    start: int  # index of the heading line
    end: int  # index just past the row's last line
    fields: tuple[tuple[str, str, int], ...]  # (key, value, line index), file order
    disposition_index: int | None  # line index of the first `- disposition:` line
    continuation: tuple[int, ...]  # line indices continuing the disposition
    extra: tuple[str, ...]  # other non-blank lines, verbatim (unknown fields, notes)
    disposition: Disposition

    def field(self, key: str) -> str | None:
        """The first value of field ``key``, or None."""
        return next((value for k, value, _ in self.fields if k == key), None)

    def field_count(self, key: str) -> int:
        return sum(1 for k, _, _ in self.fields if k == key)

    @property
    def disposition_text(self) -> str:
        """The disposition's first-line value plus its continuation lines."""
        return self.disposition.text

    @property
    def location(self) -> str | None:
        return self.field("location")

    @property
    def old(self) -> str | None:
        return self.field("old")

    @property
    def new(self) -> str | None:
        return self.field("new")

    @property
    def context(self) -> str | None:
        return self.field("context")

    @property
    def unmatched(self) -> bool:
        """True when roundtrip could not align the change to a .qmd line."""
        loc = self.location
        return loc is not None and _UNMATCHED_RE.match(loc) is not None

    @property
    def qmd(self) -> str | None:
        """The .qmd file named by the location, or None when it names none."""
        loc = self.location
        if loc is None:
            return None
        m = _UNMATCHED_RE.match(loc) or _LINE_RE.match(loc)
        return m.group("qmd").strip() if m else None

    @property
    def line(self) -> int | None:
        """The 1-based .qmd line number, or None (UNMATCHED or no line given)."""
        loc = self.location
        if loc is None or self.unmatched:
            return None
        m = _LINE_RE.match(loc)
        return int(m.group("line")) if m else None

    @property
    def apply_blocker(self) -> str | None:
        """Why `apply` cannot be chosen for this row, or None when it can."""
        if self.kind == "unparsed":
            return "wongo could not extract this change (unparsed row), so there is no text to apply"
        if self.unmatched:
            return "its location is UNMATCHED, so the .qmd line to change is unknown"
        return None

    @property
    def needs_decision(self) -> bool:
        """Pending, proposed or invalid, or an `apply` that cannot be carried out."""
        d = self.disposition
        if d.state != "final":
            return True
        return d.decision == "apply" and self.apply_blocker is not None

    def to_dict(self) -> dict:
        d = self.disposition
        return {
            "row": self.number,
            "kind": self.kind,
            "author": self.author,
            "location": self.location,
            "qmd": self.qmd,
            "line": self.line,
            "unmatched": self.unmatched,
            "old": self.old,
            "new": self.new,
            "context": self.context,
            "disposition": d.text,
            "state": d.state,
            "decision": d.decision,
            "proposal": d.proposal,
            "note": d.note,
            "problem": d.problem,
            "needs_decision": self.needs_decision,
            "apply_blocker": self.apply_blocker,
        }


@dataclass(frozen=True)
class Problem:
    severity: str  # "error" | "warning"
    row: int | None  # None for a problem with the whole worksheet
    message: str

    def __str__(self) -> str:
        where = "worksheet" if self.row is None else f"row {self.row}"
        return f"{where}: {self.severity}: {self.message}"


@dataclass(frozen=True)
class Counts:
    total: int
    pending: int
    proposed: int
    final: int
    invalid: int
    needs_decision: int  # what `wongo review` would show
    decisions: dict[str, int]  # final rows per decision
    proposals: dict[str, int]  # proposed rows per proposed decision


@dataclass(frozen=True)
class Target:
    """The .qmd line a row points at, as the file reads now."""

    path: Path | None  # the .qmd file, when the row names one
    line: int | None  # 1-based line number, when the row has one
    text: str | None  # the line's current text; None when it cannot be shown
    problem: str | None = None  # why text is None
    reason: str | None = None  # unmatched | no-location | missing-file | unreadable | beyond-end

    @property
    def inline_code(self) -> bool:
        return self.text is not None and INLINE_CODE_RE.search(self.text) is not None


def read_target(project: Path | str, row: Row, *, cache: dict | None = None) -> Target:
    """Read the .qmd line ``row`` points at, relative to ``project``. Never writes."""
    if row.unmatched:
        return Target(None, None, None, "the location is UNMATCHED", "unmatched")
    if row.qmd is None or row.line is None:
        return Target(None, None, None, "the row has no `<file>:<line>` location", "no-location")
    path = Path(project) / row.qmd
    lines = _qmd_lines(path, cache)
    if isinstance(lines, tuple):
        reason, problem = lines
        return Target(path, row.line, None, problem, reason)
    if not 1 <= row.line <= len(lines):
        return Target(
            path, row.line, None,
            f"{row.qmd} has {len(lines)} lines, so line {row.line} is beyond its end",
            "beyond-end",
        )
    return Target(path, row.line, lines[row.line - 1])


def _qmd_lines(path: Path, cache: dict | None) -> list[str] | tuple[str, str]:
    """The file's lines (numbered like roundtrip.locate), or (reason, message)."""
    if cache is not None and path in cache:
        return cache[path]
    result: list[str] | tuple[str, str]
    if not path.is_file():
        result = ("missing-file", f"{path.name} not found in {path.parent}")
    else:
        try:
            result = read_text(path).splitlines()
        except WongoError as exc:
            result = ("unreadable", str(exc))
        except OSError as exc:
            result = ("unreadable", f"cannot read {path}: {exc.strerror or exc}")
    if cache is not None:
        cache[path] = result
    return result


# ---------------------------------------------------------------------------
# The worksheet


class Worksheet:
    """A merge worksheet held as its exact lines; rows are parsed views over them."""

    def __init__(
        self,
        text: str = "",
        *,
        bom: bool = False,
        newline: str | None = None,
        path: Path | str | None = None,
    ) -> None:
        self._lines = _split_lines(text)
        self.bom = bom
        self.newline = newline or ("\r\n" if "\r\n" in text else "\n")
        self.path = Path(path) if path is not None else None
        self._disk: bytes | None = None  # file bytes at load/save, to detect outside edits
        self._rows: list[Row] = []
        self._reindex()

    # -- reading and writing -------------------------------------------------

    @classmethod
    def parse(cls, raw: bytes | str, *, path: Path | str | None = None) -> Worksheet:
        """Parse worksheet bytes (or text); a leading BOM is remembered, not kept."""
        if isinstance(raw, str):
            bom = raw.startswith("\ufeff")
            text = raw[1:] if bom else raw
            return cls(text, bom=bom, path=path)
        bom = raw.startswith(BOM)
        body = raw[len(BOM):] if bom else raw
        try:
            text = body.decode("utf-8")
        except UnicodeDecodeError as exc:
            where = path if path is not None else "the worksheet"
            position = exc.start + (len(BOM) if bom else 0)
            raise InputError(
                f"{where} is not UTF-8 text (invalid byte at position {position}). "
                "Re-save it as UTF-8, e.g. in VS Code: 'Save with Encoding' > UTF-8."
            ) from exc
        return cls(text, bom=bom, newline=detect_newline(raw), path=path)

    @classmethod
    def load(cls, path: Path | str) -> Worksheet:
        path = Path(path)
        if path.suffix.lower() == ".qmd":
            raise InputError(
                f"{path} is a .qmd manuscript source, not a merge worksheet; give the "
                "decisions/merge-*.md file that `wongo roundtrip` wrote"
            )
        if path.is_dir():
            raise InputError(
                f"{path} is a folder; give the worksheet file in it, "
                "e.g. decisions/merge-20260925-coauthor.md"
            )
        try:
            raw = path.read_bytes()
        except FileNotFoundError:
            raise InputError(
                f"worksheet not found: {path}. `wongo roundtrip <coauthor.docx>` writes one "
                "to decisions/merge-<date>-<name>.md; check the path."
            ) from None
        except OSError as exc:
            raise InputError(f"cannot read {path}: {exc.strerror or exc}") from exc
        ws = cls.parse(raw, path=path)
        ws._disk = raw
        return ws

    def text(self) -> str:
        """The worksheet text without the BOM, line endings exactly as held."""
        return "".join(line.text + line.eol for line in self._lines)

    def serialize(self) -> bytes:
        """The exact file bytes: the BOM (if the input had one) plus UTF-8 text."""
        return (BOM if self.bom else b"") + self.text().encode("utf-8")

    def save(self, path: Path | str | None = None) -> Path:
        """Write atomically (textio.write_text_atomic), keeping the BOM and the
        line-ending style. A file with mixed endings is written with one style,
        CRLF if it had any, like every file wongo rewrites.

        Refuses a .qmd target (wongo never edits the manuscript), and refuses to
        overwrite the file it was loaded from when that file changed on disk in
        the meantime, so an edit made in an editor or by the agent is not lost.
        """
        target = Path(path) if path is not None else self.path
        if target is None:
            raise InputError("this worksheet has no file yet; give a path to save it to")
        if target.suffix.lower() == ".qmd":
            raise InputError(
                f"refusing to write {target}: wongo never edits a .qmd. Save the worksheet "
                "as a .md file (roundtrip writes them to decisions/)."
            )
        if self._disk is not None and self.path is not None and _same_file(target, self.path):
            try:
                current = target.read_bytes()
            except FileNotFoundError:
                current = self._disk  # deleted meanwhile: writing it back loses nothing
            except OSError as exc:
                raise InputError(f"cannot read {target}: {exc.strerror or exc}") from exc
            if current != self._disk:
                raise InputError(
                    f"{target} changed on disk after wongo read it (edited in another program "
                    "or by the agent?). Nothing was saved; run the command again on the "
                    "current file."
                )
        for line in self._lines:
            if line.eol:
                line.eol = self.newline
        try:
            write_text_atomic(target, ("\ufeff" if self.bom else "") + self.text(), self.newline)
        except OSError as exc:
            raise InputError(
                f"could not save {target}: {exc.strerror or exc}. Close any program that "
                "has it open, then try again."
            ) from exc
        self.path = target
        self._disk = self.serialize()
        return target

    # -- structure -----------------------------------------------------------

    @property
    def rows(self) -> list[Row]:
        return list(self._rows)

    @property
    def preamble(self) -> list[str]:
        """The lines before the first row heading (title and instructions)."""
        stop = self._rows[0].start if self._rows else len(self._lines)
        return [line.text for line in self._lines[:stop]]

    def row(self, number: int) -> Row:
        """The row numbered ``number``; InputError if it is missing or repeated."""
        found = [r for r in self._rows if r.number == number]
        if len(found) == 1:
            return found[0]
        where = self.path if self.path is not None else "the worksheet"
        if not found:
            have = number_ranges(r.number for r in self._rows) or "none"
            raise InputError(f"row {number} is not in {where} (its rows: {have})")
        raise InputError(
            f"row number {number} is used by {len(found)} rows in {where}; renumber them "
            "so each number is unique, then try again"
        )

    def find(self, number: int) -> Row | None:
        """The row numbered ``number``, or None when it is missing or repeated."""
        found = [r for r in self._rows if r.number == number]
        return found[0] if len(found) == 1 else None

    def raw_row(self, number: int) -> str:
        """The row's exact text, heading to the line before the next row."""
        row = self.row(number)
        return "".join(line.text + line.eol for line in self._lines[row.start:row.end])

    def needs_decision(self) -> list[Row]:
        return [r for r in self._rows if r.needs_decision]

    def counts(self) -> Counts:
        states = Counter(r.disposition.state for r in self._rows)
        decisions = dict.fromkeys(DECISIONS, 0)
        proposals = dict.fromkeys(DECISIONS, 0)
        for r in self._rows:
            d = r.disposition
            if d.state == "final":
                decisions[d.decision] += 1
            elif d.state == "proposed":
                proposals[d.proposal] += 1
        return Counts(
            total=len(self._rows),
            pending=states["pending"],
            proposed=states["proposed"],
            final=states["final"],
            invalid=states["invalid"],
            needs_decision=sum(1 for r in self._rows if r.needs_decision),
            decisions=decisions,
            proposals=proposals,
        )

    # -- mutations (each keeps every other byte intact) ----------------------

    def set_disposition(self, number: int, value: str) -> Row:
        """Replace the disposition's first-line value; continuation lines stay.

        ``value`` must be PENDING, PROPOSED <final>, or a final value.
        """
        value = value.strip()
        check_disposition(value)
        row = self.row(number)
        if row.disposition_index is None:
            self._insert(self._content_end(row), f"- disposition: {value}")
        else:
            self._set_value(row.disposition_index, value)
        self._reindex()
        return self.row(number)

    def accept_proposal(self, number: int) -> Row:
        """Turn ``PROPOSED <x>`` into ``<x>`` by removing the PROPOSED prefix only."""
        row = self.row(number)
        if row.disposition.state != "proposed":
            shown = " ".join(row.disposition.text.split()) or "none"
            raise InputError(
                f"row {number} has no proposal to accept (disposition: {_clip(shown)}); "
                f"decide it instead, e.g. `wongo worksheet set <file> {number} apply`"
            )
        index, offset = self._disposition_head(row)
        line = self._lines[index]
        body = line.text[offset:]
        stripped = body.lstrip()
        rest = stripped[_PROPOSED.match(stripped).end():]
        if index == row.disposition_index:
            self._set_value(index, rest)
        elif rest.strip():
            line.text = line.text[:offset] + rest
        else:  # a continuation line that held only "PROPOSED"
            del self._lines[index]
        self._reindex()
        return self.row(number)

    def decide(self, number: int, final_value: str) -> Row:
        """Record a person's final decision.

        - Same decision as the row's proposal (and no different note): the
          proposal is accepted as written, rationale kept.
        - A different decision, or a note of one's own: the new value is
          written as ``<final_value> — was <old text>``, so the agent's
          rationale (``was PROPOSED ...``) or an earlier value stays on record.
        - A PENDING or missing disposition is simply replaced.
        """
        value = final_value.strip()
        chosen = check_disposition(value)
        if chosen.state != "final":
            raise InputError(
                f"a decision must be final, not {_clip(value)!r}: use apply, fix-code or "
                "needs-PI (each may add ' — note'), or reject: <reason>"
            )
        row = self.row(number)
        old = row.disposition
        same_note = chosen.note in ("", old.note)
        if old.state == "proposed" and old.proposal == chosen.decision and same_note:
            return self.accept_proposal(number)
        if old.state == "final" and old.decision == chosen.decision and same_note:
            return row
        if row.disposition_index is not None and old.state != "pending" and old.text.strip():
            first = self._value(row.disposition_index)
            self._set_value(row.disposition_index, f"{value} — was {first}".rstrip())
            self._reindex()
            return self.row(number)
        return self.set_disposition(number, value)

    def set_location(self, number: int, line: int) -> Row:
        """Point the row at ``<qmd>:<line>``, keeping its .qmd name.

        A row without one gets the .qmd the other rows name, else index.qmd.
        """
        if isinstance(line, bool) or not isinstance(line, int) or line < 1:
            raise InputError(f"a location line must be a whole number of 1 or more, not {line!r}")
        row = self.row(number)
        value = f"{row.qmd or self._common_qmd()}:{line}"
        index = next((i for k, _, i in row.fields if k == "location"), None)
        if index is None:
            self._insert(row.start + 1, f"- location: {value}")
        else:
            self._set_value(index, value)
        self._reindex()
        return self.row(number)

    # -- checks --------------------------------------------------------------

    def lint(self, project: Path | str | None = None) -> list[Problem]:
        """Errors block applying the worksheet; warnings are worth a look.

        With ``project`` (the folder holding the .qmd), each ``apply`` row's
        target line is also read: inline code on it, a line number past the end
        of the file, or a missing .qmd give warnings.
        """
        problems: list[Problem] = []
        if not self._rows:
            problems.append(Problem(
                "warning", None,
                "no rows found (row headings look like `## 1. insertion — Author`); "
                "is this a merge worksheet?",
            ))
        numbers = Counter(r.number for r in self._rows)
        repeated: set[int] = set()
        cache: dict = {}
        missing: set[Path] = set()
        for row in self._rows:
            if numbers[row.number] > 1 and row.number not in repeated:
                repeated.add(row.number)
                problems.append(Problem(
                    "error", row.number,
                    f"row number {row.number} is used by {numbers[row.number]} rows — "
                    "renumber them so each number is unique",
                ))
            problems.extend(self._row_problems(row))
            if project is not None and row.disposition.decision == "apply":
                problems.extend(_target_problems(Path(project), row, cache, missing))
        return problems

    def _row_problems(self, row: Row) -> list[Problem]:
        n, d, f = row.number, row.disposition, self._file_arg()
        out: list[Problem] = []
        if row.field_count("disposition") > 1:
            out.append(Problem("error", n, "more than one `- disposition:` line — keep one"))
        if row.disposition_index is None:
            out.append(Problem(
                "error", n,
                "no `- disposition:` line — add `- disposition: PENDING` to the row, "
                "then decide it",
            ))
        elif d.state == "pending":
            out.append(Problem(
                "error", n,
                f"still PENDING — decide it with `wongo review {f}` or "
                f"`wongo worksheet set {f} {n} <disposition>`",
            ))
        elif d.state == "proposed":
            out.append(Problem(
                "error", n,
                f"PROPOSED {d.proposal} is not confirmed by a person yet — accept or change "
                f"it with `wongo review {f}`",
            ))
        elif d.state == "invalid":
            out.append(Problem("error", n, str(d.problem)))
        elif d.decision == "apply":
            if row.kind == "unparsed":
                out.append(Problem(
                    "error", n,
                    "apply on an unparsed row: wongo extracted no text to apply — open the "
                    "DOCX at the context and choose fix-code, needs-PI or reject: <reason>",
                ))
            elif row.unmatched:
                out.append(Problem(
                    "error", n,
                    "apply, but the location is UNMATCHED — find the line and run "
                    f"`wongo worksheet set {f} {n} --location N`, or choose fix-code",
                ))
            elif row.line is None:
                where = f"location {_clip(row.location)!r}" if row.location else "no location"
                out.append(Problem(
                    "warning", n,
                    f"apply, but the row has {where}, not `<file>:<line>`; wongo cannot "
                    "check the target line",
                ))
        return out

    # -- internals -----------------------------------------------------------

    def _reindex(self) -> None:
        heads = [i for i, line in enumerate(self._lines) if ROW_RE.match(line.text)]
        ends = [*heads[1:], len(self._lines)]
        self._rows = [self._parse_row(start, end) for start, end in zip(heads, ends)]

    def _parse_row(self, start: int, end: int) -> Row:
        head = ROW_RE.match(self._lines[start].text)
        fields: list[tuple[str, str, int]] = []
        continuation: list[int] = []
        extra: list[str] = []
        seen: set[str] = set()
        disposition_index = None
        i = start + 1
        while i < end:
            text = self._lines[i].text
            m = FIELD_RE.match(text)
            if m is None:
                if text.strip():
                    extra.append(text)
                i += 1
                continue
            key = m.group(1)
            fields.append((key, m.group(2), i))
            if key in seen or key not in _KNOWN_FIELDS:
                extra.append(text)
            first = key not in seen
            seen.add(key)
            i += 1
            if key == "disposition" and first:
                disposition_index = i - 1
                while i < end and _continues(self._lines[i].text):
                    continuation.append(i)
                    i += 1
        if disposition_index is None:
            disposition = Disposition(
                "", "invalid", problem="the row has no `- disposition:` line"
            )
        else:
            parts = [self._value(disposition_index).rstrip()]
            parts += [self._lines[j].text.strip() for j in continuation]
            disposition = parse_disposition("\n".join(parts))
        return Row(
            number=int(head.group(1)),
            kind=head.group(2),
            author=(head.group(3) or "").strip(),
            start=start,
            end=end,
            fields=tuple(fields),
            disposition_index=disposition_index,
            continuation=tuple(continuation),
            extra=tuple(extra),
            disposition=disposition,
        )

    def _value(self, index: int) -> str:
        return FIELD_RE.match(self._lines[index].text).group(2)

    def _set_value(self, index: int, value: str) -> None:
        line = self._lines[index]
        prefix = line.text[: FIELD_RE.match(line.text).start(2)]
        if not value.strip():
            line.text = prefix.rstrip()
        elif prefix.endswith((" ", "\t")):
            line.text = prefix + value
        else:
            line.text = f"{prefix} {value}"

    def _disposition_head(self, row: Row) -> tuple[int, int]:
        """(line index, offset) where the disposition's text begins."""
        index = row.disposition_index
        segments = [(index, FIELD_RE.match(self._lines[index].text).start(2))]
        for j in row.continuation:
            text = self._lines[j].text
            segments.append((j, len(text) - len(text.lstrip())))
        for j, offset in segments:
            if self._lines[j].text[offset:].strip():
                return j, offset
        return segments[0]

    def _content_end(self, row: Row) -> int:
        """Index just past the row's last non-blank line."""
        i = row.end
        while i > row.start + 1 and not self._lines[i - 1].text.strip():
            i -= 1
        return i

    def _insert(self, index: int, text: str) -> None:
        if index < len(self._lines):
            self._lines.insert(index, _Line(text, self.newline))
        elif self._lines and not self._lines[-1].eol:
            self._lines[-1].eol = self.newline  # keep "no newline at end of file"
            self._lines.append(_Line(text, ""))
        else:
            self._lines.append(_Line(text, self.newline))

    def _common_qmd(self) -> str:
        """The .qmd most rows name (roundtrip writes one per worksheet), else index.qmd."""
        names = Counter(r.qmd for r in self._rows if r.qmd)
        return names.most_common(1)[0][0] if names else DEFAULT_QMD

    def _file_arg(self) -> str:
        return shell_arg(self.path) if self.path is not None else "<file>"


def parse(raw: bytes | str) -> Worksheet:
    """Parse worksheet bytes or text; ``serialize(parse(raw)) == raw`` for bytes."""
    return Worksheet.parse(raw)


def serialize(ws: Worksheet) -> bytes:
    return ws.serialize()


def load(path: Path | str) -> Worksheet:
    return Worksheet.load(path)


def shell_arg(path: Path | str) -> str:
    """A path as a user would type it in a command line: forward slashes (which
    cmd, PowerShell and Git Bash all accept; a backslash is an escape in Git
    Bash, the shell Claude Code uses on Windows), quoted if it has spaces."""
    text = Path(path).as_posix()
    return f'"{text}"' if any(ch.isspace() for ch in text) else text


def _target_problems(project: Path, row: Row, cache: dict, missing: set[Path]) -> list[Problem]:
    """Warnings about the .qmd line a final `apply` row targets."""
    if row.apply_blocker or row.line is None:
        return []  # already reported by _row_problems
    target = read_target(project, row, cache=cache)
    n = row.number
    if target.reason == "missing-file":
        if target.path in missing:
            return []
        missing.add(target.path)
        return [Problem(
            "warning", n,
            f"{target.problem}, so target lines were not checked — pass --project DIR, "
            f"the folder that holds {row.qmd}",
        )]
    if target.reason == "beyond-end":
        return [Problem("warning", n, f"{target.problem} — the location looks stale; check it")]
    if target.text is None:
        return [Problem("warning", n, f"target line not checked: {target.problem}")]
    if target.inline_code:
        return [Problem(
            "warning", n,
            f"apply on {row.qmd}:{row.line}, a line with inline code (`r ...`) — make sure "
            "no hand-typed number replaces a generated one",
        )]
    return []


def _split_lines(text: str) -> list[_Line]:
    """Split on LF only (CRLF kept as the ending), so joining restores the text."""
    lines: list[_Line] = []
    pos = 0
    while pos < len(text):
        nl = text.find("\n", pos)
        if nl == -1:
            lines.append(_Line(text[pos:], ""))
            break
        if nl > pos and text[nl - 1] == "\r":
            lines.append(_Line(text[pos:nl - 1], "\r\n"))
        else:
            lines.append(_Line(text[pos:nl], "\n"))
        pos = nl + 1
    return lines


def _continues(text: str) -> bool:
    return bool(text.strip()) and not FIELD_RE.match(text) and not _HEADING_RE.match(text)


def _same_file(a: Path, b: Path) -> bool:
    try:
        return os.path.samefile(a, b)
    except OSError:
        return a.resolve() == b.resolve()


def number_ranges(numbers) -> str:
    """'1-3, 5' for [1, 2, 3, 5] (sorted, duplicates dropped)."""
    numbers = sorted(set(numbers))
    parts: list[str] = []
    i = 0
    while i < len(numbers):
        j = i
        while j + 1 < len(numbers) and numbers[j + 1] == numbers[j] + 1:
            j += 1
        parts.append(str(numbers[i]) if i == j else f"{numbers[i]}-{numbers[j]}")
        i = j + 1
    return ", ".join(parts)
