<!-- statutor: plane=state | policy=overwrite_bounded (max 40 lines) | writer=executor | OVERWRITE, NEVER APPEND -->
# HANDOFF

last_verified: 2026-09-30 by pytest (459 passed, 3 OS-specific skips; includes real Quarto), ruff, build, CLI/profile smoke and identical 95-part parity vs v0.3.0
last_worker: codex
last_machine: unknown
handoff_id: reference-word-count-20260930
supersedes: nature-word-count-20260930

## Goal
PR #4 merged; T-0003 verified locally on `codex/reference-word-count`; publication awaits approval.

## Last verified state
- PR #4/T-0023 merged as `67ce1d9` after all CI/CodeQL checks passed.
- Reference-inclusive limits now add the new main DOCX's Bibliography words to the source
  estimate before promoting any outputs. Missing bibliography or source/profile changes during
  rendering block submission; collab renders expose failures and remain inspectable.
- Source-only checks still warn and never reuse old DOCX files. Counts explicitly remain
  estimates; see notes/reference-word-count-2026-09-30.md for scope and limitations.
- Real Water Research 8,000/8,001-word regression passes and now runs in all three OS render jobs.
- Fresh v0.3.0 baseline and candidate renders: all 95 parts across four documents byte-identical.
- v0.3.0 remains the published release at `96c386e`; no release assets changed. T-0024/T-0026
  release and legacy-skill retirement details remain in notes/release-v030-2026-09-30.md.

## Next action
1. Push `codex/reference-word-count` to hoohugokim/wongo and open a PR; then verify CI/CodeQL.
   Auto-review requires explicit user approval of this public publication. No T-0003 PR exists yet.
2. T-0025 needs a real Korean-account Windows PC: desktop setup, IME and Word-held render.
3. T-0022: PyPI trusted publishing, after maintainer account setup.

## Gotchas
- Statutor guard: use editor tools for ledger changes and `git add -u`.
- `/plugin marketplace add owner/repo` needs git, so the Windows guide installs Git for Windows first.
- `wongo review` refuses without a TTY; agents use `wongo worksheet set` (no overwrite of a
  recorded decision without `--force`).

## Do not touch
- `plans/archive/`, frozen `docs/CHANGELOG.md`, existing `docs/docx-quirks.md` entries (append only),
  `_local/`, the reference repo.
