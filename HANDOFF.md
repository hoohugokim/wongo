<!-- statutor: plane=state | policy=overwrite_bounded (max 40 lines) | writer=executor | OVERWRITE, NEVER APPEND -->
# HANDOFF

last_verified: 2026-09-19 by `uv run pytest -q` (111 passed) + ruff (AGENTS command) + `uv build` (wongo-0.2.0)
last_worker: claude
last_machine: unknown
handoff_id: 83a7660b3041a9eaf5d44ca432de4769
supersedes: none

## Goal
Cut v0.2.0: everything is committed (`ce35ad9`..`62e0d07` + ledger); only the
reference-manuscript byte comparison and the tag/push remain (T-0002, D-0007).

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
- pandoc 3.10's default reference.docx has no pgSz/pgMar; styles without `page:` must work.
- pandoc sorts rFonts attributes when copying reference styles; `set_fonts` canonicalizes.

## Do not touch
- `plans/archive/`, `HANDOFF-wongo-uplift.md`, `OVERNIGHT-LOG.md`, frozen `CHANGELOG.md`,
  existing `docs/docx-quirks.md` entries (append only), `_local/`, the reference repo.
