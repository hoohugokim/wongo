# Water Research editorial framing

Source: [Guide for Authors](https://www.sciencedirect.com/journal/water-research/publish/guide-for-authors),
fetched and read in full 2026-07-04 (see SKILL.md for the fetch-method note —
ScienceDirect blocks direct automated fetches with a CAPTCHA wall; content
was retrieved via a text-rendering proxy and cross-validated against several
independently-fetched official Elsevier pages). Supplemented by
[shop.elsevier.com's journal page](https://shop.elsevier.com/journals/water-research/0043-1354)
and Crossref bibliographic metadata for two cited papers.

## What the journal says it wants

Verbatim: "Water Research publishes refereed, original research papers on
all aspects of the science and technology of the anthropogenic water cycle,
water quality, and its management worldwide." Explicitly listed scope areas
(broad outline, not exhaustive):
- Treatment processes for water and wastewaters (municipal, agricultural,
  industrial, on-site), including resource recovery and residuals management.
- Urban hydrology: sewer systems, stormwater management, green infrastructure.
- Drinking water treatment and distribution.
- Potable and non-potable water reuse.
- Sanitation, public health, and risk assessment.
- Anaerobic digestion, solid and hazardous waste management (source
  characterization, leachate/gaseous-emission effects and control).
- Contaminants (chemical, microbial, anthropogenic particles such as
  nanoparticles or microplastics) and related sensing/monitoring/fate work.
- Anthropogenic impacts on inland, tidal, coastal, and urban waters
  (surface and groundwater; point and non-point pollution sources).
- Environmental restoration linked to surface water, groundwater, and
  groundwater remediation.
- Sediment-water and water-atmosphere interfaces, with an anthropogenic-
  impact focus.
- Mathematical modelling, systems analysis, machine learning, and beneficial
  use of big data related to the anthropogenic water cycle.
- Socio-economic, policy, and regulatory studies.

Audience: "Biologists, chemical engineers, chemists, civil engineers,
environmental engineers, limnologists, and microbiologists" — genuinely
interdisciplinary, not a single-discipline journal.

**Explicit editorial caution**: "Water Research is an interdisciplinary
journal with an applied edge. This means that papers that go into too many
details of one of the supporting disciplines (such as chemistry, toxicology,
microbiology, material sciences, etc.) without making a good link with water
research in general may be rejected up-front." The GfA points readers to a
dedicated editorial: van Loosdrecht & Henze, "Up-front rejections or which
type of paper should I not submit to Water Research," *Water Research*
**46**, 2487 (2012), DOI
[10.1016/j.watres.2012.01.038](https://doi.org/10.1016/j.watres.2012.01.038)
(title/authors/venue confirmed via Crossref API this session; the full text
is behind ScienceDirect's bot wall even through the fetch proxy used for the
GfA itself, so only the GfA's own paraphrase of its thesis is used here, not
the editorial's full argument).

**No pre-submission evaluation service**: "Water Research/Water Research X
do not do pre-submission evaluations. Please carefully review the journal
scope and previous issues of the journals to assess the fit of your
manuscript." — authors bear full responsibility for a scope self-check
before submitting; there is no informal "does this fit?" query mechanism.

**Applied, not purely disciplinary, framing**: the journal explicitly favors
manuscripts that connect specialist depth (chemistry, microbiology, materials
science, modelling, etc.) back to water-system relevance, rather than
treating water as an incidental application domain for another field's
methods.

## Fit argument for an a water-treatment application LLM benchmark / correction paper

Two explicitly named scope items map directly onto this manuscript's domain:
"Mathematical modelling, systems analysis, machine learning, and beneficial
use of big data related to the anthropogenic water cycle" (an LLM agent for
electrochemical desalination control sits squarely here) and the broader
"anthropogenic water cycle" framing that covers desalination as a treatment/
resource-recovery process. The desk-rejection caution above cuts the other
way if the manuscript reads as primarily an LLM/ML methods paper with only
incidental water framing — the applied link to electrochemical desalination
performance, data, and operational relevance must be made explicit and
central, not appended.

**Continuity / track-record angle for the cover letter**: the group has two
directly relevant prior publications in this exact journal, both confirmed
via Crossref bibliographic metadata (not read in full — ScienceDirect
article pages are blocked):

- "Autonomous water quality management in an electrochemical desalination
  process," *Water Research* **280**, 123521 (published 2025-07), DOI
  [10.1016/j.watres.2025.123521](https://doi.org/10.1016/j.watres.2025.123521).
- "On-device artificial intelligence agent based on language models for
  electrochemical water desalination," *Water Research* **301**, 125995
  (published 2026-08), DOI
  [10.1016/j.watres.2026.125995](https://doi.org/10.1016/j.watres.2026.125995).

A manuscript that reproduces and/or corrects results building on this pair —
submitted to the *same* journal — is a genuine editorial-fit asset: it
demonstrates sustained engagement with Water Research's readership and
editorial line on LLM/AI-for-desalination work, not a first-time or
opportunistic submission. Cite both explicitly in the cover letter as prior
art and track record, and be explicit about what the new manuscript adds
relative to each (reproduction scope, corrected finding, extended benchmark,
etc.) rather than gesturing at "our prior work" generally.

## Desk-screen considerations (from journal structure, not stated explicitly
as a rejection rubric — treat as judgment, not a hard rule)

- Article type choice matters: a manuscript reproducing/correcting prior
  results with new data and evaluation belongs in **Research Paper**, not
  **Making Waves** (which is for opinion/perspective communications, not
  substantive original research) or **Comment** (which is specifically for
  short critiques of a *specific* prior published paper within 4 months of
  its publication, not a standalone reproduction study).
- If reproducing/correcting the group's own prior WR papers specifically
  (rather than critiquing another group's), the "Comment on..." mechanism
  (with its 4-month window and 1,200-word cap) is very unlikely to fit —
  Research Paper is the appropriate type, with the relationship to the two
  prior papers made explicit in the introduction and cover letter instead.
- No npj/ES&T-style formal "novelty rubric" was found in the fetched GfA
  beyond the interdisciplinary-applied-link caution above; treat the
  desk-rejection editorial (van Loosdrecht & Henze 2012) as the operative
  guidance once/if its full text becomes accessible.

## Open item

The full text of the 2012 desk-rejection editorial was not accessible this
session (ScienceDirect article pages remain blocked even through the fetch
proxy that worked for the Guide for Authors page itself). If access becomes
available, mine it for concrete examples of rejected-without-review paper
patterns and fold them into the desk-screen section above.
