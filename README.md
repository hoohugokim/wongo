# wongo (원고)

[![CI](https://github.com/hoohugokim/wongo/actions/workflows/ci.yml/badge.svg)](https://github.com/hoohugokim/wongo/actions/workflows/ci.yml)
[![CodeQL](https://github.com/hoohugokim/wongo/actions/workflows/codeql.yml/badge.svg)](https://github.com/hoohugokim/wongo/actions/workflows/codeql.yml)

*Wongo* is Korean for **manuscript** — and this is a manuscript pipeline:

> **What it is:** a **Python package** (`pip install` / `uv tool install`, `wongo-0.2.0-py3-none-any.whl`) that ships a **CLI research-software pipeline** (`wongo scaffold` / `doctor` / `status` / `check` / `render` / `roundtrip` / `review` / `diff` / `profile`) and an **extensible pipeline framework** (verified journal profiles + house styles satisfying `docs/journal-profile-contract.md`). See `docs/product-definition.md` for the canonical taxonomy (package vs software vs framework vs library).

Write a journal article as a Quarto `.qmd` with every inferential number wired
to committed analysis artifacts, render **submission-grade DOCX** against
**verified journal profiles**, keep **Word-native coauthors** in the loop with
tracked-changes round-tripping, and never let a hand-typed number or a stale
journal rule reach a submission portal.

> **Status: v0.2.0** (diff v2 for cited prose, profile contract lint, `default`-style and SI-cover fixes; v0.1.0 was the first shareable release). The engine is battle-tested — it produced a real ES&T
> submission — and has been migrated into `src/wongo/`
> (`docxpatch`/`styles`/`profiles`/`engine`) per `plans/archive/HANDOFF-wongo-uplift.md`.
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

## New to wongo?

Read **[docs/getting-started.md](docs/getting-started.md)**: step-by-step setup
for Windows and macOS, written for people who have never used a terminal. The
recommended path is to let Claude run wongo for you: install Claude Code, add
this repository's plugin (see
[integrations/claude-code/README.md](integrations/claude-code/README.md)), and
ask Claude to "set up wongo". wongo runs on Windows 10/11, macOS and Linux;
CI renders the example manuscript on all three.

## Quickstart

```sh
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
| `AGENTS.md`, `HANDOFF.md`, `TASKS.md`, `DECISIONS.md`, `ROADMAP.md` | Statutor ledger for agent sessions (`CLAUDE.md` imports `AGENTS.md`) |
| `plans/archive/` | Frozen historical records of the 2026-08 skill→package uplift |
| `tests/` | Regression tests pinning every shipped OOXML fix, the diff/roundtrip engines, and the validation checks |
| `tools/` | Verification harness (`tools/bytecompare.py`) — byte-compare `main`/`si` × `collab`/`submission` vs baseline |

## Provenance

Grown inside a KIST Water Cycle Research manuscript project while preparing
a real ES&T submission with Word-native coauthors; extracted here to be
standardized and shared. First consumer: that same manuscript, which pins the
migration by byte-comparison of its renders.

## License

MIT — see `LICENSE`.
