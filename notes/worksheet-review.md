# S4 worksheet review: model, `wongo review`, `wongo worksheet` — 2026-09-25

Step 3 of notes/tui-feasibility-2026-09-25.md: read the merge worksheet back,
check it, and let a person decide rows at a terminal. New files only; no
existing file was changed. Nothing here writes a .qmd.

## What was built

- `src/wongo/engine/worksheet.py`: a lossless model. The file is held as
  exact lines (content plus its own ending), and rows are parsed views over
  them. `serialize(parse(raw)) == raw` for any bytes. Covers the disposition
  grammar, `set_disposition`, `accept_proposal`, `decide`, `set_location`,
  `lint(project=None)`, `counts()` and `read_target()`.
- `src/wongo/review.py`: `review(path, project, *, input_fn, print_fn)`. A
  standard-library prompt loop. All choices are digits followed by Enter, and
  the file is saved after every decision.
- `src/wongo/worksheet_cli.py`: `add_parsers(sub, common)` adds
  `worksheet status|lint|set` and `review`. To wire it into `cli.py`, call
  `add_parsers(sub, common)` after `sub` exists. `common` must not define
  `--project`, because lint and review add their own.
- Tests: `tests/test_worksheet.py`, `test_review.py`, `test_worksheet_cli.py`
  (160 passed, 3 skipped by design). All fixtures are synthetic.

## Design decisions

- **Line splitting.** Lines split on LF only; CRLF is kept as the line ending.
  `str.splitlines` would also split at U+2028, form feeds and lone CRs and
  break both the round trip and the line numbering.
- **Saving.** `save()` goes through `textio.write_text_atomic`, which keeps the
  BOM (written as U+FEFF) and one line-ending style. A file with *mixed*
  endings is written as all CRLF, following the `detect_newline` rule. The
  in-memory `serialize()` output stays exact.
- **No lost edits.** `save()` will not overwrite the file it loaded if the file
  changed on disk since. `review` reloads the file before each row and again
  before each save. If the row on screen changed, it is shown again. Edits to
  other rows are kept.
- **`decide()` goes a little beyond the spec.** Choosing the same decision as
  the proposal accepts it. Any other choice writes
  `<value> — was <old first line>`, which covers three more cases: the person
  adds a different note, the old value is invalid, or the old value is a
  blocked `apply`. Neither the agent's text nor the person's is lost. Only
  PENDING is replaced outright.
- **Blocked applies.** A final `apply` on an UNMATCHED or `unparsed` row counts
  as `needs_decision`. `review` offers such rows, so lint passes after a
  complete review.
- **Pressing Enter on `PROPOSED apply`** goes through the same guards as `1`:
  it is refused on UNMATCHED or unparsed rows, and an inline-code line asks
  for the row number.
- **Additions to the prompt spec.**
  - `0` alone at the reject-reason prompt goes back to the menu, so a
    mistaken `2` cannot trap the user.
  - Menu answers are NFKC-normalised, so full-width digits from an IME work.
    Reasons are stored as typed, with whitespace collapsed.
  - A progress line `(k of n to review)` precedes each row header.
- **Parser leniency.**
  - Keywords are case-insensitive, and `PROPOSED:` is accepted.
  - A note may follow `—`, `–`, `-`, `:`, `;` or `,`.
  - `reject` still needs a colon and a non-empty reason.
  - A row heading may use an en dash or hyphen and may have an empty author.
    Hand-added rows would otherwise merge into the row above as a confusing
    "two disposition lines" error.
- **Lint output.** Lines read `row N: error: …`, `row N: warning: …` or
  `worksheet: warning: …`.
  - Lint takes `--project DIR`, with the same default as review, for the
    target-line warnings. A missing .qmd is reported once.
  - Repeated row numbers are an error. Mutations and review refuse them.
- **CLI conveniences.** A bare worksheet name is also looked up in
  `./decisions/`, because roundtrip's new header prints
  `wongo review <name>` without the folder. `worksheet set` joins unquoted
  words, validates before touching anything, and does not write when nothing
  changed. `review --json` raises InputError, so `--json` still yields exactly
  one JSON object: the error.
- **No .qmd writes.** `Worksheet.load` and `Worksheet.save` both refuse a
  `.qmd` path.

## Open questions

- Should a mixed-ending file keep its exact bytes on save? That would need a
  byte-level atomic write outside `write_text_atomic`.
- Should the roundtrip header print `decisions/<name>`? It would make the
  fallback unnecessary.
- `needs-PI` is a valid final value, so lint passes with such rows. Is that
  "ready to apply"? The next-step text mentions them.
- A comment that spans several paragraphs puts extra lines under `old:`. The
  model keeps them, and review shows them verbatim below the fields; only the
  first line is labelled.
- Should `review` revisit skipped rows at the end of a session? Today the user
  re-runs it.
- Re-deciding a row stacks `— was …` history on its first line.
