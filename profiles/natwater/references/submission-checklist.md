# Nature Water submission gate (S5) — HARD/SOFT

HARD:
- [ ] Word count within limit for the declared `ms_type`, per counting_rule.
      VERIFIED 2026-07-04: Article 3,000 / Analysis 4,000 / Perspective
      4,000 / Review 6,000 / Comment 2,000 / Correspondence 300-800 (both
      bounds live) / Matters Arising 1,200 — ALL excluding
      abstract/Methods/references/figure legends. Unlike npj Clean Water,
      EVERY type here has a real numeric cap; none is "no stated limit."
      See `profile.yml` `manuscript_types[].counting_rule`.
- [ ] Content type matches the manuscript's content, not just its length.
      VERIFIED 2026-07-04: Analysis explicitly permits "a new analysis of
      existing data... a comparative analysis... a new simulation or model"
      — the best fit for a benchmark/comparative-evaluation study. Perspective
      and Review BOTH explicitly FORBID primary/unpublished research data —
      do not misclassify an original-data manuscript as either, even if the
      word count would otherwise fit. See `references/editorial-framing.md`.
- [ ] Abstract within limit and structure: Article <=150 words unreferenced;
      Analysis/Perspective 100-150 words unreferenced; Review <=150 words
      unreferenced; Matters Arising = a brief non-specialist summary
      paragraph (no numeric cap stated). VERIFIED 2026-07-04 (Content types
      page).
- [ ] Section order matches the verified Article/Analysis structure:
      Introduction (no heading) / Main text / Discussion-Conclusions (no
      subheadings) / Methods / Data availability / Code availability /
      Acknowledgements / Author contributions / Competing interests /
      References / Figure legends / Extended Data (if used). VERIFIED
      2026-07-04. Note the Data-availability-before-Tables/Figure-legends
      ordering comes from AIP-and-formatting's reference-numbering sequence,
      not from Content types alone.
- [ ] Data Availability Statement present, describing access to the
      "minimum dataset." Mandatory for every manuscript reporting original
      research. VERIFIED 2026-07-04.
- [ ] Code Availability statement present under "Code availability" (placed
      after Data availability, before References) if custom code/algorithm
      is central to the main claims. VERIFIED 2026-07-04. Nature Water does
      NOT perform formal peer review of code/algorithms (not on the short
      list of Nature-brand titles that do) — code availability disclosure is
      required, but not a code-review gate.
- [ ] No TOC/graphical abstract required or expected — do NOT block on a
      missing graphic; this journal has none (distinct from the optional,
      editor-run "Cover artwork" issue-cover contest). VERIFIED ABSENT
      2026-07-04 (`profile.yml` `toc_graphic.required: false`).
- [ ] References: numbered sequentially across Main
      Text/Methods/Data-Availability/Tables/Figure-Legends/Box/Extended-Data,
      in that fixed order; one publication per reference; footnotes not
      supported; article titles REQUIRED for long-form types (Article,
      Analysis, Perspective, Review) and OMITTED for short types (Comment,
      Correspondence); journal names italicized. All citekeys resolve
      against `assets/nature.csl`. VERIFIED 2026-07-04.
- [ ] Figure legends state centre-value definition, error-bar definition,
      sample size (n), statistical test, and P values; multi-panel figures
      use verbal cues, not symbols, for keys; legend length rides on the
      manuscript type's own word limit (no separate flat cap). VERIFIED
      2026-07-04.
- [ ] Figures >=300 dpi, <=180 mm width, 5-7 pt sans-serif labelling.
      VERIFIED 2026-07-04.
- [ ] Extended Data (if used): <=10 items, each cited as a discrete item in
      the main text, sized to one PDF page. VERIFIED 2026-07-04. This is a
      Nature-brand-specific structural element with no npj Clean Water
      analog — do not skip it when porting logic from that profile.
