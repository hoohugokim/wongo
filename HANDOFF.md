<!-- statutor: plane=state | policy=overwrite_bounded (max 40 lines) | writer=executor | OVERWRITE, NEVER APPEND -->
# HANDOFF

last_verified: 2026-09-25 by `uv run pytest -q` (396 passed) + ruff + `claude plugin validate .` + CI green on `ed5a947`
last_worker: claude
last_machine: unknown
handoff_id: 80aee22e6d4cfed921a3c214bc1c200e
supersedes: c73bd55ed9a0ab337ab5761bd907ba10

## Goal
Merge `feat/windows-front-door` (draft PR #3): Windows support, doctor/status, all-or-nothing
renders, --json everywhere, the S4 review loop and the Claude front door (T-0018..21, T-0027..28).

## Last verified state
- CI on `ed5a947`: pytest on Ubuntu/Windows/macOS; real Quarto 1.10.18 + R end-to-end on all
  three (Hangul folder on Linux/macOS; Windows asserts a cp1252 Hangul folder is refused).
- Byte parity vs a v0.2.0 baseline: only the two collab settings.xml parts differ (trackRevisions).
  Later commits change promotion, manifest and errors, not DOCX bytes (parity not re-run).
- Plugin: validated, installed under a throwaway CLAUDE_CONFIG_DIR, and a headless session picked
  the skill unprompted (notes/front-door-2026-09-25.md). Its install reads `main`: works after merge.

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
- `wongo review` refuses without a TTY; agents use `wongo worksheet set`, which will not overwrite a
  recorded decision without `--force`.
- ~10 GiB free on this Mac; a byte-compare pass copies ~0.8 GB of scratch (delete it afterwards).

## Do not touch
- `plans/archive/`, frozen `docs/CHANGELOG.md`, existing `docs/docx-quirks.md` entries (append only),
  `_local/`, the reference repo.
