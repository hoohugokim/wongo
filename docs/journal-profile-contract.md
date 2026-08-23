# Journal Profile Contract

Every `quarto-manuscript-<slug>` skill MUST provide the following so
`quarto-manuscript-sci` can drive it without journal-specific code paths.

## Required files

```
quarto-manuscript-<slug>/
├── SKILL.md                      # human/agent-readable requirements + judgment notes
├── profile.yml                   # machine-readable keys consumed by render.py/validate.py
├── assets/
│   ├── reference.docx            # Quarto/pandoc reference-doc with journal styles
│   └── <csl-file>.csl            # citation style
├── scripts/                      # OPTIONAL: reproducible builders for assets/ (e.g.
│                                  # build_reference_docx.py) — never hand-edit assets/ instead
└── references/
    ├── submission-checklist.md   # gate list for S5, marked HARD/SOFT
    └── editorial-framing.md      # scope, desk-rejection patterns, cover-letter angle
```

Profile skills are named `quarto-manuscript-<slug>` (e.g.
`quarto-manuscript-est` for Environmental Science & Technology); the consumer
project's per-project config file is our own `_journal.yml` — distinct from
any Quarto-native project config (see `quarto-manuscript-sci/SKILL.md`) —
and its `journal:` key selects the slug that resolves to this skill.

## profile.yml schema (v0 — extend as needed, keep backward compatible)

```yaml
journal: ""            # display name
slug: ""
publisher: ""
submission_portal: ""  # URL
manuscript_types:      # word limits are MAIN TEXT unless counting_rule says otherwise
  - type: ""
    word_limit: 0
    counting_rule: ""  # exactly what counts; cite source
csl: ""
reference_doc: ""
section_headings: []   # ordered; journal-specific — check this profile's list, don't assume any generic heading set applies
line_numbers: true|false
spacing: single|double
blinding: single|double-anonymous|optional  # informational in v1 (consumed by agent judgment, not render.py)
toc_graphic:           # the whole block may be null if the journal has no TOC/graphical-abstract concept at all
  required: true|false  # REQUIRED key whenever the block itself is present — render.py dispatches on this
  width_mm: 0
  height_mm: 0
  min_dpi: 0
  formats: []
  synopsis_words: [0, 0]   # min,max; null if no synopsis
  label: ""              # OPTIONAL: exact required label text for the graphic (e.g. ACS's
                          # "For Table of Contents Only"); render.py falls back to that same
                          # default string when this key is absent
  manuscript_placement: last-page|after-abstract  # OPTIONAL: where the graphic goes in the
                          # rendered manuscript; render.py's insert_toc_art() currently only
                          # implements the ACS last-page pattern (page break, label, centered
                          # image, appended at document end) — treat other values as documentation
                          # until a journal actually needs different placement logic
si:
  separate_file: true|false
  page_prefix: ""      # e.g. "S"
  needs_own_toc: true|false
  needs_cover_sheet: true|false
figures:
  placement: inline|end  # informational in v1 (consumed by agent judgment, not render.py)
  color_policy: ""
tables:
  style_notes: ""
sources: []            # URLs backing every hard number above; REQUIRED
verified_date: ""      # ISO date the numbers were last checked against the journal
```

## Rules

- Every hard number in `profile.yml` must trace to an entry in `sources`.
- Unverified or secondary-source claims go in SKILL.md under "TO VERIFY",
  never into `profile.yml`.
- `verified_date` older than 6 months ⇒ validate.py emits a staleness warning;
  re-check the journal's author guidelines before a real submission.
