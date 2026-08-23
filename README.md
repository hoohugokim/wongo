# wongo (원고)

*Wongo* is Korean for **manuscript** — and this is a manuscript pipeline:
write a journal article as a Quarto `.qmd` with every inferential number wired
to committed analysis artifacts, render **submission-grade DOCX** against
**verified journal profiles**, keep **Word-native coauthors** in the loop with
tracked-changes round-tripping, and never let a hand-typed number or a stale
journal rule reach a submission portal.

> **Status: pre-alpha scaffold (v0.1.0.dev0).** The engine is battle-tested —
> it produced a real ES&T submission — but it currently lives in `legacy/`
> verbatim from its previous life as a set of Claude Code skills. The package
> refactor is mapped in `HANDOFF-wongo-uplift.md`. Until it lands, the CLI
> delegates to the legacy scripts and requires an editable install.

## Why this exists

Labs full of Word users reject source-based writing tools for two reasons:
the output doesn't look like *their* manuscripts, and coauthor feedback has
nowhere to go. wongo answers both, and adds a third discipline nobody else
has:

1. **Verified journal profiles.** Every journal requirement (word limits and
   their exact counting rules, abstract length, TOC-art specs, SI packaging,
   reviewer minimums) is recorded in `profiles/<journal>/profile.yml` with its
   official source URL and verification date, split into VERIFIED facts and a
   TO-VERIFY queue. Renders warn when a profile goes stale. This caught ACS
   changing the ES&T guidelines *three weeks after* a verification pass.
2. **House styles.** The lab's look (title-page shape, line numbers, spacing,
   table rules) is a style profile in `styles/`, separate from journal HARD
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

## Quickstart (scaffold phase)

```sh
uv tool install --editable /path/to/wongo   # editable: engine still in legacy/
cd your-manuscript/                          # needs _journal.yml, index.qmd
wongo check                                  # validation report
wongo render --target collab                 # coauthor-facing DOCX (main + SI)
wongo render --target submission             # refuses on any HARD failure
wongo roundtrip coauthor-edits.docx          # -> decisions/merge-<date>-*.md
```

External requirements: [Quarto](https://quarto.org) ≥1.10, R with knitr (for
R-engine manuscripts), and the fonts your style profile names.

## Repository layout

| Path | What |
|---|---|
| `src/wongo/` | The package: CLI now, engine/docxpatch/profiles modules as the migration lands |
| `legacy/` | The proven scripts, verbatim (`render.py`, `validate.py`, `roundtrip.py`, `mslib.py`) — behavioral reference until fully absorbed |
| `profiles/` | Journal profiles: `est`, `wr`, `npjcw`, `natwater`, `microbiome`, `envmicrobiome`, `npjbiofilms` (contract: `docs/journal-profile-contract.md`) |
| `styles/` | House-style profiles (`kist-wcr`, `default`) |
| `assets/` | New-manuscript scaffold, cover-letter template |
| `docs/` | Profile contract, the DOCX quirks bestiary, legacy spine docs |
| `tests/` | Regression tests pinning every shipped OOXML fix |

## Provenance

Grown inside the the reference manuscript project (KIST Water Cycle Research) while preparing
a real ES&T submission with Word-native coauthors; extracted here to be
standardized and shared. First consumer: that same manuscript, which pins the
migration by byte-comparison of its renders.

## License

MIT — see `LICENSE`.
