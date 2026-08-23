---
name: quarto-manuscript-microbiome
description: >
  Journal profile for Microbiome (BMC, Springer Nature, ISSN 2049-2618),
  consumed by quarto-manuscript-sci. Use whenever a manuscript targets
  Microbiome or the user mentions Microbiome journal, BMC microbiome
  submission, BMC IMRaD/Declarations manuscript format, or
  biomed-central.csl referencing style — for authoring, rendering,
  validation, submission packaging, or revision. NOT for npj Biofilms and
  Microbiomes (Nature Portfolio npj-series sibling, different structure and
  limits) or Environmental Microbiome (BMC's narrower-scope sibling
  journal); separate profiles.
compatibility: Consumed by quarto-manuscript-sci; not intended standalone.
---

# Journal Profile: Microbiome (BMC / Springer Nature)

Implements `references/journal-profile-contract.md` from `quarto-manuscript-sci`.
Facts below are split into **VERIFIED** (official BMC/Springer Nature pages
for this journal, fetched and read this session, 2026-07-04) and a **TO
VERIFY** queue (not addressed by any fetched page) — do NOT promote to
`profile.yml` until an official source is fetched and read.

Note on hosting: `microbiomejournal.biomedcentral.com` now 301-redirects to
`link.springer.com/journal/40168` — Microbiome's author-facing pages live on
the Springer Nature Link platform, not the legacy BMC domain. All sources
below are the current `link.springer.com/journal/40168/...` URLs.

## VERIFIED requirements (as of 2026-07-04)

