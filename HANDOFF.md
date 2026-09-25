<!-- statutor: plane=state | policy=overwrite_bounded (max 40 lines) | writer=executor | OVERWRITE, NEVER APPEND -->
# HANDOFF

last_verified: 2026-09-25 by `uv run pytest -q` (111 passed) + ruff (AGENTS command) + CLI smoke (wongo 0.2.0)
last_worker: claude
last_machine: unknown
handoff_id: 321bd04f1c682ff460837104e62e8290
supersedes: 83a7660b3041a9eaf5d44ca432de4769

## Goal
Cut v0.2.0: `main` is pushed to origin at `99ae645` with CI and CodeQL green; only the
reference-manuscript byte comparison and the tag remain (T-0002, D-0007).

## Last verified state
- 111 tests green (Python 3.13 and 3.11); ruff clean; wheel 0.2.0 carries package data;
  CLI smoke clean; `statutor-doctor .` clean.
- Fixed and committed: `default`-style crash, SI cover counts, `wongo diff` v2 (D-0006),
  TOC-art box fit, `line_numbers: forbidden` (D-0005), reference fonts kept, contract
  lint, bibliography discovery, `roundtrip --qmd`, reference-doc builders without theme
  font links (all 7 assets regenerated), canonical rFonts order in `set_fonts`.
- Demo renders (est + wr, default + kist-wcr, both targets) succeed; kist-wcr output is
  byte-identical with the old and regenerated reference docs (checked on the demo).
- Full report: `notes/overnight-2026-09-19.md` (section 10 = follow-up commits).

## Next action
1. T-0002: `set -x WONGO_REF_PROJECT ~/workbench/<reference-repo>`; in a worktree at
   `ad6019d` run `uv run tools/bytecompare.py baseline --target both`, then here
   `uv run tools/bytecompare.py check --target both --allow tools/bytecompare-allow.txt`.
   Expected: `main-*` identical; only `si-*/word/document.xml` differs (cover count).
2. On PASS: `git tag -a v0.2.0 -m "wongo v0.2.0"`, `git push --follow-tags`, GitHub
   Release with `dist/wongo-0.2.0-*` from `uv build`. On FAIL: fix, never allowlist blind.

## Gotchas
- DO NOT run step 1 before T-0017: bytecompare writes into the LIVE reference output/.
- pandoc sorts rFonts attributes when copying reference styles; `set_fonts` canonicalizes.

## Do not touch
- `plans/archive/` (uplift records), frozen `docs/CHANGELOG.md`, existing
  `docs/docx-quirks.md` entries (append only), `_local/`, the reference repo.
