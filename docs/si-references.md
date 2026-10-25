# References from the main manuscript to Supporting Information

Enable the optional interface in `_journal.yml`:

```yaml
si_references: true
```

Use an ordinary Markdown link in `index.qmd`, with the exact SI figure/table id:

```markdown
See [SI table](wongo-si:tbl-rate-constants) and
[SI figure](wongo-si:fig-response) in the Supporting Information.
```

Wongo replaces each placeholder with the label printed in the final SI, for
example `Table S2` and `Figure S3`. Placeholder wording is replaced; plain text
and emphasis are supported. Main body, footnote and endnote links work. Equations,
images and Word fields inside placeholder labels are refused to preserve rich
content. Headers, footers and other annotation parts are unsupported.

The SI must contain uniquely bookmarked, numbered English Figure/Table captions.
Quarto normally generates those bookmarks for `#fig-...` and `#tbl-...` floats,
including tables emitted by R/Python. Numbers come from the rendered caption,
not the id or the source order. A data-driven reorder changes the main label on
the next render. Missing, duplicate or unsupported destinations refuse both
collab and submission and preserve the previous outputs and manifest.

If the SI should display `S` numbers, configure that in `si.qmd` using Quarto:

```yaml
crossref:
  fig-title: Figure S
  tbl-title: Table S
```

Wongo copies `Table 2` if that is what the SI prints; it never invents `S2`.
Chapter-style numeric labels are supported. Subfigure panels, equations, custom
localized caption titles, source includes and cross-file clickable Word links
are outside this first interface. Explicit SI references are plain text in the
final main DOCX, so they remain readable when files are distributed separately.

`wongo check --json` validates the opt-in and static link syntax without executing
analysis or rendering. It reports that destinations/numbers are unverified until
render; generated labels may not exist in the source. The render verifies actual
hyperlinks in final main OOXML against final SI bookmarks after declared
postprocess scripts. A transform that removes bookmarks/captions refuses the
reference. Manifest `si_references` records the final SI hash, main before/after
hashes and resolved labels/parts; sealed output hashes match those final bytes.
Earlier `postprocess` hashes continue to describe each declared script's own step.

Native `@tbl-rate-constants` still resolves only inside the document defining it.
The explicit link does not make native cross-document references valid. Existing
duplicate-label rules remain, and an explicit main-to-SI callout satisfies that
SI item's uncited-item check. Literal examples in code/comments are ignored.
An unresolved native Quarto warning still promotes collab with `checks_failed`;
mid-render input changes refuse both targets. Plain check keeps its exit-zero
JSON-failure contract; use `--strict` for a gating exit code.
