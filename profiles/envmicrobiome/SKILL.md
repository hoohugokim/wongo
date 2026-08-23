---
name: quarto-manuscript-envmicrobiome
description: >
  Journal profile for Environmental Microbiome (BMC, Springer Nature, ISSN
  2524-6372), consumed by quarto-manuscript-sci. Use whenever a manuscript
  targets Environmental Microbiome or the user mentions Environmental
  Microbiome, BMC environmental-microbiology submission, BMC
  IMRaD/Declarations format, or biomed-central.csl referencing for
  environmental/applied microbiome research (air, soil, aquatic microbial
  ecology, bioremediation, built-environment microbiome, geomicrobiology,
  plant/crop microbiome interactions, extreme-environment
  microbiology/astrobiology) — for authoring, rendering, validation,
  submission packaging, or revision. NOT for BMC's "Microbiome" (ISSN
  2049-2618, broader sibling) or npj Biofilms and Microbiomes (ISSN
  2055-5008, Nature Portfolio sibling); separate profiles.
compatibility: Consumed by quarto-manuscript-sci; not intended standalone.
---

# Journal Profile: Environmental Microbiome (BMC / Springer Nature)

Implements `references/journal-profile-contract.md` from
`quarto-manuscript-sci`. Facts below are split into **VERIFIED** (official
Springer Nature Link pages for this journal, fetched and read this session,
2026-07-04) and a **TO VERIFY** queue (not addressed by any fetched page) —
do NOT promote to `profile.yml` until an official source is fetched and
read.

**Platform note**: the journal's legacy `environmentalmicrobiome.biomedcentral.com`
URLs now all 301-redirect to `link.springer.com/journal/40793` — "BMC
journals have moved to Springer Nature Link." All `sources:` URLs in
`profile.yml` use the new `link.springer.com/journal/40793/...` form. This
platform migration is itself an important operational fact: bookmarked
biomedcentral.com URLs (including from older third-party guidance) will
redirect; always re-resolve via a live fetch before trusting a cached URL
for this journal.

## VERIFIED requirements (as of 2026-07-04)

