# T-0035–T-0038: build integrity (F1–F4)

First cycle from `notes/T-0336-wongo-development-report.md`. Synthetic fixtures
only. JONS-EA and the private reference manuscript were not modified.

## What shipped

D-0015. `_journal.yml` `dependencies`, Quarto pre/post-render script paths, and
`postprocess` scripts join the source fingerprint. A missing declared path is
the sentinel `missing` and an InputError before Quarto, for both targets.
External dependencies are hashed and not copied. `dependencies_discover: true`
warns on literal `read`/`source` calls and is off by default. The manifest
records profile, style, CSL, and reference-doc hashes plus install git state.
Dirty/clean is shown and does not stale a manuscript. A manifest without
profile or style identity is stale. A source or profile change during
rendering refuses promotion for both targets. Reference-inclusive manuscripts
still raise GateError on `word-limit-references`; other projects raise InputError.

D-0016. A cross-reference resolves only in the document that defines its label.
Duplicate labels are HARD. Uncited `fig-`/`tbl-` items are WARN `uncited`.
Quarto `Unable to resolve crossref` is HARD `crossrefs-rendered`: submission
refuses promotion; collab promotes and records `checks_failed`. Status does
not offer submission while that list is set.

D-0017. `postprocess` is a list of project-relative paths, not a shell command.
Scripts run inside the stage, after engine postprocess and before the manifest.
Python uses `sys.executable`. Timeout is 120 seconds. Failure discards the
stage and leaves the previous outputs. The manifest stores script hashes and
before/after output hashes. `status` and `check` do not run the scripts.
Engine postprocess keeps alt text, `w:ins`, and math.

`wongo check` prints rule coverage. `ok` still means no HARD machine failure.
Coverage is INFO. Non-strict check still exits 0 when JSON `ok` is false.
`--strict` still exits 1. Manifest format stays 1.

## ES&T, re-read 2026-10-22

Source: <https://researcher-resources.acs.org/publish/author_guidelines?coden=esthag>
(page updated 2026-10-05). `verified_date: 2026-10-22`.

Research article, policy analysis, and critical review: abstract 150–200 words.
Feature, correspondence, and viewpoint have no numeric abstract bound. Word
count excludes Acknowledgments, Notes, References, Bibliography, and Supporting
Information. Correspondence still adds rendered bibliography words because
`word_limit_includes_references` is true. SI availability text in `SKILL.md`
and `references/submission-checklist.md` now says before Acknowledgments.
Historical lines are ignored by the placement lint. Keywords (5–8),
one-paragraph form, and ORCID stay manual. Perspective and Spotlight were not
added. `critical-review` was not renamed. The scaffold example abstract is 172
words so `wongo scaffold --example` still passes HARD checks.

## Verification

`uv run pytest -q`: 654 passed, 6 skipped, on 2026-10-22.

`uv run --with ruff ruff check --ignore EXE001,DTZ011 src/wongo tests tools`
fails on a pre-existing E713 in `src/wongo/engine/worksheet.py`. That file is
earlier uncommitted work. This cycle did not edit it.

Bytecompare was not run. Unconditional DOCX post-processing is unchanged.
Declared postprocess is opt-in. No version bump. The local commit leaves the
earlier worksheet, new-journal, research, and AIX edits unstaged.

## Left for a later cycle

F5–F8: audit hooks, preview QA, a portable review receipt, and human approval
gates. Do not add a `Figure S3` scanner. Do not vendor `finish_docx.py`.
`notes-after-punctuation` stays a project `_quarto.yml` choice. T-0022 and
T-0025 stay open.
