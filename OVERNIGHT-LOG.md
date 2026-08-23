# OVERNIGHT-LOG — wongo uplift, HANDOFF steps 1–5 (2026-08-24 night)

Branch: `uplift/overnight-1` (6 commits on top of the WIP commit `6355ad7`
on `main`). **Not pushed. No tag.** Everything below is reviewable per phase.

## 0. Summary

All five migration phases from `HANDOFF-wongo-uplift.md` were executed in
order, each gated by (a) pytest green and (b) a byte-compare of all four
the reference manuscript render products (main/SI × collab/submission) against a
pre-migration baseline. The main documents stayed **byte-identical through
every phase**. Exactly one intentional behavior change landed (the two
long-standing SI cover-sheet gaps from the HANDOFF), isolated to
`si-<target>/word/document.xml`, tests-first, allowlisted with justification.

Steps 6 (thin the Claude skills) and 7 (docs/polish/tag v0.1.0) were
deliberately NOT touched: they affect infrastructure the live the reference manuscript
manuscript depends on before `ms-r0-sent`.

## 1. Ground-rule compliance

| Rule | How it was held |
|---|---|
| 1. Behavior pinned | `tools/bytecompare.py`: fresh copy of the reference manuscript → render with engine → unzip → byte-diff every `word/*` part vs baseline. Noise floor measured first (`selftest`: consecutive legacy runs are byte-identical, so any diff is code-caused). |
| 2. the reference manuscript untouched until ms-r0-sent | Zero writes into `~/workbench/the reference manuscript`; harness works on `/tmp/wongo-bc/ref`. No style key was added to its `_journal.yml` (consequence: transitional style fallback, see §3). |
| 3. Correctness vs taste | `wongo.docxpatch` = unconditional fixes only; everything visual is data-driven from `wongo/styles/*.yml` via `wongo.styles.apply_style()`. |

## 2. Phase-by-phase

### Phase 0 — preflight (`6355ad7` was WIP; branch created)
- Ran pytest (5/5), committed the uncommitted `track_changes` WIP as-is with a
  descriptive message.
- Built `tools/bytecompare.py` (modes: `baseline`, `selftest`, `check`;
  `--allow` pattern file = `tools/bytecompare-allow.txt`, whole-file gating).
- Established baseline for both targets (63 XML parts across 4 documents);
  noise floor zero.

**Harness gotchas found:** the manuscript references assets outside its dir
(`../training/...`), so the whole the reference manuscript repo must be copied, not just
`manuscript/`. Quarto renders are deterministic for compared parts.

### Phase 1 — `wongo.docxpatch` (`f0a50a4`)
Moved verbatim: `dedupe_ppr`, `normalize_ppr_order`(+`_PPR_ORDER`),
`set_fonts`(+`STYLES_TO_FONT`), `_style_by_name` (BabelFish docstring kept),
tbl helpers, `add_line_numbers`, `add_page_numbers`,
`restart_page_numbering`(+`_SECT_PR_TAIL`).
Refactor: `patch_theme_fonts` split into `patch_theme_fonts` /
`patch_compat_mode` / combined `patch_document_package`, all sharing one zip
pass via `_rewrite_package`. **The combined path preserves the historical
semantics exactly**, including the no-theme1.xml early-return that also skips
compat stamping (this quirk is now documented in the module docstring).
`legacy/render.py` imports flipped so every pipeline run exercises the new
code. Gate: 7/7 tests, byte-identical.

### Phase 2 — `wongo.styles` (`eb6eec7`)
All HOUSE_* logic reimplemented data-driven from `styles/<name>.yml`
(now packaged at `src/wongo/styles/`). WR title-block machinery moved here,
parameterized (`title_block.style == "wr"` gate, blank-line booleans).
Caption regexes/`_restyle_caption` moved with delimiter/spacing/align keys.
Table look gated on `tables.rules == "booktabs"` etc.; grid rescale itself
stays unconditional in docxpatch per ground rule 3.

**Deviation to review:** `restyle_abstract_heading` was hardcoded legacy
behavior not represented in kist-wcr.yml; added an explicit
`abstract_title:` key to both profiles rather than inventing hidden
behavior. Test pins kist-wcr.yml values against the old constants.
Gate: 8/8 tests, byte-identical, plus a smoke test proving `kist-wcr` and
`default` produce divergent documents (the layer actually responds).