Sources: [Journal homepage](https://link.springer.com/journal/40793) ·
[Aims and scope](https://link.springer.com/journal/40793/aims-and-scope) ·
[Submission guidelines](https://link.springer.com/journal/40793/submission-guidelines) ·
[Research](https://link.springer.com/journal/40793/submission-guidelines/research) ·
[Review](https://link.springer.com/journal/40793/submission-guidelines/review) ·
[Methodology](https://link.springer.com/journal/40793/submission-guidelines/methodology) ·
[Brief report](https://link.springer.com/journal/40793/submission-guidelines/brief-report) ·
[Software](https://link.springer.com/journal/40793/submission-guidelines/software) ·
[Perspective](https://link.springer.com/journal/40793/submission-guidelines/perspective) ·
[Comment](https://link.springer.com/journal/40793/submission-guidelines/comment) ·
[Correspondence](https://link.springer.com/journal/40793/submission-guidelines/correspondence) ·
[Meeting report](https://link.springer.com/journal/40793/submission-guidelines/meeting-report) ·
[Preparing your manuscript (general)](https://link.springer.com/journal/40793/submission-guidelines/preparing-your-manuscript) ·
[Ethics and disclosures](https://link.springer.com/journal/40793/ethics-and-disclosures) ·
[Editorial board](https://link.springer.com/journal/40793/editorial-board) ·
[How to publish with us](https://link.springer.com/journal/40793/how-to-publish-with-us) ·
[BMC-wide editorial policies](https://link.springer.com/brands/bmc/editorial-policies)

**Publisher / journal**: BMC (BioMed Central), part of Springer Nature.
ISSN 2524-6372 (confirmed via the journal homepage's own JSON-LD metadata;
online-only, fully open access). Editor-in-Chief: Joy Watts PhD (University
of Portsmouth). Journal Impact Factor 6.2 (2025), 5-year JIF 7.3 (2025),
median time to first decision 25 days (journal homepage metrics box).

**Scope** (verbatim, Aims and scope): "Microorganisms can be found across
all environments on Earth... `Environmental Microbiome` acknowledges this
universal presence and importance and is seeking submissions addressing the
varied facets of environmental and applied microbiome research." Topics
(non-exhaustive): air, soil and aquatic microbial ecology; microbiome
analyses; bioremediation; microbiome of the built environment;
geomicrobiology; microbial interaction with plants and agricultural crops;
extreme environment microbiology and astrobiology. Genome sequences are
in-scope only "if they are a fully integrated aspect of a research article
which elucidates the function and role of the microorganisms in their
environmental communities" (i.e., not standalone genome-announcement
papers). Full scope framing in `references/editorial-framing.md`.

**Article types**: exactly nine — Research, Review, Methodology, Brief
report, Software, Perspective, Comment, Correspondence, Meeting report (the
"Article Type" list on the Submission guidelines page; confirmed by
crawling each type's own subpage). There is NO "Short report" type (Brief
report is this journal's nearest equivalent) and NO "Database" type
(despite "database" appearing in generic BMC data-availability boilerplate
text about how to describe database availability — that is not an article
type here). **Review is effectively commissioned-only**: "Environmental
Microbiome no longer considers unsolicited reviews" (verbatim, Review
page) — flag this prominently before planning an unsolicited Review
submission.

**Word limits — the single biggest finding of this verification pass**: NO
article type states a main-text word limit anywhere in any fetched page.
Only the ABSTRACT is capped, at 350 words, for seven of the nine types
(Research, Review, Methodology, Brief report, Software, Perspective,
Comment); Correspondence and Meeting report have no numeric abstract cap at
all (just "briefly summarize"). Abstract STRUCTURE varies by type — see
`profile.yml` `manuscript_types[].abstract_rule` for the exact
structured/unstructured split per type (Research/Methodology/Brief
report/Software require Background/Results/Conclusions subheadings;
Perspective/Comment require a background/main-body/conclusion prose
paragraph; Review/Correspondence/Meeting report are unstructured).
`validate.py`'s word-limit check is therefore advisory-only for main text
on every type in this profile — there is no verified hard main-text number
to gate on for any of the nine types. The abstract limits ARE hard numbers
and should be checked.

**Section structure (Research, the flagship/default type)**: Title page /
Abstract / Keywords (3–10) / Background / Methods / Results / Discussion /
Conclusions / List of abbreviations / **Declarations** / Endnotes
(optional) / References. Methods "may also be placed after [the]
Conclusion section" (author's choice). Other types substitute sections —
see `profile.yml` `manuscript_types[].counting_rule` for each type's exact
structure (e.g., Software inserts Implementation / Availability and
requirements; Correspondence and Meeting report drop Background/Methods/
Results/Discussion/Conclusions entirely in favor of a single free-form
Main text section).

**Journal-specific "Criteria" requirements** (found on Research, Methodology,
and Brief report pages; a lighter version on Software; ABSENT from Review,
Perspective, Comment, Correspondence, Meeting report):
- Data/metadata/analysis-script availability: datasets in public
  repositories or as additional files; accompanying metadata formatted to
  the **MixS** (Minimum Information about any (x) Sequence) standard from
  the Genome Standards Consortium (http://gensc.org/mixs/); analysis
  code/scripts made available (knitr, iPython Notebooks, or similar).
- **Mandatory experimental controls**: "sampling controls, extraction
  controls, PCR amplification controls as negative controls, but also
  positive controls (mock communities or others)" — these controls must
  themselves be sequenced and the sequence data deposited publicly
  alongside the sample data. This is an unusually strict, journal-specific
  methodological gate distinct from generic BMC data-availability policy.
- Microbial taxon names (kingdom through subspecies) italicized per ASM /
  Journal of Bacteriology convention; strain designations/numbers NOT
  italicized.
- Terminology: use "16S rRNA gene", never "16S"/"16S rDNA"/"16S rDNA
  gene"/"16S gene" (following Marchesi et al.'s microbiome-vocabulary
  recommendations).
- Network analysis: co-association network methods must be
  compositionally-aware (the page names Pearson/Spearman correlation as
  explicitly NOT acceptable on their own, citing Gloor 2017, Friedman &
  Alm 2012, Weiss 2016, Peschel 2020, Bindels 2025).
- The homepage also flags the **STREAMS guidelines** ("standards for
  technical reporting in environmental and host-associated microbiome
  studies") as encouraged reading — a cross-journal (Microbiome +
  Environmental Microbiome) reporting-standards initiative, not a hard
  submission gate on its own fetched page, but worth checking against
  before submission.

**Declarations block** (mandatory heading, all subheadings required — write
"Not applicable" for any that don't apply, verbatim guidance on every
article-type page): Ethics approval and consent to participate · Consent
for publication · Availability of data and materials · Competing interests
· Funding · Authors' contributions · Acknowledgements · Authors'
information (optional). This is the BMC/Springer-Nature-wide Declarations
pattern, not an Environmental-Microbiome-specific invention — see
`quarto-manuscript-microbiome`'s own profile for the same block on the BMC
sibling journal. Full per-subsection content rules (ethics-approval
wording, consent-form handling, the exact allowed forms of a data
availability statement, competing-interests initials convention, authors'
contributions initials convention, group-authorship/PubMed-searchability
handling) are identical across all nine article-type pages and are
reproduced in `references/submission-checklist.md`.

**References**: "BioMed Central reference style" (Research/Review/
Methodology/Brief report/Software/Comment/Correspondence/Meeting-report
pages) — the SAME worked example block is labeled "the Vancouver reference
style" on the Perspective page alone; both names describe the identical
numbered, square-bracket, semicolon-delimited house style. Numbered
consecutively in square brackets by first appearance in text, then tables/
legends; only footnotes are permitted beyond the numbered list; journal
abbreviations follow Index Medicus/MEDLINE; web links/URLs get their own
reference-list entry (title + URL + access date), not an inline citation.
→ `assets/biomed-central.csl` (official Zotero/CSL "BioMed Central" style;
et-al-min=7/et-al-use-first=6 matches this journal's own 6-author + "et
al." worked example). No environmental-microbiome-specific CSL exists in
the official repo (confirmed 404).

**ORCID**: NOT found as a mandatory corresponding-author registration
requirement anywhere in any fetched page for this journal. The only ORCID
mention across all fetched pages is as an optional way to help an editor
verify a reviewer's identity when an author suggests peer reviewers in
their cover letter ("provide institutional email addresses where possible,
or information which will help the Editor to verify the identity of the
reviewer (for example an ORCID or Scopus ID)"). This is a notable contrast
with the Nature-brand sibling profiles (`quarto-manuscript-npjcw`,
`quarto-manuscript-natwater`), which both VERIFIED a mandatory
corresponding-author ORCID requirement — do not assume BMC journals share
that rule; see TO VERIFY.

**Formatting (applies from initial submission — BMC does not defer
formatting to acceptance the way the Nature-brand siblings do)**:
double-line spacing; line AND page numbering; no page breaks; SI units;
special characters must be embedded (not relying on font substitution,
"otherwise they will be lost during conversion to PDF"). Acceptable main
manuscript file formats: Microsoft Word (DOC/DOCX), Rich Text Format (RTF),
TeX/LaTeX (Springer Nature LaTeX template encouraged; compiled via pdfLaTeX/
TexLive 2021 during submission). Editable source files are required for
production — a PDF-only submission will need to be replaced with an
editable file at revision or acceptance.

**Figures**: uploaded as separate graphic files, numbered/ordered by first
mention; multi-panel figures (a/b/c/d...) as ONE composite file; correct
orientation; titles ≤15 words and legends ≤300 words live in the main
manuscript text (not baked into the graphic); figure KEYS are baked into
the graphic (opposite of the legend rule); tightly cropped; ≤10 MB per
file; accepted formats EPS/PDF/Word(single page)/PowerPoint(single page)/
TIFF/JPEG/PNG/BMP/CDX; final-PDF sizing 85 mm half-page / 170 mm full-page
width, ≤225 mm combined figure+legend height, ~300 dpi; lines ≥0.25 pt;
fonts embedded; author responsible for reuse permission on previously
published figures.

**Tables**: Arabic numerals, sequential citation; <1 page inline, >1 page
at the end of the text file; oversized/wide tables as additional files
(.xls/.csv); titles ≤15 words ABOVE, legends ≤300 words BELOW; native
"Table object" formatting only (never an embedded image or spreadsheet);
no color/shading (use superscript/numbering/lettering/symbols/bold,
explained in the legend); no commas in numeric values.

**Supporting information — BMC "Additional files", not "Supplementary
Information"**: each item is its OWN separate uploaded file (not one
merged SI PDF, unlike the Nature-brand sibling convention) — "Additional
file 1", "Additional file 2", etc.; ≤20 MB each; virus-scanned on upload;
no restriction on the number or total length of additional files for most
article types; a manifest (file name, file format + extension, title of
data, description of data) must be listed **inside a separate section of
the main manuscript text itself** — there is no standalone SI cover sheet
and no internal SI table of contents. Do not include patient consent forms,
language-editing certificates, or tracked-changes files as additional
files — email those to the editorial office if requested.

**Data availability**: mandatory "Availability of data and materials"
statement in every submission, using one of BMC's template sentence forms
(repository + persistent link; included in article/additional files; not
applicable/no datasets; or, for Perspective specifically, three more forms
including a "restrictions apply... available on reasonable request"
variant). Publicly available datasets must be cited in the reference list
with a DOI/accession number, formatted per DataCite minimum-information
guidance, with dataset identifiers expressed as full URLs. Software-type
submissions additionally require an "Availability and requirements" block
(project name/home page/OS/language/other requirements/license/
non-academic-use restrictions).

**Open access / APC**: fully open access; CC BY or CC BY-NC-ND (Creative
Commons Attribution Non-Commercial No Derivatives 4.0). Current APC
£1890.00 GBP / $2590.00 USD / €2190.00 EUR (VAT/local taxes may apply; price
locks at date of acceptance). Institutional agreements and low-income-
country automatic waivers available; discretionary waivers case-by-case;
**all waiver requests must be made at the point of submission** — requests
during review or after acceptance are not considered.

**Peer review / blinding**: single-anonymous — reviewers see author
identities, authors do not see reviewer identities ("the reviewer reports
provided to authors are anonymous"), confirmed independently on both the
Submission guidelines page and the journal's own Ethics & disclosures page.
No double-anonymized option of any kind is mentioned for this journal
specifically. Typically ≥2 independent reviewers per manuscript. The
journal participates in BMC's cross-journal manuscript-transfer ("Transfer
Desk") system and in COPE (Committee on Publication Ethics); uses
plagiarism-detection screening (CrossCheck) per COPE guidelines.

**AI / LLM policy** (BMC-wide, explicitly surfaced on this journal's own
Perspective article-type page): "Large Language Models (LLMs), such as
ChatGPT, do not currently satisfy our authorship criteria... Use of an LLM
should be properly documented in the Methods section (and if a Methods
section is not available, in a suitable alternative part) of the
manuscript." "AI assisted copy editing" (grammar/style/readability polish
of human-written text) does not need to be declared; generative content
creation does. Generative-AI images/video are not permitted in figures
except narrow, case-by-case, clearly-labeled exceptions (licensed-agency
images; images that are themselves the subject of an AI-focused piece;
verifiable/attributable scientific-data-grounded generative tools).
Peer reviewers are asked not to upload manuscripts into generative AI
tools, and must declare any AI-tool use that supported their evaluation.

**Authorship criteria** (BMC-wide, McNutt et al. 2018 PNAS, CC BY 4.0):
substantial contribution to conception/design OR acquisition/analysis/
interpretation of data OR new software creation OR drafting/substantive
revision, AND approval of the submitted version, AND agreement to be
personally accountable. Contributors not meeting all criteria go in
Acknowledgements, not the author list. Author-list changes after
submission require a completed change-of-authorship form signed by every
author; no additions/deletions/order changes/corresponding-author changes
are permitted after acceptance.

**Submission portal**: https://submission.springernature.com/new-submission/40793/3
(resolved target of the "Submit your manuscript" link on the journal
homepage / Submission guidelines page).

## TO VERIFY (not addressed in any fetched official page — check before submission)

- [ ] Whether ORCID becomes mandatory later in the submission workflow
      (e.g., at the actual submission-portal registration step) even though
      no fetched author-guidance page states this — tried 2026-07-04:
      fetched and read Submission guidelines, all nine article-type pages,
      Prepare supporting information, and the BMC-wide editorial-policies
      page in full; ORCID appears exactly once, as an optional
      reviewer-identity aid, never as an author requirement. The actual
      Springer Nature submission portal (`submission.springernature.com`)
      could not be driven interactively in this session (it requires an
      authenticated submission session, not a static guidance page) — this
      is a genuine gap, not a "found absent" result. `profile.yml` leaves
      no ORCID key at all rather than fabricating `required: false`.
- [ ] Whether the STREAMS guidelines (mentioned only on the journal
      homepage's "Journal highlights" feed) constitute a formal submission
      requirement or a soft recommendation — tried 2026-07-04: the
      homepage names them as something the journal "encourages authors to
      follow" but the linked full guidelines document was not fetched in
      this session; none of the nine article-type pages or the general
      Submission guidelines page names STREAMS explicitly as a completion-
      required checklist (unlike the BMC-wide CONSORT/PRISMA/STROBE/CARE/
      etc. reporting-guideline checklist, which IS framed as mandatory
      "before peer review").
- [ ] Reference limit (count) per article type — tried 2026-07-04: fetched
      and read the References section of every one of the nine article-type
      pages in full; none states a maximum reference count (unlike the
      Nature-brand siblings' "≤50/≤60/≤120" guidance numbers).
- [ ] Figure/table count limit per article type — tried 2026-07-04: same
      pages; no maximum number of figures or tables is stated anywhere.
- [ ] Conditions-of-publication as a distinct policy page — tried
      2026-07-04: the legacy `.../submission-guidelines/conditions-of-
      publication` URL 301-redirects to the plain `/submission-guidelines`
      page with no matching anchor, suggesting this content was folded
      into (or superseded by) the general Submission guidelines /
      Duplicate publication policy during the Springer Nature Link
      migration; the duplicate-publication content that likely replaced it
      IS captured above under Peer review / blinding and the BMC-wide
      editorial-policies source.
- [ ] Body manuscript font/point size — tried 2026-07-04: fetched and read
      "Preparing main manuscript text" in full; no font family or point
      size is specified for the manuscript body (only figure-file
      specifications are sized/fonted). `scripts/build_reference_docx.py`
      uses the same conventional Times New Roman 12pt/10pt default as the
      sibling profiles, explicitly NOT a verified Environmental-Microbiome
      requirement.
- Rule: each checked item moves UP into VERIFIED with a link, and its
  number lands in `profile.yml`; update `verified_date`.

## Sibling BMC/Nature-Portfolio microbiome journals — do not conflate

Two other profiles exist in this same skills library for closely related
journals; this session confirmed their identifying facts independently
while building this profile (not merely copied from their SKILL.md files):

- **`quarto-manuscript-microbiome`** — BMC's other, broader microbiome
  journal (ISSN 2049-2618, confirmed via `link.springer.com/journal/40168`
  JSON-LD metadata this session). Same publisher, same Springer Nature Link
  platform, same `assets/biomed-central.csl` (independently fetched and
  resolved to the identical CSL file by both profiles — cross-validates the
  CSL choice), same BMC-wide Declarations/authorship/AI-policy boilerplate.
  **Editorially entangled, not identical**: Environmental Microbiome's own
  homepage states its submissions are "aided by Editors working across
  Microbiome and Environmental Microbiome," and both journals promote the
  shared STREAMS reporting guidelines — but each keeps its own distinct
  ISSN, its own dedicated Editorial Board (Environmental Microbiome's own
  board, led by Joy Watts, does not simply duplicate Microbiome's), and its
  own scope statement (Microbiome's own aims-and-scope text, per that
  profile, is not restricted to "environmental" microbiomes the way this
  journal's is — Environmental Microbiome explicitly foregrounds air/soil/
  aquatic/built-environment/geomicrobiology/extreme-environment framing
  that Microbiome's broader host-and-environment scope does not lead with).
  Practically: a manuscript that could plausibly fit either journal should
  be routed by asking whether its primary frame is the ENVIRONMENT the
  microbiome inhabits (→ this profile) versus the microbiome/host-microbe
  system more generally, potentially including strong clinical/biomedical
  framing (→ `quarto-manuscript-microbiome`).
- **`quarto-manuscript-npjbiofilms`** — Nature Portfolio (not BMC), ISSN
  2055-5008 (confirmed via the official ISSN Portal record this session).
  Different publisher imprint (Nature Portfolio vs. BMC, despite both being
  Springer Nature-owned), different house style (npj/Nature referencing and
  formatting conventions, not BMC Declarations/Vancouver), different
  editorial board and submission portal. No meaningful risk of conflating
  the two once the publisher imprint is checked — flagged here only because
  the "Biofilms and Microbiomes" name is easy to mistake for an Environmental
  Microbiome article type or section.

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
- `references/editorial-framing.md` — scope + cover-letter angle
