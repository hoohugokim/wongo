# Docs drift fixes — 2026-09-19

Scope: docs-only edit pass across README.md, CONTRIBUTING.md,
docs/product-definition.md, and the 7 profile SKILL.md files. No src/,
tests/, docs/docx-quirks.md, docs/journal-profile-contract.md, TASKS.md,
HANDOFF.md, DECISIONS.md, pyproject.toml, or CI files touched.

## 1. Public-repo status (verified via `gh repo view hoohugokim/wongo`: PUBLIC)

- `docs/product-definition.md`: reworded the "Distribution (package)" row
  and the "Distribution status" bullets — repo `hoohugokim/wongo` is public
  on GitHub, distribution is via GitHub Releases; PyPI publication remains
  deferred (name reserved, not published). Kept the existing sentence that
  the reference manuscript's identity is intentionally not named (it
  already said "public repo", so no change needed there).
- `CONTRIBUTING.md`: "private repo `hoohugokim/wongo`" → "public repo
  `hoohugokim/wongo` on GitHub".
- README.md had no "private" language to begin with — no change needed
  for this item.

## 2. Legacy tool names → wongo CLI/engine equivalents

Replaced stale references to the pre-migration scripts (`render.py`,
`validate.py`, `roundtrip.py`, `mslib.py` — none of which exist anymore)
with the current `wongo` package surfaces, across all 7 profile
`SKILL.md` files (`est`, `microbiome`, `envmicrobiome`, `natwater`,
`npjcw`, `wr`, `npjbiofilms`):

- `render.py`'s `insert_toc_art()` / `find_toc_art()` → `wongo render`
  (`wongo.engine.insert_toc_art` / `wongo.engine.find_toc_art`)
- `render.py`'s `postprocess_si` → `wongo render`
  (`wongo.engine.postprocess_si`)
- `validate.py`'s word-limit check → `wongo check`'s word-limit check
- No journal facts, numbers, dates, VERIFIED/TO-VERIFY content changed —
  tool naming only.

## 3. Stale collab/submission font-swap phrase removed (est SKILL.md)

Removed "the collab-vs-submission font swap (Pretendard for internal
drafts, Times New Roman for submission)" — fonts are not `--target`-
dependent. Replaced with the current truth: fonts come from the selected
house style in `src/wongo/styles/*.yml` (verified `kist-wcr.yml` sets
`font: Cambria` "all targets"; `default.yml` sets `font: null` i.e. keeps
the journal reference-doc fonts), applied via `wongo.styles.apply_style()`.
Only `line_numbers` remained as the actual `--target`-dependent choice in
that sentence.

## 4. README "Repository layout" table

- `src/wongo/` row: added `diff` alongside `roundtrip`.
- `tests/` row: now "Regression tests pinning every shipped OOXML fix, the
  diff/roundtrip engines, and the validation checks."

## 5. CONTRIBUTING.md dev setup

Replaced the ad-hoc `uv run --with pytest --with python-docx --with
pyyaml pytest -q` block with the documented AGENTS.md commands:
`uv sync --all-extras`, `uv run pytest -q`, the ruff lint command
(`uv run --with ruff ruff check --ignore EXE001,DTZ011 src/wongo tests
tools`), `uv build`, and the CLI smoke (`uv run wongo --version && uv run
wongo profile verify est --offline`). Kept the bytecompare commands and
the Quarto/R version line unchanged. Added a note that `WONGO_REF_PROJECT`
must point at the reference manuscript repo root for bytecompare, and that
the harness never writes into that project.

## 6. docs/product-definition.md — Runnable row and CITATION.cff

- Added `wongo diff <original.docx> <revised.docx>` to the Runnable row's
  CLI list (appears twice in the file; both updated).
- "Cite as software (see `CITATION.cff` when added; until then cite the
  GitHub Release ...)" → "Cite via `CITATION.cff` (or the GitHub Release
  ...)" — `CITATION.cff` now exists in the repo.

## Verification

`git diff --stat` for the touched paths is in the handback report to the
orchestrator.
