# Changelog

All notable changes to wongo are documented here. Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed
- Stale doc paths: `profiles/`/`styles/`/`assets/` → `src/wongo/profiles/`, `src/wongo/styles/`, `src/wongo/assets/scaffold` in `README.md` and `CLAUDE.md:16`; legacy status updated from "verbatim" to thin shims (HANDOFF 1–5 complete, kept for the reference manuscript until `ms-r0-sent`); quickstart now reflects `uv tool install --editable .` and `wongo scaffold`/`wongo profile` commands. ([#OVERNIGHT-LOG §4.1])

### Added
- `CONTRIBUTING.md` — ground-rule pinned behavior, dev setup, journal-profile contract and verification discipline, style layer, DOCX quirks memory, commit/release gates.
- This `CHANGELOG.md`.

## [0.1.0.dev0] — 2026-08-24 (scaffold) + 2026-08-24 overnight uplift (steps 1–5)

Scaffolded from `~/.claude/skills/quarto-manuscript-*` mid-flight of the the reference manuscript ES&T submission (`HANDOFF-wongo-uplift.md`).

### Added
- `wongo.docxpatch` (`f0a50a4`): unconditional OOXML fixes — `dedupe_ppr`, `normalize_ppr_order` (+`_PPR_ORDER`), `patch_theme_fonts`/`patch_compat_mode`→`patch_document_package` (single zip pass, preserves no-theme1.xml early-return quirk), `set_fonts` (theme-attr stripping), `_tbl_rescale_grid`/`_tbl_set_width_pct`/`_tbl_set_borders`, `add_line_numbers`/`add_page_numbers`/`restart_page_numbering` with `_SECT_PR_TAIL` schema-correct `insert_element_before` — split parity tests added.
- `wongo.styles` (`eb6eec7`): data-driven house look from `src/wongo/styles/*.yml` (`kist-wcr` + `default` with `abstract_title`), `apply_style()` (page geometry, spacing/justify, heading look, WR `rebuild_title_block`/`inject_keywords`/`bold_caption_leads`/`_restyle_caption`, `fix_tables` with booktabs gate; grid rescaling stays unconditional in `docxpatch`).
- `wongo.profiles` (`81e8be4`): `load_journal_config`/`load_profile`/`profile_staleness_days` resolution `project-local → $WONGO_PROFILES ($QM_SKILLS_DIR alias) → src/wongo/profiles/` → repo-root fallback; 7 profiles (`est`, `wr`, `npjcw`, `natwater`, `microbiome`, `envmicrobiome`, `npjbiofilms`) moved into wheel (verified `reference.docx`+CSL shipped).
- `wongo.engine` + `wongo.engine.checks` + `wongo.engine.roundtrip` (`626886b`): `quarto_render`/`find_toc_art`/TOC-art gate (pre-render + postprocess backstop), `postprocess_main`/`postprocess_si`/`render_project`/`check_hard_failures`; checks `HARD`/`WARN` + text analysis; **SI cover fixes tests-first** (`tests/test_engine.py`): cover sheet now prints AUTHORS+title (not `Journal — ms_type`) and live `NUMPAGES` field (only `si-collab/submission/word/document.xml` diff, allowlisted).
- CLI `src/wongo/cli.py` (`b0a6f86`): real subcommands `render --target --project --style`, `check --strict`, `roundtrip <docx> --project`, `scaffold [dest]`, `profile list`, `profile verify <slug>` (HEAD drift audit; `[blocked]` for 403); `--style` threads through `resolve_style` (transitional fallback `kist-wcr` when `_journal.yml` omits `style:` — see `OVERNIGHT-LOG §3`, flip to `default` after tagging `style: kist-wcr` in the reference manuscript).
- `tools/bytecompare.py` (`baseline`/`selftest`/`check`, whole-file allowlist `tools/bytecompare-allow.txt`) + `uv.lock` + wheel e2e (`uv tool install --force`); `ov` fixups `635a8e7` (kist-wcr layout), `f82b5f3` (`fix_tables` spacer `OxmlElement`/`qn` import).
- Known pathology memory `docs/docx-quirks.md` (duplicate `pPr`, `CT_PPr`/`CT_SectPr` sequence, `compatibilityMode`, Letter-grid on A4, caption float wrappers, etc.) pinned by tests.

### Changed
- `legacy/render.py`, `legacy/mslib.py`, `legacy/validate.py`, `legacy/roundtrip.py` → thin shims delegating to `wongo.*`; imports in tests flipped from `legacy.render` to `wongo.docxpatch` where moved.

### Verified
- `pytest` 12 passed; `bytecompare selftest` noise floor zero; `bytecompare check --target both` identical for `main-*` (every phase) and allowlisted `si-*` (phase ≥4 only); wheel contains profiles/styles/scaffold and `~/.local/bin/wongo` renders all four DOCX from a fresh the reference manuscript copy.

## [0.1.0] — TBD

Planned: HANDOFF steps 6–7 — thin `quarto-manuscript-sci` + profile skills to `wongo` CLI wrappers (keep judgment content only), canonicalize `docs/docx-quirks.md`, delete `legacy/`, decide PyPI publish (`wongo` free 2026-08-24). Tag after `ms-r0-sent` when the reference manuscript can adopt `src/wongo/` and byte-compare stays green on the `kist-wcr`→`default` fallback flip.

[Unreleased]: https://github.com/hoohugokim/wongo/compare/v0.1.0.dev0...HEAD
[0.1.0.dev0]: https://github.com/hoohugokim/wongo/releases/tag/v0.1.0.dev0
[0.1.0]: https://github.com/hoohugokim/wongo/releases/tag/v0.1.0
