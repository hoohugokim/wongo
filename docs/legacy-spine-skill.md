---
name: quarto-manuscript-sci
description: >
  End-to-end SCI journal manuscript workflow in Quarto: author .qmd with
  code-generated figures/tables/stats, render submission-grade DOCX for
  Word-only coauthors, merge their tracked-changes edits back into the .qmd,
  build submission packages, cover letters, and revisions. Use whenever the
  user mentions manuscript writing/revision, journal submission, .qmd, DOCX
  round-trip, coauthor edits, tracked changes, reference-doc styling,
  Supporting Information (SI), or response-to-reviewers. Pair with the
  journal profile skill quarto-manuscript-<journal> when the target journal
  is known. NOT for general multi-format reports or dashboards — use
  quarto-report for those.
compatibility: Quarto CLI >=1.5 (bundles pandoc); Python >=3.11 (scripts are PEP 723 single-file — run via 'uv run scripts/<name>.py ...'; 'pixi run python scripts/<name>.py ...' works too in this repo's dev env); R or Python compute engine per project.
---

# Quarto SCI Manuscript Skill (Global)

Journal-agnostic spine for the manuscript lifecycle. Journal-specific numbers
(word limits, TOC art, reference style, SI packaging) live in separate
`quarto-manuscript-<slug>` profile skills (e.g. `quarto-manuscript-est` for
Environmental Science & Technology) that implement the **journal profile
contract** (see `references/journal-profile-contract.md`). Never hard-code
journal requirements here.

## 0. Routing — determine lifecycle stage first

Before doing anything, classify the request into one stage and jump to that
section. If ambiguous, ask one question, not three.

| Stage | Signals | Section |
|---|---|---|
| S1 Scaffold | "new manuscript", "start a paper", empty repo | §1 |
| S2 Author | writing/editing .qmd content, figures, stats | §2 |
| S3 Render | "make the DOCX", "send to coauthors" | §3 |
| S4 Round-trip | incoming .docx with tracked changes/comments | §4 |
| S5 Submit | "submission package", cover letter, checklist | §5 |
| S6 Revise | reviewer comments, response letter, diff for resubmission | §6 |

Load the journal profile (declared in `_journal.yml` → `journal:` key, which
holds the slug, e.g. `est`) at every stage; S3/S5/S6 MUST fail loudly if no
profile is set. All three scripts (`validate.py`, `render.py`, `roundtrip.py`)
do this resolution themselves via `mslib.load_journal_config` /
`mslib.load_profile` — a missing or malformed `_journal.yml`, or an
unrecognized `journal:` slug, raises a clear error before anything else runs.

## 1. S1 — Scaffold a new manuscript project

Copy `assets/scaffold/` into the project root and fill placeholders:

```
project/
├── _quarto.yml            # from scaffold; set engine (knitr|jupyter), bibliography
├── _journal.yml           # OURS, not Quarto's: journal: <profile-slug>, ms_type, blinding
├── index.qmd              # main text; sections as level-1 headings
├── si.qmd                 # Supporting Information; renders to separate DOCX
├── refs.bib               # exported from Zotero/Better BibTeX, citekeys stable
├── figures/               # code-generated only; no hand-edited binaries
│   └── toc-art.*          # if the profile requires TOC art (S3 looks here)
├── decisions/             # created by roundtrip.py at S4: merge worksheets
└── output/                # gitignored; render targets land here
```

`_quarto.yml`'s `docx` format block deliberately does NOT hard-code
`reference-doc`/`csl` — `render.py` injects both via `-M` flags read from the
journal profile at render time (see §3), so the same scaffold works for any
profile without editing.

Rules:
- One sentence per line in .qmd prose (semantic line breaks) — makes S4 merge
  diffs tractable. Enforce; do not silently reflow.
- Every number that appears in prose and comes from analysis must be an inline
  code expression (`` `r ...` `` / `{python} `), never typed by hand.
- Cross-references via Quarto (`@fig-`, `@tbl-`, `@eq-`, `@sec-`) only.
- Citations via citekeys (`@smith2024`) against `refs.bib` only.

## 2. S2 — Authoring support

- Match register: SCI research-article prose, no marketing language, hedge only
  where the data hedges.
- IMRaD by default; journal profile may override section names
  (e.g., ACS journals use "Materials and Methods" — profile decides, not you).
- When writing Results, read the actual computed outputs (run the chunks or
  inspect frozen results) before describing them. Never describe a figure you
  have not seen rendered.
- SI content policy: anything a specialist needs but a reader doesn't → `si.qmd`.
  Keep main-text word budget in view (profile supplies the limit) — run
  `uv run scripts/validate.py [--project DIR]` early and often; the word-limit
  check counts `index.qmd` only: body prose + the front-matter `abstract` +
  figure/table caption text, excluding headings, code, and the
  references-section-as-rendered. This is an approximation of the profile's
  `counting_rule`, not a verbatim implementation of it — the journal's own
  submission-system checker is authoritative; a pass here is a strong signal,
  not a guarantee. Content moved into `si.qmd` does NOT count toward the
  limit, so when a manuscript runs long, moving detail to SI is a legitimate
  way to get under budget, not just a content-organization choice.

## 3. S3 — Render to collaboration/submission DOCX

Entry point: `uv run scripts/render.py --target {collab|submission} [--project DIR]`

Pipeline (as implemented):
1. Run the same checks as `validate.py` and print the report. If any HARD
   check fails and `--target submission`, refuse to render at all (no docx is
   produced this run) — fix the failure or render `--target collab` instead.
   `--target collab` always proceeds, report printed for visibility.
2. `quarto render index.qmd --to docx --output main-<target>.docx`, with
   `-M reference-doc:<profile's reference_doc>` and `-M csl:<profile's csl>`
   resolved to absolute paths under the profile directory. Output lands in
   `output/` (via `project.output-dir` in `_quarto.yml`).
3. python-docx post-processing (things pandoc cannot do):
   - `--target submission` only: line numbers if `profile.line_numbers`,
     double spacing if `profile.spacing == "double"`, TOC art inserted before
     the first Heading-1 paragraph if `profile.toc_graphic.required` (hard
     error if none of `figures/toc-art.{png,tiff,tif,jpg,jpeg}` exists).
   - both targets: font swap across body/heading/caption styles — Pretendard
     for `collab`, Times New Roman for `submission` (journal portals dislike
     exotic fonts) — and a `PAGE` field in the footer.
4. If `si.qmd` exists, render it the same way to `si-<target>.docx`, then
   post-process: font swap, optional SI cover sheet (`si.needs_cover_sheet`,
   figure/table counts read from the rendered docx), footer page numbers
   prefixed with `si.page_prefix` (e.g. "S"), page numbering restarted at 1.

Stale-output caveat: refusing a submission render (or an SI step failing
after the main doc already rendered, in the same run) does NOT delete any
`output/main-<target>.docx` / `output/si-<target>.docx` left over from an
earlier successful run. Check the file's timestamp before handing it to
coauthors or a submission portal — a HARD failure today does not retroactively
invalidate yesterday's good render sitting in the same directory.

v1 scope cut: double-anonymous title-page blinding and `figures.placement:
end` are NOT implemented by `render.py` — it never strips author identity
from the DOCX, and it always leaves figures wherever `index.qmd` places them
in the source. A profile that documents either relies on your judgment at
authoring/render time, not on automated enforcement; `_journal.yml`'s
`blinding` key and a profile's `figures.placement` are informational only
for now.

## 4. S4 — Round-trip coauthor DOCX back into .qmd  ⟵ the hard part

Entry point: `uv run scripts/roundtrip.py <coauthor.docx> [--project DIR]`

Mechanics (deterministic, scripted):
- Runs `quarto pandoc --track-changes=all --wrap=none <docx> -t markdown` to
  extract insertion/deletion/comment spans with author attribution
  (`--wrap=none` avoids pandoc hard-wrapping a long span's text or attribute
  list across a line break — see `references/quarto-docx-quirks.md`).
- Adjacent delete+insert by the *same* author collapse into one `replacement`
  change; the same pair by *different* authors stays as two independent rows.
- A change whose bracket content itself contains nested brackets (e.g. a
  coauthor-inserted citation) cannot be captured by the span parser; rather
  than silently dropping it, it is surfaced as a `kind: unparsed` row instead.
- Each change is aligned to a best-guess `index.qmd` line via fuzzy text
  matching against surrounding context (this is why §1 mandates
  one-sentence-per-line); `unparsed` rows never get a location guess.
- Emits a structured merge worksheet at
  `decisions/merge-<YYYYMMDD>-<stem>.md`. Every row starts
  `disposition: PENDING`.

Judgment (yours, not the script's) — for each worksheet item decide:
- **Prose edit** → apply to .qmd text.
- **Edit inside an auto-generated number/figure caption** → do NOT paste the
  edit; flag it: either the analysis is wrong (fix code) or the coauthor
  misread (respond in comment log). Never let a hand-typed number replace an
  inline code expression.
- **New citation added by hand** → resolve to a real entry, add to `refs.bib`
  with a citekey, replace prose citation with `@citekey`. If unresolvable,
  flag; do not fabricate a reference.
- **Comment (margin note)** → append to `decisions/comments-log.md` with your
  disposition, using the worksheet's own vocabulary:
  `apply` / `reject: <reason>` / `fix-code` / `needs-PI`.
- **`unparsed` row** ("PARSER COULD NOT EXTRACT THIS CHANGE") → open the
  source DOCX at the quoted context and resolve the change by hand before
  setting any disposition. Never treat an unparsed row as ignorable or leave
  it at `PENDING` — it means a real coauthor edit exists that the tool
  could not read, not that nothing happened there.
- **Location sanity check** → worksheet locations point at body lines only;
  an edit inside the rendered title/abstract block (YAML front matter) gets
  mapped to the nearest body line instead. If a row's context reads like the
  abstract, the true edit target is the front matter — apply it there.

Always show the user the worksheet with your proposed dispositions BEFORE
applying anything to the .qmd. Apply only after approval.

## 5. S5 — Submission package

Driven entirely by the journal profile's `references/submission-checklist.md`
and `profile.yml`. Global skill responsibilities only:
- assemble `output/submission/` with profile-named files
- generate cover letter draft from `assets/cover-letter-template.md` +
  profile's editorial-framing notes
- final gate: `uv run scripts/validate.py --strict [--project DIR]` — exits 1
  on any HARD failure (the same gate `render.py` applies internally for
  `--target submission`, now checked standalone before packaging)

## 6. S6 — Revision cycle

- Ingest decision letter → build `response-to-reviewers.qmd` with a
  {reviewer comment → response → manuscript change (with location)} table.
- Diff DOCX for resubmission: render both versions and use Word's Compare;
  revisit scripting this when a journal demands a tracked-changes file
  (honest v1 scope — no automated diff tool is bundled).
- Word-limit discipline on revision is journal-specific (profiles note if the
  journal forbids growth on revision).

## Bundled resources

- `scripts/render.py` — S3 pipeline
- `scripts/validate.py` — word count (index.qmd only: prose + abstract +
  captions, an approximation of the profile's `counting_rule` — see S2),
  citekeys, cross-refs, and figure-existence HARD checks; profile-staleness
  and SI-presence WARN checks; `--strict` exits 1 on any HARD failure
- `scripts/roundtrip.py` — S4 extraction + alignment
- `scripts/mslib.py` — shared helpers imported by the three scripts above
  (not a CLI itself)
- `references/journal-profile-contract.md` — what every `quarto-manuscript-*`
  profile skill must provide
- `references/quarto-docx-quirks.md` — accumulated pandoc/quarto/docx pathologies;
  APPEND every new quirk you solve. This file is the skill's compounding memory.
- `assets/scaffold/` — new-project template
- `assets/cover-letter-template.md` — journal-agnostic skeleton

## Non-negotiables

1. The .qmd is the single source of truth. DOCX artifacts are disposable renders.
2. No hand-typed analysis numbers in prose, ever.
3. No fabricated citations; every citekey resolves in `refs.bib`.
4. Submission renders must pass profile hard checks or not be produced
   (collab renders regardless, with the failure report printed — it is for
   internal eyes, not a submission).
5. When you solve a new formatting/round-trip problem, promote it: script if
   mechanical, note in `references/quarto-docx-quirks.md` if knowledge.