Sources: [Journal homepage/info](https://link.springer.com/journal/40168) ·
[Aims and scope](https://link.springer.com/journal/40168/aims-and-scope) ·
[Submission guidelines](https://link.springer.com/journal/40168/submission-guidelines) ·
[Research article](https://link.springer.com/journal/40168/submission-guidelines/research-article) ·
[Methodology](https://link.springer.com/journal/40168/submission-guidelines/methodology) ·
[Brief report / Short report](https://link.springer.com/journal/40168/submission-guidelines/short-report) ·
[Software](https://link.springer.com/journal/40168/submission-guidelines/software-article) ·
[Review](https://link.springer.com/journal/40168/submission-guidelines/review) ·
[Comment](https://link.springer.com/journal/40168/submission-guidelines/commentary) ·
[Correspondence](https://link.springer.com/journal/40168/submission-guidelines/letter-to-the-editor) ·
[Meeting Report](https://link.springer.com/journal/40168/submission-guidelines/meeting-report) ·
[BMC-wide Editorial policies](https://link.springer.com/brands/bmc/editorial-policies)

**Publisher / journal**: BioMed Central (BMC), part of Springer Nature.
ISSN 2049-2618 (Electronic; no print edition found). Editor-in-Chief:
Jacques Ravel, PhD. 2025 Journal Impact Factor 14.9 (5-year JIF 18.5);
median submission-to-first-decision 24 days. Open access. Sister journals:
*Environmental Microbiome*, *Animal Microbiome*, *BMC Microbiology*
(manuscript transfer options exist between them, per Aims and scope).

**Scope** (verbatim/paraphrased from Aims and scope): studies of microbiomes
colonizing humans, animals, plants, or the environment — "both built and
natural or manipulated, as in agriculture" — including meta-omics
approaches, bioinformatics tools, and community/host interactions
emphasizing structure-function relationships. "Especially interested in
studies that go beyond descriptive omics surveys and include experimental
or theoretical approaches that mechanistically support proposed microbiome
functions." Explicitly does NOT consider "studies of individual microbial
isolates/species in vivo or in laboratory cultures without exploring the
mechanisms by which they affect the complex microbiome structures and
functions." Does not consider unsolicited Reviews. Full scope framing in
`references/editorial-framing.md`.

**Manuscript types** (8 total, each with its own guideline page; word
limits are ABSTRACT-only — no fetched type page states a main-text word
limit, which is silence rather than an explicit no-limit statement, unlike
npj Clean Water's explicit "we do not impose strict limits"):
- **Research** — the flagship original-research type. BMC IMRaD structure:
  Title page / Abstract / Keywords / Background / Methods / Results /
  Discussion / Conclusions / List of abbreviations / Declarations /
  References / Figures, tables, additional files. Abstract <=350 words,
  structured Background/Results/Conclusions, no abbreviations, no
  references cited in the abstract. Keywords: 3-10. Methods must state "the
  aim, design and setting of the study; the characteristics of participants
  or description of materials; a clear description of all processes,
  interventions and comparisons; the type of statistical analysis used,
  including a power calculation if appropriate." Microbiome-specific: "we
  expect that studies submitted to Microbiome include sampling controls,
  extraction controls, PCR amplification controls as negative controls, but
  also positive controls (mock communities or others)"; metadata formatted
  to MIxS (Minimum Information about any (x) Sequence, Genome Standards
  Consortium) standards; "all original sequences MUST to be deposited in a
  public repository," publicly available at time of publication.
- **Methodology** — same IMRaD/Declarations shape and abstract rule as
  Research; for new methods/procedures.
- **Brief report** (Short report) — "suitable for the presentation of
  research that extends previously published research, including the
  reporting of additional controls and confirmatory results in other
  settings, as well as negative results, small-scale clinical studies,
  clinical audits and case series." Same IMRaD shape/abstract rule.
- **Software** — "should describe a tool likely to be of broad utility that
  represents a significant advance over previously published software"
  (usually with direct comparison). Same IMRaD shape/abstract rule.
- **Review** — unsolicited Reviews NOT accepted: "Reviews published in the
  journal are specially invited by the Editors of Microbiome"; authors
  expected to be "leading experts in the field with a track record of
  publication in that specific field." Structure: Title page / Abstract /
  Keywords / Main text (may include subsections) / Conclusions / List of
  abbreviations / Declarations / References / Figures, tables, additional
  files. Abstract <=350 words, unstructured beyond the no-abbreviations/
  no-references rule.
- **Comment** — "short, narrowly focused articles" that are "usually
  commissioned by the journal" and "are not mini-reviews." Structure: Title
  page / Abstract / Keywords / Background / Main text / Conclusions / List
  of abbreviations / Declarations / References / Figures, tables,
  additional files. Abstract <=350 words, structured as background/main
  body/short conclusion.
- **Correspondence** — "may be edited for clarity or length and may be
  subject to peer review at the editors' discretion." No fixed abstract
  structure beyond "briefly summarize the aim, findings or purpose of the
  article"; no numeric abstract word cap found (see TO VERIFY). Structure:
  Title page / Abstract / Keywords / Main text / List of abbreviations /
  Declarations / References / Figures, tables, additional files.
- **Meeting Report** — "usually commissioned"; should "focus on new
  research discoveries and the application of this knowledge" rather than
  comprehensive coverage of a meeting. Abstract <=250 words (the one type
  with a DIFFERENT abstract cap than the 350-word default). Structure:
  Title page / Abstract / Keywords / Main text (may contain subsections) /
  List of abbreviations / Declarations / References / Figures, tables,
  supplementary files.

**Declarations block (mandatory for every manuscript type)** — verbatim
from the Research article page, 7 mandatory subsections plus 1 optional:
Ethics approval and consent to participate; Consent for publication;
Availability of data and materials; Competing interests; Funding; Authors'
contributions; Acknowledgements; Authors' information (optional). "If any
of the sections are not relevant to your manuscript, please include the
heading and write 'Not applicable.'" This directly matches the task brief's
"BMC mandates these" expectation.

**TOC / graphical abstract — RESOLVED, does not exist**: no mention of a
table-of-contents graphic, visual abstract, or graphical abstract appears
anywhere in Aims and scope, the Submission guidelines index page, or any of
the 8 manuscript-type pages — all fetched and read in full 2026-07-04.
`profile.yml`'s `toc_graphic.required` is explicitly set to `false` (not
left null) to record this as a checked-and-absent fact, per this profile's
authoring brief — the render gate depends on it.

**References**: numbered consecutively in square brackets, in the order
first cited in the text ("BioMed Central format," per the Research article
page's own worked examples for journal articles, books, online documents,
and DOI-bearing datasets). "Only articles, clinical trial registration
records and abstracts that have been published or are in press... may be
cited." Journal abbreviations follow Index Medicus/MEDLINE. →
`assets/biomed-central.csl` (official CSL "BioMed Central" style,
numeric/square-bracket citation format; its own `<info>` block's
documentation link points to a BMC-family journal's own "research-article"
submission-guidelines page — the same house style this journal's own
Research article page describes).

**Peer review**: single-anonymous, verbatim from the Submission guidelines
page: "Single-anonymous peer review system, where the reviewers are aware
of the names and affiliations of the authors, but the reviewer reports
provided to authors are anonymous." BMC as a publisher offers open,
transparent, and closed/single-anonymous peer review models across its
portfolio (BMC-wide Editorial policies page), but Microbiome's own page
states single-anonymous specifically, not an author-selectable option.

**Formatting**: "Double-line spacing, line and page numbering required; no
page breaks." Accepted file formats: Microsoft Word (DOC, DOCX), Rich Text
Format (RTF), or TeX/LaTeX. No body font/point-size requirement found (see
TO VERIFY).

**Figures**: individual files <=10 MB; ~300 dpi at final size; width 85 mm
(half page) or 170 mm (full page), max height 225 mm; lines >0.25 pt;
numbered in order of first mention and uploaded in that order; figure
titles (<=15 words) and legends (<=300 words) live in the manuscript text,
not the graphic file; figure keys baked into the graphic, not the legend;
multi-panel figures submitted as one composite file; closely cropped;
correct orientation.

**Tables**: numbered with Arabic numerals, cited in sequence (Table 1,
Table 2, ...); title (<=15 words) above, legend (<=300 words) below; must
use Word's native "Table object" function, not an embedded image or
spreadsheet; no color/shading; no commas for numerical values; tables under
one A4/Letter page may sit inline, larger ones go out as additional files.

**Additional files (BMC's SI equivalent)**: named sequentially "Additional
file 1," "Additional file 2," etc., each cited in the main text; multiple
formats accepted (Excel .xls, .csv, PDF, .txt, .pptx, and others) — NOT a
single-merged-PDF convention (this differs from the Nature-family npj Clean
Water / Nature Water profiles' single-combined-PDF rule); max 20 MB per
file; do not include patient consent forms, language-editing certificates,
or tracked-change manuscripts as additional files — send those by email to
the editorial address instead. No SI cover sheet or internal table of
contents was found anywhere in the fetched guidance.

**Data / ethics / consent** (BMC-wide Editorial policies, which Microbiome
follows): research on humans "must have been approved by an appropriate
ethics committee," with a statement naming the committee and reference
number; informed consent required from participants (or parent/guardian for
children under 16). "Submission of a manuscript to a BMC journal implies
that materials described in the manuscript, including all relevant raw
data, will be freely available to any scientist wishing to use them for
non-commercial purposes." Authorship requires substantial contribution to
conception/design OR acquisition/analysis/interpretation of data, approval
of the submitted version, and accountability for one's own contributions.

**Open access / APC**: fully open access; CC BY or CC BY-NC-ND license.
Article Processing Charge: £3,590.00 GBP / $5,190.00 USD / €4,290.00 EUR
(Submission guidelines page).

**Submission portal**: https://submission.springernature.com/new-submission/40168/3
("Submit your manuscript" link on the journal's own Submission guidelines
page). Authors track progress via "Your research" in their Springer Nature
account.

**LLM/authorship policy**: "Large Language Models (LLMs), such as ChatGPT,
do not currently satisfy our authorship criteria" (Research article page,
title-page section).

## TO VERIFY (not addressed in any fetched official page — check before submission)

- [ ] ORCID requirement for the corresponding/any author — tried
      2026-07-04: fetched and read both the Research article page in full
      (ORCID not mentioned anywhere in its content) and the full Submission
      guidelines page (ORCID mentioned ONLY in the context of suggesting
      peer reviewers: "provide an ORCID or Scopus ID"). No author-facing
      ORCID mandate was found in either page. Contract schema has no
      dedicated `orcid` field; this is documented here rather than in
      `profile.yml`. Do not assume ORCID is required OR that it is
      optional for authors — re-check the live submission system (Editorial
      Manager/Snapp) at time of use, since manuscript-tracking-system-level
      requirements are not always mirrored on the public guidelines pages.
- [ ] Correspondence abstract numeric word cap — tried 2026-07-04: fetched
      and read the Correspondence (letter-to-the-editor) page in full; it
      states only "The abstract should briefly summarize the aim, findings
      or purpose of the article," with no numeric limit, unlike every other
      type (350 or 250 words).
- [ ] Body font / point size — tried 2026-07-04: fetched and read the full
      Submission guidelines page; it specifies double-line spacing, line
      and page numbering, and accepted file formats (DOC/DOCX/RTF/TeX), but
      never a font family or point size.
- [ ] SI/"Additional files" internal pagination convention (e.g., an
      "S1, S2..." prefix within a file) — tried 2026-07-04: fetched and read
      the additional-files-related content on the Submission guidelines
      page in full; only the file-naming convention ("Additional file 1,"
      "Additional file 2," ...) was found, not an internal page-numbering
      scheme.
- [ ] SI internal table of contents requirement — tried 2026-07-04: same
      section; not addressed.
- [ ] SI cover sheet requirement — tried 2026-07-04: same section; not
      addressed (no analog to ACS's authors/title/counts cover sheet found).
- [ ] Preprint posting policy — tried 2026-07-04: fetched and read the full
      Submission guidelines page; preprints are not mentioned anywhere in
      the fetched content.
- [ ] Table border/rule style beyond "no color or shading" — tried
      2026-07-04: fetched and read the general figures/tables formatting
      content on the Submission guidelines page in full; no border-style
      rule beyond the no-color/no-shading statement was found.
- [ ] Whether double-anonymized or open peer review is available as an
      author-selectable option specifically for Microbiome (BMC as a
      publisher runs open/transparent/closed models across its journals,
      per the BMC-wide Editorial policies page) — tried 2026-07-04: fetched
      and read Microbiome's own Submission guidelines page in full; it
      states single-anonymous only, with no mention of an opt-in
      alternative for this specific title.
- Rule: each checked item moves UP into VERIFIED with a link, and its
  value lands in `profile.yml`; update `verified_date`.

## Quarto/DOCX implementation notes for this journal

- `assets/reference.docx` is generated by `scripts/build_reference_docx.py`
  from a fresh `quarto pandoc --print-default-data-file reference.docx`,
  restyled to Times New Roman — 12pt body/headings, 10pt captions. No
  Microbiome-specific body font or point size requirement was found during
  verification (see TO VERIFY) — this uses the same standard, portal-safe
  serif default as `quarto-manuscript-est`/`quarto-manuscript-npjcw`/
  `quarto-manuscript-natwater`. Re-run the builder script when requirements
  change; never hand-edit the `.docx`.
- No TOC-art logic applies to this profile: `toc_graphic.required: false`
  means `render.py`'s TOC-art gate and `insert_toc_art()` step are both
  skipped entirely for `--target submission`.
- Word count: every manuscript type in this profile has `word_limit: null`
  for the main text — `validate.py`'s word-limit check is advisory-only
  for all 8 types (unlike Nature Water, where every type carries a real
  numeric cap). Only the ABSTRACT word caps (350 words for 6 of 8 types,
  250 for Meeting Report, unstated for Correspondence) are real numbers;
  these live in `manuscript_types[].abstract_rule`, which `validate.py`
  does not currently gate on (same limitation noted in the sibling
  profiles) — flag abstract length at S5 by human/agent judgment until
  that check is wired up.
- Declarations: `section_headings` lists a single "Declarations" heading;
  its 7 mandatory + 1 optional subsections (Ethics approval and consent to
  participate / Consent for publication / Availability of data and
  materials / Competing interests / Funding / Authors' contributions /
  Acknowledgements / Authors' information) are documented here in prose,
  not as a `profile.yml` schema key — any consumer building a Declarations
  section for this journal should include exactly these subsections, each
  present even when "Not applicable."
- SI: `si.separate_file: true` and `si.pdf_only: false` (BMC accepts
  multiple additional-file formats, NOT a single-merged-PDF convention —
  the opposite default from the Nature-family profiles in this library) are
  wired for `render.py`/`validate.py`; `si.page_prefix` and
  `si.needs_own_toc` stay `null` pending the TO VERIFY items above.
- `figures.placement: end` is INFERRED from the official section-order list
  itself (Figures/tables/additional files is the last section in the
  single submitted manuscript file), not from an explicit "place figures at
  the end" instruction — flag this inference at S5 rather than treating it
  as equivalent in strength to a verbatim quote.

## Files in this profile

- `profile.yml` — machine-readable; ONLY verified numbers
- `scripts/build_reference_docx.py` — reproducible builder for the generated
  `assets/reference.docx`; re-run it when requirements change (never
  hand-edit the .docx)
- `assets/reference.docx` — generated by `scripts/build_reference_docx.py`;
  never hand-edit
- `assets/biomed-central.csl` — fetched 2026-07-04 from the official CSL
  styles repository
  (https://raw.githubusercontent.com/citation-style-language/styles/master/biomed-central.csl)
- `references/submission-checklist.md` — S5 gate list, HARD/SOFT
- `references/editorial-framing.md` — journal's actual scope, generic
  fit guidance for any prospective author (not tailored to any one
  manuscript)
