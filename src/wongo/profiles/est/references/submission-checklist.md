# ES&T submission gate (S5) — HARD items block submission render

HARD:
- [ ] Word count <= limit for declared ms_type, per counting_rule. VERIFIED
      2026-07-03: count spans Abstract through end of main text (abstract +
      body + graphic titles/footnotes/captions); references and all
      front/back matter (title, authors, affiliations, TOC graphic, figures,
      tables, reference list, SI file-list, acknowledgments, notes) are
      excluded — figures/tables carry NO separate word-count equivalent.
      Exception: Correspondence/Rebuttal's 1,000-word limit INCLUDES
      citations. See `profile.yml` `manuscript_types[].counting_rule`.
- [ ] TOC art present: standalone file + placed on the LAST PAGE of the
      manuscript, labeled "For Table of Contents Only" (also uploadable
      separately as "Graphics for manuscript"). VERIFIED 2026-07-04 against
      the official "Guidelines for Table of Contents/Abstract Graphics" PDF
      (dated 2024-02-28; local copy `archive/toc_abstract_graphics_guidelines.pdf`):
      area no larger than 3.25 in × 1.75 in (82.55 mm × 44.45 mm); TIF at
      300 dpi (color) or 1200 dpi (black-and-white), or EPS in RGB document
      color mode with fonts outlined/embedded; sans serif type, preferably
      8 pt, minimum 6 pt; entirely original unpublished artwork by a
      coauthor; no photos/drawings/caricatures of people; no stamps,
      currency, trademarks, or logos; must not duplicate a figure already in
      the manuscript text. No synopsis/word-count requirement exists in this
      guidance.
- [ ] SI: separate file, S-pagination, cover sheet, availability paragraph
      after Acknowledgments. VERIFIED 2026-07-03: SI does NOT have to be
      PDF-only (DOC/DOCX is an accepted format per official example
      descriptions). Whether SI needs its own internal table of contents is
      still unconfirmed (not addressed in fetched guidance).
- [ ] All citekeys resolve; references complete per ACS style
- [ ] Cover letter present, includes environmental-significance framing
- [ ] Funding + ORCID metadata block complete
SOFT:
- [ ] Suggested reviewers list drafted
- [ ] Novelty statement sanity check vs editorial-framing.md
- [ ] AI-use disclosure per current ACS policy
Open items remaining (see SKILL.md TO VERIFY queue): figure color space
(RGB vs CMYK) for regular in-text figures, table border/caption/footnote-
marker convention, SI internal table-of-contents requirement, manuscript
line spacing.
