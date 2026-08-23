---
name: quarto-manuscript-natwater
description: >
  Journal profile for Nature Water (Nature Portfolio, Springer Nature),
  consumed by quarto-manuscript-sci. Use whenever a manuscript targets Nature
  Water or the user mentions Nature Water, Nature-brand water journal,
  Nature/nature.csl referencing style, or Springer Nature submission for
  water-society research (hydrology, water/wastewater treatment,
  desalination, water governance, water-and-society engineering or social
  science) — for authoring, rendering, validation, submission packaging, or
  revision. NOT for npj Clean Water (a separate, fully-OA, less selective
  npj-series title with no Extended Data concept and softer word limits;
  separate profile, quarto-manuscript-npjcw).
compatibility: Consumed by quarto-manuscript-sci; not intended standalone.
---

# Journal Profile: Nature Water (Nature Portfolio / Springer Nature)

Implements `references/journal-profile-contract.md` from `quarto-manuscript-sci`.
Facts below are split into **VERIFIED** (official nature.com/natwater pages,
fetched and read this session, 2026-07-04) and a **TO VERIFY** queue (not
addressed by any fetched page) — do NOT promote to `profile.yml` until an
official source is fetched and read.

## VERIFIED requirements (as of 2026-07-04)

Sources: [Journal homepage](https://www.nature.com/natwater/) ·
[Aims & Scope](https://www.nature.com/natwater/aims) ·
[Content types](https://www.nature.com/natwater/content) ·
[Journal information](https://www.nature.com/natwater/journal-information) ·
[Journal metrics](https://www.nature.com/natwater/journal-impact) ·
[Editorial values statement](https://www.nature.com/natwater/editorial-values-statement) ·
[Submission guidelines (index)](https://www.nature.com/natwater/submission-guidelines) ·
[Presubmission enquiries](https://www.nature.com/natwater/submission-guidelines/presubmission-enquiries) ·
[Editorial process & peer review](https://www.nature.com/natwater/submission-guidelines/editorial-process) ·
[Preparing your material](https://www.nature.com/natwater/submission-guidelines/preparing-your-submission) ·
[Formatting your initial submission](https://www.nature.com/natwater/submission-guidelines/initial-formatting) ·
[Double-anonymized peer review](https://www.nature.com/natwater/submission-guidelines/dapr) ·
[Language](https://www.nature.com/natwater/submission-guidelines/language) ·
[AIP and formatting](https://www.nature.com/natwater/submission-guidelines/aip-and-formatting) ·
[ORCID](https://www.nature.com/natwater/submission-guidelines/orcid) ·
[Production process](https://www.nature.com/natwater/submission-guidelines/production-process) ·
[Matters Arising](https://www.nature.com/natwater/submission-guidelines/matters-arising) ·
[Publishing options](https://www.nature.com/natwater/submission-guidelines/publishing-options) ·
[Our publishing models](https://www.nature.com/natwater/our-publishing-models) ·
[Open access funding](https://www.nature.com/natwater/open-access-funding) ·
[Editorial policies (index)](https://www.nature.com/natwater/editorial-policies) ·
[Editorial policies > Peer Review](https://www.nature.com/natwater/editorial-policies/peer-review) ·
[Editorial policies > Artificial Intelligence (AI)](https://www.nature.com/natwater/editorial-policies/ai) ·
[Editorial policies > Reporting standards](https://www.nature.com/natwater/editorial-policies/reporting-standards) ·
[Editorial policies > Preprints & Conference Proceedings](https://www.nature.com/natwater/editorial-policies/preprints-conference-proceedings)

**Publisher / journal**: Springer Nature (Nature Portfolio) — a Nature-BRAND
research journal (not an npj-series spinoff; "Like other journals in the
Nature family, Nature Water has no external editorial board... all editorial
decisions are made by a dedicated team of full-time professional editors").
EISSN 2731-6084 (correct abbreviation for abstracting/indexing: "Nat. Water").
Monthly, **exclusively online** (no print edition — "Nature Water is an
exclusively online publication," Journal information page). Advance Online
Publication (AOP) used for all research articles.

**Selectivity signal** (Journal metrics page, 2025 data — NOT a formatting
rule, informational for editorial-framing): 2-year Journal Impact Factor
30.7; 5-year JIF 30.7; SNIP 3.795; SJR 5.735; median submission-to-first-
decision 6 days; median submission-to-acceptance 141 days. This is a
flagship-tier Nature-brand journal, markedly more selective/higher-impact
than npj Clean Water (an npj-series title with no comparable JIF tier).

**Scope** (verbatim/paraphrased from Aims & Scope + Journal information):
"Nature Water covers all aspects of research that are connected to this
evolving relationship between society and water resources," publishing in
natural sciences (primarily Earth and environmental science), engineering
(environmental, civil, chemical, materials), and social sciences (economics,
human geography, sociology), "with a particular interest in regards to
interdisciplinary research." Full topic list and fit argument in
`references/editorial-framing.md`.

**Content types & format rules** (Content types page, verbatim numbers). Every
non-Article/Analysis type marked with `*` on the journal's own page carries
this rule: "These content types should not include original (previously
unpublished) research findings and may only contain minimal new supporting
data. As they are non-primary articles they are not eligible for Open Access
and can only be published using the subscription-based publishing route."
- **Article** — the journal's ONLY original-research format ("Nature Water
  publishes original research in one format, Article, which may range from
  what are typically considered to be short 'communications', through to
  more in-depth studies"). Length up to 3,000 words, excluding abstract,
  Methods, references, figure legends. Abstract up to 150 words, unreferenced.
  Display items up to 7 (figures and/or tables). Structure: Introduction (no
  heading) / Main text / Discussion-Conclusions / Methods — main text and
  Methods use topical subheadings; Discussion/Conclusions does NOT. References
  guideline up to 50 (not strictly enforced — "as a guideline"). Peer
  reviewed; includes received/accepted dates; may have Supplementary
  Information; eligible for Gold OA.
- **Analysis** — "a new analysis of existing data, describes new data
  obtained in a comparative analysis or introduces a new simulation or model
  that leads to novel and arresting conclusions of importance to a broad
  audience. Systematic reviews or meta-analyses of primary research
  literature can also be accommodated by this format." Length up to 4,000
  words, excluding abstract, online Methods, references, figure legends.
  Abstract 100–150 words, unreferenced. Display items up to 8. Same
  Introduction/Main text/Discussion/Methods structure as Article (Discussion
  has no subheadings). References guideline up to 50. Peer reviewed; may have
  SI; eligible for Gold OA (Analysis is NOT asterisked on the Content types
  page — it is a primary-research-eligible format alongside Article).
  **This is the best-fit format for an LLM-benchmark-style manuscript**: its
  own definition explicitly names "a new analysis of existing data... a
  comparative analysis... a new simulation or model" — an LLM benchmark
  study (comparative evaluation across models/tasks) matches this description
  directly, more precisely than any other content type on this journal.
- **Perspective** — "a review of a topic from a personal viewpoint... more
  forward-looking and/or speculative than Reviews... **Perspectives may not
  contain primary research data.**" Abstract 100–150 words (prose) / "up to
  150 words" (Format block), unreferenced. Main text up to 4,000 words
  (excluding abstract, references, figure/table captions, boxes). Display
  items up to 5 (figures, tables, or boxes). References up to 120 (guideline;
  "citations should be selective"). Footnotes not used. Peer reviewed
  (factual accuracy, citations, scholarly balance); edited in consultation
  with the editorial team. Asterisked on Content types page → subscription-
  only, not OA-eligible. **Important finding for this manuscript's fit**: the
  explicit "may not contain primary research data" rule means a benchmark
  paper reporting ORIGINAL evaluation results (new data generated by running
  models against tasks) does not fit Perspective's own stated constraints —
  see `references/editorial-framing.md` for the full argument that Analysis,
  not Perspective, is this journal's correct format for such a manuscript.
- **Review** — "an authoritative, balanced and scholarly survey of recent
  developments... scope should be broad enough that it is not dominated by
  the work of a single research institution... **Unpublished primary
  research data are not permitted in Reviews.**" Abstract up to 150 words,
  unreferenced. Main text up to 6,000 words (excluding abstract, references,
  figure/table captions, boxes). Display items up to 8. References up to 120.
  "Reviews are usually commissioned by the editors, so it is advisable to
  send a pre-submission enquiry including a synopsis" — **this directly
  conflicts with the journal's own Presubmission enquiries page** ("Nature
  Water does not accept presubmission enquiries"); both are Nature Water's
  own official pages, fetched and read in full this session — flagging the
  contradiction rather than silently picking a side; treat "commissioned,
  enquire via general contact" as the practical reading. Asterisked →
  subscription-only.
- **Correspondence** — 300–800 words; 1 display item; references up to 10
  (article titles omitted); peer-reviewed at editors' discretion; NOT for
  technical comments on Nature Water papers (use Matters Arising instead).
  Asterisked → subscription-only.
- **Comment** — up to 2,000 words; no fixed structure; references used
  sparingly, up to 15 (titles omitted); "does not normally contain primary
  research data" although "sociological" data (funding trends, demographics,
  bibliometrics) is allowed; peer review at editors' discretion. Asterisked →
  subscription-only.
- **Matters Arising** — main text as concise as possible, "ideally not
  exceed 1,200 words"; opens with a brief non-specialist summary paragraph
  used as the submission abstract (no numeric word cap stated for this
  paragraph beyond "brief"); ideally 1–2 small figures/tables (complex ones
  as Extended Data, ≤3 items); references guideline up to 15, "reference
  style is as for Articles"; competing-interests and author-contributions
  statements mandatory; life-sciences contributions with new data need a
  completed reporting summary AND an editorial policy checklist BEFORE peer
  review. Must be preceded by an attempt to contact the original authors
  (2-week wait if no response). Nature Water does not consider Matters
  Arising on papers published in OTHER journals.
- **News & Views, Policy Brief, Feature, News Feature, Q&A, World View** —
  commissioned/invited formats (Feature and News Feature accept proposals by
  email; Q&A and Policy Brief are commissioned; World View follows the
  cross-Nature-Reviews World View format). Feature/News Feature: up to 3,000
  words, journalistic style, tables/figures encouraged. News & Views: not
  peer-reviewed. None of these are viable routes for an unsolicited primary
  research/benchmark manuscript.

**Abstract "summary paragraph" question — RESOLVED**: Nature Water's Article
abstract is explicitly **"up to 150 words, unreferenced"** (Content types
page, Format block) — a plain unreferenced abstract, not a distinctly-named,
citation-bearing "summary paragraph" convention. No fetched Nature Water page
uses the phrase "summary paragraph." Analysis differs slightly: 100–150
words (i.e., a floor as well as a ceiling), still unreferenced.

**TOC / graphical abstract — RESOLVED, does not exist**: no mention of a
table-of-contents graphic, visual abstract, or graphical abstract appears
anywhere in Aims & Scope, Content types, Preparing your material, Initial
formatting, or AIP and formatting (the journal's own full final-formatting
spec, checked section-by-section: Document type / Tables / Figures / Colour
charges / References / Methods / Acknowledgements / Extended data figures /
Source Data / Supplementary information / New structures / Gene nomenclature
/ Chemical & biological nomenclature / Equations / Cover artwork). "Cover
artwork" (AIP and formatting §15) is an OPTIONAL, editor-selected ISSUE-COVER
image contest for accepted papers — a distinct concept from a per-article
TOC/graphical-abstract requirement, and not a submission requirement.
`profile.yml`'s `toc_graphic.required` is explicitly set to `false` (not
left null) to record this as a checked-and-absent fact.

**References**: Nature Water's OWN "AIP and formatting" page (§5 References)
is a first-party, non-deferred formatting spec (stronger source than a
"see general Nature guidance" pointer): numbered sequentially in a fixed
cross-document order — Main Text, Methods, Data Availability Section, Tables,
Figure Legends, Box, Extended Data Figures; only one publication per
reference; DOI-bearing research objects (conference abstracts, numbered
patents, datasets, protocols, code) included in the reference list;
unpublished/in-prep/under-review-without-preprint works cited in text only
(with author list); URLs cited parenthetically in text, not in the reference
list; grant/acknowledgment details not permitted as numbered references;
footnotes not supported. Article titles are REQUIRED in references for
long-form types (Articles, Perspectives, Reviews) and OMITTED for short types
(Comment/Correspondence/News & Views) — confirmed both on this page and on
Content types (Correspondence, Comment). Journal names italicized (verified
from the page's own worked example: "*Nature* 344, 524–526 (1990)."). The
same worked example shows the volume number NOT visually bold in the
journal's own HTML rendering, which differs from `assets/nature.csl`'s
`font-weight="bold"` volume macro (verified in the CSL's own source) and from
generic Nature-brand house style — noted as a minor rendering discrepancy,
not treated as a reason to deviate from the official CSL, since Nature Water
IS a Nature-titled journal (the CSL's own `documentation` link points to
`nature.com/nature/for-authors/formatting-guide`, the exact house style this
journal belongs to — a more direct match than for an npj-series title).
Book citations require the publisher; dataset/code citations with DOIs
follow author/title/repository/DOI-as-URL format; preprints cited with
"Preprint at [URL] (year)." → `assets/nature.csl` (official CSL "Nature"
style, numeric citation format, fetched 2026-07-04).

**Methods**: subdivided by short bold headings referring to methods used
(e.g., Statistics, Reagents, Animal models encouraged as named subsections);
written as concisely as possible while enabling replication; Methods-only
references continue numbering from the end of the main-text reference list.
Authors encouraged to deposit step-by-step protocols to Protocol Exchange,
linked from the Methods section and added to the reference list.

**Extended Data** (Nature-brand-specific concept, NOT present in npj Clean
Water's profile): OPTIONAL online-only display items providing background
not warranting a main display slot; maximum 10 Extended Data items; must be
referred to as discrete items at an appropriate point in the main text;
sized to fit a single PDF page each; not copy-edited/styled by the journal
(authors should follow house style closely); legends included in the
"Inventory of Supporting Information" document.

**ORCID**: required for corresponding authors of ACCEPTED papers, linked
before submitting the final version (cannot be added/modified at proof
stage). Non-corresponding authors encouraged but not required.

**Data / code availability**: governed by Nature Portfolio's shared
"Reporting standards and availability of data, materials, code and
protocols" policy, which Nature Water's own Editorial policies page
confirms it follows ("As part of Nature Portfolio, Nature Water follows
common policies"). A Data Availability Statement is mandatory for every
published manuscript reporting original research, describing access to the
"minimum dataset"; large datasets in Supplementary Information are
"strongly discouraged" in favor of repository deposition. A Code
Availability statement (heading "Code availability," placed AFTER the data
availability statement and BEFORE references — confirmed by both the
Reporting standards page and the AIP-and-formatting reference-ordering list,
which places "Data Availability Section" immediately before "Tables" in the
numbering sequence) is required whenever custom code/algorithm is central to
the paper's main claims; code must be made available to editors/reviewers on
request, and best practice is deposition in a DOI-minting repository
(Zenodo, Code Ocean, etc.) at publication. Nature Water is NOT among the
subset of Nature-brand journals listed on the Reporting standards page that
perform formal PEER REVIEW of code/algorithms (that list — Nature, Nature
Biomedical Engineering, Nature Machine Intelligence, etc. — does not include
Nature Water).

**Reporting summary / editorial policy checklist**: research articles in
"the life sciences, behavioural & social sciences and ecology, evolution &
environmental sciences" require a completed Reporting Summary made available
to editors/reviewers and published with accepted manuscripts (Reporting
standards page); specific physical-sciences sub-areas (solar cells, lasing
claims) also require one. An Editorial Policy Checklist before peer review is
explicitly required for life-sciences Matters Arising contributions with new
data (Matters Arising page); its applicability to ordinary Article/Analysis
submissions generally is not stated on any fetched page — see TO VERIFY.
Given Nature Water's engineering/CS-adjacent scope, an LLM-benchmark-for-
water-technology manuscript likely falls OUTSIDE the life-sciences/
behavioural-social-sciences/ecology-environmental-sciences reporting-summary
trigger, but this is a judgment call, not a verified exemption — flag at S5.

**Peer review / blinding**: single-anonymized by default — "Reviewers are
not identified to the authors, except at the request of the reviewer"
(Editorial process page). Nature Water explicitly OFFERS a double-anonymized
peer review OPTION, opt-in at submission via checkbox in the manuscript
tracking system, per its own dedicated page (`submission-guidelines/dapr`):
"Nature Water offers double-anonymized peer review; authors who choose this
option will remain anonymous to the reviewers throughout the peer review
process." Authors are solely responsible for anonymizing the manuscript
(not checked by the editor); a Nature Portfolio-wide checklist PDF is
provided. → `blinding: optional` (default single; double-anonymized
confirmed available for THIS journal specifically, unlike npj Clean Water
where the option's availability could not be confirmed). Manuscripts
typically go to two or three reviewers, sometimes more for specialist advice.
Transparent peer review: Nature Water participates in the Nature Portfolio
transparent-peer-review scheme as an OPT-IN offered to authors "at the
completion of the peer review process, before the paper is accepted" (not
mandatory, unlike Nature Communications/Comms Earth & Environment/Comms
Psychology where it is compulsory for all articles).

**Formatting at initial submission**: NONE required beyond suitability for
assessment/review — "Your initial submission does not need to be specially
formatted." Accepted formats: PDF, Word, or TeX/LaTeX (submit compiled PDF
for LaTeX). No presubmission enquiries accepted (see the Review-type
contradiction noted above). Cover letter required, explaining importance/fit,
disclosing related manuscripts under consideration elsewhere and any prior
editor discussions; if double-anonymized peer review is chosen, author
names/affiliations go in the cover letter (not the manuscript) instead.
Supplementary Information is optional at initial submission and is sent to
peer reviewers alongside the manuscript.

**Formatting at acceptance ("AIP and formatting")** — full first-party spec:
- *Document type*: Word or TeX/LaTeX only; no PDF for final submission. Word:
  "we accept all standard fonts" (Symbol font for Greek characters). LaTeX:
  default Computer Modern fonts, standard class files (article.cls,
  revtex.cls, amsart.cls), numerical citations only, .bbl content pasted
  into the .tex file (no live \bibliography commands), no personal macros.
- *Tables*: at the end of the text document; complex tables as a separate
  Excel file; statistical tables describe error-analysis standards/ranges in
  the legend; chemical-structure tables include native ChemDraw .cdx files
  separately. No stated rule on border style or caption position (above vs.
  below) — see TO VERIFY.
- *Figures*: cited in sequence as "Fig. 1", "Fig. 2"; minimum 300 dpi;
  maximum width 180 mm; 5–7 pt sans-serif labels (Symbol font for Greek);
  scale bars not magnification factors; error bars where appropriate; no
  flattened/uneditable labeling. Legends: brief title + per-panel
  description cited in sequence; verbal cues ("open red triangles") not
  visual symbols; centre-value definition (median/mean), error-bar
  definition, sample size (n), statistical test, and P values all required
  in the legend; legend length capped by the article type's own word limit
  (i.e., NOT a separate fixed figure-legend word cap — ride on the
  manuscript-type limit).
- *Colour charges*: "(print journals only)" — Nature Water is confirmed
  EXCLUSIVELY ONLINE (Journal information page), so this charge does NOT
  apply to Nature Water; recorded as a resolved N/A, not a live cost.
- *Acknowledgements*: brief; no thanking anonymous referees/editors; grant
  numbers permitted; dedications only for named non-author contributors.
- *Source Data*: encouraged for figures; unprocessed gels/blots as per-figure
  PDFs; statistics source data as per-figure Excel files.
- *Equations*: in the main text, numbered parenthetically, e.g. "equation
  (1)".

**Supplementary Information**: "published as supplied," presented clearly
and in logical order; each item designated Supplementary
Equation/Discussion/Notes/Figure/Table/Video/Audio/Data/Software and
numbered sequentially (separate numbering from main text and Extended Data);
Supplementary Figures used only when Extended Data isn't appropriate, one
figure+legend per PDF page; primary SI submitted as a single combined PDF
("supplementary text, figures, simple tables or data, and associated
legends"); complex tables/data (larger than an A4 PDF page) accepted
separately as Excel workbooks or .csv files named "Supplementary Tables" or
"Supplementary Data"; every SI item cited at least once in the main text or
Methods, in sequence, using the word "Supplementary" each time. No SI cover
sheet or internal SI table of contents is mentioned anywhere in the fetched
guidance (same gap as npj Clean Water).

**Open access / publishing model**: HYBRID — authors of PRIMARY research
(Article, Analysis) choose between (1) traditional subscription publishing
(free to submit/publish, reader-pays-or-institution-subscribes) or (2) Gold
Open Access, APC **£9,390.00 / $12,850.00 / €10,850.00** (Publishing options
page) — markedly higher than npj Clean Water's fully-OA-only APC (~£2,990 for
Original Research) because Nature Water is a higher-tier Nature-brand title
with a subscription option, not an OA-only journal. Non-primary content
types (Review, Perspective, Comment, Correspondence, News & Views, Policy
Brief, Feature, Q&A) are NOT ELIGIBLE for Gold OA and can only be published
via the subscription route, regardless of author preference. Institutional
open-access agreements may cover the APC (Open access funding page,
institution look-up tool).

**Overlap / preprints / transfers**: submission must not "significantly
overlap" with other under-consideration/in-press papers from the same
author group (conference abstracts excepted); preprint posting explicitly
encouraged and does not count as prior publication or affect the "advance"
assessment. Manuscripts declined at Nature Water can be transferred within
the Nature Portfolio family, carrying reviewer reports/identities EXCEPT
when transferring to the npj Series or Scientific Reports (those transfers
drop reviewer identity/report by default). Conference-proceedings-derived
submissions must show a "substantial extension" over the proceedings paper
(editors decide what counts as substantial).

**AI policy** (directly relevant to this manuscript's topic — verbatim from
Editorial policies > AI, identical wording to the Nature-Portfolio-wide
policy also confirmed on npj Clean Water's page): LLMs "do not currently
satisfy our authorship criteria... an attribution of authorship carries with
it accountability for the work, which cannot be effectively applied to
LLMs." Any LLM use must be documented in the Methods section (or a suitable
alternative section). "AI assisted copy editing" (grammar/style/readability
polish of human-written text) does not need to be declared; generative
content creation does. Generative AI images are not permitted in figures
except narrow, case-by-case, clearly-labeled exceptions. This governs
LLM-as-authoring-tool, not LLM-as-subject-of-study — a manuscript that
*benchmarks* LLMs (as this one does) is not itself constrained by this
policy beyond normal disclosure of any LLM used to help write the paper
text.

**Submission portal**: https://mts-natwater.nature.com/cgi-bin/main.plex
("Submit manuscript" link, repeated across the journal's own navigation and
the Submission guidelines page).

## TO VERIFY (not addressed in any fetched official page — check before submission)

- [ ] Line spacing (single vs double) for the manuscript body — tried
      2026-07-04: fetched and read "Formatting your initial submission" and
      the full "AIP and formatting" page (all 15 numbered sections); neither
      states a line-spacing requirement. Initial submission explicitly needs
      no special formatting; final/AIP formatting covers document type,
      tables, figures, references, Methods, Acknowledgements, Extended Data,
      Source Data, SI, structures, nomenclature, equations, and cover
      artwork — never spacing.
- [ ] Line numbers requirement — tried 2026-07-04: same two pages; no
      mention found.
- [ ] Manuscript body font/point size — tried 2026-07-04: "AIP and
      formatting" §1 (Document type) states "we accept all standard fonts"
      for Word with no specific typeface/size mandated (Symbol font is
      required only for Greek characters); LaTeX requires default Computer
      Modern with no author-facing point-size instruction ("no need to spend
      time visually formatting the manuscript; our style will be imposed
      automatically"). The VERIFIED 5–7pt sans-serif rule applies only to
      text baked INTO figure images, not manuscript body text.
- [ ] Table border/rule style and caption position (above vs. below) —
      tried 2026-07-04: fetched and read "AIP and formatting" §2 (Tables) in
      full; only covers placement-at-end-of-document, complex-table Excel
      export, statistical-table legend content, and ChemDraw .cdx handling
      for chemical-structure tables. No border/caption-position rule stated.
- [ ] Editorial Policy Checklist applicability to ordinary Article/Analysis
      submissions (confirmed only for life-sciences Matters Arising
      contributions with new data) — tried 2026-07-04: fetched and read the
      Matters Arising page (states the checklist requirement explicitly for
      that type) and the Reporting standards page (describes the Reporting
      Summary requirement by discipline but never mentions an "editorial
      policy checklist" for ordinary research Articles/Analyses). Treat as
      unconfirmed for the general case; do not assume it's required for a
      water-technology/CS-adjacent Analysis submission.
- [ ] Whether an LLM-benchmark-for-water-technology Analysis manuscript
      triggers the Reporting Summary requirement (scoped to "life sciences,
      behavioural & social sciences and ecology, evolution & environmental
      sciences" plus named physical-sciences sub-areas) — tried 2026-07-04:
      fetched and read the Reporting standards page's discipline list in
      full; an engineering/CS-adjacent water-technology benchmark does not
      obviously fall in any listed bucket, but no explicit exemption
      statement exists either — this is a judgment call to flag at S5, not
      a verified fact.
- [ ] Review-type presubmission-enquiry contradiction — Content types page
      says Reviews are "usually commissioned... advisable to send a
      pre-submission enquiry including a synopsis," while the dedicated
      Presubmission enquiries page states flatly "Nature Water does not
      accept presubmission enquiries." Tried 2026-07-04: fetched and read
      both pages in full; this is a genuine unresolved contradiction between
      two of the journal's own official pages, not a research gap on my
      part — re-check directly with the editorial team
      (naturewater@nature.com) before attempting a Review submission. Not
      relevant to Article/Analysis submissions.
- [ ] SI pagination convention (e.g., an "S1, S2…" prefix) and SI cover
      sheet / internal table of contents — tried 2026-07-04: fetched and
      read "AIP and formatting" §10 (Supplementary information) in full;
      covers item-type numbering, single-PDF submission, and the
      Excel/.csv exception for oversized tables, but never states a
      page-numbering convention or mentions a cover sheet/internal TOC.
- Rule: each checked item moves UP into VERIFIED with a link, and its value
  lands in `profile.yml`; update `verified_date`.

## Editorial framing for this manuscript's topic (LLM benchmark, a water-treatment application)

See `references/editorial-framing.md` for the full scope-fit argument,
including the corrected content-type recommendation (Analysis, not
Perspective — Perspective's own rules explicitly forbid primary research
data) and the selectivity context (JIF 30.7, no external editorial board,
141-day median time to acceptance).

## Quarto/DOCX implementation notes for this journal

- `assets/reference.docx` is generated by `scripts/build_reference_docx.py`
  from a fresh `quarto pandoc --print-default-data-file reference.docx`,
  restyled to Times New Roman — 12pt body/headings, 10pt captions. No
  Nature-Water-specific manuscript-body font or point size requirement was
  found during verification (see TO VERIFY: "we accept all standard fonts"
  for Word, with no size specified) — this uses the same standard,
  portal-safe serif default as `quarto-manuscript-npjcw` and
  `quarto-manuscript-est`. The VERIFIED sans-serif (5–7pt) requirement
  applies only to lettering baked into figure images, not manuscript body
  text, so it is NOT applied to the reference doc. Re-run the builder script
  when requirements change; never hand-edit the `.docx`.
- No TOC-art logic applies to this profile: `toc_graphic.required: false`
  means `render.py`'s TOC-art gate and `insert_toc_art()` step are both
  skipped entirely for `--target submission`.
- Word count: Article word_limit 3000, Analysis 4000, Perspective 4000,
  Review 6000, Comment 2000, Correspondence 300-800 (both bounds live),
  Matters Arising 1200 — ALL excluding abstract/Methods/references/figure
  legends per each type's own counting_rule. `validate.py`'s word-limit
  check is a real hard gate for every type in this profile (unlike npj
  Clean Water, where Article had no stated cap at all).
- Extended Data (max 10 items) and the Data-Availability-before-Tables
  reference-ordering rule are Nature-brand-specific extensions beyond the
  base contract schema; consumers that only implement the npj Clean Water
  profile's simpler section list should NOT reuse it verbatim for this
  journal — see `section_headings` in `profile.yml`, which includes
  "Extended Data" and orders "Data availability"/"Code availability" ahead
  of "Tables"/"Figure legends" per the AIP-and-formatting reference sequence.
- SI: `si.separate_file: true`, `si.pdf_only: false` (oversized
  tables/spreadsheets go out as separate Excel/.csv files) are wired for
  `render.py`/`validate.py`; `si.page_prefix` and `si.needs_cover_sheet`
  stay `null`/`false` pending the TO VERIFY items above.
- `blinding: optional` is a live, actionable value for this profile (unlike
  npj Clean Water's unresolved case) — `quarto-manuscript-sci` should
  actually prompt the author on double-anonymized peer review for Nature
  Water submissions, since the option is confirmed available and requires
  author-driven manuscript anonymization per the linked checklist PDF.

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
- `references/editorial-framing.md` — scope + selectivity + corrected
  content-type argument (Analysis over Perspective) + cover-letter angle
