# npj Clean Water submission gate (S5) — HARD items block submission render

HARD:
- [ ] Word count within limit for the declared `ms_type`, per counting_rule.
      VERIFIED 2026-07-04: Article has NO stated main-text limit (npj Series
      "does not impose strict limits on word count or page numbers"); Brief
      Communication 1,000-1,500, Comment ~1,000-2,000, Matters Arising
      <=1,200, Perspective <=3,000, Review 3,000-4,000, Editorial no stated
      limit — ARE verified hard-ish guidance numbers. See `profile.yml`
      `manuscript_types[].counting_rule`.
- [ ] Abstract within limit and structure: Article <=150 words / no
      subheadings; all other peer-reviewed types <=70 words / no
      subheadings. VERIFIED 2026-07-04 (Content types page).
- [ ] Section order matches the verified Article structure: Title / Abstract
      / Introduction / Results / Discussion / Methods / Data availability /
      Code availability / Acknowledgments / Author contributions /
      Competing interests / References / Figure legends. Discussion must
      NOT contain its own subheadings, a "Limitations" section, or a
      "Conclusions" section — VERIFIED 2026-07-04.
- [ ] Data Availability Statement present as its own "Data Availability"
      heading, after Methods and before References. Mandatory for every
      submission. VERIFIED 2026-07-04.
- [ ] Code Availability statement present under "Code availability" if
      custom code central to the main claims was used. VERIFIED 2026-07-04.
- [ ] No TOC/graphical abstract required or expected — do NOT block on a
      missing graphic; this journal has none. VERIFIED ABSENT 2026-07-04
      (`profile.yml` `toc_graphic.required: false`).
- [ ] References: standard Nature referencing style, numbered by order of
      first appearance, no footnotes, >5 authors -> first author + "et al.",
      journal names italicized/abbreviated, volume number bold. All
      citekeys resolve against `assets/nature.csl`. VERIFIED 2026-07-04.
- [ ] Figure legends <=350 words per figure, placed after the reference
      list in the main manuscript file; multi-panel figures on one page
      labeled a), b), c). VERIFIED 2026-07-04.
- [ ] SI (if present): combined into a single, separate file, preferably
      PDF; contains NO Supplementary Methods (all Methods must be in the
      main manuscript); oversized tables/spreadsheets provided separately
      as "Supplementary Data XX" (not "Supplementary Table"). VERIFIED
      2026-07-04. SI cover sheet and page-numbering-prefix requirements are
      UNCONFIRMED (see SKILL.md TO VERIFY) — do not fabricate an S1/S2
      scheme for this journal without re-checking.
- [ ] ORCID on file for the corresponding author before final submission
      (cannot be edited at proof stage). VERIFIED 2026-07-04.
- [ ] Competing Interests statement present for every author (or an
      explicit "no competing interests" statement). Mandatory even when
      none exist. VERIFIED 2026-07-04.
- [ ] Author Contributions statement present, referring to each author
      individually by initials. Mandatory. VERIFIED 2026-07-04.
- [ ] Cover letter present; does not repeat the abstract/introduction;
      includes corresponding-author contact info; discloses any related
      manuscripts under consideration/in press elsewhere. VERIFIED
      2026-07-04.
- [ ] Any LLM use in preparing the manuscript text is documented in the
      Methods section (per the AI editorial policy) — separate from this
      manuscript's own subject matter, which is a benchmark OF LLMs, not
      LLM-assisted authorship. VERIFIED 2026-07-04.
SOFT:
- [ ] Reporting Summary + Editorial Policy Checklist prepared (required
      after peer review for Life/Health/Earth-Environmental/Social-
      Behavioural Sciences research articles; encouraged, not mandatory, at
      initial submission). VERIFIED 2026-07-04.
- [ ] Suggested/excluded reviewers drafted for the cover letter.
- [ ] APC waiver eligibility checked BEFORE submission if relevant — waiver
      requests made during review or after acceptance are not considered.
      VERIFIED 2026-07-04.
- [ ] Preprint posting decision made (explicitly permitted/encouraged).
Open items remaining (see SKILL.md TO VERIFY queue): double-anonymized
peer-review option availability for this specific journal, line spacing,
line numbers, SI pagination prefix, SI internal table of contents, SI cover
sheet, manuscript body font/point size, table border/caption-position
convention.
