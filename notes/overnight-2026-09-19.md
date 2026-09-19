# Overnight work report — wongo — 2026-09-19

Prepared by Claude Fable 5.1 (orchestrating thread) with three Sonnet subagents
(tests and docs). Nothing was committed; the working tree is left green for your
review. Read this top to bottom, then `git diff`.

## 1. Headline

| Metric | Before (HEAD `ad6019d` + pending diff) | After |
|---|---|---|
| Tests | 29 passed | 102 passed (Python 3.13 and 3.11) |
| Ruff | passes (ad-hoc command, not in CI) | passes (configured in `pyproject.toml`, CI lint step) |
| `wongo render` with `style: default` | crashes with `TypeError`, leaves half-processed DOCX | renders both targets |
| `wongo diff` on a real Quarto paragraph with a crossref | skipped as "rich OOXML" | tracked, link preserved, roundtrip-readable |
| SI cover "N tables" | counts every figure wrapper as a table | counts floats by caption semantics |
| Modified files vs HEAD | — | 36 files, +1291 / −299, plus 17 untracked (tests, ledger, notes) |

Every fix was written test-first (failing test observed, then minimal code), and
every previously unpinned behavior gained regression tests. Engine changes were
verified end to end on a scaffolded demo project rendered through Quarto with R/knitr.

## 2. Internalized status (as found at session start)

- Engine (`src/wongo/`, ~3100 lines): `docxpatch` (unconditional OOXML fixes),
  `styles` (YAML-driven house look), `profiles` (7 verified journals), `engine`
  (render, checks, roundtrip, diff), `cli`. Behavior pinned to a private ES&T
  manuscript rendered with `style: kist-wcr`.
- Ledger: Statutor conversion pending in the working tree (AGENTS/HANDOFF/TASKS/
  DECISIONS/ROADMAP untracked or modified); HANDOFF was 19 days stale.
- GitHub: `hoohugokim/wongo` is PUBLIC; CI (pytest matrix, wheel check) and CodeQL
  green as of 2026-09-14. Docs still called the repo private.
- Toolchain on this machine: quarto 1.10.18, pandoc 3.10, R 4.6.1 with knitr,
  python-docx 1.2.0, lxml 6.1.2.

## 3. Defects found and fixed (all confirmed by reproduction before fixing)

1. **`default` style crashed every render** (T-0005). pandoc 3.10's default
   reference.docx `w:sectPr` carries only `w:footnotePr`; `fix_tables` did
   `int(sec.page_width)` on None. Quarto had already written `main-*.docx`, so a
   partial deliverable was left behind. Fix: compute text width only when the
   geometry exists; otherwise set pct width and leave pandoc's grid. Nobody hit it
   because kist-wcr sets `page:`. Quirk entry appended.
2. **`wongo diff` skipped nearly all real paragraphs** (T-0007). Quarto writes
   every `@fig-x` and linked citation as `w:hyperlink w:anchor=...`; the 2026-08-30
   fix treated any hyperlink as unrebuildable, so on the demo render the only edited
   body paragraph was reported for Word Compare. Rewritten as a run-aware,
   hyperlink-aware token diff (tokens carry `w:rPr` and their hyperlink container;
   `w:ins`/`w:del` are emitted inside shell copies of the hyperlink). Verified
   `quarto pandoc --track-changes=all` parses the output
   (`[Figure [2]{.insertion}[1]{.deletion}](#fig-x)`), so `wongo roundtrip`
   re-extracts it (proved end to end: diff → roundtrip → worksheet row).
3. **Diff flattened per-run formatting.** One word edit in a paragraph with an
   italic species name made the whole paragraph italic (python-docx runs have no
   rPr until formatted, so the italic run was the first with one). Fixed by the same
   rewrite; pinned by test.
4. **Diff never reported nested-table changes.** `tables_differ` compared
   `doc.tables` cell text; Quarto nests data tables inside 1x1 wrappers and
   `_Cell.text` ignores nested tables, so data edits were invisible. Now recursive.
5. **Revision ids could collide** with pre-existing tracked changes (fixed base
   9000). Now starts above the max existing `w:id`.
6. **lxml FutureWarning** from `_rpr_of(p) or _rpr_of(old)` (element truth-testing).
   Removed; pytest now turns `FutureWarning` into an error.
7. **SI cover counted figure wrappers as tables** (T-0006, `docs/bugs/`). New
   `si_item_counts` classifies each top-level table by its caption lead
   ("Figure S1"/"Table S1"), falling back to nested-table/drawing heuristics; a data
   table containing an image stays a table. Demo: 2 figures, 1 table (was 3 tables).
