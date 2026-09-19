"""Regression tests recreated for wongo.engine.roundtrip's tracked-changes
parser (extract_changes / locate) and write_worksheet, pinning the behavior
documented in docs/docx-quirks.md (2026-07-03 entries). The originals were
lost in a migration; see notes/lost-tests-recreated.md for provenance and any
bugs found while recreating them.
"""
from __future__ import annotations

from wongo.engine.roundtrip import Change, extract_changes, locate, write_worksheet

# Mirrors REAL `quarto pandoc --track-changes=all --wrap=none` output syntax,
# per docs/docx-quirks.md (2026-07-03): edge whitespace sits OUTSIDE the span,
# a comment's note text is the comment-start span's own bracket content (not
# a `comment="..."` attribute), and comment-end is always empty.
PANDOC_MD = (
    'Researchers [validated the assay]{.insertion author="Jane Doe" '
    'date="2026-07-03T10:00:00Z"} before submission.\n\n'
    'The [redundant clause]{.deletion author="Jane Doe" '
    'date="2026-07-03T10:00:00Z"} was removed.\n\n'
    'Section 2 [the reviewer note]{.comment-start id="0" author="Jane Doe" '
    'date="2026-07-03T10:00:00Z"}discusses the annotated finding'
    '[]{.comment-end id="0"} in detail.\n\n'
    'The [old phrase]{.deletion author="Jane Doe" date="2026-07-03T10:00:00Z"}'
    '[new phrase]{.insertion author="Jane Doe" date="2026-07-03T10:00:00Z"} '
    'continues.\n\n'
    'The [former text]{.deletion author="Jane Doe" date="2026-07-03T10:00:00Z"}'
    '[latter text]{.insertion author="John Roe" date="2026-07-03T10:00:00Z"} '
    'continues.\n\n'
    'Also [cited work [@doe2020] supports this]{.insertion author="Jane Doe" '
    'date="2026-07-03T10:00:00Z"} elsewhere.\n\n'
    'First [recheck this]{.insertion author="Ada Lin" date="2026-07-03T10:00:00Z"} '
    'spot.\n\n'
    'Second [recheck this]{.insertion author="Ada Lin" date="2026-07-03T10:00:00Z"} '
    'spot too.\n'
)


def _changes():
    return extract_changes(PANDOC_MD)


def test_plain_insertion_extracted():
    c = next(c for c in _changes() if c.kind == "insertion" and c.new == "validated the assay")
    assert c.author == "Jane Doe"
    assert c.old == ""


def test_plain_deletion_extracted():
    c = next(c for c in _changes() if c.kind == "deletion" and c.old == "redundant clause")
    assert c.author == "Jane Doe"
    assert c.new == ""


def test_plain_comment_extracted():
    c = next(c for c in _changes() if c.kind == "comment")
    assert c.author == "Jane Doe"
    assert c.new == "the reviewer note"
    assert c.old == "discusses the annotated finding"


def test_adjacent_same_author_del_ins_becomes_one_replacement():
    replacements = [c for c in _changes() if c.kind == "replacement"]
    assert len(replacements) == 1
    r = replacements[0]
    assert r.author == "Jane Doe"
    assert r.old == "old phrase"
    assert r.new == "new phrase"


def test_adjacent_different_author_del_ins_stays_two_changes():
    changes = _changes()
    assert not any(c.kind == "replacement" and c.old == "former text" for c in changes)
    deletion = next(c for c in changes if c.kind == "deletion" and c.old == "former text")
    insertion = next(c for c in changes if c.kind == "insertion" and c.new == "latter text")
    assert deletion.author == "Jane Doe"
    assert insertion.author == "John Roe"


def test_nested_bracket_span_surfaces_as_unparsed_not_dropped():
    unparsed = [c for c in _changes() if c.kind == "unparsed"]
    assert len(unparsed) == 1
    u = unparsed[0]
    assert u.author == "?"
    assert u.old == ""
    assert u.new == ""


def test_locate_returns_none_for_unparsed():
    unparsed = next(c for c in _changes() if c.kind == "unparsed")
    qmd_lines = ["Some unrelated line.", "Another line of prose."]
    assert locate(unparsed, qmd_lines) is None


# A duplicate sentence, once inside front matter (as a YAML block-scalar
# value, so the raw line's stripped text is byte-identical to the body
# line's) and once in the body. Without the front-matter exclusion, the
# front-matter occurrence would win the difflib tie (it's encountered first
# and `score > best_score` is a strict inequality, so an equal-scoring later
# candidate never overwrites it).
FRONT_MATTER_QMD = (
    "---\n"
    "title: Test\n"
    "abstract: |\n"
    "  The catalyst degrades in strong light.\n"
    "---\n"
    "\n"
    "# Introduction\n"
    "\n"
    "The catalyst degrades in strong light.\n"
)


def test_locate_never_points_into_front_matter():
    qmd_lines = FRONT_MATTER_QMD.splitlines()
    sentence = "The catalyst degrades in strong light."
    occurrences = [i for i, line in enumerate(qmd_lines, start=1) if line.strip() == sentence]
    assert len(occurrences) == 2  # once in front matter, once in the body
    _front_matter_idx, body_idx = occurrences

    change = Change(kind="deletion", author="Jane Doe", old=sentence, new="", context="")
    assert locate(change, qmd_lines) == body_idx


def test_changes_returned_in_document_order_for_duplicate_text():
    dupes = [c for c in _changes() if c.new == "recheck this"]
    assert len(dupes) == 2
    first, second = dupes
    assert first.context.endswith("First")
    assert second.context.endswith("Second")


def test_write_worksheet_flags_unparsed_and_marks_all_pending(tmp_path):
    changes = _changes()
    locations = [None] * len(changes)
    out = tmp_path / "worksheet.md"

    write_worksheet(changes, locations, out, "coauthor.docx")

    text = out.read_text(encoding="utf-8")
    assert "PARSER COULD NOT EXTRACT" in text
    assert text.count("- disposition: PENDING") == len(changes)
