"""`wongo review`: decide merge-worksheet rows one at a time at a terminal.

Plain lines only: no colours, no full-screen mode, no raw keyboard reads. Every
answer is typed and confirmed with Enter, so a Korean input method composes
normally, and every menu choice is a digit, which types the same whether the
Korean keyboard is on or off (letter keys would type Hangul jamo).

The worksheet is read again before each row and saved right after each
decision, so Ctrl-C, a closed window or a crash loses at most the row on
screen, and an edit made meanwhile in an editor (or by the agent) is kept
rather than overwritten. Nothing here writes a .qmd: approved rows are applied
to the manuscript afterwards, by the person or the agent.
"""
from __future__ import annotations

import unicodedata
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from wongo.engine.worksheet import (
    DECISIONS,
    Row,
    Target,
    Worksheet,
    number_ranges,
    read_target,
    shell_arg,
)
from wongo.errors import InputError

HELP = """\
  Enter  accept the agent's proposal as written (only when the row has one)
  1      apply     the change goes into the .qmd (afterwards, by you or the agent)
  2      reject    you are asked for the reason, which is required
  3      fix-code  the edit touches generated output: change the code, not the prose
  4      needs-PI  leave the decision to the PI
  5      skip      decide later; the row stays undecided
  0      save and quit (each decision is already saved the moment you make it)
  Type the digit, then press Enter. Digits type the same with the Korean keyboard on."""

_LABEL = 10  # width of the "old:", "new:", ... column


def _same_text(a: str, b: str) -> bool:
    """Equal apart from line endings."""
    return a.replace("\r\n", "\n") == b.replace("\r\n", "\n")


@dataclass(frozen=True)
class Decision:
    row: int
    decision: str  # apply | reject | fix-code | needs-PI
    text: str  # the disposition line as saved


@dataclass
class ReviewSummary:
    path: Path
    total: int = 0  # rows in the worksheet
    decided: list[Decision] = field(default_factory=list)  # saved this session, in order
    skipped: list[int] = field(default_factory=list)
    remaining: list[int] = field(default_factory=list)  # rows still needing a decision
    stopped: str = "done"  # done | quit | eof | interrupted