8. **TOC art ignored the height maximum** (T-0008). A square graphic was rendered
   82.55 mm tall against ACS's 44.45 mm cap. Now fitted inside the width×height box
   with aspect ratio preserved. The reference manuscript's art already has the exact
   3.25:1.75 ratio, so its render is unchanged.
9. **`default` style forced Cambria** although `default.yml` says "keep the journal
   reference-doc fonts" (T-0010). Engine fallback `FONTS[target]` removed; with
   `font: null` neither styles nor theme are touched (verified: Times New Roman
   from the ES&T reference doc survives, theme bytes identical).
10. **House style could bake line numbers into a Water Research submission** against
    the journal's instruction (T-0009, D-0005). Added `line_numbers: forbidden`;
    submission renders strip them after styling, collab keeps them. WR profile
    updated (source already cited). Verified on a WR demo: collab 1, submission 0.
11. **`profile verify` said "older than 6 months"** for a profile with no
    `verified_date`. Message corrected.
12. **`wongo check` false positives**: commented-out images counted as missing
    figures; `:::` div fences and `{{< >}}` shortcodes counted as words. Fixed.
13. **`wongo check` hardcoded `refs.bib`** (T-0013). Now reads `bibliography` from
    the `.qmd` front matter and `_quarto.yml` (string or list), falling back to
    `refs.bib`.

## 4. Features and hardening added

- `wongo profile verify` now lints `profile.yml` against the contract
  (`wongo.profiles.validate_profile`: required keys, manuscript types, ISO date,
  `toc_graphic.required`, `line_numbers` values). All 7 shipped profiles pass; a
  parametrized test keeps it that way (T-0012).
- `wongo roundtrip --qmd si.qmd` for coauthor-edited SI renders; worksheet rows name
  the source file (T-0014).
- IndexError guards: SI opening with a float (no paragraphs), abstract as the last
  paragraph (`inject_keywords`), authors as the last paragraphs
  (`rebuild_title_block`).
- Dead profile fallback (`repo-root/profiles/`, which no longer exists) removed.
- Tooling (T-0004, D-0004): `[tool.ruff]` (E4/E7/E9/F/I/UP/B, line length 100),
  `[tool.pytest.ini_options]` (FutureWarning = error), `ruff` in the dev extra,
  CI `ruff check` step. The documented AGENTS lint command still works unchanged.

## 5. Tests recreated and added (29 → 102)

- Lost in the skill→package migration and recreated by a subagent:
  `tests/test_roundtrip_parser.py` (9: real pandoc span syntax, replacement pairing,
  different-author non-pairing, unparsed nested brackets, front-matter exclusion,
  document order, worksheet rendering) and `tests/test_sectpr_order.py` (4:
  lnNumType < pgNumType < cols, idempotence). `docs/docx-quirks.md` cited these
  tests by name although they never existed here; a correction entry was appended.
- New by a subagent: `tests/test_run_checks.py` (12 end-to-end `run_checks` cases)
  and `tests/test_styles.py` (9: caption leads, WR title block, keywords, geometry).
- New by the orchestrator: 15 tests pinning the defects above plus
  `tests/test_profile_schema.py` (8 + 7 parametrized shipped profiles).
- Subagent notes: `notes/lost-tests-recreated.md`, `notes/checks-styles-tests.md`,
  `notes/docs-drift.md`.

## 6. Documentation and ledger

- Docs drift fixed (subagent): README, CONTRIBUTING, product definition say the repo
  is public with GitHub Releases; `render.py`/`validate.py` names replaced by wongo
  commands in all 7 profile SKILL.md files; stale "Pretendard/Times font swap" text
  removed; dev setup matches AGENTS commands.
- `docs/journal-profile-contract.md`: `line_numbers` tri-state, TOC box semantics,
  wongo naming. `docs/docx-quirks.md`: four appended entries (pandoc 3.10 sectPr,
  hyperlink/formatting/nested-table diff, SI count, test-name correction).
- `docs/bugs/si-cover-table-count.md` marked FIXED. `tools/bytecompare-allow.txt`
  gained the justification for the SI cover-count diff.
- Ledger: TASKS.md T-0005..T-0016 (10 done, 2 new open), DECISIONS.md D-0004..D-0006,
  HANDOFF.md rewritten with a fresh handoff id. `statutor-doctor .` will still warn
  until the ledger files are committed (the bash guard uses embedded defaults until
  `.statutor.yaml` lands).

## 7. Verification log