### Phase 3 — `wongo.profiles` (`81e8be4`)
Profile API migrated from mslib. Resolution chain:
project-local `profiles/` → `$WONGO_PROFILES` (legacy `QM_SKILLS_DIR` kept
as alias) → packaged `src/wongo/profiles/` → repo-root fallback. The seven
profile dirs were `git mv`'d into the package; the `quarto-manuscript-*`
symlink shims deleted; wheel verified to carry profile.yml + reference.docx
+ CSL. Gate: 8/8 tests, byte-identical.

### Phase 4 — `wongo.engine` + SI cover fixes (`626886b`)
Render pipeline (`quarto_render`, TOC-art pre-gate + backstop,
postprocess_main/si, `render_project` orchestrator), checks
(`wongo.engine.checks`: HARD/WARN shape + text analysis verbatim), and
roundtrip moved into the package. legacy scripts became thin CLI shims.

**THE intentional change (tests written FIRST — see tests/test_engine.py):**
1. Cover sheet printed `Journal: <journal> — <ms_type>`; ES&T's verified
   guidance says authors/title/page-figure-table counts. Now prints title +
   full author line from index.qmd front matter.
2. Page-count literal placeholder replaced by a live `NUMPAGES` field Word
   resolves on open (python-docx cannot paginate).
Diff scope verified: ONLY `si-{collab,submission}/word/document.xml`.
Gate: 11/11 tests; bytecompare passes with the two-file allowlist.

### Phase 5 — CLI (`b0a6f86`)
Real subcommands replace runpy delegation:
`render [--target] [--style]`, `check [--strict]`, `roundtrip`,
`scaffold` (template now package data), `profile list`, `profile verify <slug>`.
`--style` threads through `resolve_style`. Style profiles moved into the
package so wheels are self-contained.

**profile verify design note:** HEADs each profile source URL and flags
`Last-Modified` newer than `verified_date` — mechanically the same signal
that caught the 2026-07-30 ES&T revision by hand. Servers that block bots
(ACS returns 403) are reported as `[blocked]` WITHOUT counting as drift, so
the tool never cries wolf; those need the manual re-fetch audit. Verified
live against est/wr.

## 3. Transitional wart — REVIEW THIS

`resolve_style` (wongo/engine/__init__.py) falls back to **`kist-wcr`**, not
`default`, when neither `_journal.yml` nor `$WONGO_STYLE` provides a style.
Reason: ground rule 2 forbids adding a `style:` key to the reference manuscript before
`ms-r0-sent`, yet it must keep rendering the house look byte-identically.
After ms-r0-sent: add `style: kist-wcr` to the reference manuscript, then flip the final
fallback to `default` (one-line change, marked in the source).

## 4. Follow-ups left for daytime

1. **README.md / CLAUDE.md paths are stale**: `profiles/` and `styles/` now
   live at `src/wongo/profiles/` and `src/wongo/styles/`. CLAUDE.md line 16
   still says `styles/*.yml` — owner may want to reword.
2. Steps 6–7 of the HANDOFF (thin skills, CONTRIBUTING/CHANGELOG, tag v0.1.0,
   PyPI decision) intentionally untouched.
3. `legacy/` is now pure shims; delete after step 6 lands.
4. `uv.lock` appeared (first `uv run` committed it) — keep or gitignore.
5. `wongo profile verify` fetches live URLs; consider `--offline` flag.
6. Scratch dirs left for inspection: `/tmp/wongo-bc/` (baseline+candidate),
   `/tmp/wongo-e2e/` (wheel-install render outputs). Safe to delete.
7. A `wongo` tool install was force-installed into `~/.local/bin` during
   wheel verification (`uv tool install --force`); uninstall if unwanted.

## 5. Verification ledger

| Gate | Result |
|---|---|
| pytest | 11 passed (docxpatch 7 incl. split-function parity, styles constants, engine cover-sheet ×3) |
| bytecompare selftest | zero noise floor |
| bytecompare check ×4 docs | main-collab/main-submission/si-* identical except allowlisted SI document.xml (phase ≥4); identical everywhere through phase 3 |
| wheel build | contains profiles + styles + scaffold template |
| wheel e2e | installed-tool `render --target both` produces all four DOCX from a fresh the reference manuscript copy |
