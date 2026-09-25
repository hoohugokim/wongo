"""The merge worksheet model: lossless round trips, the disposition grammar,
mutations that keep every other byte, lint and counts. Synthetic text only."""
from __future__ import annotations

import pytest

from wongo.engine.roundtrip import Change, write_worksheet
from wongo.engine.worksheet import (
    GRAMMAR,
    Worksheet,
    check_disposition,
    parse,
    parse_disposition,
    read_target,
    serialize,
)
from wongo.errors import InputError

HEADER = (
    "# Merge worksheet — coauthor.docx — 2026-09-25\n"
    "\n"
    "Review each item; set disposition to one of: apply / reject: <reason> /\n"
    "fix-code (edit inside auto-generated output) / needs-PI.\n"
    "\n"
)

PROPOSE_APPLY = (
    "PROPOSED apply — but NOTE: the context is the abstract's closing sentence, so the "
    "true target is the front matter, not index.qmd:5. Prose edit, no generated numbers touched."
)
PROPOSE_REJECT = (
    'PROPOSED reject: bracketed placeholder text "[suggested edit]" (the deletion half of '
    "row 1's replacement) — see row 1 for the substantive judgment."
)
PROPOSE_FIX = (
    'PROPOSED fix-code — the coauthor hand-typed "(approximately 25%)" next to an inline R '
    "value; a hand-typed number never replaces a generated one."
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


UNPARSED = (
    "## 5. unparsed — ?\n"
    "- PARSER COULD NOT EXTRACT THIS CHANGE — open the DOCX and review this location manually.\n"
    "- location: index.qmd:UNMATCHED — find manually\n"
    "- context: …cited work [@doe2020…\n"
    "- disposition: PENDING\n"
    "\n"
)

AGENT = (
    HEADER
    + row(1, "replacement", "Jane Doe", "index.qmd:5", PROPOSE_APPLY, "reactors was", "reactors were")
    + row(2, "deletion", "Jane Doe", "index.qmd:6", PROPOSE_REJECT, "[suggested edit]")
    + row(3, "insertion", "김민수", "index.qmd:7", PROPOSE_FIX, new="(approximately 25%)")
    + row(4, "comment", "John Roe", "index.qmd:UNMATCHED — find manually", "PENDING",
          "the annotated span", "Please cite the original study.")
    + UNPARSED
)

QMD = (
    "---\n"
    'title: "A synthetic manuscript"\n'
    "---\n"
    "\n"
    "The two reactors was operated for 30 days.\n"  # 5
    "As shown in [suggested edit] the first table.\n"  # 6
    "Removal efficiency reached `r round(eff, 1)`% in reactor A.\n"  # 7
    "Earlier work is summarised here.\n"  # 8
    "Inline Quarto code gives `{r} n_samples` samples.\n"  # 9
    "Python code gives `{python} total` runs.\n"  # 10
)


def crlf(text: str) -> str:
    return text.replace("\n", "\r\n")


def replace_line(text: str, old: str, new: str) -> str:
    assert text.count(old) == 1, old
    return text.replace(old, new)


# ---------------------------------------------------------------------------
# Lossless round trips


HAND_EDITED = (
    "\ufeff# Merge worksheet — hand edited\r\n"
    "Notes the human typed above the rows.   \n"
    "\n"
    "## 1. insertion — Jane Doe\t\n"
    "- location: index.qmd:5\n"
    "- new: words\n"
    "- note: an unknown field the agent added\n"
    "- disposition: apply\n"
    "  a continuation line\n"
    "### a sub-heading inside the row\n"
    "   \n"
    "free text between rows, with a form feed \x0c and a line separator \u2028 inside\n"
    "## Notes (not a row heading)\n"
    "## 2. deletion - hyphen typed by hand\n"
    "- disposition: reject:\n"
    "## 3. comment — \n"
    "\n"
    "## 4. insertion — trailing row without newline\r"
)

ROUND_TRIPS = {
    "lf": AGENT.encode(),
    "crlf": crlf(AGENT).encode(),
    "bom-lf": b"\xef\xbb\xbf" + AGENT.encode(),
    "bom-crlf": b"\xef\xbb\xbf" + crlf(AGENT).encode(),
    "no-final-newline": AGENT.rstrip("\n").encode(),
    "crlf-no-final-newline": crlf(AGENT.rstrip("\n")).encode(),
    "mixed-endings": (AGENT[:200] + crlf(AGENT[200:])).encode(),
    "hand-edited": HAND_EDITED.encode(),
    "empty": b"",
    "bom-only": b"\xef\xbb\xbf",
    "just-newline": b"\n",
    "just-crlf": b"\r\n",
    "lone-cr": b"a\rb\r",
    "double-cr": b"x\r\r\ny\n",
    "preamble-only": HEADER.encode(),
}


@pytest.mark.parametrize("name", sorted(ROUND_TRIPS))
def test_serialize_parse_is_byte_identical(name):
    raw = ROUND_TRIPS[name]
    assert serialize(parse(raw)) == raw


@pytest.mark.parametrize("name", sorted(ROUND_TRIPS))
def test_load_then_save_rewrites_the_same_bytes(tmp_path, name):
    raw = ROUND_TRIPS[name]
    if b"\r\n" in raw and b"\n" in raw.replace(b"\r\n", b""):
        pytest.skip("mixed line endings are normalised on save (own test)")
    path = tmp_path / "merge.md"
    path.write_bytes(raw)
    ws = Worksheet.load(path)
    assert ws.serialize() == raw
    ws.save()
    assert path.read_bytes() == raw


def test_writer_output_round_trips_with_unparsed_and_unmatched_rows(tmp_path):
    out = tmp_path / "decisions" / "merge-20260925-coauthor.md"
    changes = [
        Change("insertion", "Jane Doe", "", "validated the assay", "Researchers"),
        Change("unparsed", "?", "", "", "Also [cited work [@doe2020"),
        Change("replacement", "김민수", "old phrase", "new phrase", "The"),
        Change("comment", "John Roe", "annotated", "Please check.", "Section 2"),
    ]
    write_worksheet(changes, [7, None, 9, None], out, "coauthor.docx")
    raw = out.read_bytes()
    ws = parse(raw)
    assert serialize(ws) == raw

    rows = ws.rows
    assert [(r.number, r.kind, r.author) for r in rows] == [
        (1, "insertion", "Jane Doe"), (2, "unparsed", "?"),
        (3, "replacement", "김민수"), (4, "comment", "John Roe"),
    ]
    assert (rows[0].qmd, rows[0].line, rows[0].unmatched) == ("index.qmd", 7, False)
    assert (rows[1].qmd, rows[1].line, rows[1].unmatched) == ("index.qmd", None, True)
    assert rows[1].extra[0].startswith("- PARSER COULD NOT EXTRACT THIS CHANGE")
    assert rows[0].old == "—" and rows[0].new == "validated the assay"
    assert all(r.disposition.state == "pending" for r in rows)
    assert ws.preamble[0].startswith("# Merge worksheet — coauthor.docx")

    # The same file as Windows writes it (Path.write_text translates to CRLF).
    windows = raw.replace(b"\n", b"\r\n")
    assert serialize(parse(windows)) == windows


def test_writer_output_survives_a_decision_on_every_row(tmp_path):
    out = tmp_path / "merge.md"
    changes = [Change("insertion", "A", "", "x", "c"), Change("deletion", "B", "y", "", "d")]
    write_worksheet(changes, [3, 4], out, "coauthor.docx")
    raw = out.read_text(encoding="utf-8")
    ws = Worksheet.load(out)
    ws.decide(1, "apply")
    ws.decide(2, "reject: duplicate")
    ws.save()
    expected = raw.replace("- disposition: PENDING", "- disposition: apply", 1)
    expected = expected.replace("- disposition: PENDING", "- disposition: reject: duplicate", 1)
    assert out.read_text(encoding="utf-8") == expected


# ---------------------------------------------------------------------------
# Parsing


def test_rows_fields_and_locations_are_parsed():
    ws = parse(AGENT)
    assert [r.number for r in ws.rows] == [1, 2, 3, 4, 5]
    first = ws.row(1)
    assert (first.kind, first.author, first.location) == ("replacement", "Jane Doe", "index.qmd:5")
    assert (first.qmd, first.line, first.unmatched) == ("index.qmd", 5, False)
    assert (first.old, first.new, first.context) == ("reactors was", "reactors were", "…context…")
    assert first.disposition.state == "proposed"
    assert first.disposition.proposal == "apply"
    assert first.disposition.note.startswith("but NOTE: the context")
    assert ws.row(2).disposition.proposal == "reject"
    assert ws.row(2).disposition.note.startswith('bracketed placeholder text "[suggested edit]"')
    assert ws.row(3).disposition.proposal == "fix-code"
    assert ws.row(3).author == "김민수"
    fourth = ws.row(4)
    assert (fourth.qmd, fourth.line, fourth.unmatched) == ("index.qmd", None, True)
    assert ws.row(5).kind == "unparsed"


def test_continuation_lines_belong_to_the_disposition():
    text = HEADER + row(1, "insertion", "A", "index.qmd:5", "PROPOSED apply — the coauthor fixed") + ""
    text = text.replace(
        "- disposition: PROPOSED apply — the coauthor fixed\n",
        "- disposition: PROPOSED apply — the coauthor fixed\n"
        "  a grammar slip; the sentence has no generated numbers.\n"
        "Still the same rationale.\n"
        "- note: a field ends the continuation\n"
        "not a continuation any more\n",
    )
    ws = parse(text)
    r = ws.row(1)
    assert r.disposition_text == r.disposition.text == (
        "PROPOSED apply — the coauthor fixed\n"
        "a grammar slip; the sentence has no generated numbers.\n"
        "Still the same rationale."
    )
    assert r.disposition.note == (
        "the coauthor fixed a grammar slip; the sentence has no generated numbers. "
        "Still the same rationale."
    )
    assert r.extra == ("- note: a field ends the continuation", "not a continuation any more")


def test_hand_edited_worksheet_parses_leniently():
    ws = parse(HAND_EDITED.encode())
    assert ws.bom is True
    assert [r.number for r in ws.rows] == [1, 2, 3, 4]
    assert ws.row(1).author == "Jane Doe"
    assert ws.row(1).disposition.decision == "apply"
    assert ws.row(1).disposition.note == "a continuation line"
    assert ws.row(2).author == "hyphen typed by hand"
    assert ws.row(2).disposition.state == "invalid"
    assert ws.row(3).author == ""
    assert ws.row(4).disposition.state == "invalid"  # no disposition line
    assert ws.row(4).disposition_index is None
    # Only LF ends a line (str.splitlines would also split at U+2028 and form feeds).
    odd = parse("## 1. insertion — A\u2028B\x0cC\r\n- disposition: apply\n")
    assert odd.row(1).author == "A\u2028B\x0cC"
    assert odd.row(1).disposition.decision == "apply"


@pytest.mark.parametrize(
    ("text", "state", "decision", "proposal", "note"),
    [
        ("PENDING", "pending", None, None, ""),
        ("pending — ask the PI first", "pending", None, None, "ask the PI first"),
        ("apply", "final", "apply", None, ""),
        ("Apply — prose only", "final", "apply", None, "prose only"),
        ("apply: fine", "final", "apply", None, "fine"),
        ("apply — -5 °C is right", "final", "apply", None, "-5 °C is right"),
        ("fix-code", "final", "fix-code", None, ""),
        ("FIX-CODE — edit the R chunk", "final", "fix-code", None, "edit the R chunk"),
        ("needs-PI", "final", "needs-PI", None, ""),
        ("needs-pi — scope question", "final", "needs-PI", None, "scope question"),
        ("reject: duplicate sentence", "final", "reject", None, "duplicate sentence"),
        ("REJECT : 중복 표현", "final", "reject", None, "중복 표현"),
        ("reject:no space", "final", "reject", None, "no space"),
        ("PROPOSED apply", "proposed", None, "apply", ""),
        (PROPOSE_APPLY, "proposed", None, "apply", PROPOSE_APPLY[len("PROPOSED apply — "):]),
        (PROPOSE_REJECT, "proposed", None, "reject", PROPOSE_REJECT[len("PROPOSED reject: "):]),
        (PROPOSE_FIX, "proposed", None, "fix-code", PROPOSE_FIX[len("PROPOSED fix-code — "):]),
        ("proposed needs-PI — funding wording", "proposed", None, "needs-PI", "funding wording"),
        ("PROPOSED: apply", "proposed", None, "apply", ""),
    ],
)
def test_disposition_grammar(text, state, decision, proposal, note):
    d = parse_disposition(text)
    assert (d.state, d.decision, d.proposal, d.note) == (state, decision, proposal, note)
    assert d.problem is None


@pytest.mark.parametrize(
    ("text", "problem"),
    [
        ("", "empty"),
        ("   ", "empty"),
        ("approve", "`approve` is not a disposition"),
        ("applying", "`applying` is not a disposition"),
        ("fix code", "`fix` is not a disposition"),
        ("needs PI", "`needs` is not a disposition"),
        ("**apply**", "`**apply**` is not a disposition"),
        ("reject", "reject needs a colon and a reason"),
        ("reject — duplicate", "reject needs a colon and a reason"),
        ("reject:", "reject needs a reason after the colon"),
        ("reject:    ", "reject needs a reason after the colon"),
        ("PROPOSED", "PROPOSED must be followed by a decision"),
        ("PROPOSED maybe apply", "PROPOSED must be followed by a decision"),
        ("PROPOSED PENDING", "PROPOSED must be followed by a decision"),
        ("PROPOSED PROPOSED apply", "PROPOSED must be followed by a decision"),
        ("PROPOSED reject:", "reject needs a reason after the colon"),
    ],
)
def test_invalid_dispositions(text, problem):
    d = parse_disposition(text)
    assert d.state == "invalid"
    assert problem in d.problem
    assert d.label == "INVALID"


def test_labels_use_canonical_spelling():
    assert parse_disposition("needs-pi").label == "needs-PI"
    assert parse_disposition("proposed REJECT: x").label == "PROPOSED reject"
    assert parse_disposition("pending").label == "PENDING"


def test_check_disposition_gives_a_one_line_grammar_reminder():
    with pytest.raises(InputError) as exc:
        check_disposition("reject:")
    message = str(exc.value)
    assert "reject needs a reason" in message and GRAMMAR in message and "\n" not in message
    with pytest.raises(InputError, match="single line"):
        check_disposition("apply\nreject: x")


# ---------------------------------------------------------------------------
# Mutations


def test_set_disposition_replaces_only_the_first_line_value():
    ws = parse(AGENT)
    r = ws.set_disposition(4, "reject: 중복 표현")
    assert r.disposition.decision == "reject" and r.disposition.note == "중복 표현"
    assert ws.text() == replace_line(
        AGENT,
        "- disposition: PENDING\n\n## 5.",
        "- disposition: reject: 중복 표현\n\n## 5.",
    )


def test_set_disposition_keeps_continuation_lines_and_crlf():
    text = crlf(HEADER + row(1, "insertion", "A", "index.qmd:5", "PROPOSED apply — why")
                .replace("why\n", "why\n  more rationale\n"))
    ws = parse(text.encode())
    ws.set_disposition(1, "PENDING")
    assert ws.serialize() == replace_line(
        text, "- disposition: PROPOSED apply — why\r\n", "- disposition: PENDING\r\n"
    ).encode()
    assert ws.row(1).disposition.text == "PENDING\nmore rationale"


@pytest.mark.parametrize("value", ["approve", "reject", "reject:", "", "PROPOSED maybe"])
def test_set_disposition_rejects_invalid_values_without_changing_anything(value):
    ws = parse(AGENT)
    with pytest.raises(InputError) as exc:
        ws.set_disposition(4, value)
    assert GRAMMAR in str(exc.value)
    assert ws.text() == AGENT


def test_set_disposition_inserts_a_missing_disposition_line():
    text = HEADER + "## 1. insertion — A\n- location: index.qmd:5\n- new: words\n\n## 2. deletion — B\n"
    ws = parse(text)
    ws.set_disposition(1, "apply")
    ws.set_disposition(2, "needs-PI")
    assert ws.text() == (
        HEADER + "## 1. insertion — A\n- location: index.qmd:5\n- new: words\n"
        "- disposition: apply\n\n## 2. deletion — B\n- disposition: needs-PI\n"
    )


def test_insert_at_end_of_file_keeps_the_missing_final_newline():
    ws = parse("## 1. insertion — A")
    ws.set_disposition(1, "apply")
    assert ws.text() == "## 1. insertion — A\n- disposition: apply"


def test_row_lookup_errors_are_actionable():
    ws = parse(AGENT)
    with pytest.raises(InputError, match=r"row 9 is not in the worksheet \(its rows: 1-5\)"):
        ws.set_disposition(9, "apply")
    dup = parse(HEADER + row(1, "insertion", "A", "index.qmd:5", "PENDING") * 2)
    with pytest.raises(InputError, match="used by 2 rows"):
        dup.set_disposition(1, "apply")
    assert dup.find(1) is None


def test_accept_proposal_removes_only_the_prefix():
    ws = parse(AGENT)
    r = ws.accept_proposal(1)
    assert r.disposition.state == "final" and r.disposition.decision == "apply"
    assert ws.text() == replace_line(AGENT, f"- disposition: {PROPOSE_APPLY}\n",
                                     f"- disposition: {PROPOSE_APPLY[len('PROPOSED '):]}\n")
    with pytest.raises(InputError, match="no proposal to accept"):
        ws.accept_proposal(1)
    with pytest.raises(InputError, match="no proposal to accept"):
        ws.accept_proposal(4)


def test_accept_proposal_written_on_a_continuation_line():
    base = HEADER + "## 1. insertion — A\n- location: index.qmd:5\n"
    ws = parse(base + "- disposition:\n  PROPOSED\n  apply — the reason\n")
    assert ws.row(1).disposition.proposal == "apply"
    ws.accept_proposal(1)
    assert ws.text() == base + "- disposition:\n  apply — the reason\n"
    assert ws.row(1).disposition.decision == "apply"


def test_decide_same_as_proposal_accepts_it():
    ws = parse(AGENT)
    r = ws.decide(1, "apply")
    assert r.disposition.text == PROPOSE_APPLY[len("PROPOSED "):]
    r = ws.decide(2, "reject: " + PROPOSE_REJECT[len("PROPOSED reject: "):])
    assert r.disposition.text == PROPOSE_REJECT[len("PROPOSED "):]


def test_decide_differently_keeps_the_proposal_on_record():
    ws = parse(AGENT)
    r = ws.decide(1, "fix-code")
    assert r.disposition.text == f"fix-code — was {PROPOSE_APPLY}"
    assert (r.disposition.state, r.disposition.decision) == ("final", "fix-code")
    r = ws.decide(3, "apply")
    assert r.disposition.text == f"apply — was {PROPOSE_FIX}"
    r = ws.decide(2, "reject: 중복 표현")
    assert r.disposition.text == f"reject: 중복 표현 — was {PROPOSE_REJECT}"
    assert r.disposition.note.startswith("중복 표현 — was PROPOSED reject:")


def test_decide_with_a_note_of_ones_own_keeps_both():
    ws = parse(AGENT)
    r = ws.decide(1, "apply — checked the front matter too")
    assert r.disposition.text == f"apply — checked the front matter too — was {PROPOSE_APPLY}"


def test_decide_keeps_continuation_lines_after_the_first_line():
    text = HEADER + row(1, "insertion", "A", "index.qmd:5", "PROPOSED apply — why").replace(
        "why\n", "why\n  second line of rationale\n")
    ws = parse(text)
    ws.decide(1, "needs-PI")
    assert ws.text() == replace_line(
        text,
        "- disposition: PROPOSED apply — why\n",
        "- disposition: needs-PI — was PROPOSED apply — why\n",
    )
    assert ws.row(1).disposition.decision == "needs-PI"


def test_decide_replaces_pending_and_keeps_invalid_text():
    ws = parse(AGENT)
    assert ws.decide(4, "reject: off topic").disposition.text == "reject: off topic"
    ws.set_disposition(4, "PENDING")
    bad = parse(HEADER + row(1, "insertion", "A", "index.qmd:5", "approve — reads better"))
    assert bad.decide(1, "apply").disposition.text == "apply — was approve — reads better"
    same = parse(HEADER + row(1, "insertion", "A", "index.qmd:5", "apply"))
    before = same.text()
    same.decide(1, "apply")
    assert same.text() == before


@pytest.mark.parametrize("value", ["PENDING", "PROPOSED apply", "reject:", "maybe"])
def test_decide_requires_a_final_value(value):
    ws = parse(AGENT)
    with pytest.raises(InputError):
        ws.decide(1, value)
    assert ws.text() == AGENT


def test_set_location_rewrites_unmatched_and_keeps_the_qmd_name():
    ws = parse(AGENT)
    r = ws.set_location(4, 42)
    assert (r.location, r.qmd, r.line, r.unmatched) == ("index.qmd:42", "index.qmd", 42, False)
    assert ws.text() == replace_line(
        AGENT,
        "- location: index.qmd:UNMATCHED — find manually\n- old: the annotated span",
        "- location: index.qmd:42\n- old: the annotated span",
    )
    si = parse(HEADER + row(1, "insertion", "A", "si.qmd:UNMATCHED — find manually", "PENDING"))
    assert si.set_location(1, 7).location == "si.qmd:7"


def test_set_location_inserts_a_missing_location_line():
    text = HEADER + row(1, "insertion", "A", "si.qmd:3", "PENDING") + "## 2. deletion — B\n- disposition: PENDING\n"
    ws = parse(text)
    ws.set_location(2, 9)
    assert ws.text().endswith("## 2. deletion — B\n- location: si.qmd:9\n- disposition: PENDING\n")
    bare = parse("## 1. deletion — B\n- disposition: PENDING\n")
    assert bare.set_location(1, 4).location == "index.qmd:4"


@pytest.mark.parametrize("line", [0, -3, True, "12", 4.0])
def test_set_location_needs_a_positive_whole_number(line):
    ws = parse(AGENT)
    with pytest.raises(InputError, match="whole number"):
        ws.set_location(4, line)


# ---------------------------------------------------------------------------
# Lint and counts


def errors(problems):
    return {(p.row, p.message.split(" — ")[0]) for p in problems if p.severity == "error"}


def test_lint_flags_every_undecided_row():
    problems = parse(AGENT).lint()
    by_row = {p.row: p for p in problems}
    assert set(by_row) == {1, 2, 3, 4, 5}
    assert all(p.severity == "error" for p in problems)
    assert by_row[1].message.startswith("PROPOSED apply is not confirmed")
    assert by_row[4].message.startswith("still PENDING")
    assert str(by_row[4]).startswith("row 4: error: still PENDING")


def test_lint_errors_for_bad_finals():
    text = (
        HEADER
        + row(1, "insertion", "A", "index.qmd:UNMATCHED — find manually", "apply")
        + UNPARSED.replace("## 5.", "## 2.").replace("PENDING", "apply")
        + row(3, "deletion", "A", "index.qmd:5", "reject:")
        + row(4, "deletion", "A", "index.qmd:5", "approve")
        + row(5, "deletion", "A", "index.qmd:5", "apply").replace(
            "- disposition: apply\n", "- disposition: apply\n- disposition: reject: x\n")
        + "## 6. insertion — A\n- location: index.qmd:5\n\n"
        + row(7, "insertion", "A", "index.qmd:5", "apply")
        + row(7, "insertion", "B", "index.qmd:6", "apply")
    )
    problems = parse(text).lint()
    messages = {(p.row, p.severity): p.message for p in problems}
    assert "location is UNMATCHED" in messages[(1, "error")]
    assert "unparsed row" in messages[(2, "error")]
    assert "reject needs a reason" in messages[(3, "error")]
    assert "`approve` is not a disposition" in messages[(4, "error")]
    assert "more than one `- disposition:` line" in messages[(5, "error")]
    assert "no `- disposition:` line" in messages[(6, "error")]
    assert "row number 7 is used by 2 rows" in messages[(7, "error")]


def test_lint_passes_a_fully_decided_worksheet():
    text = (
        HEADER
        + row(1, "insertion", "A", "index.qmd:5", "apply — prose")
        + row(2, "deletion", "A", "index.qmd:UNMATCHED — find manually", "reject: 중복 표현")
        + row(3, "comment", "A", "index.qmd:UNMATCHED — find manually", "needs-PI")
        + UNPARSED.replace("## 5.", "## 4.").replace("PENDING", "fix-code — cite doe2020 in the R table")
    )
    assert parse(text).lint() == []


def test_lint_with_project_warns_about_target_lines(tmp_path):
    (tmp_path / "index.qmd").write_text(QMD, encoding="utf-8")
    text = (
        HEADER
        + row(1, "insertion", "A", "index.qmd:5", "apply")  # plain prose: no warning
        + row(2, "insertion", "A", "index.qmd:7", "apply")  # `r
        + row(3, "insertion", "A", "index.qmd:9", "apply")  # `{r}
        + row(4, "insertion", "A", "index.qmd:10", "apply")  # `{python}
        + row(5, "insertion", "A", "index.qmd:99", "apply")  # beyond the end
        + row(6, "insertion", "A", "index.qmd:7", "reject: not applied, no warning")
        + row(7, "insertion", "A", "chapter.qmd:1", "apply")  # missing file
        + row(8, "insertion", "A", "chapter.qmd:2", "apply")  # reported once
        + row(9, "insertion", "A", "front matter", "apply")  # not <file>:<line>
    )
    ws = parse(text)
    assert [p for p in ws.lint() if p.row in (2, 3, 4, 5, 7)] == []  # no project, no reading
    problems = ws.lint(project=tmp_path)
    assert all(p.severity == "warning" for p in problems)
    rows = [p.row for p in problems]
    assert rows == [2, 3, 4, 5, 7, 9]
    text_of = {p.row: p.message for p in problems}
    assert "inline code" in text_of[2] and "index.qmd:7" in text_of[2]
    assert "inline code" in text_of[3] and "inline code" in text_of[4]
    assert "beyond its end" in text_of[5] and "10 lines" in text_of[5]
    assert "chapter.qmd not found" in text_of[7] and "--project" in text_of[7]
    assert "not `<file>:<line>`" in text_of[9]


def test_lint_warns_when_there_are_no_rows():
    problems = parse(HEADER).lint()
    assert [(p.severity, p.row) for p in problems] == [("warning", None)]
    assert str(problems[0]).startswith("worksheet: warning: no rows found")


def test_counts_by_state_and_decision():
    ws = parse(AGENT)
    ws.decide(1, "apply")
    ws.set_disposition(4, "reject: off topic")
    c = ws.counts()
    assert (c.total, c.pending, c.proposed, c.final, c.invalid) == (5, 1, 2, 2, 0)
    assert c.decisions == {"apply": 1, "reject": 1, "fix-code": 0, "needs-PI": 0}
    assert c.proposals == {"apply": 0, "reject": 1, "fix-code": 1, "needs-PI": 0}
    assert c.needs_decision == 3
    ws.set_disposition(5, "apply")  # blocked: an unparsed row cannot be applied
    assert ws.counts().needs_decision == 3
    assert ws.row(5).needs_decision and ws.row(5).apply_blocker


def test_read_target(tmp_path):
    (tmp_path / "index.qmd").write_text(QMD, encoding="utf-8")
    ws = parse(AGENT)
    t = read_target(tmp_path, ws.row(1))
    assert (t.line, t.text, t.inline_code) == (5, "The two reactors was operated for 30 days.", False)
    assert read_target(tmp_path, ws.row(3)).inline_code is True
    t = read_target(tmp_path, ws.row(4))
    assert (t.text, t.reason) == (None, "unmatched")
    far = parse(HEADER + row(1, "insertion", "A", "index.qmd:11", "apply"))
    assert read_target(tmp_path, far.row(1)).reason == "beyond-end"
    assert read_target(tmp_path / "nowhere", ws.row(1)).reason == "missing-file"


# ---------------------------------------------------------------------------
# Files


def test_save_keeps_bom_crlf_and_changes_one_line(tmp_path):
    path = tmp_path / "merge.md"
    raw = b"\xef\xbb\xbf" + crlf(AGENT).encode()
    path.write_bytes(raw)
    ws = Worksheet.load(path)
    ws.decide(4, "reject: 중복 표현")
    ws.save()
    expected = raw.replace(
        b"- disposition: PENDING\r\n\r\n## 5.",
        "- disposition: reject: 중복 표현\r\n\r\n## 5.".encode(),
    )
    assert path.read_bytes() == expected
    assert [p.name for p in tmp_path.iterdir()] == ["merge.md"]  # no temp file left


def test_save_keeps_a_missing_final_newline(tmp_path):
    path = tmp_path / "merge.md"
    text = AGENT.rstrip("\n")
    path.write_text(text, encoding="utf-8", newline="")
    ws = Worksheet.load(path)
    ws.set_disposition(5, "needs-PI")
    ws.save()
    assert path.read_bytes() == text.replace(
        "- disposition: PENDING", "- disposition: needs-PI").replace(
        "- disposition: needs-PI", "- disposition: PENDING", 1).encode()


def test_save_normalises_mixed_line_endings_to_crlf(tmp_path):
    path = tmp_path / "merge.md"
    path.write_bytes(ROUND_TRIPS["mixed-endings"])
    Worksheet.load(path).save()
    assert path.read_bytes() == crlf(AGENT).encode()


def test_save_refuses_to_overwrite_an_outside_edit(tmp_path):
    path = tmp_path / "merge.md"
    path.write_text(AGENT, encoding="utf-8", newline="")
    ws = Worksheet.load(path)
    ws.set_disposition(4, "needs-PI")
    edited = AGENT.replace("Please cite the original study.", "Please cite it.")
    path.write_text(edited, encoding="utf-8", newline="")
    with pytest.raises(InputError, match="changed on disk"):
        ws.save()
    assert path.read_text(encoding="utf-8") == edited
    ws.save(tmp_path / "copy.md")  # saving elsewhere is fine
    assert "needs-PI" in (tmp_path / "copy.md").read_text(encoding="utf-8")


def test_worksheet_never_writes_or_reads_a_qmd(tmp_path):
    qmd = tmp_path / "index.qmd"
    qmd.write_text(QMD, encoding="utf-8")
    ws = parse(AGENT)
    with pytest.raises(InputError, match="never edits a .qmd"):
        ws.save(qmd)
    with pytest.raises(InputError, match="not a merge worksheet"):
        Worksheet.load(qmd)
    assert qmd.read_text(encoding="utf-8") == QMD


def test_load_errors_are_actionable(tmp_path):
    with pytest.raises(InputError, match="worksheet not found.*wongo roundtrip"):
        Worksheet.load(tmp_path / "missing.md")
    with pytest.raises(InputError, match="is a folder"):
        Worksheet.load(tmp_path)
    bad = tmp_path / "cp949.md"
    bad.write_bytes("## 1. insertion 김민수\n".encode("cp949"))
    with pytest.raises(InputError, match="not UTF-8.*Save with Encoding"):
        Worksheet.load(bad)
