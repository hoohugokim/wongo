"""`wongo review` driven by scripted answers: digits and Enter only, a save after
every decision, graceful EOF/Ctrl-C, and the .qmd never touched. Synthetic text."""
from __future__ import annotations

import pytest

from wongo.engine.worksheet import Worksheet
from wongo.errors import InputError
from wongo.review import HELP, review

HEADER = (
    "# Merge worksheet — coauthor.docx — 2026-09-25\n"
    "\n"
    "Review each item; set disposition to one of: apply / reject: <reason> /\n"
    "fix-code (edit inside auto-generated output) / needs-PI.\n"
    "\n"
)
PROPOSE_APPLY = "PROPOSED apply — prose edit, no generated numbers touched."
PROPOSE_REJECT = 'PROPOSED reject: bracketed placeholder text "[suggested edit]" — see row 1.'
PROPOSE_FIX = 'PROPOSED fix-code — the coauthor hand-typed "(approximately 25%)" next to an inline R value.'

QMD = (
    "---\n"
    'title: "A synthetic manuscript"\n'
    "---\n"
    "\n"
    "The two reactors was operated for 30 days.\n"  # 5
    "As shown in [suggested edit] the first table.\n"  # 6
    "Removal efficiency reached `r round(eff, 1)`% in reactor A.\n"  # 7
    "Earlier work is summarised here.\n"  # 8
)


def row(n, kind, author, location, disposition, old="—", new="—", context="…context…"):
    return (
        f"## {n}. {kind} — {author}\n"
        f"- location: {location}\n"
        f"- old: {old}\n"
        f"- new: {new}\n"
        f"- context: {context}\n"
        f"- disposition: {disposition}\n"
        "\n"
    )


UNMATCHED = "index.qmd:UNMATCHED — find manually"
SHEET = (
    HEADER
    + row(1, "replacement", "Jane Doe", "index.qmd:5", PROPOSE_APPLY, "reactors was", "reactors were")
    + row(2, "deletion", "Jane Doe", "index.qmd:6", PROPOSE_REJECT, "[suggested edit]")
    + row(3, "insertion", "김민수", "index.qmd:7", PROPOSE_FIX, new="(approximately 25%)")
    + row(4, "comment", "John Roe", UNMATCHED, "PENDING", "the span", "Please cite the original study.")
    + "## 5. unparsed — ?\n"
    "- PARSER COULD NOT EXTRACT THIS CHANGE — open the DOCX and review this location manually.\n"
    f"- location: {UNMATCHED}\n"
    "- context: …cited work [@doe2020…\n"
    "- disposition: PENDING\n"
    "\n"
    + row(6, "replacement", "Ada Lin", "index.qmd:7", "PENDING", "reached", "rose to")
)


@pytest.fixture
def project(tmp_path):
    (tmp_path / "index.qmd").write_text(QMD, encoding="utf-8", newline="")
    (tmp_path / "decisions").mkdir()
    sheet = tmp_path / "decisions" / "merge-20260925-coauthor.md"
    sheet.write_text(SHEET, encoding="utf-8", newline="")
    return tmp_path


def sheet_of(project):
    return project / "decisions" / "merge-20260925-coauthor.md"


