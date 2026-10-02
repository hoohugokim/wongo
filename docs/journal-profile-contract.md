# Journal Profile Contract

> **Canonical implementation:** `src/wongo/profiles/<slug>/` in this repo (shipped as wheel data).
> The `quarto-manuscript-<slug>` skills at `~/.claude/skills/` are now thin wrappers that retain judgment
> (`SKILL.md`, `references/`) and point to `wongo` for machine-readable `profile.yml`/`assets/`.
> New profiles must still satisfy this contract — add them under `src/wongo/profiles/` and register via
> `wongo profile list` / `wongo profile verify`.

Every `quarto-manuscript-<slug>` skill MUST provide the following so
`quarto-manuscript-sci` can drive it without journal-specific code paths.

## Required files

```
quarto-manuscript-<slug>/
├── SKILL.md                      # human/agent-readable requirements + judgment notes
├── profile.yml                   # machine-readable keys consumed by `wongo render` / `wongo check`
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
    word_limit_includes_references: false  # OPTIONAL: true when the limit counts the
                       # reference list (e.g. Water Research). `wongo check` gives a source
                       # estimate plus WARN; render adds the staged main bibliography count
                       # and refuses an over-limit submission before promoting any outputs.
    word_count:        # OPTIONAL per-type source-counting policy; shown defaults preserve
                       # existing profiles. `counting_rule` remains the source-backed rule.
      include_abstract: true
      exclude_sections: []
      include_figure_captions: true
      include_table_captions: true
      exclude_boxes: false
csl: ""
reference_doc: ""
section_headings: []   # ordered; journal-specific — check this profile's list, don't assume any generic heading set applies
line_numbers: true|false|forbidden  # true: engine adds them on the submission render; false: not
                       # required (house style may add them); forbidden: the journal says do NOT
                       # include them (e.g. Water Research adds its own) — the submission render
                       # strips line numbers even if the house style enables them
spacing: single|double
blinding: single|double-anonymous|optional  # informational in v1 (consumed by agent judgment, not wongo render)
toc_graphic:           # the whole block may be null if the journal has no TOC/graphical-abstract concept at all
  required: true|false  # REQUIRED key whenever the block itself is present — render.py dispatches on this
  width_mm: 0          # width_mm/height_mm are the MAXIMUM box; the render scales the
  height_mm: 0         # image to fit inside it with its aspect ratio preserved
  min_dpi: 0
  formats: []
  synopsis_words: [0, 0]   # min,max; null if no synopsis
  label: ""              # OPTIONAL: exact required label text for the graphic (e.g. ACS's
                          # "For Table of Contents Only"); render.py falls back to that same
                          # default string when this key is absent
  manuscript_placement: last-page|after-abstract  # OPTIONAL: where the graphic goes in the
                          # rendered manuscript; wongo.engine.insert_toc_art() currently only
                          # implements the ACS last-page pattern (page break, label, centered
                          # image, appended at document end) — treat other values as documentation
                          # until a journal actually needs different placement logic
si:
  separate_file: true|false
  page_prefix: ""      # e.g. "S"
  needs_own_toc: true|false
  needs_cover_sheet: true|false
figures:
  placement: inline|end  # informational in v1 (consumed by agent judgment, not wongo render)
  color_policy: ""
tables:
  style_notes: ""
sources: []            # URLs backing every hard number above; REQUIRED
verified_date: ""      # ISO date the numbers were last checked against the journal
```

## Rules

For `word_limit_includes_references: true`, source checks can fail an already
over-limit manuscript before Quarto runs, but a source-only pass is unproven.
During rendering, wongo adds the words in the newly staged main DOCX's
`Bibliography` paragraphs to that source estimate. The report exposes both
counts and calls their sum an **estimated total**; it does not claim to match
Word or a submission system's tokenizer. Formatted runs are joined before
counting, and linked text, tabs and line breaks are included. Only the main
manuscript's reference list counts; SI and uncited `.bib` entries are not added.

The final HARD gate runs before output/ and its manifest are replaced. Missing
bibliography text when the main document requests citations or `nocite`, or
source/profile edits during rendering, leave the count unverified and block
submission. Collab renders remain available for inspection and report the HARD
failure. Source-only `wongo check` never silently reuses an old or edited DOCX;
run `wongo render --target submission` for the final reference-inclusive gate.

This path assumes Quarto/Pandoc's standard `Bibliography` paragraph style. Do
not apply that style to hand-written prose already counted in the source, or
strip it from generated references with a custom filter. Manually written
references in ordinary source paragraphs already enter the source estimate.
Generated main-text prose, includes, complex markup and citation expansion
remain limitations of that estimate; this change measures the reference-list
contribution, not the entire rendered manuscript.

`word_count.exclude_sections` lists exact heading titles, matched without case,
manual section numbering, emphasis or Pandoc attributes. Both ATX (`# Methods`)
and setext headings work; an excluded section includes its subsections and ends
at the next heading of equal or higher rank. List aliases explicitly in the
profile (for example `Methods`, `Online Methods`, `Materials and Methods`).
`include_abstract: false` excludes both YAML abstract metadata and a body
`Abstract` section. Use YAML for an abstract followed by unheaded main text.

Caption flags control `fig-cap`/`tbl-cap` chunk options. Figure exclusion also
covers inline Markdown images and fenced `#fig-*` floats. Table-caption
exclusion covers `:`/`Table:` caption paragraphs labelled with `#tbl-*` or
adjacent to pipe tables; separate legend sections belong in `exclude_sections`.
`exclude_boxes: true` drops `Box`, `Boxes` and numbered `Box N` sections, plus
fenced divs marked `.box`, `#box-*` or `box`, including nested content.

These are source estimates, with inline code represented by one word. They do
not evaluate code, expand includes or shortcodes, parse raw HTML/LaTeX, or count
the rendered bibliography. Complex caption/table syntax can still need a manual
count. Exclusions affect only the word count: citations, crossrefs and missing
figures are checked throughout the original manuscript. Invalid policy keys or
values fail as configuration errors, including when a local profile overrides
a shipped one. Do not infer an exclusion from a journal name or parse the prose
`counting_rule`; record the verified policy for each manuscript type.

- Every hard number in `profile.yml` must trace to an entry in `sources`.
- Unverified or secondary-source claims go in SKILL.md under "TO VERIFY",
  never into `profile.yml`.
- `verified_date` older than 6 months ⇒ `wongo check` emits a staleness warning;
  re-check the journal's author guidelines before a real submission.
