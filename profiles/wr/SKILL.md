---
name: quarto-manuscript-wr
description: >
  Journal profile for Water Research (Elsevier, in association with IWA),
  consumed by quarto-manuscript-sci. Use whenever a manuscript targets Water
  Research or the user mentions Water Research, Elsevier water journal, IWA
  (International Water Association) co-published journal, Editorial Manager
  submission for water/wastewater/desalination research, or Elsevier-Harvard
  referencing — for authoring, rendering, validation, submission packaging,
  or revision. NOT for Water Research X (the open-access companion journal;
  same aims/scope, separate profile).
compatibility: Consumed by quarto-manuscript-sci; not intended standalone.
---

# Journal Profile: Water Research (Elsevier / IWA)

Implements `references/journal-profile-contract.md` from `quarto-manuscript-sci`.
Facts below are split into **VERIFIED** (official sources, fetched and read
this session) and a **TO VERIFY** queue (not addressed anywhere in fetched
official guidance) — do NOT promote to `profile.yml` until an official source
is fetched and read.

## A note on how the Guide for Authors was actually fetched

ScienceDirect (`sciencedirect.com`) serves an automated CAPTCHA/bot-challenge
page (HTTP 403, "Are you a robot?") to direct fetches of
`https://www.sciencedirect.com/journal/water-research/publish/guide-for-authors`
— confirmed independently via both the WebFetch tool and a raw `curl` with
full browser headers this session. The full official GfA text was instead
retrieved via a text-rendering fetch proxy (`r.jina.ai`) pointed at that exact
URL, which returns the same page rendered to clean markdown server-side. The
resulting content was cross-validated word-for-word against several
independently-fetched, non-blocked official sources (ISSN, IWA affiliation,
submission-portal URL, the 14 CRediT roles, the Highlights spec, the
graphical-abstract pixel spec) from `shop.elsevier.com` and
`elsevier.com/researcher/author/...` policy pages — all matched exactly. This
is treated as a legitimate fetch-and-read of the official page, not a
third-party summary; article-level ScienceDirect pages (e.g. the desk-rejection
editorial's DOI) remained blocked even through this proxy and were NOT
promoted beyond their Crossref bibliographic metadata.

## VERIFIED requirements (as of 2026-07-04)

Sources: [Guide for Authors](https://www.sciencedirect.com/journal/water-research/publish/guide-for-authors)
(fetched via proxy, see note above) ·
[Elsevier Shop journal page](https://shop.elsevier.com/journals/water-research/0043-1354) ·
[Official CSL dependent style: water-research.csl](https://raw.githubusercontent.com/citation-style-language/styles/master/dependent/water-research.csl) ·
[Official CSL independent style: elsevier-harvard.csl](https://raw.githubusercontent.com/citation-style-language/styles/master/elsevier-harvard.csl) ·
[Editorial Manager (journal code "wr")](https://www.editorialmanager.com/wr/default2.aspx) ·
[Elsevier CRediT policy](https://www.elsevier.com/researcher/author/policies-and-guidelines/credit-author-statement) ·
[Elsevier Highlights policy](https://www.elsevier.com/researcher/author/tools-and-resources/highlights) ·
[Elsevier Graphical Abstract policy](https://www.elsevier.com/researcher/author/tools-and-resources/graphical-abstract) ·
[Elsevier Data Statement policy](https://www.elsevier.com/researcher/author/tools-and-resources/research-data/data-statement) ·
[Elsevier double-anonymized peer review policy](https://www.elsevier.support/publishing/answer/what-are-the-requirements-for-doubleanonymized-peer-review) ·
Crossref API (bibliographic metadata only, for the desk-rejection editorial and the group's two prior WR papers).

**Publisher / journal**: Elsevier, in association with the International
Water Association (IWA). ISSN 0043-1354. Has an open-access companion
journal, **Water Research X**, which shares "the same aims and scope and
rigorous peer review" — a *different* skill/profile, not this one.

**Scope** (verbatim, official Guide for Authors): "Water Research publishes
refereed, original research papers on all aspects of the science and
technology of the anthropogenic water cycle, water quality, and its
management worldwide." Explicitly listed scope areas: treatment processes for
water/wastewater (incl. resource recovery); urban hydrology (sewers,
stormwater, green infrastructure); drinking water treatment/distribution;
potable/non-potable water reuse; sanitation, public health, risk assessment;
anaerobic digestion and solid/hazardous waste management; contaminants
(chemical, microbial, anthropogenic particles incl. nanoparticles/
microplastics) and related sensing/monitoring; anthropogenic impacts on
surface/ground/coastal/urban waters; environmental restoration; sediment-water
and water-atmosphere interfaces; mathematical modelling, systems analysis,
machine learning, big data; socio-economic/policy/regulatory studies. Full
framing in `references/editorial-framing.md`.

**Desk-rejection framing** (directly quoted from the GfA): "Water Research is
an interdisciplinary journal with an applied edge. This means that papers
that go into too many details of one of the supporting disciplines (such as
chemistry, toxicology, microbiology, material sciences, etc.) without making
a good link with water research in general may be rejected up-front." The GfA
points to a dedicated editorial on this: van Loosdrecht & Henze, "Up-front
rejections or which type of paper should I not submit to Water Research,"
*Water Research* **46**, 2487 (2012), DOI
[10.1016/j.watres.2012.01.038](https://doi.org/10.1016/j.watres.2012.01.038)
(title/authors/venue confirmed via Crossref; full text itself is behind
ScienceDirect's bot wall even through the fetch proxy — not read in full).
Also: "*Water Research*/*Water Research X* do not do pre-submission
evaluations" — authors are expected to self-assess fit against scope and
back issues before submitting.

**Manuscript types & word limits** (all four VERIFIED with exact counting
rules — see `profile.yml` `manuscript_types[]` for the full text of each):
- **Research Paper** — 8,000 words, and unusually the limit **includes
  references** ("total length of the manuscript including references must
  not exceed 8000 words"). No case studies unless of wide industry impact.
- **Review Paper** — "typically less than 12,000 words including
  references" (phrased as guidance, not an absolute cap like the Research
  Paper limit). Must be a *critical* review with a novel perspective, not a
  literature summary; cover letter must state the authors' own expertise and
  related publications and differentiate from existing reviews on the topic.
- **Making Waves** — a communication type, "usually limited to 3000 words,"
  ≤2 illustrations total, title must start with "Making Waves: ", topical
  section headings instead of Materials-and-Methods/Results-and-Discussion,
  bullet-point Conclusions, a short abstract, **up to three** Highlights
  (not the general 3–5), and **no Supplementary Information permitted**.
- **Comment / Reply** ("Discussion" article type) — ≤1,200 words each, must
  be submitted within 4 months of the original article's publication, exact
  mandated title format, accepted/rejected without corrections.

**Abstract**: general rule ≤250 words, one paragraph, factual (purpose,
principal results, major conclusions); avoid references unless essential;
avoid non-standard abbreviations. Applies to Research Paper and (by silence/
no stated override) Review Paper. Making Waves gets "a short abstract" with
no stated word count. Comments/Replies: no abstract requirement stated at
all.

**Keywords**: 1 to 7, English, avoid multi-word "and/of" phrases.

**Highlights — REQUIRED** (Elsevier-specific; not in the base contract
schema — added as a custom `highlights:` key in `profile.yml`, plus a
checklist item in `references/submission-checklist.md`): "You are required
to provide article highlights at submission." 3 to 5 bullet points, each
≤85 characters including spaces, submitted as a **separate editable file**
(not inline in the manuscript) with "highlights" in the filename. **Making
Waves overrides this to "up to three" highlights** — a documented per-type
exception, not a general relaxation.

**Graphical abstract — OPTIONAL, not required** (`toc_graphic.required:
false`, explicitly verified, not merely defaulted): "You are **encouraged**
to provide a graphical abstract at submission" — directly contrasted against
Highlights' "you are **required**." Image ≥531×1328 px (h×w) or
proportionally larger, readable at 5×13 cm (→ `width_mm: 130`,
`height_mm: 50`); preferred formats TIFF, EPS, PDF, or MS Office files. No
"dpi" figure is stated for the graphical abstract specifically (contrast
with the explicit dpi tiers given for regular manuscript figures — see
below). Uploaded as a **separate file** in the online submission system —
the GfA never describes it being inserted into the manuscript document
itself, so neither of the contract's `manuscript_placement` options
(`last-page`/`after-abstract`) applies; `render.py`'s `insert_toc_art()`
should not run for this profile.

**Peer review / blinding**: "This journal follows a single anonymized review
process" — reviewers know author identities, authors do not know reviewers'.
No double-anonymized option is mentioned anywhere in the GfA. (Elsevier's
double-anonymized option is opt-in per journal and requires checking that
journal's own GfA — checked here; WR's GfA does not offer it.) Minimum two
independent reviewers typical. Editors recuse themselves from papers they
authored or that involve family/colleagues/products they have an interest
in; one formal appeal per submission is allowed (WR-specific appeal process:
email `wr-eo@elsevier.com` with "Appeal" + manuscript number in the subject
line, ≤1 page of reasoned argument, decided within the process described on
the GfA page, appeal window 1 month from the decision).

**Line numbering**: verbatim — "Please do not include line numbering in the
manuscript file, as it will be added automatically." This is a real but
unusual result: the profile's `line_numbers: false` means **render.py must
not bake line numbers into the submitted docx**, because Elsevier's own
submission-processing pipeline adds them when generating the peer-review PDF.
It is not a claim that the reviewed PDF has no line numbers.

**Line spacing**: NOT addressed anywhere in the fetched "Writing and
formatting" section (only column layout is specified: single-column for
Word, double-column permitted only for LaTeX — a different axis from line
spacing). Stays `null` in `profile.yml`.

**Reference style — resolved via the official CSL repository, with a caveat
about the GfA's own internal contradiction**: the official CSL project's
journal-metadata-derived file
[`dependent/water-research.csl`](https://raw.githubusercontent.com/citation-style-language/styles/master/dependent/water-research.csl)
maps ISSN 0043-1354 (an exact match) to `independent-parent: elsevier-harvard`,
`citation-format: author-date` — fetched and confirmed 2026-07-04. The live
GfA page itself is internally inconsistent: it contains a "Reference style"
subsection with a generic numbered/bracket-citation example (`[1] J. van der
Geer...`) immediately followed by a SECOND, differently-formatted "Reference
style" subsection giving an author-date/Harvard example whose worked example
specifically cites *"Water Research 25 (9), 1137-1143"* — i.e. someone wrote
that example referencing the journal itself, unlike the generic fictitious
"J. Sci. Commun." example in the numbered section. Combined with the CSL
repo's authoritative ISSN-matched mapping, this is treated as: the numbered/
bracket section is unpruned generic Elsevier GfA boilerplate, and
**Elsevier-Harvard (author-date) is the actual required style** →
`assets/elsevier-harvard.csl`. The GfA also states references are NOT
strictly enforced at submission ("any style... as long as it's consistent")
and the journal's own style is applied at the proof stage — so this matters
most for the final submission-ready render, not early drafts.

**Data availability — Option A (encouraged, not mandatory)**: "For this
journal, Option A instructions... apply. This means that you are encouraged
to: deposit your research data in a relevant data repository; cite this
dataset in your article." Not a mandatory statement (contrast with journals
using Elsevier's stricter Option B/C tiers). Custom `data_availability:` key
in `profile.yml`.

**CRediT authorship statement — REQUIRED**: "Corresponding authors are
required to acknowledge co-author contributions using CRediT... roles" — the
14-role taxonomy is given explicitly on the GfA page (see `profile.yml`
`credit_authorship_statement.roles`). Custom key, since CRediT has no slot in
the base contract schema.

**Declaration of Competing Interests — REQUIRED for every submission**
(even when there is nothing to declare): completed via Elsevier's
`declarations.elsevier.com` tool; the resulting Word document is uploaded as
a **separate file** at the "attach/upload files" submission step (not typed
into the manuscript body); no author signatures required. Custom key.

**Declaration of generative AI use — required only if AI tools were used**:
placed in a new section titled "Declaration of generative AI and
AI-assisted technologies in the manuscript preparation process," positioned
before the References list, added at first submission (not revision-only).
Silent if nothing to disclose. Basic grammar/spelling tools and accessibility
assistive tech are explicitly exempted from disclosure. Full policy deferred
to Elsevier's [generative AI policies for journals](https://www.elsevier.com/about/policies-and-standards/generative-ai-policies-for-journals)
(not independently fetched this session — GfA excerpt is the verified
source).

**Figures**: resolution tiers by artwork type — color/grayscale halftones
≥300 dpi (single-column ≥1063 px, full-page ≥2244 px); bitmapped line
drawings ≥1000 dpi (single-column ≥3543 px, full-page ≥7480 px); combination
bitmapped line/halftone ≥500 dpi (single-column ≥1772 px, full-page
≥3740 px). Vector artwork as EPS/PDF with fonts embedded or converted to
outlines. Text graphics may be embedded inline; all figures/images must also
be supplied as separate files. No RGB-vs-CMYK statement, no explicit
free-of-charge-in-print-color statement, no sans-serif figure-lettering rule
found (all three stay open, see TO VERIFY).

**Tables**: submit as editable text (never as images); place next to
relevant text or at the end; number consecutively; caption with the table;
notes go BELOW the table body, not in the caption; avoid vertical rules and
cell shading; use sparingly (don't duplicate data shown elsewhere).

**Supplementary material**: submitted alongside the manuscript at initial
submission; after that, can only be added/replaced at the revision stage;
NOT typeset by production — published online exactly as received; no
file-format restriction stated (PDF is not required). **Not admissible for
the Making Waves article type.** No SI cover-sheet, internal-TOC, or
page-prefix convention was found (stays open, see TO VERIFY).

**Submission portal**: [https://submit.elsevier.com/WR](https://submit.elsevier.com/WR)
— stated directly in the Guide for Authors ("Please follow this link to
submit your paper"); this is Elsevier's Editorial Manager, journal code
`wr`, independently cross-checked by fetching
`editorialmanager.com/wr/default2.aspx` directly and confirming "Water
Research" branding in the raw HTML (that generic entry page also shows a
"Site under development. Do not use for live manuscript submission" banner —
likely boilerplate for the credential-less default entry point rather than
evidence the real portal is unavailable, since the GfA's own submission link
points at the same journal code; noted for transparency, not treated as
contradicting the GfA's explicit submission link).

**Continuity angle for this manuscript's cover letter**: the group has two
directly relevant prior Water Research publications, confirmed via Crossref
bibliographic metadata (not read in full — ScienceDirect article pages are
blocked): "Autonomous water quality management in an electrochemical
desalination process," *Water Research* **280**, 123521 (2025-07), DOI
[10.1016/j.watres.2025.123521](https://doi.org/10.1016/j.watres.2025.123521);
and "On-device artificial intelligence agent based on language models for
electrochemical water desalination," *Water Research* **301**, 125995
(2026-08), DOI
[10.1016/j.watres.2026.125995](https://doi.org/10.1016/j.watres.2026.125995).
A reproduction-and-correction submission in the same journal as these two
prior papers is a genuine editorial-fit and track-record argument — expand
in `references/editorial-framing.md` and the cover-letter draft.

## TO VERIFY (not addressed in any fetched official page — check before submission)

- [ ] Line spacing (single vs double) — tried 2026-07-04: fetched and read
      the full "Writing and formatting" section of the Guide for Authors;
      only column layout (single-column Word / double-column LaTeX-only) is
      specified, never line spacing.
- [ ] SI page-numbering prefix (e.g. "S1, S2…"), internal SI table of
      contents, and SI cover sheet — tried 2026-07-04: fetched and read the
      "Supplementary material" section in full; none of these three is
      addressed.
- [ ] Figure color space (RGB vs CMYK) and whether color reproduction is
      free of charge in print — tried 2026-07-04: fetched and read the
      "Color artwork" and "Formats" sections in full; neither is stated
      (only that accepted color figures "will appear in color online").
- [ ] Sans-serif figure-lettering rule (font/size for text baked into
      figure images) — tried 2026-07-04: fetched and read "Figures, images
      and artwork" and "Formats" sections in full; not addressed (contrast
      with npj Clean Water, which does specify this).
- [ ] Manuscript body font/point size — tried 2026-07-04: fetched and read
      the full "Writing and formatting" section; not addressed anywhere
      (Word files must be "editable" and single-column; no font/size
      stated).
- [ ] Revision word-count-overrun rule (cf. ES&T's "must not exceed the
      submitted count, with justification") — tried 2026-07-04: not found
      anywhere in the fetched Guide for Authors.
- [ ] Graphical abstract minimum dpi as an explicit figure (the GfA gives a
      physical readable size, 5×13 cm, and a pixel count, but never states
      "dpi" for this asset specifically) — tried 2026-07-04.
- [ ] Full text of the desk-rejection editorial (van Loosdrecht & Henze,
      2012, DOI 10.1016/j.watres.2012.01.038) — tried 2026-07-04: blocked by
      ScienceDirect's bot wall even through the fetch proxy used for the GfA
      page itself; only Crossref bibliographic metadata (title/authors/
      venue) was confirmed, plus the GfA's own paraphrase/quote of its
      thesis.
- Rule: each checked item moves UP into VERIFIED with a link, and its number
  lands in `profile.yml`; update `verified_date`.

## Quarto/DOCX implementation notes for this journal

- `assets/reference.docx` is generated by `scripts/build_reference_docx.py`
  from a fresh `quarto pandoc --print-default-data-file reference.docx`,
  restyled to Times New Roman — 12pt body/headings, 10pt captions. No WR
  body-font/point-size requirement was found during verification (see TO
  VERIFY) — this is the same standard, portal-safe serif default used by
  `quarto-manuscript-est` and `quarto-manuscript-npjcw`. Re-run the builder
  script when requirements change; never hand-edit the `.docx`.
- Line numbers: `line_numbers: false` here means render.py must NOT insert
  line numbers into the `--target submission` docx — Water Research's own
  submission-processing system adds them automatically. Do not treat this
  the same as ES&T's "not required at all."
- No TOC-art insertion logic applies to this profile even though
  `toc_graphic` is optional-not-required: the graphical abstract, when
  produced, is uploaded as a separate file to Editorial Manager, never
  inserted into the manuscript document — `render.py`'s `insert_toc_art()`
  should not run for `--target submission` under this profile regardless of
  whether a graphic file is present.
- Word count: `validate.py`'s word-limit check should be aware that the
  Research Paper and Review Paper limits (8,000 / ~12,000 words) INCLUDE the
  reference list — a materially different counting rule from ES&T/ACS (which
  excludes references). `references/submission-checklist.md` flags this
  explicitly as a HARD gotcha.
- Highlights and the Declaration of Competing Interest are both submitted as
  SEPARATE FILES outside the main manuscript docx (not sections rendered
  inside `index.qmd`) — any future authoring tooling for this profile should
  treat them as sibling deliverables, not manuscript sections, unlike
  Acknowledgements/CRediT which likely live inside the manuscript body.

## Files in this profile

- `profile.yml` — machine-readable; ONLY verified numbers, plus a small set
  of Elsevier-specific custom keys (`highlights`, `credit_authorship_statement`,
  `declaration_of_competing_interest`, `data_availability`,
  `generative_ai_declaration`) beyond the base contract schema
- `scripts/build_reference_docx.py` — reproducible builder for the generated
  `assets/reference.docx`; re-run it when requirements change (never
  hand-edit the .docx)
- `assets/reference.docx` — generated by `scripts/build_reference_docx.py`;
  never hand-edit
- `assets/elsevier-harvard.csl` — fetched 2026-07-04 from the official CSL
  styles repository
  (https://raw.githubusercontent.com/citation-style-language/styles/master/elsevier-harvard.csl),
  identified as Water Research's style via the official CSL project's own
  ISSN-matched dependent-style file (`dependent/water-research.csl`)
- `references/submission-checklist.md` — S5 gate list, HARD/SOFT
- `references/editorial-framing.md` — scope, desk-rejection framing, and the
  cover-letter continuity angle (prior WR papers 280:123521 and 301:125995)
