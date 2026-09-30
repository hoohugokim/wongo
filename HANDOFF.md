<!-- statutor: plane=state | policy=overwrite_bounded (max 40 lines) | writer=executor | OVERWRITE, NEVER APPEND -->
# HANDOFF

last_verified: 2026-09-30 by pytest (446 passed, 3 OS-specific skips), ruff, build, CLI/profile smoke and identical 95-part parity vs v0.3.0
last_worker: codex
last_machine: unknown
handoff_id: nature-word-count-20260930
supersedes: v030-released-20260930

## Goal
T-0023 implemented on `codex/nature-word-count`; ready for PR review and merge.

## Last verified state
- Nature-family types now declare optional word-count policies for abstract, sections, captions
  and boxes; Methods stay counted for types without that exclusion. Defaults are unchanged.
- Official counting rules checked 2026-09-30; numeric limits and broader verified_date untouched.
- Invalid policies fail with ConfigError. Exact-limit/overflow, Markdown boundaries, independent
  citation/figure checks and all-or-nothing submission regressions pass.
- Fresh v0.3.0 baseline and candidate renders: all 95 parts across four documents byte-identical,
  empty allowlist. See notes/nature-word-count-2026-09-30.md for scope and verification.
- v0.3.0 remains the published release at `96c386e`; no release assets changed. T-0024/T-0026
  release and legacy-skill retirement details remain in notes/release-v030-2026-09-30.md.

## Next action
1. Review/merge the `codex/nature-word-count` PR after GitHub CI and CodeQL pass.
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
