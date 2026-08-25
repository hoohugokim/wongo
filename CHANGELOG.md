# Changelog

All notable changes to wongo are documented here. Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- `wongo diff <original.docx> <revised.docx>` — S6 revision engine: stamps real Word track changes (`w:ins`/`w:del`, attributed author/date) into a copy of the revised render, word-level within replaced paragraphs and whole-paragraph insertions/deletions; tables intentionally untouched but reported via `tables_differ`. Output is pandoc-`--track-changes`-parseable, so `wongo roundtrip` can re-extract it. Seven new tests in `tests/test_diff.py`.
- CI: GitHub Actions workflow running pytest on Python 3.11–3.13, CLI smoke checks, wheel+sdist build with a package-data assertion; CodeQL analysis weekly and on pushes.
- `CITATION.cff` (cff 1.2.0, schema-validated) — cite the repo as software.
- README CI/CodeQL badges.

## [0.1.0] — 2026-08-24

First shareable release: `quarto-manuscript-*` skills uplifted into `wongo` Python package. The lab's reference manuscript now pins `style: kist-wcr` and uses `wongo` directly; skills thinned to wrappers. (Manuscript identity intentionally unnamed in this public repo.)

### Added
- `CONTRIBUTING.md` — ground-rule pinned behavior (now `legacy/` removed, post-`ms-r0-sent` wiring), dev setup, journal-profile contract and verification discipline, style layer, DOCX quirks memory, commit/release gates.
- This `CHANGELOG.md` (Keep a Changelog).

### Changed
- Stale doc paths fixed: `profiles/`/`styles/`/`assets/` → `src/wongo/profiles/`, `src/wongo/styles/`, `src/wongo/assets/scaffold` in `README.md` and `CLAUDE.md:16`; quickstart now `uv tool install --editable .` + `wongo scaffold`/`wongo profile` (`64052b9`).
- `wongo.engine:resolve_style` fallback flipped `kist-wcr` → `default` (`b1a8084`) — transitional wart (`OVERNIGHT-LOG §3`) resolved after the reference manuscript pinned `style: kist-wcr` in `manuscript/_journal.yml`.
- `~/.claude/skills/quarto-manuscript-sci` thinned to wrapper: `SKILL.md` now points to `wongo render/check/roundtrip/scaffold/profile`, `references/quarto-docx-quirks.md` and `references/journal-profile-contract.md` are pointers to `wongo/docs/*`, `scripts/` are deprecated shims, `assets/scaffold` is pointer to `wongo/src/wongo/assets/scaffold/`.
- `~/.claude/skills/quarto-manuscript-{est,wr,natwater,npjcw,microbiome,envmicrobiome,npjbiofilms}` thinned: `profile.yml` → deprecated pointer to `wongo/src/wongo/profiles/<slug>/profile.yml`, `assets/` and `scripts/` → pointers to `wongo` package data; `SKILL.md` retains VERIFIED/TO-VERIFY judgment with migration banner; `references/` judgment files kept (mirrored in `wongo`).
- `legacy/` shim directory removed (`render.py`, `validate.py`, `roundtrip.py`, `mslib.py`); `README.md`/`CLAUDE.md`/`CONTRIBUTING.md` updated to reflect removal (post-`ms-r0-sent`).

### Fixed
- `wongo.styles:fix_tables` missing `OxmlElement`/`qn` import for spacer paragraph (`f82b5f3`).

## [0.1.0.dev0] — 2026-08-24 (scaffold) + 2026-08-24 overnight uplift (steps 1–5)

Scaffolded from `~/.claude/skills/quarto-manuscript-*` mid-flight of an ES&T submission (identity intentionally unnamed here) (`HANDOFF-wongo-uplift.md`).

