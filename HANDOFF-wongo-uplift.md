# HANDOFF — wongo uplift (scaffold → v0.1.0)

> **Status: completed in v0.1.0 (2026-08-24) — retained as historical record.**
> `legacy/` shims removed, skills thinned to `wongo` wrappers, `style: kist-wcr`
> pinned by the lab's reference manuscript. Canonical code now in `src/wongo/`; skills at
> `~/.claude/skills/quarto-manuscript-*` are wrappers calling `wongo`
> (`docs/docx-quirks.md` is canonical quirks, `docs/journal-profile-contract.md`
> is canonical contract). For active work see `CONTRIBUTING.md` + `CHANGELOG.md`.

**For the dedicated session that turns this scaffold into the real package.**
Scaffolded 2026-08-24 from the `quarto-manuscript-*` Claude Code skills, mid-flight
of an ES&T submission (manuscript identity intentionally unnamed in the public repo).
Read this whole file before touching code.

## Ground rules

1. **Behavior is pinned.** `legacy/` is the verbatim, battle-tested engine that
   rendered a real submission. Every migration step must end with
   `tests/` green AND a byte-relevant comparison against the reference
   manuscript's renders (`WONGO_REF_PROJECT`, tag `ms-r0-initial`+): render with
   legacy, render with the migrated code, diff the unzipped document.xml /
   styles.xml / settings.xml. Cosmetic-identical or explainable-diff only.
2. **The live manuscript stays pinned to the skill scripts until `ms-r0-sent`
   is tagged.** Do NOT point the live manuscript at wongo before its r0 review
   round closes. After that, it becomes the first consumer and validation target.
3. **Correctness vs taste.** OOXML fixes (dedupe_ppr, normalize_ppr_order,
   patch_theme_fonts incl. compatibilityMode, grid rescaling) are UNCONDITIONAL
   engine behavior. The HOUSE_* constants are KIST-WCR taste and must move
   behind the style-profile layer (`styles/kist-wcr.yml`, already extracted).
   `styles/default.yml` defines the no-house-look baseline.

## Migration map (suggested order)

1. **wongo.docxpatch** ← from `legacy/render.py`: `dedupe_ppr`,
   `normalize_ppr_order` (+`_PPR_ORDER`), `patch_theme_fonts` (rename: it also
   stamps compatibilityMode; split into `patch_theme_fonts` + `patch_compat_mode`
   sharing one zip pass), `set_fonts` (theme-attr stripping), `_tbl_rescale_grid`,
   `_tbl_set_width_pct`, `_tbl_set_borders`, `add_line_numbers`,
   `add_page_numbers`, `restart_page_numbering`, `_style_by_name` (keep its
   BabelFish docstring). Tests exist in `tests/test_docxpatch.py` — extend as
   functions move (imports flip from `legacy/render.py` to `wongo.docxpatch`).
2. **wongo.styles** — new: load `styles/<name>.yml`; reimplement
   `apply_house_style` as data-driven (`title_block`, spacing/justify lists,
   caption/table options). Resolution: `_journal.yml` `style:` key → `--style`
   flag → `default`. The WR title-block rebuild (`rebuild_title_block`,
   `read_front_matter`, `inject_keywords`, `bold_caption_leads`,
   `_restyle_caption`) moves here, parameterized by the style file.
3. **wongo.profiles** ← from `legacy/mslib.py`: `load_journal_config`,
   `load_profile`, staleness checks. Resolution order: project-local
   `profiles/` dir → `$WONGO_PROFILES` → packaged `profiles/` (ship them as
   package data so a wheel install works; drop the `quarto-manuscript-<slug>`
   symlink shim and the QM_SKILLS_DIR env once nothing legacy remains).
4. **wongo.engine** ← `legacy/render.py`'s `quarto_render`, target logic,
   TOC-art gate, SI pipeline (`prepend_si_cover` has TWO KNOWN GAPS: cover
   sheet prints journal+type where the profile wants AUTHORS, and the
   page-count line ships a literal placeholder — fix during migration, tests
   first). `legacy/validate.py` → `wongo check` (keep the HARD/WARN report
   shape); `legacy/roundtrip.py` → `wongo roundtrip`.
5. **CLI**: replace the `runpy` delegation in `src/wongo/cli.py` subcommand by
   subcommand; add `wongo scaffold` (from `assets/scaffold/`) and
   `wongo profile verify <slug>` (the live-refetch drift audit — the 2026-08-24
   ES&T audit found a July-30 guideline revision this way; see that session's
   notes: SI paragraph moved BEFORE Acknowledgment, reviewers min 4,
   keywords 5–8 mandatory).
6. **Thin the Claude skills**: `quarto-manuscript-sci` and profile skills
   become wrappers that call the installed `wongo` CLI and keep only the
   judgment content (S4 disposition rules, S5 checklists). The quirks file's
   canonical home becomes `docs/docx-quirks.md` here — skills reference it.
7. **Docs/polish**: CONTRIBUTING (how to add a journal profile — the contract
   + verification discipline is the point of the project), CHANGELOG, tag
   v0.1.0, decide on publishing to PyPI (name `wongo` was free 2026-08-24).

## Known environment facts

- Quarto 1.10.18 / pandoc 3.10 on the Mac; R 4.6.1 now brew-linked (`Rscript`
  on PATH). Quarto 1.10 quirks this engine works around are documented in
  `docs/docx-quirks.md` — re-test them when Quarto is upgraded; several are
  version-specific (duplicate pPr, float wrapper tables, NBSP caption leads).
- `uv` is the runner of choice (`uv run --with pytest --with python-docx
  --with pyyaml pytest`).
- The skills these files came from live at `~/.claude/skills/quarto-manuscript-*`
  and REMAIN AUTHORITATIVE for the live manuscript until ms-r0-sent
  (ground rule 2). Any bug found there during the review round must be fixed
  BOTH there and here until the switch.

## Non-goals for v0.1.0

- No automated tracked-changes DIFF generation for resubmissions (S6 keeps
  Word Compare); no double-anonymized blinding automation; no figure
  generation (figures are project code, not pipeline code).
