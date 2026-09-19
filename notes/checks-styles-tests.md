# notes: checks-styles-tests

Added two new test files, no `src/` or existing `tests/*` edits:

- `tests/test_run_checks.py` — 12 tests, all passing (no xfail needed).
- `tests/test_styles.py` — 9 tests, all passing (no xfail needed).

Total: 21 passed, 0 xfail.

## tests/test_run_checks.py

End-to-end `wongo.engine.checks.run_checks(project)` against `tmp_path`
projects. A helper (`make_project`) writes `_journal.yml`
(`journal: demo`, `ms_type: article`) plus a project-local profile at
`<project>/profiles/demo/profile.yml`. Per `wongo.profiles.candidate_dirs`,
`<project>/profiles` is tried first, so no monkeypatching of
`WONGO_PROFILES`/packaged profiles was needed.

Covered, one test (or pair) per required scenario:
- clean project -> every `Check.ok` is `True`.
- citekey used in `index.qmd` but absent from `refs.bib` -> HARD `citekeys`
  fails, missing key named in `detail`.
- `@fig-x` with no matching label -> HARD `crossrefs` fails, `fig-x` named.
- knitr chunk header ` ```{r fig-plot} ` counts as a `fig-plot` label
  definition -> no orphan (regression coverage for `LABEL_DEF_RE`'s third
  alternative).
- markdown image pointing at a missing file -> HARD `figures` fails, path
  named.
- body over `word_limit` -> HARD `word-limit` fails (plus a within-limit
  passing counterpart).
- `si.separate_file: true` without `si.qmd` -> WARN `si-file`, `ok=False`;
  with `si.qmd` present -> `ok=True`.
- `verified_date` 200 days old (> `STALE_DAYS`=183) -> WARN
  `profile-staleness`, `ok=False`, "200" in detail; fresh date -> `ok=True`.
- missing `index.qmd` -> `SystemExit`.

No source bugs found in `wongo.engine.checks`; behavior matched the
docstrings/comments exactly, including the knitr-chunk-label alternative in
`LABEL_DEF_RE` and the chunk-option caption harvesting in `prose()`.

## tests/test_styles.py

Uses plain `python-docx` `Document()` objects; styles missing from the
blank template (`Author`, `Abstract`) are added via
`doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)`.

Covered:
- `bold_caption_leads`: body-level `Caption`-styled paragraph
  `"Figure\xa01: A caption."` -> bold lead run `"Figure 1."` + non-bold
  `" A caption."`, justified. Table-cell caption `"Table S\xa02: SI
  caption"` -> bold lead `"Table S2."`. Prose `"Table 1 shows the
  result"` in a cell (no `[.:]` immediately after the digits) is left as
  a single unbolded run — confirms `_CAPTION_LEAD`'s stricter,
  delimiter-required table-cell pattern does the right thing.
- `rebuild_title_block`: two consecutive `Author`-styled paragraphs +
  one `Abstract`-styled paragraph collapse to one merged author
  paragraph containing both names with superscript run text `"a,*"` and
  `"a"`, one lettered affiliation line (`"a KIST, Seoul, Korea"`), a
  `"* Corresponding author:"` line, and an `"E-mail: jane@kist.re.kr
  (J. Q. Public)"` line. The original `Abstract` paragraph is untouched
  and appears exactly once afterward.
- `inject_keywords`: inserts `"Keywords: a, b"` immediately after the
  last `Abstract`-styled paragraph, left-aligned; no-op when
  `enabled=False`; no-op when no `Abstract` paragraph exists at all.
  Note: the function does `doc.paragraphs[abstract_idx[-1] + 1]` with no
  bounds check, so a test doc needs a paragraph *after* Abstract (matches
  real Quarto output, where Abstract is never the final paragraph) —
  otherwise this would `IndexError`. Not exercised as a bug since it
  isn't a realistic input shape; noted here for visibility only.
- `apply_page_geometry` against `load_style("kist-wcr")`: A4
  (210x297 mm) and the profile's margins (L/R 25 mm, T 30 mm, B 25 mm).
  **Rounding note (not a bug):** OOXML page geometry is stored in
  twentieths of a point (dxa, 635 EMU each); millimeter inputs that
  aren't exact multiples of 635 EMU round to the nearest dxa on
  round-trip (e.g. `Mm(210)` = 7,560,000 EMU is read back as 7,560,310
  EMU after `apply_page_geometry` sets it — `docx.shared.Mm` and the
  underlying `CT_PageSz`/`CT_PageMar` dxa storage disagree at
  sub-twip precision). This is inherent `python-docx`/OOXML unit
  precision, not a `wongo.styles` bug, so the test asserts within one
  dxa (635 EMU) tolerance rather than exact `Length` equality.
- `load_style("nope")` -> `SystemExit` whose message names `nope` and
  both known style profiles (`default`, `kist-wcr`).

No source bugs found in `wongo.styles` either; every behavior matched
what the module's docstrings and inline comments describe.
