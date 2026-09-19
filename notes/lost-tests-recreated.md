# Lost tests recreated (roundtrip parser + sectPr order)

Recreated two regression test files described as lost during a migration,
per the task brief and `docs/docx-quirks.md` (2026-07-03 entries). Did not
touch anything under `src/` or any pre-existing file under `tests/`.

## Files added

- `tests/test_roundtrip_parser.py` — pure-Python tests of
  `wongo.engine.roundtrip.extract_changes` / `locate` / `write_worksheet`
  against a hand-written markdown fixture (`PANDOC_MD`) that mirrors real
  `quarto pandoc --track-changes=all --wrap=none` span syntax as documented
  in docs/docx-quirks.md: edge whitespace outside spans, comment note text
  as comment-start's own bracket content, empty comment-end.
- `tests/test_sectpr_order.py` — python-docx `Document()` tests of
  `wongo.docxpatch.add_line_numbers` / `restart_page_numbering`, asserting
  ECMA-376 CT_SectPr child order (`lnNumType`/`pgNumType` before `cols`) and
  no duplicate elements on repeated calls.

## Coverage (test_roundtrip_parser.py)

- plain insertion / deletion / comment each extracted with correct
  kind/author/old/new.
- adjacent deletion+insertion by the *same* author collapses to one
  `replacement` change (old/new correctly split).
- the same adjacency by *different* authors stays two separate changes
  (`deletion` + `insertion`, each keeping its own author).
- a span whose bracket content itself contains nested square brackets
  (`[cited work [@doe2020] supports this]{.insertion ...}`) is surfaced as a
  `kind == "unparsed"` change (author "?", old/new "") rather than silently
  dropped — this exercises `extract_changes`'s marker-scanning safety net,
  since `SPAN_RE` cannot match nested brackets by design.
- `locate()` returns `None` for an unparsed change (explicit kind guard).
- `locate()` never resolves into YAML front matter: fixture has the *same*
  sentence once inside front matter (as a `|`-block-scalar value, so its
  stripped line text is byte-identical to the body line) and once in the
  body. Without the front-matter exclusion this would be a genuine
  scoring tie that the code's strict `score > best_score` comparison would
  resolve to the *first* (front-matter) occurrence — so this test actually
  exercises the guard, not just "picks the better match."
- changes are returned in document order even when the same inserted text
  ("recheck this") occurs twice, distinguished via each change's `context`
  tail ("...First" vs "...Second").
- `write_worksheet` (called positionally with the original four args —
  `changes, locations, out_path, source_name` — since the current source
  has no `qmd_name` kwarg yet) renders the unparsed row's "PARSER COULD NOT
  EXTRACT" warning and every row's "disposition: PENDING" line.

## Coverage (test_sectpr_order.py)

- `add_line_numbers(doc)` places `w:lnNumType` before `w:cols` in a blank
  `Document()`'s sectPr (which already ships `w:cols`/`w:docGrid`).
- `restart_page_numbering(doc)` places `w:pgNumType` before `w:cols`.
- calling `restart_page_numbering` first, then `add_line_numbers`, yields
  `lnNumType < pgNumType < cols` — this is the exact "subtle second bug"
  scenario called out in docs/docx-quirks.md (2026-07-03): lnNumType's
  successor list must include `w:pgNumType` itself, not just the shared
  `_SECT_PR_TAIL`, or it would land between pgNumType and cols instead of
  before both.
- calling both functions twice each does not duplicate `w:lnNumType` /
  `w:pgNumType` (idempotent "reuse existing element" branch).

## Result

All 14 new tests pass against current `src/` with no source changes and no
`xfail` needed — the sectPr ordering fix and the roundtrip parser both
behave exactly as documented in docs/docx-quirks.md. No new bugs found.

Ran the full suite once for interference-checking only (not to fix):
`tests/test_diff.py` (5 tests) and `tests/test_engine.py` (1 test:
`test_default_style_renders_without_page_geometry_and_keeps_reference_fonts`)
were already failing before and after adding these two files — unrelated to
this task, consistent with the concurrent engineer's in-flight edits to
`src/` and those existing test files. Not investigated further per the "do
not touch src/ or existing tests" boundary.