class Script:
    """input_fn stand-in: answers in order; a callable is run first (to look at or
    edit the file mid-review) and returns the answer; an exception is raised;
    running out of answers is EOF, like Ctrl-D."""

    def __init__(self, *answers):
        self.answers = list(answers)
        self.prompts: list[str] = []

    def __call__(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if not self.answers:
            raise EOFError
        answer = self.answers.pop(0)
        if isinstance(answer, BaseException) or (
            isinstance(answer, type) and issubclass(answer, BaseException)
        ):
            raise answer
        return answer() if callable(answer) else answer


class Output(list):
    def __call__(self, *args, **_kwargs):
        self.append(" ".join(str(a) for a in args))

    @property
    def text(self) -> str:
        return "\n".join(self)


def run(project, *answers):
    script, out = Script(*answers), Output()
    summary = review(sheet_of(project), project, input_fn=script, print_fn=out)
    return summary, script, out


def disposition(project, number):
    return Worksheet.load(sheet_of(project)).row(number).disposition.text


# ---------------------------------------------------------------------------


def test_full_review_with_every_kind_of_answer(project):
    summary, script, out = run(
        project,
        "",  # row 1: accept PROPOSED apply (plain prose line)
        "",  # row 2: accept PROPOSED reject
        "",  # row 3: accept PROPOSED fix-code
        "2", "중복 표현",  # row 4: reject with a Hangul reason
        "1", "4",  # row 5: apply refused (unparsed), then needs-PI
        "1", "6",  # row 6: inline code line, confirm with the row number
    )
    assert summary.stopped == "done"
    assert [(d.row, d.decision) for d in summary.decided] == [
        (1, "apply"), (2, "reject"), (3, "fix-code"), (4, "reject"), (5, "needs-PI"), (6, "apply"),
    ]
    assert summary.remaining == [] and summary.skipped == []
    assert disposition(project, 1) == PROPOSE_APPLY[len("PROPOSED "):]
    assert disposition(project, 2) == PROPOSE_REJECT[len("PROPOSED "):]
    assert disposition(project, 3) == PROPOSE_FIX[len("PROPOSED "):]
    assert disposition(project, 4) == "reject: 중복 표현"
    assert disposition(project, 5) == "needs-PI"
    assert disposition(project, 6) == "apply"
    problems = Worksheet.load(sheet_of(project)).lint(project=project)
    assert [(p.severity, p.row) for p in problems] == [("warning", 6)]  # inline code line
    assert "saved row 4: reject: 중복 표현" in out.text
    assert "next: wongo worksheet lint" in out.text
    assert "wongo never edits the .qmd" in out.text


def test_only_the_decided_lines_change_and_the_qmd_is_untouched(project):
    qmd_before = (project / "index.qmd").read_bytes()
    run(project, "", "3")  # row 1 accepted, row 2 fix-code, then EOF
    expected = SHEET.replace(f"- disposition: {PROPOSE_APPLY}\n",
                             f"- disposition: {PROPOSE_APPLY[len('PROPOSED '):]}\n")
    expected = expected.replace(f"- disposition: {PROPOSE_REJECT}\n",
                                f"- disposition: fix-code — was {PROPOSE_REJECT}\n")
    assert sheet_of(project).read_text(encoding="utf-8") == expected
    assert (project / "index.qmd").read_bytes() == qmd_before
    assert sorted(p.name for p in project.iterdir()) == ["decisions", "index.qmd"]
    assert sorted(p.name for p in (project / "decisions").iterdir()) == [
        "merge-20260925-coauthor.md"
    ]


def test_each_decision_is_on_disk_before_the_next_question(project):
    seen = []

    def check_row_1_saved():
        seen.append(disposition(project, 1))
        return "3"

    def check_row_2_saved():
        seen.append(disposition(project, 2))
        return "0"

    summary, _, out = run(project, "", check_row_1_saved, check_row_2_saved)
    assert seen == [PROPOSE_APPLY[len("PROPOSED "):], f"fix-code — was {PROPOSE_REJECT}"]
    assert summary.stopped == "quit"
    assert [d.row for d in summary.decided] == [1, 2]
    assert summary.remaining == [3, 4, 5, 6]
    assert disposition(project, 3) == PROPOSE_FIX  # untouched after quitting
    assert "4 of 6 rows still need a decision (rows 3-6)" in out.text
    assert "continue with: wongo review" in out.text


def test_header_target_line_and_proposal_are_shown(project):
    _, _, out = run(project)  # EOF at the first question
    assert "(1 of 6 to review)" in out
    assert "Row 1/6 · replacement · Jane Doe · index.qmd:5" in out
    assert "  old:      reactors was" in out
    assert "  new:      reactors were" in out
    assert "  in .qmd:  The two reactors was operated for 30 days." in out
    assert f"  proposal: {PROPOSE_APPLY}" in out
    assert any(line.startswith("  Enter accept proposal (apply) · 1 apply · 2 reject") for line in out)


def test_unmatched_apply_is_refused_with_the_way_out(project):
    summary, _, out = run(project, "5", "5", "5", "1", "3")
    assert "Row 4/6 · comment · John Roe · index.qmd:UNMATCHED — find manually" in out
    assert "  in .qmd:  (line not found: the location is UNMATCHED)" in out
    assert "apply is not possible: its location is UNMATCHED" in out.text
    assert "--location N" in out.text and "3 fix-code" in out.text
    assert disposition(project, 4) == "fix-code"
    assert summary.skipped == [1, 2, 3]


def test_unparsed_apply_is_refused(project):
    _, _, out = run(project, "5", "5", "5", "5", "1", "0")
    assert "- PARSER COULD NOT EXTRACT THIS CHANGE" in out.text
    assert "there is no text to apply" in out.text
    assert disposition(project, 5) == "PENDING"


def test_accepting_a_proposed_apply_on_an_unmatched_row_is_refused_too(project):
    sheet_of(project).write_text(
        HEADER + row(1, "comment", "A", UNMATCHED, "PROPOSED apply — looks right"), encoding="utf-8"
    )
    summary, _, out = run(project, "", "4")
    assert "apply is not possible" in out.text
    assert disposition(project, 1) == "needs-PI — was PROPOSED apply — looks right"
    assert summary.remaining == []


def test_inline_code_apply_needs_the_row_number(project):
    summary, script, out = run(project, "5", "5", "5", "5", "5", "1", "", "1", "7", "1", "6")
    assert "Line 7 of index.qmd has inline code" in out.text
    assert out.text.count("Not applied.") == 2  # Enter and a wrong number both cancel
    assert script.prompts.count("  Type the row number (6) to apply anyway, or just Enter to go back: ") == 3
    assert "(this line has inline code: its numbers are generated)" in out.text
    assert disposition(project, 6) == "apply"
    assert [d.row for d in summary.decided] == [6]


def test_inline_code_cancel_then_other_choice(project):
    run(project, "5", "5", "5", "5", "5", "1", "", "3")
    assert disposition(project, 6) == "fix-code"


def test_accepting_a_proposed_apply_on_an_inline_code_line_asks_first(project):
    sheet_of(project).write_text(
        HEADER + row(1, "replacement", "A", "index.qmd:7", "PROPOSED apply — prose only"),
        encoding="utf-8",
    )
    run(project, "", "", "", "1")
    assert disposition(project, 1) == "apply — prose only"


def test_reject_reason_is_required_and_0_goes_back(project):
    summary, script, out = run(project, "2", "", "   ", "0", "2", "  말이  중복됨  ")
    assert out.text.count("A reason is required.") == 2
    assert disposition(project, 1) == f"reject: 말이 중복됨 — was {PROPOSE_APPLY}"
    assert summary.decided[0].decision == "reject"


def test_invalid_answers_reprompt_and_full_width_digits_work(project):
    summary, _, out = run(project, "x", "ㅁ", "9", "12", "５")
    assert out.text.count("is not a choice") == 4
    assert summary.skipped == [1]
    assert disposition(project, 1) == PROPOSE_APPLY


def test_help_and_enter_without_a_proposal(project):
    _, _, out = run(project, "5", "5", "5", "?", "", "0")
    assert HELP in out
    assert "This row has no proposal to accept" in out.text
    assert any(line.startswith("  1 apply · 2 reject") for line in out)  # no Enter choice


def test_eof_stops_gracefully_and_changes_nothing(project):
    before = sheet_of(project).read_bytes()
    summary, _, out = run(project)
    assert summary.stopped == "eof"
    assert summary.decided == [] and summary.remaining == [1, 2, 3, 4, 5, 6]
    assert "Stopped. Every decision made so far is saved." in out
    assert sheet_of(project).read_bytes() == before


def test_ctrl_c_keeps_what_was_saved(project):
    summary, _, out = run(project, "", "3", KeyboardInterrupt)
    assert summary.stopped == "interrupted"
    assert [d.row for d in summary.decided] == [1, 2]
    assert disposition(project, 2) == f"fix-code — was {PROPOSE_REJECT}"
    assert disposition(project, 3) == PROPOSE_FIX
    assert "Stopped. Every decision made so far is saved." in out


def test_ctrl_c_inside_the_reason_prompt(project):
    summary, _, _ = run(project, "2", KeyboardInterrupt)
    assert summary.stopped == "interrupted"
    assert disposition(project, 1) == PROPOSE_APPLY


def test_an_edit_to_the_row_on_screen_is_shown_again_not_overwritten(project):
    def agent_edits_row_1():
        text = sheet_of(project).read_text(encoding="utf-8")
        sheet_of(project).write_text(
            text.replace(PROPOSE_APPLY, "PROPOSED needs-PI — ask about scope"), encoding="utf-8"
        )
        return "3"

    _, _, out = run(project, agent_edits_row_1, "", "0")
    assert "Row 1 changed in the file while you were deciding; here it is again." in out.text
    assert disposition(project, 1) == "needs-PI — ask about scope"


def test_an_edit_to_another_row_is_kept(project):
    def human_edits_row_4():
        text = sheet_of(project).read_text(encoding="utf-8")
        sheet_of(project).write_text(
            text.replace("Please cite the original study.", "Please cite it."), encoding="utf-8"
        )
        return "3"

    run(project, human_edits_row_4, "0")
    ws = Worksheet.load(sheet_of(project))
    assert ws.row(1).disposition.text == f"fix-code — was {PROPOSE_APPLY}"
    assert ws.row(4).new == "Please cite it."


def test_a_row_decided_elsewhere_meanwhile_is_skipped(project):
    def agent_decides_row_2():
        ws = Worksheet.load(sheet_of(project))
        ws.set_disposition(2, "reject: already handled")
        ws.save()
        return ""

    summary, _, out = run(project, agent_decides_row_2, "0")
    assert "Row 2 was decided meanwhile (reject); skipped." in out.text
    assert "Row 3/6" in out.text
    assert [d.row for d in summary.decided] == [1]


def test_crlf_and_bom_survive_a_review(project):
    raw = b"\xef\xbb\xbf" + SHEET.replace("\n", "\r\n").encode()
    sheet_of(project).write_bytes(raw)
    run(project, "4")
    expected = raw.replace(
        f"- disposition: {PROPOSE_APPLY}\r\n".encode(),
        f"- disposition: needs-PI — was {PROPOSE_APPLY}\r\n".encode(),
    )
    assert sheet_of(project).read_bytes() == expected


def test_nothing_to_review(project):
    sheet_of(project).write_text(HEADER + row(1, "insertion", "A", "index.qmd:5", "apply"),
                                 encoding="utf-8")
    summary, script, out = run(project)
    assert script.prompts == []
    assert "Nothing to review: every row in" in out.text
    assert "next: wongo worksheet lint" in out.text
    assert summary.decided == [] and summary.remaining == []
    sheet_of(project).write_text(HEADER, encoding="utf-8")  # roundtrip found no changes
    _, script, out = run(project)
    assert script.prompts == [] and "has no rows" in out.text


def test_blocked_final_apply_is_offered_for_review(project):
    sheet_of(project).write_text(HEADER + row(1, "comment", "A", UNMATCHED, "apply — typed by hand"),
                                 encoding="utf-8")
    _, _, out = run(project, "3")
    assert "current:  apply — typed by hand   (blocked: its location is UNMATCHED" in out.text
    assert disposition(project, 1) == "fix-code — was apply — typed by hand"


def test_invalid_row_is_offered_with_its_problem(project):
    sheet_of(project).write_text(HEADER + row(1, "insertion", "A", "index.qmd:5", "reject:"),
                                 encoding="utf-8")
    _, _, out = run(project, "2", "off topic")
    assert "(not valid: reject needs a reason after the colon" in out.text
    assert disposition(project, 1) == "reject: off topic — was reject:"


def test_repeated_row_numbers_and_missing_project_are_refused(project):
    sheet_of(project).write_text(HEADER + row(1, "insertion", "A", "index.qmd:5", "PENDING") * 2,
                                 encoding="utf-8")
    with pytest.raises(InputError, match="renumber"):
        review(sheet_of(project), project, input_fn=Script(), print_fn=Output())
    with pytest.raises(InputError, match="project folder not found"):
        review(sheet_of(project), project / "nope", input_fn=Script(), print_fn=Output())
    with pytest.raises(InputError, match="not a merge worksheet"):
        review(project / "index.qmd", project, input_fn=Script(), print_fn=Output())