### Added
- `wongo.docxpatch` (`f0a50a4`): unconditional OOXML fixes — `dedupe_ppr`, `normalize_ppr_order` (+`_PPR_ORDER`), `patch_theme_fonts`/`patch_compat_mode`→`patch_document_package` (single zip pass, preserves no-theme1.xml early-return quirk), `set_fonts` (theme-attr stripping), `_tbl_rescale_grid`/`_tbl_set_width_pct`/`_tbl_set_borders`, `add_line_numbers`/`add_page_numbers`/`restart_page_numbering` with `_SECT_PR_TAIL` schema-correct `insert_element_before` — split parity tests added.
- `wongo.styles` (`eb6eec7`): data-driven house look from `src/wongo/styles/*.yml` (`kist-wcr` + `default` with `abstract_title`), `apply_style()` (page geometry, spacing/justify, heading look, WR `rebuild_title_block`/`inject_keywords`/`bold_caption_leads`/`_restyle_caption`, `fix_tables` with booktabs gate; grid rescaling stays unconditional in `docxpatch`).
- `wongo.profiles` (`81e8be4`): `load_journal_config`/`load_profile`/`profile_staleness_days` resolution `project-local → $WONGO_PROFILES ($QM_SKILLS_DIR alias) → src/wongo/profiles/` → repo-root fallback; 7 profiles (`est`, `wr`, `npjcw`, `natwater`, `microbiome`, `envmicrobiome`, `npjbiofilms`) moved into wheel (verified `reference.docx`+CSL shipped).
- `wongo.engine` + `wongo.engine.checks` + `wongo.engine.roundtrip` (`626886b`): `quarto_render`/`find_toc_art`/TOC-art gate (pre-render + postprocess backstop), `postprocess_main`/`postprocess_si`/`render_project`/`check_hard_failures`; checks `HARD`/`WARN` + text analysis; **SI cover fixes tests-first** (`tests/test_engine.py`): cover sheet now prints AUTHORS+title (not `Journal — ms_type`) and live `NUMPAGES` field (only `si-collab/submission/word/document.xml` diff, allowlisted).
- CLI `src/wongo/cli.py` (`b0a6f86`): real subcommands `render --target --project --style`, `check --strict`, `roundtrip <docx> --project`, `scaffold [dest]`, `profile list`, `profile verify <slug>` (HEAD drift audit; `[blocked]` for 403); `--style` threads through `resolve_style` (fallback `kist-wcr` transitional — see `OVERNIGHT-LOG §3`, flipped to `default` in v0.1.0).
- `tools/bytecompare.py` (`baseline`/`selftest`/`check`, whole-file allowlist `tools/bytecompare-allow.txt`) + `uv.lock` + wheel e2e (`uv tool install --force`); `ov` fixups `635a8e7` (kist-wcr layout), `f82b5f3` (`fix_tables` spacer `OxmlElement`/`qn` import).
- Known pathology memory `docs/docx-quirks.md` (duplicate `pPr`, `CT_PPr`/`CT_SectPr` sequence, `compatibilityMode`, Letter-grid on A4, caption float wrappers, etc.) pinned by tests.

### Changed
- `legacy/render.py`, `legacy/mslib.py`, `legacy/validate.py`, `legacy/roundtrip.py` → thin shims delegating to `wongo.*` (now removed in v0.1.0); imports in tests flipped from `legacy.render` to `wongo.docxpatch` where moved.

### Verified
- `pytest` 12 passed; `bytecompare selftest` noise floor zero; `bytecompare check --target both` identical for `main-*` (every phase) and allowlisted `si-*` (phase ≥4 only); wheel contains profiles/styles/scaffold and `~/.local/bin/wongo` renders all four DOCX from a fresh copy of the reference manuscript.

[Unreleased]: https://github.com/hoohugokim/wongo/compare/v0.1.0...HEAD
[0.1.0.dev0]: https://github.com/hoohugokim/wongo/releases/tag/v0.1.0.dev0
[0.1.0]: https://github.com/hoohugokim/wongo/releases/tag/v0.1.0
