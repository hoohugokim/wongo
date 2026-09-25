<!-- statutor: plane=state | policy=overwrite_bounded (max 40 lines) | writer=executor | OVERWRITE, NEVER APPEND -->
# HANDOFF

last_verified: 2026-09-25 by `uv run pytest -q` (131 passed) + ruff + `tools/bytecompare.py check --target both` (PASS)
last_worker: claude
last_machine: unknown
handoff_id: c73bd55ed9a0ab337ab5761bd907ba10
supersedes: 321bd04f1c682ff460837104e62e8290

## Goal
v0.2.0 is released. Now: Windows compatibility, environment floor, headless seam and
the S4 review loop (steps 2-4 of notes/tui-feasibility-2026-09-25.md; TUI deferred).

## Last verified state
- `v0.2.0` tagged at `b0db8ba`, pushed, GitHub Release with wheel and sdist; the
  release wheel installs and runs from its URL via `uvx --from`.
- T-0002: baseline `ad6019d` vs `34e8150`, 95 parts, only the SI cover count differs
  ("26 tables" to "12 tables"). T-0017 harness fix and T-0003 interim gate shipped.
- The reference project's post-render hook (`keep_captions.py`) finds files through
  `QUARTO_PROJECT_OUTPUT_FILES`, so a staging file name does not break it.

## Next action
1. Work continues on branch `feat/windows-front-door`: T-0018 (trackRevisions), T-0019
   (staged renders), T-0020 (doctor, preflight, UTF-8), S4 worksheet review, Claude front door.
2. Re-run the byte comparison against a `v0.2.0` baseline before merging:
   `git worktree add --detach <tmp> v0.2.0`, then `bytecompare.py baseline --repo <tmp>`
   and `bytecompare.py check --allow tools/bytecompare-allow.txt` (WONGO_BC_SCRATCH set).

## Gotchas
- pandoc 3.10's default reference.docx has no pgSz/pgMar; styles without `page:` must work.
- pandoc sorts rFonts attributes when copying reference styles; `set_fonts` canonicalizes.
- Only ~9 GiB disk free on this Mac; each harness pass copies ~0.7 GB of the reference repo.

## Do not touch
- `plans/archive/` (uplift records), frozen `docs/CHANGELOG.md`, existing
  `docs/docx-quirks.md` entries (append only), `_local/`, the reference repo.