- [ ] SI (if present): single combined PDF preferred; complex/oversized
      tables or data may go out separately as Excel/.csv files named
      "Supplementary Tables"/"Supplementary Data"; every SI item cited at
      least once in sequence using the word "Supplementary." UNLIKE npj
      Clean Water, Nature Water explicitly PERMITS a "Supplementary Note"
      for extra methodological detail (algorithms, protocols, synthesis) —
      do not apply npj Clean Water's "no Supplementary Methods" rule here.
      VERIFIED 2026-07-04. SI cover sheet and page-numbering-prefix
      requirements are UNCONFIRMED (see SKILL.md TO VERIFY).
- [ ] ORCID on file for the corresponding author before final submission
      (cannot be edited at proof stage). VERIFIED 2026-07-04.
- [ ] Competing Interests statement present for every author (or an
      explicit "no competing interests" statement). VERIFIED 2026-07-04
      (general Nature Portfolio requirement, explicitly stated as mandatory
      for Matters Arising and standard practice for all research types).
- [ ] Author Contributions statement present, referring to each author
      individually. VERIFIED 2026-07-04.
- [ ] Cover letter present; explains importance/fit for Nature Water's
      diverse readership; discloses related manuscripts under consideration
      or in press elsewhere and any prior discussions with a Nature Water
      editor; if double-anonymized peer review is chosen, author names and
      affiliations go in the COVER LETTER, not the manuscript file.
      VERIFIED 2026-07-04.
- [ ] If double-anonymized peer review is requested: manuscript file itself
      conceals all author identities (per the linked checklist PDF); box
      ticked in the manuscript tracking system at submission. Author is
      solely responsible — not checked by the editor. VERIFIED 2026-07-04.
- [ ] Any LLM use in preparing the manuscript TEXT is documented in the
      Methods section (per the AI editorial policy) — separate from this
      manuscript's own subject matter, which is a benchmark OF LLMs, not
      LLM-assisted authorship. VERIFIED 2026-07-04.
- [ ] Manuscript file format at initial submission: PDF, Word, or compiled
      PDF from TeX/LaTeX. At acceptance: Word or TeX/LaTeX ONLY — no PDF
      accepted for final submission. VERIFIED 2026-07-04.
- [ ] Open-access route decided before acceptance: subscription (default,
      no charge) or Gold OA (APC £9,390/$12,850/€10,850) — ONLY for primary
      types (Article, Analysis); Perspective/Review/Comment/Correspondence
      are NOT eligible for Gold OA regardless of preference. VERIFIED
      2026-07-04.
SOFT:
- [ ] Reporting Summary prepared if the manuscript falls in life sciences,
      behavioural & social sciences, or ecology/evolution/environmental
      sciences (or named physical-sciences sub-areas: solar cells, lasing
      claims). VERIFIED 2026-07-04 for the general policy; applicability to
      an engineering/CS-adjacent LLM-benchmark-for-water-technology
      manuscript is a JUDGMENT CALL, not a verified exemption — flag for
      human review rather than auto-skip.
- [ ] Editorial Policy Checklist — confirmed REQUIRED only for life-sciences
      Matters Arising contributions with new data; applicability to ordinary
      Article/Analysis submissions is UNCONFIRMED (see SKILL.md TO VERIFY).
- [ ] Suggested/excluded reviewers drafted for the cover letter (optional,
      "often helpful, although not always followed").
- [ ] APC waiver / institutional open-access agreement checked via the
      Open access funding institution look-up tool, if pursuing Gold OA.
- [ ] Preprint posting decision made (explicitly permitted/encouraged; does
      not count as prior publication or affect the novelty assessment).
- [ ] Transparent peer review opt-in decision made — offered AFTER peer
      review completes, before acceptance; not mandatory for Nature Water.
- [ ] Source Data prepared for figures where applicable (unprocessed
      gels/blots as per-figure PDFs; statistics source data as per-figure
      Excel files) — encouraged, not universally mandatory.
Open items remaining (see SKILL.md TO VERIFY queue): manuscript body line
spacing, line numbers, body font/point size, table border/caption-position
convention, general Editorial Policy Checklist applicability, Reporting
Summary applicability to this manuscript's discipline, and the unresolved
Review-type presubmission-enquiry contradiction between two of the
journal's own pages.
