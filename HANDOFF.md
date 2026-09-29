<!-- statutor: plane=state | policy=overwrite_bounded (max 40 lines) | writer=executor | OVERWRITE, NEVER APPEND -->
# HANDOFF

last_verified: 2026-09-30 by pytest (402 passed, 3 OS-specific skips), ruff, build, CLI smoke and 95-part parity vs v0.2.0
last_worker: codex
last_machine: unknown
handoff_id: v030-release-prepared-20260930
supersedes: 64b5ac965c6459a9308aac5720baf675

## Goal
Finish T-0024: publish v0.3.0 after merging PR #3; finish T-0026: retire personal legacy skills.

## Last verified state
- PR #3 merged as `91641f9`; its main-branch CI and CodeQL passed.
- Version, citation date, lockfile, plugin manifest and current setup guides prepared for 0.3.0.
- Fresh v0.2.0 baseline and candidate renders: 95 parts, only the two collab settings.xml parts
  differ; canonical XML confirms exactly trackChanges -> trackRevisions.
- Legacy skills were already absent from the shared personal collection; nine dangling Codex
  links archived under ~/Agents/Codex/retired-skills/wongo-20260930 (links.json preserves targets).
- Personal wongo links point to the canonical plugin skill; Claude marketplace registered.

## Next action
1. Commit and push the release changes, wait for CI, tag/publish v0.3.0 with wheel and sdist.
2. Install the released Claude plugin; close T-0024 and T-0026 after verification.
3. T-0025 needs a real Korean-account Windows PC: desktop setup, IME and Word-held render.
4. Still open: T-0003, T-0022 (PyPI account setup), T-0023.

## Gotchas
- Statutor guard: use editor tools for ledger changes and `git add -u`.
- `/plugin marketplace add owner/repo` needs git, so the Windows guide installs Git for Windows first.
- `wongo review` refuses without a TTY; agents use `wongo worksheet set` (no overwrite of a
  recorded decision without `--force`).

## Do not touch
- `plans/archive/`, frozen `docs/CHANGELOG.md`, existing `docs/docx-quirks.md` entries (append only),
  `_local/`, the reference repo.
