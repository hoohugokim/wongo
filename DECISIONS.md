<!-- statutor: plane=log | policy=append_only (insertions only; supersede, never edit) | writer=orchestrator/human -->
# DECISIONS

## D-0001 — Adopt the statutor ledger framework
**Status:** accepted
**Context:** Multi-agent sessions re-litigate settled questions and lose state across context windows.
**Decision:** Four-plane typed ledger, single writer per file, hook-enforced mutation policies.
**Consequences:** HANDOFF.md is overwrite-only and bounded; this file is append-only; CHANGELOG.md is generated from conventional commits, never hand-maintained.

## D-0002 — Make AGENTS.md the single agent constitution
**Status:** accepted
**Context:** Wongo previously made CLAUDE.md authoritative and told AGENTS.md readers to follow it, opposite Statutor's cross-harness convention.
**Decision:** Merge project doctrine into bounded AGENTS.md and reduce CLAUDE.md to the native `@AGENTS.md` import.
**Consequences:** Codex, Claude Code, OpenCode, and other AGENTS-aware tools read one source of truth; future constitutional edits touch AGENTS.md only.

## D-0003 — Freeze the existing changelog as historical context
**Status:** accepted
**Context:** Wongo maintained CHANGELOG.md through v0.1.0, while Statutor derives future history from conventional commits and tags.
**Decision:** Retain CHANGELOG.md so published history is not destroyed, but stop editing it after the current quality patch is committed.
**Consequences:** New changes use conventional commits and release tags; agents treat CHANGELOG.md as frozen legacy context.

## D-0004 — Lint and test configuration live in pyproject.toml; Pyright deferred
**Status:** accepted (2026-09-19, resolves T-0004)
**Context:** Ruff ran only from a hand-typed command with ad-hoc `--ignore` flags and never in CI; pytest had no configuration, so a `FutureWarning` from lxml truth-testing went unnoticed in the diff engine.
**Decision:** `[tool.ruff]` selects E4/E7/E9/F/I/UP/B at line length 100 (long lines not enforced), `[tool.pytest.ini_options]` turns `FutureWarning` into errors, `ruff` joins the dev extra, and CI runs `ruff check` before pytest. Pyright and python-docx factory type aliases are not adopted now; revisit when a type error escapes tests.
**Consequences:** The documented lint command keeps working unchanged; new code must be import-sorted and bugbear-clean; deprecation warnings fail the suite early.

## D-0005 — `line_numbers` is tri-state: true | false | forbidden
**Status:** accepted (2026-09-19)
**Context:** Water Research says "do not include line numbering; it will be added automatically", but the profile encoded that as `false`, which the engine reads as "not required". The kist-wcr house style turns line numbers on for every target, so a WR submission would ship with line numbers against the journal's instruction — taste overriding a journal directive.
**Decision:** Profiles may declare `line_numbers: forbidden`. On the submission target the engine strips line numbers after the house style is applied; collab renders keep them for coauthor comments. `true` still means the engine adds them; `false` stays "not required". The WR profile now uses `forbidden` (source already cited in its comment).
**Consequences:** Journal HARD directives outrank style taste for submission renders; `validate_profile` rejects other values; the contract doc records the three meanings.

## D-0006 — `wongo diff` v2 rebuilds hyperlink paragraphs; other rich OOXML is still reported, never flattened
**Status:** accepted (2026-09-19, supersedes the v1 scope in the 2026-08-30 quirk entry)
**Context:** Quarto writes every crossref and linked citation as `w:hyperlink`, so v1's "skip any hyperlink paragraph" rule left almost every body paragraph of a real manuscript un-tracked. v1 also copied one run's `w:rPr` onto the whole paragraph (italic species names spread to every word) and compared only top-level table text (nested data tables invisible).
**Decision:** Tokens carry their run properties and hyperlink container; changed paragraphs are rebuilt with `w:ins`/`w:del` inside shell copies of the hyperlinks (pandoc `--track-changes=all` parses this, so roundtrip still works). Fields, drawings, footnotes, math, tabs, breaks, and pre-existing tracked changes remain "rich": preserved and reported for Word Compare. Table comparison is recursive.
**Consequences:** S6 marked-up revisions now cover ordinary cited prose; `rich_paragraphs_skipped` should be near zero on a Quarto render, and a non-zero count points at genuinely special paragraphs.

## D-0007 — v0.2.0 is the next release boundary; the tag follows render parity
**Status:** accepted (2026-09-19, resolves T-0016)
**Context:** v0.1.0 was the first shareable package. Since then the engine gained a materially different `wongo diff`, a profile contract lint, regenerated reference docs, and fixes that change the `default` style's output — more than a patch release, no breaking CLI changes.
**Decision:** Bump `pyproject.toml`, `wongo.__version__`, and `CITATION.cff` together to 0.2.0 (a test pins their agreement). The annotated tag `v0.2.0`, the push, and the GitHub Release wheel are cut only after `tools/bytecompare.py check --target both` passes against the reference manuscript (T-0002); PyPI publication stays deferred.
**Consequences:** Version bumps are one commit touching three files; a release without a clean byte comparison is not allowed; the frozen CHANGELOG is not updated (D-0003) — the tag message and commit history carry the notes.
