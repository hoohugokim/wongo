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


# The scaffold example's layout: a multi-line HTML comment of writing rules
# sits above the prose. Its inner lines are never rendered, so no coauthor can
# have edited them, yet their length made one of them the fuzzy match for an
# insertion whose context crosses the Introduction heading.
COMMENT_QMD = (
    "---\n"
    'title: "Example"\n'
    "abstract: |\n"
    "  Replace this abstract with your own.\n"
    "---\n"
    "\n"
    "<!-- Writing rules (wongo):\n"
    "     - ONE SENTENCE PER LINE. Never reflow; the DOCX round-trip depends on it.\n"
    "     - Analysis numbers ONLY as inline R code, never typed by hand.\n"
    "     - Cross-references only via @fig-/@tbl-/@sec-; citations only via @citekey. -->\n"
    "\n"
    "# Introduction\n"
    "\n"
    "Constructed wetlands remove nitrate from agricultural runoff [@kadlec2009].\n"
    "This example estimates a first-order removal rate from ten days of synthetic data.\n"
)
TARGET = "Constructed wetlands remove nitrate from agricultural runoff [@kadlec2009]."


def _line_of(lines: list[str], text: str) -> int:
    return lines.index(text) + 1


def test_locate_never_points_inside_an_html_comment():
    lines = COMMENT_QMD.splitlines()
    insertion = Change("insertion", "Kim Coauthor", "", "efficiently",
                       "abstract with your own. # Introduction Constructed wetlands")

    assert locate(insertion, lines) == _line_of(lines, TARGET)


def test_the_scaffold_example_places_this_insertion_on_its_prose_line():
    from pathlib import Path

    import wongo

    example = Path(wongo.__file__).parent / "assets" / "scaffold-example" / "index.qmd"
    lines = example.read_text(encoding="utf-8").splitlines()
    insertion = Change("insertion", "Kim Coauthor", "", "efficiently",
                       "abstract with your own. # Introduction Constructed wetlands")

    assert locate(insertion, lines) == _line_of(lines, TARGET)


def test_prose_before_an_inline_comment_is_still_a_candidate():
    lines = [
        "Ponds settle solids first.",
        "Wetlands remove nitrate efficiently. <!-- TODO: cite a review -->",
        "<!-- a whole-line note -->",
        "Rates vary with temperature.",
    ]
    deletion = Change("deletion", "Kim", "efficiently", "",
                      "Ponds settle solids first. Wetlands remove nitrate")

    assert locate(deletion, lines) == 2


def test_an_insertion_is_placed_by_the_words_right_before_it():
    # The context is mostly the Methods sentence, which wins on similarity;
    # only its last words, "Removal was", say where the insertion happened.
    lines = [
        "# Methods",
        "",
        "Samples were filtered and stored at 4 °C before analysis of all ions.",
        "",
        "# Results",
        "",
        "Removal was fastest in June.",
    ]
    insertion = Change("insertion", "Kim", "", "clearly ",
                       "d stored at 4 °C before analysis of all ions. # Results Removal was")

    assert locate(insertion, lines) == 7


def test_old_text_that_follows_the_context_beats_a_similar_line_holding_it_too():
    lines = [
        "Twelve weeks after start-up we observed stable operation, and the reactor held its pH.",
        "Nitrate fell once the reactor warmed.",
    ]
    replacement = Change("replacement", "Kim", "the reactor", "the bioreactor",
                         "weeks after start-up we observed stable operation. Nitrate fell once")

    assert locate(replacement, lines) == 2


def test_without_an_anchor_the_fuzzy_match_still_applies():
    # rendered citation text in the context is not in the source, but the
    # old text alone still finds its line
    lines = ["Wetlands remove nitrate [@kadlec2009].", "Rates vary with temperature in every season."]
    deletion = Change("deletion", "Kim", "in every season", "",
                      "(Kadlec and Wallace 2009). Rates vary with temperature")

    assert locate(deletion, lines) == 2


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
