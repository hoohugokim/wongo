---
name: quarto-manuscript-npjbiofilms
description: >
  Journal profile for npj Biofilms and Microbiomes (Nature Portfolio,
  Springer Nature), consumed by quarto-manuscript-sci. Use whenever a
  manuscript targets npj Biofilms and Microbiomes or the user mentions npj
  Biofilms and Microbiomes, a Nature Portfolio biofilm/microbiome journal, or
  Springer Nature submission for biofilm biology, microbiome, or host-microbe
  research — for authoring, rendering, validation, submission packaging, or
  revision. NOT for BMC's "Microbiome" journal or Springer's "Environmental
  Microbiome" (different publishers/portfolios, separate profiles).
compatibility: Consumed by quarto-manuscript-sci; not intended standalone.
---

# Journal Profile: npj Biofilms and Microbiomes (Nature Portfolio / Springer Nature)

Implements `references/journal-profile-contract.md` from `quarto-manuscript-sci`.
Facts below are split into **VERIFIED** (official nature.com/npjbiofilms
pages, fetched and read this session) and a **TO VERIFY** queue (not
addressed by any fetched page) — do NOT promote to `profile.yml` until an
official source is fetched and read. Where a rule is shared with the
npj-Series sibling profile `quarto-manuscript-npjcw` (npj Clean Water), that
is called out explicitly; every such rule was independently re-confirmed on
npj Biofilms and Microbiomes' own pages this session, not blind-copied.

## VERIFIED requirements (as of 2026-07-04)

