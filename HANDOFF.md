<!-- statutor: plane=state | policy=overwrite_bounded (max 40 lines) | writer=executor | OVERWRITE, NEVER APPEND -->
# HANDOFF

last_verified: 2026-09-30 by pytest (402 passed, 3 OS-specific skips), ruff, build, wheel smoke, 95-part parity and CI/CodeQL on `96c386e`
last_worker: codex
last_machine: unknown
handoff_id: v030-released-20260930
supersedes: v030-release-prepared-20260930

## Goal
T-0024 and T-0026 complete: v0.3.0 released and personal legacy skills retired.

## Last verified state
- PR #3 merged as `91641f9`; release commit `96c386e` passed CI and CodeQL.
- v0.3.0 annotated tag and GitHub Release published with wheel and sdist; remote SHA-256 digests
  match local artifacts. Version/citation/lockfile/plugin and setup guides agree on 0.3.0.
- Fresh v0.2.0 baseline and candidate renders: 95 parts, only the two collab settings.xml parts
  differ; canonical XML confirms exactly trackChanges -> trackRevisions.
- Legacy skills were already absent from the shared personal collection; nine dangling Codex
  links archived under ~/Agents/Codex/retired-skills/wongo-20260930 (links.json preserves targets).
- Personal wongo links point to the canonical plugin skill; Claude plugin 0.3.0 installed/enabled
  at user scope. Restart sessions to refresh skill discovery. See notes/release-v030-2026-09-30.md.

## Next action
1. T-0023: Nature-family word-count exclusions (current counts can falsely fail a manuscript).
2. T-0003: reference-inclusive count gate (currently a lower-bound HARD gate plus WARN).
3. T-0025 needs a real Korean-account Windows PC: desktop setup, IME and Word-held render.
4. T-0022: PyPI trusted publishing, after maintainer account setup.

## Gotchas
- Statutor guard: use editor tools for ledger changes and `git add -u`.
- `/plugin marketplace add owner/repo` needs git, so the Windows guide installs Git for Windows first.
- `wongo review` refuses without a TTY; agents use `wongo worksheet set` (no overwrite of a
  recorded decision without `--force`).

## Do not touch
- `plans/archive/`, frozen `docs/CHANGELOG.md`, existing `docs/docx-quirks.md` entries (append only),
  `_local/`, the reference repo.
