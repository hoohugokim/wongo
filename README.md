# wongo (원고)

[![CI](https://github.com/hoohugokim/wongo/actions/workflows/ci.yml/badge.svg)](https://github.com/hoohugokim/wongo/actions/workflows/ci.yml)
[![CodeQL](https://github.com/hoohugokim/wongo/actions/workflows/codeql.yml/badge.svg)](https://github.com/hoohugokim/wongo/actions/workflows/codeql.yml)

*Wongo* is Korean for **manuscript** — and this is a manuscript pipeline:

> **What it is:** a **Python package** (`pip install` / `uv tool install`, `wongo-0.1.0-py3-none-any.whl`) that ships a **CLI research-software pipeline** (`wongo scaffold` / `check` / `render` / `roundtrip` / `profile`) and an **extensible pipeline framework** (verified journal profiles + house styles satisfying `docs/journal-profile-contract.md`). See `docs/product-definition.md` for the canonical taxonomy (package vs software vs framework vs library).

Write a journal article as a Quarto `.qmd` with every inferential number wired
to committed analysis artifacts, render **submission-grade DOCX** against
**verified journal profiles**, keep **Word-native coauthors** in the loop with
tracked-changes round-tripping, and never let a hand-typed number or a stale
journal rule reach a submission portal.

> **Status: v0.1.0.** The engine is battle-tested — it produced a real ES&T
> submission — and has been migrated into `src/wongo/`
> (`docxpatch`/`styles`/`profiles`/`engine`) per `HANDOFF-wongo-uplift.md`.
> `legacy/` shims were removed in v0.1.0; the lab's reference manuscript pins
> `style: kist-wcr` and renders through `wongo`. The CLI `wongo` is installed
> as a wheel/editable package.

## Why this exists

Labs full of Word users reject source-based writing tools for two reasons:
the output doesn't look like *their* manuscripts, and coauthor feedback has
nowhere to go. wongo answers both, and adds a third discipline nobody else
has:

1. **Verified journal profiles.** Every journal requirement (word limits and
   their exact counting rules, abstract length, TOC-art specs, SI packaging,
   reviewer minimums) is recorded in `src/wongo/profiles/<journal>/profile.yml` with its
   official source URL and verification date, split into VERIFIED facts and a
   TO-VERIFY queue. Renders warn when a profile goes stale. This caught ACS
   changing the ES&T guidelines *three weeks after* a verification pass.
2. **House styles.** The lab's look (title-page shape, line numbers, spacing,
   table rules) is a style profile in `src/wongo/styles/` (`kist-wcr`/`default`), separate from journal HARD
   rules and from OOXML correctness fixes. Coauthors meet a familiar page;
   the source stays clean.
3. **Round-tripping.** Coauthors annotate a rendered DOCX with Track Changes
   and comments; `wongo roundtrip` extracts every edit with author attribution
   into a merge worksheet; a human disposes each row; the `.qmd` stays the
   single source of truth.

Along the way it fixes real OOXML pathologies in the Quarto/pandoc DOCX
toolchain — duplicate `pPr` elements, schema-order violations that make Word
silently discard formatting, missing `compatibilityMode` (Compatibility Mode),
theme-font leaks (Aptos), and Letter-width table grids on A4 pages. Each is
documented with its root cause in `docs/docx-quirks.md` and pinned by a test.

## Quickstart

```sh
uv tool install --editable .                 # or: pip install -e .
cd your-manuscript/                          # needs _journal.yml, index.qmd
wongo check                                  # validation report
wongo render --target collab                 # coauthor-facing DOCX (main + SI)
wongo render --target submission             # refuses on any HARD failure
wongo roundtrip coauthor-edits.docx          # -> decisions/merge-<date>-*.md
wongo diff original.docx revised.docx        # -> revised-tracked.docx (S6 marked-up revision)
wongo scaffold my-paper && cd my-paper       # new manuscript from template
wongo profile list && wongo profile verify est  # journal profile drift audit
```

External requirements: [Quarto](https://quarto.org) ≥1.10, R with knitr (for
R-engine manuscripts), and the fonts your style profile names.

## Repository layout

| Path | What |
|---|---|
| `src/wongo/` | The package and library: `cli`, `engine`/`checks`/`roundtrip`, `docxpatch`, `styles` (`kist-wcr`/`default`), `profiles/` (7 journals), `assets/scaffold` |
| `docs/` | Product definition (`docs/product-definition.md`), profile contract (`docs/journal-profile-contract.md`), DOCX quirks bestiary (`docs/docx-quirks.md`), legacy spine docs |
| `tests/` | Regression tests pinning every shipped OOXML fix |
| `tools/` | Verification harness (`tools/bytecompare.py`) — byte-compare `main`/`si` × `collab`/`submission` vs baseline |

## Provenance

Grown inside a KIST Water Cycle Research manuscript project while preparing
a real ES&T submission with Word-native coauthors; extracted here to be
standardized and shared. First consumer: that same manuscript, which pins the
migration by byte-comparison of its renders.

## License

MIT — see `LICENSE`.
