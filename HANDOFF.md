<!-- statutor: plane=state | policy=overwrite_bounded (max 40 lines) | writer=executor | OVERWRITE, NEVER APPEND -->
# HANDOFF

last_verified: 2026-10-22 by uv run pytest -q (654 passed, 6 skipped) && statutor-doctor .
last_worker: grok
last_machine: unknown
handoff_id: build-integrity-20261022
supersedes: research-complete-20261008

## Goal
F1–F4 from notes/T-0336-wongo-development-report.md are committed locally. F5–F8 are not started.

## Last verified state
- T-0035–T-0038 done. D-0015, D-0016, D-0017. Note: notes/T-0035-build-integrity.md.
- `uv run pytest -q`: 654 passed, 6 skipped, on the full tree including files left unstaged.
- The commit excludes worksheet, new profiles (bite, cej, estletters, natcomms, wrx), docs/research, and AIX edits.
- Ruff fails on uncommitted E713 at src/wongo/engine/worksheet.py:1129.
- Not pushed. No version bump. T-0022 and T-0025 stay open.

## Next action
1. Leave the uncommitted worksheet, profile, research, and AIX files in place. Do not revert them.
2. F5–F8 (audit hooks, preview QA, review receipt, human approval) are the next cycle. The report stays untracked at notes/T-0336-wongo-development-report.md.
3. Clear the worksheet.py E713 before treating `ruff check` as green.

## Gotchas
- `wongo check` exits 0 when JSON `ok` is false. `--strict` exits 1.
- Collab still promotes when `crossrefs-rendered` fails. Status must not offer submission while `checks_failed` is set.
- A mid-render source change refuses promotion for both targets. Reference-inclusive manuscripts raise GateError on `word-limit-references`.
- ES&T abstract 150–200 and SI-before-Acknowledgments were re-read 2026-10-22 (page updated 2026-10-05). Keywords, one paragraph, and ORCID stay manual.
- `dependencies_discover` is off by default. Discovery is a literal-call scan, not a trace.

## Do not touch
- `plans/archive/`, frozen `docs/CHANGELOG.md`, existing `docs/docx-quirks.md` entries. Do not edit D-0008 in place. Do not vendor `finish_docx.py`.

