<!-- statutor: plane=state | policy=overwrite_bounded (max 40 lines) | writer=executor | OVERWRITE, NEVER APPEND -->
# HANDOFF

last_verified: 2026-09-26 by `uv run pytest -q` (402 passed) + ruff + CI green on `da6ff85`
last_worker: claude
last_machine: unknown
handoff_id: 64b5ac965c6459a9308aac5720baf675
supersedes: 80aee22e6d4cfed921a3c214bc1c200e

## Goal
Merge `feat/windows-front-door` (draft PR #3): Windows support, doctor/status, all-or-nothing
renders, --json everywhere, the S4 review loop and the Claude front door (T-0018..21, T-0027..29).

## Last verified state
- CI on `da6ff85`: pytest on Ubuntu/Windows/macOS; real Quarto 1.10.18 + R end-to-end on all
  three (Hangul folder on Linux/macOS; Windows asserts a cp1252 Hangul folder is refused).
- T-0029: roundtrip skips HTML-comment lines and anchors on the context's last words; the demo
  insertion that landed on index.qmd:19 (inside a comment) now lands on :34.
- Byte parity vs a v0.2.0 baseline: only the two collab settings.xml parts differ (trackRevisions).
  Later commits change promotion, manifest, errors and roundtrip, not DOCX bytes (not re-run).
- Lab-meeting deck (claude.ai Slides artifact "Wongo Lab Meeting Update") shows this branch's state.

## Next action
1. Maintainer reviews and merges PR #3; then T-0024 (v0.3.0 tag and release, then drop the
   "do not use the v0.2.0 wheel" line in the skill's setup reference).
2. T-0025: real Windows PC with a Korean account: Claude desktop + plugin, Korean IME in
   `wongo review`, a render while Word holds the file.
3. Still open: T-0003, T-0022 (PyPI, maintainer account), T-0023, T-0026 (needs the maintainer's OK).

## Gotchas
- The statutor bash guard blocks commands and commit messages that name ledger files; use editor
  tools and `git add -u`.
- `/plugin marketplace add owner/repo` needs git, so the Windows guide installs Git for Windows first.
- `wongo review` refuses without a TTY; agents use `wongo worksheet set` (no overwrite of a
  recorded decision without `--force`).

## Do not touch
- `plans/archive/`, frozen `docs/CHANGELOG.md`, existing `docs/docx-quirks.md` entries (append only),
  `_local/`, the reference repo.
