<!-- statutor: plane=state | policy=state (doctor-checked) | writer=orchestrator | stable IDs, one line per task -->
# TASKS

- [x] T-0001 Review and commit the current quality fixes plus Statutor conversion with all local gates green (committed 2026-09-19 as `ce35ad9`..`62e0d07` plus the ledger commit; see notes/overnight-2026-09-19.md).
- [ ] T-0002 Set `WONGO_REF_PROJECT` and pass byte comparison for collab and submission targets (baseline from `ad6019d` first; expect `si-*/document.xml` cover-count diff only, allowlisted). Then tag `v0.2.0` and push (D-0007).
- [ ] T-0003 Design a reference-inclusive word-count gate for profiles such as Water Research without false precision.
- [x] T-0004 Decide whether to formalize Ruff/Pyright configuration and python-docx factory type aliases (D-0004: ruff+pytest config in pyproject, CI lint step; Pyright/type aliases deferred).
- [x] T-0005 Fix `wongo render` crash for styles without `page:` geometry (pandoc 3.10 reference doc has no pgSz) — `default` style was unusable.
- [x] T-0006 SI cover sheet: stop counting figure wrappers as tables (docs/bugs/si-cover-table-count.md).
- [x] T-0007 `wongo diff`: rebuild hyperlink (crossref/citation) paragraphs instead of skipping them; keep per-run formatting; report nested-table changes; collision-free revision ids.
- [x] T-0008 TOC art: fit inside the profile's width×height box preserving aspect ratio (ACS 3.25 in × 1.75 in).
- [x] T-0009 Profile contract: `line_numbers: forbidden` (D-0005); Water Research profile updated; submission render strips house-style line numbers.
- [x] T-0010 `default` style must keep the journal reference-doc fonts (engine no longer forces Cambria when `font: null`).
- [x] T-0011 Recreate the roundtrip-parser and sectPr-order regression tests lost in the skill→package migration; add end-to-end `run_checks` and styles tests.
- [x] T-0012 `wongo profile verify` lints profile.yml against the contract (`validate_profile`); all shipped profiles pass.
- [x] T-0013 `wongo check`: discover `bibliography` from `_quarto.yml`/front matter; ignore commented-out images, div fences, and shortcodes.
- [x] T-0014 `wongo roundtrip --qmd` for SI renders; robustness guards (empty SI body, abstract/authors as last paragraph).
- [x] T-0015 Profile reference-doc builders: strip theme font attributes from heading styles so the `default` style does not fall back to Aptos (`eac0f96`; all seven reference.docx regenerated; kist-wcr renders verified byte-identical via canonical rFonts order in `set_fonts`).
- [x] T-0016 Decide the next release boundary (v0.2.0: diff v2, contract lint, default-style fix) and bump `pyproject`/`CITATION.cff`/`__init__` together (`62e0d07`, D-0007; tag/push after T-0002).
