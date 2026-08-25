# Water Research submission gate (S5) — HARD items block submission render

HARD:
- [ ] Word count within limit for the declared `ms_type`, per counting_rule
      — **GOTCHA**: for Research Paper (8,000 words) and Review Paper
      (~12,000 words), the limit INCLUDES the reference list, unlike ES&T/
      ACS conventions which exclude references. Making Waves ≤3,000 words +
      ≤2 illustrations total; Comment/Reply ≤1,200 words each. VERIFIED
      2026-07-04 from the official Guide for Authors. See `profile.yml`
      `manuscript_types[].counting_rule`.
- [ ] Abstract ≤250 words (Research Paper, Review Paper); Making Waves gets
      a "short abstract" (no fixed count); Comment/Reply has no stated
      abstract requirement. VERIFIED 2026-07-04.
- [ ] Highlights present: 3-5 bullet points (Making Waves: up to 3 only),
      each ≤85 characters including spaces, submitted as a SEPARATE
      EDITABLE FILE (not inline in the manuscript) with "highlights" in the
      filename. REQUIRED, not optional. VERIFIED 2026-07-04.
- [ ] If a graphical abstract is included (OPTIONAL for this journal — do
      NOT block submission on its absence): ≥531×1328 px (h×w), readable at
      5×13 cm (130mm×50mm), TIFF/EPS/PDF/MS Office, uploaded as a separate
      file (never inserted into the manuscript document itself). VERIFIED
      2026-07-04 — `profile.yml` `toc_graphic.required: false`.
- [ ] Line numbers: manuscript file must NOT contain manually-inserted line
      numbers — Elsevier's own submission system adds them automatically.
      VERIFIED 2026-07-04 ("Please do not include line numbering in the
      manuscript file, as it will be added automatically").
- [ ] Single-anonymized peer review acknowledged (no double-anonymized
      option exists for this journal — do not offer it as a choice).
      VERIFIED 2026-07-04.
- [ ] Reference style: Elsevier-Harvard (author-date), matching
      `assets/elsevier-harvard.csl` — NOT the numbered/bracket style that
      also appears (inconsistently) on the official Guide for Authors page.
      VERIFIED 2026-07-04 via the official CSL repository's ISSN-matched
      `dependent/water-research.csl` mapping. All citekeys must resolve.
      Formatting is not strictly enforced pre-acceptance, but should match
      at submission-ready render time.
- [ ] CRediT authorship statement present, using the 14 official CRediT
      roles. REQUIRED of the corresponding author. VERIFIED 2026-07-04.
- [ ] Declaration of Competing Interest completed via
      declarations.elsevier.com and the resulting Word document attached as
      a SEPARATE FILE at the upload-files step — mandatory even when there
      is nothing to declare ("I have nothing to declare"). VERIFIED
      2026-07-04.
- [ ] Declaration of generative AI use present (new section before
      References) IF any generative AI tool was used in manuscript
      preparation; omit entirely if nothing to disclose. VERIFIED
      2026-07-04.
- [ ] Supplementary Information (if present): separate file(s), no
      PDF-only restriction, NOT admissible at all for Making Waves
      submissions. VERIFIED 2026-07-04. SI cover sheet / internal TOC /
      page-numbering-prefix conventions are UNCONFIRMED (see SKILL.md TO
      VERIFY) — do not fabricate an S1/S2 scheme for this journal without
      re-checking.
- [ ] Submission via https://submit.elsevier.com/WR (Editorial Manager,
      journal code "wr"). VERIFIED 2026-07-04 (stated directly on the
      official Guide for Authors page).
- [ ] Data availability: Option A applies (encouraged, not mandatory) —
      deposit + cite dataset if applicable; do not treat as a hard blocker.
      VERIFIED 2026-07-04.
SOFT:
- [ ] Scope self-check against the desk-rejection framing in
      editorial-framing.md — Water Research has NO pre-submission
      evaluation service; authors are expected to self-assess fit.
- [ ] Cover letter continuity argument drafted; if building on the group's
      own prior WR papers, cite them explicitly as track record in this
      exact journal (identify them privately — not listed here).
- [ ] Funding statement drafted using the journal's standard "Funding:
      This work was supported by..." template (or the "did not receive any
      specific grant" fallback sentence if unfunded).
- [ ] Table style sanity check: editable text (not images), notes below
      the table body, no vertical rules/cell shading.
- [ ] Figure resolution sanity check against the three dpi tiers (halftone
      >=300dpi, line-art >=1000dpi, combination >=500dpi).
Open items remaining (see SKILL.md TO VERIFY queue): line spacing,
manuscript body font/size, SI page-prefix/cover-sheet/internal-TOC, figure
color space (RGB/CMYK) and free-color-in-print status, sans-serif
figure-lettering rule, revision word-count-overrun rule, graphical-abstract
minimum dpi, full text of the 2012 desk-rejection editorial.