Sources: [Journal homepage](https://www.nature.com/npjbiofilms/) ·
[Aims & Scope](https://www.nature.com/npjbiofilms/aims) ·
[Content types](https://www.nature.com/npjbiofilms/content-types) ·
[For Authors and Referees](https://www.nature.com/npjbiofilms/for-authors-and-referees) ·
[Guide to Authors](https://www.nature.com/npjbiofilms/for-authors-and-referees/guide-to-authors) ·
[Submission guidelines](https://www.nature.com/npjbiofilms/for-authors-and-referees/submission-guidelines) ·
[Editorial process](https://www.nature.com/npjbiofilms/for-authors-and-referees/editorial-process) ·
[Matters Arising](https://www.nature.com/npjbiofilms/for-authors-and-referees/matters-arising) ·
[Editorial policies](https://www.nature.com/npjbiofilms/editorial-policies) ·
[Editorial policies > Peer Review](https://www.nature.com/npjbiofilms/editorial-policies/peer-review) ·
[Editorial policies > Artificial Intelligence (AI)](https://www.nature.com/npjbiofilms/editorial-policies/ai) ·
[Editorial policies > Reporting standards](https://www.nature.com/npjbiofilms/editorial-policies/reporting-standards) ·
[Article Processing Charges](https://www.nature.com/npjbiofilms/apc)

**Publisher / journal**: Springer Nature Limited (Nature Portfolio),
published in partnership with Nanyang Technological University Singapore and
the Singapore Centre for Environmental Life Sciences Engineering (SCELSE).
ISSN 2055-5008 (online only; fully Open Access, part of the npj Series) —
**journal-specific**: different partner institutions and ISSN from npj Clean
Water (KFUPM, ISSN 2059-7037).

**Scope** (paraphrased from Aims & Scope, which itself is not fully quotable
verbatim from the fetch but was read in full): the journal examines "the
biology, ecology, and communal function of biofilms, microbial populations,
and communities, as well as derived applications across the medical,
environmental, and engineering sciences." Topics include microbiology
fundamentals (genetics, evolution, environmental effects, dynamics); biofilm
formation, prevention, detection, and removal (mechanical/chemical/
therapeutic); biofilm control and engineering applications; host-microbiome
relationships in animals, plants, health and disease; environmental
microbiomes including extreme-environment communities; microbiome
engineering; and bioinformatics tools/methods. **Journal-specific** — this
scope (biofilm biology + microbiome/host-microbe science) is substantively
different from npj Clean Water's water-treatment/desalination scope; only
the npj-Series publishing-model boilerplate ("fully open-access and more
inclusive platform... global partnerships with the research community and
other Springer Nature journals") is shared wording. Full scope framing in
`references/editorial-framing.md`.

**Manuscript types & word limits** (**npj-Series-wide** rule, re-confirmed
on this journal's own Content types page: "We do not impose strict limits on
word count or page numbers... However, we strongly recommend that you write
concisely" is the general npj Series framing; the specific numbers below are
this journal's own Content types table):
- Article — no stated main-text limit; "Articles should report substantial
  original primary research"; systematic reviews, scoping reviews, and
  meta-analyses must be submitted as Articles, not Reviews (verbatim,
  journal-specific confirmation of an npj-Series-wide pattern); abstract
  ≤150 words (no subheadings); references ≤60 (not strictly enforced);
  figure legends ≤350 words/figure. Structure: Title page / Abstract /
  Introduction / Results / Discussion / Methods / Data availability / Code
  availability / Acknowledgments / Author contributions / Competing
  Interests / References / Figure legends (Figure legends confirmed as its
  own final section, placed after References).
- Brief Communication — main text 1,000–1,500 words (excludes abstract,
  methods, references, figure legends); abstract ≤70 words; references ~20
  (guide only).
- Comment — main text typically 1,000–2,000 words; abstract ≤70 words;
  references typically ≤25.
- Editorial — no stated main-text limit; abstract ≤70 words; references ≤60
  (not strictly enforced — **journal-specific**: this numeric reference cap
  for Editorials was found on npj Biofilms and Microbiomes' own page and was
  NOT part of npj Clean Water's verified set); "typically written by the
  senior editorial team of the journal, under the direction of the
  Editor-in-Chief. Unsolicited Editorials will not be considered."
  (npj-Series-wide wording pattern, re-confirmed here).
- Matters Arising — main text ideally ≤1,200 words; opening paragraph
  functions as the abstract, written for non-specialist readers; references
  typically ≤15; "should ideally have been sent to the authors of the paper
  under discussion before submission" (2-week wait if no response); only
  considered for papers published in this journal itself.
- **Meeting Report — journal-specific type, NOT present in npj Clean
  Water's verified type list.** Up to 3,000 words; typically commissioned by
  the Editors; "should include a substantive discussion and clear outputs
  from a scientific meeting or workshop that will be of broad interest";
  peer reviewed; abstract ≤70 words; references ≤70 (not strictly
  enforced). Shares the lower APC tier with Brief Communication/Perspective/
  Review/Comment.
- Perspective — main text should not normally exceed 3,000 words; abstract
  ≤70 words; references ≤70 (not strictly enforced).
- Review — main text typically 3,000–4,000 words; "narratively summarize
  recent advances in the scientific literature within a given research
  field"; scope must be broad enough not to be dominated by the work of a
  single laboratory, particularly not the authors' own work (verbatim,
  npj-Series-wide wording pattern, re-confirmed here); abstract ≤70 words;
  references ≤60 (not strictly enforced).

**TOC / graphical abstract — RESOLVED, does not exist**: no mention of a
table-of-contents graphic, visual abstract, or graphical abstract appears
anywhere in Aims & Scope, Content types, or Submission guidelines; the
Submission guidelines page's own "NOT MENTIONED" summary explicitly names
"Graphical abstract", "Table of contents", and "Visual summary" as absent
from the fetched guidance. `profile.yml`'s `toc_graphic.required` is
explicitly set to `false` (not left null) to record this as a
checked-and-absent fact, per this profile's authoring brief — the render
gate keys directly on that field. **npj-Series-wide finding**, re-confirmed
independently on this journal's own pages (same result as npj Clean Water
and Nature Water).

**References**: "The npj Series journals use standard Nature referencing
style" (Submission guidelines, verbatim — **npj-Series-wide**, re-confirmed
on this journal's own page). Numbered sequentially by order of first
appearance in text/methods/tables/figure legends; more than five authors →
first author only + "et al."; journal names italicized and abbreviated with
full stops; volume number in bold. Example given: "Schott, D. H., Collins,
R. N. & Bretscher, A. Secretory vesicle transport velocity in living cells
depends on the myosin V lever arm length. _J. Cell Biol._ **156**, 35-39
(2002)." → `assets/nature.csl` (official CSL "Nature" style, numeric
citation-format; byte-identical to the copy independently verified for npj
Clean Water and Nature Water; its own documentation link points to
`nature.com/nature/for-authors/formatting-guide`, the general Nature
author-formatting guide this journal's Submission guidelines page defers
to).

**Methods**: "The journal does not permit Supplementary Methods, all
Methods should be reported in the main manuscript file" (verbatim,
**npj-Series-wide** rule shared with npj Clean Water, re-confirmed on this
journal's own Submission guidelines page). Must include adequate
experimental/characterization detail for reproduction, commercial supplier
and kit sources identified, safety hazards flagged; subdivided by short bold
headings; a statistics subsection is required stating test name, n,
comparisons, justification, alpha level, one- vs two-tailed designation, and
exact P values (not merely "significant" or "P < 0.05"). Data-plotting rule:
bar charts must overlay individual data points or be converted to
dot-plots/box-and-whisker plots to show the full data distribution.

**ORCID**: required for all corresponding authors of ACCEPTED papers, before
the final version is submitted ("it is not possible to add/modify ORCID
details at proof stage"). Non-corresponding authors are encouraged but not
required.

**Data / code availability**: a Data Availability Statement is mandatory,
placed as its own "Data Availability" heading after Methods and before
References; "we request that authors avoid 'data not shown' statements and
instead make their data available via deposition in a public repository." A
Code Availability statement (under "Code availability") is required
whenever custom code central to the main claims was used.

**Reporting summary / reporting standards**: a Nature Portfolio Reporting
Summary is mandatory (verbatim, npj Biofilms and Microbiomes' own Reporting
standards page) for research articles in "the life sciences, behavioural &
social sciences and ecology, evolution & environmental sciences," and for
select physical-sciences areas (solar cells, lasing claims); the completed
summary "will be made available to editors and reviewers during manuscript
assessment" and "will be published with all accepted manuscripts." The
Guide to Authors page separately mentions authors are "encouraged to
include completed reporting summaries and editorial policy checklists at
the time of submission" — this is the only mention of an "editorial policy
checklist" found for this journal; unlike npj Clean Water's SKILL.md, no
page fetched this session states the checklist is mandatory-but-not-sent-
to-reviewers, only that it is encouraged at submission alongside the
reporting summary. Mandatory reporting-guideline checklists for specific
study types: CONSORT (randomized controlled trials), PRISMA or appropriate
extension (systematic reviews/meta-analyses) — required before peer review.
STROBE/CARE/COREQ/SRQR/STARD/TRIPOD/CHEERS/ARRIVE strongly recommended per
EQUATOR Network guidance for their respective study types.

**Peer review / blinding**: single-anonymized by default — "The npj Series
operate a 'single-anonymized peer review process.' In line with policy,
referees are not identified to the authors, except at the request of the
referee" (Editorial process page, **npj-Series-wide** wording, re-confirmed
on this journal's own page). Manuscripts typically go to two or three
reviewers; ideally no more than two resubmission rounds; authors may
transfer a declined manuscript to another Nature Portfolio journal via an
automated transfer service (with consent, including prior reviewer
reports).

**Formatting at initial submission**: NONE required — "Manuscripts
submitted to npj Biofilms and Microbiomes do not need to adhere to our
formatting requirements at the point of initial submission; formatting
requirements only apply at the time of acceptance" (**npj-Series-wide**
wording, re-confirmed on this journal's own page). A single combined PDF or
Word file (text + figures) is encouraged; LaTeX accepted only as a compiled
PDF at initial submission.

**Figures**: at initial submission, figures incorporated into the main
article file at sufficient quality to be clearly legible, or submitted
separately / via a private repository link if impractical. At acceptance:
each complete multi-panel figure as ONE image file (not individual panels
uploaded separately), RGB color, ≥300 dpi, sans-serif typeface (Arial or
Helvetica) for all figure lettering and symbol font for Greek letters,
optimum 8pt at final print size, lines ≥1pt; preferred vector formats
.ai/.eps/.pdf/.ps/.svg (layered .psd/.tif also accepted; bitmap .psd/.tif/
.png/.jpg; .ppt if fully editable; ChemDraw .cdx for chemical structures);
avoid red/green contrast and rainbow pseudo-color, recolor for colorblind
accessibility; multi-panel figures on one page labeled lower-case bold a),
b), c); scale bars, not magnification factors; verbal cues in legends
("open red triangles") rather than visual symbols. Figure legends ≤350
words/figure, placed in the main manuscript file after the reference list.
Video files accepted as figures (many formats, e.g. mp4/mov/avi), ≤150MB
per file, ≤1GB combined, first frame used as the static PDF image — this
video-as-figure detail was not part of npj Clean Water's verified set.

**Supporting/Supplementary Information**: "All supplementary information
cited in the manuscript should be provided in a separate, single merged
PDF" (**npj-Series-wide** wording, re-confirmed here). Supplementary
Methods explicitly NOT permitted. Oversized supplementary tables too large
for a PDF page are provided as separate "Supplementary Data XX" files (not
"Supplementary Table"), with title/legend kept in the main SI PDF. The
journal does not edit SI files — "they will be uploaded with the published
article as they are submitted" and "any tracked changes should be removed
from the file" before submission. No SI cover sheet or internal table of
contents is mentioned anywhere in the fetched guidance.

**Open access / APC**: fully open access. APC (**journal-specific — higher
than npj Clean Water**): Original Research £3,190.00 / $4,390.00 /
€3,890.00; Brief Communication/Perspective/Review/Comment/Meeting Report
£1,490.00 / $2,120.00 / €1,795.00 (npj Clean Water: £2,990/£1,175 tiers —
different amounts, confirming APC is NOT a shared npj-Series-wide constant
and must be re-checked per journal). Automatic waivers for corresponding
authors in the lowest-income countries per Springer Nature's policy list;
discretionary waivers case-by-case; all waiver requests must be made AT THE
POINT OF SUBMISSION (requests during review or after acceptance are not
considered).

**Submission portal**: https://submission.springernature.com/new-submission/41522/3
("Submit manuscript" link on the journal homepage) — different portal ID
from npj Clean Water's 41545.

**Overlap / preprints**: submission implies no significant overlap with
other papers under consideration/in press elsewhere (conference abstracts
excepted); related manuscripts submitted elsewhere must be disclosed.

**AI policy**: LLMs "do not currently satisfy our authorship criteria" —
any LLM use must be documented in the Methods section; "AI assisted copy
editing" (grammar/style/readability polish) does not need to be declared,
but generative content creation does; "there must be human accountability
for the final version of the text." Generative AI images in figures are
generally prohibited except three narrow, individually labeled exceptions
(contracted-agency images, AI-generated images that are themselves the
subject of an article about AI, and tools using attributable/verifiable
scientific data). Peer reviewers must not upload manuscripts into
generative AI tools and must declare any AI support used in their review.
This is **npj-Series-wide** wording, re-confirmed verbatim-identical to npj
Clean Water's AI policy on this journal's own page.

## TO VERIFY (not addressed in any fetched official page — check before submission)

- [ ] Double-anonymized peer review as an author-selectable OPTION for this
      specific journal — tried 2026-07-04: fetched and read the
      Nature-Portfolio-wide Peer Review policy page that npj Biofilms and
      Microbiomes' own Editorial Policies page links to, in full; it lists
      19 journals offering transparent peer review and a separate 2015
      rollout list of journals that gained a double-anonymized option —
      npj Biofilms and Microbiomes appears in neither list. Default stays
      `blinding: single` in `profile.yml`; the option itself is unconfirmed
      either way for this journal specifically (same unresolved status as
      npj Clean Water).
- [ ] Line spacing (single vs double) at final/acceptance-stage formatting
      — tried 2026-07-04: fetched and read Submission guidelines in full;
      its own "NOT MENTIONED" summary explicitly names "Line spacing" as
      absent from the fetched guidance.
- [ ] Line numbers requirement — tried 2026-07-04: same page; its "NOT
      MENTIONED" summary explicitly names "Line numbers" as absent.
- [ ] SI pagination convention (e.g. an "S1, S2…" prefix) — tried
      2026-07-04: fetched and read the Submission guidelines Supplementary
      Information section in full; covers single-merged-PDF handling and
      the "Supplementary Data XX" exception, but never states a
      page-numbering convention.
- [ ] SI internal table of contents requirement — tried 2026-07-04: same
      section; not addressed.
- [ ] SI cover sheet requirement — tried 2026-07-04: same section; not
      addressed (no analog to ACS's authors/title/counts cover sheet
      found).
- [ ] Body font/point size for the manuscript file itself (distinct from
      the verified figure-lettering sans-serif rule, which only applies to
      text baked INTO figures) — tried 2026-07-04: fetched and read
      Submission guidelines in full; its own "NOT MENTIONED" summary
      explicitly names "Font size for main text" and "Title page
      format/requirements" as absent.
- [ ] Table border/rule style and caption position (above vs. below) —
      tried 2026-07-04: fetched and read the "Tables" subsection of
      Submission guidelines in full; it only says to place tables at the
      end of the text file and to describe error-analysis standards in the
      table legend for tables with statistics. No border/caption-position
      rule stated.
- [ ] Editorial Policy Checklist — is it actually mandatory (as npj Clean
      Water's SKILL.md describes for that journal) or only "encouraged" as
      the Guide to Authors page's wording suggests for this journal — tried
      2026-07-04: fetched and read Guide to Authors and Reporting standards
      in full; only "encouraged... at the time of submission" language was
      found for this journal; no page confirmed it as a hard, editors-only,
      pre-review-mandatory gate the way npj Clean Water's profile describes.
      Do not assume the two journals match on this point without a fresh
      check.
- Rule: each checked item moves UP into VERIFIED with a link, and its
  number lands in `profile.yml`; update `verified_date`.

## Editorial appetite / precedent search

No manuscript-specific precedent-paper search was performed for this
profile (unlike npj Clean Water's SKILL.md, which cites a specific
LLM-benchmark precedent paper relevant to that manuscript's topic) — this
profile was built as a general-purpose journal profile, not tailored to a
specific in-flight manuscript. See `references/editorial-framing.md` for
the generic scope-fit description any prospective author can use.

## Quarto/DOCX implementation notes for this journal

- `assets/reference.docx` is generated by `scripts/build_reference_docx.py`
  from a fresh `quarto pandoc --print-default-data-file reference.docx`,
  restyled to Times New Roman — 12pt body/headings, 10pt captions. No
  npj-Biofilms-and-Microbiomes-specific body font or point size requirement
  was found during verification (see TO VERIFY) — this is the same
  standard, portal-safe serif default used by `quarto-manuscript-npjcw` and
  `quarto-manuscript-est`, not a verified journal rule. The VERIFIED
  sans-serif (Arial/Helvetica, 8pt) requirement applies only to lettering
  baked into figure images, not to the manuscript body text, so it is NOT
  applied to the reference doc. Re-run the builder script when requirements
  change; never hand-edit the `.docx`.
- No TOC-art logic applies to this profile: `toc_graphic.required: false`
  means `render.py`'s TOC-art gate and `insert_toc_art()` step are both
  skipped entirely for `--target submission`.
- Word count: since npj Biofilms and Microbiomes sets no hard main-text
  limit for Articles or Editorials (the two open-ended types),
  `validate.py`'s word-limit check against `manuscript_types[].word_limit:
  null` is effectively advisory only for those two types — it becomes a
  real hard gate for Brief Communication/Comment/Matters Arising/Meeting
  Report/Perspective/Review, whose `word_limit` values ARE verified
  numbers. `references/submission-checklist.md` paraphrases the same
  distinction for human review at S5.
- SI: `si.separate_file: true` and `si.pdf_only: false` (oversized tables
  go out as separate "Supplementary Data XX" files) are wired for
  `render.py`/`validate.py`; `si.page_prefix` and `si.needs_own_toc` stay
  `null` pending the TO VERIFY items above — `postprocess_si` will not
  apply page-prefix renumbering or generate an internal SI table of
  contents for this profile until those are confirmed.
- `manuscript_types` includes a `meeting-report` entry not present in
  `quarto-manuscript-npjcw`'s profile — `render.py`/`validate.py` callers
  should not assume the two npj-Series profiles' `manuscript_types` lists
  are interchangeable.

## Files in this profile

- `profile.yml` — machine-readable; ONLY verified numbers
- `scripts/build_reference_docx.py` — reproducible builder for the
  generated `assets/reference.docx`; re-run it when requirements change
  (never hand-edit the .docx)
- `assets/reference.docx` — generated by `scripts/build_reference_docx.py`;
  never hand-edit
- `assets/nature.csl` — fetched 2026-07-04 from the official CSL styles
  repository
  (https://raw.githubusercontent.com/citation-style-language/styles/master/nature.csl);
  confirmed byte-identical to the copies independently verified for
  `quarto-manuscript-npjcw` and `quarto-manuscript-natwater`
- `references/submission-checklist.md` — S5 gate list, HARD/SOFT
- `references/editorial-framing.md` — generic scope + fit description for
  any prospective author (not tailored to a specific manuscript)
