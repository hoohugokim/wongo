---
name: quarto-manuscript-est
description: >
  Journal profile for Environmental Science & Technology (ES&T, ACS),
  consumed by quarto-manuscript-sci. Use whenever a manuscript targets ES&T
  or the user mentions ES&T, Environmental Science & Technology, ACS
  Publishing Center / Paragon Plus, TOC art or abstract graphics for ACS, or
  ACS reference style — for authoring, rendering, validation, submission
  packaging, or revision. NOT for ES&T Letters or ACS Environmental Au
  (different limits; separate profiles).
compatibility: Consumed by quarto-manuscript-sci; not intended standalone.
---

# Journal Profile: Environmental Science & Technology (ACS)

Implements `references/journal-profile-contract.md` from `quarto-manuscript-sci`.
Facts below are split into **VERIFIED** (official ACS sources, linked) and a
**TO VERIFY** queue (secondary sources or memory — do NOT promote to
`profile.yml` until checked against the current Author Guidelines PDF at
https://researcher-resources.acs.org/publish/author_guidelines?coden=esthag ).

## VERIFIED requirements (as of 2026-07-04)

Sources: [ES&T Author Guidelines PDF (ACS)](https://researcher-resources.acs.org/publish/author_guidelines/pdf?coden=esthag) ·
[ES&T Author Guidelines (HTML)](https://researcher-resources.acs.org/publish/author_guidelines?coden=esthag) ·
[ACS Peer Reviews policy](https://researcher-resources.acs.org/publish/peer_reviews) ·
[ES&T Information for Authors](https://pubs.acs.org/page/esthag/submission/authors.html) ·
[ES&T revision instructions](https://pubs.acs.org/page/esthag/submission/revisions.html) ·
[ES&T word-limit editorial, 10.1021/es2012269](https://pubs.acs.org/doi/10.1021/es2012269) ·
[Guidelines for Table of Contents/Abstract Graphics (ACS, dated 2024-02-28)](https://pubs.acs.org/paragonplus/submission/toc_abstract_graphics_guidelines.pdf) (local copy: `archive/toc_abstract_graphics_guidelines.pdf`, fetched by the user 2026-07-04)

**Manuscript types & word limits** (limit covers main text; title, authors,
affiliations, references, and TOC art sit outside it — exact counting rule is
in the Author Guidelines PDF and enforced via ES&T Checklists):
- Research Article — 7,000 words
- Policy Analysis — 7,000 words
- Feature — 5,000 words
- Critical Review — 10,000 words
- Correspondence — 1,000 words
- Viewpoint — 1,000 words, NO abstract, ≤5 references, ≤1 single-pane figure
  (50-word caption) OR one 350-word table
- Letter to the Editor — 500 words, NO abstract

**TOC art**: required for ES&T submissions; a "visual abstract" that
illustrates the manuscript without duplicating a contained figure. Uploaded
separately AND referenced in manuscript flow. Full dimensions, format, and
placement rules are verified below (source: the official "Guidelines for
Table of Contents/Abstract Graphics" PDF, dated 2024-02-28).

**TOC/Abstract Graphic — full specification** (VERIFIED against
[Guidelines for Table of Contents/Abstract Graphics](https://pubs.acs.org/paragonplus/submission/toc_abstract_graphics_guidelines.pdf)
(ACS, dated 2024-02-28; local copy at
`archive/toc_abstract_graphics_guidelines.pdf`, fetched by the user
2026-07-04)):
- **Purpose**: required for every manuscript; must give a visual impression
  of the paper's essence WITHOUT showing specific results.
- **Size**: must fit within an area no larger than 3.25 in × 1.75 in
  (≈ 82.55 mm × 44.45 mm). → `profile.yml` `toc_graphic.width_mm` / `height_mm`.
- **File format**: TIF at 300 dpi if in color, or 1200 dpi if black-and-white;
  OR EPS in RGB document color mode with all fonts outlined/embedded.
  → `profile.yml` `toc_graphic.formats: [tif, eps]`, `min_dpi: 300` (the
  color-TIF floor; B&W TIF needs 1200 dpi; EPS is vector and dpi-exempt).
- **Typography**: sans serif (e.g., Helvetica); preferred size 8 pt, minimum
  6 pt.
- **Content rules** (authoring guidance — enforce by judgment, not by
  render.py):
  - Must be entirely original, unpublished artwork created by a coauthor.
  - No photographs, drawings, or caricatures of people.
  - No stamps, currency, trademarks, or logos.
  - Avoid reusing a graphic that already appears in the manuscript body —
    the TOC graphic should be a distinct visual synthesis, not a duplicate
    figure.
  - Text is limited to labels, arrows, and diagram annotations — not
    prose.
- **Manuscript placement**: label the graphic **"For Table of Contents
  Only"** and place it on the **LAST PAGE** of the submitted manuscript. It
  may ALSO be uploaded separately to the submission portal as "Graphics for
  manuscript". → `profile.yml` `toc_graphic.label` / `manuscript_placement`;
  `render.py`'s `insert_toc_art()` appends the labeled graphic at the end of
  the document accordingly.
- **Synopsis requirement — RESOLVED, does not exist**: the current official
  guidance (2024-02-28 PDF) contains no mention of a synopsis, abstract
  blurb, or word count anywhere in the TOC/Abstract Graphics rules. The
  earlier "50–60-word synopsis" claim tracked in TO VERIFY was a secondary
  source and is now refuted for current ACS guidance — `synopsis_words`
  stays `null` in `profile.yml` on purpose, not because it's unverified.

**Revision discipline**: revised manuscripts must stay at or below the word
limit; if over, must not exceed the submitted version's count, and any excess
needs explicit justification in the revision letter. Build this into S6.

**Supporting Information**: submitted as separate file(s); "Supporting
Information Available" paragraph placed after Acknowledgments ending with the
standard availability sentence; SI needs a cover sheet (authors, title, counts
of pages/figures/tables) and pages numbered S1, S2, …. Letters to the Editor,
Features, Viewpoints, and Correspondence cannot include SI.

**References**: author responsibility for accuracy/format per the ACS Style
Guide / Literature Citation Sample. → `assets/american-chemical-society.csl`
(pull from the official CSL repository; do NOT hand-write).

**Submission**: via ACS Publishing Center; cover letter required; suggested
reviewers expected; ORCID and complete funding declarations (Funder Registry
+ in-manuscript) required; iThenticate similarity screening; AI-use must
follow ACS AI policies (disclose per current ACS guidance).

**Editorial screen (desk rejection)**: novelty = new data, new interpretation
of existing data, or new analyses yielding environmental insight; significance
judged by breadth of impact; routine-data manuscripts declined. Environmental
relevance must be demonstrable, not asserted. → expand in
`references/editorial-framing.md` and wire into the cover-letter draft.

**Word count rule** (verified against the live Author Guidelines page,
2026-07-03): count runs from the Abstract through the end of the main text
(abstract + body + titles/footnotes/captions of graphics); references are
excluded; all front/back matter (title, authors, affiliations, TOC graphic,
figures, tables, reference list, SI file-list, acknowledgments, notes) is
excluded. **Figures and tables carry no separate per-graphic word-count
equivalent** — the "figures/tables have word-count penalties" secondary claim
is false for ES&T. Exception: Correspondence/Rebuttal's 1,000-word limit
explicitly *includes* citations, unlike the general rule. `validate.py`'s
word-limit check only counts `index.qmd` (main text) against this rule; SI
content in `si.qmd` is never included, matching this journal's own rule.

**Line numbers**: NOT required for submission ("Line numbers are not
required." — Manuscript Submission Requirements Checklist).

**Section heading**: the manuscript template uses **"Materials and
Methods"**, not "Experimental Section" (the phrase "Experimental Section"
appears only informally, once, in the Safety Considerations text). The
secondary source's claim that ACS mandates "Experimental Section" is
refuted for ES&T.

**Peer-review blinding**: ACS-wide policy is **single-anonymized review** —
authors do not know reviewer identities, but reviewers know author identities
("ACS journals engage in single-anonymized review." — ACS Peer Reviews page).
No ES&T-specific double-anonymous option was found in any fetched official
source.

**Figure color policy** (partial): color reproduction is free of additional
cost to authors; figures meant for black-and-white/grayscale reproduction
must not be submitted in color; color must not be the sole carrier of
information; graphics must meet WCAG contrast minimums (4.5:1 text, 3:1
non-text). Minimum resolutions: 1200 dpi (B&W line art), 600 dpi (grayscale),
300 dpi (color). RGB-vs-CMYK color space is NOT stated anywhere in the
fetched guidance — stays open (see TO VERIFY).

**Table style** (partial): each table needs a brief one-phrase/sentence
title understandable without reference to the text; details/definitions go
in footnotes, not the title; don't merge/split cells. Horizontal-rules-only
borders, caption-above placement, and superscript-letter (vs numeral)
footnote markers are NOT stated in the fetched guidance — stays open (see
TO VERIFY).

**Abstract length/structure**: 150–200 words, one paragraph (purpose,
methods/procedures, significant new results, implications; no reference
numbers) for Research Articles, Review, Policy Analysis, and Perspective
manuscripts. Features get a shorter 3–5 sentence abstract for a
scientifically literate general audience. Viewpoint manuscripts have no
abstract.

**Figure placement**: figures/charts/tables/schemes/equations should be
embedded inline in the text at the point of relevance for initial submission
("Fast Format").

**Supporting Information file format**: SI is NOT required to be PDF-only.
The official guidelines' own examples of sufficient SI descriptions include
both "(PDF)" and "(DOC)" as acceptable file-type labels.

## TO VERIFY (secondary sources / memory — check before first real submission)

- [ ] Figure color space: RGB vs CMYK (for regular in-text figures, NOT the
      TOC graphic) — tried 2026-07-03: fetched and read the Author Guidelines
      "Preparing Graphics → Color" section in full; it covers free color
      reproduction, grayscale/color-intent matching, and WCAG contrast, but
      never states a required color space. (The free-color-reproduction and
      accessibility facts ARE now in VERIFIED.) The 2026-07-04 TOC/Abstract
      Graphics PDF does specify RGB, but only for its own EPS-format TOC
      graphic option — that rule does not generalize to regular manuscript
      figures, so this item stays open.
- [ ] Table border/rule style, caption position (above vs below), and
      footnote-marker convention (superscript letters vs numerals) — tried
      2026-07-03: fetched and read the Author Guidelines "Tables" section in
      full; it only says tables need a brief title and that details go in
      footnotes, not the title. No statement on rule/border style, caption
      placement, or footnote-marker format. (The confirmed part is now in
      VERIFIED.)
- [ ] SI: whether SI must contain its own table of contents — tried
      2026-07-03: fetched and read the Author Guidelines Supporting
      Information section in full; it covers the per-file description
      requirement and Review-Only file handling but never addresses an
      internal SI table of contents.
- [ ] Manuscript line spacing requirement (single vs double) — tried
      2026-07-03: not addressed on the researcher-resources
      author-guidelines page; check the ES&T Checklists / formatting
      section when accessible. (Tracks the pre-existing `spacing: null`
      in `profile.yml`.)
- Rule: each checked item moves UP into VERIFIED with a link, and its number
  lands in `profile.yml`; update `verified_date`.

## Quarto/DOCX implementation notes for this journal

- `assets/reference.docx` is generated by `scripts/build_reference_docx.py`
  from a fresh `quarto pandoc --print-default-data-file reference.docx`,
  restyled to Times New Roman — 12pt for body/heading styles, 10pt for
  caption styles (no ES&T-specific font/size requirement was found during
  verification, so this uses a standard, portal-safe serif default). Line numbers and spacing are
  NOT baked into this file (line numbers confirmed NOT required; spacing
  still pending verification above) — they, plus the collab-vs-submission
  font swap (Pretendard for internal drafts, Times New Roman for submission),
  are `--target`-dependent choices already implemented in `render.py` (see
  `quarto-manuscript-sci` §3), not in the reference doc itself. Re-run the
  builder script when requirements change; never hand-edit the `.docx`.
- TOC art is generated OUTSIDE the manuscript render: drop the finished
  graphic at `figures/toc-art.{png,tiff,tif,jpg,jpeg}` in the project —
  `render.py`'s `find_toc_art()` discovers it there and `insert_toc_art()`
  appends it at the END of the document (a page break, the "For Table of
  Contents Only" label, then the centered image, per this profile's
  `toc_graphic.label` and `manuscript_placement: last-page`) for `--target
  submission` (hard error if this profile's `toc_graphic.required` is true
  and no file is found). Producing the graphic itself at the verified
  dimensions (3.25 in × 1.75 in / 82.55 mm × 44.45 mm; see the full
  specification above) is not part of the manuscript render.
- Word count: `validate.py` counts body prose + the front-matter `abstract` +
  figure/table caption text in `index.qmd`, excluding headings, code, and the
  references-section-as-rendered. This is an approximation of this profile's
  `manuscript_types[].counting_rule`, not an exact reimplementation of the
  ES&T Author Guidelines derivation — ACS's own submission-system checker is
  authoritative; `references/submission-checklist.md` paraphrases the same
  rule with a link, for human review at S5.
- SI pagination (S1…): `render.py`'s `postprocess_si` handles this — it
  restarts page numbering at 1 with the profile's `si.page_prefix`, and
  prepends a cover sheet (from `_journal.yml` metadata plus figure/table
  counts read off the rendered SI docx) when `si.needs_cover_sheet` is true.

## Files in this profile

- `profile.yml` — machine-readable; ONLY verified numbers
- `scripts/build_reference_docx.py` — reproducible builder for the generated
  `assets/reference.docx`; re-run it when requirements change (never
  hand-edit the .docx)
- `assets/reference.docx` — generated by `scripts/build_reference_docx.py`;
  never hand-edit
- `assets/american-chemical-society.csl` — fetched 2026-07-03 from the official
  CSL styles repository
  (https://raw.githubusercontent.com/citation-style-language/styles/master/american-chemical-society.csl)
- `references/submission-checklist.md` — S5 gate list, HARD/SOFT
- `references/editorial-framing.md` — scope + cover-letter angle