```
uv run pytest -q                                   -> 102 passed (py3.13)
uv run --python 3.11 ... pytest -q                 -> 102 passed (py3.11)
uv run --with ruff ruff check --ignore EXE001,DTZ011 src/wongo tests tools -> clean
uv build + wheel package-data check                -> OK (71 files)
uv run wongo --version / profile list / profile verify est|wr --offline -> clean
demo (scaffold, est, default + kist-wcr, collab + submission) -> 8 DOCX, no errors
demo (wr, kist-wcr): lnNumType collab=1 submission=0
wongo diff -> roundtrip on real Quarto output: 1 replacement extracted, pandoc parses it
```

## 8. Not done, and why

- **T-0002 render parity against the reference manuscript.** You declined the
  in-session worktree + `bytecompare baseline` run, so it is left for you. Expected
  result: `main-*` byte-identical (reasoning in `tools/bytecompare-allow.txt`),
  `si-*/word/document.xml` differs only in the cover "N tables" line (allowlisted).
- **No commits.** HANDOFF says to commit after parity; suggested grouping:
  1. `chore(ledger): statutor conversion + tooling config` (AGENTS/CLAUDE/ledger
     files, `.statutor.yaml`, `.pre-commit-config.yaml`, pyproject, CI);
  2. `fix(engine): default-style geometry, SI counts, TOC box, forbidden line numbers,
     reference fonts` + tests;
  3. `feat(diff): run- and hyperlink-aware tracked changes, recursive table report`
     + tests;
  4. `feat(check,profile,roundtrip): bibliography discovery, contract lint, --qmd`
     + tests;
  5. `docs: drift fixes, quirks entries, contract`.
- **T-0015**: the ES&T reference doc's theme-linked heading styles still resolve to
  Aptos under the `default` style (theme untouched by design). The profile builder
  scripts should strip `w:asciiTheme`/`w:hAnsiTheme` attributes when generating
  `reference.docx`; regenerate and re-verify. Not done because it changes generated
  profile assets.
- **T-0003** (reference-inclusive word count for WR) and **T-0016** (v0.2.0 release
  bump) remain design decisions for you.
- Multi-line chunk captions (`#| fig-cap: |`) are still not harvested by the
  word count; minor undercount, noted only.

## 9. Files to look at first

- `src/wongo/engine/diff.py` (rewritten), `src/wongo/engine/__init__.py`
  (`si_item_counts`, `insert_toc_art`, `_style_font`, forbidden line numbers),
  `src/wongo/styles/__init__.py` (`fix_tables` geometry), `src/wongo/profiles/__init__.py`
  (`validate_profile`), `src/wongo/engine/checks.py` (`bibliography_paths`).
- `tests/test_diff.py`, `tests/test_engine.py`, `tests/test_profile_schema.py`.
- `docs/docx-quirks.md` (tail), `DECISIONS.md` (D-0004..D-0006), `TASKS.md`.

## 10. Follow-up (same day): commits, T-0015, T-0016

- **Commits** (each passed the statutor pre-commit hook):
  `ce35ad9` ci lint step + lock; `e544c48` engine fixes; `54a97a4` diff v2;
  `df436af` check/profile/roundtrip; `eac0f96` reference-doc builders + regenerated
  assets; `d8e8bb4` docs; `62e0d07` release v0.2.0; then the ledger commit.
  Commits that carry the 2026-08-30 pending quality work also credit Codex as
  co-author (inferred from `_local/codex-transcripts/rollout-2026-08-30…`); amend
  if that attribution is wrong.
- **T-0015 done.** All seven builders set the four rFonts slots literally and
  strip theme links; assets regenerated by the scripts (only `styles.xml` rFonts
  lines changed, verified against HEAD). Regeneration exposed a second quirk:
  pandoc sorts rFonts attributes alphabetically when copying reference styles,
  which would have changed the byte-pinned kist-wcr `styles.xml` (order only).
  `set_fonts` now canonicalizes the order; the demo rendered with the HEAD and
  the regenerated ES&T reference doc is byte-identical for `main-*` and `si-*`.
  Quirk entry appended; `tests/test_reference_docs.py` pins every shipped asset.
- **T-0016 done.** Version 0.2.0 in `pyproject.toml`, `wongo.__version__`,
  `CITATION.cff` (date-released 2026-09-19), README; a test pins their agreement.
  D-0007: the `v0.2.0` tag, push, and GitHub Release wait for T-0002 (byte
  comparison against the reference manuscript), which you asked to run yourself.
- Final gate after the follow-up: 111 tests, ruff clean, wheel 0.2.0 builds,
  `statutor-doctor .` clean.