class _Stop(Exception):
    """Input ended (EOF) or was interrupted (Ctrl-C)."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def review(
    path: Path | str,
    project: Path | str,
    *,
    input_fn: Callable[[str], str] = input,
    print_fn: Callable[..., object] = print,
) -> ReviewSummary:
    """Walk the rows that still need a person's decision, saving after each one.

    ``project`` is the folder holding the .qmd, used to show each row's target
    line. Returns what was decided; never writes anything but the worksheet.
    """
    path, project = Path(path), Path(project)
    if not project.is_dir():
        raise InputError(
            f"project folder not found: {project}; pass --project DIR, the folder that "
            "holds the .qmd"
        )
    ws = Worksheet.load(path)
    repeated = sorted(n for n, k in Counter(r.number for r in ws.rows).items() if k > 1)
    if repeated:
        raise InputError(
            f"{path} numbers more than one row {', '.join(map(str, repeated))}; renumber "
            "the rows so each number is unique, then run wongo review again"
        )
    summary = ReviewSummary(path=path, total=len(ws.rows))
    queue = [row.number for row in ws.rows if row.needs_decision]
    if not ws.rows:
        print_fn(f"Nothing to review: {path} has no rows.")
    elif not queue:
        print_fn(f"Nothing to review: every row in {path} has a decision ({len(ws.rows)} rows).")
    else:
        print_fn(f"Reviewing {path}: {len(queue)} of {len(ws.rows)} rows need a decision.")
        print_fn("Type a digit and press Enter; ? shows help. Each decision is saved at once.")
        session = _Session(path, project, input_fn, print_fn, summary, len(queue))
        try:
            for position, number in enumerate(queue, start=1):
                if session.run_row(number, position) == "quit":
                    summary.stopped = "quit"
                    break
        except _Stop as stop:
            summary.stopped = stop.reason
            print_fn("")
        except KeyboardInterrupt:  # Ctrl-C outside a prompt, e.g. while saving
            summary.stopped = "interrupted"
            print_fn("")
    summary.remaining = [r.number for r in Worksheet.load(path).rows if r.needs_decision]
    _print_summary(summary, print_fn)
    return summary


class _Session:
    def __init__(self, path: Path, project: Path, input_fn, print_fn, summary, queue_len):
        self.path = path
        self.project = project
        self.input_fn = input_fn
        self.out = print_fn
        self.summary = summary
        self.queue_len = queue_len
        self.file = shell_arg(path)

    def run_row(self, number: int, position: int) -> str:
        """Show one row until it is decided, skipped or the person quits."""
        while True:
            ws = Worksheet.load(self.path)  # pick up edits made since the last row
            row = ws.find(number)
            if row is None:
                self.out(f"\nRow {number} is no longer in the file (or its number repeats); skipped.")
                return "gone"
            if not row.needs_decision:
                self.out(f"\nRow {number} was decided meanwhile ({row.disposition.label}); skipped.")
                return "gone"
            shown = ws.raw_row(number)
            target = read_target(self.project, row)
            self._show(row, target, position)
            action, value = self._choose(row, target)
            if action == "skip":
                self.summary.skipped.append(number)
                self.out(f"  skipped row {number}")
                return "skipped"
            if action == "quit":
                return "quit"
            if self._commit(row, shown, action, value):
                return "decided"

    def _show(self, row: Row, target: Target, position: int) -> None:
        out = self.out
        out("")
        out(f"({position} of {self.queue_len} to review)")
        out(
            f"Row {row.number}/{self.summary.total} · {row.kind} · {row.author} · "
            f"{row.location or '(no location)'}"
        )
        extra = [f"  {text}" for text in row.extra]
        if row.kind == "unparsed":  # the parser's warning is the first thing to read
            for line in extra:
                out(line)
            extra = []
        for key in ("old", "new", "context"):
            value = row.field(key)
            if value is not None:
                out(f"  {key + ':':<{_LABEL}}{value}")
        for line in extra:
            out(line)
        if target.text is not None:
            out(f"  {'in .qmd:':<{_LABEL}}{target.text}")
            if target.inline_code:
                out(f"  {'':<{_LABEL}}(this line has inline code: its numbers are generated)")
        else:
            out(f"  {'in .qmd:':<{_LABEL}}(line not found: {target.problem})")
        d = row.disposition
        if d.state == "pending":
            return
        label = "proposal:" if d.state == "proposed" else "current:"
        lines = d.text.split("\n")
        if d.state == "invalid":
            lines[-1] += f"   (not valid: {d.problem})"
        elif d.state == "final":
            lines[-1] += f"   (blocked: {row.apply_blocker})"
        out(f"  {label:<{_LABEL}}{lines[0]}")
        for extra in lines[1:]:
            out(f"  {'':<{_LABEL}}{extra}")

    def _menu(self, row: Row) -> str:
        parts = []
        if row.disposition.state == "proposed":
            parts.append(f"Enter accept proposal ({row.disposition.proposal})")
        parts += ["1 apply", "2 reject", "3 fix-code", "4 needs-PI", "5 skip", "0 save & quit",
                  "? help"]
        return "  " + " · ".join(parts)

    def _choose(self, row: Row, target: Target) -> tuple[str, str | None]:
        d = row.disposition
        menu = self._menu(row)
        self.out(menu)
        while True:
            answer = self._ask(f"row {row.number}> ")
            key = _key(answer)
            if key == "":
                if d.state != "proposed":
                    self.out("  This row has no proposal to accept; type a digit (? for help).")
                    continue
                if d.proposal == "apply" and not self._apply_allowed(row, target):
                    self.out(menu)
                    continue
                return "accept", None
            if key == "1":
                if self._apply_allowed(row, target):
                    return "decide", "apply"
                self.out(menu)
                continue
            if key == "2":
                reason = self._reason()
                if reason is not None:
                    return "decide", f"reject: {reason}"
                self.out(menu)
                continue
            if key == "3":
                return "decide", "fix-code"
            if key == "4":
                return "decide", "needs-PI"
            if key == "5":
                return "skip", None
            if key == "0":
                return "quit", None
            if key == "?":
                self.out(HELP)
                self.out(menu)
                continue
            self.out(f"  {answer.strip()!r} is not a choice: type one digit (0-5) and press "
                     "Enter, or ? for help.")

    def _apply_allowed(self, row: Row, target: Target) -> bool:
        blocker = row.apply_blocker
        if blocker:
            self.out(f"  apply is not possible: {blocker}.")
            if row.kind == "unparsed":
                self.out("  Open the DOCX at the context shown, then choose 3 fix-code, "
                         "4 needs-PI or 2 reject.")
            else:
                self.out(f"  Choose 3 fix-code, or find the line in the .qmd, run "
                         f"`wongo worksheet set {self.file} {row.number} --location N` "
                         "and review this row again.")
            return False
        if target.inline_code:
            self.out(f"  Line {target.line} of {row.qmd} has inline code: its numbers are "
                     "generated, and a hand-typed number must never replace one.")
            answer = self._ask(f"  Type the row number ({row.number}) to apply anyway, "
                               "or just Enter to go back: ")
            if _key(answer) == str(row.number):
                return True
            self.out("  Not applied.")
            return False
        return True

    def _reason(self) -> str | None:
        """A non-empty reject reason, or None when the person goes back."""
        while True:
            answer = self._ask("  Reason for rejecting (required; 0 alone goes back): ")
            if _key(answer) == "0":
                return None
            reason = " ".join(answer.split())
            if reason:
                return reason
            self.out("  A reason is required.")

    def _commit(self, row: Row, shown: str, action: str, value: str | None) -> bool:
        """Save the decision into the file as it is now; False if the row changed."""
        fresh = Worksheet.load(self.path)
        current = fresh.find(row.number)
        # line endings alone do not count as a change: a Windows editor saving
        # the worksheet turns every LF into CRLF without touching any row
        if current is None or _same_text(fresh.raw_row(row.number), shown) is False:
            self.out(f"  Row {row.number} changed in the file while you were deciding; "
                     "here it is again.")
            return False
        if action == "accept":
            saved = fresh.accept_proposal(row.number)
        else:
            saved = fresh.decide(row.number, str(value))
        fresh.save()
        first = saved.disposition.text.split("\n")[0]
        self.summary.decided.append(Decision(row.number, str(saved.disposition.decision), first))
        self.out(f"  saved row {row.number}: {first}")
        return True

    def _ask(self, prompt: str) -> str:
        try:
            return self.input_fn(prompt)
        except EOFError:
            raise _Stop("eof") from None
        except KeyboardInterrupt:
            raise _Stop("interrupted") from None


def _key(answer: str) -> str:
    """A menu answer, normalised so full-width digits from an IME count too."""
    return unicodedata.normalize("NFKC", answer).strip()


def _print_summary(s: ReviewSummary, out) -> None:
    file = shell_arg(s.path)
    out("")
    if s.stopped in ("eof", "interrupted"):
        out("Stopped. Every decision made so far is saved.")
    if s.decided or s.skipped:
        by = Counter(d.decision for d in s.decided)
        detail = ", ".join(f"{k} {by[k]}" for k in DECISIONS if by[k])
        out(f"This session: {len(s.decided)} decided" + (f" ({detail})" if detail else "")
            + f", {len(s.skipped)} skipped.")
    if s.remaining:
        rows = number_ranges(s.remaining)
        out(f"{len(s.remaining)} of {s.total} rows still need a decision (rows {rows}); "
            f"continue with: wongo review {file}")
    out(f"next: wongo worksheet lint {file}")
    out("      when it passes, the approved rows can be applied to the .qmd by you or "
        "the agent (wongo never edits the .qmd).")
