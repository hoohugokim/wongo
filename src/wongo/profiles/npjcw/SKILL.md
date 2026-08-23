---
name: quarto-manuscript-npjcw
description: >
  Journal profile for npj Clean Water (Nature Portfolio, Springer Nature),
  consumed by quarto-manuscript-sci. Use whenever a manuscript targets npj
  Clean Water or the user mentions npj Clean Water, Nature Portfolio water
  journal, Nature/npj referencing style, or Springer Nature submission for
  desalination/water/wastewater research — for authoring, rendering,
  validation, submission packaging, or revision. NOT for Nature Water (a
  separate, more selective Nature-brand journal; different profile).
compatibility: Consumed by quarto-manuscript-sci; not intended standalone.
---

# Journal Profile: npj Clean Water (Nature Portfolio / Springer Nature)

Implements `references/journal-profile-contract.md` from `quarto-manuscript-sci`.
Facts below are split into **VERIFIED** (official nature.com/npjcleanwater
pages, fetched and read this session) and a **TO VERIFY** queue (not
addressed by any fetched page) — do NOT promote to `profile.yml` until an
official source is fetched and read.

## VERIFIED requirements (as of 2026-07-04)

Sources: [Aims & Scope](https://www.nature.com/npjcleanwater/aims) ·
[Content types](https://www.nature.com/npjcleanwater/content-types) ·
[For Authors and Referees](https://www.nature.com/npjcleanwater/for-authors-and-referees) ·
[Guide to Authors](https://www.nature.com/npjcleanwater/for-authors-and-referees/guide-to-authors) ·
[Submission guidelines](https://www.nature.com/npjcleanwater/for-authors-and-referees/submission-guidelines) ·
[Editorial process](https://www.nature.com/npjcleanwater/for-authors-and-referees/editorial-process) ·
[Editorial policies](https://www.nature.com/npjcleanwater/editorial-policies) ·
[Editorial policies > Peer Review](https://www.nature.com/npjcleanwater/editorial-policies/peer-review) ·
[Editorial policies > Artificial Intelligence (AI)](https://www.nature.com/npjcleanwater/editorial-policies/ai) ·
[Article Processing Charges](https://www.nature.com/npjcleanwater/apc) ·
[Journal homepage](https://www.nature.com/npjcleanwater/)

**Publisher / journal**: Springer Nature (Nature Portfolio), published in
partnership with King Fahd University of Petroleum and Minerals (KFUPM).
ISSN 2059-7037 (online only; fully Open Access, part of the npj Series).

**Scope** (verbatim from Aims & Scope): "npj Clean Water considers research
that explores all aspects of the sustainable supply of clean water,"
covering drinking-water/wastewater treatment (physical/chemical/biological);
new materials and process technologies incl. nanotechnologies; desalination
of seawater, groundwater, and non-traditional sources; renewable-energy
integration with water treatment; water-quality measurement/detection
including real-time pathogen and emerging-contaminant monitoring;
software/hardware for water distribution; and smart water systems. Full
scope framing in `references/editorial-framing.md`.

**Manuscript types & word limits** (the npj Series does NOT impose strict
word/page limits — "We do not impose strict limits on word count or page
numbers as the journals are online only and fully Open Access. However, we
strongly recommend that you write concisely" — the numbers below are the
journal's own recommended guidance, not hard portal-enforced caps except
where noted):
- Article — no stated main-text limit; abstract ≤150 words (no subheadings);
  references ≤60 (not strictly enforced); figure legends ≤350 words/figure.
  Structure: Title (≤15 words) / Abstract / Introduction (no subheadings) /
  Results (subheadings used) / Discussion (no subheadings, limitations, or
  conclusions sections permitted) / Methods (subheadings used) / Data
  availability / Code availability / Acknowledgments / Author contributions /
  Competing interests / References / Figure legends (placed after
  references). Systematic reviews, scoping reviews, and meta-analyses must
  be submitted as Articles, not Reviews.
- Brief Communication — main text 1,000–1,500 words (excludes abstract,
  methods, references, figure legends); abstract ≤70 words; references ~20
  (guide only).
- Comment — main text typically 1,000–2,000 words; abstract ≤70 words;
  references typically ≤25; flexible format for a broad, non-technical
  readership.
- Editorial — no stated main-text limit; abstract ≤70 words; written by the
  journal's own senior editorial team; unsolicited Editorials not considered.
- Matters Arising — main text ≤1,200 words; abstract ≤70 words; references
  typically ≤15; original article under discussion must be the first
  reference; usually paired with a Reply.
- Perspective — main text should not normally exceed 3,000 words; abstract
  ≤70 words; references ≤70 (not strictly enforced).
- Review — main text typically 3,000–4,000 words; abstract ≤70 words;
  references ≤60 (not strictly enforced); scope must not be dominated by a
  single lab, including the authors' own work.

**TOC / graphical abstract — RESOLVED, does not exist**: no mention of a
table-of-contents graphic, visual abstract, or graphical abstract appears
anywhere in Aims & Scope, Content types, Guide to Authors, or Submission
guidelines. `profile.yml`'s `toc_graphic.required` is explicitly set to
`false` (not left null) to record this as a checked-and-absent fact, per
this profile's authoring brief — the render gate keys directly on that
field.

**References**: "The npj Series journals use standard Nature referencing
style" (Submission guidelines, verbatim). Numbered sequentially by order of
first appearance in text/methods/tables/figure legends; footnotes not used;
more than five authors → first author only + "et al."; journal names
italicized and abbreviated with full stops; volume number (and following
comma) in bold; URLs cited parenthetically in text, not in the reference
list; datasets/patents/published conference abstracts may be included with
a DOI/accession code where available. → `assets/nature.csl` (official CSL
"Nature" style, numeric citation-format; its own documentation link points
to `nature.com/nature/for-authors/formatting-guide`, i.e. the general Nature
author-formatting guide that npj Clean Water's own Submission guidelines
page explicitly defers to).

**Methods**: reported entirely in the main manuscript file — "The journal
does not permit Supplementary Methods, all Methods should be reported in
the main manuscript file." Subdivided by short bold headings; authors
encouraged to include specific subsections for statistics, reagents, and
animal models; a statistics-and-reproducibility subsection is expected
(test name, n, comparisons, justification, alpha level, one- vs two-tailed,
exact P values). Section is named plain "Methods" (not "Materials and
Methods" or "Experimental Section").

**ORCID**: required for all corresponding authors of ACCEPTED papers, before
the final version is submitted (cannot be added/modified at proof stage).
Non-corresponding authors are encouraged but not required to link ORCID.

**Data / code availability**: a Data Availability Statement is mandatory in
every submitted manuscript, placed as its own "Data Availability" heading
after Methods and before References. A Code Availability statement is
required (under a "Code availability" heading) whenever custom code central
to the main claims was used.

**Reporting summary / editorial policy checklist**: research articles in
Life Sciences, Health Sciences, Earth and Environmental Sciences, or Social
and Behavioural Sciences must complete a Nature Portfolio Reporting Summary
(submitted with the revised manuscript after peer review; published as a
Supplementary File for primary research articles in Life/Health/Physical/
Applied Sciences or Society & the environment accepted from January 2019)
plus an Editorial Policy Checklist (received by Editors before peer review
begins; not sent to reviewers). Both are encouraged, though not mandatory,
at initial submission.

**Peer review / blinding**: single-anonymized by default — "referees are not
identified to the authors, except at the request of the referee" (npj Clean
Water's own Editorial process / Peer Review pages). Manuscripts typically go
to two or three reviewers; authors may suggest or exclude reviewers in the
cover letter.

**Formatting at initial submission**: NONE required — "Manuscripts submitted
to npj Clean Water do not need to adhere to our formatting requirements at
the point of initial submission; formatting requirements only apply at the
time of acceptance." A single combined PDF or Word file (text + figures) is
encouraged; LaTeX accepted only at acceptance stage (compiled PDF before
then).

**Figures**: at initial submission ("for peer review"), figures may be
embedded in text or grouped at the end, at ≥300 dpi and "clearly legible";
acceptable initial formats: .ai, .eps, .pdf, .ps, .psd, .jpeg, .tiff, .png,
.gif, .ppt, .pptx, .cdx. At acceptance ("for publication"): RGB color,
≥300 dpi; figure lettering in a sans-serif typeface (Arial or Helvetica),
optimum 8 pt at final print size; preferred vector formats .ai/.eps/.pdf/
.ps/.svg (layered .psd/.tif also accepted; bitmap .psd/.tif/.png/.jpg; .ppt
if fully editable; ChemDraw .cdx for chemical structures); avoid red/green
contrast and rainbow color scales; multi-panel figures on one page labeled
a), b), c); scale bars, not magnification factors; lines ≥1 pt. Figure
legends ≤350 words per figure, placed in the main manuscript file after the
reference list.

**Supporting/Supplementary Information**: submitted with the manuscript as
"a separate, single merged PDF" (preferred format; not edited/typeset by the
journal). Supplementary Methods are explicitly NOT permitted — all Methods
must be in the main manuscript. Oversized supplementary tables or
spreadsheets are provided as separate files labeled "Supplementary Data XX"
(not "Supplementary Table"), with title/legend still in the main SI PDF —
so the SI is not strictly 100%-PDF-only in every case. No SI cover sheet
(authors/title/page-figure-table counts) or internal SI table of contents
is mentioned anywhere in the fetched guidance.

**Open access / APC**: fully open access; articles freely and permanently
available online immediately on publication. APC: Original Research
£2,990.00 / $4,090.00 / €3,290.00; other peer-reviewed types (Brief
Communication, Perspective, Review, Comment) £1,175.00 / $1,695.00 /
€1,335.00. Automatic APC waivers/discounts for corresponding authors based
in the lowest-income countries; discretionary waivers considered
case-by-case for others — all waiver requests must be made AT THE POINT OF
SUBMISSION (requests during review or after acceptance are not considered).
Institutional open-access agreements may also cover costs.

**Submission portal**: https://submission.springernature.com/new-submission/41545/3
("Submit manuscript" link on the journal homepage).

**Overlap / preprints**: submission implies no significant overlap with
other papers under consideration/in press elsewhere (conference abstracts
excepted); preprint posting is explicitly supported/encouraged.

**AI policy (directly relevant to this manuscript's topic)**: LLMs "do not
currently satisfy our authorship criteria" — any LLM use must be documented
in the Methods section (or a suitable alternative section if no Methods
section exists); "AI assisted copy editing" (grammar/style/readability
polish of human-written text) does not need to be declared, but generative
content creation does. Generative AI-created images/video are not permitted
in figures except narrow, labeled exceptions. This governs LLM-as-authoring-
tool, not LLM-as-subject-of-study — a manuscript that *benchmarks* LLMs (as
this one does) is not itself constrained by this policy beyond normal
disclosure of any LLM used to help write the paper.

## TO VERIFY (not addressed in any fetched official page — check before submission)

- [ ] Double-anonymized peer review as an author-selectable OPTION for this
      specific journal — tried 2026-07-04: fetched and read npj Clean
      Water's own Editorial policies > Peer Review page in full; it carries
      the Nature-Portfolio-wide boilerplate "Some Nature-branded journals
      and Communications journals offer a double-anonymized peer review
      option. Please visit the journal website for information on the peer
      review options available" — this is circular (it IS the journal
      website) and the page's own 2015 rollout list of specific journals
      that gained the option does not include any npj-series title. Default
      stays `blinding: single` in `profile.yml`; the option itself is
      unconfirmed either way for npj Clean Water specifically.
- [ ] Line spacing (single vs double) at final/acceptance-stage formatting
      — tried 2026-07-04: fetched and read Submission guidelines' "Format
      of manuscripts" section in full; it states formatting requirements
      only apply at acceptance but never specifies spacing.
- [ ] Line numbers requirement — tried 2026-07-04: same section as above;
      no mention found.
- [ ] SI pagination convention (e.g. an "S1, S2…" prefix) — tried
      2026-07-04: fetched and read the Submission guidelines "Supplementary
      information" section in full; it covers single-merged-PDF handling
      and the "Supplementary Data XX" exception for oversized tables, but
      never states a page-numbering convention.
- [ ] SI internal table of contents requirement — tried 2026-07-04: same
      section; not addressed.
- [ ] SI cover sheet requirement — tried 2026-07-04: same section; not
      addressed (no analog to ACS's authors/title/counts cover sheet was
      found).
- [ ] Body font/point size for the manuscript file itself (distinct from
      the verified figure-lettering sans-serif rule, which only applies to
      text baked INTO figures) — tried 2026-07-04: fetched and read
      Submission guidelines "Format of manuscripts" section; no body font
      or point size is specified anywhere, consistent with "formatting
      requirements only apply at acceptance" and no acceptance-stage style
      template being publicly posted.
- [ ] Table border/rule style and caption position (above vs. below) —
      tried 2026-07-04: fetched and read the "Tables" subsection of
      Submission guidelines in full; it only says to place tables at the
      end of the text file and to describe error-analysis standards in the
      table legend for tables with statistics. No border/caption-position
      rule stated.
- Rule: each checked item moves UP into VERIFIED with a link, and its
  number lands in `profile.yml`; update `verified_date`.

## Editorial appetite for this manuscript's topic (LLM benchmark, a water-treatment application)

npj Clean Water has already published directly adjacent work: **"Towards
domain-adapted large language models for water and wastewater management:
methods, datasets and benchmarking"**, npj Clean Water **8**, 82 (2025)
(DOI: [10.1038/s41545-025-00509-8](https://doi.org/10.1038/s41545-025-00509-8),
published 2025-08-26) — an LLM/benchmarking-for-water-domain paper in this
exact journal, confirmed via Crossref metadata (title, volume 8, article
number 82, container-title "npj Clean Water"). This is strong precedent for
editorial appetite for LLM-benchmark-for-water-technology submissions;
expand the fit argument in `references/editorial-framing.md` and the cover
letter around it.

## Quarto/DOCX implementation notes for this journal

- `assets/reference.docx` is generated by `scripts/build_reference_docx.py`
  from a fresh `quarto pandoc --print-default-data-file reference.docx`,
  restyled to Times New Roman — 12pt body/headings, 10pt captions. No
  npj-Clean-Water-specific body font or point size requirement was found
  during verification (see TO VERIFY) — this is the same standard,
  portal-safe serif default used by `quarto-manuscript-est`, not a verified
  npj Clean Water rule. The VERIFIED sans-serif (Arial/Helvetica, 8pt)
  requirement applies only to lettering baked into figure images, not to
  the manuscript body text, so it is NOT applied to the reference doc.
  Re-run the builder script when requirements change; never hand-edit the
  `.docx`.
- No TOC-art logic applies to this profile: `toc_graphic.required: false`
  means `render.py`'s TOC-art gate and `insert_toc_art()` step are both
  skipped entirely for `--target submission`.
- Word count: since npj Clean Water sets no hard main-text limit for
  Articles (the primary type this manuscript will use), `validate.py`'s
  word-limit check against `manuscript_types[].word_limit: null` is
  effectively advisory only for Articles — it becomes a real hard gate only
  for Brief Communication/Comment/Matters Arising/Perspective/Review, whose
  `word_limit` values ARE verified numbers.
  `references/submission-checklist.md` paraphrases the same distinction for
  human review at S5.
- SI: `si.separate_file: true` and `si.pdf_only: false` (oversized
  tables/spreadsheets go out as separate "Supplementary Data XX" files) are
  wired for `render.py`/`validate.py`; `si.page_prefix` and
  `si.needs_cover_sheet` stay `null`/`false` pending the TO VERIFY items
  above — `postprocess_si` will not apply page-prefix renumbering or
  prepend a cover sheet for this profile until those are confirmed.

## Files in this profile

- `profile.yml` — machine-readable; ONLY verified numbers
- `scripts/build_reference_docx.py` — reproducible builder for the generated
  `assets/reference.docx`; re-run it when requirements change (never
  hand-edit the .docx)
- `assets/reference.docx` — generated by `scripts/build_reference_docx.py`;
  never hand-edit
- `assets/nature.csl` — fetched 2026-07-04 from the official CSL styles
  repository
  (https://raw.githubusercontent.com/citation-style-language/styles/master/nature.csl)
- `references/submission-checklist.md` — S5 gate list, HARD/SOFT
- `references/editorial-framing.md` — scope + cover-letter angle, incl. the
  LLM/benchmark precedent paper
