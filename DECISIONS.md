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

## D-0008 — The engine speaks WongoError and results; the CLI owns all output; renders are all-or-nothing
**Status:** accepted (2026-09-25, T-0019, T-0020)
**Context:** Errors travelled as SystemExit (silently lost in worker threads, fatal to asyncio loops, invisible to `except Exception`), results as print() calls, and a failure after Quarto left a half-processed DOCX in output/ — a breach of the no-partial-deliverable rule that a Word lock on Windows triggers routinely.
**Decision:** User-fixable errors are `wongo.errors.WongoError` subclasses whose message states the fix; keyword details (e.g. the failing checks of a refused render) travel with them. Engine functions return dataclasses and print nothing. Every command accepts `--json` and then prints exactly one object `{command, wongo, ok, ...}`, errors included, with exit code 1 on failure. Renders stage Quarto output under `.wongo-stage-*` and post-process in `output/.stage-<target>/`; `promote()` backs up existing outputs, restores them on any failure, and reports a Word lock as OutputLockedError. `output/.wongo-manifest.json` records versions, config and source hashes for freshness checks.
**Consequences:** The Claude skill reads JSON instead of parsing prose; a render either replaces all outputs or none; the staging file name was verified not to change any compared DOCX part, and the byte comparison against v0.2.0 differs only in the intended collab `trackRevisions` fix.

## D-0009 — Worksheet decisions: the agent proposes, a person decides, wongo never edits the .qmd
**Status:** accepted (2026-09-25)
**Context:** `wongo roundtrip` wrote a worksheet of PENDING rows that nothing read back; decisions lived in free-form Markdown edits, with no check that every row was decided before edits reached the manuscript.
**Decision:** The worksheet grammar is PENDING, `PROPOSED <final> — <rationale>`, and the finals `apply`, `fix-code`, `needs-PI`, `reject: <reason>`. The agent writes proposals with `wongo worksheet set`; a person confirms with `wongo review` (digits only, saved after each row) or by explicit per-row approval in chat. `wongo worksheet lint` must pass before any approved row is applied, and `apply` is refused on UNMATCHED locations and unparsed rows. Overriding a proposal keeps it as `was PROPOSED ...`. wongo itself never writes a .qmd (the roundtrip rule stands).
**Consequences:** Every coauthor edit has an auditable decision; the Markdown file stays the single record and round-trips byte-for-byte; applying edits remains a deliberate human or agent step outside wongo.

## D-0010 — The Claude front door ships with wongo: a plugin marketplace in this repo and agent files in every scaffold
**Status:** accepted (2026-09-25; KIST allows Claude with this skill as the front door)
**Context:** Non-technical lab members, on Windows as well as macOS, should use wongo by talking to Claude. The spine skill lived only in the maintainer's ~/.claude/skills, so nobody else could install it.
**Decision:** The repository is a Claude Code plugin marketplace (`.claude-plugin/marketplace.json`) whose plugin (`integrations/claude-code/`) carries the wongo skill; journal judgment stays in the profiles and is reached through `wongo profile show <slug> --json`. `wongo scaffold` writes agent instruction files and editor tasks into each new project; the templates ship with a `.tmpl` suffix so this repo's own agents never read them as instructions. Installing wongo needs no git: uv installs from the GitHub source archive.
**Consequences:** One install path for Claude users on both platforms; the maintainer's personal skills become optional; PyPI publication (T-0022) would shorten the install further.

## D-0011 — The TUI is deferred; interactive surfaces are line-oriented and digit-driven
**Status:** accepted (2026-09-25, resolves T-0021; notes/tui-feasibility-2026-09-25.md)
**Context:** A full terminal UI was judged feasible but low-value now: the hard parts of wongo (toolchain setup, .qmd authoring, S4 judgment) sit where no screen reaches, and Textual carries Korean input-method and maintenance risks.
**Decision:** No full-screen TUI. Interaction happens through standard-library prompts that appear only at a real terminal (`clitools.is_interactive()`), choose with digits, and never block CI, the byte-compare harness or the agent. Revisit only if a pilot with real labmates shows screens, not setup or writing, are the bottleneck.
**Consequences:** No new runtime dependencies; prompts work with a Korean input method on; the CLI plus the Claude front door is the interface.
