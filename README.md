# Wongo · 원고

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="brand/logos/wongo-lockup-reverse.svg">
  <img src="brand/logos/wongo-lockup.svg" alt="Wongo · 원고" width="420">
</picture>

**A connected path from Quarto source to Word review.**

[Get started](docs/getting-started.md) · [Documentation](docs/README.md) ·
[Claude integration](integrations/claude-code/README.md) · [Design system](brand/README.md)

[![CI](https://github.com/hoohugokim/wongo/actions/workflows/ci.yml/badge.svg)](https://github.com/hoohugokim/wongo/actions/workflows/ci.yml)
[![CodeQL](https://github.com/hoohugokim/wongo/actions/workflows/codeql.yml/badge.svg)](https://github.com/hoohugokim/wongo/actions/workflows/codeql.yml)

*Wongo* is Korean for **manuscript**. It is a Python package and command-line
pipeline for writing in Quarto, checking journal requirements, producing Word
documents, and resolving coauthor edits. Journal profiles and house styles form
its extension surface. See the [product definition](docs/product-definition.md)
for the package, software, framework and library interfaces.

| Write & check | Render & share | Review & revise |
|:---|:---|:---|
| Keep prose, citations and analysis connected in `.qmd`. Check the target journal's recorded requirements. | Create main and supporting-information DOCX files with the selected journal profile and house style. | Extract Word Track Changes, inspect source context and record author-approved decisions before updating the source. |

**Release:** [v0.3.0](https://github.com/hoohugokim/wongo/releases/tag/v0.3.0).
This branch contains the **v0.3.1 development revision**, including the native MCP
integration and its [verified demo](examples/aix-demo/README.md). PyPI publication
is pending; use the source-archive installation below to install from `main`.

## Why this exists

Labs full of Word users reject source-based writing tools for two reasons:
the output doesn't look like *their* manuscripts, and coauthor feedback has
nowhere to go. Wongo brings three parts of the workflow together:

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

## New to wongo?

Read **[docs/getting-started.md](docs/getting-started.md)**: step-by-step setup
for Windows and macOS, written for people who have never used a terminal. The
recommended path is to let Claude run wongo for you: install Claude Code, add
this repository's plugin (see
[integrations/claude-code/README.md](integrations/claude-code/README.md)), and
ask Claude to "set up wongo". wongo runs on Windows 10/11, macOS and Linux;
CI renders the example manuscript on all three.

## Quickstart

```fish
uv tool install https://github.com/hoohugokim/wongo/archive/refs/heads/main.zip  # no git needed
wongo doctor                                 # is Quarto/R ready? (prints the fix if not)
wongo scaffold demo --example && cd demo     # a small manuscript that renders right away
wongo status                                 # where things stand + the next command
wongo check                                  # validation report
wongo render --target collab                 # coauthor-facing DOCX, opens with Track Changes on
wongo render --target submission             # refuses on any HARD failure
wongo roundtrip coauthor-edits.docx          # -> decisions/merge-<date>-*.md
wongo review decisions/merge-<date>-*.md     # decide each coauthor edit (digits only)
wongo worksheet lint decisions/merge-<date>-*.md  # must pass before edits reach the .qmd
wongo diff original.docx revised.docx        # -> revised-tracked.docx (S6 marked-up revision)
wongo profile show est                       # a journal's verified requirements
wongo profile verify est                     # journal profile drift audit
```

Every command accepts `--json` and then prints a single JSON object, which is
what the Claude plugin reads. A render replaces its output files only when every
step succeeded; if Word has one of them open, wongo says so and changes
nothing. For development, `uv tool install --editable .` from a checkout.

For limits that include references, such as Water Research, `wongo check`
reports the source estimate and remaining headroom. Rendering adds the new
main bibliography's words; an over-limit or unverified count blocks submission
before any existing deliverable is replaced. The combined count remains an
estimate, with its source and reference contributions shown in the report.

`wongo diff` tracks word-level changes in body paragraphs, keeping each
word's run formatting and rebuilding Quarto's crossref/citation hyperlinks
around the tracked runs. Changed paragraphs containing fields, drawings,
footnotes, or other rich OOXML are left intact and reported, as are table
differences (nested data tables included); use Word Compare for those
reported locations. `wongo roundtrip --qmd si.qmd` aligns a coauthor-edited
SI render against `si.qmd` instead of `index.qmd`.

External requirements: [Quarto](https://quarto.org) 1.10.x (the version
wongo's output is verified against), R with knitr and rmarkdown (for R-engine
manuscripts), and the fonts your style profile names. `wongo doctor` checks
all of them and prints the install command for your platform.

## Repository layout

| Path | What |
|---|---|
| `src/wongo/` | The package and library: `cli`, `engine`/`checks`/`roundtrip`/`diff`/`worksheet`, `review`, `doctor`, `status`, `scaffold`, `toolchain`, `docxpatch`, `styles` (`kist-wcr`/`default`), `profiles/` (7 journals), `assets/scaffold` |
| `integrations/claude-code/`, `.claude-plugin/` | The Claude Code plugin (the wongo skill) and the marketplace that serves it |
| `docs/` | Product definition (`docs/product-definition.md`), profile contract (`docs/journal-profile-contract.md`), DOCX quirks bestiary (`docs/docx-quirks.md`), contributing guide (`docs/CONTRIBUTING.md`), frozen changelog (`docs/CHANGELOG.md`), legacy spine docs |
| [`brand/`](brand/README.md) | Wongo design system: vector and PNG logos, offline fonts, design tokens, CSS, Quarto branding and a visual guide |
| `AGENTS.md`, `HANDOFF.md`, `TASKS.md`, `DECISIONS.md`, `ROADMAP.md` | Statutor ledger for agent sessions (`CLAUDE.md` imports `AGENTS.md`) |
| `plans/archive/` | Frozen historical records of the 2026-08 skill→package uplift |
| `tests/` | Regression tests pinning every shipped OOXML fix, the diff/roundtrip engines, and the validation checks |
| `tools/` | Verification harness (`tools/bytecompare.py`) — byte-compare `main`/`si` × `collab`/`submission` vs baseline |

## Project identity

The [Wongo design system](brand/README.md) supplies the manuscript-grid emblem,
serif wordmark, light/dark artwork, local fonts and reusable HTML/Quarto styling.
Open the [visual guide](brand/design-system.html) locally to inspect the system,
or use the [workflow brief](brand/examples/workflow-brief.qmd) as a branded document
example. GitHub controls Markdown typography; repository pages use the supplied
artwork and a consistent reading hierarchy.

Branding is for Wongo's documentation and communications. Journal output keeps
the requirements and typography of its selected profile and manuscript style.

## Provenance

Grown inside a KIST Water Cycle Research manuscript project while preparing
a real ES&T submission with Word-native coauthors; extracted here to be
standardized and shared. First consumer: that same manuscript, which pins the
migration by byte-comparison of its renders.

## License

MIT — see `LICENSE`.
