# Nature Water editorial framing

Sources: [Aims & Scope](https://www.nature.com/natwater/aims),
[Journal information](https://www.nature.com/natwater/journal-information),
[Journal metrics](https://www.nature.com/natwater/journal-impact),
[Content types](https://www.nature.com/natwater/content),
[Editorial process & peer review](https://www.nature.com/natwater/submission-guidelines/editorial-process),
all fetched and read in full 2026-07-04.

## What the journal says it wants

Verbatim: "Nature Water covers all aspects of research that are connected to
this evolving relationship between society and water resources." Publishing
monthly, exclusively online, in three broad areas: natural sciences
(primarily Earth and environmental science), engineering (environmental,
civil, chemical, materials), and social sciences (economics, human
geography, sociology) — "with a particular interest in regards to
interdisciplinary research." Explicitly named topics (Aims & Scope, not
exhaustive) include water resources science, hydrology, climate-change
effects on water resources, water pollution monitoring, water and
wastewater treatment, desalination, large water infrastructure, water
governance and management, water distribution, water security, and water/
sanitation economics, policy, and justice.

## Selectivity context (why this journal is a different tier than npj Clean Water)

Nature Water is a Nature-BRAND flagship-tier research journal, not an
npj-series spinoff: "Like other journals in the Nature family, Nature Water
has no external editorial board... all editorial decisions are made by a
dedicated team of full-time professional editors" (Editorial process page).
2025 Journal Impact Factor: **30.7** (5-year JIF also 30.7); SNIP 3.795; SJR
5.735 (Journal metrics page). Median submission-to-first-decision: 6 days;
median submission-to-acceptance: **141 days**. The editorial-process page's
own description of desk-screening is explicit and blunt: "Those papers
judged by the editors to be of insufficient general interest or otherwise
inappropriate are rejected promptly without external review." Criteria for
publication: "a paper should represent an advance in understanding likely
to influence thinking in the field, with strong evidence for their
conclusions. There should be a discernible reason why the work deserves the
visibility of publication in a Nature Portfolio journal rather than the best
of the specialist journals." This is a materially higher bar than npj Clean
Water, which carries no comparable JIF tier and is explicitly positioned as
"a fully open-access and more inclusive platform" for Nature Portfolio
authors (npj Clean Water's own Aims & Scope). Set expectations accordingly
in any cover letter: Nature Water desk-rejects on "not enough general
interest," not just on technical soundness.

## Corrected content-type recommendation: Analysis, not Perspective

The user's own project review flagged this manuscript (an LLM benchmark for
a water-treatment application) as fitting Nature Water only as "Analysis/Perspective."
Having now read Nature Water's own Content types page in full, **Perspective
is very likely NOT a viable format for a manuscript reporting original
benchmark results**:

> "A Perspective is a review of a topic from a personal viewpoint... They
> may be more forward-looking and/or speculative than Reviews... **Perspectives
> may not contain primary research data.**"

An LLM benchmark study — running models against a water-treatment application tasks and
reporting their comparative performance — generates original, previously
unpublished primary research data (the benchmark results themselves). That
places it outside Perspective's own stated boundary, regardless of length
fit (both are ~4,000 words). The same "no primary research data" constraint
also rules out Review ("Unpublished primary research data are not permitted
in Reviews").

**Analysis is the better-fitting, and likely the ONLY correctly-fitting,
non-Article format** — its own definition on the Content types page reads:

> "An Analysis is a new analysis of existing data, describes new data
> obtained in a comparative analysis or introduces a new simulation or model
> that leads to novel and arresting conclusions of importance to a broad
> audience. Systematic reviews or meta-analyses of primary research
> literature can also be accommodated by this format."

"New data obtained in a comparative analysis" is close to a verbatim
description of a benchmark study: multiple LLMs evaluated comparatively
against a shared task set (a water-treatment application), producing new performance
data and (presumably) actionable conclusions for the water-technology
community. Analysis also allows a larger main-text budget (4,000 words, up
to 8 display items, abstract 100-150 words) than Perspective's now-ruled-out
4,000/5-display-item envelope, and — unlike Perspective — Analysis is NOT
asterisked as non-primary on the Content types page, meaning it remains
ELIGIBLE for Gold Open Access if that route is wanted.

**Article remains the fallback general-purpose option** ("Nature Water
publishes original research in one format, Article, which may range from
what are typically considered to be short 'communications', through to more
in-depth studies") but its tighter 3,000-word / 7-display-item envelope and
up-to-150-word abstract are a harder fit for a benchmark paper with
multiple models × multiple task conditions to report; Analysis's larger
budget is the more comfortable choice. Recommend leading with **Analysis**
in the cover letter and initial content-type selection, not Perspective.

## Fit argument against the explicit scope list

Two of Aims & Scope's named topics anchor the fit: "Desalination" (electrochemical water treatment is a
desalination technology) and the engineering dimension of "Water and
wastewater treatment" — an LLM benchmark for a desalination technology sits
squarely inside the engineering bucket the journal explicitly claims
("engineering (including environmental, civil, chemical and materials
engineering)"), with an interdisciplinary AI-for-water-technology angle that
matches the journal's stated "particular interest in regards to
interdisciplinary research."

No directly on-topic LLM-benchmark-for-water-technology precedent paper was
found published in Nature Water itself during this verification pass (unlike
npj Clean Water, which has a confirmed precedent: "Towards domain-adapted
large language models for water and wastewater management," npj Clean Water
8, 82 (2025)). Do not claim a Nature Water precedent that wasn't found and
verified — if the cover letter wants a precedent citation, use the npj Clean
Water paper as evidence of adjacent-journal appetite for the topic while
being explicit that it was published in a different (lower-tier, fully-OA)
Nature Portfolio title, not Nature Water itself. This is an open item, not
a resolved fact — a targeted search of Nature Water's own back catalogue for
AI/ML-for-water papers would need to happen before making a stronger
precedent claim.

## Desk-screen considerations (inferred from journal structure and the
editorial-process page's own language, not a formal rubric — treat as
judgment, not a rule)

- The "insufficient general interest... rejected promptly without external
  review" language is Nature Water's own, not inferred — lean on framing the
  water-technology + AI-benchmark angle as broadly interesting to the
  journal's explicitly interdisciplinary (natural science / engineering /
  social science) readership, not just to a desalination-engineering niche.
- The journal explicitly separates primary-research formats (Article,
  Analysis — both OA-eligible) from non-primary commissioned/opinion formats
  (Review, Perspective, Comment, Correspondence, News & Views, Policy Brief,
  Feature, Q&A, World View — all asterisked, subscription-only, "should not
  include original... research findings"). An LLM benchmark study with
  original evaluation data belongs unambiguously on the primary-research
  side (Article or Analysis), never on the commissioned/opinion side,
  regardless of length.
- The AI editorial policy explicitly distinguishes AI-as-authorship-tool
  (restricted, must be disclosed if used to help write the manuscript text)
  from AI-as-subject-of-study (this manuscript's actual topic — benchmarking
  LLMs against a water-treatment application tasks). Make this distinction explicit in
  the cover letter so editors don't conflate "a paper about LLMs" with "a
  paper written by an LLM."
- No stated novelty/significance rubric beyond the general "advance in
  understanding... discernible reason [to publish] in a Nature Portfolio
  journal rather than the best of the specialist journals" (Editorial
  process page) — this is the operative desk-screen bar; the cover letter
  should make the "why here, not a specialist water-tech journal" case
  explicitly, leaning on the interdisciplinary AI + desalination-engineering
  framing.

## Open items

- No Nature Water back-catalogue search for AI/ML-for-water precedent papers
  was performed during this verification pass (only the npj Clean Water
  precedent was already known from that profile's own research) — a
  targeted nature.com search within `/natwater/` for LLM/AI/machine-learning
  content would strengthen the cover letter's "editorial appetite" argument
  if a genuine Nature Water precedent exists.
- The unresolved Review-type presubmission-enquiry contradiction (see
  SKILL.md TO VERIFY) does not affect Analysis/Article submissions, which do
  not require or reference a presubmission enquiry anywhere in the fetched
  guidance.
